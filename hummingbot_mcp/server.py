"""
Main MCP server for Hummingbot API integration
"""

import asyncio
import logging
import os
import platform
import sys
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from hummingbot_mcp.api_servers import api_servers_config
from hummingbot_mcp.formatters import (
    format_active_bots_as_table,
    format_bot_logs_as_table,
    format_connector_result,
    format_gateway_clmm_pool_result,
    format_gateway_config_result,
    format_gateway_container_result,
    format_gateway_swap_result,
    format_portfolio_as_table,
)
from hummingbot_mcp.hummingbot_client import hummingbot_client
from hummingbot_mcp.middleware import GATEWAY_LOG_HINT, handle_errors
from hummingbot_mcp.schemas import (
    GatewayCLMMRequest,
    GatewayConfigRequest,
    GatewayContainerRequest,
    GatewaySwapRequest,
    ManageExecutorsRequest,
    SetupConnectorRequest,
)
from hummingbot_mcp.settings import settings
from hummingbot_mcp.tools import bot_management as bot_management_tools
from hummingbot_mcp.tools import controllers as controllers_tools
from hummingbot_mcp.tools import market_data as market_data_tools
from hummingbot_mcp.tools import portfolio as portfolio_tools
from hummingbot_mcp.tools import trading as trading_tools
from hummingbot_mcp.tools.account import setup_connector as setup_connector_impl
from hummingbot_mcp.tools.executors import manage_executors as manage_executors_impl
from hummingbot_mcp.tools.gateway import (
    manage_gateway_config as manage_gateway_config_impl,
    manage_gateway_container as manage_gateway_container_impl,
)
from hummingbot_mcp.tools.gateway_clmm import manage_gateway_clmm as manage_gateway_clmm_impl
from hummingbot_mcp.tools.gateway_swap import manage_gateway_swaps as manage_gateway_swaps_impl
from hummingbot_mcp.tools import history as history_tools

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
@handle_errors("setup/delete connector")
async def setup_connector(
        action: Literal["setup", "delete"] | None = None,
        connector: str | None = None,
        credentials: dict[str, Any] | None = None,
        account: str | None = None,
        confirm_override: bool | None = None,
) -> str:
    """Setup or delete an exchange connector for an account with credentials using progressive disclosure.

    This tool guides you through the entire process of connecting an exchange with a four-step flow:
    1. No parameters → List available exchanges
    2. Connector only → Show required credential fields
    3. Connector + credentials, no account → Select account from available accounts
    4. All parameters → Connect the exchange (with override confirmation if needed)

    Delete flow (action="delete"):
    1. action="delete" only → List all accounts and their configured connectors
    2. action="delete" + connector → Show which accounts have this connector configured
    3. action="delete" + connector + account → Delete the credential

    Args:
        action: Action to perform. 'setup' (default) to add/update credentials, 'delete' to remove credentials.
        connector: Exchange connector name (e.g., 'binance', 'binance_perpetual'). Leave empty to list available connectors.
        credentials: Credentials object with required fields for the connector. Leave empty to see required fields first.
        account: Account name to add credentials to. If not provided, prompts for account selection.
        confirm_override: Explicit confirmation to override existing connector. Required when connector already exists.
    """
    request = SetupConnectorRequest(
        action=action, connector=connector, credentials=credentials,
        account=account, confirm_override=confirm_override,
    )

    client = await hummingbot_client.get_client()
    result = await setup_connector_impl(client, request)
    return format_connector_result(result)


