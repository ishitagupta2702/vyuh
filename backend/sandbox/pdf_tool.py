import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
from tool_base import SandboxToolBase

class PDFTool(SandboxToolBase):
    """
    Tool for PDF generation using wkhtmltopdf in the sandbox environment.
    """
    
    def __init__(self, sandbox_manager=None):
        super().__init__(
            name="pdf_tool",
            description="Generate PDFs from HTML and text using wkhtmltopdf",
            sandbox_manager=sandbox_manager
        )
        self.wkhtmltopdf_path = "wkhtmltopdf"
        self.default_options = [
            '--quiet',
            '--encoding', 'UTF-8',
            '--page-size', 'A4',
            '--margin-top', '20mm',
            '--margin-right', '20mm',
            '--margin-bottom', '20mm',
            '--margin-left', '20mm'
        ]
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the PDF tool based on the action specified.
        
        Args:
            **kwargs: Must contain 'action' and action-specific parameters
            
        Returns:
            Dict containing operation result
        """
        action = kwargs.get('action')
        
        if action == 'create_from_html':
            return self._create_pdf_from_html_operation(**kwargs)
        elif action == 'create_from_text':
            return self._create_pdf_from_text_operation(**kwargs)
        else:
            raise ValueError(f"Unknown action: {action}. Supported actions: create_from_html, create_from_text")
    
    def _custom_validation(self, **kwargs) -> None:
        """Custom validation for PDF operations."""
        action = kwargs.get('action')
        if not action:
            raise ValueError("'action' parameter is required")
        
        if action not in ['create_from_html', 'create_from_text']:
            raise ValueError(f"Invalid action: {action}")
        
        if action == 'create_from_html':
            if 'html_content' not in kwargs:
                raise ValueError("'html_content' parameter is required for HTML to PDF conversion")
        
        if action == 'create_from_text':
            if 'text_content' not in kwargs:
                raise ValueError("'text_content' parameter is required for text to PDF conversion")
        
        if 'output_filename' not in kwargs:
            raise ValueError("'output_filename' parameter is required")
    
    def _create_pdf_from_html_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle HTML to PDF conversion operation."""
        html_content = kwargs['html_content']
        output_filename = kwargs['output_filename']
        options = kwargs.get('options', [])
        template_data = kwargs.get('template_data', {})
        
        try:
            # Apply template data if provided
            if template_data:
                html_content = self._apply_template(html_content, template_data)
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.html',
                dir=self.sandbox_manager.workspace_dir,
                delete=False,
                encoding='utf-8'
            ) as html_file:
                html_file.write(html_content)
                html_file.flush()
                html_path = html_file.name
            
            # Prepare output path
            output_path = Path(self.sandbox_manager.workspace_dir) / output_filename
            if not output_path.suffix.lower() == '.pdf':
                output_path = output_path.with_suffix('.pdf')
            
            # Build wkhtmltopdf command
            cmd = [self.wkhtmltopdf_path] + self.default_options + options + [html_path, str(output_path)]
            
            # Execute conversion
            result = subprocess.run(
                cmd,
                cwd=self.sandbox_manager.workspace_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Clean up temporary HTML file
            try:
                os.unlink(html_path)
            except:
                pass
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "PDF generation failed",
                    "stderr": result.stderr,
                    "message": f"Failed to generate PDF from HTML"
                }
            
            # Verify PDF was created
            if not output_path.exists():
                return {
                    "success": False,
                    "error": "PDF file not created",
                    "message": "PDF generation completed but file not found"
                }
            
            return {
                "success": True,
                "message": f"PDF generated successfully: {output_filename}",
                "output_path": str(output_path),
                "file_size": output_path.stat().st_size,
                "html_source_size": len(html_content)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "PDF generation timeout",
                "message": "PDF generation exceeded 60 second timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate PDF from HTML"
            }
    
    def _create_pdf_from_text_operation(self, **kwargs) -> Dict[str, Any]:
        """Handle text to PDF conversion operation."""
        text_content = kwargs['text_content']
        output_filename = kwargs['output_filename']
        options = kwargs.get('options', [])
        styling = kwargs.get('styling', {})
        
        try:
            # Convert text to HTML with styling
            html_content = self._text_to_html(text_content, styling)
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.html',
                dir=self.sandbox_manager.workspace_dir,
                delete=False,
                encoding='utf-8'
            ) as html_file:
                html_file.write(html_content)
                html_file.flush()
                html_path = html_file.name
            
            # Prepare output path
            output_path = Path(self.sandbox_manager.workspace_dir) / output_filename
            if not output_path.suffix.lower() == '.pdf':
                output_path = output_path.with_suffix('.pdf')
            
            # Build wkhtmltopdf command
            cmd = [self.wkhtmltopdf_path] + self.default_options + options + [html_path, str(output_path)]
            
            # Execute conversion
            result = subprocess.run(
                cmd,
                cwd=self.sandbox_manager.workspace_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Clean up temporary HTML file
            try:
                os.unlink(html_path)
            except:
                pass
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "PDF generation failed",
                    "stderr": result.stderr,
                    "message": f"Failed to generate PDF from text"
                }
            
            # Verify PDF was created
            if not output_path.exists():
                return {
                    "success": False,
                    "error": "PDF file not created",
                    "message": "PDF generation completed but file not found"
                }
            
            return {
                "success": True,
                "message": f"PDF generated successfully: {output_filename}",
                "output_path": str(output_path),
                "file_size": output_path.stat().st_size,
                "text_source_size": len(text_content)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "PDF generation timeout",
                "message": "PDF generation exceeded 60 second timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate PDF from text"
            }
    
    def _apply_template(self, html_content: str, template_data: Dict[str, Any]) -> str:
        """Apply template data to HTML content."""
        try:
            # Simple template variable replacement
            for key, value in template_data.items():
                placeholder = f"{{{{{key}}}}}"
                html_content = html_content.replace(placeholder, str(value))
            
            return html_content
        except Exception as e:
            self.logger.warning(f"Template application failed: {str(e)}")
            return html_content
    
    def _text_to_html(self, text_content: str, styling: Dict[str, Any]) -> str:
        """Convert plain text to HTML with styling."""
        # Default styling
        default_styling = {
            'font_family': 'Arial, sans-serif',
            'font_size': '12px',
            'line_height': '1.6',
            'color': '#333333',
            'background_color': '#ffffff'
        }
        
        # Merge with custom styling
        final_styling = {**default_styling, **styling}
        
        # Convert text to HTML
        html_lines = []
        for line in text_content.split('\n'):
            if line.strip():
                html_lines.append(f'<p>{line}</p>')
            else:
                html_lines.append('<br>')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Generated PDF</title>
            <style>
                body {{
                    font-family: {final_styling['font_family']};
                    font-size: {final_styling['font_size']};
                    line-height: {final_styling['line_height']};
                    color: {final_styling['color']};
                    background-color: {final_styling['background_color']};
                    margin: 0;
                    padding: 20px;
                }}
                p {{
                    margin: 0 0 10px 0;
                }}
            </style>
        </head>
        <body>
            {''.join(html_lines)}
        </body>
        </html>
        """
        
        return html_content
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get available wkhtmltopdf options and their descriptions."""
        return {
            "page_sizes": ["A4", "A3", "Letter", "Legal", "Tabloid"],
            "margins": ["10mm", "20mm", "30mm", "40mm"],
            "orientations": ["Portrait", "Landscape"],
            "common_options": [
                "--quiet",
                "--encoding UTF-8",
                "--no-outline",
                "--enable-local-file-access",
                "--disable-smart-shrinking"
            ]
        }
