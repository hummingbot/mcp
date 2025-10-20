"""
Main MCP server for Hummingbot API integration
"""

import asyncio
import logging
import sys
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from hummingbot_mcp.api_servers import api_servers_config
from hummingbot_mcp.exceptions import MaxConnectionsAttemptError as HBConnectionError, ToolError
from hummingbot_mcp.hummingbot_client import hummingbot_client
from hummingbot_mcp.settings import settings
from hummingbot_mcp.tools.account import SetupConnectorRequest

# Configure root logger
logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("hummingbot-mcp")

# Initialize FastMCP server
mcp = FastMCP("hummingbot-mcp")


# Account Management Tools


@mcp.tool()
async def setup_connector(
        connector: str | None = None,
        credentials: dict[str, Any] | None = None,
        account: str | None = None,
        confirm_override: bool | None = None,
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
            connector=connector, credentials=credentials, account=account, confirm_override=confirm_override
        )

        from .tools.account import setup_connector as setup_connector_impl

        result = await setup_connector_impl(request)
        return f"Setup Connector Result: {result}"
    except Exception as e:
        logger.error(f"setup_connector failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to setup connector: {str(e)}")


@mcp.tool()
async def configure_api_servers(
        action: str | None = None,
        name: str | None = None,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
) -> str:
    """Configure API servers using progressive disclosure.

    This tool helps you manage multiple Hummingbot API servers with a simple flow:
    1. No parameters → List all configured servers
    2. action="add" + name + url (+ optional username/password) → Add a new server
    3. action="set_default" + name → Set a server as default (reconnects client)
    4. action="remove" + name → Remove a server

    Args:
        action: Action to perform ('add', 'set_default', 'remove'). Leave empty to list servers.
        name: Server name (required for all actions)
        url: API URL (required for 'add')
        username: API username (optional for 'add', defaults to 'admin')
        password: API password (optional for 'add', defaults to 'admin')
    """
    try:
        # No action = list servers
        if action is None:
            servers = api_servers_config.list_servers()
            result = "Configured API Servers:\n\n"
            for server_name, server_info in servers.items():
                default_marker = " (DEFAULT)" if server_info["is_default"] else ""
                result += f"- {server_name}{default_marker}\n"
                result += f"  URL: {server_info['url']}\n"
                result += f"  Username: {server_info['username']}\n\n"
            return result

        # Validate name for all actions
        if name is None:
            return "Error: 'name' parameter is required for all actions"

        # Add server
        if action == "add":
            if url is None:
                return "Error: 'url' parameter is required for 'add' action"

            result = api_servers_config.add_server(
                name=name,
                url=url,
                username=username or "admin",
                password=password or "admin",
            )
            return result

        # Set default server
        elif action == "set_default":
            # Health check before setting as default
            is_healthy, health_msg = await api_servers_config.health_check(name)
            if not is_healthy:
                return f"Cannot set '{name}' as default: {health_msg}\n\nPlease ensure the server is running before setting it as default."

            result = api_servers_config.set_default(name)

            # Reload settings and reconnect client
            settings.reload_from_default_server()
            await hummingbot_client.close()
            await hummingbot_client.initialize()

            return f"{result}. Client reconnected to new default server."

        # Remove server
        elif action == "remove":
            result = api_servers_config.remove_server(name)

            # If we removed the default, reload settings
            default_server = api_servers_config.get_default_server()
            if default_server.name != name:
                settings.reload_from_default_server()
                await hummingbot_client.close()
                await hummingbot_client.initialize()
                result += f" New default server is '{default_server.name}'. Client reconnected."

            return result

        else:
            return f"Error: Invalid action '{action}'. Use 'add', 'set_default', or 'remove'"

    except Exception as e:
        logger.error(f"configure_api_servers failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to configure API servers: {str(e)}")


