from pydantic import BaseModel, Field
from typing import List, Optional

class SourceMetadata(BaseModel):
    id: int                     
    filename: str               
    uuid_name: str              
    page: Optional[int] = 0     
    snippet: str
    is_global: bool = False     
    type: str # "db" | "web"
    related_images: List[str] = [] 
    score: Optional[float] = None  
    context_info: Optional[str] = None
    url: Optional[str] = None

class ImageResult(BaseModel):
    """Schema for images/tables extracted from documents."""
    uuid_name: str      
    original_doc: str   
    score: float        
    reason: Optional[str] = "semantic_match" # 'semantic_match' (CLIP) or 'layout_relation' (Docling)

class ChatResponse(BaseModel):
    """What the frontend receives as the final result."""
    response: str
    citations: List[SourceMetadata] = Field(default_factory=list)
    images: List[ImageResult] = Field(default_factory=list)