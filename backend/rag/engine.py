"""
RAG Engine - Advanced embedding and vector storage with HyDE and hybrid search.
"""
import os
import logging
import requests
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid

logger = logging.getLogger(__name__)


class RAGEngine:
    """Advanced RAG engine with HyDE, parent-document retrieval, and hybrid search."""
    
    COLLECTION_NAME = "repo_docs"
    EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension
    
    def __init__(self):
        logger.info("[RAG] Initializing embedding model...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info("[RAG] Connecting to Qdrant...")
        
        # Read Qdrant Cloud settings from environment
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if qdrant_url and qdrant_api_key:
            # Use Qdrant Cloud
            logger.info(f"[RAG] Using Qdrant Cloud: {qdrant_url[:50]}...")
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            # Fallback to in-memory for local development
            logger.info("[RAG] Using in-memory Qdrant (no QDRANT_URL set)")
            self.client = QdrantClient(location=":memory:")
        
        self._init_collection()
        
        # LLM config for HyDE
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        
        logger.info("[RAG] Engine initialized successfully!")
    
    def _init_collection(self):
        """Create the collection if it doesn't exist."""
        collections = self.client.get_collections()
        existing = [c.name for c in collections.collections]
        
        if self.COLLECTION_NAME not in existing:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"[RAG] Created collection: {self.COLLECTION_NAME}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embedder.encode(text, convert_to_numpy=True).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return self.embedder.encode(texts, convert_to_numpy=True).tolist()
    
    def _generate_hyde_document(self, query: str) -> str:
        """
        Generate a hypothetical document that would answer the query.
        This improves retrieval by matching against ideal answers, not just questions.
        """
        if not self.groq_key:
            return query  # Fallback to original query
        
        prompt = f"""Given this question about a GitHub repository, write a short paragraph (2-3 sentences) that would be a good answer. Be specific and technical.

Question: {query}

Answer:"""
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.3
                },
                timeout=10
            )
            
            if response.ok:
                answer = response.json()["choices"][0]["message"]["content"].strip()
                logger.info(f"[RAG] HyDE generated: {answer[:80]}...")
                return answer
        except Exception as e:
            logger.warning(f"[RAG] HyDE generation failed: {e}")
        
        return query
    
    def index_documents(self, repo_name: str, documents: List[Dict]) -> int:
        """Index documents into the vector store."""
        if not documents:
            return 0
        
        # Generate embeddings for all documents
        texts = [doc['content'] for doc in documents]
        embeddings = self.embed_batch(texts)
        
        # Create points for Qdrant
        points = []
        for doc, embedding in zip(documents, embeddings):
            point_id = str(uuid.uuid4())
            payload = {
                "repo_name": repo_name,
                "content": doc['content'],
                "doc_type": doc.get('type', 'unknown'),
                **doc.get('metadata', {})
            }
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        
        logger.info(f"[RAG] Indexed {len(points)} documents for {repo_name}")
        return len(points)
    
    def search(
        self, 
        query: str, 
        repo_name: Optional[str] = None, 
        top_k: int = 5,
        doc_type: Optional[str] = None,
        use_hyde: bool = False
    ) -> List[Dict]:
        """
        Semantic search for relevant documents.
        
        Args:
            query: Search query
            repo_name: Filter by repository
            top_k: Number of results
            doc_type: Filter by document type
            use_hyde: Use hypothetical document embeddings for better recall
        """
        # Apply HyDE if enabled
        search_text = query
        if use_hyde and len(query) > 20:
            search_text = self._generate_hyde_document(query)
        
        query_embedding = self.embed_text(search_text)
        
        # Build filter conditions
        filter_conditions = []
        if repo_name:
            filter_conditions.append(
                FieldCondition(key="repo_name", match=MatchValue(value=repo_name))
            )
        if doc_type:
            filter_conditions.append(
                FieldCondition(key="doc_type", match=MatchValue(value=doc_type))
            )
        
        search_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k
        )
        
        return [
            {
                "content": hit.payload.get("content", ""),
                "type": hit.payload.get("doc_type", "unknown"),
                "score": hit.score,
                "metadata": {k: v for k, v in hit.payload.items() 
                           if k not in ["content", "doc_type", "repo_name"]}
            }
            for hit in results
        ]
    
    def search_with_context(
        self,
        query: str,
        repo_name: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search with parent-document retrieval.
        When a section matches, also retrieves the full README for context.
        """
        # First, search for specific sections
        section_results = self.search(
            query=query,
            repo_name=repo_name,
            top_k=top_k,
            use_hyde=True
        )
        
        # Check if any result is a readme section
        has_readme_section = any(r['type'] == 'readme' for r in section_results)
        
        if has_readme_section:
            # Also fetch the full README for context
            full_readme = self.search(
                query="full readme overview",
                repo_name=repo_name,
                doc_type="readme_full",
                top_k=1
            )
            if full_readme:
                # Add as lower-scored context
                full_readme[0]['score'] = 0.5
                full_readme[0]['is_parent'] = True
                section_results.append(full_readme[0])
        
        return section_results
    
    def search_for_files(self, query: str, repo_name: str) -> List[Dict]:
        """
        Search specifically for file/directory recommendations.
        Uses the file_tree document type.
        """
        results = self.search(
            query=query,
            repo_name=repo_name,
            doc_type="file_tree",
            top_k=1
        )
        
        if not results:
            # Fallback: search README for file mentions
            results = self.search(
                query=f"files directories {query}",
                repo_name=repo_name,
                top_k=2
            )
        
        return results
    
    def delete_repo(self, repo_name: str) -> bool:
        """Delete all documents for a repository."""
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="repo_name", match=MatchValue(value=repo_name))]
            )
        )
        logger.info(f"[RAG] Deleted documents for {repo_name}")
        return True
    
    def get_indexed_repos(self) -> List[str]:
        """Get list of all indexed repository names."""
        results = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            limit=1000,
            with_payload=["repo_name"]
        )
        
        repos = set()
        for point in results[0]:
            if point.payload and "repo_name" in point.payload:
                repos.add(point.payload["repo_name"])
        
        return list(repos)
