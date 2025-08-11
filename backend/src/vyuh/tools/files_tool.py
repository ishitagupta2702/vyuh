import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from extend_tool_base import SandboxBaseTool


class SandboxFilesTool(SandboxBaseTool):
    """
    Simple file tool that extends SandboxBaseTool for basic file operations.
    Works with Daytona sandbox and CrewAI agents.
    """
    
    def __init__(self, name: str, description: str, project_id: str):
        super().__init__(name=name, description=description, project_id=project_id)
        self._workspace_path = "/workspace"
    
    @property
    def workspace_path(self) -> str:
        """Get the workspace path"""
        return self._workspace_path
    
    def _clean_path(self, file_path: str) -> str:
        """
        Clean and normalize file path to be relative to workspace.
        """
        # Remove leading slashes and workspace prefix
        clean_path = file_path.lstrip('/').lstrip('workspace/')
        return clean_path
    
    async def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method that routes to specific file operations.
        """
        operation = kwargs.get('operation')
        
        if operation == 'create_file':
            return await self._create_file_operation(
                kwargs.get('file_path'),
                kwargs.get('file_contents')
            )
        elif operation == 'delete_file':
            return await self._delete_file_operation(
                kwargs.get('file_path')
            )
        elif operation == 'edit_file':
            return await self._edit_file_operation(
                kwargs.get('file_path'),
                kwargs.get('new_content')
            )
        else:
            return self.fail_response(f"Unknown operation: {operation}")
    
    async def _create_file_operation(self, file_path: str, file_contents: str) -> Dict[str, Any]:
        """
        Create a new file in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            if not file_path or not file_contents:
                return self.fail_response("file_path and file_contents are required")
            
            clean_path = self._clean_path(file_path)
            full_path = f"{self.workspace_path}/{clean_path}"
            
            # Create the file using sandbox file system
            await self.sandbox.fs.upload_file(
                path=full_path,
                content=file_contents.encode('utf-8')
            )
            
            return self.success_response(f"File '{clean_path}' created successfully")
            
        except Exception as e:
            return self.fail_response(f"Error creating file: {str(e)}")
    
    async def _delete_file_operation(self, file_path: str) -> Dict[str, Any]:
        """
        Delete an existing file in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            if not file_path:
                return self.fail_response("file_path is required")
            
            clean_path = self._clean_path(file_path)
            full_path = f"{self.workspace_path}/{clean_path}"
            
            # Check if file exists
            try:
                await self.sandbox.fs.get_file_info(full_path)
            except Exception:
                return self.fail_response(f"File '{clean_path}' does not exist")
            
            # Delete the file
            await self.sandbox.fs.delete_file(full_path)
            
            return self.success_response(f"File '{clean_path}' deleted successfully")
            
        except Exception as e:
            return self.fail_response(f"Error deleting file: {str(e)}")
    
    async def _edit_file_operation(self, file_path: str, new_content: str) -> Dict[str, Any]:
        """
        Edit an existing file in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            if not file_path or not new_content:
                return self.fail_response("file_path and new_content are required")
            
            clean_path = self._clean_path(file_path)
            full_path = f"{self.workspace_path}/{clean_path}"
            
            # Check if file_path exists
            try:
                await self.sandbox.fs.get_file_info(full_path)
            except Exception:
                return self.fail_response(f"File '{clean_path}' does not exist")
            
            # Update the file content
            await self.sandbox.fs.upload_file(
                path=full_path,
                content=new_content.encode('utf-8')
            )
            
            return self.success_response(f"File '{clean_path}' updated successfully")
            
        except Exception as e:
            return self.fail_response(f"Error editing file: {str(e)}")
    
    # Convenience methods for direct usage
    async def create_file(self, file_path: str, file_contents: str) -> Dict[str, Any]:
        """
        Convenience method to create a file.
        """
        return await self._create_file_operation(file_path, file_contents)
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Convenience method to delete a file.
        """
        return await self._delete_file_operation(file_path)
    
    async def edit_file(self, file_path: str, new_content: str) -> Dict[str, Any]:
        """
        Convenience method to edit a file.
        """
        return await self._edit_file_operation(file_path, new_content)
