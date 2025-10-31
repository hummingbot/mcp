"""
Market data formatters for prices, candles, and order books.

This module provides table formatters for market data including
prices, OHLCV candles, and order book snapshots.
"""
from typing import Any

from .base import format_currency, format_number, format_timestamp, format_table_separator


def format_prices_as_table(prices_data: dict[str, Any]) -> str:
    """
    Format prices data as a table string for better LLM processing.

    Columns: trading_pair | price

    Args:
        prices_data: Dictionary containing prices keyed by trading pair

    Returns:
        Formatted table string
    """
    prices = prices_data.get("prices", {})

    if not prices:
        return "No prices available."

    # Header
    header = "trading_pair      | price"
    separator = format_table_separator(50)

    # Format each price as a row
    rows = []
    for pair, price in prices.items():
        pair_str = pair[:16].ljust(16)
        price_str = format_currency(price, decimals=2 if price >= 1 else 6)
        row = f"{pair_str}  | {price_str}"
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


def format_candles_as_table(candles: list[dict[str, Any]]) -> str:
    """
    Format candle data as a table string for better LLM processing.

    Columns: time | open | high | low | close | volume

    Args:
        candles: List of OHLCV candle dictionaries

    Returns:
        Formatted table string
    """
    if not candles:
        return "No candles found."

    def format_price(price: Any) -> str:
        """Format price value"""
        try:
            return f"{float(price):.2f}"
        except (ValueError, TypeError):
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
        except (ValueError, TypeError):
            return "N/A"

    # Header
    header = "time        | open     | high     | low      | close    | volume"
    separator = format_table_separator(85)

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

    Args:
        order_book_data: Dictionary containing 'bids' and 'asks' lists

    Returns:
        Formatted table string
    """
    bids = order_book_data.get("bids", [])[:10]
    asks = order_book_data.get("asks", [])[:10]

    if not bids and not asks:
        return "No order book data available."

    # Header
    header = "BIDS                      |  ASKS"
    sub_header = "price      | amount       |  price      | amount"
    separator = format_table_separator(65)

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
