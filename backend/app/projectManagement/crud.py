from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

# --- Project CRUD Operations ---
def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_project_by_name(db: Session, name: str) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.name == name).first()

def get_projects(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Project]:
    return db.query(models.Project).order_by(models.Project.id.desc()).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(
        name=project.name
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(
    db: Session, project_id: int, project_update: schemas.ProjectUpdate
) -> Optional[models.Project]:
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int) -> bool:
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db.delete(db_project)
    db.commit()
    return True

# --- Document CRUD Operations ---
def get_document(db: Session, document_id: int) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == document_id).first()

def get_documents_by_project(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> List[models.Document]:
    return (
        db.query(models.Document)
        .filter(models.Document.project_id == project_id)
        .order_by(models.Document.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_document(
    db: Session, document: schemas.DocumentCreate
) -> models.Document:
    db_document = models.Document(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document(
    db: Session, document_id: int, document_update: schemas.DocumentUpdate
) -> Optional[models.Document]:
    db_document = get_document(db, document_id)
    if not db_document:
        return None
    
    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_document, field, value)
        
    db.commit()
    db.refresh(db_document)
    return db_document

def delete_document(db: Session, document_id: int) -> bool:
    db_document = get_document(db, document_id)
    if not db_document:
        return False
    
    db.delete(db_document)
    db.commit()
    return True
