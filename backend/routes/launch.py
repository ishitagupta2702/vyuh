from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
import sys
from pathlib import Path

# Add the src directory to Python path to import vyuh modules
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import the orchestrator
from vyuh.tools.orchestrator import launch_crew_from_linear_list

router = APIRouter()

class LaunchRequest(BaseModel):
    crew: List[str]
    topic: str

class LaunchResponse(BaseModel):
    session_id: str
    status: str = "success"
    message: str = "Crew launched successfully"

@router.post("/api/launch", response_model=LaunchResponse)
async def launch_crew(request: LaunchRequest):
    """
    Launch a CrewAI workflow with the specified crew and topic.
    
    Args:
        request: LaunchRequest containing crew list and topic
        
    Returns:
        LaunchResponse with session ID and status
    """
    print(f"[DEBUG] Launch request received: crew={request.crew}, topic={request.topic}")
    
    try:
        print("[DEBUG] Checking OpenAI API key...")
        # Check if OpenAI API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("[ERROR] OpenAI API key not found")
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not found in environment variables"
            )
        print("[DEBUG] OpenAI API key found")
        
        # Validate crew list
        print("[DEBUG] Validating crew list...")
        if not request.crew:
            print("[ERROR] Empty crew list")
            raise HTTPException(
                status_code=400,
                detail="Crew list cannot be empty"
            )
        print(f"[DEBUG] Crew list validated: {request.crew}")
        
        # Launch the crew
        print("[DEBUG] Calling launch_crew_from_linear_list...")
        session_id = launch_crew_from_linear_list(request.crew, request.topic)
        print(f"[DEBUG] Crew launched successfully, session_id: {session_id}")
        
        return LaunchResponse(
            session_id=session_id,
            status="success",
            message="Crew launched successfully"
        )
    
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
