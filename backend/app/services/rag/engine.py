import os
import logging
import concurrent.futures
from typing import List, Dict

from qdrant_client.async_qdrant_client import AsyncQdrantClient
from app.core.config import settings

from .factory import model_factory
from .processor import DocumentProcessor
from .vector_store import VectorStoreService
from .storage import StorageService
from .ingestion import IngestionPipeline
from .retrieval import RetrievalService
from .models.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Hybrid RAG Engine.
    Orchestrates specialized services for Ingestion, Storage, and Retrieval,
    providing a unified facade for multimodal document processing.
    """

    def __init__(self):
        # 1. Shared Resources init
        self.qdrant_client = AsyncQdrantClient(url=settings.QDRANT_URL)
        
        max_workers = max(2, (os.cpu_count() or 2) - 1)
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="rag_worker"
        )

        # 2. Services Initialization
        self.vector_store = VectorStoreService(self.qdrant_client)
        self.storage = StorageService(self.executor)
        self.processor = DocumentProcessor()
        
        self.embedder = EmbeddingService(model_factory, self.executor)
        
        self.ingestion = IngestionPipeline(
            vector_store=self.vector_store,
            storage=self.storage,
            embedding_service=self.embedder,
            processor=self.processor,
            executor=self.executor
        )
        
        self.retrieval = RetrievalService(
            vector_store=self.vector_store,
            embedding_service=self.embedder,
            model_factory=model_factory,
            executor=self.executor
        )

        logger.info(f"RAGEngine initialized with {max_workers} workers.")

    async def initialize(self):
        """
        Performs dynamic initialization of the Vector Database schema.
        Detects vector dimensions directly from loaded models to ensure 
        compatibility between the embedders and the database collections.
        """
        try:
            # 1. TEXT DIMENSION
            text_dim = 384 # fallback
            val_t = None
            
            if hasattr(model_factory.dense, 'get_sentence_embedding_dimension'):
                val_t = model_factory.dense.get_sentence_embedding_dimension()
            
            if isinstance(val_t, int):
                text_dim = val_t

            # 2. VISION DIMENSION
            vision_dim = 512 # fallback
            val_v = None

            if hasattr(model_factory.vision, 'get_sentence_embedding_dimension'):
                val_v = model_factory.vision.get_sentence_embedding_dimension()
            
            if val_v is None and hasattr(model_factory.vision, '_first_module'):
                try:
                    module = model_factory.vision._first_module()
                    if hasattr(module, 'get_sentence_embedding_dimension'):
                        val_v = module.get_sentence_embedding_dimension()
                except Exception:
                    pass

            if isinstance(val_v, int):
                vision_dim = val_v
            
            if vision_dim is None:
                logger.warning("Vision dimension detection returned None. Forcing default 512.")
                vision_dim = 512

            logger.info(f"Auto-Config: Text Dim: {text_dim}, Vision Dim: {vision_dim}")
            
            await self.vector_store.ensure_collections(text_dim, vision_dim)
            
        except Exception as e:
            logger.critical(f" RAGEngine Init Failed: {e}")
            raise RuntimeError(f"Critical: Vector DB initialization failed due to: {e}")
        
    async def shutdown(self):
        """Clean shutdown."""
        self.executor.shutdown(wait=False)
        await self.qdrant_client.close()

    # Facade Methods

    async def index_documents(self, file_data: List[Dict], session_id: str):
        return await self.ingestion.run(file_data, session_id)

    async def add_to_global_store(self, file_data: List[Dict]):
        return await self.ingestion.run(file_data, settings.GLOBAL_ID)

    async def search(self, query: str, session_id: str):
        return await self.retrieval.search_text(query, session_id)

    async def search_vision(self, query: str, session_id: str, limit: int = 3):
        return await self.retrieval.search_vision(query, session_id, limit)

    async def get_image_metadata(self, image_uuid: str):
        return await self.retrieval.get_image_metadata(image_uuid)

    async def clear_database(self):
        await self.vector_store.clear_collections()
        await self.initialize()