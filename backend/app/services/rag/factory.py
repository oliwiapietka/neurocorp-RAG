import logging
import torch
from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer, CrossEncoder
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelFactory:
    """
    Singleton factory for centralizing the initialization and management of 
    Machine Learning models, including Dense, Sparse, Vision, and Reranking models.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelFactory, cls).__new__(cls)
            cls._instance._init_models()
        return cls._instance
    
    def _create_text_splitter(self):
        """
        Initializes the RecursiveCharacterTextSplitter with validation logic
        to ensure chunk overlap does not exceed chunk size.
        """
        c_size = settings.CHUNK_SIZE
        c_overlap = settings.CHUNK_OVERLAP
        
        # Safety check for configuration
        if c_overlap >= c_size:
            logger.warning(f"Overlap ({c_overlap}) is too high for chunk size ({c_size}). Adjusting to 20%.")
            c_overlap = int(c_size * 0.2)

        return RecursiveCharacterTextSplitter(
            chunk_size=c_size,
            chunk_overlap=c_overlap,
            separators=["\n", ". ", " ", ""],
            length_function=len
        )

    def _init_models(self):
        """
        Loads all required RAG models into memory. Models are allocated to GPU (CUDA) 
        if available, otherwise fallback to CPU is utilized.
        """
        logger.info("Loading RAG models...")
        self.text_splitter = self._create_text_splitter()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Inference Device: {self.device}")
        
        # 1. Local Embedding Models
        # Dense (Text)
        self.dense = SentenceTransformer(settings.DENSE_MODEL, device=self.device)
        
        # Vision (CLIP/SigLIP)
        self.vision = SentenceTransformer(settings.VISION_EMBED_MODEL, device=self.device)
        
        # Sparse (SPLADE/BM25)
        self.sparse = SparseTextEmbedding(model_name=settings.SPARSE_MODEL)
        
        # Reranker (Cross-Encoder)
        self.reranker = CrossEncoder(settings.RERANKER_MODEL, device=self.device)

        # 2. Cloud Vision LLM (Groq)
        # Dedicated VLM for image captioning and visual data interpretation
        self.vision_llm = ChatGroq(
            model_name=settings.GROQ_VISION_MODEL,
            groq_api_key=settings.GROQ_API_KEY.get_secret_value(),
            temperature=0.0,
            max_retries=2
        )
        logger.info("All RAG models loaded successfully.")

# Global singleton instance
model_factory = ModelFactory()