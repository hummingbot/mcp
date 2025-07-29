"""Tools module for Hummingbot MCP Server"""

from .account import setup_connector

# Tool registry for the MCP server
TOOLS = [
    setup_connector,
]

__all__ = ["TOOLS", "setup_connector"]