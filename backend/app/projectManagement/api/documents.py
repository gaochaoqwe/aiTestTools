from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil # For file operations
import os
import uuid # For generating unique file IDs

from .. import crud, schemas, models # Adjusted imports for current structure
from ...database import get_db # Adjusted import for get_db from app/database.py

# Define a base path for uploads, ideally from config
# Ensure this directory exists or is created by your app startup logic
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads", "project_documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(
    prefix="/documents",
    # tags=["Documents"] # Tags are often better defined when including the router
)

@router.post("/projects/{project_id}/documents/", response_model=schemas.Document, status_code=status.HTTP_201_CREATED)
async def upload_and_create_document_for_project(
    project_id: int,
    file_type: Optional[str] = None, # Query parameters for metadata
    review_type: Optional[str] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document file and associate it with a project.
    Generates a unique file_id (UUID) and saves the file to a designated UPLOAD_DIR.
    """
    # Check if project exists
    db_project = crud.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Generate a unique file ID and path
    unique_file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    # It's better to store files in subdirectories, e.g., by project_id or by date
    # For simplicity, storing directly in UPLOAD_DIR with unique_file_id as name
    saved_file_name = f"{unique_file_id}{file_extension}"
    file_path_on_server = os.path.join(UPLOAD_DIR, saved_file_name)

    # Save the uploaded file
    try:
        with open(file_path_on_server, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save file")
    finally:
        file.file.close()

    document_data = schemas.DocumentCreate(
        project_id=project_id,
        original_filename=file.filename,
        file_id=unique_file_id, # Store the UUID part as file_id
        file_path=file_path_on_server, # Store the server path
        file_type=file_type,
        review_type=review_type,
        status="uploaded" # Initial status
    )
    
    return crud.create_document(db=db, document=document_data)

@router.get("/projects/{project_id}/documents/", response_model=List[schemas.Document])
def read_documents_for_project(
    project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """
    Retrieve documents for a specific project.
    """
    db_project = crud.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    documents = crud.get_documents_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return documents

@router.get("/{document_id}", response_model=schemas.Document)
def read_single_document(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single document by its ID.
    """
    db_document = crud.get_document(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return db_document

@router.put("/{document_id}", response_model=schemas.Document)
def update_existing_document(
    document_id: int, document_update: schemas.DocumentUpdate, db: Session = Depends(get_db)
):
    """
    Update an existing document's metadata (not the file itself via this endpoint).
    """
    updated_document = crud.update_document(db=db, document_id=document_id, document_update=document_update)
    if updated_document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return updated_document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete an existing document (metadata and the physical file).
    """
    db_document = crud.get_document(db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Attempt to delete the physical file
    try:
        if os.path.exists(db_document.file_path):
            os.remove(db_document.file_path)
    except Exception as e:
        # Log this error, but proceed to delete DB record if file deletion fails
        # Or, handle more gracefully (e.g., mark as 'file_missing' in DB)
        print(f"Error deleting file {db_document.file_path}: {e}") # Basic logging

    success = crud.delete_document(db=db, document_id=document_id)
    if not success: # Should not happen if db_document was found, but good practice
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete document record")
    
    return # No content for 204
