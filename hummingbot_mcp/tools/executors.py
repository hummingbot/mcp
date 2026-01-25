"""
Executor Tools - Primary trading interface for Hummingbot MCP.

Executors are smart trading algorithms that handle order placement,
position management, and risk controls automatically.

Executor Types:
- position_executor: Single position with stop loss, take profit, time limit
- grid_executor: Grid trading with multiple buy/sell levels
- dca_executor: Dollar-cost averaging with multiple entry points
- twap_executor: Time-weighted average price execution
- arbitrage_executor: Cross-exchange price arbitrage
- xemm_executor: Cross-exchange market making
"""

from typing import Any


# ========================================
# Executor API Operations
# ========================================

async def create_executor(
    client: Any,
    executor_config: dict[str, Any],
    account_name: str | None = None
) -> dict[str, Any]:
    """
    Create and start a new executor.

    Args:
        client: Hummingbot API client
        executor_config: Executor configuration with 'type' and type-specific params
        account_name: Account to run executor on

    Returns:
        Created executor information
    """
    return await client.executors.create_executor(
        executor_config=executor_config,
        account_name=account_name
    )


async def search_executors(
    client: Any,
    executor_ids: list[str] | None = None,
    executor_types: list[str] | None = None,
    statuses: list[str] | None = None,
    is_active: bool | None = None,
    trading_pair: str | None = None,
    connector_name: str | None = None,
    account_name: str | None = None,
    side: str | None = None
) -> dict[str, Any]:
    """
    Search for executors with filters.

    Args:
        client: Hummingbot API client
        executor_ids: Filter by specific executor IDs
        executor_types: Filter by executor types
        statuses: Filter by statuses
        is_active: Filter by active status
        trading_pair: Filter by trading pair
        connector_name: Filter by connector
        account_name: Filter by account
        side: Filter by side (buy/sell)

    Returns:
        List of matching executors
    """
    return await client.executors.search_executors(
        executor_ids=executor_ids,
        executor_types=executor_types,
        statuses=statuses,
        is_active=is_active,
        trading_pair=trading_pair,
        connector_name=connector_name,
        account_name=account_name,
        side=side
    )