@mcp.tool()
@handle_errors("configure API servers")
async def configure_api_servers(
        action: str | None = None,
        name: str | None = None,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
) -> str:
    """Configure API servers using progressive disclosure.

    This tool helps you manage multiple Hummingbot API servers with a simple flow:
    1. No parameters → List all configured servers
    2. action="add" + name + (optional host/port/username/password) → Add a new server
    3. action="modify" + name + (host/port/username/password) → Modify existing server (partial updates supported)
    4. action="set_default" + name → Set a server as default (reconnects client)
    5. action="remove" + name → Remove a server

    Args:
        action: Action to perform ('add', 'modify', 'set_default', 'remove'). Leave empty to list servers.
        name: Server name (required for all actions)
        host: API host (optional, defaults to 'localhost' for 'add'. Examples: 'localhost', 'host.docker.internal', '72.212.424.42')
        port: API port (optional, defaults to 8000 for 'add')
        username: API username (optional for 'add', defaults to 'admin'; optional for 'modify')
        password: API password (optional for 'add', defaults to 'admin'; optional for 'modify')
    """
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
        # Apply defaults and construct URL from host and port
        if host is None:
            host = "localhost"
        if port is None:
            port = 8000

        url = f"http://{host}:{port}"

        result = api_servers_config.add_server(
            name=name,
            url=url,
            username=username or "admin",
            password=password or "admin",
        )

        # Add Docker networking warning for localhost URLs
        if host == "localhost" and os.getenv("DOCKER_CONTAINER") == "true":
            system = platform.system()
            if system in ["Darwin", "Windows"]:
                result += (
                    "\n\n⚠️  Docker Networking Notice:\n"
                    f"You're running on {system} and using 'localhost' as the host.\n"
                    "Docker containers on Mac/Windows cannot access 'localhost' on the host.\n"
                    f"If connection fails, use 'host.docker.internal' instead:\n"
                    f"  configure_api_servers(action='add', name='{name}', "
                    f"host='host.docker.internal', port={port}, ...)"
                )

        return result

    # Modify server
    elif action == "modify":
        # Construct URL from host and port if either is provided
        url = None
        if host is not None or port is not None:
            # Get current server config to use existing values as defaults
            servers = api_servers_config.list_servers()
            if name not in servers:
                return f"Error: Server '{name}' not found"

            current_server = servers[name]
            current_url = current_server["url"]

            # Parse current URL to extract host and port
            from urllib.parse import urlparse
            parsed = urlparse(current_url)
            current_host = parsed.hostname or "localhost"
            current_port = parsed.port or 8000

            # Use provided values or fall back to current values
            final_host = host if host is not None else current_host
            final_port = port if port is not None else current_port

            url = f"http://{final_host}:{final_port}"

        result = api_servers_config.modify_server(name=name, url=url, username=username, password=password)

        # Check if we modified the default server and need to reconnect
        default_server = api_servers_config.get_default_server()
        if default_server.name == name:
            settings.reload_from_default_server()
            await hummingbot_client.close()
            try:
                await hummingbot_client.initialize(force=True)
                return f"{result}. Client reconnected successfully."
            except Exception as e:
                return f"{result}. Warning: Could not connect to server - {str(e)}"

        return result

    # Set default server
    elif action == "set_default":
        result = api_servers_config.set_default(name)

        # Reload settings and reconnect client
        settings.reload_from_default_server()
        await hummingbot_client.close()
        try:
            await hummingbot_client.initialize(force=True)
            return f"{result}. Client reconnected successfully."
        except Exception as e:
            return f"{result}. Warning: Could not connect to server - {str(e)}"

    # Remove server
    elif action == "remove":
        result = api_servers_config.remove_server(name)

        # Reload settings and reconnect if there are remaining servers
        try:
            settings.reload_from_default_server()
            await hummingbot_client.close()
            await hummingbot_client.initialize(force=True)
            default_server = api_servers_config.get_default_server()
            result += f" New default is '{default_server.name}'."
        except Exception:
            pass

        return result

    else:
        return f"Error: Invalid action '{action}'. Use 'add', 'modify', 'set_default', or 'remove'"


@mcp.tool()
@handle_errors("get portfolio overview")
async def get_portfolio_overview(
        account_names: list[str] | None = None,
        connector_names: list[str] | None = None,
        include_balances: bool = True,
        include_perp_positions: bool = True,
        include_lp_positions: bool = True,
        include_active_orders: bool = True,
        as_distribution: bool = False,
        refresh: bool = False,
) -> str:
    """Get a unified portfolio overview with balances, perpetual positions, LP positions, and active orders.

    This tool provides a comprehensive view of your entire portfolio by fetching data from multiple sources
    in parallel. By default, it returns all four types of data, but you can filter to only include
    specific sections.

    Data Sources (fetched in parallel using asyncio.gather):
    1. Token Balances - Holdings across all connected CEX/DEX exchanges
    2. Perpetual Positions - Open perpetual futures positions from CEX
    3. LP Positions (CLMM) - Real-time concentrated liquidity positions from blockchain DEXs
       - Queries database to find all pools user has interacted with
       - Calls get_positions() for each pool to fetch real-time blockchain data
       - Includes real-time fees and token amounts
    4. Active Orders - Currently open orders across all exchanges

    NOTE: This only shows ACTIVE/OPEN positions. For historical data, use search_history() instead.

    Args:
        account_names: List of account names to filter by (optional). If empty, returns all accounts.
        connector_names: List of connector names to filter by (optional). If empty, returns all connectors.
        include_balances: Include token balances in the overview (default: True)
        include_perp_positions: Include perpetual positions in the overview (default: True)
        include_lp_positions: Include LP (CLMM) positions in the overview (default: True)
        include_active_orders: Include active (open) orders in the overview (default: True)
        as_distribution: Show token balances as distribution percentages (default: False)
        refresh: If True, refresh balances from exchanges before returning. If False, return cached state (default: False)
    """
    client = await hummingbot_client.get_client()

    # Handle distribution mode separately
    if as_distribution:
        result = await client.portfolio.get_distribution(
            account_names=account_names,
            connector_names=connector_names
        )
        return f"Portfolio Distribution:\n{result}"

    # Normal portfolio overview
    result = await portfolio_tools.get_portfolio_overview(
        client=client,
        account_names=account_names,
        connector_names=connector_names,
        include_balances=include_balances,
        include_perp_positions=include_perp_positions,
        include_lp_positions=include_lp_positions,
        include_active_orders=include_active_orders,
        refresh=refresh,
    )

    return result["formatted_output"]


# Trading Tools


