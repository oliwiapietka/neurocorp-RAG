import logging
from typing import List, Optional
from qdrant_client import models
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Service responsible for managing interactions with the Qdrant vector database,
    including collection management, data upserts, and hybrid search operations.
    """    
    def __init__(self, client: AsyncQdrantClient):
        self.client = client
        self.text_collection = settings.COLLECTION_NAME
        self.vision_collection = settings.VISION_COLLECTION
        self.global_id = settings.GLOBAL_ID

    async def ensure_collections(self, text_dim: int, vision_dim: int):
        """Creates collections if they don't exist."""
        configs = {
            self.text_collection: {
                "vectors_config": {
                    "dense": models.VectorParams(size=text_dim, distance=models.Distance.COSINE)
                },
                "sparse_vectors_config": {
                    "sparse": models.SparseVectorParams(index=models.SparseIndexParams())
                }
            },
            self.vision_collection: {
                "vectors_config": {
                    "image": models.VectorParams(size=vision_dim, distance=models.Distance.COSINE),
                    "text": models.VectorParams(size=text_dim, distance=models.Distance.COSINE)
                }
            }
        }

        for name, config in configs.items():
            if not await self.client.collection_exists(name):
                await self.client.create_collection(collection_name=name, **config)
                logger.info(f"Created Qdrant collection: {name}")

    async def upsert(self, collection_name: str, points: List[models.PointStruct], batch_size: int = 64):
        """
        Performs a batched upsert of data points into a specified collection
        to optimize network I/O and prevent timeouts.
        """
        if not points:
            return
        
        # Simple batching generator
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await self.client.upsert(collection_name, batch)

    async def query_hybrid(self, 
                           collection_name: str, 
                           prefetch_params: List[models.Prefetch], 
                           session_id: str, 
                           limit: int) -> List[models.ScoredPoint]:
        """
        Executes a hybrid search using Reciprocal Rank Fusion (RRF).
        Filters results to include both session-specific data and global knowledge base entries.
        """
        
        should_filter = [
            models.FieldCondition(key="session_id", match=models.MatchValue(value=session_id)),
            models.FieldCondition(key="session_id", match=models.MatchValue(value=self.global_id))
        ]

        hits = await self.client.query_points(
            collection_name=collection_name,
            prefetch=prefetch_params,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=models.Filter(should=should_filter),
            limit=limit
        )
        return hits.points if hits.points else []

    async def scroll_by_id(self, collection_name: str, key: str, value: str) -> Optional[models.PointStruct]:
        """Helper to fetch metadata by a specific field ID."""
        result = await self.client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key=key, match=models.MatchValue(value=value))]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        if result and result[0]:
            return result[0][0]
        return None

    async def clear_collections(self):
        """Deletes collections."""
        for coll in [self.text_collection, self.vision_collection]:
            try:
                await self.client.delete_collection(coll)
            except Exception:
                pass