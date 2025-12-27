"""
Repository Analyzer - AI-powered analysis and contribution suggestions.
Uses Groq API with Llama 3 for fast, high-quality responses.
"""
import os
import logging
import json
import re
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """Analyze repositories and suggest contributions using RAG + LLM."""
    
    def __init__(self, rag_engine):
        """
        Initialize analyzer with RAG engine and Groq LLM client.
        
        Args:
            rag_engine: RAGEngine instance for semantic search
        """
        self.rag = rag_engine
        
        # Try Groq first, fall back to HuggingFace router
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        
        if self.groq_key:
            self.provider = "groq"
            self.model = "llama-3.3-70b-versatile"
            logger.info("[Analyzer] Using Groq with Llama 3.3 70B")
        elif self.hf_token:
            self.provider = "huggingface"
            self.model = "meta-llama/Llama-3.2-3B-Instruct"
            logger.info("[Analyzer] Using HuggingFace with Llama 3.2")
        else:
            raise ValueError("Either GROQ_API_KEY or HUGGINGFACEHUB_API_TOKEN is required")
    
    def _generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate text using the configured LLM provider."""
        
        if self.provider == "groq":
            return self._generate_groq(prompt, max_tokens)
        else:
            return self._generate_hf(prompt, max_tokens)
    
    def _generate_groq(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate using Groq API."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"[Analyzer] Groq generation failed: {e}")
            raise ValueError(f"AI generation failed: {e}")
    
    def _generate_hf(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate using HuggingFace Inference API (new router)."""
        url = f"https://router.huggingface.co/hf-inference/models/{self.model}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"[Analyzer] HuggingFace generation failed: {e}")
            raise ValueError(f"AI generation failed: {e}")
    
    def analyze(self, repo_name: str, question: str) -> Dict:
        """
        Answer a question about a repository using advanced RAG.
        Uses HyDE for better retrieval and parent-document context.
        """
        # Use context-aware search with HyDE
        results = self.rag.search_with_context(
            query=question, 
            repo_name=repo_name, 
            top_k=5
        )
        
        if not results:
            return {
                "answer": "I don't have enough information about this repository. Please make sure it has been indexed.",
                "sources": []
            }
        
        # Build context from search results with citations
        context_parts = []
        sources = []
        for i, doc in enumerate(results, 1):
            # Build citation info
            section_info = ""
            if doc['type'] == 'readme':
                section = doc.get('metadata', {}).get('section_title', 'README')
                line_start = doc.get('metadata', {}).get('line_start', '')
                section_info = f" (Section: {section}, Line {line_start})" if line_start else f" (Section: {section})"
            elif doc['type'] == 'file_tree':
                section_info = " (File Structure)"
            
            context_parts.append(f"[{i}] {doc['type'].upper()}{section_info}:\n{doc['content'][:600]}")
            
            sources.append({
                "type": doc['type'],
                "score": round(doc['score'], 3),
                "section": doc.get('metadata', {}).get('section_title', ''),
                "line": doc.get('metadata', {}).get('line_start', ''),
                "preview": doc['content'][:200]
            })
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""You are a helpful assistant analyzing a GitHub repository.

Based on the following indexed information, answer the user's question.
When referencing information, cite the source number (e.g., "According to [1]...").

REPOSITORY CONTEXT:
{context}

USER QUESTION: {question}

Provide a clear, helpful answer. If referencing specific sections or files, mention them explicitly."""

        answer = self._generate(prompt)
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    def suggest_contributions(self, repo_name: str) -> Dict:
        """
        Analyze repository and suggest ways to contribute.
        """
        # Get repository metadata
        metadata_results = self.rag.search(
            query="repository description language topics",
            repo_name=repo_name,
            doc_type="metadata",
            top_k=1
        )
        
        # Get all issues
        all_issues_results = self.rag.search(
            query="issue bug feature documentation help",
            repo_name=repo_name,
            doc_type="issue",
            top_k=15
        )
        
        if not all_issues_results:
            return {
                "summary": "No issues found to analyze. The repository may not have any open issues, or it hasn't been indexed yet.",
                "beginner_friendly": [],
                "documentation": [],
                "bugs": [],
                "features": []
            }
        
        issues_text = "\n\n".join([f"- {doc['content'][:400]}" for doc in all_issues_results[:10]])
        repo_info = metadata_results[0]['content'] if metadata_results else repo_name
        
        prompt = f"""Analyze this GitHub repository and suggest how a developer can contribute.

REPOSITORY INFO:
{repo_info}

OPEN ISSUES:
{issues_text}

