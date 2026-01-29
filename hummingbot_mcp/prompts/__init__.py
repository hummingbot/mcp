"""
MCP Prompts for guided workflows in Hummingbot.

These prompts provide step-by-step guidance for common tasks and work across
all MCP-compatible clients (Claude Code, Claude Desktop, Gemini CLI, Cursor, etc.)
"""

from .setup import register_setup_prompts
from .grid_executor import register_grid_executor_prompts
from .position_executor import register_position_executor_prompts
from .candles_feed import register_candles_feed_prompts


def register_all_prompts(mcp):
    """Register all prompts with the MCP server."""
    register_setup_prompts(mcp)
    register_grid_executor_prompts(mcp)
    register_position_executor_prompts(mcp)
    register_candles_feed_prompts(mcp)
