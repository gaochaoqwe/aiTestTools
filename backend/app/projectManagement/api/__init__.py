from fastapi import APIRouter
from . import projects, documents # Assuming you will create documents.py for document APIs

router = APIRouter()

# Include project-related routes
router.include_router(projects.router, tags=["Projects"])
# Include document-related routes (if they are separate)
router.include_router(documents.router, tags=["Documents"])

__all__ = ["router"]
