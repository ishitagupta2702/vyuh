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

# Import the publishCrew class
from vyuh.crew import publishCrew

# Import routes
from routes.agents import router as agents_router
from routes.crew_builder import router as crew_builder_router

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

class AgentRequest(BaseModel):
    topic: str = "The future of content creation"

class AgentResponse(BaseModel):
    result: str
    topic: str
    status: str = "success"

@app.get("/")
async def root():
    return {"message": "Vyuh API is running"}

@app.get("/run-agent")
async def run_agent_get():
    """
    GET endpoint for browser testing - uses default topic
    """
    try:
        # Check if OpenAI API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not found in environment variables"
            )
        
        # Use default topic for GET requests
        default_topic = "The future of content creation"
        
        # Instantiate and run the crew
        crew_instance = publishCrew()
        result = crew_instance.crew().kickoff(inputs={"topic": default_topic})
        
        return AgentResponse(
            result=str(result),
            topic=default_topic,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running agent: {str(e)}"
        )

@app.post("/run-agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """
    Run the publishCrew agent with the specified topic
    """
    try:
        # Check if OpenAI API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not found in environment variables"
            )
        
        # Instantiate and run the crew
        crew_instance = publishCrew()
        result = crew_instance.crew().kickoff(inputs={"topic": request.topic})
        
        return AgentResponse(
            result=str(result),
            topic=request.topic,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running agent: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vyuh-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)