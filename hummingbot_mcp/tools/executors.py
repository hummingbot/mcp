"""
Executor management operations business logic.

This module provides the core business logic for managing trading executors,
including exploration, creation, orchestration, and position hold management.

Executors are automated trading objects that execute specific trading strategies:
- PositionExecutor: Manages single positions with triple barrier (TP/SL/Time) risk management
- GridExecutor: Creates grid trading strategies with multiple price levels
- DCAExecutor: Dollar-cost averaging with multiple entry points
- ArbitrageExecutor: Cross-exchange arbitrage trading
- TWAPExecutor: Time-weighted average price execution
- XEMMExecutor: Cross-exchange market making
- OrderExecutor: Simple order execution with various strategies (limit, market, chaser)
"""
from typing import Any, Literal


# Executor type descriptions for documentation
EXECUTOR_DESCRIPTIONS = {
    "position_executor": {
        "name": "Position Executor",
        "description": "Manages a single trading position with triple barrier risk management (take profit, stop loss, time limit). Supports trailing stops and various order types.",
        "use_cases": [
            "Opening and managing positions with automatic risk management",
            "Setting up positions with trailing stop losses",
            "Time-limited trading positions",
        ],
        "key_params": [
            "trading_pair: The market to trade (e.g., 'BTC-USDT')",
            "connector_name: Exchange connector (e.g., 'binance_perpetual')",
            "side: Trade direction (1=BUY, 2=SELL)",
            "amount: Position size in base currency",
            "triple_barrier_config: Risk management settings (stop_loss, take_profit, time_limit, trailing_stop)",
            "leverage: Position leverage (default: 1)",
            "entry_price: Optional specific entry price",
        ],
    },
    "grid_executor": {
        "name": "Grid Executor",
        "description": "Creates a grid of buy/sell orders across a price range. Each level has its own take profit target. Ideal for range-bound markets.",
        "use_cases": [
            "Range trading in sideways markets",
            "Accumulation strategies at multiple price levels",
            "Automated market making within a price band",
        ],
        "key_params": [
            "trading_pair: The market to trade",
            "connector_name: Exchange connector",
            "start_price: Lower bound of the grid",
            "end_price: Upper bound of the grid",
            "limit_price: Price limit for execution",
            "total_amount_quote: Total capital to deploy (in quote currency)",
            "side: Grid direction (1=BUY grid, 2=SELL grid)",
            "max_open_orders: Maximum concurrent open orders",
            "min_spread_between_orders: Minimum spread between grid levels",
        ],
    },
    "dca_executor": {
        "name": "DCA Executor",
        "description": "Dollar-cost averaging executor that places multiple orders at predefined price levels. Supports maker/taker modes and risk management.",
        "use_cases": [
            "Accumulating positions at multiple price points",
            "Averaging down/up strategies",
            "Systematic position building",
        ],
        "key_params": [
            "trading_pair: The market to trade",
            "connector_name: Exchange connector",
            "side: Trade direction (1=BUY, 2=SELL)",
            "amounts_quote: List of amounts for each DCA level",
            "prices: List of prices for each DCA level",
            "take_profit: Optional take profit percentage",
            "stop_loss: Optional stop loss percentage",
            "mode: Execution mode (MAKER or TAKER)",
        ],
    },
    "arbitrage_executor": {
        "name": "Arbitrage Executor",
        "description": "Executes arbitrage trades between two markets when price difference exceeds minimum profitability threshold.",
        "use_cases": [
            "Cross-exchange arbitrage",
            "Price discrepancy exploitation",
            "Market neutral strategies",
        ],
        "key_params": [
            "buying_market: ConnectorPair for the buy side",
            "selling_market: ConnectorPair for the sell side",
            "order_amount: Size of arbitrage orders",
            "min_profitability: Minimum profit threshold to execute",
        ],
    },
    "twap_executor": {
        "name": "TWAP Executor",
        "description": "Time-weighted average price executor that splits a large order into smaller orders executed over time to minimize market impact.",
        "use_cases": [
            "Large order execution with minimal slippage",
            "Gradual position building/unwinding",
            "Reducing market impact",
        ],
        "key_params": [
            "trading_pair: The market to trade",
            "connector_name: Exchange connector",
            "side: Trade direction (1=BUY, 2=SELL)",
            "total_amount_quote: Total amount to execute",
            "total_duration: Total time in seconds for execution",
            "order_interval: Seconds between each order",
            "mode: Execution mode (MAKER or TAKER)",
        ],
    },
    "xemm_executor": {
        "name": "XEMM Executor",
        "description": "Cross-exchange market making executor that provides liquidity on one exchange while hedging on another.",
        "use_cases": [
            "Cross-exchange market making",
            "Spread capture between exchanges",
            "Liquidity provision with hedging",
        ],
        "key_params": [
            "buying_market: ConnectorPair for buy orders",
            "selling_market: ConnectorPair for sell orders",
            "maker_side: Which side to make (1=BUY, 2=SELL)",
            "order_amount: Size of market making orders",
            "min_profitability: Minimum acceptable spread",
            "target_profitability: Target spread to aim for",
            "max_profitability: Maximum spread (wider = more conservative)",
        ],
    },
    "order_executor": {
        "name": "Order Executor",
        "description": "Simple order execution with multiple strategies: MARKET, LIMIT, LIMIT_MAKER, and LIMIT_CHASER (follows price).",
        "use_cases": [
            "Single order execution with specific strategy",
            "Chasing limit orders that follow the market",
            "Maker-only order placement",
        ],
        "key_params": [
            "trading_pair: The market to trade",
            "connector_name: Exchange connector",
            "side: Trade direction (1=BUY, 2=SELL)",
            "amount: Order size in base currency",
            "execution_strategy: MARKET, LIMIT, LIMIT_MAKER, or LIMIT_CHASER",
            "price: Required for LIMIT and LIMIT_MAKER strategies",
            "chaser_config: Required for LIMIT_CHASER (distance, refresh_threshold)",
        ],
    },
}


