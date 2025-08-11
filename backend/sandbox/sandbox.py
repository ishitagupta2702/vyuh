import os
import logging
import docker
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SandboxManager:
    """
    Manages Docker-based sandbox environments for safe code execution.
    """
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or tempfile.mkdtemp(prefix="sandbox_")
        self.docker_client = docker.from_env()
        self.container = None
        self.network_name = "sandbox_network"
        self.logger = logger
        
    def initialize_sandbox(self) -> bool:
        """
        Initialize the sandbox environment and start Docker container.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("Initializing sandbox environment...")
            
            # Ensure workspace directory exists
            Path(self.workspace_dir).mkdir(parents=True, exist_ok=True)
            
            # Check if network exists, create if not
            try:
                self.docker_client.networks.get(self.network_name)
            except docker.errors.NotFound:
                self.docker_client.networks.create(self.network_name, driver="bridge")
                self.logger.info(f"Created network: {self.network_name}")
            
            # Start container using docker-compose
            self._start_container()
            
            self.logger.info("Sandbox initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sandbox: {str(e)}")
            return False
    
    def _start_container(self):
        """Start the sandbox container using docker-compose."""
        try:
            # Use docker-compose to start services
            import subprocess
            docker_compose_path = os.path.join(os.path.dirname(__file__), "docker", "docker-compose.yml")
            
            if not os.path.exists(docker_compose_path):
                raise FileNotFoundError(f"Docker-compose file not found at {docker_compose_path}")
            
            # Start services
            result = subprocess.run(
                ["docker-compose", "-f", docker_compose_path, "up", "-d", "sandbox"],
                cwd=os.path.dirname(docker_compose_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to start container: {result.stderr}")
                
            self.logger.info("Container started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start container: {str(e)}")
            raise
    
    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command in the sandbox container.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Dict containing execution results
        """
        try:
            if not self.container:
                raise RuntimeError("Sandbox not initialized. Call initialize_sandbox() first.")
            
            self.logger.info(f"Executing command: {command}")
            
            # Execute command in container
            result = self.docker_client.containers.run(
                self.container.id,
                command,
                timeout=timeout,
                detach=False,
                remove=True
            )
            
            return {
                "success": True,
                "stdout": result.decode('utf-8') if result else "",
                "stderr": "",
                "return_code": 0
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
    
    def cleanup(self):
        """Clean up sandbox resources and stop containers."""
        try:
            self.logger.info("Cleaning up sandbox...")
            
            # Stop and remove containers
            if self.container:
                try:
                    self.container.stop(timeout=10)
                    self.container.remove()
                except Exception as e:
                    self.logger.warning(f"Failed to remove container: {str(e)}")
            
            # Stop docker-compose services
            try:
                import subprocess
                docker_compose_path = os.path.join(os.path.dirname(__file__), "docker", "docker-compose.yml")
                
                if os.path.exists(docker_compose_path):
                    subprocess.run(
                        ["docker-compose", "-f", docker_compose_path, "down"],
                        cwd=os.path.dirname(docker_compose_path),
                        capture_output=True
                    )
            except Exception as e:
                self.logger.warning(f"Failed to stop docker-compose services: {str(e)}")
            
            # Clean up workspace directory
            if os.path.exists(self.workspace_dir) and self.workspace_dir.startswith(tempfile.gettempdir()):
                shutil.rmtree(self.workspace_dir, ignore_errors=True)
            
            self.logger.info("Sandbox cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize_sandbox()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
