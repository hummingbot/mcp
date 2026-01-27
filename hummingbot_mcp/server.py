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
from hummingbot_mcp.exceptions import MaxConnectionsAttemptError as HBConnectionError, ToolError
from hummingbot_mcp.formatters import (
    format_active_bots_as_table,
    format_bot_logs_as_table,
    format_portfolio_as_table,
)
from hummingbot_mcp.hummingbot_client import hummingbot_client
from hummingbot_mcp.settings import settings
from hummingbot_mcp.tools import bot_management as bot_management_tools
from hummingbot_mcp.tools import controllers as controllers_tools
from hummingbot_mcp.tools import executors as executors_tools
from hummingbot_mcp.tools import market_data as market_data_tools
from hummingbot_mcp.tools import portfolio as portfolio_tools
from hummingbot_mcp.tools import trading as trading_tools
from hummingbot_mcp.tools.account import SetupConnectorRequest
from hummingbot_mcp.tools.gateway import GatewayContainerRequest, GatewayConfigRequest
from hummingbot_mcp.tools.gateway_swap import GatewaySwapRequest
from hummingbot_mcp.tools.gateway_clmm import GatewayCLMMPoolRequest, GatewayCLMMPositionRequest

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

        # Format response based on action type
        action = result.get("action", "")

        if action == "list_connectors":
            connectors = result.get("connectors", [])
            # Format connectors in columns for better readability
            connector_lines = []
            for i in range(0, len(connectors), 4):
                line = "  ".join(f"{c:25}" for c in connectors[i:i+4])
                connector_lines.append(line)

            return (
                f"Available Exchange Connectors ({result.get('total_connectors', 0)} total):\n\n"
                + "\n".join(connector_lines) + "\n\n"
                f"{result.get('current_accounts', '')}\n\n"
                f"Next Step: {result.get('next_step', '')}\n"
                f"Example: {result.get('example', '')}"
            )

        elif action == "show_config_map":
            fields = result.get("required_fields", [])
            example_dict = result.get("example", {})

            return (
                f"Required Credentials for {result.get('connector', '')}:\n\n"
                f"Fields needed:\n" + "\n".join(f"  - {field}" for field in fields) + "\n\n"
                f"Next Step: {result.get('next_step', '')}\n"
                f"Example: {result.get('example', '')}"
            )

        elif action == "select_account":
            accounts = result.get("accounts", [])
            return (
                f"{result.get('message', '')}\n\n"
                f"Available Accounts:\n" + "\n".join(f"  - {acc}" for acc in accounts) + "\n\n"
                f"Default Account: {result.get('default_account', '')}\n\n"
                f"Next Step: {result.get('next_step', '')}\n"
                f"Example: {result.get('example', '')}"
            )

        elif action == "requires_confirmation":
            return (
                f"⚠️  {result.get('message', '')}\n\n"
                f"Account: {result.get('account', '')}\n"
                f"Connector: {result.get('connector', '')}\n"
                f"Warning: {result.get('warning', '')}\n\n"
                f"Next Step: {result.get('next_step', '')}\n"
                f"Example: {result.get('example', '')}"
            )

        elif action == "override_rejected":
            return (
                f"❌ {result.get('message', '')}\n\n"
                f"Account: {result.get('account', '')}\n"
                f"Connector: {result.get('connector', '')}\n\n"
                f"Next Step: {result.get('next_step', '')}"
            )

        elif action in ["credentials_added", "credentials_overridden"]:
            return (
                f"✅ {result.get('message', '')}\n\n"
                f"Account: {result.get('account', '')}\n"
                f"Connector: {result.get('connector', '')}\n"
                f"Credentials Count: {result.get('credentials_count', 0)}\n"
                f"Was Existing: {result.get('was_existing', False)}\n\n"
                f"Next Step: {result.get('next_step', '')}"
            )

        # Fallback for unknown actions
        return f"Setup Connector Result: {result}"
    except Exception as e:
        logger.error(f"setup_connector failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to setup connector: {str(e)}")


@mcp.tool()
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

    except Exception as e:
        logger.error(f"configure_api_servers failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to configure API servers: {str(e)}")


