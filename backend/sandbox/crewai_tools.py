from crewai import Tool
from typing import Dict, Any, Optional
from .file_tool import FileTool
from .shell_tool import ShellTool
from .pdf_tool import PDFTool
from .sandbox import SandboxManager

class FileCreationTool(Tool):
    """
    CrewAI tool wrapper for file operations in the sandbox environment.
    """
    
    def __init__(self, sandbox_manager: SandboxManager = None):
        super().__init__(
            name="file_creation_tool",
            description="Create, edit, delete, and list files in the sandbox workspace. Supports text, code, and binary files.",
            function_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "edit", "delete", "list"],
                        "description": "The file operation to perform"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file (required for create, edit, delete)"
                    },
                    "content": {
                        "type": "string",
                        "description": "File content (required for create, edit)"
                    },
                    "file_type": {
                        "type": "string",
                        "enum": ["text", "binary"],
                        "default": "text",
                        "description": "Type of file to create"
                    },
                    "path": {
                        "type": "string",
                        "default": ".",
                        "description": "Directory path for list operations"
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to show hidden files in list operations"
                    }
                },
                "required": ["action"]
            }
        )
        self.sandbox_manager = sandbox_manager
        self.file_tool = FileTool(sandbox_manager) if sandbox_manager else None
    
    def _run(self, **kwargs) -> str:
        """Execute the file operation."""
        if not self.file_tool:
            return "ERROR: Sandbox manager not initialized. Please set sandbox manager first."
        
        try:
            result = self.file_tool._run(**kwargs)
            return str(result)
        except Exception as e:
            return f"ERROR: File operation failed: {str(e)}"
    
    def set_sandbox_manager(self, sandbox_manager: SandboxManager):
        """Set the sandbox manager for this tool."""
        self.sandbox_manager = sandbox_manager
        self.file_tool = FileTool(sandbox_manager)

class CommandExecutionTool(Tool):
    """
    CrewAI tool wrapper for command execution in the sandbox environment.
    """
    
    def __init__(self, sandbox_manager: SandboxManager = None):
        super().__init__(
            name="command_execution_tool",
            description="Execute shell commands and scripts safely in the sandbox. Supports bash, Python, and other script types.",
            function_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["execute", "run_script", "get_output"],
                        "description": "The command operation to perform"
                    },
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute (required for execute and get_output)"
                    },
                    "script_content": {
                        "type": "string",
                        "description": "Script content to execute (required for run_script)"
                    },
                    "script_type": {
                        "type": "string",
                        "enum": ["bash", "python", "perl", "ruby", "javascript"],
                        "default": "bash",
                        "description": "Type of script to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "description": "Command timeout in seconds"
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Working directory for command execution"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "File path for get_output operations"
                    }
                },
                "required": ["action"]
            }
        )
        self.sandbox_manager = sandbox_manager
        self.shell_tool = ShellTool(sandbox_manager) if sandbox_manager else None
    
    def _run(self, **kwargs) -> str:
        """Execute the command operation."""
        if not self.shell_tool:
            return "ERROR: Sandbox manager not initialized. Please set sandbox manager first."
        
        try:
            result = self.shell_tool._run(**kwargs)
            return str(result)
        except Exception as e:
            return f"ERROR: Command execution failed: {str(e)}"
    
    def set_sandbox_manager(self, sandbox_manager: SandboxManager):
        """Set the sandbox manager for this tool."""
        self.sandbox_manager = sandbox_manager
        self.shell_tool = ShellTool(sandbox_manager)

class PDFGenerationTool(Tool):
    """
    CrewAI tool wrapper for PDF generation in the sandbox environment.
    """
    
    def __init__(self, sandbox_manager: SandboxManager = None):
        super().__init__(
            name="pdf_generation_tool",
            description="Generate PDFs from HTML and text using wkhtmltopdf. Supports templates and custom styling.",
            function_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_from_html", "create_from_text"],
                        "description": "The PDF generation method"
                    },
                    "html_content": {
                        "type": "string",
                        "description": "HTML content for PDF generation (required for create_from_html)"
                    },
                    "text_content": {
                        "type": "string",
                        "description": "Text content for PDF generation (required for create_from_text)"
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "Output PDF filename (required)"
                    },
                    "template_data": {
                        "type": "object",
                        "description": "Template variables for HTML content (optional)"
                    },
                    "styling": {
                        "type": "object",
                        "description": "CSS styling options for text to PDF conversion (optional)"
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional wkhtmltopdf options (optional)"
                    }
                },
                "required": ["action", "output_filename"]
            }
        )
        self.sandbox_manager = sandbox_manager
        self.pdf_tool = PDFTool(sandbox_manager) if sandbox_manager else None
    
    def _run(self, **kwargs) -> str:
        """Execute the PDF generation operation."""
        if not self.pdf_tool:
            return "ERROR: Sandbox manager not initialized. Please set sandbox manager first."
        
        try:
            result = self.pdf_tool._run(**kwargs)
            return str(result)
        except Exception as e:
            return f"ERROR: PDF generation failed: {str(e)}"
    
    def set_sandbox_manager(self, sandbox_manager: SandboxManager):
        """Set the sandbox manager for this tool."""
        self.sandbox_manager = sandbox_manager
        self.pdf_tool = PDFTool(sandbox_manager)

class SandboxToolFactory:
    """
    Factory class for creating and configuring sandbox tools with CrewAI integration.
    """
    
    def __init__(self, sandbox_manager: SandboxManager):
        self.sandbox_manager = sandbox_manager
    
    def create_file_tool(self) -> FileCreationTool:
        """Create a configured file creation tool."""
        tool = FileCreationTool(self.sandbox_manager)
        return tool
    
    def create_command_tool(self) -> CommandExecutionTool:
        """Create a configured command execution tool."""
        tool = CommandExecutionTool(self.sandbox_manager)
        return tool
    
    def create_pdf_tool(self) -> PDFGenerationTool:
        """Create a configured PDF generation tool."""
        tool = PDFGenerationTool(self.sandbox_manager)
        return tool
    
    def create_all_tools(self) -> Dict[str, Tool]:
        """Create all available sandbox tools."""
        return {
            "file_tool": self.create_file_tool(),
            "command_tool": self.create_command_tool(),
            "pdf_tool": self.create_pdf_tool()
        }

# Convenience functions for easy tool creation
def create_sandbox_tools(sandbox_manager: SandboxManager) -> Dict[str, Tool]:
    """
    Create all sandbox tools with the given sandbox manager.
    
    Args:
        sandbox_manager: Initialized SandboxManager instance
        
    Returns:
        Dictionary containing all available tools
    """
    factory = SandboxToolFactory(sandbox_manager)
    return factory.create_all_tools()

def create_file_tool(sandbox_manager: SandboxManager) -> FileCreationTool:
    """Create a file creation tool."""
    return FileCreationTool(sandbox_manager)

def create_command_tool(sandbox_manager: SandboxManager) -> CommandExecutionTool:
    """Create a command execution tool."""
    return CommandExecutionTool(sandbox_manager)

def create_pdf_tool(sandbox_manager: SandboxManager) -> PDFGenerationTool:
    """Create a PDF generation tool."""
    return PDFGenerationTool(sandbox_manager)
