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
        
        # Initialize and validate Daytona configuration
        self.daytona_config = self._initialize_daytona_config()
        
        # Validate configuration
        self._validate_configuration()
        
        # Sandbox snapshot configuration
        self.sandbox_snapshot = os.getenv("SANDBOX_SNAPSHOT_NAME", "ubuntu-22.04")
    
    def _initialize_daytona_config(self) -> DaytonaConfig:
        """Initialize Daytona configuration from environment variables."""
        api_key = os.getenv("DAYTONA_API_KEY")
        api_url = os.getenv("DAYTONA_SERVER_URL", "https://cloud.daytona.com")
        target = os.getenv("DAYTONA_TARGET", "default")
        
        # Log configuration status
        if api_key:
            self.logger.debug("Daytona API key configured successfully")
        else:
            self.logger.warning("No Daytona API key found in environment variables")
        
        if api_url:
            self.logger.debug(f"Daytona API URL set to: {api_url}")
        else:
            self.logger.warning("No Daytona API URL found in environment variables")
        
        if target:
            self.logger.debug(f"Daytona target set to: {target}")
        else:
            self.logger.warning("No Daytona target found in environment variables")
        
        return DaytonaConfig(
            api_key=api_key,
            api_url=api_url,
            target=target
        )
    
    def _validate_configuration(self) -> None:
        """Validate required Daytona configuration."""
        missing_configs = []
        
        if not self.daytona_config.api_key:
            missing_configs.append("DAYTONA_API_KEY")
        
        if not self.daytona_config.api_url:
            missing_configs.append("DAYTONA_SERVER_URL")
        
        if not self.daytona_config.target:
            missing_configs.append("DAYTONA_TARGET")
        
        if missing_configs:
            config_list = ", ".join(missing_configs)
            self.logger.warning(f"Missing required Daytona configuration: {config_list}")
            self.logger.warning("Sandbox operations may fail. Please check your environment variables.")
        else:
            self.logger.info("Daytona configuration validated successfully")
    
    def is_configured(self) -> bool:
        """Check if Daytona is properly configured."""
        return bool(self.daytona_config.api_key and self.daytona_config.api_url and self.daytona_config.target)
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get current configuration status."""
        return {
            "api_key_configured": bool(self.daytona_config.api_key),
            "api_url_configured": bool(self.daytona_config.api_url),
            "target_configured": bool(self.daytona_config.target),
            "snapshot_configured": bool(self.sandbox_snapshot),
            "fully_configured": self.is_configured()
        }
        
    async def initialize_sandbox(self) -> bool:
        """
        Initialize the sandbox environment and create Daytona sandbox.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("Initializing Daytona sandbox environment...")
            
            # Check if Daytona configuration is valid
            if not self.daytona_config.api_key:
                self.logger.error("Cannot initialize sandbox: DAYTONA_API_KEY is required")
                return False
            
            # Ensure workspace directory exists
            Path(self.workspace_dir).mkdir(parents=True, exist_ok=True)
            
            # Initialize Daytona client
            self.daytona_client = AsyncDaytona(self.daytona_config)
            
            # Create new sandbox
            self.sandbox = await self.create_sandbox()
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
            await self.start_supervisord_session(sandbox)
            
            self.logger.debug(f"Sandbox environment successfully initialized")
            return sandbox
            
        except Exception as e:
            self.logger.error(f"Failed to create sandbox: {str(e)}")
            raise
    
    async def start_supervisord_session(self, sandbox: AsyncSandbox):
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
    
    async def get_or_start_sandbox(self, sandbox_id: str) -> AsyncSandbox:
        """Retrieve a sandbox by ID, check its state, and start it if needed."""
        
        self.logger.info(f"Getting or starting sandbox with ID: {sandbox_id}")

        try:
            sandbox = await self.daytona_client.get(sandbox_id)
            
            # Check if sandbox needs to be started
            if sandbox.state == SandboxState.ARCHIVED or sandbox.state == SandboxState.STOPPED:
                self.logger.info(f"Sandbox is in {sandbox.state} state. Starting...")
                try:
                    await self.daytona_client.start(sandbox)
                    # Wait a moment for the sandbox to initialize
                    # sleep(5)
                    # Refresh sandbox state after starting
                    sandbox = await self.daytona_client.get(sandbox_id)
                    
                    # Start supervisord in a session when restarting
                    await self.start_supervisord_session(sandbox)
                except Exception as e:
                    self.logger.error(f"Error starting sandbox: {e}")
                    raise e
            
            self.logger.info(f"Sandbox {sandbox_id} is ready")
            return sandbox
            
        except Exception as e:
            self.logger.error(f"Error retrieving or starting sandbox: {str(e)}")
            raise e
    
    async def create_sandbox(self, password: str = None, project_id: str = None) -> AsyncSandbox:
        """Create a new sandbox with all required services configured and running."""
        
        self.logger.debug("Creating new Daytona sandbox environment")
        self.logger.debug("Configuring sandbox with snapshot and environment variables")
        
        labels = None
        if project_id:
            self.logger.debug(f"Using project_id as label: {project_id}")
            labels = {'id': project_id}
        
        # Set default password if none provided
        if not password:
            password = "vyuh123"
        
        env_vars = {
            "RESOLUTION": "1024x768x24",
            "RESOLUTION_WIDTH": "1024",
            "RESOLUTION_HEIGHT": "768",
            "VNC_PASSWORD": password,
            "ANONYMIZED_TELEMETRY": "false"
        }
        
        # Create sandbox with snapshot
        params = CreateSandboxFromSnapshotParams(
            snapshot=self.sandbox_snapshot,
            public=True,
            labels=labels,
            env_vars=env_vars,
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
        await self.start_supervisord_session(sandbox)
        
        self.logger.debug(f"Sandbox environment successfully initialized")
        return sandbox
    
    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox by its ID."""
        self.logger.info(f"Deleting sandbox with ID: {sandbox_id}")

        try:
            # Get the sandbox
            sandbox = await self.daytona_client.get(sandbox_id)
            
            # Delete the sandbox
            await self.daytona_client.delete(sandbox)
            
            self.logger.info(f"Successfully deleted sandbox {sandbox_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting sandbox {sandbox_id}: {str(e)}")
            raise e
    
    async def get_sandbox_status(self, sandbox_id: str = None) -> Dict[str, Any]:
        """Get the status of a sandbox."""
        try:
            if not sandbox_id:
                sandbox_id = self.sandbox_id
            
            if not sandbox_id:
                return {"error": "No sandbox ID provided"}
            
            sandbox = await self.daytona_client.get(sandbox_id)
            return {
                "sandbox_id": sandbox.id,
                "state": str(sandbox.state),
                "created_at": str(sandbox.created_at) if hasattr(sandbox, 'created_at') else None,
                "status": "active" if sandbox.state == SandboxState.RUNNING else "inactive"
            }
        except Exception as e:
            self.logger.error(f"Error getting sandbox status: {str(e)}")
            return {"error": str(e)}
    
    async def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all available sandboxes."""
        try:
            sandboxes = await self.daytona_client.list()
            return [
                {
                    "id": sandbox.id,
                    "state": str(sandbox.state),
                    "created_at": str(sandbox.created_at) if hasattr(sandbox, 'created_at') else None,
                    "labels": getattr(sandbox, 'labels', {})
                }
                for sandbox in sandboxes
            ]
        except Exception as e:
            self.logger.error(f"Error listing sandboxes: {str(e)}")
            return []
    
    async def start_sandbox(self, sandbox_id: str) -> bool:
        """Start a stopped sandbox."""
        try:
            sandbox = await self.daytona_client.get(sandbox_id)
            await self.daytona_client.start(sandbox)
            self.logger.info(f"Sandbox {sandbox_id} started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error starting sandbox {sandbox_id}: {str(e)}")
            return False
    
    async def stop_sandbox(self, sandbox_id: str) -> bool:
        """Stop a running sandbox."""
        try:
            sandbox = await self.daytona_client.get(sandbox_id)
            await self.daytona_client.stop(sandbox)
            self.logger.info(f"Sandbox {sandbox_id} stopped successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping sandbox {sandbox_id}: {str(e)}")
            return False
    
    async def wait_for_sandbox_ready(self, sandbox_id: str, timeout: int = 60) -> bool:
        """Wait for a sandbox to be ready (running state)."""
        try:
            import asyncio
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                status = await self.get_sandbox_status(sandbox_id)
                if "error" not in status and status.get("state") == "RUNNING":
                    self.logger.info(f"Sandbox {sandbox_id} is ready")
                    return True
                
                await asyncio.sleep(2)
            
            self.logger.warning(f"Timeout waiting for sandbox {sandbox_id} to be ready")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for sandbox ready: {str(e)}")
            return False
    
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
            if self.sandbox_id and self.daytona_client:
                try:
                    await self.delete_sandbox(self.sandbox_id)
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
