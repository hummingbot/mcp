"""
Middleware decorators for common tool patterns.

This module provides decorators that standardize common patterns across tool functions,
including client initialization and error handling. Using these decorators reduces
code duplication and ensures consistent behavior.
"""
import functools
import logging
from typing import Any, Callable, Coroutine, TypeVar

from hummingbot_mcp.exceptions import MaxConnectionsAttemptError as HBConnectionError, ToolError
from hummingbot_mcp.hummingbot_client import hummingbot_client

logger = logging.getLogger("hummingbot-mcp")

# Type variable for the return type of async functions
T = TypeVar("T")


def with_client(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Decorator to inject the Hummingbot client as the first argument.

    This decorator handles lazy initialization of the Hummingbot client connection
    and passes it as the first positional argument to the decorated function.

    The decorated function should expect 'client' as its first parameter.

    Example:
        @with_client
        async def get_balances(client, account_name: str):
            return await client.accounts.get_balances(account_name)

        # Called as:
        result = await get_balances(account_name="master_account")

    Args:
        func: Async function that expects client as first argument

    Returns:
        Wrapped async function that auto-injects the client
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        client = await hummingbot_client.get_client()
        return await func(client, *args, **kwargs)
    return wrapper


def handle_errors(action_name: str) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """
    Decorator for standardized error handling in tool functions.

    Wraps the function in a try/except block that:
    - Re-raises HBConnectionError with the original message (connection issues)
    - Re-raises existing ToolError as-is
    - Logs and wraps other exceptions in ToolError with a descriptive message

    Example:
        @handle_errors("get prices")
        async def get_prices(connector_name: str, trading_pairs: list[str]):
            # If this raises an exception, it will be caught and
            # wrapped in a ToolError with message "Failed to get prices: <error>"
            ...

    Args:
        action_name: Description of the action for error messages (e.g., "get prices", "place order")

    Returns:
        Decorator function that wraps the target function with error handling
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except HBConnectionError as e:
                # Re-raise connection errors with the helpful message from hummingbot_client
                raise ToolError(str(e))
            except ToolError:
                # Re-raise ToolErrors as-is
                raise
            except Exception as e:
                logger.error(f"{action_name} failed: {str(e)}", exc_info=True)
                raise ToolError(f"Failed to {action_name}: {str(e)}")
        return wrapper
    return decorator


def tool_handler(action_name: str) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """
    Combined decorator that applies both with_client and handle_errors.

    This is a convenience decorator that combines the most common patterns:
    - Injects the Hummingbot client as the first argument
    - Wraps the function with standardized error handling

    The decorated function should expect 'client' as its first parameter.

    Example:
        @tool_handler("get portfolio")
        async def get_portfolio(client, account_name: str):
            return await client.accounts.get_balances(account_name)

        # Called as:
        result = await get_portfolio(account_name="master_account")

    Args:
        action_name: Description of the action for error messages

    Returns:
        Decorator function that applies both with_client and handle_errors
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        # Apply handle_errors first (outer), then with_client (inner)
        # This way errors from client initialization are also caught
        @functools.wraps(func)
        @handle_errors(action_name)
        @with_client
        async def wrapper(client: Any, *args: Any, **kwargs: Any) -> T:
            return await func(client, *args, **kwargs)
        return wrapper
    return decorator