Return a JSON object with these exact keys:
{{
    "summary": "2-3 sentence overview of what this project is and current contribution opportunities",
    "beginner_friendly": ["list", "of", "3-5", "beginner", "friendly", "tasks"],
    "documentation": ["list", "of", "2-3", "documentation", "improvements"],
    "bugs": ["list", "of", "3-5", "bugs", "to", "fix"],
    "features": ["list", "of", "3-5", "features", "to", "implement"]
}}

Be specific and actionable. Each item should be under 100 characters. Return ONLY valid JSON."""

        try:
            response = self._generate(prompt, max_tokens=1500)
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions
            else:
                return {
                    "summary": response[:500],
                    "beginner_friendly": [],
                    "documentation": [],
                    "bugs": [],
                    "features": []
                }
        except json.JSONDecodeError:
            logger.warning("[Analyzer] Failed to parse JSON, using fallback")
            return self._fallback_suggestions(repo_name, all_issues_results, metadata_results)
        except Exception as e:
            logger.error(f"[Analyzer] Failed to generate suggestions: {e}")
            return self._fallback_suggestions(repo_name, all_issues_results, metadata_results)
    
    def _fallback_suggestions(self, repo_name: str, issues: List[Dict], metadata: List[Dict]) -> Dict:
        """Generate suggestions without LLM using search results."""
        return {
            "summary": f"Repository: {repo_name}. Found {len(issues)} open issues to analyze.",
            "beginner_friendly": [
                doc.get('metadata', {}).get('title', doc['content'][:80]) 
                for doc in issues[:4]
            ],
            "documentation": [],
            "bugs": [],
            "features": []
        }
    
    def get_issue_details(self, repo_name: str, issue_number: int) -> Optional[Dict]:
        """Get detailed information about a specific issue."""
        results = self.rag.search(
            query=f"Issue #{issue_number}",
            repo_name=repo_name,
            doc_type="issue",
            top_k=10
        )
        
        for doc in results:
            if doc.get('metadata', {}).get('number') == issue_number:
                return {
                    "content": doc['content'],
                    "metadata": doc['metadata']
                }
        
        return None

    def detect_tech_stack(self, repo_name: str) -> Dict:
        """
        Detect the technology stack of a repository.
        Returns technologies, languages, and frameworks.
        """
        # Get README and metadata
        readme_results = self.rag.search(
            query="dependencies requirements technology stack framework library",
            repo_name=repo_name,
            doc_type="readme",
            top_k=1
        )
        
        metadata_results = self.rag.search(
            query="language topics",
            repo_name=repo_name,
            doc_type="metadata",
            top_k=1
        )
        
        context = ""
        if readme_results:
            context += readme_results[0]['content'][:2000]
        if metadata_results:
            context += "\n" + metadata_results[0]['content'][:500]
        
        if not context:
            return {"languages": [], "frameworks": [], "tools": []}
        
        prompt = f"""Analyze this repository and extract the tech stack.

REPOSITORY INFO:
{context}

Return a JSON object with:
{{
    "languages": ["list", "of", "programming", "languages"],
    "frameworks": ["list", "of", "frameworks", "and", "libraries"],
    "tools": ["list", "of", "dev", "tools", "like", "docker", "webpack"]
}}

Only include technologies actually used. Return ONLY valid JSON."""

        try:
            response = self._generate(prompt, max_tokens=500)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"[Analyzer] Tech stack detection failed: {e}")
        
        return {"languages": [], "frameworks": [], "tools": []}

    def calculate_difficulty(self, issue_title: str, issue_body: str, labels: List[str]) -> Dict:
        """
        Calculate difficulty score for an issue.
        Returns score (1-10), time estimate, and required skills.
        """
        # Check for easy indicators in labels
        easy_labels = ['good first issue', 'beginner', 'easy', 'starter', 'help wanted']
        hard_labels = ['complex', 'hard', 'expert', 'breaking change', 'architecture']
        
        base_score = 5
        
        for label in labels:
            label_lower = label.lower()
            if any(easy in label_lower for easy in easy_labels):
                base_score -= 2
            if any(hard in label_lower for hard in hard_labels):
                base_score += 2
        
        # Estimate based on content length
        content_length = len(issue_title) + len(issue_body)
        if content_length < 200:
            base_score -= 1  # Short issues often simpler
        elif content_length > 1000:
            base_score += 1  # Long issues often complex
        
        # Clamp score
        score = max(1, min(10, base_score))
        
        # Time estimate mapping
        time_map = {
            1: "30 mins", 2: "1 hour", 3: "2 hours",
            4: "3 hours", 5: "4 hours", 6: "6 hours",
            7: "8 hours", 8: "1-2 days", 9: "2-3 days", 10: "1 week+"
        }
        
        # Extract skills using LLM
        prompt = f"""Analyze this issue and list 2-4 skills needed to solve it.

