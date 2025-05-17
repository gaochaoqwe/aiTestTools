from fastapi import FastAPI
from .api import router as project_api_router # Ensure this router is correctly defined in .api

# Create a new FastAPI app instance specifically for project management
pm_app = FastAPI(
    title="Project Management API",
    description="API for managing projects and their documents.",
    version="0.1.0",
    openapi_url="/openapi.json", # Relative to the mount path of this app
    docs_url="/docs",             # Relative to the mount path
    redoc_url="/redoc"            # Relative to the mount path
)

# Include the API router. Routes defined within this router (e.g., /projects, /documents)
# will be available at the root of this pm_app.
# For example, if projects.router has a prefix "/projects", it will be available at /projects
pm_app.include_router(project_api_router)

# The main export from this module for integration will be 'pm_app'.
