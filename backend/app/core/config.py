from pathlib import Path
from typing import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # PROJECT AND ENV
    PROJECT_NAME: str = "NeuroCorp RAG Service"
    API_V1_STR: str = "/api/v1"

    HF_TOKEN: Optional[SecretStr] = None 
    
    DEVICE: Optional[str] = Field(default=None)

    # DATABASE
    MONGO_URL: str = Field(default="mongodb://localhost:27017")
    QDRANT_URL: str = Field(default="http://localhost:6333")
    MONGO_DB_NAME: str = "neurocorp_chat"

    # API KEYS
    GROQ_API_KEY: SecretStr
    TAVILY_API_KEY: Optional[SecretStr] = None

    MODEL_NAME: str = "llama-3.3-70b-versatile"

    # QDRANT COLLECTIONS
    COLLECTION_NAME: str = "neurocorp_v1"
    VISION_COLLECTION: str = "neurocorp_vision"
    GLOBAL_ID: str = "global_knowledge_base"

    # RAG Tuning
    TEXT_RETRIEVAL_WINDOW: int = 150
    VISION_RETRIEVAL_WINDOW: int = 80

    # RAG HYPERPARAMETERS
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 400

    # EMBEDDING MODELS
    DENSE_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPARSE_MODEL: str = "Qdrant/bm42-all-minilm-l6-v2-attentions"
    VISION_EMBED_MODEL: str = "sentence-transformers/clip-ViT-B-32"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # LLM MODELS
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    MAX_WEB_RESULTS: int = 3
    MAX_CONTEXT_LEN: int = 1000
    VISION_LIMIT_IMAGE: int = 50
    VISION_LIMIT_TEXT: int = 50
    VLM_IMAGE_QUALITY: int = 85
    RERANK_BATCH_SIZE: int = 16

    # Infrastructure
    INGESTION_SEMAPHORE: int = 3
    TEXT_BATCH_SIZE: int = 64
    VISION_BATCH_SIZE: int = 16


    UPLOAD_DIR: Path = BASE_DIR / "temp_uploads"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def setup_app_directories(self):
        """Create necessary directories on startup."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()