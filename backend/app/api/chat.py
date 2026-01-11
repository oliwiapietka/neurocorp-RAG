import logging
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form

from app.database import db_manager
from app.schemas.chat import ChatResponse
from app.schemas.admin import IngestResponse
from app.services.orchestrator import ChatOrchestrator
from app.services.rag import rag_engine 
from app.services.agent_service import agent_service
from app.services.web_search import web_search_service 

logger = logging.getLogger(__name__)

router = APIRouter()

def get_orchestrator() -> ChatOrchestrator:
    """Inject the assembled orchestrator after validating the RAG engine state."""
    if not rag_engine:
        logger.error("RAGEngine not initialized")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI engine is not ready."
        )
    return ChatOrchestrator(
        rag_engine=rag_engine, 
        agent_service=agent_service, 
        web_search_service=web_search_service
    )

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(
    files: List[UploadFile] = File(...)
):
    """
    Endpoint to index documents into the global knowledge base.
    """
    try:
        # Save files to GridFS
        file_data = []
        for file in files:
            safe_name = f"global_{uuid.uuid4()}_{file.filename}"
            content = await file.read()
            
            grid_in = db_manager.fs.open_upload_stream(
                safe_name,
                metadata={
                    "original_name": file.filename, 
                    "purpose": "global_knowledge"
                }
            )
            await grid_in.write(content)
            await grid_in.close()
            
            file_data.append({"safe_name": safe_name, "original_name": file.filename})
            logger.info(f"Saved {file.filename} to GridFS")

        logger.info(f"Starting RAG indexing for {len(files)} files...")
        stats = await rag_engine.add_to_global_store(file_data)
        
        logger.info(f"Stats type: {type(stats)}, value: {stats}")
        
        if not isinstance(stats, dict):
            logger.error(f"RAG returned invalid type: {type(stats)}")
            raise ValueError(f"Expected dict from RAG engine, got {type(stats)}")
        
        chunks = int(stats.get("chunks_added", 0))
        images = int(stats.get("images_added", 0))
        
        logger.info(f"Ingest complete: {chunks} chunks, {images} images added.")

        return IngestResponse(
            message=f"Successfully indexed {len(files)} files.",
            chunks_added=chunks,
            images_added=images,
            files_processed=len(files)
        )

    except Exception as e:
        logger.error(f"Ingest Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")
    

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    message: str = Form(..., min_length=1),
    session_id: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    orch: ChatOrchestrator = Depends(get_orchestrator)
):
    """Standard JSON response endpoint (RAG + Web Search + AI Agent)."""
    try:
        return await orch.process_chat(session_id, message, files)
    except Exception as e:
        logger.error(f"Chat Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing the message.")