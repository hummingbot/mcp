"""
Trading-related formatters for orders and positions.

This module provides table formatters for trading data including
orders and positions.
"""
from typing import Any

from .base import format_number, format_timestamp, format_table_separator


def format_orders_as_table(orders: list[dict[str, Any]]) -> str:
    """
    Format orders as a table string for better LLM processing.

    Columns: time | pair | side | type | amount | price | filled | status

    Args:
        orders: List of order dictionaries

    Returns:
        Formatted table string
    """
    if not orders:
        return "No orders found."

    # Header
    header = "time        | pair          | side | type   | amount   | price    | filled   | status"
    separator = format_table_separator()

    # Format each order as a row
    rows = []
    for order in orders:
        time_str = format_timestamp(
            order.get("created_at") or order.get("creation_timestamp") or order.get("timestamp", 0)
        )
        pair = (order.get("trading_pair") or "N/A")[:12]
        side = (order.get("trade_type") or order.get("side") or "N/A")[:4]
        order_type = (order.get("order_type") or order.get("type") or "N/A")[:6]
        amount = format_number(order.get("amount") or order.get("order_size"), compact=False)
        price = format_number(order.get("price"), compact=False)
        filled = format_number(
            order.get("filled_amount") or order.get("executed_amount_base"), compact=False
        )
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

    Args:
        positions: List of position dictionaries

    Returns:
        Formatted table string
    """
    if not positions:
        return "No positions found."

    # Header
    header = "pair          | side  | amount   | entry_price | current_price | unrealized_pnl | leverage"
    separator = format_table_separator()

    # Format each position as a row
    rows = []
    for position in positions:
        pair = (position.get("trading_pair") or "N/A")[:12]
        side = (position.get("position_side") or position.get("side") or "N/A")[:5]
        amount = format_number(
            position.get("amount") or position.get("position_size"), compact=False
        )
        entry_price = format_number(position.get("entry_price"), compact=False)
        current_price = format_number(
            position.get("current_price") or position.get("mark_price"), compact=False
        )
        unrealized_pnl = format_number(position.get("unrealized_pnl"), compact=False)
        leverage = position.get("leverage") or "N/A"

        row = f"{pair:13} | {side:5} | {amount:8} | {entry_price:11} | {current_price:13} | {unrealized_pnl:14} | {leverage}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table
