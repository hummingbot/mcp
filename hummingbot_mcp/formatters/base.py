"""
Base formatting utilities shared across all formatters.

This module provides common formatting functions for numbers, timestamps,
percentages, and currency values used throughout the application.
"""
from datetime import datetime
from typing import Any


def format_number(num: Any, decimals: int = 2, compact: bool = True) -> str:
    """
    Format a number to be more compact and readable.

    Args:
        num: The number to format
        decimals: Number of decimal places (default: 2)
        compact: If True, uses K/M notation for large numbers (default: True)

    Returns:
        Formatted number string

    Examples:
        >>> format_number(1500)
        '1.50K'
        >>> format_number(0.001234, decimals=4)
        '0.0012'
        >>> format_number(None)
        'N/A'
    """
    if num is None or num == "N/A":
        return "N/A"

    try:
        num_float = float(num)

        # Handle compact notation for large numbers
        if compact and num_float >= 1000:
            if num_float >= 1_000_000:
                return f"{num_float/1_000_000:.{decimals}f}M"
            return f"{num_float/1000:.{decimals}f}K"

        # Handle very small numbers
        if abs(num_float) < 0.01 and num_float != 0:
            return f"{num_float:.{max(decimals, 4)}f}"

        return f"{num_float:.{decimals}f}"
    except (ValueError, TypeError):
        return str(num)


def format_timestamp(ts: Any, format_str: str = "%m/%d %H:%M") -> str:
    """
    Format a timestamp to readable datetime string.

    Args:
        ts: Unix timestamp (int/float) or ISO datetime string
        format_str: strftime format string (default: "%m/%d %H:%M")

    Returns:
        Formatted datetime string

    Examples:
        >>> format_timestamp(1234567890)
        '02/13 23:31'
        >>> format_timestamp("2023-01-01T12:00:00Z")
        '01/01 12:00'
    """
    try:
        if isinstance(ts, (int, float)):
            # Handle both seconds and milliseconds timestamps
            timestamp = ts / 1000 if ts > 1e12 else ts
            dt = datetime.fromtimestamp(timestamp)
        else:
            # Try parsing ISO format string
            dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))

        return dt.strftime(format_str)
    except (ValueError, OSError, OverflowError):
        return "N/A"


def format_time_only(ts: float) -> str:
    """
    Format a timestamp to time only (HH:MM:SS).

    Args:
        ts: Unix timestamp

    Returns:
        Formatted time string
    """
    return format_timestamp(ts, "%H:%M:%S")


def format_full_datetime(ts: Any) -> str:
    """
    Format a timestamp to full datetime (YYYY-MM-DD HH:MM:SS).

    Args:
        ts: Unix timestamp or datetime string

    Returns:
        Formatted datetime string
    """
    return format_timestamp(ts, "%Y-%m-%d %H:%M:%S")


def format_percentage(pct: Any, decimals: int = 2) -> str:
    """
    Format a decimal percentage to percentage string.

    Args:
        pct: Percentage as decimal (0.05 = 5%)
        decimals: Number of decimal places (default: 2)

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(0.05)
        '5.00%'
        >>> format_percentage(None)
        'N/A'
    """
    if pct is None or pct == "N/A":
        return "N/A"

    try:
        pct_float = float(pct) * 100
        return f"{pct_float:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(pct)


def format_currency(amount: Any, symbol: str = "$", decimals: int = 2) -> str:
    """
    Format a number as currency with symbol.

    Args:
        amount: The amount to format
        symbol: Currency symbol (default: "$")
        decimals: Number of decimal places (default: 2)

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(0.001234, decimals=6)
        '$0.001234'
    """
    if amount is None or amount == "N/A":
        return "N/A"

    try:
        amount_float = float(amount)

        # For large amounts, use comma separator
        if abs(amount_float) >= 1:
            return f"{symbol}{amount_float:,.{decimals}f}"

        # For small amounts, show more decimals
        return f"{symbol}{amount_float:.{max(decimals, 6)}f}"
    except (ValueError, TypeError):
        return str(amount)


def truncate_string(text: str, max_len: int = 80, suffix: str = "...") -> str:
    """
    Truncate a string if it exceeds max length.

    Args:
        text: The text to truncate
        max_len: Maximum length (default: 80)
        suffix: Suffix to add when truncated (default: "...")

    Returns:
        Truncated string

    Examples:
        >>> truncate_string("a" * 100, max_len=50)
        'aaaaaaaaaa...aaaaaaa' (47 chars + '...')
    """
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def truncate_address(address: str, prefix_len: int = 8, suffix_len: int = 6) -> str:
    """
    Truncate a blockchain address or hash to readable format.

    Args:
        address: The address to truncate
        prefix_len: Number of characters to show at start (default: 8)
        suffix_len: Number of characters to show at end (default: 6)

    Returns:
        Truncated address

    Examples:
        >>> truncate_address("0x1234567890abcdef1234567890abcdef12345678")
        '0x123456...345678'
    """
    if len(address) <= prefix_len + suffix_len + 3:
        return address
    return f"{address[:prefix_len]}...{address[-suffix_len:]}"


def format_table_separator(length: int = 120, char: str = "-") -> str:
    """
    Create a table separator line.

    Args:
        length: Length of the separator (default: 120)
        char: Character to use (default: "-")

    Returns:
        Separator string
    """
    return char * length
