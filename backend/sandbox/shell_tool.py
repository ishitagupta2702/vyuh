import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from tool_base import SandboxToolBase

class ShellTool(SandboxToolBase):
    """
    Tool for safe command execution in the sandbox environment.
    """
    
    def __init__(self, sandbox_manager=None):
        super().__init__(
            name="shell_tool",
            description="Execute shell commands and scripts safely in the sandbox",
            sandbox_manager=sandbox_manager
        )
        self.default_timeout = 30
        self.max_output_size = 1024 * 1024  # 1MB
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the shell tool based on the action specified.
        
        Args:
            **kwargs: Must contain 'action' and action-specific parameters
            
        Returns:
            Dict containing execution result
        """
        action = kwargs.get('action')
        
        if action == 'execute':
            return self._execute_command_operation(**kwargs)
        elif action == 'run_script':
            return self._run_script_operation(**kwargs)
        elif action == 'get_output':
            return self._get_output_operation(**kwargs)
        else:
            raise ValueError(f"Unknown action: {action}. Supported actions: execute, run_script, get_output")
    
    def _custom_validation(self, **kwargs) -> None:
        """Custom validation for shell operations."""
        action = kwargs.get('action')
        if not action:
            raise ValueError("'action' parameter is required")
        
        if action not in ['execute', 'run_script', 'get_output']:
            raise ValueError(f"Invalid action: {action}")
        
        if action == 'execute':
            if 'command' not in kwargs:
                raise ValueError("'command' parameter is required for execute operations")
        
        if action == 'run_script':
            if 'script_content' not in kwargs:
                raise ValueError("'script_content' parameter is required for run_script operations")
    
    def _execute_command_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle command execution operation."""
        command = kwargs['command']
        timeout = kwargs.get('timeout', self.default_timeout)
        working_dir = kwargs.get('working_dir', self.sandbox_manager.workspace_dir)
        
        try:
            # Validate command for security
            if not self._is_command_safe(command):
                return {
                    "success": False,
                    "error": "Command blocked for security reasons",
                    "message": f"Command '{command}' contains potentially unsafe operations"
                }
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Truncate output if too long
            stdout = self._truncate_output(result.stdout)
            stderr = self._truncate_output(result.stderr)
            
            return {
                "success": True,
                "command": command,
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time": "completed within timeout"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout",
                "message": f"Command '{command}' exceeded timeout of {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute command '{command}'"
            }
    
    def _run_script_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle script execution operation."""
        script_content = kwargs['script_content']
        script_type = kwargs.get('script_type', 'bash')
        timeout = kwargs.get('timeout', self.default_timeout)
        working_dir = kwargs.get('working_dir', self.sandbox_manager.workspace_dir)
        
        try:
            # Create temporary script file
            script_ext = self._get_script_extension(script_type)
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=script_ext,
                dir=working_dir,
                delete=False
            ) as script_file:
                script_file.write(script_content)
                script_file.flush()
                script_path = script_file.name
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Execute script
            if script_type == 'bash':
                result = subprocess.run(
                    ['bash', script_path],
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            elif script_type == 'python':
                result = subprocess.run(
                    ['python', script_path],
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                # Generic execution
                result = subprocess.run(
                    script_path,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            # Clean up script file
            try:
                os.unlink(script_path)
            except:
                pass
            
            # Truncate output if too long
            stdout = self._truncate_output(result.stdout)
            stderr = self._truncate_output(result.stderr)
            
            return {
                "success": True,
                "script_type": script_type,
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time": "completed within timeout"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script timeout",
                "message": f"Script exceeded timeout of {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to run script"
            }
    
    def _get_output_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle output retrieval operation."""
        command = kwargs.get('command')
        file_path = kwargs.get('file_path')
        
        try:
            if command:
                # Get output from command
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.sandbox_manager.workspace_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": result.stderr,
                    "return_code": result.returncode
                }
            
            elif file_path:
                # Get output from file
                full_path = Path(self.sandbox_manager.workspace_dir) / file_path
                
                if not full_path.exists():
                    return {
                        "success": False,
                        "error": "File not found",
                        "message": f"File '{file_path}' does not exist"
                    }
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "output": content,
                    "file_path": str(full_path)
                }
            
            else:
                return {
                    "success": False,
                    "error": "Missing parameter",
                    "message": "Either 'command' or 'file_path' must be specified"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get output"
            }
    
    def _is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute."""
        dangerous_patterns = [
            'rm -rf /',
            'dd if=',
            'mkfs',
            'fdisk',
            'mount',
            'umount',
            'chmod 777',
            'chown root',
            'sudo',
            'su -'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        
        return True
    
    def _truncate_output(self, output: str, max_size: int = None) -> str:
        """Truncate output if it exceeds maximum size."""
        if max_size is None:
            max_size = self.max_output_size
        
        if len(output) > max_size:
            return output[:max_size] + f"\n... [truncated, total size: {len(output)} bytes]"
        return output
    
    def _get_script_extension(self, script_type: str) -> str:
        """Get file extension for script type."""
        extensions = {
            'bash': '.sh',
            'python': '.py',
            'perl': '.pl',
            'ruby': '.rb',
            'javascript': '.js'
        }
        return extensions.get(script_type, '.sh')
