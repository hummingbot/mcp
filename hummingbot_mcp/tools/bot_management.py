"""
Bot management operations business logic.

This module provides the core business logic for managing bots, including
status retrieval, log management, and execution control.
"""
import asyncio
from typing import Any, Literal

from hummingbot_mcp.formatters import format_active_bots_as_table, format_bot_logs_as_table


async def get_active_bots_status(client: Any) -> dict[str, Any]:
    """
    Get the status of all active bots.

    Args:
        client: Hummingbot API client

    Returns:
        Dictionary containing active bots data and formatted table
    """
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

    return {
        "active_bots": active_bots,
        "bots_table": bots_table,
        "total_bots": total_bots,
    }


async def get_bot_logs(
    client: Any,
    bot_name: str,
    log_type: Literal["error", "general", "all"] = "all",
    limit: int = 50,
    search_term: str | None = None,
) -> dict[str, Any]:
    """
    Get detailed logs for a specific bot with filtering options.

    Args:
        client: Hummingbot API client
        bot_name: Name of the bot to get logs for
        log_type: Type of logs to retrieve ('error', 'general', or 'all')
        limit: Maximum number of log entries to return (default: 50, max: 1000)
        search_term: Optional search term to filter logs by message content

    Returns:
        Dictionary containing logs data and formatted table

    Raises:
        ValueError: If bot is not found
    """
    active_bots = await client.bot_orchestration.get_active_bots_status()

    if not isinstance(active_bots, dict) or "data" not in active_bots:
        return {
            "error": "No active bots data found",
            "message": "No active bots data found",
        }

    if bot_name not in active_bots["data"]:
        available_bots = list(active_bots["data"].keys())
        return {
            "error": f"Bot '{bot_name}' not found",
            "available_bots": available_bots,
            "message": f"Bot '{bot_name}' not found. Available bots: {available_bots}",
        }

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

    return {
        "bot_name": bot_name,
        "log_type": log_type,
        "search_term": search_term,
        "logs": logs,
        "logs_table": logs_table,
        "total_logs": len(logs),
    }


async def manage_bot_execution(
    client: Any,
    bot_name: str,
    action: Literal["stop_bot", "stop_controllers", "start_controllers"],
    controller_names: list[str] | None = None,
) -> dict[str, Any]:
    """
    Manage bot and controller execution states.

    Args:
        client: Hummingbot API client
        bot_name: Name of the bot to manage
        action: The action to perform
        controller_names: List of controller names (required for stop/start_controllers)

    Returns:
        Dictionary containing execution management results

    Raises:
        ValueError: If parameters are invalid
    """
    if action == "stop_bot":
        result = await client.bot_orchestration.stop_and_archive_bot(bot_name)
        return {
            "action": "stop_bot",
            "bot_name": bot_name,
            "result": result,
            "message": f"Bot execution stopped and archived: {result}",
        }

    elif action == "stop_controllers":
        if controller_names is None or len(controller_names) == 0:
            raise ValueError("controller_names is required for stop_controllers action")

        tasks = [
            client.controllers.update_bot_controller_config(bot_name, controller, {"manual_kill_switch": True})
            for controller in controller_names
        ]
        result = await asyncio.gather(*tasks)

        return {
            "action": "stop_controllers",
            "bot_name": bot_name,
            "controller_names": controller_names,
            "result": result,
            "message": f"Controllers stopped: {result}",
        }

    elif action == "start_controllers":
        if controller_names is None or len(controller_names) == 0:
            raise ValueError("controller_names is required for start_controllers action")

        tasks = [
            client.controllers.update_bot_controller_config(bot_name, controller, {"manual_kill_switch": False})
            for controller in controller_names
        ]
        result = await asyncio.gather(*tasks)

        return {
            "action": "start_controllers",
            "bot_name": bot_name,
            "controller_names": controller_names,
            "result": result,
            "message": f"Controllers started: {result}",
        }

    else:
        raise ValueError(f"Invalid action: {action}")
