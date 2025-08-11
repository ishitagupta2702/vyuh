import sys
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import base64

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from extend_tool_base import SandboxBaseTool


class SandboxPDFTool(SandboxBaseTool):
    """
    Simple PDF tool that extends SandboxBaseTool for PDF creation.
    Works with Daytona sandbox and CrewAI agents.
    """
    
    def __init__(self, name: str, description: str, project_id: str):
        super().__init__(name=name, description=description, project_id=project_id)
        self._workspace_path = "/workspace"
        self._pdf_tools_installed = False
    
    @property
    def workspace_path(self) -> str:
        """Get the workspace path"""
        return self._workspace_path
    
    @property
    def pdf_tools_installed(self) -> bool:
        """Get the PDF tools installed status"""
        return self._pdf_tools_installed
    
    async def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method that routes to specific PDF operations.
        """
        operation = kwargs.get('operation')
        
        if operation == 'create_pdf_from_html':
            return await self._create_pdf_from_html_operation(
                kwargs.get('html_content'),
                kwargs.get('filename')
            )
        elif operation == 'create_pdf_from_text':
            return await self._create_pdf_from_text_operation(
                kwargs.get('text_content'),
                kwargs.get('filename')
            )
        elif operation == 'install_pdf_tools':
            return await self._install_pdf_tools_operation()
        else:
            return self.fail_response(f"Unknown operation: {operation}")
    
    async def _install_pdf_tools_operation(self) -> Dict[str, Any]:
        """
        Install required PDF tools in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            # Check if tools are already installed
            if self._pdf_tools_installed:
                return self.success_response("PDF tools already installed")
            
            # Install wkhtmltopdf and other required packages
            install_commands = [
                "apt-get update",
                "apt-get install -y wkhtmltopdf xvfb",
                "which wkhtmltopdf"
            ]
            
            for cmd in install_commands:
                try:
                    result = await self.sandbox.process.execute_session_command(
                        "install_session",
                        command=cmd,
                        timeout=120
                    )
                    print(f"Command '{cmd}' completed: {result}")
                except Exception as e:
                    print(f"Warning: Command '{cmd}' failed: {e}")
            
            self._pdf_tools_installed = True
            return self.success_response("PDF tools installed successfully")
            
        except Exception as e:
            return self.fail_response(f"Error installing PDF tools: {str(e)}")
    
    async def _create_pdf_from_html_operation(self, html_content: str, filename: str) -> Dict[str, Any]:
        """
        Create a PDF from HTML content in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            if not html_content or not filename:
                return self.fail_response("html_content and filename are required")
            
            # Ensure PDF tools are installed
            if not self._pdf_tools_installed:
                await self._install_pdf_tools_operation()
            
            # Create temporary HTML file
            temp_html = f"temp_{asyncio.get_event_loop().time()}.html"
            temp_html_path = f"{self._workspace_path}/{temp_html}"
            
            # Upload HTML content
            await self.sandbox.fs.upload_file(
                path=temp_html_path,
                content=html_content.encode('utf-8')
            )
            
            # Create PDF filename
            if not filename.endswith('.pdf'):
                filename = f"{filename}.pdf"
            
            pdf_path = f"{self.workspace_path}/{filename}"
            
            # Convert HTML to PDF using wkhtmltopdf
            pdf_command = f"wkhtmltopdf --quiet --encoding utf-8 {temp_html_path} {pdf_path}"
            
            result = await self.sandbox.process.execute_session_command(
                "pdf_session",
                command=pdf_command,
                timeout=60
            )
            
            # Check if PDF was created
            try:
                pdf_info = await self.sandbox.fs.get_file_info(pdf_path)
                pdf_size = pdf_info.size if hasattr(pdf_info, 'size') else 0
            except Exception:
                pdf_size = 0
            
            # Clean up temporary HTML file
            try:
                await self.sandbox.fs.delete_file(temp_html_path)
            except:
                pass
            
            if pdf_size > 0:
                return self.success_response({
                    "message": f"PDF '{filename}' created successfully",
                    "filename": filename,
                    "size_bytes": pdf_size,
                    "source": "html"
                })
            else:
                return self.fail_response("PDF creation failed - no output file generated")
            
        except Exception as e:
            return self.fail_response(f"Error creating PDF from HTML: {str(e)}")
    
    async def _create_pdf_from_text_operation(self, text_content: str, filename: str) -> Dict[str, Any]:
        """
        Create a PDF from text content in the Daytona sandbox.
        """
        try:
            if not await self._ensure_sandbox():
                return self.fail_response("Failed to initialize sandbox")
            
            if not text_content or not filename:
                return self.fail_response("text_content and filename are required")
            
            # Ensure PDF tools are installed
            if not self._pdf_tools_installed:
                await self._install_pdf_tools_operation()
            
            # Convert text to simple HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Text to PDF</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    pre {{ white-space: pre-wrap; font-family: monospace; background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <pre>{text_content}</pre>
            </body>
            </html>
            """
            
            # Create PDF using the HTML method
            return await self._create_pdf_from_html_operation(html_content, filename)
            
        except Exception as e:
            return self.fail_response(f"Error creating PDF from text: {str(e)}")
    
    # Convenience methods for direct usage
    async def create_pdf_from_html(self, html_content: str, filename: str) -> Dict[str, Any]:
        """
        Convenience method to create PDF from HTML.
        """
        return await self._create_pdf_from_html_operation(html_content, filename)
    
    async def create_pdf_from_text(self, text_content: str, filename: str) -> Dict[str, Any]:
        """
        Convenience method to create PDF from text.
        """
        return await self._create_pdf_from_text_operation(text_content, filename)
    
    async def install_pdf_tools(self) -> Dict[str, Any]:
        """
        Convenience method to install PDF tools.
        """
        return await self._install_pdf_tools_operation()
    
    def _validate_filename(self, filename: str) -> bool:
        """
        Validate filename for safety.
        """
        if not filename:
            return False
        
        # Remove any path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Ensure filename is reasonable length
        if len(filename) > 100:
            return False
        
        return True
