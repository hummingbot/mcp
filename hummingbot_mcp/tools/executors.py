"""
Executor management tools for Hummingbot MCP Server.

This module provides business logic for managing trading executors including
creation, viewing, stopping, and position management with progressive disclosure.
"""
import logging
from typing import Any

from hummingbot_mcp.executor_preferences import executor_preferences
from hummingbot_mcp.formatters.executors import (
    format_executor_detail,
    format_executor_schema_table,
    format_executor_summary,
    format_executors_table,
    format_positions_held_table,
    format_positions_summary,
)
from hummingbot_mcp.schemas import ManageExecutorsRequest

logger = logging.getLogger("hummingbot-mcp")

# Executor type descriptions for helping users choose the right executor
EXECUTOR_TYPE_DESCRIPTIONS = {
    "position_executor": {
        "name": "position_executor",
        "description": "Takes directional positions with defined entry, stop-loss, and take-profit levels",
        "use_when": "Clear directional view, want automated SL/TP, defined risk/reward",
        "avoid_when": "Want to provide liquidity, need multi-leg strategies",
    },
    "dca_executor": {
        "name": "dca_executor",
        "description": "Dollar-cost averages into positions over time with scheduled purchases",
        "use_when": "Accumulating gradually, reducing timing risk, building long-term position",
        "avoid_when": "Need immediate full entry, want quick exits",
    },
    "grid_executor": {
        "name": "grid_executor",
        "description": "Trades in ranging markets with multiple buy/sell levels in a grid pattern",
        "use_when": "Range-bound market, profit from volatility, want auto-rebalancing",
        "avoid_when": "Strongly trending market, limited capital for spread across levels",
        "notes": """
**Direction Rules:**
- LONG grid:  limit_price < start_price < end_price (limit below grid, buys low)
- SHORT grid: start_price < end_price < limit_price (limit above grid, sells high)
- side must be explicitly set: 1=BUY (LONG), 2=SELL (SHORT)

**Example (BTC at $85,000):**
- LONG grid to buy dips: start=82000, end=84000, limit=81000, side=1
- SHORT grid to sell rallies: start=86000, end=88000, limit=89000, side=2

**Risk Management (NO stop_loss):**
- `limit_price` is the safety boundary — when price crosses it, the grid stops.
- `keep_position=false`: closes position on stop (stop-loss-like exit).
- `keep_position=true`: holds position on stop (wait for recovery).
- Never suggest or expose `stop_loss` — `limit_price` + `keep_position` is the only risk mechanism.

For full parameter docs and behavioral explanations, see your preferences file via `get_preferences`.""",
    },
    "order_executor": {
        "name": "order_executor",
        "description": "Simple order execution with retry logic and multiple execution strategies. "
                       "Closest executor to a plain BUY/SELL order but with strategy options.",
        "use_when": "Want to place a single buy or sell order with a specific execution strategy "
                    "(LIMIT, MARKET, LIMIT_MAKER, or LIMIT_CHASER). Best for one-off acquisitions "
                    "or liquidations with reliable execution.",
        "avoid_when": "Need complex multi-level strategies (use grid/dca instead), "
                      "want automated SL/TP management (use position_executor instead)",
        "notes": """
**Execution Strategies:**
- MARKET: Immediate execution at current market price
- LIMIT: Place a limit order at a specified price
- LIMIT_MAKER: Post-only limit order (rejected if it would match immediately)
- LIMIT_CHASER: Continuously chases the best price, refreshing the limit order as the market moves

**LIMIT_CHASER Config (chaser_config):**
- distance: How far from best price to place the order (e.g., 0.001 = 0.1%)
- refresh_threshold: How far price must move before refreshing the order (e.g., 0.0005 = 0.05%)

**Key Parameters:**
- connector_name: Exchange to execute on
- trading_pair: Trading pair (e.g., 'USDT-BRL')
- side: 1 (BUY) or 2 (SELL)
- amount: Order amount (base currency, or '$100' for USD value)
- execution_strategy: LIMIT, MARKET, LIMIT_MAKER, or LIMIT_CHASER
- price: Required for LIMIT/LIMIT_MAKER strategies
- chaser_config: Required for LIMIT_CHASER strategy""",
    },
}


