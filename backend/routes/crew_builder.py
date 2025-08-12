from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import time
import uuid
from pathlib import Path

# Add the src directory to Python path to import vyuh modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Add sandbox path to import worker
sandbox_path = project_root / "sandbox"
sys.path.insert(0, str(sandbox_path))

# Import the orchestrator
from vyuh.tools.orchestrator import launch_crew_from_linear_list
# Import worker for job queuing
from worker import queue_crew_workflow, get_job_status

router = APIRouter()

class CrewLaunchRequest(BaseModel):
    crew: List[str]
    topic: str

class CrewLaunchResponse(BaseModel):
    session_id: str
    job_id: str
    status: str = "queued"
    message: str = "Job queued successfully"
    topic: Optional[str] = None
    crew: Optional[List[str]] = None

@router.post("/api/launch", response_model=CrewLaunchResponse)
async def launch_crew(request: CrewLaunchRequest):
    """
    Launch a CrewAI workflow with the specified crew and topic.
    
    Args:
        request: CrewLaunchRequest containing crew list and topic
        
    Returns:
        CrewLaunchResponse with session ID, status, and complete result data including
        the actual crew execution output, topic, and crew information
    """
    print(f"[CREW_BUILDER] Launch request received: crew={request.crew}, topic={request.topic}")
    print("Received launch request:", request.crew, request.topic)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"[CREW_BUILDER] Generated session_id: {session_id}")
    
    print("[CREW_BUILDER] Starting validation...")
    
    try:
        print("[CREW_BUILDER] Checking OpenAI API key...")
        # Check if OpenAI API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("[ERROR] OpenAI API key not found")
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not found in environment variables"
            )
        print("[CREW_BUILDER] OpenAI API key found")
        
        # Validate crew list
        print("[CREW_BUILDER] Validating crew list...")
        if not request.crew:
            print("[ERROR] Empty crew list")
            raise HTTPException(
                status_code=400,
                detail="Crew list cannot be empty"
            )
        print(f"[CREW_BUILDER] Crew list validated: {request.crew}")
        
        print(f"[CREW_BUILDER] Starting crew job queuing for session_id: {session_id}")
        
        # Create crew configuration for background execution
        crew_config = {
            "agents": [
                {
                    "role": "researcher" if "researcher" in agent else "writer" if "writer" in agent else "agent",
                    "goal": f"Process {request.topic}",
                    "backstory": f"Specialized agent for {agent} operations",
                    "verbose": True,
                    "allow_delegation": False
                }
                for agent in request.crew
            ],
            "tasks": [
                {
                    "description": f"Execute {agent} task for {request.topic}",
                    "agent_index": i,
                    "expected_output": f"Results from {agent}",
                    "context": []
                }
                for i, agent in enumerate(request.crew)
            ],
            "verbose": True
        }
        
        # Queue the job instead of running synchronously
        try:
            job_id = queue_crew_workflow(crew_config, request.topic)
            print(f"[CREW_BUILDER] Job queued with ID: {job_id}")
            
            return CrewLaunchResponse(
                session_id=session_id,
                job_id=job_id,
                status="queued",
                message="Crew workflow queued for background execution",
                topic=request.topic,
                crew=request.crew
            )
            
        except Exception as e:
            print(f"[CREW_BUILDER] Failed to queue job: {e}")
            raise e
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration file not found: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error launching crew: {str(e)}"
        )


@router.get("/api/result/{session_id}")
async def get_result(session_id: str):
    """
    Retrieve the result of a crew execution by session ID.
    
    Args:
        session_id: The session ID to retrieve results for
        
    Returns:
        The contents of the result file as text
    """
    try:
        # Construct the path to the result file
        runs_dir = Path("runs")
        result_file = runs_dir / f"{session_id}.txt"
        
        # Check if the file exists
        if not result_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Result not found for session ID: {session_id}"
            )
        
        # Read and return the file contents
        with open(result_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"session_id": session_id, "content": content}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving result: {str(e)}"
        )

@router.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a background job.
    """
    try:
        from worker import worker_manager
        status = worker_manager.get_job_status(job_id)
        return {"job_id": job_id, "status": status}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting job status: {str(e)}"
        )

@router.get("/api/jobs")
async def get_all_jobs():
    """
    Get all active jobs.
    """
    try:
        from worker import get_all_jobs
        jobs = get_all_jobs()
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting jobs: {str(e)}"
        )