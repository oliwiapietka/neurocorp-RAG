import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from bson import ObjectId
from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Infrastructure: manage database connection and resources."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.sessions = None
        self.fs: Optional[AsyncIOMotorGridFSBucket] = None

    async def connect(self):
        """Initialize connection with error handling and index creation."""
        if self.client:
            return

        try:
            self.client = AsyncIOMotorClient(
                settings.MONGO_URL,
                maxPoolSize=10,
                minPoolSize=2
            )
            
            db_name = getattr(settings, "MONGO_DB_NAME", "neurocorp_chat")
            self.db = self.client[db_name]
            
            self.sessions = self.db["sessions"]
            self.fs = AsyncIOMotorGridFSBucket(self.db)
            
            await self.sessions.create_index("session_id", unique=True)
            await self.sessions.create_index("last_update")
            
            logger.info(f"MongoDB: Connected to '{db_name}' and indexes verified.")
        except Exception as e:
            logger.error(f"MongoDB Connection Error: {e}")
            raise

    async def close(self):
        """Safely close database resources."""
        if self.client:
            self.client.close()
            logger.info("MongoDB: Connection closed.")

# Global instance (Manager)
db_manager = MongoDBManager()

# REPOSITORY PATTERN (DAL)

class SessionRepository:
    """Business logic: operations on sessions and messages."""

    @staticmethod
    def _map_id(doc: Optional[Dict]) -> Optional[Dict]:
        """Convert ObjectId to string for the frontend."""
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_history(self, session_id: str, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve message history.

        :param session_id: Session identifier
        :param limit: 0 = fetch all (for UI), >0 = fetch last N messages (for LLM context)
        """
        if not session_id or session_id in ["null", "undefined"]:
            return []
        
        projection = {"messages": {"$slice": -limit}} if limit > 0 else {"messages": 1}

        doc = await db_manager.sessions.find_one(
            {"session_id": session_id}, 
            projection
        )
        return doc.get("messages", []) if doc else []

    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        attachments: Optional[List[Dict]] = None,
        citations: Optional[List[Dict]] = None
    ):
        """Add a message and intelligently update session metadata."""
        if not session_id or session_id in ["null", "undefined"]:
            return

        now = datetime.now(timezone.utc)
        message_doc = {
            "role": role,
            "content": content,
            "timestamp": now,
            "attachments": attachments or [],
            "citations": citations or []
        }

        # Update operation
        update_op = {
            "$push": {"messages": message_doc},
            "$set": {"last_update": now}
        }

        # Generate title only on document creation
        if role == "user":
            auto_title = content[:40] + "..." if len(content) > 40 else content
            update_op["$setOnInsert"] = {
                "created_at": now,
                "title": auto_title,
                "session_id": session_id
            }

        await db_manager.sessions.update_one(
            {"session_id": session_id},
            update_op,
            upsert=True
        )

    async def get_all_sessions(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve a list of sessions with pagination.

        :param skip: number of sessions to skip (offset)
        :param limit: number of sessions to return (page size)
        """
        cursor = db_manager.sessions.find(
            {}, 
            {"messages": 0}  # Projection: do not fetch conversation contents, only metadata
        ).sort("last_update", -1).skip(skip).limit(limit)
        
        raw = await cursor.to_list(length=limit)
        return [self._map_id(s) for s in raw]

    async def delete_session(self, session_id: str):
        """Delete a session and any associated files stored in GridFS."""
        
        # Find session to identify files to delete
        session = await db_manager.sessions.find_one(
            {"session_id": session_id},
            {"messages.attachments": 1}
        )

        if session:
            messages = session.get("messages", [])
            file_ids_to_delete = []

            for msg in messages:
                for attachment in msg.get("attachments", []):
                    f_id = attachment.get("file_id")
                    if f_id:
                        try:
                            file_ids_to_delete.append(ObjectId(f_id))
                        except Exception:
                            pass

            # Deleting files from GridFS
            for fid in file_ids_to_delete:
                try:
                    await db_manager.fs.delete(fid)
                except Exception as e:
                    logger.warning(f" GridFS delete error for {fid}: {e}")

        result = await db_manager.sessions.delete_one({"session_id": session_id})
        logger.info(f" Deleted session {session_id}. Removed files: {result.deleted_count}")

    async def update_title(self, session_id: str, new_title: str):
        """Aktualizuje tytuł rozmowy."""
        await db_manager.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"title": new_title}}
        )

session_repo = SessionRepository()