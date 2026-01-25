"""
MCP Prompts for guided workflows in Hummingbot.

These prompts provide step-by-step guidance for common tasks and work across
all MCP-compatible clients (Claude Code, Claude Desktop, Gemini CLI, Cursor, etc.)
"""

from .setup import register_setup_prompts
from .first_bot import register_first_bot_prompts
from .add_exchange import register_add_exchange_prompts
from .troubleshoot import register_troubleshoot_prompts


def register_all_prompts(mcp):
    """Register all prompts with the MCP server."""
    register_setup_prompts(mcp)
    register_first_bot_prompts(mcp)
    register_add_exchange_prompts(mcp)
    register_troubleshoot_prompts(mcp)
