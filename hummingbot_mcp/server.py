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
from hummingbot_mcp.hummingbot_client import hummingbot_client
from hummingbot_mcp.settings import settings
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


# Helper Functions

def format_bot_logs_as_table(logs: list[dict[str, Any]]) -> str:
    """
    Format bot logs as a table string for better LLM processing.

    Columns: time | level | category | message
    """
    if not logs:
        return "No logs found."

    from datetime import datetime

    def format_timestamp(ts: float) -> str:
        """Format unix timestamp to readable time"""
        try:
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%H:%M:%S")
        except:
            return "N/A"

    def truncate_message(msg: str, max_len: int = 80) -> str:
        """Truncate message if too long"""
        if len(msg) <= max_len:
            return msg
        return msg[:max_len-3] + "..."

    # Header
    header = "time     | level | category | message"
    separator = "-" * 120

    # Format each log as a row
    rows = []
    for log_entry in logs:
        time_str = format_timestamp(log_entry.get("timestamp", 0))
        level = log_entry.get("level_name", "INFO")[:4]  # Truncate to 4 chars (INFO, WARN, ERR)
        category = log_entry.get("log_category", "gen")[:3]  # gen or err
        message = truncate_message(log_entry.get("msg", ""))

        row = f"{time_str} | {level:4} | {category:3} | {message}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_active_bots_as_table(bots_data: dict[str, Any]) -> str:
    """
    Format active bots data as a table string for better LLM processing.

    Columns: bot_name | controller | status | realized_pnl | unrealized_pnl | global_pnl | volume | errors
    """
    if not bots_data or "data" not in bots_data or not bots_data["data"]:
        return "No active bots found."

    def format_number(num: Any) -> str:
        """Format number to be more compact"""
        if num is None or num == "N/A":
            return "N/A"
        try:
            num_float = float(num)
            if abs(num_float) < 0.01 and num_float != 0:
                return f"{num_float:.4f}"
            return f"{num_float:.2f}"
        except (ValueError, TypeError):
            return str(num)

    def format_pct(pct: Any) -> str:
        """Format percentage"""
        if pct is None or pct == "N/A":
            return "N/A"
        try:
            return f"{float(pct) * 100:.2f}%"
        except (ValueError, TypeError):
            return str(pct)

    # Header
    header = "bot_name | controller | status | realized_pnl | unrealized_pnl | global_pnl | volume | errors | recent_logs"
    separator = "-" * 120

    # Format each bot as rows
    rows = []
    for bot_name, bot_data in bots_data["data"].items():
        if not isinstance(bot_data, dict):
            continue

        bot_status = bot_data.get("status", "unknown")
        error_count = len(bot_data.get("error_logs", []))
        log_count = len(bot_data.get("general_logs", []))

        # Get controller performance data
        performance = bot_data.get("performance", {})

        if not performance:
            # Bot with no controllers
            row = (
                f"{bot_name[:20]} | "
                f"N/A | "
                f"{bot_status} | "
                f"N/A | N/A | N/A | N/A | "
                f"{error_count} | "
                f"{log_count}"
            )
            rows.append(row)
        else:
            # Bot with controllers
            for controller_name, controller_data in performance.items():
                ctrl_status = controller_data.get("status", "unknown")
                ctrl_perf = controller_data.get("performance", {})

                realized_pnl = format_number(ctrl_perf.get("realized_pnl_quote"))
                unrealized_pnl = format_number(ctrl_perf.get("unrealized_pnl_quote"))
                global_pnl = format_number(ctrl_perf.get("global_pnl_quote"))
                global_pnl_pct = format_pct(ctrl_perf.get("global_pnl_pct"))
                volume = format_number(ctrl_perf.get("volume_traded"))

                row = (
                    f"{bot_name[:20]} | "
                    f"{controller_name[:20]} | "
                    f"{ctrl_status} | "
                    f"{realized_pnl} | "
                    f"{unrealized_pnl} | "
                    f"{global_pnl} ({global_pnl_pct}) | "
                    f"{volume} | "
                    f"{error_count} | "
                    f"{log_count}"
                )
                rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_orders_as_table(orders: list[dict[str, Any]]) -> str:
    """
    Format orders as a table string for better LLM processing.

    Columns: time | pair | side | type | amount | price | filled | status
    """
    if not orders:
        return "No orders found."

    from datetime import datetime

    def format_timestamp(ts: Any) -> str:
        """Format timestamp to readable format"""
        try:
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
            else:
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
            return dt.strftime("%m/%d %H:%M")
        except:
            return "N/A"

    def format_number(num: Any) -> str:
        """Format number compactly"""
        if num is None or num == "N/A":
            return "N/A"
        try:
            num_float = float(num)
            if abs(num_float) < 0.01 and num_float != 0:
                return f"{num_float:.4f}"
            return f"{num_float:.2f}"
        except (ValueError, TypeError):
            return str(num)

    # Header
    header = "time        | pair          | side | type   | amount   | price    | filled   | status"
    separator = "-" * 120

    # Format each order as a row
    rows = []
    for order in orders:
        time_str = format_timestamp(order.get("created_at") or order.get("creation_timestamp") or order.get("timestamp", 0))
        pair = (order.get("trading_pair") or "N/A")[:12]
        side = (order.get("trade_type") or order.get("side") or "N/A")[:4]
        order_type = (order.get("order_type") or order.get("type") or "N/A")[:6]
        amount = format_number(order.get("amount") or order.get("order_size"))
        price = format_number(order.get("price"))
        filled = format_number(order.get("filled_amount") or order.get("executed_amount_base"))
        status = (order.get("status") or "N/A")[:8]

        row = f"{time_str:11} | {pair:13} | {side:4} | {order_type:6} | {amount:8} | {price:8} | {filled:8} | {status}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_positions_as_table(positions: list[dict[str, Any]]) -> str:
    """
    Format positions as a table string for better LLM processing.

    Columns: pair | side | amount | entry_price | current_price | unrealized_pnl | leverage
    """
    if not positions:
        return "No positions found."

    def format_number(num: Any) -> str:
        """Format number compactly"""
        if num is None or num == "N/A":
            return "N/A"
        try:
            num_float = float(num)
            if abs(num_float) < 0.01 and num_float != 0:
                return f"{num_float:.4f}"
            return f"{num_float:.2f}"
        except (ValueError, TypeError):
            return str(num)

    # Header
    header = "pair          | side  | amount   | entry_price | current_price | unrealized_pnl | leverage"
    separator = "-" * 120

    # Format each position as a row
    rows = []
    for position in positions:
        pair = (position.get("trading_pair") or "N/A")[:12]
        side = (position.get("position_side") or position.get("side") or "N/A")[:5]
        amount = format_number(position.get("amount") or position.get("position_size"))
        entry_price = format_number(position.get("entry_price"))
        current_price = format_number(position.get("current_price") or position.get("mark_price"))
        unrealized_pnl = format_number(position.get("unrealized_pnl"))
        leverage = position.get("leverage") or "N/A"

        row = f"{pair:13} | {side:5} | {amount:8} | {entry_price:11} | {current_price:13} | {unrealized_pnl:14} | {leverage}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_prices_as_table(prices_data: dict[str, Any]) -> str:
    """
    Format prices data as a table string for better LLM processing.
    Columns: trading_pair | price
    """
    prices = prices_data.get("prices", {})

    if not prices:
        return "No prices available."

    # Header
    header = "trading_pair      | price"
    separator = "-" * 50

    # Format each price as a row
    rows = []
    for pair, price in prices.items():
        pair_str = pair[:16].ljust(16)
        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        row = f"{pair_str}  | {price_str}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_candles_as_table(candles: list[dict[str, Any]]) -> str:
    """
    Format candle data as a table string for better LLM processing.
    Columns: time | open | high | low | close | volume
    """
    if not candles:
        return "No candles found."

    from datetime import datetime

    def format_timestamp(ts: float) -> str:
        """Format unix timestamp to readable datetime"""
        try:
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%m/%d %H:%M")
        except:
            return "N/A"

    def format_price(price: Any) -> str:
        """Format price"""
        try:
            return f"{float(price):.2f}"
        except:
            return "N/A"

    def format_volume(vol: Any) -> str:
        """Format volume compactly"""
        try:
            vol_float = float(vol)
            if vol_float >= 1_000_000:
                return f"{vol_float/1_000_000:.2f}M"
            elif vol_float >= 1_000:
                return f"{vol_float/1_000:.2f}K"
            else:
                return f"{vol_float:.2f}"
        except:
            return "N/A"

    # Header
    header = "time        | open     | high     | low      | close    | volume"
    separator = "-" * 85

    # Format each candle as a row
    rows = []
    for candle in candles:
        time_str = format_timestamp(candle.get("timestamp", 0))
        open_price = format_price(candle.get("open"))
        high_price = format_price(candle.get("high"))
        low_price = format_price(candle.get("low"))
        close_price = format_price(candle.get("close"))
        volume = format_volume(candle.get("volume"))

        row = f"{time_str:11} | {open_price:8} | {high_price:8} | {low_price:8} | {close_price:8} | {volume}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_order_book_as_table(order_book_data: dict[str, Any]) -> str:
    """
    Format order book snapshot as a table string for better LLM processing.
    Shows top 10 bids and asks side by side.
    """
    bids = order_book_data.get("bids", [])[:10]
    asks = order_book_data.get("asks", [])[:10]

    if not bids and not asks:
        return "No order book data available."

    # Header
    header = "BIDS                      |  ASKS"
    sub_header = "price      | amount       |  price      | amount"
    separator = "-" * 65

    # Format rows
    rows = []
    max_rows = max(len(bids), len(asks))

    for i in range(max_rows):
        bid_price = f"{bids[i]['price']:10.2f}" if i < len(bids) else " " * 10
        bid_amount = f"{bids[i]['amount']:12.3f}" if i < len(bids) else " " * 12
        ask_price = f"{asks[i]['price']:10.2f}" if i < len(asks) else " " * 10
        ask_amount = f"{asks[i]['amount']:12.3f}" if i < len(asks) else " " * 12

        row = f"{bid_price} | {bid_amount} |  {ask_price} | {ask_amount}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{sub_header}\n{separator}\n" + "\n".join(rows)
    return table