@mcp.tool()
async def get_portfolio_balances(
        account_names: list[str] | None = None, connector_names: list[str] | None = None, as_distribution: bool = False
) -> str:
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
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
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
        price: str | None = None,
        order_type: str = "MARKET",
        position_action: str | None = "OPEN",
        account_name: str | None = "master_account",
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
    try:
        client = await hummingbot_client.get_client()
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
            position_action=position_action,
        )
        return f"Order Result: {result}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"place_order failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to place order: {str(e)}")


@mcp.tool()
async def set_account_position_mode_and_leverage(
        account_name: str,
        connector_name: str,
        trading_pair: str | None = None,
        position_mode: str | None = None,
        leverage: int | None = None,
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
                account_name=account_name, connector_name=connector_name, position_mode=position_mode
            )
            response += f"Position Mode Set: {position_mode_result}\n"
        if leverage is not None:
            if not isinstance(leverage, int) or leverage <= 0:
                raise ValueError("Leverage must be a positive integer")
            if trading_pair is None:
                raise ValueError("Trading_pair must be specified")
            leverage_result = await client.trading.set_leverage(
                account_name=account_name, connector_name=connector_name, trading_pair=trading_pair, leverage=leverage
            )
            response += f"Leverage Set: {leverage_result}\n"
        return f"{response.strip()}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"set_account_position_mode_and_leverage failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to set position mode and leverage: {str(e)}")


@mcp.tool()
async def get_orders(
        account_names: list[str] | None = None,
        connector_names: list[str] | None = None,
        trading_pairs: list[str] | None = None,
        status: Literal["OPEN", "FILLED", "CANCELED", "FAILED"] | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = 500,
        cursor: str | None = None,
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
            account_names=account_names,
            connector_names=connector_names,
            trading_pairs=trading_pairs,
            status=status,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            cursor=cursor,
        )
        return f"Order Management Result: {result}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"manage_orders failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage orders: {str(e)}")


@mcp.tool()
async def get_positions(
        account_names: list[str] | None = None, connector_names: list[str] | None = None, limit: int | None = 100
) -> str:
    """Get the positions managed by the connected accounts.

    Args:
        account_names: List of account names to filter by (optional). If empty, returns all accounts.
        connector_names: List of connector names to filter by (optional). If empty, returns all connectors.
        limit: Number of positions to return defaults to 100, maximum is 1000.
    """
    try:
        client = await hummingbot_client.get_client()
        result = await client.trading.get_positions(account_names=account_names, connector_names=connector_names,
                                                    limit=limit)
        return f"Position Management Result: {result}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"manage_positions failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage positions: {str(e)}")


# Market Data Tools


@mcp.tool()
async def get_prices(connector_name: str, trading_pairs: list[str]) -> str:
    """Get the latest prices for the specified trading pairs on a specific exchange connector.
    Args:
        connector_name: Exchange connector name (e.g., 'binance', 'binance_perpetual')
        trading_pairs: List of trading pairs to get prices for (e.g., ['BTC-USDT', 'ETH-USD'])
    """
    try:
        client = await hummingbot_client.get_client()
        prices = await client.market_data.get_prices(connector_name=connector_name, trading_pairs=trading_pairs)
        return f"Price results: {prices}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"get_prices failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get prices: {str(e)}")


@mcp.tool()
async def get_candles(connector_name: str, trading_pair: str, interval: str = "1h", days: int = 30) -> str:
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
            raise ValueError(
                f"Connector '{connector_name}' does not support candle data. Available connectors: {available_candles_connectors}"
            )
        # Determine max records based on interval "m" is minute, "s" is second, "h" is hour, "d" is day, "w" is week
        if interval.endswith("m"):
            max_records = 1440 * days  # 1440 minutes in a day
        elif interval.endswith("h"):
            max_records = 24 * days
        elif interval.endswith("d"):
            max_records = days
        elif interval.endswith("w"):
            max_records = 7 * days
        else:
            raise ValueError(
                f"Unsupported interval format: {interval}. Use '1m', '5m', '15m', '30m', '1h', '4h', '1d', or '1w'.")
        max_records = int(max_records / int(interval[:-1])) if interval[:-1] else max_records

        candles = await client.market_data.get_candles(
            connector_name=connector_name, trading_pair=trading_pair, interval=interval, max_records=max_records
        )
        return f"Candle results: {candles}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"get_candles failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get candles: {str(e)}")


