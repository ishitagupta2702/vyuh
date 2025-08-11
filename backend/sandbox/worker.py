import dramatiq
import redis
import json
import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

# Import sandbox components
from sandbox import SandboxManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Dramatiq broker and backend
redis_broker = RedisBroker(host="localhost", port=6379, db=0)
redis_backend = RedisBackend(host="localhost", port=6379, db=0)
redis_broker.add_middleware(Results(backend=redis_backend))

# Set the broker for Dramatiq
dramatiq.set_broker(redis_broker)

# Redis connection for job status updates
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

class JobStatus:
    """Job status constants and utilities."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkerManager:
    """
    Manages background job processing and status updates.
    """
    
    def __init__(self):
        self.redis_client = redis_client
        self.logger = logger
    
    def update_job_status(self, job_id: str, status: str, result: Any = None, error: str = None):
        """
        Update job status in Redis.
        
        Args:
            job_id: Unique job identifier
            status: Job status (pending, running, completed, failed, cancelled)
            result: Job result data
            error: Error message if failed
        """
        try:
            job_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
                "result": result,
                "error": error
            }
            
            if status == JobStatus.RUNNING:
                job_data["started_at"] = datetime.utcnow().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job_data["completed_at"] = datetime.utcnow().isoformat()
            
            # Store job status in Redis
            self.redis_client.hset(f"job:{job_id}", mapping=job_data)
            self.redis_client.expire(f"job:{job_id}", 86400)  # Expire after 24 hours
            
            self.logger.info(f"Job {job_id} status updated to: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update job status for {job_id}: {str(e)}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get current job status from Redis.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Dict containing job status information
        """
        try:
            job_data = self.redis_client.hgetall(f"job:{job_id}")
            if not job_data:
                return {"status": "not_found", "error": f"Job {job_id} not found"}
            
            return job_data
            
        except Exception as e:
            self.logger.error(f"Failed to get job status for {job_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or running job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        try:
            current_status = self.get_job_status(job_id)
            if current_status.get("status") in [JobStatus.PENDING, JobStatus.RUNNING]:
                self.update_job_status(job_id, JobStatus.CANCELLED)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            return False

# Global worker manager instance
worker_manager = WorkerManager()

@dramatiq.actor(store_results=True, max_retries=3, time_limit=3600000)  # 1 hour timeout
def execute_crew_workflow(crew_config: Dict[str, Any], task_description: str, job_id: str) -> Dict[str, Any]:
    """
    Execute a CrewAI workflow in the background.
    
    Args:
        crew_config: Configuration for the crew and agents
        task_description: Description of the task to execute
        job_id: Unique identifier for job tracking
        
    Returns:
        Dict containing execution results
    """
    try:
        # Update job status to running
        worker_manager.update_job_status(job_id, JobStatus.RUNNING)
        
        logger.info(f"Starting crew workflow execution for job {job_id}")
        
        # Import CrewAI components (avoid circular imports)
        from crewai import Crew, Agent, Task
        from crewai.tools import BaseTool
        
        # Create agents from configuration
        agents = []
        for agent_config in crew_config.get("agents", []):
            agent = Agent(
                role=agent_config["role"],
                goal=agent_config["goal"],
                backstory=agent_config.get("backstory", ""),
                verbose=agent_config.get("verbose", True),
                allow_delegation=agent_config.get("allow_delegation", False)
            )
            
            # Add tools if specified
            if "tools" in agent_config:
                tools = []
                for tool_config in agent_config["tools"]:
                    # Create tool instances based on configuration
                    tool = _create_tool_from_config(tool_config)
                    if tool:
                        tools.append(tool)
                agent.tools = tools
            
            agents.append(agent)
        
        # If no tools specified, add sandbox tools automatically
        if not any(agent.tools for agent in agents):
            logger.info("No tools specified, adding Daytona sandbox tools automatically")
            try:
                # Use sandbox context manager for proper lifecycle management
                async def add_sandbox_tools():
                    async with SandboxContextManager() as sandbox_ctx:
                        tools = sandbox_ctx.get_tools()
                        
                        # Add appropriate tools based on agent role
                        for i, agent in enumerate(agents):
                            if "researcher" in agent_config.get("role", "").lower():
                                agent.tools = [tools["file_tool"], tools["command_tool"]]
                            elif "writer" in agent_config.get("role", "").lower():
                                agent.tools = [tools["file_tool"], tools["pdf_tool"]]
                            else:
                                agent.tools = [tools["file_tool"]]
                        
                        # Execute crew with sandbox tools
                        crew = Crew(
                            agents=agents,
                            tasks=tasks,
                            verbose=crew_config.get("verbose", True),
                            memory=crew_config.get("memory", None)
                        )
                        
                        return crew.kickoff()
                
                # Run async function
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(add_sandbox_tools())
                finally:
                    loop.close()
                
                # Update job status to completed
                worker_manager.update_job_status(job_id, JobStatus.COMPLETED, result=result)
                
                logger.info(f"Sandbox-enabled crew workflow completed successfully for job {job_id}")
                
                return {
                    "success": True,
                    "result": result,
                    "job_id": job_id,
                    "completed_at": datetime.utcnow().isoformat(),
                    "sandbox_enabled": True
                }
                
            except Exception as e:
                logger.error(f"Failed to execute sandbox-enabled crew workflow: {str(e)}")
                # Fall back to regular execution
                logger.info("Falling back to regular crew execution")
        
        # Create tasks from configuration
        tasks = []
        for task_config in crew_config.get("tasks", []):
            task = Task(
                description=task_config["description"],
                agent=agents[task_config.get("agent_index", 0)] if agents else None,
                expected_output=task_config.get("expected_output", ""),
                context=task_config.get("context", [])
            )
            tasks.append(task)
        
        # Create and execute crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=crew_config.get("verbose", True),
            memory=crew_config.get("memory", None)
        )
        
        # Execute the crew workflow
        result = crew.kickoff()
        
        # Update job status to completed
        worker_manager.update_job_status(job_id, JobStatus.COMPLETED, result=result)
        
        logger.info(f"Crew workflow completed successfully for job {job_id}")
        
        return {
            "success": True,
            "result": result,
            "job_id": job_id,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Crew workflow execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update job status to failed
        worker_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "job_id": job_id,
            "failed_at": datetime.utcnow().isoformat()
        }