async def explore_executors(
    client: Any,
    action: Literal["list_types", "get_schema", "search", "get_summary", "get_executor"],
    executor_type: str | None = None,
    executor_id: str | None = None,
    # Search filters
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
) -> dict[str, Any]:
    """
    Explore executors: list types, get schemas, search, and retrieve details.

    Args:
        client: Hummingbot API client
        action: Action to perform
        executor_type: Type of executor (for get_schema)
        executor_id: Specific executor ID (for get_executor)
        Various search filters for the search action

    Returns:
        Dictionary containing exploration results and formatted output
    """
    if action == "list_types":
        # Get available executor types from API
        available_types = await client.executors.get_available_executor_types()

        result = "Available Executor Types:\n\n"
        for exec_type in available_types:
            info = EXECUTOR_DESCRIPTIONS.get(exec_type, {})
            name = info.get("name", exec_type)
            desc = info.get("description", "No description available")
            result += f"## {name} ({exec_type})\n"
            result += f"{desc}\n\n"
            if "use_cases" in info:
                result += "Use Cases:\n"
                for use_case in info["use_cases"]:
                    result += f"  - {use_case}\n"
                result += "\n"

        result += "\nUse action='get_schema' with executor_type to see configuration parameters."

        return {
            "action": "list_types",
            "executor_types": available_types,
            "descriptions": EXECUTOR_DESCRIPTIONS,
            "formatted_output": result,
        }

    elif action == "get_schema":
        if not executor_type:
            return {
                "action": "get_schema",
                "error": "executor_type is required for get_schema action",
                "formatted_output": "Error: Please provide executor_type parameter",
            }

        schema = await client.executors.get_executor_config_schema(executor_type)
        info = EXECUTOR_DESCRIPTIONS.get(executor_type, {})

        result = f"Configuration Schema for {info.get('name', executor_type)}:\n\n"
        result += f"Type: {executor_type}\n"
        result += f"Description: {info.get('description', 'N/A')}\n\n"

        if "key_params" in info:
            result += "Key Parameters:\n"
            for param in info["key_params"]:
                result += f"  - {param}\n"
            result += "\n"

        result += "Full Schema:\n"
        result += "-" * 60 + "\n"
        result += "Parameter                    | Type              | Required | Default\n"
        result += "-" * 60 + "\n"

        properties = schema.get("properties", schema)
        required_fields = schema.get("required", [])

        for param_name, param_info in properties.items():
            if param_name in ["type"]:
                continue

            param_type = param_info.get("type", param_info.get("anyOf", "unknown"))
            if isinstance(param_type, list):
                param_type = "/".join(str(t) for t in param_type[:2])
            param_type = str(param_type)[:17]

            is_required = "Yes" if param_name in required_fields else "No"
            default = str(param_info.get("default", "-"))[:15]

            result += f"{param_name:28} | {param_type:17} | {is_required:8} | {default}\n"

        return {
            "action": "get_schema",
            "executor_type": executor_type,
            "schema": schema,
            "description": info,
            "formatted_output": result,
        }

    elif action == "search":
        search_result = await client.executors.search_executors(
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

        executors = search_result.get("data", search_result) if isinstance(search_result, dict) else search_result

        if not executors:
            return {
                "action": "search",
                "executors": [],
                "formatted_output": "No executors found matching the criteria.",
            }

        result = f"Found {len(executors)} executor(s):\n\n"
        result += "ID (short)   | Type              | Status     | Pair        | Side | PnL\n"
        result += "-" * 80 + "\n"

        for executor in executors[:50]:  # Limit display to 50
            exec_id = str(executor.get("id", ""))[:12]
            exec_type = str(executor.get("type", ""))[:17]
            status = str(executor.get("status", ""))[:10]
            pair = str(executor.get("trading_pair", executor.get("config", {}).get("trading_pair", "")))[:11]
            side = str(executor.get("side", executor.get("config", {}).get("side", "")))[:4]
            pnl = executor.get("net_pnl_quote", executor.get("realized_pnl_quote", 0))
            pnl_str = f"{float(pnl):.2f}" if pnl else "0.00"

            result += f"{exec_id:12} | {exec_type:17} | {status:10} | {pair:11} | {side:4} | {pnl_str}\n"

        if len(executors) > 50:
            result += f"\n... and {len(executors) - 50} more executors"

        return {
            "action": "search",
            "executors": executors,
            "total": len(executors),
            "formatted_output": result,
        }

    elif action == "get_summary":
        summary = await client.executors.get_summary()

        result = "Executors Summary:\n\n"

        if isinstance(summary, dict):
            for key, value in summary.items():
                if isinstance(value, dict):
                    result += f"{key}:\n"
                    for k, v in value.items():
                        result += f"  {k}: {v}\n"
                else:
                    result += f"{key}: {value}\n"
        else:
            result += str(summary)

        return {
            "action": "get_summary",
            "summary": summary,
            "formatted_output": result,
        }

    elif action == "get_executor":
        if not executor_id:
            return {
                "action": "get_executor",
                "error": "executor_id is required for get_executor action",
                "formatted_output": "Error: Please provide executor_id parameter",
            }

        executor = await client.executors.get_executor(executor_id)

        result = f"Executor Details:\n\n"
        result += f"ID: {executor.get('id', 'N/A')}\n"
        result += f"Type: {executor.get('type', 'N/A')}\n"
        result += f"Status: {executor.get('status', 'N/A')}\n"
        result += f"Controller ID: {executor.get('controller_id', 'N/A')}\n\n"

        config = executor.get("config", {})
        if config:
            result += "Configuration:\n"
            for key, value in config.items():
                if key not in ["id", "type", "timestamp"]:
                    result += f"  {key}: {value}\n"

        result += "\nPerformance:\n"
        result += f"  Net PnL (Quote): {executor.get('net_pnl_quote', 0)}\n"
        result += f"  Realized PnL (Quote): {executor.get('realized_pnl_quote', 0)}\n"
        result += f"  Volume Traded: {executor.get('filled_amount_quote', 0)}\n"

        return {
            "action": "get_executor",
            "executor": executor,
            "formatted_output": result,
        }

    else:
        return {
            "action": action,
            "error": f"Invalid action: {action}",
            "formatted_output": f"Error: Invalid action '{action}'. Use 'list_types', 'get_schema', 'search', 'get_summary', or 'get_executor'.",
        }


async def manage_executors(
    client: Any,
    action: Literal["create", "stop", "delete"],
    executor_config: dict[str, Any] | None = None,
    executor_id: str | None = None,
    keep_position: bool = False,
    account_name: str | None = None,
) -> dict[str, Any]:
    """
    Create, stop, or delete executors.

    Args:
        client: Hummingbot API client
        action: Action to perform (create, stop, delete)
        executor_config: Configuration for creating executor
        executor_id: ID of executor to stop/delete
        keep_position: Whether to keep position when stopping (default: False)
        account_name: Account to run executor on (for create)

    Returns:
        Dictionary containing action results
    """
    if action == "create":
        if not executor_config:
            return {
                "action": "create",
                "error": "executor_config is required for create action",
                "message": "Error: Please provide executor_config parameter with the executor configuration.",
            }

        # Validate executor type is present
        if "type" not in executor_config:
            return {
                "action": "create",
                "error": "executor_config must include 'type' field",
                "message": "Error: executor_config must include 'type' field specifying the executor type.",
            }

        result = await client.executors.create_executor(
            executor_config=executor_config,
            account_name=account_name,
        )

        return {
            "action": "create",
            "result": result,
            "message": f"Executor created successfully: {result}",
        }

    elif action == "stop":
        if not executor_id:
            return {
                "action": "stop",
                "error": "executor_id is required for stop action",
                "message": "Error: Please provide executor_id parameter.",
            }

        result = await client.executors.stop_executor(
            executor_id=executor_id,
            keep_position=keep_position,
        )

        position_msg = " (position kept)" if keep_position else " (position closed)"
        return {
            "action": "stop",
            "executor_id": executor_id,
            "keep_position": keep_position,
            "result": result,
            "message": f"Executor {executor_id} stopped{position_msg}: {result}",
        }

    elif action == "delete":
        if not executor_id:
            return {
                "action": "delete",
                "error": "executor_id is required for delete action",
                "message": "Error: Please provide executor_id parameter.",
            }

        result = await client.executors.delete_executor(executor_id)

        return {
            "action": "delete",
            "executor_id": executor_id,
            "result": result,
            "message": f"Executor {executor_id} deleted: {result}",
        }

    else:
        return {
            "action": action,
            "error": f"Invalid action: {action}",
            "message": f"Error: Invalid action '{action}'. Use 'create', 'stop', or 'delete'.",
        }


async def manage_position_holds(
    client: Any,
    action: Literal["get_summary", "get_position", "clear_position"],
    connector_name: str | None = None,
    trading_pair: str | None = None,
    account_name: str | None = None,
) -> dict[str, Any]:
    """
    Manage executor position holds.

    Position holds track the aggregate position state across executors for a given
    connector/trading pair. This is useful for understanding overall exposure.

    Args:
        client: Hummingbot API client
        action: Action to perform
        connector_name: Connector name (required for get_position, clear_position)
        trading_pair: Trading pair (required for get_position, clear_position)
        account_name: Account name (optional)

    Returns:
        Dictionary containing position hold information
    """
    if action == "get_summary":
        summary = await client.executors.get_positions_summary()

        result = "Position Holds Summary:\n\n"

        if isinstance(summary, dict):
            positions = summary.get("data", summary.get("positions", [summary]))
            if isinstance(positions, list):
                if not positions:
                    result += "No active position holds."
                else:
                    result += "Connector        | Pair         | Side | Amount      | Breakeven   | uPnL\n"
                    result += "-" * 80 + "\n"
                    for pos in positions:
                        conn = str(pos.get("connector_name", ""))[:16]
                        pair = str(pos.get("trading_pair", ""))[:12]
                        side = str(pos.get("side", ""))[:4]
                        amount = f"{float(pos.get('amount', 0)):.4f}"[:11]
                        breakeven = f"{float(pos.get('breakeven_price', 0)):.2f}"[:11]
                        upnl = f"{float(pos.get('unrealized_pnl_quote', 0)):.2f}"
                        result += f"{conn:16} | {pair:12} | {side:4} | {amount:11} | {breakeven:11} | {upnl}\n"
            else:
                for key, value in (positions if isinstance(positions, dict) else {}).items():
                    result += f"{key}: {value}\n"
        else:
            result += str(summary)

        return {
            "action": "get_summary",
            "summary": summary,
            "formatted_output": result,
        }

    elif action == "get_position":
        if not connector_name or not trading_pair:
            return {
                "action": "get_position",
                "error": "connector_name and trading_pair are required",
                "formatted_output": "Error: Please provide connector_name and trading_pair parameters.",
            }

        position = await client.executors.get_position_held(
            connector_name=connector_name,
            trading_pair=trading_pair,
            account_name=account_name,
        )

        result = f"Position Hold for {connector_name} {trading_pair}:\n\n"

        if isinstance(position, dict):
            result += f"Side: {position.get('side', 'N/A')}\n"
            result += f"Amount: {position.get('amount', 0)}\n"
            result += f"Breakeven Price: {position.get('breakeven_price', 0)}\n"
            result += f"Unrealized PnL: {position.get('unrealized_pnl_quote', 0)}\n"
            result += f"Realized PnL: {position.get('realized_pnl_quote', 0)}\n"
            result += f"Volume Traded: {position.get('volume_traded_quote', 0)}\n"
            result += f"Cumulative Fees: {position.get('cum_fees_quote', 0)}\n"
        else:
            result += str(position)

        return {
            "action": "get_position",
            "connector_name": connector_name,
            "trading_pair": trading_pair,
            "position": position,
            "formatted_output": result,
        }

    elif action == "clear_position":
        if not connector_name or not trading_pair:
            return {
                "action": "clear_position",
                "error": "connector_name and trading_pair are required",
                "formatted_output": "Error: Please provide connector_name and trading_pair parameters.",
            }

        result = await client.executors.clear_position_held(
            connector_name=connector_name,
            trading_pair=trading_pair,
            account_name=account_name,
        )

        return {
            "action": "clear_position",
            "connector_name": connector_name,
            "trading_pair": trading_pair,
            "result": result,
            "formatted_output": f"Position hold cleared for {connector_name} {trading_pair}: {result}",
        }

    else:
        return {
            "action": action,
            "error": f"Invalid action: {action}",
            "formatted_output": f"Error: Invalid action '{action}'. Use 'get_summary', 'get_position', or 'clear_position'.",
        }
