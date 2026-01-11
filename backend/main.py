import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.api import chat_router, admin_router, sessions_router
from app.database import db_manager
from app.services.rag import rag_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class UndefinedDetectorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect malformed requests containing 'undefined' in the URL or query.
    This helps catch frontend issues where an uninitialized state is sent to the API.
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        query_params = str(request.query_params)

        if ("undefined" in path.lower() or "undefined" in query_params.lower()) and request.method != "POST":
            logger.error(f"[FRONTEND BUG] Detected 'undefined' in request. Path: {path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Malformed Request",
                    "detail": "The value 'undefined' is not allowed in the URL. Please check frontend state initialization.",
                    "hint": f"You are requesting {path} without a valid session ID."
                }
            )

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(f"REQ: {request.method} {path} | STATUS: {response.status_code} | TIME: {process_time:.4f}s")
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context:
    - prepares directories
    - connects to MongoDB (GridFS and sessions)
    - initializes the RAG engine (models and Qdrant)
    - performs cleanup on shutdown
    """
    logger.info(f"Initializing {settings.PROJECT_NAME}...")

    # Ensure required folders exist
    settings.setup_app_directories()

    # Connect to MongoDB (GridFS and sessions collection)
    try:
        await db_manager.connect()
        logger.info("MongoDB: connection established.")
    except Exception as e:
        logger.critical(f"MongoDB: critical error during connection: {e}")
        raise SystemExit(1)

    # Initialize RAG engine (models, collections)
    try:
        await rag_engine.initialize()
        logger.info("RAGEngine: models and collections are ready.")
    except Exception as e:
        logger.critical(f"RAGEngine: initialization error: {e}")
        raise SystemExit(1)

    yield

    logger.info("Shutting down application and cleaning up resources...")
    await db_manager.close()

def create_app() -> FastAPI:
    """
    Factory that builds and configures the FastAPI application:
    - registers middleware
    - configures CORS
    - mounts API routers
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    # Register middleware
    application.add_middleware(UndefinedDetectorMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    application.include_router(
        chat_router,
        prefix=f"{settings.API_V1_STR}/chat",
        tags=["AI Engine"]
    )
    application.include_router(
        sessions_router,
        prefix=f"{settings.API_V1_STR}/sessions",
        tags=["History & Files"]
    )
    application.include_router(
        admin_router,
        prefix=f"{settings.API_V1_STR}/admin",
        tags=["Knowledge Base Admin"]
    )

    return application

app = create_app()

@app.get("/", tags=["Health"])
async def root():
    """Basic health/info endpoint."""
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple liveness endpoint used by monitoring systems."""
    return {"status": "healthy"}