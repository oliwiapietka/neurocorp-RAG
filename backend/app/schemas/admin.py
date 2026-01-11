from pydantic import BaseModel

class IngestResponse(BaseModel):
    """Result of ingesting documents into the global knowledge base."""
    message: str
    chunks_added: int
    images_added: int
    files_processed: int


class ClearDatabaseResponse(BaseModel):
    """Response status after clearing the knowledge base."""
    status: str
    message: str