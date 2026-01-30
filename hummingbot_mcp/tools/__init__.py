"""Tools module for Hummingbot MCP Server.

This module provides the implementation functions for MCP tools. The tools are
registered in server.py via FastMCP decorators. This module only exports the
implementation functions for reuse.

Note: Request models have been moved to hummingbot_mcp.schemas for centralized
management.
"""

# Account management
from .account import setup_connector

# Bot management
from .bot_management import (
    get_active_bots_status,
    get_bot_logs,
    manage_bot_execution,
)

# Controllers
from .controllers import (
    deploy_bot,
    explore_controllers,
    modify_controllers,
)

# Executors
from .executors import (
    EXECUTOR_TYPE_DESCRIPTIONS,
    manage_executor_positions,
    manage_executors,
)

# Gateway
from .gateway import manage_gateway_config, manage_gateway_container
from .gateway_clmm import (
    explore_gateway_clmm_pools,
    format_pools_as_detailed_table,
    format_pools_as_table,
    manage_gateway_clmm_positions,
)
from .gateway_swap import manage_gateway_swaps

# Market data
from .market_data import (
    get_candles,
    get_funding_rate,
    get_order_book,
    get_prices,
)

# Portfolio
from .portfolio import get_portfolio_overview

# Trading
from .trading import (
    get_positions,
    place_order,
    search_orders,
    set_position_mode_and_leverage,
)

__all__ = [
    # Account
    "setup_connector",
    # Bot management
    "get_active_bots_status",
    "get_bot_logs",
    "manage_bot_execution",
    # Controllers
    "deploy_bot",
    "explore_controllers",
    "modify_controllers",
    # Executors
    "EXECUTOR_TYPE_DESCRIPTIONS",
    "manage_executor_positions",
    "manage_executors",
    # Gateway
    "manage_gateway_config",
    "manage_gateway_container",
    "explore_gateway_clmm_pools",
    "format_pools_as_detailed_table",
    "format_pools_as_table",
    "manage_gateway_clmm_positions",
    "manage_gateway_swaps",
    # Market data
    "get_candles",
    "get_funding_rate",
    "get_order_book",
    "get_prices",
    # Portfolio
    "get_portfolio_overview",
    # Trading
    "get_positions",
    "place_order",
    "search_orders",
    "set_position_mode_and_leverage",
]