ISSUE: {issue_title}
{issue_body[:500]}

Return a JSON array of skill names only: ["skill1", "skill2"]"""

        skills = []
        try:
            response = self._generate(prompt, max_tokens=100)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                skills = json.loads(json_match.group())[:4]
        except Exception:
            pass
        
        return {
            "score": score,
            "time_estimate": time_map.get(score, "Unknown"),
            "required_skills": skills,
            "level": "Beginner" if score <= 3 else "Intermediate" if score <= 6 else "Advanced"
        }

    def find_relevant_files(self, repo_name: str, issue_title: str, issue_body: str) -> List[Dict]:
        """
        Find files most relevant to solving an issue.
        Uses RAG to locate where changes might be needed.
        """
        query = f"{issue_title} {issue_body[:300]}"
        
        # Search for related content
        results = self.rag.search(
            query=query,
            repo_name=repo_name,
            top_k=5
        )
        
        # Extract file references from results
        files = []
        seen = set()
        
        for doc in results:
            # Try to extract file paths from content
            content = doc.get('content', '')
            
            # Look for file path patterns
            file_patterns = re.findall(r'(?:src|lib|app|components?|pages?)/[\w/.-]+\.(?:js|jsx|ts|tsx|py|go|rs|java|rb)', content)
            
            for fp in file_patterns[:2]:
                if fp not in seen:
                    seen.add(fp)
                    files.append({
                        "path": fp,
                        "confidence": round(doc['score'], 2),
                        "reason": f"Related to: {doc['type']}"
                    })
        
        # If no specific files found, use LLM to guess
        if not files and results:
            prompt = f"""Based on this issue, what files might need to be modified?

ISSUE: {issue_title}
{issue_body[:400]}

Return a JSON array of likely file paths: ["path/to/file1.js", "path/to/file2.py"]
Only suggest 2-4 files. Return ONLY valid JSON array."""

            try:
                response = self._generate(prompt, max_tokens=200)
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    paths = json.loads(json_match.group())[:4]
                    files = [{"path": p, "confidence": 0.5, "reason": "AI suggested"} for p in paths]
            except Exception:
                pass
        
        return files[:5]

    def extract_setup_instructions(self, repo_name: str) -> Dict:
        """
        Extract setup instructions from README.
        Returns step-by-step setup guide.
        """
        readme_results = self.rag.search(
            query="install setup run development environment requirements getting started",
            repo_name=repo_name,
            doc_type="readme",
            top_k=1
        )
        
        if not readme_results:
            return {
                "steps": [],
                "requirements": [],
                "commands": []
            }
        
        readme_content = readme_results[0]['content'][:3000]
        
        prompt = f"""Extract the setup instructions from this README.

README:
{readme_content}

Return a JSON object with:
{{
    "requirements": ["list", "of", "prerequisites", "like", "Node 18+", "Python 3.8+"],
    "steps": ["Step 1: Clone the repo", "Step 2: Install dependencies", "Step 3: Run the app"],
    "commands": ["npm install", "npm run dev"]
}}

Be specific. Return ONLY valid JSON."""

        try:
            response = self._generate(prompt, max_tokens=800)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"[Analyzer] Setup extraction failed: {e}")
        
        return {
            "steps": ["Check the README for setup instructions"],
            "requirements": [],
            "commands": []
        }

    def analyze_issue_skills(self, issue_title: str, issue_body: str, labels: List[str], language: str) -> Dict:
        """
        Analyze an issue to extract required skills and calculate match score.
        Returns skills needed and a complexity assessment.
        """
        labels_text = ", ".join(labels) if labels else "none"
        
        prompt = f"""Analyze this GitHub issue and identify specific technical skills required.

ISSUE TITLE: {issue_title}

ISSUE BODY:
{issue_body[:800]}

LABELS: {labels_text}
LANGUAGE: {language}

Return a JSON object with:
{{
    "skills": ["list", "of", "3-5", "specific", "skills"],
    "difficulty": "beginner" | "intermediate" | "advanced",
    "time_estimate": "30 mins" | "1-2 hours" | "half day" | "1 day" | "2+ days",
    "skill_level": 1-10,
    "summary": "One sentence describing what this issue needs"
}}

