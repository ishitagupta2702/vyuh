import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from daytona_sdk import AsyncDaytona, DaytonaConfig, CreateSandboxFromSnapshotParams, AsyncSandbox, SessionExecuteRequest, Resources, SandboxState
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SandboxManager:
    """
    Manages Daytona-based cloud sandbox environments for safe code execution.
    """
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or tempfile.mkdtemp(prefix="sandbox_")
        self.daytona_client = None
        self.sandbox = None
        self.sandbox_id = None
        self.logger = logger
        
        # Initialize Daytona configuration from environment variables
        self.daytona_config = DaytonaConfig(
            api_key=os.getenv("DAYTONA_API_KEY"),
            api_url=os.getenv("DAYTONA_SERVER_URL", "https://cloud.daytona.com"),  # Use api_url instead of url
            target=os.getenv("DAYTONA_TARGET", "default")
        )
        
        # Sandbox snapshot configuration
        self.sandbox_snapshot = os.getenv("DAYTONA_SANDBOX_SNAPSHOT", "ubuntu-22.04")
        
    async def initialize_sandbox(self) -> bool:
        """
        Initialize the sandbox environment and create Daytona sandbox.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("Initializing Daytona sandbox environment...")
            
            # Ensure workspace directory exists
            Path(self.workspace_dir).mkdir(parents=True, exist_ok=True)
            
            # Initialize Daytona client
            self.daytona_client = AsyncDaytona(self.daytona_config)
            
            # Create new sandbox
            self.sandbox = await self._create_sandbox()
            self.sandbox_id = self.sandbox.id
            
            self.logger.info("Daytona sandbox initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sandbox: {str(e)}")
            return False
    
    async def _create_sandbox(self) -> AsyncSandbox:
        """Create a new sandbox with required services configured."""
        try:
            self.logger.debug("Creating new Daytona sandbox environment")
            
            # Create sandbox with snapshot
            params = CreateSandboxFromSnapshotParams(
                snapshot=self.sandbox_snapshot,
                public=True,
                labels={'project': 'vyuh-sandbox'},
                env_vars={
                    "RESOLUTION": "1024x768x24",
                    "RESOLUTION_WIDTH": "1024",
                    "RESOLUTION_HEIGHT": "768",
                    "ANONYMIZED_TELEMETRY": "false"
                },
                resources=Resources(
                    cpu=2,
                    memory=4,
                    disk=5,
                ),
                auto_stop_interval=15,
                auto_archive_interval=2 * 60,
            )
            
            # Create the sandbox
            sandbox = await self.daytona_client.create(params)
            self.logger.debug(f"Sandbox created with ID: {sandbox.id}")
            
            # Start supervisord in a session for new sandbox
            await self._start_supervisord_session(sandbox)
            
            self.logger.debug(f"Sandbox environment successfully initialized")
            return sandbox
            
        except Exception as e:
            self.logger.error(f"Failed to create sandbox: {str(e)}")
            raise
    
    async def _start_supervisord_session(self, sandbox: AsyncSandbox):
        """Start supervisord in a session."""
        session_id = "supervisord-session"
        try:
            self.logger.info(f"Creating session {session_id} for supervisord")
            await sandbox.process.create_session(session_id)
            
            # Execute supervisord command
            await sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
                command="exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf",
                var_async=True
            ))
            self.logger.info(f"Supervisord started in session {session_id}")
        except Exception as e:
            self.logger.error(f"Error starting supervisord session: {str(e)}")
            # Don't raise here as it's not critical for basic functionality
    
    async def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command in the Daytona sandbox.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Dict containing execution results
        """
        try:
            if not self.sandbox:
                raise RuntimeError("Sandbox not initialized. Call initialize_sandbox() first.")
            
            self.logger.info(f"Executing command: {command}")
            
            # Execute command in Daytona sandbox
            result = await self.sandbox.process.execute_command(
                command=command,
                timeout=timeout
            )
            
            return {
                "success": True,
                "stdout": result.stdout if hasattr(result, 'stdout') and result.stdout else "",
                "stderr": result.stderr if hasattr(result, 'stderr') and result.stderr else "",
                "return_code": result.exit_code if hasattr(result, 'exit_code') else 0
            }
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
    
    def create_file(self, filename: str, content: str) -> bool:
        """
        Create a file in the sandbox workspace.
        
        Args:
            filename: Name of the file to create
            content: File content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = os.path.join(self.workspace_dir, filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Created file: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create file {filename}: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up sandbox resources and delete Daytona sandbox."""
        try:
            self.logger.info("Cleaning up Daytona sandbox...")
            
            # Delete Daytona sandbox
            if self.sandbox and self.daytona_client:
                try:
                    await self.daytona_client.delete(self.sandbox)
                    self.logger.info("Daytona sandbox deleted successfully")
                except Exception as e:
                    self.logger.warning(f"Failed to delete sandbox: {str(e)}")
            
            # Clean up workspace directory
            if os.path.exists(self.workspace_dir) and self.workspace_dir.startswith(tempfile.gettempdir()):
                shutil.rmtree(self.workspace_dir, ignore_errors=True)
            
            self.logger.info("Daytona sandbox cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_sandbox()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    def __enter__(self):
        """Synchronous context manager entry (for backward compatibility)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.initialize_sandbox())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous context manager exit (for backward compatibility)."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.cleanup())
        loop.close()
