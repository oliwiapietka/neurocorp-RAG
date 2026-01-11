import logging
from typing import Dict, Any
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client import models
from app.core.config import settings

logger = logging.getLogger(__name__)

class QdrantManager:
    """
    Manager for Qdrant client and collection lifecycle.

    Provides utilities to create collections with appropriate vector
    configurations based on loaded model dimensions, delete collections,
    and close the client connection.
    """

    def __init__(self, url: str = settings.QDRANT_URL):
        """Initialize the async Qdrant client and collection names."""
        self.client = AsyncQdrantClient(url=url)
        self.collection_name = settings.COLLECTION_NAME
        self.vision_collection = settings.VISION_COLLECTION

    async def close(self):
        """Close the Qdrant client connection."""
        await self.client.close()

    async def get_or_create_collections(self, models_factory):
        """
        Ensure required collections exist with correct vector configurations.

        The method inspects the loaded embedding models to determine
        vector dimensions and creates collections if they do not exist.
        Raises RuntimeError on failure.
        """
        try:
            # Detect vector dimensions from loaded models
            text_dim = self._detect_dimension(models_factory.dense, default=384)
            vision_dim = self._detect_dimension(models_factory.vision, default=512)

            logger.info(f"Qdrant initialization: text_dim={text_dim}, vision_dim={vision_dim}")

            # Collection configurations
            configs = {
                self.collection_name: self._get_text_collection_config(text_dim),
                self.vision_collection: self._get_vision_collection_config(text_dim, vision_dim)
            }

            # Create collections if missing
            for name, config in configs.items():
                if not await self.client.collection_exists(name):
                    await self.client.create_collection(collection_name=name, **config)
                    logger.info(f"Created collection: {name}")
                else:
                    logger.debug(f"Collection {name} already exists.")

        except Exception as e:
            logger.critical(f"Qdrant initialization failed: {e}")
            raise RuntimeError(f"Could not initialize vector DB: {e}")

    async def delete_all_collections(self):
        """Delete configured collections (hard reset)."""
        for name in [self.collection_name, self.vision_collection]:
            try:
                await self.client.delete_collection(name)
                logger.warning(f"Deleted collection: {name}")
            except Exception as e:
                logger.error(f"Error deleting collection {name}: {e}")

    def _detect_dimension(self, model, default: int) -> int:
        """
        Detect embedding vector dimension from a SentenceTransformer-like model.

        Falls back to `default` if detection fails.
        """
        if hasattr(model, 'get_sentence_embedding_dimension'):
            val = model.get_sentence_embedding_dimension()
            return val if isinstance(val, int) else default
        # Fallback for some CLIP wrappers
        try:
            if hasattr(model, '_first_module'):
                return model._first_module().get_sentence_embedding_dimension()
        except Exception:
            pass
        return default

    def _get_text_collection_config(self, dim: int) -> Dict[str, Any]:
        """Return configuration dict for the main text collection (hybrid search)."""
        return {
            "vectors_config": {
                "dense": models.VectorParams(size=dim, distance=models.Distance.COSINE)
            },
            "sparse_vectors_config": {
                "sparse": models.SparseVectorParams(index=models.SparseIndexParams())
            }
        }

    def _get_vision_collection_config(self, text_dim: int, vision_dim: int) -> Dict[str, Any]:
        """Return configuration dict for the multimodal (vision) collection."""
        return {
            "vectors_config": {
                "image": models.VectorParams(size=vision_dim, distance=models.Distance.COSINE),
                "text": models.VectorParams(size=text_dim, distance=models.Distance.COSINE)
            }
        }