@mcp.tool()
@handle_errors("place order")
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
    """Place a buy or sell order on a OrderBook Exchange (supports USD values by adding at the start of the amount $).

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
    result = await trading_tools.place_order(
        client=client,
        connector_name=connector_name,
        trading_pair=trading_pair,
        trade_type=trade_type,
        amount=amount,
        order_type=order_type,
        price=price,
        position_action=position_action,
        account_name=account_name,
    )
    return f"Order Result: {result['result']}"


@mcp.tool()
@handle_errors("set position mode and leverage")
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
    client = await hummingbot_client.get_client()
    results = await trading_tools.set_position_mode_and_leverage(
        client=client,
        account_name=account_name,
        connector_name=connector_name,
        trading_pair=trading_pair,
        position_mode=position_mode,
        leverage=leverage,
    )

    response = ""
    if "position_mode" in results:
        response += f"Position Mode Set: {results['position_mode']}\n"
    if "leverage" in results:
        response += f"Leverage Set: {results['leverage']}\n"

    return response.strip()


@mcp.tool()
@handle_errors("search history")
async def search_history(
        data_type: Literal["orders", "perp_positions", "clmm_positions"],
        account_names: list[str] | None = None,
        connector_names: list[str] | None = None,
        trading_pairs: list[str] | None = None,
        status: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 50,
        offset: int = 0,
        network: str | None = None,
        wallet_address: str | None = None,
        position_addresses: list[str] | None = None,
) -> str:
    """Search historical data from the backend database.

    This tool is for historical analysis, reporting, and tax purposes.
    For real-time current state, use get_portfolio_overview() instead.

    Data Types:
    - orders: Historical order data (filled, cancelled, failed)
    - perp_positions: Perpetual positions (both open and closed)
    - clmm_positions: CLMM LP positions (both open and closed)

    Common Filters (apply to all data types):
        account_names: Filter by account names (optional)
        connector_names: Filter by connector names (optional)
        trading_pairs: Filter by trading pairs (optional)
        status: Filter by status (optional, e.g., 'OPEN', 'CLOSED', 'FILLED', 'CANCELED')
        start_time: Start timestamp in seconds (optional)
        end_time: End timestamp in seconds (optional)
        limit: Maximum number of results (default: 50, max: 1000)
        offset: Pagination offset (default: 0)

    CLMM-Specific Filters:
        network: Network filter for CLMM positions (optional)
        wallet_address: Wallet address filter for CLMM positions (optional)
        position_addresses: Specific position addresses for CLMM (optional)

    Examples:
    - Search filled orders: search_history("orders", status="FILLED", limit=100)
    - Search closed perp positions: search_history("perp_positions", status="CLOSED")
    - Search all CLMM positions: search_history("clmm_positions", limit=100)
    """
    client = await hummingbot_client.get_client()

    result = await history_tools.search_history(
        client=client,
        data_type=data_type,
        account_names=account_names,
        connector_names=connector_names,
        trading_pairs=trading_pairs,
        status=status,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
        network=network,
        wallet_address=wallet_address,
        position_addresses=position_addresses,
    )

    return result.get("formatted_output", str(result))


# Market Data Tools


@mcp.tool()
@handle_errors("get market data")
async def get_market_data(
        data_type: Literal["prices", "candles", "funding_rate", "order_book"],
        connector_name: str,
        trading_pairs: list[str] | None = None,
        trading_pair: str | None = None,
        interval: str = "1h",
        days: int = 30,
        query_type: Literal[
            "snapshot", "volume_for_price", "price_for_volume", "quote_volume_for_price", "price_for_quote_volume"] | None = None,
        query_value: float | None = None,
        is_buy: bool = True,
) -> str:
    """Get market data: prices, candles, funding rates, or order book data.

    Data Types:
    - prices: Get latest prices for multiple trading pairs
    - candles: Get OHLCV candle data for a trading pair
    - funding_rate: Get perpetual funding rate (connector must have _perpetual)
    - order_book: Get order book snapshot or queries

    Args:
        data_type: Type of market data to retrieve ('prices', 'candles', 'funding_rate', 'order_book')
        connector_name: Exchange connector name (e.g., 'binance', 'binance_perpetual')
        trading_pairs: List of trading pairs (required for 'prices', e.g., ['BTC-USDT', 'ETH-USD'])
        trading_pair: Single trading pair (required for 'candles', 'funding_rate', 'order_book')
        interval: Candle interval for 'candles' (default: '1h'). Options: '1m', '5m', '15m', '30m', '1h', '4h', '1d'.
        days: Number of days of historical data for 'candles' (default: 30).
        query_type: Order book query type for 'order_book' (default: 'snapshot'). Options: 'snapshot',
            'volume_for_price', 'price_for_volume', 'quote_volume_for_price', 'price_for_quote_volume'.
        query_value: Value for order book queries (required if query_type is not 'snapshot').
        is_buy: Side for order book queries (default: True for buy side).
    """
    client = await hummingbot_client.get_client()

    if data_type == "prices":
        if not trading_pairs:
            return "Error: 'trading_pairs' is required for data_type='prices'"
        result = await market_data_tools.get_prices(
            client=client, connector_name=connector_name, trading_pairs=trading_pairs,
        )
        return (
            f"Latest Prices for {result['connector_name']}:\n"
            f"Timestamp: {result['timestamp']}\n\n"
            f"{result['prices_table']}"
        )

    elif data_type == "candles":
        if not trading_pair:
            return "Error: 'trading_pair' is required for data_type='candles'"
        result = await market_data_tools.get_candles(
            client=client, connector_name=connector_name,
            trading_pair=trading_pair, interval=interval, days=days,
        )
        return (
            f"Candles for {result['trading_pair']} on {result['connector_name']}:\n"
            f"Interval: {result['interval']}\n"
            f"Total Candles: {result['total_candles']}\n\n"
            f"{result['candles_table']}"
        )

    elif data_type == "funding_rate":
        if not trading_pair:
            return "Error: 'trading_pair' is required for data_type='funding_rate'"
        result = await market_data_tools.get_funding_rate(
            client=client, connector_name=connector_name, trading_pair=trading_pair,
        )
        return (
            f"Funding Rate for {result['trading_pair']} on {result['connector_name']}:\n\n"
            f"Funding Rate: {result['funding_rate_pct']:.4f}%\n"
            f"Mark Price: ${result['mark_price']:.2f}\n"
            f"Index Price: ${result['index_price']:.2f}\n"
            f"Next Funding Time: {result['next_funding_time']}"
        )

    elif data_type == "order_book":
        if not trading_pair:
            return "Error: 'trading_pair' is required for data_type='order_book'"
        result = await market_data_tools.get_order_book(
            client=client, connector_name=connector_name, trading_pair=trading_pair,
            query_type=query_type or "snapshot", query_value=query_value, is_buy=is_buy,
        )
        if result["query_type"] == "snapshot":
            return (
                f"Order Book Snapshot for {result['trading_pair']} on {result['connector_name']}:\n"
                f"Timestamp: {result['timestamp']}\n"
                f"Top 10 Levels:\n\n"
                f"{result['order_book_table']}"
            )
        else:
            return (
                f"Order Book Query for {result['trading_pair']} on {result['connector_name']}:\n\n"
                f"Query Type: {result['query_type']}\n"
                f"Query Value: {result['query_value']}\n"
                f"Side: {result['side']}\n"
                f"Result: {result['result']}"
            )

    else:
        return f"Error: Invalid data_type '{data_type}'. Use 'prices', 'candles', 'funding_rate', or 'order_book'"


@mcp.tool()
@handle_errors("manage controllers")
async def manage_controllers(
        action: Literal["list", "describe", "upsert", "delete"],
        target: Literal["controller", "config"] | None = None,
        controller_type: Literal["directional_trading", "market_making", "generic"] | None = None,
        controller_name: str | None = None,
        controller_code: str | None = None,
        config_name: str | None = None,
        config_data: dict[str, Any] | None = None,
        bot_name: str | None = None,
        confirm_override: bool = False,
) -> str:
    """
    Manage controllers and their configurations: list, describe, create/update, delete.

    ⚠️ NOTE: For most trading strategies (grid, DCA, position trading), use manage_executors() instead.
    Only use controllers when the user EXPLICITLY asks for "controllers", "bots", or needs advanced
    multi-strategy bot deployments with centralized risk management.

    Exploration flow:
    1. action="list" → List all controllers and their configs
    2. action="list" + controller_type → List controllers of that type with config counts
    3. action="describe" + controller_name → Show controller code + list its configs + explain parameters
    4. action="describe" + config_name → Show specific config details + which controller it uses

    Modification flow:
    5. action="upsert" + target="controller" → Create/update a controller template
    6. action="upsert" + target="config" → Create/update a controller config
    7. action="delete" + target="controller" → Delete a controller template
    8. action="delete" + target="config" → Delete a controller config

    Common Enum Values for Controller Configs:

    Position Mode (position_mode):
    - "HEDGE" - Allows holding both long and short positions simultaneously
    - "ONEWAY" - Allows only one direction position at a time

    Trade Side (side):
    - 1 or "BUY" - For long/buy positions
    - 2 or "SELL" - For short/sell positions
    - Note: Numeric values are required for controller configs

    Order Type (order_type, open_order_type, take_profit_order_type, etc.):
    - 1 or "MARKET" - Market order
    - 2 or "LIMIT" - Limit order
    - 3 or "LIMIT_MAKER" - Limit maker order (post-only)
    - Note: Numeric values are required for controller configs

    Args:
        action: "list", "describe", "upsert" (create/update), or "delete"
        target: "controller" (template) or "config" (instance). Required for upsert/delete.
        controller_type: Type of controller (e.g., 'directional_trading', 'market_making', 'generic').
        controller_name: Name of the controller to describe or modify.
        controller_code: Code for controller (required for controller upsert).
        config_name: Name of the config to describe or modify.
        config_data: Configuration data (required for config upsert). Must include 'controller_type' and 'controller_name'.
        bot_name: Bot name (for modifying config in a specific bot).
        confirm_override: Required True if overwriting existing items.
    """
    client = await hummingbot_client.get_client()
    result = await controllers_tools.manage_controllers(
        client=client,
        action=action,
        target=target,
        controller_type=controller_type,
        controller_name=controller_name,
        controller_code=controller_code,
        config_name=config_name,
        config_data=config_data,
        bot_name=bot_name,
        confirm_override=confirm_override,
    )
    # list/describe return formatted_output, upsert/delete return message
    return result.get("formatted_output") or result.get("message", str(result))


@mcp.tool()
@handle_errors("manage bots")
async def manage_bots(
        action: Literal["deploy", "status", "logs", "stop_bot", "stop_controllers", "start_controllers"],
        bot_name: str | None = None,
        controllers_config: list[str] | None = None,
        account_name: str | None = "master_account",
        max_global_drawdown_quote: float | None = None,
        max_controller_drawdown_quote: float | None = None,
        image: str = "hummingbot/hummingbot:latest",
        log_type: Literal["error", "general", "all"] = "all",
        limit: int = 50,
        search_term: str | None = None,
        controller_names: list[str] | None = None,
) -> str:
    """Manage controller-based bots: deploy, monitor, get logs, and control execution.

    ⚠️ NOTE: For most trading strategies (grid, DCA, position trading), use manage_executors() instead.
    Only use bots when the user EXPLICITLY asks for "bot" deployment or needs advanced features like
    multi-strategy bots with centralized risk management.

    Actions:
    - deploy: Deploy a new bot with controller configurations (requires bot_name + controllers_config)
    - status: Get status of all active bots (no additional params needed)
    - logs: Get detailed logs for a specific bot (requires bot_name)
    - stop_bot: Stop and archive a bot forever (requires bot_name)
    - stop_controllers: Stop specific controllers in a bot (requires bot_name + controller_names)
    - start_controllers: Start/resume specific controllers (requires bot_name + controller_names)

    Args:
        action: Action to perform on bots.
        bot_name: Name of the bot (required for deploy, logs, stop_bot, stop/start_controllers).
        controllers_config: List of controller config names (required for deploy).
        account_name: Account name for deployment (default: master_account).
        max_global_drawdown_quote: Maximum global drawdown in quote currency (deploy only).
        max_controller_drawdown_quote: Maximum per-controller drawdown in quote currency (deploy only).
        image: Docker image for deployment (default: "hummingbot/hummingbot:latest").
        log_type: Type of logs to retrieve for 'logs' action ('error', 'general', 'all').
        limit: Maximum log entries for 'logs' action (default: 50, max: 1000).
        search_term: Search term to filter logs by message content (logs only).
        controller_names: List of controller names (required for stop/start_controllers).
    """
    client = await hummingbot_client.get_client()

    if action == "deploy":
        if not bot_name:
            return "Error: 'bot_name' is required for deploy action"
        if not controllers_config:
            return "Error: 'controllers_config' is required for deploy action"
        result = await controllers_tools.deploy_bot(
            client=client,
            bot_name=bot_name,
            controllers_config=controllers_config,
            account_name=account_name,
            max_global_drawdown_quote=max_global_drawdown_quote,
            max_controller_drawdown_quote=max_controller_drawdown_quote,
            image=image,
        )
        return result["message"]

    elif action == "status":
        result = await bot_management_tools.get_active_bots_status(client)
        return (
            f"Active Bots Status Summary:\n"
            f"Total Active Bots: {result['total_bots']}\n\n"
            f"{result['bots_table']}"
        )

    elif action == "logs":
        if not bot_name:
            return "Error: 'bot_name' is required for logs action"
        result = await bot_management_tools.get_bot_logs(
            client=client,
            bot_name=bot_name,
            log_type=log_type,
            limit=limit,
            search_term=search_term,
        )
        if "error" in result:
            return result["message"]
        return (
            f"Bot Logs for: {result['bot_name']}\n"
            f"Log Type: {result['log_type']}\n"
            f"Search Term: {result['search_term'] if result['search_term'] else 'None'}\n"
            f"Total Logs Returned: {result['total_logs']}\n\n"
            f"{result['logs_table']}"
        )

    elif action in ("stop_bot", "stop_controllers", "start_controllers"):
        if not bot_name:
            return f"Error: 'bot_name' is required for {action} action"
        result = await bot_management_tools.manage_bot_execution(
            client=client,
            bot_name=bot_name,
            action=action,
            controller_names=controller_names,
        )
        return result["message"]

    else:
        return f"Error: Invalid action '{action}'"


# Executor Management Tools


@mcp.tool()
@handle_errors("manage executors")
async def manage_executors(
        action: Literal["create", "search", "get", "stop", "get_summary", "get_preferences", "save_preferences", "reset_preferences", "positions_summary", "get_position", "clear_position"] | None = None,
        executor_type: str | None = None,
        executor_config: dict[str, Any] | None = None,
        executor_id: str | None = None,
        account_names: list[str] | None = None,
        connector_names: list[str] | None = None,
        trading_pairs: list[str] | None = None,
        executor_types: list[str] | None = None,
        status: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
        keep_position: bool = False,
        save_as_default: bool = False,
        preferences_content: str | None = None,
        account_name: str | None = None,
        connector_name: str | None = None,
        trading_pair: str | None = None,
) -> str:
    """Manage trading executors with progressive disclosure for lifecycle management.

    ⭐ PRIORITY: This is the DEFAULT tool for trading strategies like grid trading, DCA, position trading,
    and arbitrage. Use executors FIRST unless the user explicitly asks for "controllers" or "bots".

    Available Executor Types:

    ## position_executor
    Takes directional positions with defined entry, stop-loss, and take-profit levels.
    Use when: Clear directional view, want automated SL/TP, defined risk/reward.
    Avoid when: Want to provide liquidity, need multi-leg strategies.

    ## dca_executor
    Dollar-cost averages into positions over time with scheduled purchases.
    Use when: Accumulating gradually, reducing timing risk, building long-term position.
    Avoid when: Need immediate full entry, want quick exits.

    ## grid_executor
    Trades in ranging markets with multiple buy/sell levels in a grid pattern.
    Use when: Range-bound market, profit from volatility, want auto-rebalancing.
    Avoid when: Strongly trending market, limited capital for spread across levels.
    Direction rules:
    - LONG grid:  limit_price < start_price < end_price (limit below grid, buys low)
    - SHORT grid: start_price < end_price < limit_price (limit above grid, sells high)
    - side must be explicitly set: 1=BUY (LONG), 2=SELL (SHORT)
    Risk management (NO stop_loss):
    - limit_price is the safety boundary — when price crosses it, the grid stops.
    - keep_position=false: closes position on stop (stop-loss-like exit).
    - keep_position=true: holds position on stop (wait for recovery).

    ## order_executor
    Simple order execution with retry logic and multiple execution strategies.
    Closest executor to a plain BUY/SELL order but with strategy options.
    Use when: Want to place a single buy or sell order with a specific execution strategy
    (LIMIT, MARKET, LIMIT_MAKER, or LIMIT_CHASER).
    Avoid when: Need complex multi-level strategies (use grid/dca instead),
    want automated SL/TP management (use position_executor instead).
    Execution strategies: MARKET, LIMIT, LIMIT_MAKER, LIMIT_CHASER.

    Executors are automated trading components that execute specific strategies.
    This tool guides you through understanding, creating, monitoring, and stopping executors.

    IMPORTANT: When creating any executor, you MUST ask the user for `total_amount_quote` (the capital
    to allocate) before creating. Never assume or default this value. The amount is denominated in the
    quote currency of the trading pair (e.g., BRL for BTC-BRL, USDT for BTC-USDT). If the user gives
    a USD amount, convert it to the quote currency first.

    IMPORTANT - Grid Executor Side:
    When creating a grid_executor, you MUST explicitly set the `side` parameter using numeric enum values:
    - side: 1 = BUY (LONG grid)
    - side: 2 = SELL (SHORT grid)
    The limit_price alone does NOT determine the direction. If side is omitted, it defaults to BUY.
    For SHORT grids (limit_price above the range), always pass side: 2.

    IMPORTANT - Grid Executor Risk Management:
    The grid executor does NOT use stop_loss. Never suggest or expose stop_loss to the user.
    Risk management is handled entirely via `limit_price` + `keep_position`:
    - `limit_price` acts as the safety boundary — when price crosses it, the grid stops.
    - `keep_position=false`: closes the accumulated position on stop (acts like a stop-loss exit).
    - `keep_position=true`: holds the accumulated position on stop (wait for recovery).
    Always guide users to set `limit_price` as their risk boundary and choose `keep_position` accordingly.

    Progressive Flow:
    1. executor_type only → Show config schema with your saved defaults applied
    2. action="create" + executor_config → Create executor (merged with your defaults)
    3. action="search" → Search/list executors with filters
    4. action="get" + executor_id → Get specific executor details
    5. action="stop" + executor_id → Stop executor (with keep_position option)
    6. action="get_summary" → Get overall executor summary

    Preference Management (stored in ~/.hummingbot_mcp/executor_preferences.md):
    7. action="get_preferences" → View raw markdown preferences file (read before saving)
    8. action="save_preferences" + preferences_content → Save complete preferences file content
    9. action="reset_preferences" → Reset all preferences to defaults

    Position Management:
    10. action="positions_summary" → Get aggregated positions summary
    11. action="get_position" + connector_name + trading_pair → Get specific position details
    12. action="clear_position" + connector_name + trading_pair → Clear position closed manually

    Args:
        action: Action to perform. Leave empty to see executor types or config schema.
        executor_type: Type of executor (e.g., 'position_executor', 'dca_executor'). Provide to see config schema.
        executor_config: Configuration for creating an executor. Required for 'create' action.
        executor_id: Executor ID for 'get' or 'stop' actions.
        account_names: Filter by account names (for search).
        connector_names: Filter by connector names (for search).
        trading_pairs: Filter by trading pairs (for search).
        executor_types: Filter by executor types (for search).
        status: Filter by status - 'RUNNING', 'TERMINATED' (for search).
        cursor: Pagination cursor for search results.
        limit: Maximum results to return (default: 50, max: 1000).
        keep_position: When stopping, keep the position open instead of closing it (default: False).
        save_as_default: Save executor_config as default for this executor_type (default: False).
        preferences_content: Complete markdown content for the preferences file. Required for 'save_preferences' action. Read current content with 'get_preferences' first, make edits, then save back.
        account_name: Account name for creating executors (default: 'master_account').
        connector_name: Connector name for position filtering or clearing.
        trading_pair: Trading pair for position filtering or clearing.
    """
    # Create and validate request using Pydantic model
    request = ManageExecutorsRequest(
        action=action,
        executor_type=executor_type,
        executor_config=executor_config,
        executor_id=executor_id,
        account_names=account_names,
        connector_names=connector_names,
        trading_pairs=trading_pairs,
        executor_types=executor_types,
        status=status,
        cursor=cursor,
        limit=limit,
        keep_position=keep_position,
        save_as_default=save_as_default,
        preferences_content=preferences_content,
        account_name=account_name,
        connector_name=connector_name,
        trading_pair=trading_pair,
    )

    client = await hummingbot_client.get_client()
    result = await manage_executors_impl(client, request)

    return result.get("formatted_output", str(result))


# Gateway Tools


@mcp.tool()
@handle_errors("manage gateway container", GATEWAY_LOG_HINT)
async def manage_gateway_container(
        action: Literal["get_status", "start", "stop", "restart", "get_logs"],
        config: dict[str, Any] | None = None,
        tail: int | None = 100,
) -> str:
    """Manage Gateway container lifecycle operations.

    Supports:
    - get_status: Check Gateway container status
    - start: Start Gateway with configuration
    - stop: Stop Gateway container
    - restart: Restart Gateway (optionally with new config)
    - get_logs: Get container logs

    Args:
        action: Action to perform on Gateway container
        config: Gateway configuration (required for 'start', optional for 'restart').
               Required fields: passphrase (Gateway passphrase), image (Docker image).
               Optional fields: port (exposed port, default: 15888), environment (env vars)
        tail: Number of log lines to retrieve (only for 'get_logs' action, default: 100, max: 200)
    """
    # Create and validate request using Pydantic model
    request = GatewayContainerRequest(action=action, config=config, tail=tail)

    client = await hummingbot_client.get_client()
    result = await manage_gateway_container_impl(client, request)
    return format_gateway_container_result(result)


@mcp.tool()
@handle_errors("manage gateway configuration", GATEWAY_LOG_HINT)
async def manage_gateway_config(
        resource_type: Literal["chains", "networks", "tokens", "connectors", "pools", "wallets"],
        action: Literal["list", "get", "update", "add", "delete"],
        network_id: str | None = None,
        connector_name: str | None = None,
        config_updates: dict[str, Any] | None = None,
        token_address: str | None = None,
        token_symbol: str | None = None,
        token_decimals: int | None = None,
        token_name: str | None = None,
        pool_type: str | None = None,
        pool_base: str | None = None,
        pool_quote: str | None = None,
        pool_address: str | None = None,
        search: str | None = None,
        network: str | None = None,
        chain: str | None = None,
        private_key: str | None = None,
        wallet_address: str | None = None,
) -> str:
    """Manage Gateway configuration for chains, networks, tokens, connectors, pools, and wallets.

    Resource Types:
    - chains: Get all blockchain chains
    - networks: List/get/update network configurations (format: 'chain-network')
    - tokens: List/add/delete tokens per network
    - connectors: List/get/update DEX connector configurations
    - pools: List/add liquidity pools per connector/network
    - wallets: Add/delete wallets for blockchain chains

    Args:
        resource_type: Type of resource to manage
        action: Action to perform on the resource
        network_id: Network ID in format 'chain-network' (e.g., 'solana-mainnet-beta')
        connector_name: DEX connector name (e.g., 'meteora', 'raydium')
        config_updates: Configuration updates as key-value pairs
        token_address: Token contract address
        token_symbol: Token symbol (e.g., 'USDC')
        token_decimals: Token decimals (e.g., 6 for USDC)
        token_name: Token name (optional)
        pool_type: Pool type (e.g., 'CLMM', 'AMM')
        pool_base: Base token symbol for pool
        pool_quote: Quote token symbol for pool
        pool_address: Pool contract address
        search: Search term to filter tokens
        network: Network name (e.g., 'mainnet-beta') for pool operations
        chain: Blockchain chain for wallet (e.g., 'solana', 'ethereum')
        private_key: Private key for wallet (required for 'add' wallet action)
        wallet_address: Wallet address (required for 'delete' wallet action)
    """
    # Create and validate request using Pydantic model
    request = GatewayConfigRequest(
        resource_type=resource_type,
        action=action,
        network_id=network_id,
        connector_name=connector_name,
        config_updates=config_updates,
        token_address=token_address,
        token_symbol=token_symbol,
        token_decimals=token_decimals,
        token_name=token_name,
        pool_type=pool_type,
        pool_base=pool_base,
        pool_quote=pool_quote,
        pool_address=pool_address,
        search=search,
        network=network,
        chain=chain,
        private_key=private_key,
        wallet_address=wallet_address,
    )

    client = await hummingbot_client.get_client()
    result = await manage_gateway_config_impl(client, request)
    return format_gateway_config_result(result)


@mcp.tool()
@handle_errors("manage gateway swaps", GATEWAY_LOG_HINT)
async def manage_gateway_swaps(
        action: Literal["quote", "execute", "search", "get_status"],
        connector: str | None = None,
        network: str | None = None,
        trading_pair: str | None = None,
        side: Literal["BUY", "SELL"] | None = None,
        amount: str | None = None,
        slippage_pct: str | None = "1.0",
        wallet_address: str | None = None,
        transaction_hash: str | None = None,
        search_connector: str | None = None,
        search_network: str | None = None,
        search_wallet_address: str | None = None,
        search_trading_pair: str | None = None,
        status: Literal["SUBMITTED", "CONFIRMED", "FAILED"] | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = 50,
        offset: int | None = 0,
) -> str:
    """Manage Gateway swap operations: quote, execute, search swaps.

    Supports DEX router swaps via Jupiter (Solana) and 0x (Ethereum).

    Actions:
    - quote: Get price quote for a swap before executing
    - execute: Execute a swap transaction on DEX
    - search: Search swap history with filters
    - get_status: Get status of a specific swap by transaction hash

    Quote/Execute Parameters (required for quote/execute):
        connector: DEX router connector (e.g., 'jupiter', '0x')
        network: Network ID in 'chain-network' format (e.g., 'solana-mainnet-beta', 'ethereum-mainnet')
        trading_pair: Trading pair in BASE-QUOTE format (e.g., 'SOL-USDC', 'ETH-USDT')
        side: Trade side - 'BUY' (buy base with quote) or 'SELL' (sell base for quote)
        amount: Amount to swap (for BUY: base to receive, for SELL: base to sell)
        slippage_pct: Maximum slippage percentage (default: 1.0)
        wallet_address: Wallet address for execute (optional, uses default if not provided)

    Get Status Parameters:
        transaction_hash: Transaction hash to check status

    Search Parameters (all optional):
        search_connector: Filter by connector
        search_network: Filter by network
        search_wallet_address: Filter by wallet address
        search_trading_pair: Filter by trading pair
        status: Filter by status (SUBMITTED, CONFIRMED, FAILED)
        start_time: Start timestamp (unix seconds)
        end_time: End timestamp (unix seconds)
        limit: Max results (default: 50, max: 1000)
        offset: Pagination offset (default: 0)
    """
    # Create and validate request using Pydantic model
    request = GatewaySwapRequest(
        action=action,
        connector=connector,
        network=network,
        trading_pair=trading_pair,
        side=side,
        amount=amount,
        slippage_pct=slippage_pct,
        wallet_address=wallet_address,
        transaction_hash=transaction_hash,
        search_connector=search_connector,
        search_network=search_network,
        search_wallet_address=search_wallet_address,
        search_trading_pair=search_trading_pair,
        status=status,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    client = await hummingbot_client.get_client()
    result = await manage_gateway_swaps_impl(client, request)
    return format_gateway_swap_result(action, result)


@mcp.tool()
@handle_errors("manage gateway CLMM", GATEWAY_LOG_HINT)
async def manage_gateway_clmm(
        action: Literal["list_pools", "get_pool_info", "open_position", "close_position", "collect_fees", "get_positions"],
        connector: str | None = None,
        network: str | None = None,
        pool_address: str | None = None,
        position_address: str | None = None,
        page: int = 0,
        limit: int = 50,
        search_term: str | None = None,
        sort_key: str | None = "volume",
        order_by: str | None = "desc",
        include_unknown: bool = True,
        detailed: bool = False,
        wallet_address: str | None = None,
        lower_price: str | None = None,
        upper_price: str | None = None,
        base_token_amount: str | None = None,
        quote_token_amount: str | None = None,
        slippage_pct: str | None = "1.0",
        extra_params: dict[str, Any] | None = None,
) -> str:
    """Manage Gateway CLMM pools and positions: explore pools, open/close positions, collect fees.

    Supports CLMM DEX connectors (Meteora, Raydium, Uniswap V3) for concentrated liquidity.

    Pool Exploration:
    - list_pools: Browse available CLMM pools with filtering and sorting
    - get_pool_info: Get detailed information about a specific pool (requires network + pool_address)

    Position Management:
    - open_position: Create a new CLMM position with initial liquidity
    - close_position: Close a position completely (removes all liquidity)
    - collect_fees: Collect accumulated fees from a position
    - get_positions: Get all positions for a specific pool (fetches real-time data from blockchain)

    Args:
        action: Action to perform on CLMM pools or positions.
        connector: CLMM connector name (e.g., 'meteora', 'raydium', 'uniswap'). Required for most actions.
        network: Network ID in 'chain-network' format (e.g., 'solana-mainnet-beta'). Required for get_pool_info and position actions.
        pool_address: Pool contract address (required for get_pool_info, open_position, get_positions).
        position_address: Position NFT address (required for close_position and collect_fees).
        page: Page number for list_pools (default: 0).
        limit: Results per page for list_pools (default: 50, max: 100).
        search_term: Search term to filter pools by token symbols (e.g., 'SOL', 'USDC').
        sort_key: Sort by field for list_pools (volume, tvl, feetvlratio, etc.).
        order_by: Sort order for list_pools ('asc' or 'desc').
        include_unknown: Include pools with unverified tokens (default: True).
        detailed: Return detailed table with more columns for list_pools (default: False).
        wallet_address: Wallet address for position actions (optional, uses default if not provided).
        lower_price: Lower price bound for open_position (e.g., '150').
        upper_price: Upper price bound for open_position (e.g., '250').
        base_token_amount: Amount of base token for open_position (optional).
        quote_token_amount: Amount of quote token for open_position (optional).
        slippage_pct: Maximum slippage percentage for open_position (default: 1.0).
        extra_params: Additional connector-specific parameters (e.g., {"strategyType": 0} for Meteora).
    """
    request = GatewayCLMMRequest(
        action=action,
        connector=connector,
        network=network,
        pool_address=pool_address,
        position_address=position_address,
        page=page,
        limit=limit,
        search_term=search_term,
        sort_key=sort_key,
        order_by=order_by,
        include_unknown=include_unknown,
        detailed=detailed,
        wallet_address=wallet_address,
        lower_price=lower_price,
        upper_price=upper_price,
        base_token_amount=base_token_amount,
        quote_token_amount=quote_token_amount,
        slippage_pct=slippage_pct,
        extra_params=extra_params,
    )

    client = await hummingbot_client.get_client()
    result = await manage_gateway_clmm_impl(client, request)

    # Pool actions return formatted output via format_gateway_clmm_pool_result
    if action in ("list_pools", "get_pool_info"):
        return format_gateway_clmm_pool_result(action, result)
    else:
        return f"Gateway CLMM Position Management Result: {result}"


async def main():
    """Run the MCP server"""
    # Setup logging once at application start
    logger.info("Starting Hummingbot MCP Server")
    logger.info(f"Configured API URL: {settings.api_url}")
    logger.info(f"Default Account: {settings.default_account}")
    logger.info("Server will connect to API on first use (lazy initialization)")
    logger.info("💡 Use 'configure_api_servers' tool to manage API server connections")

    # Run the server with FastMCP
    # Connection to API will happen lazily on first tool use
    try:
        await mcp.run_stdio_async()
    finally:
        # Clean up client connection if it was initialized
        await hummingbot_client.close()


if __name__ == "__main__":
    asyncio.run(main())
