from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import logging
from crewai import Tool

logger = logging.getLogger(__name__)

class SandboxToolBase(Tool, ABC):
    """
    Base class for sandbox tools that integrate with CrewAI.
    Extends the CrewAI Tool class with sandbox-specific functionality.
    """
    
    def __init__(self, name: str, description: str, sandbox_manager=None, **kwargs):
        """
        Initialize the sandbox tool.
        
        Args:
            name: Tool name
            description: Tool description
            sandbox_manager: SandboxManager instance
            **kwargs: Additional arguments for CrewAI Tool
        """
        super().__init__(name=name, description=description, **kwargs)
        self.sandbox_manager = sandbox_manager
        self.logger = logger
        
    def _run(self, **kwargs) -> str:
        """
        Main execution method that CrewAI calls.
        This method validates input, runs the tool, and handles errors.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            str: Tool execution result
        """
        try:
            # Validate input parameters
            self._validate_input(**kwargs)
            
            # Execute the tool logic
            result = self._execute_tool(**kwargs)
            
            # Format and return result
            return self._format_result(result)
            
        except Exception as e:
            # Handle and log errors
            error_result = self._handle_error(e, **kwargs)
            return error_result
    
    @abstractmethod
    def _execute_tool(self, **kwargs) -> Any:
        """
        Abstract method that subclasses must implement.
        Contains the actual tool logic.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            Any: Tool execution result
        """
        pass
    
    def _validate_input(self, **kwargs) -> None:
        """
        Validate input parameters before execution.
        
        Args:
            **kwargs: Input parameters to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Base validation - subclasses can override
        if not self.sandbox_manager:
            raise ValueError("Sandbox manager is required but not provided")
        
        # Log validation
        self.logger.debug(f"Validating input for tool {self.name}: {kwargs}")
        
        # Additional validation can be implemented by subclasses
        self._custom_validation(**kwargs)
    
    def _custom_validation(self, **kwargs) -> None:
        """
        Custom validation logic that subclasses can implement.
        Default implementation does nothing.
        
        Args:
            **kwargs: Input parameters to validate
        """
        pass
    
    def _handle_error(self, error: Exception, **kwargs) -> str:
        """
        Handle errors that occur during tool execution.
        
        Args:
            error: The exception that occurred
            **kwargs: Original input parameters
            
        Returns:
            str: Error message formatted for CrewAI
        """
        error_msg = f"Tool {self.name} failed: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        
        # Return formatted error message
        return f"ERROR: {error_msg}"
    
    def _format_result(self, result: Any) -> str:
        """
        Format the tool execution result for CrewAI.
        
        Args:
            result: Raw tool execution result
            
        Returns:
            str: Formatted result string
        """
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            # Convert dict to readable string
            return self._dict_to_string(result)
        elif isinstance(result, (list, tuple)):
            # Convert list/tuple to readable string
            return self._list_to_string(result)
        else:
            return str(result)
    
    def _dict_to_string(self, data: Dict[str, Any]) -> str:
        """
        Convert dictionary to readable string format.
        
        Args:
            data: Dictionary to convert
            
        Returns:
            str: Formatted string representation
        """
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}: {sub_value}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _list_to_string(self, data: Union[list, tuple]) -> str:
        """
        Convert list or tuple to readable string format.
        
        Args:
            data: List or tuple to convert
            
        Returns:
            str: Formatted string representation
        """
        if not data:
            return "[]"
        
        lines = []
        for i, item in enumerate(data):
            if isinstance(item, dict):
                lines.append(f"[{i}]:")
                for key, value in item.items():
                    lines.append(f"  {key}: {value}")
            else:
                lines.append(f"[{i}]: {item}")
        return "\n".join(lines)
    
    def set_sandbox_manager(self, sandbox_manager):
        """
        Set the sandbox manager for this tool.
        
        Args:
            sandbox_manager: SandboxManager instance
        """
        self.sandbox_manager = sandbox_manager
        self.logger.info(f"Sandbox manager set for tool {self.name}")
    
    def get_sandbox_manager(self):
        """
        Get the current sandbox manager.
        
        Returns:
            SandboxManager: Current sandbox manager instance
        """
        return self.sandbox_manager
