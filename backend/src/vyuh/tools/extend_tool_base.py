import sys
from pathlib import Path
import asyncio
from typing import Dict, Any, Optional
from crewai.tools import BaseTool

# Add sandbox path to import sandbox tools
project_root = Path(__file__).parent.parent.parent.parent
sandbox_path = project_root / "sandbox"
sys.path.insert(0, str(sandbox_path))

from sandbox.sandbox import SandboxManager


class SandboxBaseTool(BaseTool):
    """
    Simple base class that extends CrewAI Tool and integrates with Daytona sandbox.
    Replaces complex AgentPress dependencies with simple, working code.
    """
    
    def __init__(self, name: str, description: str, project_id: str):
        super().__init__(name=name, description=description)
        # Store project_id as a custom attribute
        self._project_id = project_id
        self._sandbox_manager = None
        self._sandbox = None
    
    @property
    def project_id(self) -> str:
        """Get the project ID"""
        return self._project_id
    
    @property
    def sandbox_manager(self):
        """Get the sandbox manager"""
        return self._sandbox_manager
    
    @property
    def sandbox(self):
        """Get the sandbox instance"""
        return self._sandbox
    
    async def _ensure_sandbox(self) -> bool:
        """
        Ensure Daytona sandbox is initialized and ready.
        Returns True if successful, False otherwise.
        """
        try:
            if not self._sandbox_manager:
                self._sandbox_manager = SandboxManager()
                await self._sandbox_manager.initialize_sandbox()
                self._sandbox = self._sandbox_manager.sandbox
            
            if not self._sandbox:
                # Fallback: try to create a new sandbox
                self._sandbox = await self._sandbox_manager.create_sandbox()
            
            return True
        except Exception as e:
            print(f"Error ensuring sandbox: {e}")
            return False
    
    def success_response(self, data: Any) -> Dict[str, Any]:
        """
        Return a standardized success response.
        
        Args:
            data: The data to include in the response
            
        Returns:
            Dict with success=True and output=data
        """
        return {
            "success": True,
            "output": data,
            "project_id": self.project_id
        }
    
    def fail_response(self, error: Any) -> Dict[str, Any]:
        """
        Return a standardized failure response.
        
        Args:
            error: The error message or exception
            
        Returns:
            Dict with success=False and error=str(error)
        """
        return {
            "success": False,
            "error": str(error),
            "project_id": self.project_id
        }
    
    async def cleanup_sandbox(self):
        """
        Clean up the Daytona sandbox resources.
        """
        try:
            if self._sandbox_manager:
                await self._sandbox_manager.cleanup()
                self._sandbox_manager = None
                self._sandbox = None
        except Exception as e:
            print(f"Error cleaning up sandbox: {e}")
    
    def _run(self, **kwargs) -> str:
        """
        Override CrewAI's _run method to handle async execution.
        This allows subclasses to use async methods while maintaining CrewAI compatibility.
        """
        try:
            # Check if the subclass has an async _execute_tool method
            if hasattr(self, '_execute_tool') and asyncio.iscoroutinefunction(self._execute_tool):
                # Run async tool in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self._execute_tool(**kwargs))
                finally:
                    loop.close()
            else:
                # Fallback to sync execution
                result = self._execute_tool(**kwargs)
            
            # Format the result
            if isinstance(result, dict):
                return str(result)
            return str(result)
            
        except Exception as e:
            return str(self.fail_response(e))
    
    def __del__(self):
        """
        Cleanup when the tool is destroyed.
        """
        try:
            if self._sandbox_manager:
                # Run cleanup in a new event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create a new thread for cleanup if main loop is running
                        import threading
                        def cleanup_async():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                new_loop.run_until_complete(self.cleanup_sandbox())
                            finally:
                                new_loop.close()
                        
                        thread = threading.Thread(target=cleanup_async)
                        thread.daemon = True
                        thread.start()
                    else:
                        loop.run_until_complete(self.cleanup_sandbox())
                except:
                    pass
        except:
            pass
