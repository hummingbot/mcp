"""
Response wrapper for standardized tool responses.

This module provides the ToolResponse class that standardizes how tool functions
return results, making it easier to handle both successful responses and errors
consistently across the codebase.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResponse:
    """
    Standardized response wrapper for tool functions.

    Provides a consistent interface for returning results from tools, including
    formatted output for display and optional structured data and error information.

    Attributes:
        formatted_output: Human-readable output string for display
        data: Optional dictionary of structured data
        error: Optional error message if the operation failed

    Examples:
        >>> # Successful response
        >>> response = ToolResponse(
        ...     formatted_output="Order placed successfully",
        ...     data={"order_id": "123", "status": "filled"}
        ... )
        >>> response.to_dict()
        {'formatted_output': 'Order placed successfully', 'order_id': '123', 'status': 'filled'}

        >>> # Error response
        >>> response = ToolResponse.error_response("place order", "Insufficient balance")
        >>> response.to_dict()
        {'formatted_output': 'Error placing order: Insufficient balance', 'action': 'place order', 'error': 'Insufficient balance'}
    """

    formatted_output: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the response to a dictionary format.

        Merges the formatted_output with any additional data, and includes
        the error field if present.

        Returns:
            Dictionary containing formatted_output, all data fields, and error if present
        """
        result = {"formatted_output": self.formatted_output, **self.data}
        if self.error:
            result["error"] = self.error
        return result

    @classmethod
    def error_response(cls, action: str, error: str | Exception) -> "ToolResponse":
        """
        Create a standardized error response.

        Args:
            action: Description of the action that failed (e.g., "place order", "get prices")
            error: Error message or exception

        Returns:
            ToolResponse configured as an error response
        """
        error_str = str(error)
        return cls(
            formatted_output=f"Error {action}: {error_str}",
            data={"action": action},
            error=error_str
        )

    @classmethod
    def success(cls, formatted_output: str, **data: Any) -> "ToolResponse":
        """
        Create a successful response with formatted output and optional data.

        Args:
            formatted_output: Human-readable output string
            **data: Additional key-value pairs to include in the response

        Returns:
            ToolResponse configured as a success response
        """
        return cls(formatted_output=formatted_output, data=data)

    def __str__(self) -> str:
        """Return the formatted output when converting to string."""
        return self.formatted_output

    def is_error(self) -> bool:
        """Check if this response represents an error."""
        return self.error is not None
