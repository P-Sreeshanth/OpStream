import os
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debug: Print to verify env is loaded
print(f"[DEBUG] GITHUB_TOKEN loaded: {bool(os.getenv('GITHUB_TOKEN'))}")
print(f"[DEBUG] HF_TOKEN loaded: {bool(os.getenv('HUGGINGFACEHUB_API_TOKEN'))}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global references (initialized at startup)
rag_engine = None
fetcher = None
analyzer = None
gh_engine = None  # For issue search

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components at startup."""
    global rag_engine, fetcher, analyzer, gh_engine
    
    try:
        from backend.rag.engine import RAGEngine
        from backend.rag.fetcher import GitHubFetcher
        from backend.rag.analyzer import RepositoryAnalyzer
        from backend.tools.github_engine import GitHubEngine
        
        gh_engine = GitHubEngine()
        rag_engine = RAGEngine()
        fetcher = GitHubFetcher()
        analyzer = RepositoryAnalyzer(rag_engine)
        logger.info("All components initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        import traceback
        traceback.print_exc()
    
    yield  # App runs here
    
    # Cleanup (if needed)
    logger.info("Shutting down...")

app = FastAPI(title="Opstream API", lifespan=lifespan)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class IssueSearchRequest(BaseModel):
    limit: int = 10
    domain: Optional[str] = None  # react, python, ml, rust, go, etc.
    sort_by: str = "recent"  # recent or popular

class IndexRepoRequest(BaseModel):
    repo_url: str
    issue_limit: int = 50

class AnalyzeRequest(BaseModel):
    repo_name: str
    question: str

class SuggestRequest(BaseModel):
    repo_name: str

class IndexRepoResponse(BaseModel):
    status: str
    repo_name: str
    documents_indexed: int

class AnalyzeResponse(BaseModel):
    answer: str
    sources: List[dict]

class SuggestResponse(BaseModel):
    summary: str
    beginner_friendly: List[str]
    documentation: List[str]
    bugs: List[str]
    features: List[str]


# New request models for vision features
class IssueSkillsRequest(BaseModel):
    issue_title: str
    issue_body: str = ""
    labels: List[str] = []
    language: str = ""

class CodeReviewRequest(BaseModel):
    code: str
    context: str = ""
    language: str = "python"

class WarmthScoreRequest(BaseModel):
    repo_name: str


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "github_ready": gh_engine is not None,
        "rag_ready": rag_engine is not None,
        "analyzer_ready": analyzer is not None
    }


@app.get("/api/domains")
async def get_domains():
    """Get available domains for filtering issues."""
    return {
        "domains": [
            {"id": "react", "label": "React", "icon": "⚛️"},
            {"id": "python", "label": "Python", "icon": "🐍"},
            {"id": "machine-learning", "label": "Machine Learning", "icon": "🤖"},
            {"id": "javascript", "label": "JavaScript", "icon": "📜"},
            {"id": "typescript", "label": "TypeScript", "icon": "💎"},
            {"id": "rust", "label": "Rust", "icon": "🦀"},
            {"id": "go", "label": "Go", "icon": "🐹"},
            {"id": "java", "label": "Java", "icon": "☕"},
            {"id": "web", "label": "Web/Frontend", "icon": "🌐"},
            {"id": "backend", "label": "Backend/API", "icon": "⚙️"},
            {"id": "mobile", "label": "Mobile", "icon": "📱"},
            {"id": "devops", "label": "DevOps", "icon": "🚀"},
            {"id": "data", "label": "Data Science", "icon": "📊"},
        ]
    }


@app.post("/api/issues")
async def search_issues(request: IssueSearchRequest):
    """Search for good first issues with optional domain filtering."""
    if not gh_engine:
        raise HTTPException(status_code=503, detail="GitHub Engine unavailable. Check GITHUB_TOKEN.")
    
    try:
        issues = await asyncio.to_thread(
            gh_engine.search_issues, 
            limit=request.limit,
            domain=request.domain,
            sort_by=request.sort_by
        )
        return {"issues": issues, "domain": request.domain, "sort_by": request.sort_by}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/repos")
async def list_repos():
    """List all indexed repositories."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG Engine unavailable")
    
    try:
        repos = rag_engine.get_indexed_repos()
        return {"repos": repos}
    except Exception as e:
        logger.error(f"Failed to list repos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index-repo", response_model=IndexRepoResponse)