def format_portfolio_as_table(portfolio_data: dict[str, Any]) -> str:
    """
    Format portfolio balances as a table string for better LLM processing.

    Columns: token | connector | total | available | value_usd

    Portfolio structure:
    {
      "account_name": {
        "connector_name": [
          {"token": "BTC", "units": 0.5, "available_units": 0.5, "value": 50000}
        ]
      }
    }
    """
    if not portfolio_data:
        return "No portfolio data found."

    def format_number(num: Any) -> str:
        """Format number compactly"""
        if num is None or num == "N/A":
            return "N/A"
        try:
            num_float = float(num)
            if num_float >= 1000:
                return f"{num_float/1000:.2f}K"
            elif abs(num_float) < 0.01 and num_float != 0:
                return f"{num_float:.6f}"
            return f"{num_float:.4f}"
        except (ValueError, TypeError):
            return str(num)

    # Header
    header = "token    | connector         | total        | available    | value_usd"
    separator = "-" * 100

    # Flatten nested structure: account -> connector -> balances
    rows = []
    for account_name, connectors in portfolio_data.items():
        if not isinstance(connectors, dict):
            continue

        for connector_name, balances in connectors.items():
            if not isinstance(balances, list):
                continue

            for balance in balances:
                token = (balance.get("token") or "N/A")[:8]
                connector = connector_name[:17]
                total = format_number(balance.get("units"))
                available = format_number(balance.get("available_units"))
                value_usd = format_number(balance.get("value"))

                row = f"{token:8} | {connector:17} | {total:12} | {available:12} | {value_usd}"
                rows.append(row)

    if not rows:
        return "No portfolio balances found."

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


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
            # For distribution, we can keep it simple for now
            return f"Portfolio Distribution: {result}"

        # Get portfolio state
        result = await client.portfolio.get_state(account_names=account_names, connector_names=connector_names)

        # Debug: Check the actual structure
        if not result or not isinstance(result, dict):
            return f"Error: Unexpected portfolio response format. Type: {type(result)}"

        # Format portfolio as table for better readability
        portfolio_table = format_portfolio_as_table(result)

        # Calculate total value from nested structure: account -> connector -> balances
        total_value = 0.0
        for account_name, connectors in result.items():
            if not isinstance(connectors, dict):
                continue
            for connector_name, balances in connectors.items():
                if not isinstance(balances, list):
                    continue
                for balance in balances:
                    value = balance.get("value", 0)
                    if value:
                        total_value += float(value)

        summary = (
            f"Portfolio Balances:\n"
            f"Total Value (USD): ${total_value:.2f}\n\n"
            f"{portfolio_table}"
        )

        return summary
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

        # Format orders as table for better readability
        orders = result.get("data", [])
        orders_table = format_orders_as_table(orders)

        pagination = result.get("pagination", {})
        total_orders = pagination.get("total_count", len(orders))
        has_more = pagination.get("has_more", False)
        next_cursor = pagination.get("next_cursor")

        summary = (
            f"Orders Search Result:\n"
            f"Total Orders Returned: {len(orders)}\n"
            f"Total Count: {total_orders}\n"
            f"Status Filter: {status if status else 'All'}\n"
            f"Has More: {has_more}\n"
            f"Next Cursor: {next_cursor if next_cursor else 'None'}\n\n"
            f"{orders_table}"
        )

        return summary
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

        # Format positions as table for better readability
        positions = result.get("positions", [])
        positions_table = format_positions_as_table(positions)

        total_positions = len(positions)

        summary = (
            f"Positions Result:\n"
            f"Total Positions: {total_positions}\n\n"
            f"{positions_table}"
        )

        return summary
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

        # Format prices as table for better readability
        prices_table = format_prices_as_table(prices)

        from datetime import datetime
        timestamp = prices.get("timestamp", 0)
        time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"

        summary = (
            f"Latest Prices for {connector_name}:\n"
            f"Timestamp: {time_str}\n\n"
            f"{prices_table}"
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

        # Format candles as table for better readability
        candles_table = format_candles_as_table(candles)

        summary = (
            f"Candles for {trading_pair} on {connector_name}:\n"
            f"Interval: {interval}\n"
            f"Total Candles: {len(candles)}\n\n"
            f"{candles_table}"
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
        if "_perpetual" not in connector_name:
            raise ValueError(
                f"Connector '{connector_name}' is not a perpetual connector. Funding rates are only available for"
                f"perpetual connectors."
            )
        funding_rate = await client.market_data.get_funding_info(connector_name=connector_name,
                                                                 trading_pair=trading_pair)

        # Format funding rate as clean text
        from datetime import datetime
        next_funding_time = funding_rate.get("next_funding_time", 0)
        time_str = datetime.fromtimestamp(next_funding_time).strftime("%Y-%m-%d %H:%M:%S") if next_funding_time else "N/A"

        rate = funding_rate.get("funding_rate", 0)
        rate_pct = rate * 100  # Convert to percentage

        summary = (
            f"Funding Rate for {trading_pair} on {connector_name}:\n\n"
            f"Funding Rate: {rate_pct:.4f}%\n"
            f"Mark Price: ${funding_rate.get('mark_price', 0):.2f}\n"
            f"Index Price: ${funding_rate.get('index_price', 0):.2f}\n"
            f"Next Funding Time: {time_str}"
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
        if query_type == "snapshot":
            order_book = await client.market_data.get_order_book(connector_name=connector_name,
                                                                 trading_pair=trading_pair)

            # Format order book as table for better readability
            order_book_table = format_order_book_as_table(order_book)

            from datetime import datetime
            timestamp = order_book.get("timestamp", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"

            summary = (
                f"Order Book Snapshot for {trading_pair} on {connector_name}:\n"
                f"Timestamp: {time_str}\n"
                f"Top 10 Levels:\n\n"
                f"{order_book_table}"
            )

            return summary
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

            # Format query results as clean text
            side_str = "BUY" if is_buy else "SELL"
            summary = (
                f"Order Book Query for {trading_pair} on {connector_name}:\n\n"
                f"Query Type: {query_type}\n"
                f"Query Value: {query_value}\n"
                f"Side: {side_str}\n"
                f"Result: {result}"
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
            template = await client.controllers.get_controller_config_template(controller_type, controller_name)

            result += f"Controller: {controller_name} ({controller_type})\n\n"
            result += f"Controller Code:\n{controller_code}\n\n"

            # Format configs list more compactly
            result += f"Total Configs Available: {len(controller_configs)}\n"
            # Show first 10 configs, or all if less than 10
            if len(controller_configs) <= 10:
                result += f"Configs:\n" + "\n".join(f"  - {c}" for c in controller_configs if c) + "\n\n"
            else:
                result += f"Configs (showing first 10 of {len(controller_configs)}):\n"
                result += "\n".join(f"  - {c}" for c in controller_configs[:10] if c) + "\n"
                result += f"  ... and {len(controller_configs) - 10} more\n\n"

            # Format config template parameters as table instead of verbose dict
            result += "Configuration Parameters:\n"
            result += "parameter                    | type              | default\n"
            result += "-" * 80 + "\n"

            for param_name, param_info in template.items():
                if param_name in ['id', 'controller_name', 'controller_type', 'candles_config', 'initial_positions']:
                    continue  # Skip internal fields

                param_type = str(param_info.get('type', 'unknown'))
                # Simplify type names
                param_type = param_type.replace("<class '", "").replace("'>", "").replace("decimal.Decimal", "Decimal")
                param_type = param_type.replace("typing.", "").split(".")[-1][:15]

                default = str(param_info.get('default', 'None'))
                if len(default) > 30:
                    default = default[:27] + "..."

                result += f"{param_name:28} | {param_type:17} | {default}\n"

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

        # Format as table for better readability
        bots_table = format_active_bots_as_table(active_bots)

        # Count total bots
        total_bots = len(active_bots.get("data", {})) if isinstance(active_bots, dict) else 0

        summary = (
            f"Active Bots Status Summary:\n"
            f"Total Active Bots: {total_bots}\n\n"
            f"{bots_table}"
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

        # Format logs as table for better readability
        logs_table = format_bot_logs_as_table(logs)

        summary = (
            f"Bot Logs for: {bot_name}\n"
            f"Log Type: {log_type}\n"
            f"Search Term: {search_term if search_term else 'None'}\n"
            f"Total Logs Returned: {len(logs)}\n\n"
            f"{logs_table}"
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
            return (
                f"Gateway Container Status:\n\n"
                f"Status: {'Running ✓' if running else 'Stopped ✗'}\n"
                f"Container ID: {status.get('container_id', 'N/A')[:12]}...\n"
                f"Image: {status.get('image', 'N/A')}\n"
                f"Port: {status.get('port', 'N/A')}\n"
                f"Created: {status.get('created_at', 'N/A')[:19]}"
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
        raise ToolError(f"Failed to manage gateway container: {str(e)}")


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
        raise ToolError(f"Failed to manage gateway configuration: {str(e)}")


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
            swaps = result.get("result", {}).get("swaps", [])

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
        raise ToolError(f"Failed to manage gateway swaps: {str(e)}")


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
        )

        from .tools.gateway_clmm import explore_gateway_clmm_pools as explore_gateway_clmm_pools_impl

        result = await explore_gateway_clmm_pools_impl(request)

        # Return formatted table for list_pools to reduce response size
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

        return f"Gateway CLMM Pool Exploration Result: {result}"
    except Exception as e:
        logger.error(f"explore_gateway_clmm_pools failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to explore gateway CLMM pools: {str(e)}")


@mcp.tool()
async def manage_gateway_clmm_positions(
        action: Literal["open_position", "close_position", "collect_fees", "get_positions", "search_positions"],
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
        search_network: str | None = None,
        search_connector: str | None = None,
        search_wallet_address: str | None = None,
        trading_pair: str | None = None,
        status: Literal["OPEN", "CLOSED"] | None = None,
        position_addresses: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        refresh: bool = False,
) -> str:
    """Manage Gateway CLMM positions: open, close, collect fees, and search positions.

    Supports CLMM DEX connectors (Meteora, Raydium, Uniswap V3) for concentrated liquidity positions.

    Actions:
    - open_position: Create a new CLMM position with initial liquidity
    - close_position: Close a position completely (removes all liquidity)
    - collect_fees: Collect accumulated fees from a position
    - get_positions: Get all positions owned by a wallet for a specific pool
    - search_positions: Search positions with various filters

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

    Search Parameters (optional for search_positions):
        search_network: Filter by network
        search_connector: Filter by connector
        search_wallet_address: Filter by wallet address
        trading_pair: Filter by trading pair (e.g., 'SOL-USDC')
        status: Filter by status (OPEN, CLOSED)
        position_addresses: Filter by specific position addresses
        limit: Max results (default: 50, max: 1000)
        offset: Pagination offset (default: 0)
        refresh: Refresh position data from Gateway before returning (default: False)
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
            search_network=search_network,
            search_connector=search_connector,
            search_wallet_address=search_wallet_address,
            trading_pair=trading_pair,
            status=status,
            position_addresses=position_addresses,
            limit=limit,
            offset=offset,
            refresh=refresh,
        )

        from .tools.gateway_clmm import manage_gateway_clmm_positions as manage_gateway_clmm_positions_impl

        result = await manage_gateway_clmm_positions_impl(request)

        # Format search_positions results with pagination info
        if action == "search_positions" and isinstance(result, dict):
            filters = result.get("filters", {})
            pagination = result.get("pagination", {})
            positions = result.get("result", {}).get("positions", [])

            summary = (
                f"Gateway CLMM Positions Search Result:\n"
                f"Total Positions Found: {len(positions)}\n"
                f"Limit: {pagination.get('limit', 'N/A')}, Offset: {pagination.get('offset', 'N/A')}\n"
                f"Filters: {filters if filters else 'None'}\n\n"
                f"Positions: {positions}"
            )
            return summary

        return f"Gateway CLMM Position Management Result: {result}"
    except Exception as e:
        logger.error(f"manage_gateway_clmm_positions failed: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to manage gateway CLMM positions: {str(e)}")


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
