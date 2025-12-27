import time
from typing import Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class UsageTracker:
    def __init__(self, location=":memory:"):
        """
        Initialize the UsageTracker with an in-memory Qdrant instance for MVP.
        In production, this would connect to a persistent Qdrant server.
        """
        self.client = QdrantClient(location=location)
        self._init_collections()

    def _init_collections(self):
        """Initialize necessary collections if they don't exist."""
        collections = self.client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "user_activity" not in collection_names:
            # For simple ID tracking, we can use a dummy vector or just payload
            # But Qdrant requires a vector config. We'll use size 1 for simplicity.
            self.client.create_collection(
                collection_name="user_activity",
                vectors_config=VectorParams(size=1, distance=Distance.DOT),
            )
        
        if "pr_rejections" not in collection_names:
            # This would likely store embeddings of rejection reasons in a real app
            # For MVP, we'll store basic text.
            self.client.create_collection(
                collection_name="pr_rejections",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE), # Assuming 384 dim model for future
            )

    def can_contribute(self, user_id: int) -> bool:
        """
        Check if the user is allowed to contribute (1 PR per 24 hours).
        """
        points = self.client.retrieve(
            collection_name="user_activity",
            ids=[user_id]
        )
        
        if not points:
            return True
            
        last_contribution = points[0].payload.get("last_contribution_ts", 0)
        current_time = time.time()
        
        # 24 hours in seconds = 86400
        return (current_time - last_contribution) > 86400

    def log_contribution(self, user_id: int):
        """
        Log a successful contribution attempt.
        """
        self.client.upsert(
            collection_name="user_activity",
            points=[
                PointStruct(
                    id=user_id,
                    vector=[1.0], # Dummy vector
                    payload={"last_contribution_ts": time.time()}
                )
            ]
        )

    def add_rejection(self, reason: str):
        """
        Store a rejection reason. 
        In a full implementation, this might embed the text. 
        For MVP, we just store it to show the structure.
        """
        # We simulate an ID and vector for now
        import uuid
        point_id = str(uuid.uuid4())
        
        # In a real app, compute embedding for 'reason'
        dummy_vector = [0.1] * 384 
        
        self.client.upsert(
            collection_name="pr_rejections",
            points=[
                PointStruct(
                    id=point_id,
                    vector=dummy_vector,
                    payload={"reason": reason}
                )
            ]
        )