async def index_repository(request: IndexRepoRequest):
    """
    Index a GitHub repository into RAG.
    Fetches README, metadata, and issues.
    """
    if not rag_engine or not fetcher:
        raise HTTPException(status_code=503, detail="Services unavailable")
    
    try:
        # Fetch all data from the repository
        data = await asyncio.to_thread(
            fetcher.fetch_all,
            request.repo_url,
            request.issue_limit
        )
        
        repo_name = data["repo_name"]
        documents = data["documents"]
        
        if not documents:
            raise HTTPException(
                status_code=400, 
                detail="No data could be fetched from the repository"
            )
        
        # Delete existing data for this repo (re-index)
        await asyncio.to_thread(rag_engine.delete_repo, repo_name)
        
        # Index the documents
        count = await asyncio.to_thread(
            rag_engine.index_documents,
            repo_name,
            documents
        )
        
        return IndexRepoResponse(
            status="success",
            repo_name=repo_name,
            documents_indexed=count
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Index failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest):
    """
    Ask a question about an indexed repository.
    Uses RAG to retrieve relevant context and LLM to generate answer.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.analyze,
            request.repo_name,
            request.question
        )
        
        return AnalyzeResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggest", response_model=SuggestResponse)
async def suggest_contributions(request: SuggestRequest):
    """
    Get contribution suggestions for an indexed repository.
    Analyzes issues and suggests beginner-friendly tasks, bugs, features, etc.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.suggest_contributions,
            request.repo_name
        )
        
        return SuggestResponse(
            summary=result.get("summary", ""),
            beginner_friendly=result.get("beginner_friendly", []),
            documentation=result.get("documentation", []),
            bugs=result.get("bugs", []),
            features=result.get("features", [])
        )
        
    except Exception as e:
        logger.error(f"Suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/repos/{repo_owner}/{repo_name}")
async def delete_repository(repo_owner: str, repo_name: str):
    """Delete an indexed repository."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG Engine unavailable")
    
    try:
        full_name = f"{repo_owner}/{repo_name}"
        await asyncio.to_thread(rag_engine.delete_repo, full_name)
        return {"status": "deleted", "repo_name": full_name}
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# NEW VISION FEATURES
# ============================================

class TechStackRequest(BaseModel):
    repo_name: str

class DifficultyRequest(BaseModel):
    issue_title: str
    issue_body: str = ""
    labels: List[str] = []

class RelevantFilesRequest(BaseModel):
    repo_name: str
    issue_title: str
    issue_body: str = ""

class SetupRequest(BaseModel):
    repo_name: str


@app.post("/api/tech-stack")
async def get_tech_stack(request: TechStackRequest):
    """
    Detect the technology stack of a repository.
    Returns languages, frameworks, and tools used.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.detect_tech_stack,
            request.repo_name
        )
        return result
    except Exception as e:
        logger.error(f"Tech stack detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/difficulty")
async def calculate_difficulty(request: DifficultyRequest):
    """
    Calculate difficulty score for an issue.
    Returns score (1-10), time estimate, and required skills.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.calculate_difficulty,
            request.issue_title,
            request.issue_body,
            request.labels
        )
        return result
    except Exception as e:
        logger.error(f"Difficulty calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/relevant-files")
async def find_relevant_files(request: RelevantFilesRequest):
    """
    Find files most relevant to solving an issue.
    Uses RAG + LLM to locate where changes might be needed.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.find_relevant_files,
            request.repo_name,
            request.issue_title,
            request.issue_body
        )
        return {"files": result}
    except Exception as e:
        logger.error(f"File finding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/setup")
async def get_setup_instructions(request: SetupRequest):
    """
    Extract setup instructions from repository README.
    Returns requirements, steps, and commands.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.extract_setup_instructions,
            request.repo_name
        )
        return result
    except Exception as e:
        logger.error(f"Setup extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AGENTIC MENTORSHIP FEATURES
# ============================================

@app.post("/api/issue-skills")
async def analyze_issue_skills(request: IssueSkillsRequest):
    """
    Analyze an issue to extract required skills.
    Returns skills needed, difficulty, time estimate.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.analyze_issue_skills,
            request.issue_title,
            request.issue_body,
            request.labels,
            request.language
        )
        return result
    except Exception as e:
        logger.error(f"Skill analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code-review")
async def mock_code_review(request: CodeReviewRequest):
    """
    Simulate a senior maintainer code review.
    Returns structured feedback: critical issues, suggestions, praise.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.mock_code_review,
            request.code,
            request.context,
            request.language
        )
        return result
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/warmth-score")
async def get_warmth_score(request: WarmthScoreRequest):
    """
    Calculate maintainer warmth/friendliness score.
    Returns score (0-100), label, and factors.
    """
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer unavailable")
    
    try:
        result = await asyncio.to_thread(
            analyzer.calculate_warmth_score,
            request.repo_name
        )
        return result
    except Exception as e:
        logger.error(f"Warmth score failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
