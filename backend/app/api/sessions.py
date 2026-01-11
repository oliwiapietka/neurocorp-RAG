import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.database.session_db import session_repo, db_manager
from app.schemas.sessions import SessionCreate, SessionUpdate, SessionHeader, SessionDetail
import mimetypes

from urllib.parse import unquote

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[SessionHeader])
async def get_sessions():
    """Return a list of all sessions (metadata only, message history excluded for performance)."""
    return await session_repo.get_all_sessions()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_session(data: SessionCreate):
    """Create a new session in the database."""
    if data.session_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid session ID.")
    
    await session_repo.add_message(
        session_id=data.session_id,
        role="system",
        content=""
    )

    final_title = data.title if data.title and data.title.strip() else "New Chat"

    await session_repo.update_title(data.session_id, final_title)
    
    return {
        "message": "Session created", 
        "session_id": data.session_id, 
        "title": final_title
    }

@router.get("/{session_id}", response_model=SessionDetail)
async def get_single_session(session_id: str):
    """Retrieve full data for a specific session."""
    session = await session_repo.get_history(session_id)
    full_session = await db_manager.sessions.find_one({"session_id": session_id})
    if not full_session:
        raise HTTPException(status_code=404, detail="Session does not exist.")
    
    full_session["_id"] = str(full_session["_id"])
    return full_session

@router.patch("/{session_id}")
async def update_session(session_id: str, data: SessionUpdate):
    """Update the session title."""
    await session_repo.update_title(session_id, data.title)
    return {"message": "Title updated"}

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session from the database."""
    await session_repo.delete_session(session_id)
    return {"message": "Session deleted"}

@router.get("/download/{uuid_filename}")
async def download_file(uuid_filename: str):
    """Download a file from GridFS; resilient to frontend errors and memory-efficient."""
    try:
        # cleaning filename
        decoded_name = unquote(uuid_filename)
        clean_name = decoded_name.strip("{} ").replace("%7B", "").replace("%7D", "")
        
        try:
            grid_out = await db_manager.fs.open_download_stream_by_name(clean_name)
        except Exception:
            raise HTTPException(status_code=404, detail=f"No file named: {clean_name}.")

        # determine content type
        content_type, _ = mimetypes.guess_type(clean_name)
        content_type = content_type or "application/octet-stream"

        return StreamingResponse(
            grid_out,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={clean_name}",
                "Cache-Control": "public, max-age=31536000"
            }
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Critical error downloading {uuid_filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error during file download.")