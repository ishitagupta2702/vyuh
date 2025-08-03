from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from pathlib import Path
import asyncio
import time
from typing import AsyncGenerator

router = APIRouter()

async def stream_file_content(session_id: str) -> AsyncGenerator[str, None]:
    """
    Generator function that streams file content line by line as SSE events.
    
    Args:
        session_id: The session ID to stream results for
        
    Yields:
        SSE formatted data strings
    """
    runs_dir = Path("runs")
    result_file = runs_dir / f"{session_id}.txt"
    
    # Wait for file to exist (up to 30 seconds)
    max_wait_time = 30
    start_time = time.time()
    
    while not result_file.exists():
        if time.time() - start_time > max_wait_time:
            yield f"data: [ERROR] File not found after {max_wait_time} seconds\n\n"
            return
        
        await asyncio.sleep(0.5)
    
    # Stream the file content line by line
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            for line in f:
                # Clean the line and send as SSE data
                cleaned_line = line.strip()
                if cleaned_line:
                    # Check if this is a JSON line (starts with {)
                    if cleaned_line.startswith('{'):
                        # Send JSON data as-is for frontend parsing
                        yield f"data: {cleaned_line}\n\n"
                    else:
                        # Send regular text data
                        yield f"data: {cleaned_line}\n\n"
                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming the client
        
        # Send completion signal
        yield f"data: [COMPLETE] Stream finished\n\n"
        
    except Exception as e:
        yield f"data: [ERROR] Failed to read file: {str(e)}\n\n"

@router.get("/api/stream/{session_id}")
async def stream_crew_output(session_id: str):
    """
    Stream crew execution output using Server-Sent Events.
    
    Args:
        session_id: The session ID to stream results for
        
    Returns:
        EventSourceResponse that streams the crew output
    """
    try:
        return EventSourceResponse(stream_file_content(session_id))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error setting up stream: {str(e)}"
        )
