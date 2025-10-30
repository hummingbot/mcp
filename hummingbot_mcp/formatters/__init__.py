"""
Formatters package for the Hummingbot MCP server.

This package provides table formatters for various data types including
trading data, market data, bot information, and portfolio balances.
"""

# Export all formatters for easy importing
from .bots import format_active_bots_as_table, format_bot_logs_as_table
from .market_data import (
    format_candles_as_table,
    format_order_book_as_table,
    format_prices_as_table,
)
from .portfolio import format_portfolio_as_table
from .trading import format_orders_as_table, format_positions_as_table

__all__ = [
    # Trading formatters
    "format_orders_as_table",
    "format_positions_as_table",
    # Market data formatters
    "format_prices_as_table",
    "format_candles_as_table",
    "format_order_book_as_table",
    # Bot formatters
    "format_bot_logs_as_table",
    "format_active_bots_as_table",
    # Portfolio formatters
    "format_portfolio_as_table",
]
