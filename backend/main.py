from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to Python path to import vyuh modules
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Load environment variables from backend .env file
load_dotenv(project_root / ".env")

# Import routes
from routes.agents import router as agents_router
from routes.crew_builder import router as crew_builder_router

app = FastAPI(
    title="Vyuh API",
    description="AI Agent System API using CrewAI",
    version="1.0.0"
)

# Get CORS origins from environment
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(crew_builder_router)



@app.get("/")
async def root():
    return {"message": "Vyuh API is running"}



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vyuh-api"}

@app.get("/config/daytona")
async def daytona_config_status():
    """Check Daytona configuration status"""
    try:
        from sandbox.sandbox import SandboxManager
        
        # Create a temporary sandbox manager to check configuration
        sandbox_manager = SandboxManager()
        config_status = sandbox_manager.get_configuration_status()
        
        return {
            "status": "configured" if config_status["fully_configured"] else "incomplete",
            "configuration": config_status,
            "message": "Daytona configuration check completed"
        }
    except Exception as e:
        return {
            "status": "error",
            "configuration": {},
            "message": f"Failed to check Daytona configuration: {str(e)}"
        }

@app.get("/sandbox/list")
async def list_sandboxes():
    """List all available Daytona sandboxes"""
    try:
        from sandbox.sandbox import SandboxManager
        
        sandbox_manager = SandboxManager()
        if not sandbox_manager.is_configured():
            return {"error": "Daytona not configured"}
        
        sandboxes = await sandbox_manager.list_sandboxes()
        return {
            "sandboxes": sandboxes,
            "count": len(sandboxes)
        }
    except Exception as e:
        return {"error": f"Failed to list sandboxes: {str(e)}"}

@app.get("/sandbox/{sandbox_id}/status")
async def get_sandbox_status(sandbox_id: str):
    """Get status of a specific sandbox"""
    try:
        from sandbox.sandbox import SandboxManager
        
        sandbox_manager = SandboxManager()
        if not sandbox_manager.is_configured():
            return {"error": "Daytona not configured"}
        
        status = await sandbox_manager.get_sandbox_status(sandbox_id)
        return status
    except Exception as e:
        return {"error": f"Failed to get sandbox status: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)