@mcp.tool()
async def get_portfolio_overview(
        account_names: list[str] | None = None,
        connector_names: list[str] | None = None,
        include_balances: bool = True,
        include_perp_positions: bool = True,
        include_lp_positions: bool = True,
        include_active_orders: bool = True,
        as_distribution: bool = False,
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
    """
    try:
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
        )

        return result["formatted_output"]

    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"get_portfolio_overview failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to get portfolio overview: {str(e)}")


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
    try:
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
    except HBConnectionError as e:
        # Re-raise connection errors with the helpful message from hummingbot_client
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"set_account_position_mode_and_leverage failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to set position mode and leverage: {str(e)}")


@mcp.tool()
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
    try:
        client = await hummingbot_client.get_client()

        from .tools import history as history_tools

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

    except HBConnectionError as e:
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"search_history failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to search history: {str(e)}")


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
        result = await market_data_tools.get_prices(
            client=client,
            connector_name=connector_name,
            trading_pairs=trading_pairs,
        )

        summary = (
            f"Latest Prices for {result['connector_name']}:\n"
            f"Timestamp: {result['timestamp']}\n\n"
            f"{result['prices_table']}"
        )

        return summary
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
        result = await market_data_tools.get_candles(
            client=client,
            connector_name=connector_name,
            trading_pair=trading_pair,
            interval=interval,
            days=days,
        )

        summary = (
            f"Candles for {result['trading_pair']} on {result['connector_name']}:\n"
            f"Interval: {result['interval']}\n"
            f"Total Candles: {result['total_candles']}\n\n"
            f"{result['candles_table']}"
        )

        return summary
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
        result = await market_data_tools.get_funding_rate(
            client=client,
            connector_name=connector_name,
            trading_pair=trading_pair,
        )

        summary = (
            f"Funding Rate for {result['trading_pair']} on {result['connector_name']}:\n\n"
            f"Funding Rate: {result['funding_rate_pct']:.4f}%\n"
            f"Mark Price: ${result['mark_price']:.2f}\n"
            f"Index Price: ${result['index_price']:.2f}\n"
            f"Next Funding Time: {result['next_funding_time']}"
        )

        return summary
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
        result = await market_data_tools.get_order_book(
            client=client,
            connector_name=connector_name,
            trading_pair=trading_pair,
            query_type=query_type,
            query_value=query_value,
            is_buy=is_buy,
        )

        # Format response based on query type
        if result["query_type"] == "snapshot":
            summary = (
                f"Order Book Snapshot for {result['trading_pair']} on {result['connector_name']}:\n"
                f"Timestamp: {result['timestamp']}\n"
                f"Top 10 Levels:\n\n"
                f"{result['order_book_table']}"
            )
        else:
            summary = (
                f"Order Book Query for {result['trading_pair']} on {result['connector_name']}:\n\n"
                f"Query Type: {result['query_type']}\n"
                f"Query Value: {result['query_value']}\n"
                f"Side: {result['side']}\n"
                f"Result: {result['result']}"
            )
        return summary
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
        result = await controllers_tools.explore_controllers(
            client=client,
            action=action,
            controller_type=controller_type,
            controller_name=controller_name,
            config_name=config_name,
        )
        return result["formatted_output"]

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
        result = await controllers_tools.modify_controllers(
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
        return result["message"]

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
        result = await bot_management_tools.get_active_bots_status(client)

        summary = (
            f"Active Bots Status Summary:\n"
            f"Total Active Bots: {result['total_bots']}\n\n"
            f"{result['bots_table']}"
        )

        return summary
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
        result = await bot_management_tools.get_bot_logs(
            client=client,
            bot_name=bot_name,
            log_type=log_type,
            limit=limit,
            search_term=search_term,
        )

        # Check for errors
        if "error" in result:
            return result["message"]

        summary = (
            f"Bot Logs for: {result['bot_name']}\n"
            f"Log Type: {result['log_type']}\n"
            f"Search Term: {result['search_term'] if result['search_term'] else 'None'}\n"
            f"Total Logs Returned: {result['total_logs']}\n\n"
            f"{result['logs_table']}"
        )

        return summary

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
        result = await bot_management_tools.manage_bot_execution(
            client=client,
            bot_name=bot_name,
            action=action,
            controller_names=controller_names,
        )
        return result["message"]

    except HBConnectionError as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        raise ToolError(
            "Failed to connect to Hummingbot API. Please ensure it is running and API credentials are correct.")
    except Exception as e:
        logger.error(f"manage_bot_execution failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage bot execution: {str(e)}")


@mcp.tool()
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
    try:
        # Create and validate request using Pydantic model
        request = GatewayContainerRequest(action=action, config=config, tail=tail)

        from .tools.gateway import manage_gateway_container as manage_gateway_container_impl

        result = await manage_gateway_container_impl(request)

        # Format result based on action
        action = result.get("action", "")

        if action == "get_status":
            status = result.get("status", {})
            running = status.get("running", False)
            container_id = status.get('container_id')
            created_at = status.get('created_at')

            # Handle None values properly
            container_id_display = f"{container_id[:12]}..." if container_id else "None"
            created_at_display = created_at[:19] if created_at else "None"

            return (
                f"Gateway Container Status:\n\n"
                f"Status: {'Running ✓' if running else 'Stopped ✗'}\n"
                f"Container ID: {container_id_display}\n"
                f"Image: {status.get('image') or 'None'}\n"
                f"Port: {status.get('port') or 'None'}\n"
                f"Created: {created_at_display}"
            )

        elif action == "get_logs":
            logs = result.get("logs", "No logs available")
            return f"Gateway Container Logs:\n\n{logs}"

        elif action in ["start", "stop", "restart"]:
            message = result.get("message", "")
            return f"Gateway Container: {message}"

        # Fallback for other actions
        return f"Gateway Container Result: {result}"
    except Exception as e:
        logger.error(f"manage_gateway_container failed: {str(e)}", exc_info=True)
        error_msg = f"Failed to manage gateway container: {str(e)}"
        if action != "get_logs":
            error_msg += "\n\n💡 Check gateway logs for more details: manage_gateway_container(action='get_logs')"
        raise ToolError(error_msg)


@mcp.tool()
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
    try:
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

        from .tools.gateway import manage_gateway_config as manage_gateway_config_impl

        result = await manage_gateway_config_impl(request)

        # Format result based on resource_type and action
        resource_type = result.get("resource_type", "")
        action = result.get("action", "")

        if action == "list":
            if resource_type == "chains":
                chains = result.get("result", {}).get("chains", [])
                output = "Available Chains:\n\n"
                for chain_info in chains:
                    chain = chain_info.get("chain", "")
                    networks = chain_info.get("networks", [])
                    output += f"- {chain}: {', '.join(networks)}\n"
                return output

            elif resource_type == "networks":
                networks = result.get("result", {}).get("networks", [])
                count = result.get("result", {}).get("count", len(networks))
                output = f"Available Networks ({count} total):\n\n"
                for network in networks:
                    output += f"- {network.get('network_id', 'N/A')}\n"
                return output

            elif resource_type == "connectors":
                connectors = result.get("result", {}).get("connectors", [])
                output = f"Available DEX Connectors ({len(connectors)} total):\n\n"
                for conn in connectors:
                    if isinstance(conn, dict):
                        name = conn.get("name", "unknown")
                        trading_types = ", ".join(conn.get("trading_types", []))
                        chain = conn.get("chain", "")
                        output += f"- {name} ({chain}): {trading_types}\n"
                    else:
                        output += f"- {conn}\n"
                return output

            elif resource_type == "tokens":
                tokens = result.get("result", {}).get("tokens", [])
                network_id = result.get("result", {}).get("network_id", "")
                output = f"Tokens on {network_id} ({len(tokens)} total):\n\n"
                output += "symbol   | address\n"
                output += "-" * 50 + "\n"
                for token in tokens[:20]:  # Limit to first 20
                    symbol = token.get("symbol", "")[:8]
                    address = token.get("address", "")
                    if len(address) > 20:
                        address = f"{address[:8]}...{address[-6:]}"
                    output += f"{symbol:8} | {address}\n"
                if len(tokens) > 20:
                    output += f"... and {len(tokens) - 20} more tokens\n"
                return output

            elif resource_type == "wallets":
                wallets = result.get("result", {}).get("wallets", [])
                output = f"Configured Wallets ({len(wallets)} total):\n\n"
                for wallet in wallets:
                    chain = wallet.get("chain", "")
                    address = wallet.get("address", "")
                    if len(address) > 20:
                        address = f"{address[:10]}...{address[-8:]}"
                    output += f"- {chain}: {address}\n"
                return output

        elif action in ["add", "delete", "update"]:
            message = result.get("result", {}).get("message", "")
            return f"Gateway Config {action.title()}: {message}"

        elif action == "get":
            # Keep structured for get action as it returns detailed config
            return f"Gateway Configuration:\n{result.get('result', {})}"

        # Fallback
        return f"Gateway Configuration Result: {result}"
    except Exception as e:
        logger.error(f"manage_gateway_config failed: {str(e)}", exc_info=True)
        error_msg = f"Failed to manage gateway configuration: {str(e)}"
        error_msg += "\n\n💡 Check gateway logs for more details: manage_gateway_container(action='get_logs')"
        raise ToolError(error_msg)


@mcp.tool()
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
    try:
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

        from .tools.gateway_swap import manage_gateway_swaps as manage_gateway_swaps_impl

        result = await manage_gateway_swaps_impl(request)

        # Format search results with pagination info
        if action == "search" and isinstance(result, dict):
            filters = result.get("filters", {})
            pagination = result.get("pagination", {})
            swaps = result.get("result", {}).get("data", [])

            summary = (
                f"Gateway Swaps Search Result:\n"
                f"Total Swaps Found: {len(swaps)}\n"
                f"Limit: {pagination.get('limit', 'N/A')}, Offset: {pagination.get('offset', 'N/A')}\n"
                f"Filters: {filters if filters else 'None'}\n\n"
                f"Swaps: {swaps}"
            )
            return summary

        return f"Gateway Swap Result: {result}"
    except Exception as e:
        logger.error(f"manage_gateway_swaps failed: {str(e)}", exc_info=True)
        error_msg = f"Failed to manage gateway swaps: {str(e)}"
        error_msg += "\n\n💡 Check gateway logs for more details: manage_gateway_container(action='get_logs')"
        raise ToolError(error_msg)


@mcp.tool()
async def explore_gateway_clmm_pools(
        action: Literal["list_pools", "get_pool_info"],
        connector: str,
        network: str | None = None,
        pool_address: str | None = None,
        page: int = 0,
        limit: int = 50,
        search_term: str | None = None,
        sort_key: str | None = "volume",
        order_by: str | None = "desc",
        include_unknown: bool = True,
        detailed: bool = False,
) -> str:
    """Explore Gateway CLMM pools: list pools and get pool information.

    Supports CLMM DEX connectors (Meteora, Raydium, Uniswap V3) for concentrated liquidity pools.

    Actions:
    - list_pools: Browse available CLMM pools with filtering and sorting
    - get_pool_info: Get detailed information about a specific pool (requires network and pool_address)

    Args:
        action: Action to perform ('list_pools' or 'get_pool_info')
        connector: CLMM connector name (e.g., 'meteora', 'raydium', 'uniswap')
        network: Network ID in 'chain-network' format (required for get_pool_info, e.g., 'solana-mainnet-beta')
        pool_address: Pool contract address (required for get_pool_info)
        page: Page number for list_pools (default: 0)
        limit: Results per page for list_pools (default: 50, max: 100)
        search_term: Search term to filter pools by token symbols (e.g., 'SOL', 'USDC')
        sort_key: Sort by field (volume, tvl, feetvlratio, etc.)
        order_by: Sort order ('asc' or 'desc')
        include_unknown: Include pools with unverified tokens (default: True)
        detailed: Return detailed table with more columns including mint addresses, fee percentages, and time-series metrics (default: False)
    """
    try:
        # Create and validate request using Pydantic model
        request = GatewayCLMMPoolRequest(
            action=action,
            connector=connector,
            network=network,
            pool_address=pool_address,
            page=page,
            limit=limit,
            search_term=search_term,
            sort_key=sort_key,
            order_by=order_by,
            include_unknown=include_unknown,
            detailed=detailed,
        )

        from .tools.gateway_clmm import explore_gateway_clmm_pools as explore_gateway_clmm_pools_impl

        result = await explore_gateway_clmm_pools_impl(request)

        # Return formatted table for list_pools (non-detailed mode)
        if action == "list_pools" and "pools_table" in result:
            summary = (
                f"Gateway CLMM Pool Exploration Result:\n"
                f"Connector: {result['connector']}\n"
                f"Total Pools: {result['pagination']['total']}\n"
                f"Page: {result['pagination']['page']}, Limit: {result['pagination']['limit']}\n"
                f"Filters: {result['filters']}\n\n"
                f"{result['pools_table']}"
            )
            return summary

        # Return full dict for detailed mode or get_pool_info
        return f"Gateway CLMM Pool Exploration Result: {result}"
    except Exception as e:
        logger.error(f"explore_gateway_clmm_pools failed: {str(e)}", exc_info=True)
        error_msg = f"Failed to explore gateway CLMM pools: {str(e)}"
        error_msg += "\n\n💡 Check gateway logs for more details: manage_gateway_container(action='get_logs')"
        raise ToolError(error_msg)


@mcp.tool()
async def manage_gateway_clmm_positions(
        action: Literal["open_position", "close_position", "collect_fees", "get_positions"],
        connector: str | None = None,
        network: str | None = None,
        wallet_address: str | None = None,
        pool_address: str | None = None,
        position_address: str | None = None,
        lower_price: str | None = None,
        upper_price: str | None = None,
        base_token_amount: str | None = None,
        quote_token_amount: str | None = None,
        slippage_pct: str | None = "1.0",
        extra_params: dict[str, Any] | None = None,
) -> str:
    """Manage Gateway CLMM positions: open, close, collect fees, and get positions.

    Supports CLMM DEX connectors (Meteora, Raydium, Uniswap V3) for concentrated liquidity positions.

    Actions:
    - open_position: Create a new CLMM position with initial liquidity
    - close_position: Close a position completely (removes all liquidity)
    - collect_fees: Collect accumulated fees from a position
    - get_positions: Get all positions owned by a wallet for a specific pool (fetches real-time data from blockchain)

    Open Position Parameters (required for open_position):
        connector: CLMM connector name (e.g., 'meteora', 'raydium')
        network: Network ID in 'chain-network' format (e.g., 'solana-mainnet-beta')
        pool_address: Pool contract address
        lower_price: Lower price bound (e.g., '150')
        upper_price: Upper price bound (e.g., '250')
        base_token_amount: Amount of base token to provide (optional)
        quote_token_amount: Amount of quote token to provide (optional)
        slippage_pct: Maximum slippage percentage (default: 1.0)
        wallet_address: Wallet address (optional, uses default if not provided)
        extra_params: Additional connector-specific parameters (e.g., {"strategyType": 0} for Meteora)

    Close/Collect Parameters (required for close_position and collect_fees):
        connector: CLMM connector name
        network: Network ID in 'chain-network' format
        position_address: Position NFT address
        wallet_address: Wallet address (optional)

    Get Positions Parameters (required for get_positions):
        connector: CLMM connector name
        network: Network ID in 'chain-network' format
        pool_address: Pool contract address
        wallet_address: Wallet address (optional)
    """
    try:
        # Create and validate request using Pydantic model
        request = GatewayCLMMPositionRequest(
            action=action,
            connector=connector,
            network=network,
            wallet_address=wallet_address,
            pool_address=pool_address,
            position_address=position_address,
            lower_price=lower_price,
            upper_price=upper_price,
            base_token_amount=base_token_amount,
            quote_token_amount=quote_token_amount,
            slippage_pct=slippage_pct,
            extra_params=extra_params,
        )

        from .tools.gateway_clmm import manage_gateway_clmm_positions as manage_gateway_clmm_positions_impl

        result = await manage_gateway_clmm_positions_impl(request)

        return f"Gateway CLMM Position Management Result: {result}"
    except Exception as e:
        if isinstance(e, ToolError):
            # Re-raise ToolErrors as-is (they already have good error messages)
            raise
        logger.error(f"manage_gateway_clmm_positions failed: {str(e)}", exc_info=True)
        error_msg = f"Failed to manage gateway CLMM positions: {str(e)}"
        error_msg += "\n\n💡 Check gateway logs for more details: manage_gateway_container(action='get_logs')"
        raise ToolError(error_msg)


@mcp.tool()
async def manage_executors(
        action: Literal["list_types", "get_schema", "search", "get_summary", "get_executor", "create", "stop", "delete", "get_positions_summary", "get_position_held", "clear_position_held"],
        # For get_schema
        executor_type: str | None = None,
        # For get_executor, stop, delete
        executor_id: str | None = None,
        # For create
        executor_config: dict[str, Any] | None = None,
        # For stop
        keep_position: bool = False,
        # For search filters
        executor_ids: list[str] | None = None,
        controller_id: str | None = None,
        executor_types: list[str] | None = None,
        statuses: list[str] | None = None,
        is_active: bool | None = None,
        is_archived: bool | None = None,
        trading_pair: str | None = None,
        connector_name: str | None = None,
        account_name: str | None = None,
        side: str | None = None,
        start_time_from: int | None = None,
        start_time_to: int | None = None,
        end_time_from: int | None = None,
        end_time_to: int | None = None,
) -> str:
    """Unified tool for managing trading executors - automated trading objects that execute specific strategies.

    Executors are powerful automation components that handle trading logic:
    - PositionExecutor: Single position with triple barrier (TP/SL/Time) risk management
    - GridExecutor: Grid trading with multiple price levels
    - DCAExecutor: Dollar-cost averaging at multiple entry points
    - ArbitrageExecutor: Cross-exchange arbitrage
    - TWAPExecutor: Time-weighted average price execution
    - XEMMExecutor: Cross-exchange market making
    - OrderExecutor: Simple order execution (market, limit, chaser)

    Actions:
    - list_types: List all available executor types with descriptions
    - get_schema: Get configuration schema for a specific executor type (requires executor_type)
    - search: Search executors with filters (is_active, statuses, trading_pair, etc.)
    - get_summary: Get summary statistics of all executors
    - get_executor: Get details of a specific executor (requires executor_id)
    - create: Create a new executor (requires executor_config)
    - stop: Stop a running executor (requires executor_id, optional keep_position)
    - delete: Delete an executor (requires executor_id)
    - get_positions_summary: Get summary of all position holds across executors
    - get_position_held: Get position held for specific connector/pair (requires connector_name, trading_pair)
    - clear_position_held: Clear position held for specific connector/pair (requires connector_name, trading_pair)

    Args:
        action: Action to perform
        executor_type: Executor type for get_schema (e.g., 'position_executor', 'grid_executor')
        executor_id: Executor ID for get_executor, stop, delete actions
        executor_config: Configuration dict for create action (must include 'type' field)
        keep_position: Whether to keep position when stopping executor (default: False)
        executor_ids: Filter by specific executor IDs
        controller_id: Filter by controller ID
        executor_types: Filter by executor types
        statuses: Filter by statuses (e.g., ['RUNNING', 'COMPLETED'])
        is_active: Filter by active state
        is_archived: Filter by archived state
        trading_pair: Filter by trading pair
        connector_name: Filter by connector name
        account_name: Account name for operations
        side: Filter by side (BUY/SELL)
        start_time_from: Filter by start time (unix timestamp)
        start_time_to: Filter by start time (unix timestamp)
        end_time_from: Filter by end time (unix timestamp)
        end_time_to: Filter by end time (unix timestamp)

    Example executor_config for PositionExecutor:
    {
        "type": "position_executor",
        "trading_pair": "BTC-USDT",
        "connector_name": "binance_perpetual",
        "side": 1,  # 1=BUY, 2=SELL
        "amount": "0.01",
        "leverage": 10,
        "triple_barrier_config": {
            "stop_loss": "0.02",
            "take_profit": "0.04",
            "time_limit": 3600
        }
    }
    """
    try:
        client = await hummingbot_client.get_client()

        # Route to appropriate function based on action
        if action in ["list_types", "get_schema", "search", "get_summary", "get_executor"]:
            result = await executors_tools.explore_executors(
                client=client,
                action=action,
                executor_type=executor_type,
                executor_id=executor_id,
                executor_ids=executor_ids,
                controller_id=controller_id,
                executor_types=executor_types,
                statuses=statuses,
                is_active=is_active,
                is_archived=is_archived,
                trading_pair=trading_pair,
                connector_name=connector_name,
                account_name=account_name,
                side=side,
                start_time_from=start_time_from,
                start_time_to=start_time_to,
                end_time_from=end_time_from,
                end_time_to=end_time_to,
            )
            return result.get("formatted_output", str(result))

        elif action in ["create", "stop", "delete"]:
            result = await executors_tools.manage_executors(
                client=client,
                action=action,
                executor_config=executor_config,
                executor_id=executor_id,
                keep_position=keep_position,
                account_name=account_name,
            )
            return result.get("message", str(result))

        elif action in ["get_positions_summary", "get_position_held", "clear_position_held"]:
            # Map action names to position hold actions
            position_action_map = {
                "get_positions_summary": "get_summary",
                "get_position_held": "get_position",
                "clear_position_held": "clear_position",
            }
            result = await executors_tools.manage_position_holds(
                client=client,
                action=position_action_map[action],
                connector_name=connector_name,
                trading_pair=trading_pair,
                account_name=account_name,
            )
            return result.get("formatted_output", str(result))

        else:
            return f"Error: Invalid action '{action}'"

    except HBConnectionError as e:
        raise ToolError(str(e))
    except Exception as e:
        logger.error(f"manage_executors failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage executors: {str(e)}")


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