Be specific about skills (e.g., "React Hooks" not just "React", "REST API" not just "backend").
Return ONLY valid JSON."""

        try:
            response = self._generate(prompt, max_tokens=400)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                # Ensure all fields exist
                result.setdefault("skills", [language] if language else ["General"])
                result.setdefault("difficulty", "intermediate")
                result.setdefault("time_estimate", "1-2 hours")
                result.setdefault("skill_level", 5)
                result.setdefault("summary", issue_title[:100])
                return result
        except Exception as e:
            logger.warning(f"[Analyzer] Skill analysis failed: {e}")
        
        # Fallback based on labels
        return {
            "skills": [language] if language else ["General Programming"],
            "difficulty": "beginner" if any("beginner" in l.lower() or "easy" in l.lower() for l in labels) else "intermediate",
            "time_estimate": "1-2 hours",
            "skill_level": 4,
            "summary": issue_title[:100]
        }

    def mock_code_review(self, code: str, context: str = "", language: str = "python") -> Dict:
        """
        Simulate a senior maintainer code review.
        Provides structured feedback with blocking issues vs suggestions.
        """
        prompt = f"""You are a Senior Maintainer reviewing a pull request. Be helpful but thorough.

CONTEXT: {context if context else "A contributor is submitting this code for review."}

LANGUAGE: {language}

CODE TO REVIEW:
```{language}
{code[:3000]}
```

Provide a code review with:
1. CRITICAL issues (must fix before merge) - security, bugs, logic errors
2. SUGGESTIONS (optional improvements) - style, readability, best practices
3. POSITIVE feedback (what's good about this code)

Return a JSON object:
{{
    "verdict": "approve" | "request_changes" | "comment",
    "critical": [
        {{"line": "approximate line or code snippet", "issue": "description", "fix": "suggested fix"}}
    ],
    "suggestions": [
        {{"line": "code snippet", "suggestion": "improvement idea"}}
    ],
    "praise": ["list", "of", "positive", "aspects"],
    "summary": "Overall review summary in 1-2 sentences"
}}

Be constructive and educational. Explain WHY something is an issue.
Return ONLY valid JSON."""

        try:
            response = self._generate(prompt, max_tokens=1200)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                result.setdefault("verdict", "comment")
                result.setdefault("critical", [])
                result.setdefault("suggestions", [])
                result.setdefault("praise", [])
                result.setdefault("summary", "Review complete")
                return result
        except Exception as e:
            logger.error(f"[Analyzer] Code review failed: {e}")
        
        return {
            "verdict": "comment",
            "critical": [],
            "suggestions": [{"line": "general", "suggestion": "Unable to analyze code. Please try again."}],
            "praise": [],
            "summary": "Review could not be completed"
        }

    def calculate_warmth_score(self, repo_name: str, issues_data: List[Dict] = None) -> Dict:
        """
        Calculate maintainer warmth/friendliness score for a repository.
        Analyzes response patterns and sentiment.
        """
        # Get issues from RAG if not provided
        if not issues_data:
            results = self.rag.search(
                query="issue discussion maintainer response",
                repo_name=repo_name,
                doc_type="issue",
                top_k=10
            )
            if not results:
                return {
                    "score": 50,
                    "label": "Unknown",
                    "factors": {"data": "Insufficient data to calculate warmth score"}
                }
            issues_text = "\n".join([doc['content'][:300] for doc in results])
        else:
            issues_text = "\n".join([f"{d.get('title', '')} - {d.get('body', '')[:200]}" for d in issues_data[:10]])

        prompt = f"""Analyze these GitHub issue discussions to determine how welcoming this repository is to new contributors.

ISSUE DISCUSSIONS:
{issues_text[:2000]}

Rate the maintainer warmth/friendliness:

Return a JSON object:
{{
    "score": 0-100,
    "label": "Very Welcoming" | "Welcoming" | "Neutral" | "Strict" | "Not Recommended",
    "response_speed": "fast" | "moderate" | "slow",
    "factors": {{
        "positive": ["list", "of", "positive", "signs"],
        "negative": ["list", "of", "concerning", "signs"]
    }},
    "recommendation": "One sentence advice for new contributors"
}}

Consider: response time patterns, tone of comments, helpfulness, patience with beginners.
Return ONLY valid JSON."""

        try:
            response = self._generate(prompt, max_tokens=500)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                result.setdefault("score", 50)
                result.setdefault("label", "Unknown")
                return result
        except Exception as e:
            logger.warning(f"[Analyzer] Warmth score failed: {e}")
        
        return {
            "score": 50,
            "label": "Unknown",
            "response_speed": "moderate",
            "factors": {"positive": [], "negative": []},
            "recommendation": "Check the repository's contribution guidelines"
        }
