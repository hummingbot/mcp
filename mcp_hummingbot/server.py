"""
Main MCP server for Hummingbot API integration
"""

import asyncio
from typing import Dict, Any, Optional, List

from mcp.server.fastmcp import FastMCP
from .config.settings import settings
from .client import hummingbot_client
from .utils.logging import setup_logging
from .exceptions import ToolError, MaxConnectionsAttemptError as HBConnectionError
from .tools.account import SetupConnectorRequest
import logging

logger = logging.getLogger("hummingbot-mcp")

# Initialize FastMCP server
mcp = FastMCP("hummingbot-mcp")


# Account Management Tools

@mcp.tool()
async def setup_connector(
    connector: Optional[str] = None,
    credentials: Optional[Dict[str, Any]] = None,
    account: Optional[str] = None,
    confirm_override: Optional[bool] = None
) -> str:
    """Setup a new exchange connector for an account with credentials using progressive disclosure.
    
    This tool guides you through the entire process of connecting an exchange with a four-step flow:
    1. No parameters → List available exchanges
    2. Connector only → Show required credential fields  
    3. Connector + credentials, no account → Select account from available accounts
    4. All parameters → Connect the exchange (with override confirmation if needed)
    
    Args:
        connector: Exchange connector name (e.g., 'binance', 'binance_perpetual'). Leave empty to list available connectors.
        credentials: Credentials object with required fields for the connector. Leave empty to see required fields first.
        account: Account name to add credentials to. If not provided, prompts for account selection.
        confirm_override: Explicit confirmation to override existing connector. Required when connector already exists.
    """
    try:
        # Create and validate request using Pydantic model
        request = SetupConnectorRequest(
            connector=connector,
            credentials=credentials,
            account=account,
            confirm_override=confirm_override
        )
        
        from .tools.account import setup_connector as setup_connector_impl
        result = await setup_connector_impl(request)
        return f"Setup Connector Result: {result}"
    except Exception as e:
        logger.error(f"setup_connector failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to setup connector: {str(e)}")

@mcp.tool()
async def create_delete_accounts(
    action: str,
    account_name: Optional[str] = None,
    credential: Optional[str] = None,
) -> str:
    """
    Create or delete an account. Important: Deleting an account will remove all associated credentials and data, and
    the master_account cannot be deleted.
    If a credential is provided, only the credential for the account will be deleted
    Args:
        action: Action to perform ('create' or 'delete')
        account_name: Name of the account to create or delete. Required for 'create' and optional for 'delete'.
    """
    try:
        client = await hummingbot_client.get_client()
        if action == "create":
            if not account_name:
                raise ValueError("Account name is required for creating an account")
            result = await client.accounts.add_account(account_name)
            return f"Account '{account_name}' created successfully: {result}"
        elif action == "delete":
            if not account_name:
                raise ValueError("Account name is required for deleting an account")
            if account_name == settings.default_account:
                raise ValueError("Cannot delete the master account")
            if credential is not None:
                # If credential is provided, delete only the credential for the account
                result = await client.accounts.delete_credential(account_name, credential)
                return f"Credential '{credential}' for account '{account_name}' deleted successfully: {result}"
            result = await client.accounts.delete_account(account_name)
            return f"Account '{account_name}' deleted successfully: {result}"
        else:
            raise ValueError("Invalid action. Must be 'create' or 'delete'.")
    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError("Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")



@mcp.tool()
async def get_portfolio_balances(account_names: Optional[List[str]] = None,
                                 connector_names: Optional[List[str]] = None,
                                 as_distribution: bool = False) -> str:
    """Get portfolio balances and holdings across all connected exchanges.
    
    Returns detailed token balances, values, and available units for each account. Use this to check your portfolio,
    see what tokens you hold, and their current values. If passing accounts and connectors it will only return the
    filtered accounts and connectors, leave it empty to return all accounts and connectors.
    You can also get the portfolio distribution by setting `as_distribution` to True, which will return the distribution
    of tokens and their values across accounts and connectors and the percentage of each token in the portfolio.

    Args:
        account_names: List of account names to filter by (optional). If empty, returns all accounts.
        connector_names: List of connector names to filter by (optional). If empty, returns all connectors.
        as_distribution: If True, returns the portfolio distribution as a percentage of each token in the portfolio and
        their values across accounts and connectors. Defaults to False.
    """
    try:
        # Get account credentials to know which exchanges are connected
        client = await hummingbot_client.get_client()
        if as_distribution:
            # Get portfolio distribution
            result = await client.portfolio.get_distribution(account_names=account_names, connector_names=connector_names)
            return f"Portfolio Distribution: {result}"
        account_info = await client.portfolio.get_state(account_names=account_names, connector_names=connector_names)
        return f"Account State: {account_info}"
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