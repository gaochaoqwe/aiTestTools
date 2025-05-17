import sys
import os

# Add the backend directory to sys.path to allow direct script execution
# and correct module imports like 'from app.projectManagement.database import Base, engine'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = SCRIPT_DIR # Assuming init_db.py is in the backend root
sys.path.append(os.path.dirname(BACKEND_DIR)) # Add parent of backend to path if needed for 'app'
sys.path.append(BACKEND_DIR) # Add backend to path

from app.database import Base, engine # Corrected import path
from app.projectManagement.models import Project, Document # Ensure models are imported

def init_db():
    print("Initializing database...")
    # Create all tables
    # This will create tables based on all imported models that inherit from Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully (if they didn't exist)!")

if __name__ == "__main__":
    # This allows running the script directly, e.g., python init_db.py
    print(f"Current working directory: {os.getcwd()}")
    print(f"System path: {sys.path}")
    init_db()
