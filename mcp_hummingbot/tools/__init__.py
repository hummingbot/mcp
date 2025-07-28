"""Tools module for Hummingbot MCP Server"""

from .account import setup_connector, get_account_state
from .trading import place_order, manage_orders
from .market_data import get_market_data

# Tool registry for the MCP server
TOOLS = [
    setup_connector,
    get_account_state, 
    place_order,
    manage_orders,
    get_market_data
]

__all__ = ["TOOLS", "setup_connector", "get_account_state", "place_order", "manage_orders", "get_market_data"]