@mcp.tool()
async def get_funding_rate(connector_name: str, trading_pair: str) -> str:
    """Get the latest funding rate for a trading pair on a specific exchange connector. Only works for perpetual
    connectors so the connector name must have _perpetual in it.
    Args:
        connector_name: Exchange connector name (e.g., 'binance_perpetual', 'hyperliquid_perpetual')
        trading_pair: Trading pair to get funding rate for (e.g., 'BTC-USDT')
    """
    try:
        client = await hummingbot_client.get_client()
        if "_perpetual" not in connector_name:
            raise ValueError(
                f"Connector '{connector_name}' is not a perpetual connector. Funding rates are only available for"
                f"perpetual connectors."
            )
        funding_rate = await client.market_data.get_funding_info(connector_name=connector_name,
                                                                 trading_pair=trading_pair)
        return f"Funding Rate: {funding_rate}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"get_funding_rate failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get funding rate: {str(e)}")


@mcp.tool()
async def get_order_book(
        connector_name: str,
        trading_pair: str,
        query_type: Literal[
            "snapshot", "volume_for_price", "price_for_volume", "quote_volume_for_price", "price_for_quote_volume"],
        query_value: float | None = None,
        is_buy: bool = True,
) -> str:
    """Get order book data for a trading pair on a specific exchange connector, if the query type is different than
    snapshot, you need to provide query_value and is_buy
    Args:
        connector_name: Connector name (e.g., 'binance', 'binance_perpetual')
        trading_pair: Trading pair (e.g., BTC-USDT)
        query_type: Order book query type ('snapshot', 'volume_for_price', 'price_for_volume', 'quote_volume_for_price',
        'price_for_quote_volume')
        query_value: Only required if query_type is not 'snapshot'. The value to query against the order book.
        is_buy: Only required if query_type is not 'snapshot'. Is important to see what orders of the book analyze.
    """
    try:
        client = await hummingbot_client.get_client()
        if query_type == "snapshot":
            order_book = await client.market_data.get_order_book(connector_name=connector_name,
                                                                 trading_pair=trading_pair)
            return f"Order Book Snapshot: {order_book}"
        else:
            if query_value is None:
                raise ValueError(f"query_value must be provided for query_type '{query_type}'")
            if query_type == "volume_for_price":
                result = await client.market_data.get_volume_for_price(
                    connector_name=connector_name, trading_pair=trading_pair, price=query_value, is_buy=is_buy
                )
            elif query_type == "price_for_volume":
                result = await client.market_data.get_price_for_volume(
                    connector_name=connector_name, trading_pair=trading_pair, volume=query_value, is_buy=is_buy
                )
            elif query_type == "quote_volume_for_price":
                result = await client.market_data.get_quote_volume_for_price(
                    connector_name=connector_name, trading_pair=trading_pair, price=query_value, is_buy=is_buy
                )
            elif query_type == "price_for_quote_volume":
                result = await client.market_data.get_price_for_quote_volume(
                    connector_name=connector_name, trading_pair=trading_pair, quote_volume=query_value, is_buy=is_buy
                )
            else:
                raise ValueError(f"Unsupported query type: {query_type}")
            return f"Order Book Query Result: {result}"
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"get_market_data failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get market data: {str(e)}")


