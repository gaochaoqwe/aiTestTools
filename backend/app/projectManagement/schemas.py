from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The name of the project")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class ProjectInDBBase(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Replaces orm_mode = True

# Properties to return to client
class Project(ProjectInDBBase):
    pass

# --- Document Schemas ---
class DocumentBase(BaseModel):
    original_filename: str = Field(..., max_length=255)
    file_id: str = Field(..., max_length=100, description="Unique identifier for the file content, e.g., hash or UUID")
    file_path: str = Field(..., max_length=500, description="Server-side path to the file")
    file_type: Optional[str] = Field(None, max_length=50, description="Type of the document, e.g., 'requirement_spec'")
    review_type: Optional[str] = Field(None, max_length=50, description="Type of review, e.g., 'configuration_item'")
    status: str = Field(default="pending", max_length=20)

class DocumentCreate(DocumentBase):
    project_id: int

class DocumentUpdate(BaseModel):
    original_filename: Optional[str] = Field(None, max_length=255)
    file_type: Optional[str] = Field(None, max_length=50)
    review_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)

class DocumentInDBBase(DocumentBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True # Replaces orm_mode = True

# Properties to return to client
class Document(DocumentInDBBase):
    pass

# For Project response model to include its documents
class ProjectWithDocuments(Project):
    documents: List[Document] = []
