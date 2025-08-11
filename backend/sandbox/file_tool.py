import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from tool_base import SandboxToolBase

class FileTool(SandboxToolBase):
    """
    Tool for file creation and management in the sandbox environment.
    """
    
    def __init__(self, sandbox_manager=None):
        super().__init__(
            name="file_tool",
            description="Create, edit, delete, and list files in the sandbox workspace",
            sandbox_manager=sandbox_manager
        )
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the file tool based on the action specified.
        
        Args:
            **kwargs: Must contain 'action' and action-specific parameters
            
        Returns:
            Dict containing operation result
        """
        action = kwargs.get('action')
        
        if action == 'create':
            return self._create_file_operation(**kwargs)
        elif action == 'edit':
            return self._edit_file_operation(**kwargs)
        elif action == 'delete':
            return self._edit_file_operation(**kwargs)
        elif action == 'list':
            return self._list_files_operation(**kwargs)
        else:
            raise ValueError(f"Unknown action: {action}. Supported actions: create, edit, delete, list")
    
    def _custom_validation(self, **kwargs) -> None:
        """Custom validation for file operations."""
        action = kwargs.get('action')
        if not action:
            raise ValueError("'action' parameter is required")
        
        if action not in ['create', 'edit', 'delete', 'list']:
            raise ValueError(f"Invalid action: {action}")
        
        if action in ['create', 'edit']:
            if 'filename' not in kwargs:
                raise ValueError("'filename' parameter is required for create/edit operations")
            if 'content' not in kwargs:
                raise ValueError("'content' parameter is required for create/edit operations")
        
        if action == 'delete':
            if 'filename' not in kwargs:
                raise ValueError("'filename' parameter is required for delete operations")
    
    def _create_file_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle file creation operation."""
        filename = kwargs['filename']
        content = kwargs['content']
        file_type = kwargs.get('file_type', 'text')
        
        try:
            file_path = Path(self.sandbox_manager.workspace_dir) / filename
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle different file types
            if file_type == 'binary':
                # For binary content, expect bytes
                if isinstance(content, str):
                    content = content.encode('utf-8')
                with open(file_path, 'wb') as f:
                    f.write(content)
            else:
                # For text files
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return {
                "success": True,
                "message": f"File '{filename}' created successfully",
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create file '{filename}'"
            }
    
    def _edit_file_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle file editing operation."""
        filename = kwargs['filename']
        content = kwargs['content']
        file_type = kwargs.get('file_type', 'text')
        
        try:
            file_path = Path(self.sandbox_manager.workspace_dir) / filename
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"File '{filename}' does not exist"
                }
            
            # Handle different file types
            if file_type == 'binary':
                if isinstance(content, str):
                    content = content.encode('utf-8')
                with open(file_path, 'wb') as f:
                    f.write(content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return {
                "success": True,
                "message": f"File '{filename}' edited successfully",
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to edit file '{filename}'"
            }
    
    def _delete_file_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle file deletion operation."""
        filename = kwargs['filename']
        
        try:
            file_path = Path(self.sandbox_manager.workspace_dir) / filename
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"File '{filename}' does not exist"
                }
            
            # Remove file or directory
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            
            return {
                "success": True,
                "message": f"'{filename}' deleted successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete '{filename}'"
            }
    
    def _list_files_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle file listing operation."""
        path = kwargs.get('path', '.')
        show_hidden = kwargs.get('show_hidden', False)
        
        try:
            base_path = Path(self.sandbox_manager.workspace_dir)
            target_path = base_path / path
            
            if not target_path.exists():
                return {
                    "success": False,
                    "error": "Path not found",
                    "message": f"Path '{path}' does not exist"
                }
            
            files = []
            for item in target_path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                file_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                }
                files.append(file_info)
            
            return {
                "success": True,
                "files": files,
                "path": str(target_path),
                "count": len(files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list files in '{path}'"
            }