@mcp.tool()
async def explore_controllers(
        action: Literal["list", "describe"],
        controller_type: Literal["directional_trading", "market_making", "generic"] | None = None,
        controller_name: str | None = None,
        config_name: str | None = None,
) -> str:
    """
    Explore and understand controllers and their configs.

    Use this tool to discover what's available and understand how things work.

    Progressive flow:
    1. action="list" → List all controllers and their configs
    2. action="list" + controller_type → List controllers of that type with config counts
    3. action="describe" + controller_name → Show controller code + list its configs + explain parameters
    4. action="describe" + config_name → Show specific config details + which controller it uses

    Common Enum Values for Controller Configs:

    Position Mode (position_mode):
    - "HEDGE" - Allows holding both long and short positions simultaneously
    - "ONEWAY" - Allows only one direction position at a time
    - Note: Use as string value, e.g., position_mode: "HEDGE"

    Trade Side (side):
    - 1 or "BUY" - For long/buy positions
    - 2 or "SELL" - For short/sell positions
    - 3 - Other trade types
    - Note: Numeric values are required for controller configs

    Order Type (order_type, open_order_type, take_profit_order_type, etc.):
    - 1 or "MARKET" - Market order
    - 2 or "LIMIT" - Limit order
    - 3 or "LIMIT_MAKER" - Limit maker order (post-only)
    - 4 - Other order types
    - Note: Numeric values are required for controller configs

    Args:
        action: "list" to list controllers or "describe" to show details of a specific controller or config.
        controller_type: Type of controller to filter by (optional, e.g., 'directional_trading', 'market_making', 'generic').
        controller_name: Name of the controller to describe (optional, only required for describe specific controller).
        config_name: Name of the config to describe (optional, only required for describe specific config).
    """
    try:
        client = await hummingbot_client.get_client()
        # List all controllers and their configs
        controllers = await client.controllers.list_controllers()
        configs = await client.controllers.list_controller_configs()
        result = ""
        if action == "list":
            result = "Available Controllers:\n\n"
            for c_type, controllers in controllers.items():
                if controller_type is not None and c_type != controller_type:
                    continue
                result += f"Controller Type: {c_type}\n"
                for controller in controllers:
                    controller_configs = [c for c in configs if c.get('controller_name') == controller]
                    result += f"- {controller} ({len(controller_configs)} configs)\n"
                    if len(controller_configs) > 0:
                        for config in controller_configs:
                            result += f"    - {config.get('id', 'unknown')}\n"
            return result
        elif action == "describe":
            config = await client.controllers.get_controller_config(config_name) if config_name else None
            if config:
                if controller_name != config.get("controller_name"):
                    controller_name = config.get("controller_name")
                    result += f"Controller name not matching, using config's controller name: {controller_name}\n"
                result += f"Config Details for {config_name}:\n{config}\n\n"
            if not controller_name:
                return "Please provide a controller name to describe."
            # First, determine the controller type
            controller_type = None
            for c_type, controllers in controllers.items():
                if controller_name in controllers:
                    controller_type = c_type
                    break
            if not controller_type:
                return f"Controller '{controller_name}' not found."
            # Get controller code and configs
            controller_code = await client.controllers.get_controller(controller_type, controller_name)
            controller_configs = [c.get("id") for c in configs if c.get('controller_name') == controller_name]
            result = f"Controller Code for {controller_name} ({controller_type}):\n{controller_code}\n\n"
            template = await client.controllers.get_controller_config_template(controller_type, controller_name)
            result += f"All configs available for controller:\n {controller_configs}"
            result += f"\n\nController Config Template:\n{template}\n\n"
            return result
        else:
            return "Invalid action. Use 'list' or 'describe', or omit for overview."

    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")


