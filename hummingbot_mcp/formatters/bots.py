"""
Bot-related formatters for logs and status information.

This module provides table formatters for bot logs and active bot status.
"""
from typing import Any

from .base import (
    format_number,
    format_percentage,
    format_table_separator,
    format_time_only,
    truncate_string,
)


def format_bot_logs_as_table(logs: list[dict[str, Any]]) -> str:
    """
    Format bot logs as a table string for better LLM processing.

    Columns: time | level | category | message

    Args:
        logs: List of log entry dictionaries

    Returns:
        Formatted table string
    """
    if not logs:
        return "No logs found."

    # Header
    header = "time     | level | category | message"
    separator = format_table_separator()

    # Format each log as a row
    rows = []
    for log_entry in logs:
        time_str = format_time_only(log_entry.get("timestamp", 0))
        level = log_entry.get("level_name", "INFO")[:4]  # Truncate to 4 chars (INFO, WARN, ERR)
        category = log_entry.get("log_category", "gen")[:3]  # gen or err
        message = truncate_string(log_entry.get("msg", ""))

        row = f"{time_str} | {level:4} | {category:3} | {message}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_active_bots_as_table(bots_data: dict[str, Any]) -> str:
    """
    Format active bots data as a table string for better LLM processing.

    Columns: bot_name | controller | status | realized_pnl | unrealized_pnl | global_pnl | volume | errors

    Args:
        bots_data: Dictionary containing bot data

    Returns:
        Formatted table string
    """
    if not bots_data or "data" not in bots_data or not bots_data["data"]:
        return "No active bots found."

    # Header
    header = "bot_name | controller | status | realized_pnl | unrealized_pnl | global_pnl | volume | errors | recent_logs"
    separator = format_table_separator()

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

                realized_pnl = format_number(ctrl_perf.get("realized_pnl_quote"), compact=False)
                unrealized_pnl = format_number(ctrl_perf.get("unrealized_pnl_quote"), compact=False)
                global_pnl = format_number(ctrl_perf.get("global_pnl_quote"), compact=False)
                global_pnl_pct = format_percentage(ctrl_perf.get("global_pnl_pct"))
                volume = format_number(ctrl_perf.get("volume_traded"), compact=False)

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
