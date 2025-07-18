"""
Main MCP server for Hummingbot API integration
"""

import asyncio
import json
from typing import List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult

from .config.settings import settings
from .client import hummingbot_client
from .tools import TOOLS
from .utils.logging import setup_logging
from .exceptions import ToolError, MaxConnectionsAttemptError as HBConnectionError
import logging

logger = logging.getLogger("hummingbot-mcp")

# Initialize MCP server
server = Server("hummingbot-mcp")


def format_error(error: str) -> TextContent:
    """Format error messages consistently"""
    return TextContent(text=f"Error: {error}")


def format_success(data: any) -> TextContent:
    """Format successful responses"""
    return TextContent(text=json.dumps(data, indent=2, default=str))


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools"""
    return [tool.tool_definition for tool in TOOLS]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls"""
    try:
        # Find the tool function
        tool_func = None
        for tool in TOOLS:
            if tool.tool_definition.name == name:
                tool_func = tool
                break
        
        if not tool_func:
            raise ToolError(f"Unknown tool: {name}")
        
        # Execute the tool
        result = await tool_func(arguments)
        return CallToolResult(content=[format_success(result)])
        
    except HBConnectionError as e:
        return CallToolResult(content=[format_error(f"Connection error: {str(e)}")], isError=True)
    except ToolError as e:
        return CallToolResult(content=[format_error(str(e))], isError=True)
    except Exception as e:
        logger.error(f"Tool {name} failed: {str(e)}", exc_info=True)
        return CallToolResult(content=[format_error(f"Tool execution failed: {str(e)}")], isError=True)


async def main():
    """Run the MCP server"""
    # Setup logging once at application start
    setup_logging()
    logger.info("Starting Hummingbot MCP Server")
    logger.info(f"API URL: {settings.api_url}")
    logger.info(f"Default Account: {settings.default_account}")
    
    # Test API connection
    try:
        client = await hummingbot_client.initialize()
        accounts = await client.accounts.list_accounts()
        logger.info(f"Successfully connected to Hummingbot API. Found {len(accounts)} accounts.")
    except Exception as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        logger.error("Please ensure Hummingbot is running and API credentials are correct.")
        # Don't exit - let MCP server start anyway and handle errors per request
    
    # Run the server
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)
    finally:
        # Clean up client connection
        await hummingbot_client.close()


if __name__ == "__main__":
    asyncio.run(main())