@mcp.tool()
async def modify_controllers(
        action: Literal["upsert", "delete"],
        target: Literal["controller", "config"],
        # For controllers
        controller_type: Literal["directional_trading", "market_making", "generic"] | None = None,
        controller_name: str | None = None,
        controller_code: str | None = None,
        # For configs
        config_name: str | None = None,
        config_data: dict[str, Any] | None = None,
        # For configs in bots
        bot_name: str | None = None,
        # Safety
        confirm_override: bool = False,
) -> str:
    """
    Create, update, or delete controllers and their configurations. If bot name is provided, it can only modify the config
    in the bot deployed with that name.

    IMPORTANT: When creating a config without specifying config_data details, you MUST first use the explore_controllers tool
    with action="describe" and the controller_name to understand what parameters are required. The config_data must include
    ALL relevant parameters for the controller to function properly.

    Controllers = are essentially strategies that can be run in Hummingbot.
    Configs = are the parameters that the controller uses to run.

    Args:
        action: "upsert" (create/update) or "delete"
        target: "controller" (template) or "config" (instance)
        confirm_override: Required True if overwriting existing
        config_data: For config creation, MUST contain all required controller parameters. Use explore_controllers first!

    Workflow for creating a config:
    1. Use explore_controllers(action="describe", controller_name="<name>") to see required parameters
    2. Create config_data dict with ALL required parameters from the controller template
    3. Call modify_controllers with the complete config_data

    Examples:
    - Create new controller: modify_controllers("upsert", "controller", controller_type="market_making", ...)
    - Create config: modify_controllers("upsert", "config", config_name="pmm_btc", config_data={...})
    - Modify config from bot: modify_controllers("upsert", "config", config_name="pmm_btc", config_data={...}, bot_name="my_bot")
    - Delete config: modify_controllers("delete", "config", config_name="old_strategy")
    """
    try:
        client = await hummingbot_client.get_client()

        if target == "controller":
            if action == "upsert":
                if not controller_type or not controller_name or not controller_code:
                    raise ValueError("controller_type, controller_name, and controller_code are required for controller upsert")

                # Check if controller exists
                controllers = await client.controllers.list_controllers()
                exists = controller_name in controllers.get(controller_type, [])

                if exists and not confirm_override:
                    controller_code = await client.controllers.get_controller(controller_type, controller_name)
                    return (f"Controller '{controller_name}' already exists and this is the current code: {controller_code}. "
                            f"Set confirm_override=True to update it.")

                result = await client.controllers.create_or_update_controller(
                    controller_type, controller_name, controller_code
                )
                return f"Controller {'updated' if exists else 'created'}: {result}"

            elif action == "delete":
                if not controller_type or not controller_name:
                    raise ValueError("controller_type and controller_name are required for controller delete")

                result = await client.controllers.delete_controller(controller_type, controller_name)
                return f"Controller deleted: {result}"

        elif target == "config":
            if action == "upsert":
                if not config_name or not config_data:
                    raise ValueError("config_name and config_data are required for config upsert")

                # Extract controller_type and controller_name from config_data
                config_controller_type = config_data.get("controller_type")
                config_controller_name = config_data.get("controller_name")

                if not config_controller_type or not config_controller_name:
                    raise ValueError("config_data must include 'controller_type' and 'controller_name'")

                # validate config first
                await client.controllers.validate_controller_config(config_controller_type, config_controller_name, config_data)

                if bot_name:
                    if not confirm_override:
                        current_configs = await client.controllers.get_bot_controller_configs(bot_name)
                        config = next((c for c in current_configs if c.get("id") == config_name), None)
                        if config:
                            return (f"Config '{config_name}' already exists in bot '{bot_name}' with data: {config}. "
                                    "Set confirm_override=True to update it.")
                        else:
                            update_op = await client.controllers.update_bot_controller_config(config_name, config_data)
                            return f"Config created in bot '{bot_name}': {update_op}"
                    else:
                        # Ensure config_data has the correct id
                        if "id" not in config_data or config_data["id"] != config_name:
                            config_data["id"] = config_name
                        update_op = await client.controllers.update_bot_controller_config(config_name, config_data)
                        return f"Config updated in bot '{bot_name}': {update_op}"
                else:
                    # Ensure config_data has the correct id
                    if "id" not in config_data or config_data["id"] != config_name:
                        config_data["id"] = config_name

                    controller_configs = await client.controllers.list_controller_configs()
                    exists = config_name in controller_configs

                    if exists and not confirm_override:
                        existing_config = await client.controllers.get_controller_config(config_name)
                        return (f"Config '{config_name}' already exists with data: {existing_config}."
                                "Set confirm_override=True to update it.")

                    result = await client.controllers.create_or_update_controller_config(config_name, config_data)
                    return f"Config {'updated' if exists else 'created'}: {result}"

            elif action == "delete":
                if not config_name:
                    raise ValueError("config_name is required for config delete")

                result = await client.controllers.delete_controller_config(config_name)
                await client.bot_orchestration.deploy_v2_controllers()
                return f"Config deleted: {result}"
        else:
            raise ValueError("Invalid target. Must be 'controller' or 'config'.")

    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")
    except Exception as e:
        logger.error(f"Failed request to Hummingbot API: {e}")
        raise ToolError(f"Failed to modify controllers/configs: {str(e)}")


