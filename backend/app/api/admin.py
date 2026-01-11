import logging
import uuid
import asyncio
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.rag import rag_engine
from app.database import db_manager
from app.schemas.admin import IngestResponse, ClearDatabaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def save_admin_file(file: UploadFile) -> str:
    """Helper: save an admin-uploaded file to GridFS with metadata."""
    safe_name = f"global_{uuid.uuid4()}_{file.filename}"
    try:
        content = await file.read()
        grid_in = db_manager.fs.open_upload_stream(
            safe_name,
            metadata={
                "original_name": file.filename,
                "type": "global_knowledge",
                "uploaded_by": "admin"
            }
        )
        await grid_in.write(content)
        await grid_in.close()
        return safe_name
    except Exception as e:
        logger.error(f"GridFS admin save error: {e}")
        raise e

@router.post("/ingest", response_model=IngestResponse)
async def ingest_to_global_store(files: List[UploadFile] = File(...)):
    """Accept admin files and add them to the global NeuroCorp knowledge base."""
    try:
        # Parallel save of files to GridFS
        save_tasks = [save_admin_file(f) for f in files]
        safe_names = await asyncio.gather(*save_tasks)
        
        # Prepare payload for the RAG engine
        file_data = [
            {"safe_name": sn, "original_name": f.filename} 
            for sn, f in zip(safe_names, files)
        ]
        
        # Process documents (Docling -> Embeddings -> Qdrant)
        stats = await rag_engine.add_to_global_store(file_data)
        
        chunks = int(stats.get("chunks_added", 0))
        images = int(stats.get("images_added", 0))

        logger.info(f"Ingest success: {chunks} chunks and {images} images added.")
        
        return IngestResponse(
            files_processed=len(files),
            chunks_added=chunks,
            images_added=images,
            message="Global knowledge base has been updated."
        )        
    
    except Exception as e:
        logger.error(f"Ingest error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while processing documents: {str(e)}"
        )
    
@router.delete("/clear", response_model=ClearDatabaseResponse)
async def clear_database():
    """Completely clear the global knowledge base in Qdrant."""
    try:
        await rag_engine.clear_database()
        return ClearDatabaseResponse(
            status="success",
            message="Collections have been rebuilt. Schema issues should be resolved."
        )
    except Exception as e:
        logger.error(f"Clear database error: {e}")
        raise HTTPException(status_code=500, detail=f"Error while clearing the database: {str(e)}")