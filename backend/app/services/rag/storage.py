import io
import uuid
import os
import logging
import asyncio
from typing import Dict
from PIL import Image
from fastapi import UploadFile
from app.database import db_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """
    Service responsible for File I/O operations, managing storage 
    between GridFS (MongoDB) and the local disk.
    """

    def __init__(self, executor):
        self.executor = executor

    async def download_file(self, safe_name: str, destination_path: str):
        """Downloads file from GridFS to local path."""
        grid_out = await db_manager.fs.open_download_stream_by_name(safe_name)
        with open(destination_path, "wb") as f:
            async for chunk in grid_out:
                f.write(chunk)

    async def upload_image(self, image: Image.Image, filename: str, metadata: Dict):
        """Compresses and uploads image to GridFS."""
        def _compress():
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=settings.VLM_IMAGE_QUALITY)
            return buf.getvalue()

        try:
            img_bytes = await asyncio.get_running_loop().run_in_executor(
                self.executor, _compress
            )
            stream = db_manager.fs.open_upload_stream(filename, metadata=metadata)
            await stream.write(img_bytes)
            await stream.close()
        except Exception as e:
            logger.error(f"GridFS Upload Error for {filename}: {e}")

    async def save_upload_file(self, file: UploadFile) -> str:
        """
        Saves a file uploaded via the FastAPI endpoint (UploadFile) into GridFS.
        Generates a unique 'safe_name' using a UUID to prevent filename collisions.

        Returns:
            str: The unique safe_name used to retrieve the file later.
        """
        original_name = os.path.basename(file.filename)
        safe_name = f"{uuid.uuid4()}_{original_name}" 
        
        try:
            content = await file.read()
            
            gridin = db_manager.fs.open_upload_stream(
                safe_name,
                metadata={
                    "original_name": original_name, 
                    "content_type": file.content_type,
                    "purpose": "chat_attachment"
                }
            )
            await gridin.write(content)
            await gridin.close()
            return safe_name
        except Exception as e:
            logger.error(f" StorageService: Failed to save upload {original_name}: {e}")
            raise