@mcp.tool()
async def deploy_bot_with_controllers(
        bot_name: str,
        controllers_config: list[str],
        account_name: str | None = "master_account",
        max_global_drawdown_quote: float | None = None,
        max_controller_drawdown_quote: float | None = None,
        image: str = "hummingbot/hummingbot:latest",
) -> str:
    """Deploy a bot with specified controller configurations.
    Args:
        bot_name: Name of the bot to deploy
        controllers_config: List of controller configs to use for the bot deployment.
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
            controllers_config=controllers_config,
            credentials_profile=account_name,
            max_global_drawdown_quote=max_global_drawdown_quote,
            max_controller_drawdown_quote=max_controller_drawdown_quote,
            image=image,
        )
        return f"Bot Deployment Result: {result}"
    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")


@mcp.tool()
async def get_active_bots_status():
    """
    Get the status of all active bots. Including the unrealized PnL, realized PnL, volume traded, latest logs, etc.
    Note: Both error logs and general logs are limited to the last 5 entries. Use get_bot_logs for more detailed log searching.
    """
    try:
        client = await hummingbot_client.get_client()
        active_bots = await client.bot_orchestration.get_active_bots_status()

        # Limit logs to last 5 entries for each bot to reduce output size
        if isinstance(active_bots, dict) and "data" in active_bots:
            for bot_name, bot_data in active_bots["data"].items():
                if isinstance(bot_data, dict):
                    # Keep only the last 5 error logs
                    if "error_logs" in bot_data:
                        bot_data["error_logs"] = bot_data["error_logs"][-5:]
                    # Keep only the last 5 general logs
                    if "general_logs" in bot_data:
                        bot_data["general_logs"] = bot_data["general_logs"][-5:]

        return f"Active Bots Status: {active_bots}"
    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")


@mcp.tool()
async def get_bot_logs(
        bot_name: str,
        log_type: Literal["error", "general", "all"] = "all",
        limit: int = 50,
        search_term: str | None = None,
) -> str:
    """
    Get detailed logs for a specific bot with filtering options.

    Args:
        bot_name: Name of the bot to get logs for
        log_type: Type of logs to retrieve ('error', 'general', or 'all')
        limit: Maximum number of log entries to return (default: 50, max: 1000)
        search_term: Optional search term to filter logs by message content
    """
    try:
        client = await hummingbot_client.get_client()
        active_bots = await client.bot_orchestration.get_active_bots_status()

        if not isinstance(active_bots, dict) or "data" not in active_bots:
            return "No active bots data found"

        if bot_name not in active_bots["data"]:
            available_bots = list(active_bots["data"].keys())
            return f"Bot '{bot_name}' not found. Available bots: {available_bots}"

        bot_data = active_bots["data"][bot_name]

        # Validate limit
        limit = min(max(1, limit), 1000)

        logs = []

        # Collect error logs if requested
        if log_type in ["error", "all"] and "error_logs" in bot_data:
            error_logs = bot_data["error_logs"]
            for log_entry in error_logs:
                if search_term is None or search_term.lower() in log_entry.get("msg", "").lower():
                    log_entry["log_category"] = "error"
                    logs.append(log_entry)

        # Collect general logs if requested
        if log_type in ["general", "all"] and "general_logs" in bot_data:
            general_logs = bot_data["general_logs"]
            for log_entry in general_logs:
                if search_term is None or search_term.lower() in log_entry.get("msg", "").lower():
                    log_entry["log_category"] = "general"
                    logs.append(log_entry)

        # Sort logs by timestamp (most recent first) and apply limit
        logs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        logs = logs[:limit]

        result = {
            "bot_name": bot_name,
            "log_type": log_type,
            "search_term": search_term,
            "total_logs_returned": len(logs),
            "logs": logs
        }

        return f"Bot Logs Result: {result}"

    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")
    except Exception as e:
        logger.error(f"get_bot_logs failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get bot logs: {str(e)}")


@mcp.tool()
async def manage_bot_execution(
        bot_name: str,
        action: Literal["stop_bot", "stop_controllers", "start_controllers"],
        controller_names: list[str] | None = None,
):
    """
    Manage bot and controller execution states.

    Actions:
    - "stop_bot": Stop and archive the entire bot forever (controller_names not needed)
    - "stop_controllers": Stop specific controllers by setting manual_kill_switch to True (requires controller_names)
    - "start_controllers": Start/resume specific controllers by setting manual_kill_switch to False (requires controller_names)

    Args:
        bot_name: Name of the bot to manage
        action: The action to perform ("stop_bot", "stop_controllers", or "start_controllers")
        controller_names: List of controller names (required for stop_controllers and start_controllers actions)
    """
    try:
        client = await hummingbot_client.get_client()

        if action == "stop_bot":
            result = await client.bot_orchestration.stop_and_archive_bot(bot_name)
            return f"Bot execution stopped and archived: {result}"

        elif action == "stop_controllers":
            if controller_names is None or len(controller_names) == 0:
                raise ValueError("controller_names is required for stop_controllers action")
            tasks = [client.controllers.update_bot_controller_config(bot_name, controller, {"manual_kill_switch": True})
                     for controller in controller_names]
            result = await asyncio.gather(*tasks)
            return f"Controllers stopped: {result}"

        elif action == "start_controllers":
            if controller_names is None or len(controller_names) == 0:
                raise ValueError("controller_names is required for start_controllers action")
            tasks = [client.controllers.update_bot_controller_config(bot_name, controller, {"manual_kill_switch": False})
                     for controller in controller_names]
            result = await asyncio.gather(*tasks)
            return f"Controllers started: {result}"

        else:
            raise ValueError(f"Invalid action: {action}")

    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")
    except Exception as e:
        logger.error(f"manage_bot_execution failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage bot execution: {str(e)}")


# Backward compatibility alias (deprecated)
@mcp.tool()
async def stop_bot_or_controllers(
        bot_name: str,
        controller_names: list[str] | None = None,
):
    """
    [DEPRECATED - Use manage_bot_execution instead]
    Stop and archive a bot forever or stop the execution of controllers in a running bot.

    Args:
        bot_name: Name of the bot to stop
        controller_names: List of controller names to stop (optional, if not provided will stop the bot execution)
    """
    action = "stop_bot" if controller_names is None or len(controller_names) == 0 else "stop_controllers"
    return await manage_bot_execution(bot_name, action, controller_names)


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
        logger.error("Please ensure Hummingbot API is running and credentials are correct.")
        logger.error("💡 Use 'configure_api_servers' tool to manage API server connections")
        # Don't exit - let MCP server start anyway and handle errors per request

    # Run the server with FastMCP
    try:
        await mcp.run_stdio_async()
    finally:
        # Clean up client connection
        await hummingbot_client.close()


if __name__ == "__main__":
    asyncio.run(main())