async def get_executor(client: Any, executor_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific executor.

    Args:
        client: Hummingbot API client
        executor_id: The executor ID

    Returns:
        Executor details
    """
    return await client.executors.get_executor(executor_id)


async def stop_executor(
    client: Any,
    executor_id: str,
    keep_position: bool = False
) -> dict[str, Any]:
    """
    Stop a running executor.

    Args:
        client: Hummingbot API client
        executor_id: The executor ID to stop
        keep_position: If True, keep position open after stopping

    Returns:
        Stop operation result
    """
    return await client.executors.stop_executor(
        executor_id=executor_id,
        keep_position=keep_position
    )


async def delete_executor(client: Any, executor_id: str) -> dict[str, Any]:
    """
    Delete an executor from tracking.

    Args:
        client: Hummingbot API client
        executor_id: The executor ID to delete

    Returns:
        Delete operation result
    """
    return await client.executors.delete_executor(executor_id)


async def get_executors_summary(client: Any) -> dict[str, Any]:
    """
    Get summary statistics for all executors.

    Args:
        client: Hummingbot API client

    Returns:
        Summary statistics
    """
    return await client.executors.get_summary()


async def get_available_executor_types(client: Any) -> list[str]:
    """
    Get list of available executor types.

    Args:
        client: Hummingbot API client

    Returns:
        List of executor type names
    """
    return await client.executors.get_available_executor_types()


async def get_executor_config_schema(client: Any, executor_type: str) -> dict[str, Any]:
    """
    Get configuration schema for a specific executor type.

    Args:
        client: Hummingbot API client
        executor_type: The executor type

    Returns:
        Configuration schema
    """
    return await client.executors.get_executor_config_schema(executor_type)


async def get_positions_summary(client: Any) -> dict[str, Any]:
    """
    Get summary of all positions held by executors.

    Args:
        client: Hummingbot API client

    Returns:
        Positions summary
    """
    return await client.executors.get_positions_summary()


# ========================================
# Formatting Helpers
# ========================================

def format_executor_summary(executor: dict[str, Any]) -> str:
    """Format a single executor for display."""
    status_emoji = "🟢" if executor.get("is_active") else "⚫"
    pnl = executor.get("net_pnl_quote", 0) or 0
    pnl_pct = executor.get("net_pnl_pct", 0) or 0
    pnl_emoji = "📈" if pnl >= 0 else "📉"

    exec_id = executor.get('id', executor.get('executor_id', 'N/A'))
    exec_id_short = exec_id[:12] + "..." if len(str(exec_id)) > 12 else exec_id

    return (
        f"{status_emoji} {exec_id_short} | "
        f"{executor.get('type', executor.get('executor_type', 'unknown'))} | "
        f"{executor.get('connector_name', 'N/A')}/{executor.get('trading_pair', 'N/A')} | "
        f"{executor.get('side', 'N/A')} | "
        f"{pnl_emoji} ${pnl:+.2f} ({pnl_pct:+.2f}%)"
    )


def format_executor_detail(executor: dict[str, Any]) -> str:
    """Format detailed executor information."""
    exec_id = executor.get('id', executor.get('executor_id', 'N/A'))
    exec_type = executor.get('type', executor.get('executor_type', 'unknown'))
    status = executor.get('status', 'unknown')
    is_active = executor.get('is_active', False)

    lines = [
        f"Executor: {exec_id}",
        f"{'=' * 60}",
        f"Type: {exec_type}",
        f"Status: {status} {'(Active)' if is_active else '(Stopped)'}",
        f"Account: {executor.get('account_name', 'N/A')}",
        f"Connector: {executor.get('connector_name', 'N/A')}",
        f"Trading Pair: {executor.get('trading_pair', 'N/A')}",
        f"Side: {executor.get('side', 'N/A')}",
        "",
        "Performance:",
        f"  Net PnL: ${executor.get('net_pnl_quote', 0) or 0:.2f} ({executor.get('net_pnl_pct', 0) or 0:.2f}%)",
        f"  Fees: ${executor.get('cum_fees_quote', 0) or 0:.2f}",
        f"  Volume: ${executor.get('filled_amount_quote', 0) or 0:.2f}",
    ]

    config = executor.get('config') or executor.get('executor_config')
    if config:
        lines.extend(["", "Configuration:"])
        for key, value in config.items():
            if not key.startswith('_') and key != 'type':
                lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def format_executors_table(executors: list[dict[str, Any]], title: str = "Executors") -> str:
    """Format multiple executors as a table."""
    if not executors:
        return "No executors found."

    lines = [
        f"{title}:",
        "=" * 80,
    ]

    for ex in executors:
        lines.append(format_executor_summary(ex))

    lines.append("=" * 80)
    lines.append(f"Total: {len(executors)} executor(s)")

    return "\n".join(lines)


def format_executor_types(types_info: list[dict[str, Any]]) -> str:
    """Format executor types information."""
    lines = ["Available Executor Types:", "=" * 60]

    for info in types_info:
        lines.extend([
            f"\n📦 {info.get('type', 'unknown')}",
            f"   {info.get('description', 'No description')}",
            f"   Use case: {info.get('use_case', 'General trading')}",
        ])

    return "\n".join(lines)


def format_executors_summary_stats(summary: dict[str, Any]) -> str:
    """Format executor summary statistics."""
    lines = [
        "Executors Summary",
        "=" * 60,
        f"Active: {summary.get('total_active', 0)}",
        f"Completed: {summary.get('total_completed', 0)}",
        f"Total PnL: ${summary.get('total_pnl_quote', 0):.2f}",
        f"Total Volume: ${summary.get('total_volume_quote', 0):.2f}",
    ]

    by_type = summary.get('by_type', {})
    if by_type:
        lines.extend(["", "By Type:"])
        for t, count in by_type.items():
            lines.append(f"  {t}: {count}")

    by_status = summary.get('by_status', {})
    if by_status:
        lines.extend(["", "By Status:"])
        for s, count in by_status.items():
            lines.append(f"  {s}: {count}")

    return "\n".join(lines)
