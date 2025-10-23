"""Tools module for Hummingbot MCP Server"""

from .account import setup_connector
from .gateway import manage_gateway_container, manage_gateway_config
from .gateway_trading import manage_gateway_swaps

# Tool registry for the MCP server
TOOLS = [
    setup_connector,
    manage_gateway_container,
    manage_gateway_config,
    manage_gateway_swaps,
]

__all__ = [
    "TOOLS",
    "setup_connector",
    "manage_gateway_container",
    "manage_gateway_config",
    "manage_gateway_swaps",
]
