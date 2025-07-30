"""
Main MCP server for Hummingbot API integration
"""

import asyncio
import sys
from typing import Dict, Any, Optional, List, Literal

from mcp.server.fastmcp import FastMCP
from mcp_hummingbot.settings import settings
from mcp_hummingbot.hummingbot_client import hummingbot_client
from mcp_hummingbot.exceptions import ToolError, MaxConnectionsAttemptError as HBConnectionError
from mcp_hummingbot.tools.account import SetupConnectorRequest
import logging

# Configure root logger
logging.basicConfig(
    level="INFO",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
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
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")


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
            result = await client.portfolio.get_distribution(account_names=account_names,
                                                             connector_names=connector_names)
            return f"Portfolio Distribution: {result}"
        account_info = await client.portfolio.get_state(account_names=account_names, connector_names=connector_names)
        return f"Account State: {account_info}"
    except Exception as e:
        logger.error(f"get_account_state failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get account state: {str(e)}")


# Trading Tools

@mcp.tool()
async def place_order(
        connector_name: str,
        trading_pair: str,
        trade_type: str,
        amount: str,
        price: Optional[str] = None,
        order_type: str = "MARKET",
        position_action: Optional[str] = "OPEN",
        account_name: Optional[str] = "master_account"
) -> str:
    """Place a buy or sell order (supports USD values by adding at the start of the amount $).

    Args:
        connector_name: Exchange connector name (e.g., 'binance', 'binance_perpetual')
        trading_pair: Trading pair (e.g., BTC-USDT, ETH-USD)
        trade_type: Order side ('BUY' or 'SELL')
        amount: Order amount (is always in base currency, if you want to use USD values, add a dollar sign at the start, e.g., '$100')
        order_type: Order type ('MARKET' or 'LIMIT')
        price: Price for limit orders (required for limit orders)
        position_action: Position action ('OPEN', 'CLOSE'). Defaults to 'OPEN' and is useful for perpetuals with HEDGE mode where you
        can hold a long and short position at the same time.
        account_name: Account name (default: master_account)
    """
    client = await hummingbot_client.get_client()
    try:
        if "$" in amount and price is None:
            prices = await client.market_data.get_prices(connector_name=connector_name, trading_pairs=trading_pair)
            price = prices["prices"][trading_pair]
            amount = float(amount.replace("$", "")) / price
        else:
            amount = float(amount)
        result = await client.trading.place_order(
            account_name=account_name,
            connector_name=connector_name,
            trading_pair=trading_pair,
            trade_type=trade_type,
            amount=amount,
            order_type=order_type,
            price=price,
            position_action=position_action
        )
        return f"Order Result: {result}"
    except Exception as e:
        logger.error(f"place_order failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to place order: {str(e)}")


@mcp.tool()
async def set_account_position_mode_and_leverage(
        account_name: str,
        connector_name: str,
        trading_pair: Optional[str] = None,
        position_mode: Optional[str] = None,
        leverage: Optional[int] = None
) -> str:
    """Set position mode and leverage for an account on a specific exchange. If position mode is not specified, will only
    set the leverage. If leverage is not specified, will only set the position mode.

    Args:
        account_name: Account name (default: master_account)
        connector_name: Exchange connector name (e.g., 'binance_perpetual')
        trading_pair: Trading pair (e.g., ETH-USD) only required for setting leverage
        position_mode: Position mode ('HEDGE' or 'ONE-WAY')
        leverage: Leverage to set (optional, required for HEDGE mode)
    """

    try:
        client = await hummingbot_client.get_client()
        if position_mode is None and leverage is None:
            raise ValueError("At least one of position_mode or leverage must be specified")
        response = ""
        if position_mode:
            position_mode = position_mode.upper()
            if position_mode not in ["HEDGE", "ONE-WAY"]:
                raise ValueError("Invalid position mode. Must be 'HEDGE' or 'ONE-WAY'")
            position_mode_result = await client.trading.set_position_mode(
                account_name=account_name,
                connector_name=connector_name,
                position_mode=position_mode
            )
            response += f"Position Mode Set: {position_mode_result}\n"
        if leverage is not None:
            if not isinstance(leverage, int) or leverage <= 0:
                raise ValueError("Leverage must be a positive integer")
            if trading_pair is None:
                raise ValueError("Trading_pair must be specified")
            leverage_result = await client.trading.set_leverage(
                account_name=account_name,
                connector_name=connector_name,
                trading_pair=trading_pair,
                leverage=leverage
            )
            response += f"Leverage Set: {leverage_result}\n"
        return f"{response.strip()}"
    except Exception as e:
        logger.error(f"set_account_position_mode_and_leverage failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to set position mode and leverage: {str(e)}")


@mcp.tool()
async def get_orders(
        account_names: Optional[List[str]] = None,
        connector_names: Optional[List[str]] = None,
        trading_pairs: Optional[List[str]] = None,
        status: Optional[Literal["OPEN", "FILLED", "CANCELED", "FAILED"]] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = 500,
        cursor: Optional[str] = None
) -> str:
    """Get the orders manged by the connected accounts.
    
    Args:
        account_names: List of account names to filter by (optional). If empty, returns all accounts.
        connector_names: List of connector names to filter by (optional). If empty, returns all connectors.
        trading_pairs: List of trading pairs to filter by (optional). If empty, returns all trading pairs.
        status: Order status to filter by can be OPEN, PARTIALLY_FILLED, FILLED, CANCELED, FAILED (is optional).
        start_time: Start time (in seconds) to filter by (optional).
        end_time: End time (in seconds) to filter by (optional).
        limit: Number of orders to return defaults to 500, maximum is 1000.
        cursor: Cursor for pagination (optional, should be used if another request returned a cursor).
    """

    try:
        client = await hummingbot_client.get_client()
        result = await client.trading.search_orders(
            account_names=account_names, connector_names=connector_names, trading_pairs=trading_pairs,
            status=status, start_time=start_time, end_time=end_time, limit=limit, cursor=cursor
        )
        return f"Order Management Result: {result}"
    except Exception as e:
        logger.error(f"manage_orders failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage orders: {str(e)}")


@mcp.tool()
async def get_positions(
        account_names: Optional[List[str]] = None,
        connector_names: Optional[List[str]] = None,
        limit: Optional[int] = 100
) -> str:
    """Get the positions managed by the connected accounts.

    Args:
        account_names: List of account names to filter by (optional). If empty, returns all accounts.
        connector_names: List of connector names to filter by (optional). If empty, returns all connectors.
        limit: Number of positions to return defaults to 100, maximum is 1000.
    """
    try:
        client = await hummingbot_client.get_client()
        result = await client.trading.get_positions(
            account_names=account_names, connector_names=connector_names, limit=limit
        )
        return f"Position Management Result: {result}"
    except Exception as e:
        logger.error(f"manage_positions failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage positions: {str(e)}")

# Market Data Tools

@mcp.tool()
async def get_prices(
        connector_name: str,
        trading_pairs: List[str]) -> str:
    """Get the latest prices for the specified trading pairs on a specific exchange connector.
    Args:
        connector_name: Exchange connector name (e.g., 'binance', 'binance_perpetual')
        trading_pairs: List of trading pairs to get prices for (e.g., ['BTC-USDT', 'ETH-USD'])
    """
    try:
        client = await hummingbot_client.get_client()
        prices = await client.market_data.get_prices(connector_name=connector_name, trading_pairs=trading_pairs)
        return f"Price results: {prices}"
    except Exception as e:
        logger.error(f"get_prices failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get prices: {str(e)}")

@mcp.tool()
async def get_candles(
        connector_name: str,
        trading_pair: str,
        interval: str = "1h",
        days: int = 30) -> str:
    """Get the real-time candles for a trading pair on a specific exchange connector.
    Args:
        connector_name: Exchange connector name (e.g., 'binance', 'binance_perpetual')
        trading_pair: Trading pair to get candles for (e.g., 'BTC-USDT')
        interval: Candle interval (default: '1h'). Options include '1m', '5m', '15m', '30m', '1h', '4h', '1d'.
        days: Number of days of historical data to retrieve (default: 30).
    """
    try:
        client = await hummingbot_client.get_client()
        available_candles_connectors = await client.market_data.get_available_candle_connectors()
        if connector_name not in available_candles_connectors:
            raise ValueError(f"Connector '{connector_name}' does not support candle data. Available connectors: {available_candles_connectors}")
        # Determine max records based on interval "m" is minute, "s" is second, "h" is hour, "d" is day, "w" is week
        if interval.endswith("m"):
            max_records = 1440 * days # 1440 minutes in a day
        elif interval.endswith("h"):
            max_records = 24 * days
        elif interval.endswith("d"):
            max_records = days
        elif interval.endswith("w"):
            max_records = 7 * days
        else:
            raise ValueError(f"Unsupported interval format: {interval}. Use '1m', '5m', '15m', '30m', '1h', '4h', '1d', or '1w'.")
        max_records = int(max_records / int(interval[:-1])) if interval[:-1] else max_records

        candles = await client.market_data.get_candles(
            connector_name=connector_name,
            trading_pair=trading_pair,
            interval=interval,
            max_records=max_records
        )
        return f"Candle results: {candles}"
    except Exception as e:
        logger.error(f"get_candles failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get candles: {str(e)}")

@mcp.tool()
async def get_funding_rate(
        connector_name: str,
        trading_pair: str) -> str:
    """Get the latest funding rate for a trading pair on a specific exchange connector. Only works for perpetual
    connectors so the connector name must have _perpetual in it.
    Args:
        connector_name: Exchange connector name (e.g., 'binance_perpetual', 'hyperliquid_perpetual')
        trading_pair: Trading pair to get funding rate for (e.g., 'BTC-USDT')
    """
    try:
        client = await hummingbot_client.get_client()
        if "_perpetual" not in connector_name:
            raise ValueError(f"Connector '{connector_name}' is not a perpetual connector. Funding rates are only available for perpetual connectors.")
        funding_rate = await client.market_data.get_funding_info(connector_name=connector_name, trading_pair=trading_pair)
        return f"Funding Rate: {funding_rate}"
    except Exception as e:
        logger.error(f"get_funding_rate failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get funding rate: {str(e)}")

@mcp.tool()
async def get_order_book(
        connector_name: str,
        trading_pair: str,
        query_type: Literal["snapshot", "volume_for_price", "price_for_volume", "quote_volume_for_price", "price_for_quote_volume"],
        query_value: Optional[float] = None,
) -> str:
    """Get order book data for a trading pair on a specific exchange connector, if the typ
    
    Args:
        connector_name: Connector name (e.g., 'binance', 'binance_perpetual')
        trading_pair: Trading pair (e.g., BTC-USDT)
        query_type: Order book query type ('snapshot', 'volume_for_price', 'price_for_volume', 'quote_volume_for_price', 'price_for_quote_volume')
        query_value: Only required if query_type is not 'snapshot'. The value to query against the order book.
    """
    try:
        client = await hummingbot_client.get_client()
        if query_type == "snapshot":
            order_book = await client.market_data.get_order_book(connector_name=connector_name, trading_pair=trading_pair)
            return f"Order Book Snapshot: {order_book}"
        else:
            if query_value is None:
                raise ValueError(f"query_value must be provided for query_type '{query_type}'")
            if query_type == "volume_for_price":
                result = await client.market_data.get_volume_for_price(connector_name=connector_name, trading_pair=trading_pair, price=query_value)
            elif query_type == "price_for_volume":
                result = await client.market_data.get_price_for_volume(connector_name=connector_name, trading_pair=trading_pair, volume=query_value)
            elif query_type == "quote_volume_for_price":
                result = await client.market_data.get_quote_volume_for_price(connector_name=connector_name, trading_pair=trading_pair, price=query_value)
            elif query_type == "price_for_quote_volume":
                result = await client.market_data.get_price_for_quote_volume(connector_name=connector_name, trading_pair=trading_pair, quote_volume=query_value)
            else:
                raise ValueError(f"Unsupported query type: {query_type}")
            return f"Order Book Query Result: {result}"
    except Exception as e:
        logger.error(f"get_market_data failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get market data: {str(e)}")

@mcp.tool()
async def manage_controller_configs(
        action: Literal["list", "get", "upsert", "delete"],
        config_name: Optional[str] = None,
        config_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Manage controller configurations for Hummingbot MCP. If action is 'list', it will return all controller configs.
    If action is 'get', it will return the config for the given config_name. If action is 'upsert', it will update
    the config for the given config_name with the provided config_data, creating it if it doesn't exist, is important
    to know that the config_name should be the same as the value of 'id' in the config data. If action is 'delete',
    it will delete the config for the given config_name.
    Args:
        action: Action to perform ('list', 'get', 'upsert', 'delete')
        config_name: Name of the controller config to manage (required for 'get', 'upsert', 'delete')
        config_data: Data for the controller config (required for 'upsert')
    """
    try:
        client = await hummingbot_client.get_client()
        if action == "list":
            configs = await client.controllers.list_controller_configs()
            return f"Controller Configs: {configs}"
        elif action == "get":
            if not config_name:
                raise ValueError("config_name is required for 'get' action")
            config = await client.controllers.get_controller_config(config_name)
            return f"Controller Config: {config}"
        elif action == "upsert":
            if not config_name or not config_data:
                raise ValueError("config_name and config_data are required for 'upsert' action")
            if "id" not in config_data or config_data["id"] != config_name:
                config_data["id"] = config_name
            result = await client.controllers.create_or_update_controller_config(config_data)
            return f"Controller Config Upserted: {result}"
        elif action == "delete":
            if not config_name:
                raise ValueError("config_name is required for 'delete' action")
            result = await client.controllers.delete_controller_config(config_name)
            await client.bot_orchestration.deploy_v2_controllers()
            return f"Controller Config Deleted: {result}"
        else:
            raise ValueError("Invalid action. Must be 'list', 'get', 'upsert', or 'delete'.")
    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")

@mcp.tool()
async def deploy_bot_with_controllers(
        bot_name: str,
        controller_configs: List[str],
        account_name: Optional[str] = "master_account",
        max_global_drawdown_quote: Optional[float] = None,
        max_controller_drawdown_quote: Optional[float] = None,
        image: str = "hummingbot/hummingbot:latest"
) -> str:
    """Deploy a bot with specified controller configurations.
    Args:
        bot_name: Name of the bot to deploy
        controller_configs: List of controller configs to use for the bot deployment.
        account_name: Account name to use for the bot (default: master_account)
        max_global_drawdown_quote: Maximum global drawdown in quote currency (optional) defaults to None.
        max_controller_drawdown_quote: Maximum drawdown per controller in quote currency (optional) defaults to None.
        image: Docker image to use for the bot (default: "hummingbot/hummingbot:latest")
    """
    try:
        client = await hummingbot_client.get_client()
        # Validate controller configs
        result = await client.bot_orchestration.deploy_v2_controllers(
            instance_name=bot_name,
            controller_configs=controller_configs,
            credentials_profile=account_name,
            max_global_drawdown_quote=max_global_drawdown_quote,
            max_controller_drawdown_quote=max_controller_drawdown_quote,
            image=image
        )
        return f"Bot Deployment Result: {result}"
    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")

async def main():
    """Run the MCP server"""
    # Setup logging once at application start
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