async def manage_executors(client: Any, request: ManageExecutorsRequest) -> dict[str, Any]:
    """
    Manage executors with progressive disclosure.

    Args:
        client: Hummingbot API client
        request: ManageExecutorsRequest with action and parameters

    Returns:
        Dictionary containing results and formatted output
    """
    flow_stage = request.get_flow_stage()

    if flow_stage == "list_types":
        # Brief static response — full descriptions are in the tool docstring
        formatted = (
            "Available Executor Types:\n\n"
            "- **position_executor** — Directional trading with entry, stop-loss, and take-profit\n"
            "- **dca_executor** — Dollar-cost averaging for gradual position building\n"
            "- **grid_executor** — Grid trading across multiple price levels in ranging markets\n"
            "- **order_executor** — Simple BUY/SELL order with execution strategy\n\n"
            "Provide `executor_type` to see the configuration schema."
        )

        return {
            "action": "list_types",
            "formatted_output": formatted,
            "next_step": "Call again with 'executor_type' to see the configuration schema",
            "example": "manage_executors(executor_type='position_executor')",
        }

    elif flow_stage == "show_schema":
        # Stage 2: Show config schema with user defaults
        try:
            schema = await client.executors.get_executor_config_schema(request.executor_type)
        except Exception as e:
            return {
                "action": "show_schema",
                "error": f"Failed to get schema for {request.executor_type}: {e}",
                "formatted_output": f"Error: Failed to get schema for {request.executor_type}: {e}",
            }

        # Get user defaults
        user_defaults = executor_preferences.get_defaults(request.executor_type)

        # Get type description
        type_info = EXECUTOR_TYPE_DESCRIPTIONS.get(request.executor_type, {})

        # Get the rich guide from the preferences file (if available)
        executor_guide = executor_preferences.get_executor_guide(request.executor_type)

        formatted = f"Configuration Schema for {request.executor_type}\n\n"
        if executor_guide:
            # Use the rich guide from preferences — it has full behavioral docs
            formatted += f"{executor_guide}\n\n"
        elif type_info:
            # Fallback to the condensed description
            formatted += f"{type_info.get('description', '')}\n"
            formatted += f"Use when: {type_info.get('use_when', '')}\n"
            formatted += f"Avoid when: {type_info.get('avoid_when', '')}\n"
            if type_info.get("notes"):
                formatted += f"\n{type_info.get('notes')}\n"
            formatted += "\n"

        formatted += format_executor_schema_table(schema, user_defaults)

        if user_defaults:
            formatted += f"\n\nYour saved defaults for {request.executor_type}:\n"
            for key, value in user_defaults.items():
                formatted += f"  {key}: {value}\n"
            formatted += f"\nPreferences file: {executor_preferences.get_preferences_path()}"

        return {
            "action": "show_schema",
            "executor_type": request.executor_type,
            "schema": schema,
            "user_defaults": user_defaults,
            "type_info": type_info,
            "formatted_output": formatted,
            "next_step": "Call with action='create' and executor_config to create an executor",
            "example": f"manage_executors(action='create', executor_type='{request.executor_type}', executor_config={{...}})",
        }

    elif flow_stage == "create":
        # Stage 3: Create executor
        executor_type = request.executor_type or request.executor_config.get("type") or request.executor_config.get("executor_type")

        if not executor_type:
            return {
                "action": "create",
                "error": "executor_type is required for creating an executor",
                "formatted_output": "Error: Please provide executor_type",
            }

        # Merge with defaults
        merged_config = executor_preferences.merge_with_defaults(executor_type, request.executor_config)

        # Ensure type is set in config
        if "type" not in merged_config and "executor_type" not in merged_config:
            merged_config["type"] = executor_type

        account = request.account_name or "master_account"

        try:
            result = await client.executors.create_executor(
                executor_config=merged_config,
                account_name=account,
            )

            # Save as default if requested
            if request.save_as_default:
                executor_preferences.update_defaults(executor_type, request.executor_config)

            formatted = f"Executor created successfully!\n\n"
            formatted += f"Executor ID: {result.get('id', 'N/A')}\n"
            formatted += f"Type: {executor_type}\n"
            formatted += f"Account: {account}\n"

            if request.save_as_default:
                formatted += f"\nConfiguration saved as default for {executor_type}"

            return {
                "action": "create",
                "executor_id": result.get("id"),
                "executor_type": executor_type,
                "account": account,
                "config_used": merged_config,
                "saved_as_default": request.save_as_default,
                "result": result,
                "formatted_output": formatted,
            }

        except Exception as e:
            return {
                "action": "create",
                "error": str(e),
                "formatted_output": f"Error creating executor: {e}",
            }

    elif flow_stage == "search":
        # Stage 4: Search executors
        try:
            result = await client.executors.search_executors(
                account_names=request.account_names,
                connector_names=request.connector_names,
                trading_pairs=request.trading_pairs,
                executor_types=request.executor_types,
                status=request.status,
                cursor=request.cursor,
                limit=request.limit,
            )

            executors = result.get("data", result) if isinstance(result, dict) else result
            if not isinstance(executors, list):
                executors = [executors] if executors else []

            formatted = f"Executors Found: {len(executors)}\n\n"
            formatted += format_executors_table(executors)

            # Add pagination info if available
            if isinstance(result, dict) and "next_cursor" in result:
                formatted += f"\n\nNext cursor: {result.get('next_cursor')}"

            return {
                "action": "search",
                "executors": executors,
                "count": len(executors),
                "cursor": result.get("next_cursor") if isinstance(result, dict) else None,
                "formatted_output": formatted,
            }

        except Exception as e:
            return {
                "action": "search",
                "error": str(e),
                "formatted_output": f"Error searching executors: {e}",
            }

    elif flow_stage == "get":
        # Stage 5: Get specific executor
        try:
            result = await client.executors.get_executor(request.executor_id)

            formatted = format_executor_detail(result)

            return {
                "action": "get",
                "executor_id": request.executor_id,
                "executor": result,
                "formatted_output": formatted,
            }

        except Exception as e:
            return {
                "action": "get",
                "error": str(e),
                "formatted_output": f"Error getting executor {request.executor_id}: {e}",
            }

    elif flow_stage == "stop":
        # Stage 6: Stop executor
        try:
            result = await client.executors.stop_executor(
                executor_id=request.executor_id,
                keep_position=request.keep_position,
            )

            formatted = f"Executor stopped successfully!\n\n"
            formatted += f"Executor ID: {request.executor_id}\n"
            formatted += f"Keep Position: {request.keep_position}\n"

            return {
                "action": "stop",
                "executor_id": request.executor_id,
                "keep_position": request.keep_position,
                "result": result,
                "formatted_output": formatted,
            }

        except Exception as e:
            return {
                "action": "stop",
                "error": str(e),
                "formatted_output": f"Error stopping executor {request.executor_id}: {e}",
            }

    elif flow_stage == "get_summary":
        # Stage 7: Get overall summary with positions and recent executors
        try:
            result = await client.executors.get_summary()

            formatted = format_executor_summary(result)

            # Fetch positions held
            positions = []
            try:
                positions_result = await client.executors.get_positions_summary()
                positions = positions_result.get("positions", positions_result) if isinstance(positions_result, dict) else positions_result
                if not isinstance(positions, list):
                    positions = [positions] if positions else []

                if positions:
                    formatted += "\n\nPositions Held:\n"
                    formatted += format_positions_held_table(positions)
            except Exception:
                # If fetching positions fails, continue without them
                pass

            # Also fetch last 10 executors to show recent activity
            recent_executors = []
            try:
                recent_result = await client.executors.search_executors(limit=10)
                recent_executors = recent_result.get("data", recent_result) if isinstance(recent_result, dict) else recent_result
                if not isinstance(recent_executors, list):
                    recent_executors = [recent_executors] if recent_executors else []

                if recent_executors:
                    formatted += "\n\nRecent Executors (last 10):\n"
                    formatted += format_executors_table(recent_executors)
            except Exception:
                # If fetching recent executors fails, just show the summary
                pass

            return {
                "action": "get_summary",
                "summary": result,
                "positions": positions,
                "recent_executors": recent_executors,
                "formatted_output": formatted,
            }

        except Exception as e:
            return {
                "action": "get_summary",
                "error": str(e),
                "formatted_output": f"Error getting executor summary: {e}",
            }

    elif flow_stage == "get_preferences":
        # Stage 8: Get saved preferences (returns raw markdown content)
        raw_content = executor_preferences.get_raw_content()

        formatted = f"Preferences file: {executor_preferences.get_preferences_path()}\n\n"

        # Check if documentation is outdated
        if executor_preferences.needs_documentation_update():
            formatted += (
                "**Note:** Your preferences file has outdated documentation. "
                "Run `reset_preferences` to get updated docs — your YAML configs will be preserved.\n\n"
            )

        formatted += raw_content

        return {
            "action": "get_preferences",
            "executor_type": request.executor_type,
            "raw_content": raw_content,
            "preferences_path": executor_preferences.get_preferences_path(),
            "needs_update": executor_preferences.needs_documentation_update(),
            "formatted_output": formatted,
        }

    elif flow_stage == "save_preferences":
        # Stage 9: Save full preferences file content
        executor_preferences.save_content(request.preferences_content)

        formatted = f"Preferences file saved successfully.\n\n"
        formatted += f"Preferences file: {executor_preferences.get_preferences_path()}"

        return {
            "action": "save_preferences",
            "preferences_path": executor_preferences.get_preferences_path(),
            "formatted_output": formatted,
        }

    elif flow_stage == "reset_preferences":
        # Stage 10: Reset preferences to defaults (preserves YAML configs)
        preserved = executor_preferences.reset_to_defaults()
        preserved_count = sum(1 for c in preserved.values() if c)

        formatted = "Preferences documentation updated to latest version.\n\n"
        if preserved_count > 0:
            preserved_names = [k for k, v in preserved.items() if v]
            formatted += f"Preserved {preserved_count} config(s): {', '.join(preserved_names)}\n"
        else:
            formatted += "No existing configs to preserve.\n"
        formatted += f"\nPreferences file: {executor_preferences.get_preferences_path()}"

        return {
            "action": "reset_preferences",
            "preserved_configs": preserved,
            "preserved_count": preserved_count,
            "formatted_output": formatted,
        }

    # Position management stages (merged from manage_executor_positions)

    elif flow_stage == "positions_summary":
        # Get positions summary (aggregated view)
        try:
            result = await client.executors.get_positions_summary()

            positions = result.get("positions", result) if isinstance(result, dict) else result
            if not isinstance(positions, list):
                positions = [positions] if positions else []

            formatted = f"Positions Held Summary\n\n"

            if isinstance(result, dict) and any(k in result for k in ["total_positions", "total_value", "by_connector"]):
                formatted += format_positions_summary(result)
                if positions:
                    formatted += "\n\nPositions Detail:\n"
                    formatted += format_positions_held_table(positions)
            else:
                formatted += format_positions_held_table(positions)

            return {
                "action": "positions_summary",
                "positions": positions,
                "summary": result if isinstance(result, dict) else {"positions": positions},
                "formatted_output": formatted,
                "next_step": "Call with action='get_position', connector_name and trading_pair to see specific position details",
            }

        except Exception as e:
            return {
                "action": "positions_summary",
                "error": str(e),
                "formatted_output": f"Error getting positions summary: {e}",
            }

    elif flow_stage == "get_position":
        # Get specific position details
        account = request.account_name or "master_account"
        try:
            result = await client.executors.get_position_held(
                connector_name=request.connector_name,
                trading_pair=request.trading_pair,
                account_name=account,
            )

            formatted = f"Position Details\n\n"
            formatted += f"Connector: {request.connector_name}\n"
            formatted += f"Trading Pair: {request.trading_pair}\n"
            formatted += f"Account: {account}\n\n"

            if result:
                positions = [result] if not isinstance(result, list) else result
                formatted += format_positions_held_table(positions)
            else:
                formatted += "No position found for this connector/pair combination."

            return {
                "action": "get_position",
                "connector_name": request.connector_name,
                "trading_pair": request.trading_pair,
                "account": account,
                "position": result,
                "formatted_output": formatted,
                "next_step": "Use action='clear_position' if you need to clear this position",
            }

        except Exception as e:
            return {
                "action": "get_position",
                "error": str(e),
                "formatted_output": f"Error getting position: {e}",
            }

    elif flow_stage == "clear_position":
        # Clear a position that was closed manually
        account = request.account_name or "master_account"
        try:
            result = await client.executors.clear_position_held(
                connector_name=request.connector_name,
                trading_pair=request.trading_pair,
                account_name=account,
            )

            formatted = f"Position cleared successfully!\n\n"
            formatted += f"Connector: {request.connector_name}\n"
            formatted += f"Trading Pair: {request.trading_pair}\n"
            formatted += f"Account: {account}\n"

            return {
                "action": "clear_position",
                "connector_name": request.connector_name,
                "trading_pair": request.trading_pair,
                "account": account,
                "result": result,
                "formatted_output": formatted,
            }

        except Exception as e:
            return {
                "action": "clear_position",
                "error": str(e),
                "formatted_output": f"Error clearing position: {e}",
            }

    else:
        return {
            "action": "unknown",
            "error": f"Unknown flow stage: {flow_stage}",
            "formatted_output": f"Error: Unknown flow stage: {flow_stage}",
        }
