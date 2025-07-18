"""
Main MCP server for Hummingbot API integration
"""

import asyncio
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP
from .config.settings import settings
from .client import hummingbot_client
from .utils.logging import setup_logging
from .exceptions import ToolError, MaxConnectionsAttemptError as HBConnectionError
from .tools import account, trading, market_data
import logging

logger = logging.getLogger("hummingbot-mcp")

# Initialize FastMCP server
mcp = FastMCP("hummingbot-mcp")


# Account Management Tools

@mcp.tool()
async def setup_connector(
    connector: Optional[str] = None,
    credentials: Optional[Dict[str, Any]] = None,
    account: Optional[str] = None
) -> str:
    """Setup a new exchange connector with credentials. 
    
    This tool guides you through the entire process of connecting an exchange.
    If no parameters are provided, it will list available connectors.
    
    Args:
        connector: Exchange connector name (e.g., binance, coinbase). Leave empty to list available connectors.
        credentials: Credentials object with required fields for the connector. Leave empty to get required fields.
        account: Account name to add credentials to (default: master)
    """
    from .tools.account import setup_connector as setup_connector_impl
    
    args = {
        "connector": connector,
        "credentials": credentials,
        "account": account or settings.default_account
    }
    
    try:
        result = await setup_connector_impl(args)
        return f"Setup Connector Result: {result}"
    except Exception as e:
        logger.error(f"setup_connector failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to setup connector: {str(e)}")


@mcp.tool()
async def get_account_state(
    account: Optional[str] = None,
    exchanges: Optional[List[str]] = None
) -> str:
    """Get comprehensive account state including balances, positions, and active orders.
    
    Args:
        account: Account name to get state for (default: master)
        exchanges: List of exchange names to get state for. If empty, gets all exchanges.
    """
    from .tools.account import get_account_state as get_account_state_impl
    
    args = {
        "account": account or settings.default_account,
        "exchanges": exchanges or []
    }
    
    try:
        result = await get_account_state_impl(args)
        return f"Account State: {result}"
    except Exception as e:
        logger.error(f"get_account_state failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get account state: {str(e)}")


# Trading Tools

@mcp.tool()
async def place_order(
    trading_pair: str,
    side: str,
    amount: str,
    order_type: str = "market",
    price: Optional[str] = None,
    exchange: Optional[str] = None,
    account: Optional[str] = None
) -> str:
    """Place a buy or sell order with smart amount handling (supports USD values).
    
    Args:
        trading_pair: Trading pair (e.g., BTC-USDT, ETH-USD)
        side: Order side ('buy' or 'sell')
        amount: Order amount (can be in base currency or USD, e.g., '0.1' or '$100')
        order_type: Order type ('market' or 'limit')
        price: Price for limit orders (required for limit orders)
        exchange: Exchange name (if not specified, uses first available)
        account: Account name (default: master)
    """
    from .tools.trading import place_order as place_order_impl
    
    args = {
        "trading_pair": trading_pair,
        "side": side,
        "amount": amount,
        "order_type": order_type,
        "price": price,
        "exchange": exchange,
        "account": account or settings.default_account
    }
    
    try:
        result = await place_order_impl(args)
        return f"Order Result: {result}"
    except Exception as e:
        logger.error(f"place_order failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to place order: {str(e)}")


@mcp.tool()
async def manage_orders(
    action: str,
    account: Optional[str] = None,
    exchange: Optional[str] = None,
    order_id: Optional[str] = None,
    trading_pair: Optional[str] = None
) -> str:
    """Manage orders - cancel orders or get order history.
    
    Args:
        action: Action to perform ('cancel', 'cancel_all', 'get_history')
        account: Account name (default: master)
        exchange: Exchange name (required for cancel_all)
        order_id: Order ID (required for cancel)
        trading_pair: Trading pair filter for history (optional)
    """
    from .tools.trading import manage_orders as manage_orders_impl
    
    args = {
        "action": action,
        "account": account or settings.default_account,
        "exchange": exchange,
        "order_id": order_id,
        "trading_pair": trading_pair
    }
    
    try:
        result = await manage_orders_impl(args)
        return f"Order Management Result: {result}"
    except Exception as e:
        logger.error(f"manage_orders failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage orders: {str(e)}")


# Market Data Tools

@mcp.tool()
async def get_market_data(
    data_type: str,
    trading_pair: Optional[str] = None,
    exchange: Optional[str] = None,
    interval: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """Get market data including prices, candles, order book, and funding rates.
    
    Args:
        data_type: Type of data ('price', 'candles', 'order_book', 'funding_rate')
        trading_pair: Trading pair (e.g., BTC-USDT)
        exchange: Exchange name (if not specified, uses first available)
        interval: Candle interval for candles data (e.g., '1m', '1h', '1d')
        limit: Number of records to return (default: 100)
    """
    from .tools.market_data import get_market_data as get_market_data_impl
    
    args = {
        "data_type": data_type,
        "trading_pair": trading_pair,
        "exchange": exchange,
        "interval": interval,
        "limit": limit
    }
    
    try:
        result = await get_market_data_impl(args)
        return f"Market Data: {result}"
    except Exception as e:
        logger.error(f"get_market_data failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get market data: {str(e)}")


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
    
    # Run the server with FastMCP
    try:
        await mcp.run_stdio_async()
    finally:
        # Clean up client connection
        await hummingbot_client.close()


if __name__ == "__main__":
    asyncio.run(main())