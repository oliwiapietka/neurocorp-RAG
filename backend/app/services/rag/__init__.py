from .engine import RAGEngine

# module-level singleton used by the application lifecycle (initialized on import)
rag_engine = RAGEngine()

__all__ = ["RAGEngine", "rag_engine"]