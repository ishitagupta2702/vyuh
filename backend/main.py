from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to Python path to import vyuh modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Load environment variables from root .env file
load_dotenv(project_root / ".env")

# Import routes
from routes.agents import router as agents_router
from routes.crew_builder import router as crew_builder_router
from routes.stream import router as stream_router

app = FastAPI(
    title="Vyuh API",
    description="AI Agent System API using CrewAI",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(crew_builder_router)
app.include_router(stream_router)



@app.get("/")
async def root():
    return {"message": "Vyuh API is running"}



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vyuh-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)