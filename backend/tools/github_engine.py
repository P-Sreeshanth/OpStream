import os
import base64
from github import Github, GithubException, Auth
from typing import List, Dict, Optional

class GitHubEngine:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN is required")
        self.client = Github(auth=Auth.Token(self.token))

    def search_issues(self, limit: int = 5, domain: str = None, sort_by: str = "recent") -> List[Dict]:
        """
        Search for 'good first issue' with optional domain filtering.
        
        Args:
            limit: Max number of issues to return
            domain: Filter by domain (react, python, ml, rust, go, javascript, etc.)
            sort_by: 'recent' (created date) or 'popular' (reactions/comments)
        """
        from datetime import datetime, timedelta
        
        # Domain to GitHub search query mapping
        domain_queries = {
            "react": "language:javascript language:typescript topic:react",
            "python": "language:python",
            "machine-learning": "language:python topic:machine-learning topic:deep-learning topic:tensorflow topic:pytorch",
            "rust": "language:rust",
            "go": "language:go",
            "javascript": "language:javascript",
            "typescript": "language:typescript",
            "java": "language:java",
            "cpp": "language:c++",
            "web": "topic:web topic:frontend topic:css topic:html",
            "backend": "topic:backend topic:api topic:rest",
            "mobile": "topic:android topic:ios topic:react-native topic:flutter",
            "devops": "topic:devops topic:docker topic:kubernetes topic:ci-cd",
            "data": "topic:data-science topic:data-analysis topic:pandas",
        }
        
        # Build query
        cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        
        query_parts = [
            'label:"good first issue"',
            'is:open',
            f'created:>{cutoff}'
        ]
        
        # Add domain filter if specified
        if domain and domain.lower() in domain_queries:
            query_parts.append(domain_queries[domain.lower()])
        
        query = " ".join(query_parts)
        
        # Sort order - GitHub supports: created, updated, comments
        # 'popular' uses comments as a proxy for engagement
        sort_order = "comments" if sort_by == "popular" else "created"
        
        print(f"[DEBUG] GitHub Query: {query}")
        print(f"[DEBUG] Sort by: {sort_order}")
        
        issues = self.client.search_issues(query, sort=sort_order, order="desc")
        results = []
        
        for issue in issues:
            if len(results) >= limit:
                break
            
            created_at = issue.created_at.strftime("%Y-%m-%d %H:%M") if issue.created_at else "Unknown"
            
            # Get labels
            labels = [label.name for label in issue.labels] if issue.labels else []
            
            # Get repo info for tech stack hints
            repo = issue.repository
            language = repo.language or "Unknown"
            stars = repo.stargazers_count
            
            print(f"[DEBUG] Found: {issue.title} | {language} | ⭐{stars}")
            
            results.append({
                "title": issue.title,
                "url": issue.html_url,
                "repo_name": issue.repository.full_name,
                "number": issue.number,
                "comments": issue.comments,
                "created_at": created_at,
                "labels": labels,
                "language": language,
                "stars": stars,
                "body": (issue.body or "")[:500]  # First 500 chars for skill analysis
            })
        
        print(f"[DEBUG] Total results: {len(results)}")
        return results

    def get_issue_details(self, issue_url: str) -> Dict:
        """Parse issue URL and fetch details."""
        # Expected format: https://github.com/owner/repo/issues/number
        parts = issue_url.rstrip("/").split("/")
        if "github.com" not in parts:
            raise ValueError("Invalid GitHub URL")
            
        try:
            owner = parts[-4]
            repo_name = parts[-3]
            number = int(parts[-1])
            repo_full_name = f"{owner}/{repo_name}"
            
            repo = self.client.get_repo(repo_full_name)
            issue = repo.get_issue(number)
            
            return {
                "owner": owner,
                "repo_name": repo_name,
                "full_name": repo_full_name,
                "number": number,
                "title": issue.title,
                "body": issue.body or "",
                "repo": repo
            }
        except (IndexError, ValueError) as e:
             raise ValueError(f"Could not parse issue URL: {e}")
        except GithubException as e:
            raise ValueError(f"GitHub API Error: {e}")

    def get_file_content(self, repo, path: str) -> str:
        """Fetch content of a specific file."""
        try:
            file_content = repo.get_contents(path)
            return base64.b64decode(file_content.content).decode("utf-8")
        except GithubException:
            return ""

    def fork_and_create_pr(self, 
                          repo_full_name: str, 
                          file_path: str, 
                          new_content: str, 
                          issue_number: int,
                          dco_name: str = "Anonymous",        # Default for MVP
                          dco_email: str = "anon@example.com" # Default for MVP
                          ) -> str:
        """
        1. Fork repo
        2. Create branch
        3. Commit with DCO
        4. Open PR
        """
        # 1. Get Repo & Fork
        original_repo = self.client.get_repo(repo_full_name)
        user = self.client.get_user()
        
        try:
            fork = user.create_fork(original_repo)
            # Fetch fork object to ensure we have the full object with permissions (sometimes async)
            # In a real app, might need a retry loop here as forking isn't instant
        except GithubException:
            # Fork might already exist
            fork = self.client.get_repo(f"{user.login}/{original_repo.name}")

        # 2. Create Branch
        # Get default branch sha
        default_branch = fork.default_branch
        sb = fork.get_branch(default_branch)
        
        branch_name = f"fix-issue-{issue_number}-{int(os.urandom(4).hex(), 16)}"
        
        try:
            fork.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sb.commit.sha)
        except GithubException as e:
            # If branch exists (unlikely with random), fail or handle
            raise ValueError(f"Could not create branch: {e}")

        # 3. Commit
        # Get current file sha for update
        try:
            contents = fork.get_contents(file_path, ref=branch_name)
            sha = contents.sha
            message = f"Fix issue #{issue_number}\n\nSigned-off-by: {dco_name} <{dco_email}>"
            
            fork.update_file(
                path=file_path,
                message=message,
                content=new_content,
                sha=sha,
                branch=branch_name
            )
        except GithubException as e:
            raise ValueError(f"Could not commit file: {e}")

        # 4. Create PR
        # PR is created on the ORIGINAL repo, from the fork's branch
        # Head format: user:branch_name
        head = f"{user.login}:{branch_name}"
        
        try:
            pr = original_repo.create_pull(
                title=f"Fix for Issue #{issue_number}",
                body=f"Automated fix for #{issue_number}.\n\nGenerated by OpenSourceLink Bot.",
                head=head,
                base=original_repo.default_branch
            )
            return pr.html_url
        except GithubException as e:
             raise ValueError(f"Could not create PR: {e}")