@dramatiq.actor(store_results=True, max_retries=3, time_limit=1800000)  # 30 minute timeout
def execute_sandbox_task(task_type: str, task_config: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Execute a sandbox operation in the background.
    
    Args:
        task_type: Type of sandbox task (file, shell, pdf)
        task_config: Configuration for the task
        job_id: Unique identifier for job tracking
        
    Returns:
        Dict containing execution results
    """
    try:
        # Update job status to running
        worker_manager.update_job_status(job_id, JobStatus.RUNNING)
        
        logger.info(f"Starting sandbox task execution for job {job_id}: {task_type}")
        
        # Import sandbox components
        from .sandbox import SandboxManager
        from .file_tool import FileTool
        from .crewai_tools import SandboxContextManager
        from .shell_tool import ShellTool
        from .pdf_tool import PDFTool
        
        # Initialize sandbox manager
        sandbox_manager = SandboxManager()
        
        try:
            # Initialize sandbox
            if not sandbox_manager.initialize_sandbox():
                raise RuntimeError("Failed to initialize sandbox")
            
            # Execute task based on type
            if task_type == "file":
                result = _execute_file_task(sandbox_manager, task_config)
            elif task_type == "shell":
                result = _execute_shell_task(sandbox_manager, task_config)
            elif task_type == "pdf":
                result = _execute_pdf_task(sandbox_manager, task_config)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Update job status to completed
            worker_manager.update_job_status(job_id, JobStatus.COMPLETED, result=result)
            
            logger.info(f"Sandbox task completed successfully for job {job_id}")
            
            return {
                "success": True,
                "result": result,
                "job_id": job_id,
                "task_type": task_type,
                "completed_at": datetime.utcnow().isoformat()
            }
            
        finally:
            # Always cleanup sandbox
            sandbox_manager.cleanup()
        
    except Exception as e:
        error_msg = f"Sandbox task execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update job status to failed
        worker_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "job_id": job_id,
            "task_type": task_type,
            "failed_at": datetime.utcnow().isoformat()
        }

def _create_tool_from_config(tool_config: Dict[str, Any]) -> Optional[Any]:
    """Create a tool instance from configuration."""
    try:
        tool_type = tool_config.get("type")
        
        if tool_type == "file":
            from .crewai_tools import create_file_tool
            # Note: This would need a sandbox manager instance
            return None  # Placeholder for now
        elif tool_type == "shell":
            from .crewai_tools import create_command_tool
            return None  # Placeholder for now
        elif tool_type == "pdf":
            from .crewai_tools import create_pdf_tool
            return None  # Placeholder for now
        else:
            logger.warning(f"Unknown tool type: {tool_type}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create tool from config: {str(e)}")
        return None

def _execute_file_task(sandbox_manager: SandboxManager, task_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a file operation task."""
    file_tool = FileTool(sandbox_manager)
    return file_tool._run(**task_config)

def _execute_shell_task(sandbox_manager: SandboxManager, task_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a shell operation task."""
    shell_tool = ShellTool(sandbox_manager)
    return shell_tool._run(**task_config)

def _execute_pdf_task(sandbox_manager: SandboxManager, task_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a PDF generation task."""
    pdf_tool = PDFTool(sandbox_manager)
    return pdf_tool._run(**task_config)

# Utility functions for job management
def queue_crew_workflow(crew_config: Dict[str, Any], task_description: str) -> str:
    """
    Queue a crew workflow for background execution.
    
    Args:
        crew_config: Configuration for the crew and agents
        task_description: Description of the task to execute
        
    Returns:
        str: Job ID for tracking
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Queue the job
    execute_crew_workflow.send(crew_config, task_description, job_id)
    
    # Update initial job status
    worker_manager.update_job_status(job_id, JobStatus.PENDING)
    
    logger.info(f"Queued crew workflow job: {job_id}")
    return job_id

def queue_sandbox_task(task_type: str, task_config: Dict[str, Any]) -> str:
    """
    Queue a sandbox task for background execution.
    
    Args:
        task_type: Type of sandbox task
        task_config: Configuration for the task
        
    Returns:
        str: Job ID for tracking
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Queue the job
    execute_sandbox_task.send(task_type, task_config, job_id)
    
    # Update initial job status
    worker_manager.update_job_status(job_id, JobStatus.PENDING)
    
    logger.info(f"Queued sandbox task job: {job_id}")
    return job_id

def get_all_jobs() -> List[Dict[str, Any]]:
    """Get all active jobs from Redis."""
    try:
        job_keys = redis_client.keys("job:*")
        jobs = []
        
        for key in job_keys:
            job_id = key.replace("job:", "")
            job_data = worker_manager.get_job_status(job_id)
            job_data["job_id"] = job_id
            jobs.append(job_data)
        
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to get all jobs: {str(e)}")
        return []

def cleanup_completed_jobs() -> int:
    """Clean up completed and failed jobs older than 24 hours."""
    try:
        job_keys = redis_client.keys("job:*")
        cleaned_count = 0
        
        for key in job_keys:
            job_data = redis_client.hgetall(key)
            status = job_data.get("status")
            
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                # Check if job is older than 24 hours
                completed_at = job_data.get("completed_at")
                if completed_at:
                    try:
                        completed_time = datetime.fromisoformat(completed_at)
                        if (datetime.utcnow() - completed_time).days >= 1:
                            redis_client.delete(key)
                            cleaned_count += 1
                    except:
                        pass
        
        logger.info(f"Cleaned up {cleaned_count} old jobs")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup jobs: {str(e)}")
        return 0
