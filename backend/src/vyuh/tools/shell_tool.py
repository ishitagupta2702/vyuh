import sys
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from extend_tool_base import SandboxBaseTool


class SandboxShellTool(SandboxBaseTool):
    """
    Simple shell tool that extends SandboxBaseTool for command execution.
    Works with Daytona sandbox and CrewAI agents.
    """
    
    def __init__(self, name: str, description: str, project_id: str):
        super().__init__(name=name, description=description, project_id=project_id)
        self._workspace_path = "/workspace"
        self._last_command_output = None
        self._last_command_session = None
    
    @property
    def workspace_path(self) -> str:
        """Get the workspace path"""
        return self._workspace_path
    
    @property
    def last_command_output(self):
        """Get the last command output"""
        return self._last_command_output
    
    @property
    def last_command_session(self):
        """Get the last command session"""
        return self._last_command_session
    
    async def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method that routes to specific shell operations.
        """
        operation = kwargs.get('operation')
        
        if operation == 'execute_command':
            return await self._execute_command_operation(
                kwargs.get('command')
            )
        elif operation == 'run_script':
            return await self._run_script_operation(
                kwargs.get('script_content')
            )
        elif operation == 'get_output':
            return await self._get_output_operation()
        else:
            return self.fail_response(f"Unknown operation: {operation}")
    
    async def _execute_command_operation(self, command: str) -> Dict[str, Any]:
        """
        Execute a shell command in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            if not command:
                return self.fail_response("command is required")
            
            # Create a session for command execution
            session_id = f"cmd_{asyncio.get_event_loop().time()}"
            await self.sandbox.process.create_session(session_id)
            
            # Execute the command
            result = await self.sandbox.process.execute_session_command(
                session_id, 
                command=command,
                timeout=60
            )
            
            # Store output for later retrieval
            self._last_command_output = result.output if hasattr(result, 'output') else str(result)
            self._last_command_session = session_id
            
            # Clean up session
            try:
                await self.sandbox.process.delete_session(session_id)
            except:
                pass
            
            return self.success_response({
                "command": command,
                "output": self.last_command_output,
                "status": "completed"
            })
            
        except Exception as e:
            return self.fail_response(f"Error executing command: {str(e)}")
    
    async def _run_script_operation(self, script_content: str) -> Dict[str, Any]:
        """
        Execute script content in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            if not script_content:
                return self.fail_response("script_content is required")
            
            # Create a temporary script file
            script_name = f"script_{asyncio.get_event_loop().time()}.sh"
            script_path = f"{self.workspace_path}/{script_name}"
            
            # Upload script content
            await self.sandbox.fs.upload_file(
                path=script_path,
                content=script_content.encode('utf-8')
            )
            
            # Make script executable
            await self.sandbox.process.execute_session_command(
                "temp_session",
                command=f"chmod +x {script_path}",
                timeout=30
            )
            
            # Execute the script
            result = await self.sandbox.process.execute_session_command(
                "temp_session",
                command=f"bash {script_path}",
                timeout=120
            )
            
            # Clean up script file
            try:
                await self.sandbox.fs.delete_file(script_path)
            except:
                pass
            
            # Store output
            self.last_command_output = result.output if hasattr(result, 'output') else str(result)
            
            return self.success_response({
                "script": script_name,
                "output": self.last_command_output,
                "status": "completed"
            })
            
        except Exception as e:
            return self.fail_response(f"Error running script: {str(e)}")
    
    async def _get_output_operation(self) -> Dict[str, Any]:
        """
        Get the output from the last executed command or script.
        """
        try:
            if not self.last_command_output:
                return self.fail_response("No command output available. Execute a command first.")
            
            return self.success_response({
                "output": self.last_command_output,
                "session": self.last_command_session
            })
            
        except Exception as e:
            return self.fail_response(f"Error getting output: {str(e)}")
    
    # Convenience methods for direct usage
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Convenience method to execute a command.
        """
        return await self._execute_command_operation(command)
    
    async def run_script(self, script_content: str) -> Dict[str, Any]:
        """
        Convenience method to run a script.
        """
        return await self._run_script_operation(script_content)
    
    async def get_output(self) -> Dict[str, Any]:
        """
        Convenience method to get command output.
        """
        return await self._get_output_operation()
    
    def _is_safe_command(self, command: str) -> bool:
        """
        Basic safety check for potentially dangerous commands.
        """
        dangerous_commands = [
            'rm -rf /', 'rm -rf /*', 'dd if=/dev/zero', 'mkfs', 'fdisk',
            'shutdown', 'reboot', 'halt', 'poweroff', 'init 0', 'init 6'
        ]
        
        command_lower = command.lower().strip()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                return False
        
        return True
