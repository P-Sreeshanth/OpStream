"""
GitHub Fetcher - Extract README, metadata, issues, and file tree from repositories.
Advanced chunking: parses README into sections for better context retrieval.
"""
import os
import re
import base64
import logging
from typing import List, Dict, Optional
from github import Github, GithubException, Auth

logger = logging.getLogger(__name__)


class GitHubFetcher:
    """Fetch repository data from GitHub for RAG indexing."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN is required")
        
        self.client = Github(auth=Auth.Token(self.token))
        logger.info("[Fetcher] GitHub client initialized")
    
    def parse_repo_url(self, url: str) -> str:
        """Parse GitHub URL to get owner/repo format."""
        url = url.rstrip("/")
        
        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        
        if "/" in url and "http" not in url:
            return url
        
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def _chunk_readme_by_sections(self, content: str) -> List[Dict]:
        """
        Parse README into sections based on markdown headers.
        Each section becomes a separate document with parent reference.
        """
        lines = content.split('\n')
        sections = []
        current_section = {
            'title': 'Introduction',
            'level': 0,
            'content': [],
            'line_start': 1
        }
        
        for i, line in enumerate(lines, 1):
            # Check for markdown headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                # Save previous section if it has content
                if current_section['content']:
                    sections.append({
                        'title': current_section['title'],
                        'level': current_section['level'],
                        'content': '\n'.join(current_section['content']).strip(),
                        'line_start': current_section['line_start'],
                        'line_end': i - 1
                    })
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {
                    'title': title,
                    'level': level,
                    'content': [line],
                    'line_start': i
                }
            else:
                current_section['content'].append(line)
        
        # Don't forget the last section
        if current_section['content']:
            sections.append({
                'title': current_section['title'],
                'level': current_section['level'],
                'content': '\n'.join(current_section['content']).strip(),
                'line_start': current_section['line_start'],
                'line_end': len(lines)
            })
        
        return sections
    
    def fetch_readme(self, repo_full_name: str) -> List[Dict]:
        """
        Fetch README and parse into sections.
        Returns multiple documents - one per section.
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            readme = repo.get_readme()
            content = base64.b64decode(readme.content).decode("utf-8")
            
            sections = self._chunk_readme_by_sections(content)
            
            documents = []
            for section in sections:
                # Skip empty or very small sections
                if len(section['content']) < 20:
                    continue
                
                documents.append({
                    "content": section['content'],
                    "type": "readme",
                    "metadata": {
                        "filename": readme.name,
                        "section_title": section['title'],
                        "section_level": section['level'],
                        "line_start": section['line_start'],
                        "line_end": section['line_end']
                    }
                })
            
            # Also store full README for parent-document retrieval
            documents.append({
                "content": content[:8000],  # First 8k chars
                "type": "readme_full",
                "metadata": {
                    "filename": readme.name,
                    "section_title": "Full Document"
                }
            })
            
            logger.info(f"[Fetcher] Parsed README into {len(documents)} sections")
            return documents
            
        except GithubException as e:
            logger.warning(f"[Fetcher] Failed to fetch README: {e}")
            return []
    
    def fetch_metadata(self, repo_full_name: str) -> Optional[Dict]:
        """Fetch repository metadata."""
        try:
            repo = self.client.get_repo(repo_full_name)
            
            parts = [
                f"Repository: {repo.full_name}",
                f"Description: {repo.description or 'No description'}",
                f"Language: {repo.language or 'Not specified'}",
                f"Stars: {repo.stargazers_count}",
                f"Forks: {repo.forks_count}",
                f"Open Issues: {repo.open_issues_count}",
            ]
            
            topics = repo.get_topics()
            if topics:
                parts.append(f"Topics: {', '.join(topics)}")
            
            content = "\n".join(parts)
            
            logger.info(f"[Fetcher] Fetched metadata for {repo.full_name}")
            
            return {
                "content": content,
                "type": "metadata",
                "metadata": {
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "topics": topics
                }
            }
        except GithubException as e:
            logger.warning(f"[Fetcher] Failed to fetch metadata: {e}")
            return None
    
    def fetch_file_tree(self, repo_full_name: str, max_depth: int = 3) -> Optional[Dict]:
        """
        Fetch repository file tree structure.
        Creates a searchable document of the directory structure.
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            
            # Get the default branch tree
            tree = repo.get_git_tree(repo.default_branch, recursive=True)
            
            # Group files by directory
            directories = {}
            important_files = []
            
            for item in tree.tree:
                if item.type == "blob":  # It's a file
                    path = item.path
                    parts = path.split('/')
                    
                    # Track important files
                    basename = parts[-1].lower()
                    if basename in ['package.json', 'requirements.txt', 'cargo.toml', 
                                   'go.mod', 'pom.xml', 'dockerfile', 'docker-compose.yml',
                                   'tsconfig.json', 'vite.config.ts', 'next.config.js']:
                        important_files.append(path)
                    
                    # Track source directories
                    if len(parts) <= max_depth:
                        dir_path = '/'.join(parts[:-1]) or '/'
                        if dir_path not in directories:
                            directories[dir_path] = []
                        directories[dir_path].append(parts[-1])
            
            # Build a searchable description
            content_parts = [
                f"File Structure for {repo_full_name}",
                "",
                "Important Configuration Files:",
                *[f"  - {f}" for f in important_files[:10]],
                "",
                "Directory Structure:"
            ]
            
            # Add key directories
            src_dirs = ['src', 'lib', 'app', 'components', 'pages', 'api', 'utils', 
                       'backend', 'frontend', 'server', 'client', 'core']
            
            for dir_name in src_dirs:
                matching = [d for d in directories.keys() if dir_name in d.lower()]
                for dir_path in matching[:3]:
                    files = directories[dir_path][:8]
                    content_parts.append(f"\n{dir_path}/")
                    for f in files:
                        content_parts.append(f"  - {f}")
            
            content = "\n".join(content_parts)
            
            logger.info(f"[Fetcher] Fetched file tree ({len(tree.tree)} items)")
            
            return {
                "content": content,
                "type": "file_tree",
                "metadata": {
                    "total_files": len(tree.tree),
                    "important_files": important_files[:10],
                    "key_directories": list(directories.keys())[:20]
                }
            }
            
        except GithubException as e:
            logger.warning(f"[Fetcher] Failed to fetch file tree: {e}")
            return None
    
    def fetch_issues(self, repo_full_name: str, limit: int = 50) -> List[Dict]:
        """Fetch open issues with enhanced metadata."""
        try:
            repo = self.client.get_repo(repo_full_name)
            issues = repo.get_issues(state="open", sort="created", direction="desc")
            
            documents = []
            for issue in issues[:limit]:
                if issue.pull_request:
                    continue
                
                labels = [label.name for label in issue.labels]
                
                # Enhanced content with more context
                content_parts = [
                    f"Issue #{issue.number}: {issue.title}",
                    f"Labels: {', '.join(labels) if labels else 'None'}",
                ]
                
                if issue.body:
                    # Clean up body - remove very long code blocks
                    body = issue.body
                    body = re.sub(r'```[\s\S]{500,}?```', '[code block]', body)
                    content_parts.append(f"Description: {body[:1500]}")
                
                documents.append({
                    "content": "\n".join(content_parts),
                    "type": "issue",
                    "metadata": {
                        "number": issue.number,
                        "title": issue.title,
                        "labels": labels,
                        "url": issue.html_url,
                        "comments": issue.comments,
                        "created_at": issue.created_at.isoformat() if issue.created_at else None,
                        "is_good_first": any('good first' in l.lower() or 'beginner' in l.lower() for l in labels)
                    }
                })
            
            logger.info(f"[Fetcher] Fetched {len(documents)} issues")
            return documents
            
        except GithubException as e:
            logger.warning(f"[Fetcher] Failed to fetch issues: {e}")
            return []
    
    def fetch_all(self, repo_url: str, issue_limit: int = 50) -> Dict:
        """Fetch all data from a repository."""
        repo_name = self.parse_repo_url(repo_url)
        
        documents = []
        
        # Fetch README sections
        readme_docs = self.fetch_readme(repo_name)
        documents.extend(readme_docs)
        
        # Fetch metadata
        metadata = self.fetch_metadata(repo_name)
        if metadata:
            documents.append(metadata)
        
        # Fetch file tree
        file_tree = self.fetch_file_tree(repo_name)
        if file_tree:
            documents.append(file_tree)
        
        # Fetch issues
        issues = self.fetch_issues(repo_name, limit=issue_limit)
        documents.extend(issues)
        
        logger.info(f"[Fetcher] Total documents fetched: {len(documents)}")
        
        return {
            "repo_name": repo_name,
            "documents": documents
        }
