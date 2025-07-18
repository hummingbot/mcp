"""
Input validation utilities for Hummingbot MCP Server
"""

import re
from typing import Tuple, Union
from ..exceptions import ValidationError


def validate_trading_pair(trading_pair: str) -> str:
    """Validate and normalize trading pair format"""
    if not trading_pair:
        raise ValidationError("Trading pair cannot be empty")
    
    # Normalize to uppercase and ensure proper format
    trading_pair = trading_pair.upper().replace("/", "-").replace("_", "-")
    
    # Basic validation for trading pair format
    if not re.match(r'^[A-Z0-9]+-[A-Z0-9]+$', trading_pair):
        raise ValidationError(f"Invalid trading pair format: {trading_pair}")
    
    return trading_pair


def validate_amount(amount: Union[str, float]) -> float:
    """Validate that amount is a positive number"""
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            raise ValidationError("Amount must be positive")
        return amount_float
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid amount: {amount}")


def parse_amount(amount_str: str) -> Tuple[float, bool]:
    """
    Parse amount string and determine if it's USD or base currency
    
    Returns:
        Tuple of (amount, is_usd)
    """
    if not amount_str:
        raise ValidationError("Amount cannot be empty")
    
    amount_str = str(amount_str).strip()
    
    # Check if it's USD notation
    if amount_str.startswith("$"):
        try:
            usd_amount = float(amount_str[1:])
            if usd_amount <= 0:
                raise ValidationError("USD amount must be positive")
            return usd_amount, True
        except ValueError:
            raise ValidationError(f"Invalid USD amount: {amount_str}")
    else:
        # Base currency amount
        try:
            base_amount = float(amount_str)
            if base_amount <= 0:
                raise ValidationError("Amount must be positive")
            return base_amount, False
        except ValueError:
            raise ValidationError(f"Invalid amount: {amount_str}")


def validate_order_type(order_type: str) -> str:
    """Validate order type"""
    valid_types = ["MARKET", "LIMIT", "LIMIT_MAKER"]
    order_type = order_type.upper()
    
    if order_type not in valid_types:
        raise ValidationError(f"Invalid order type: {order_type}. Must be one of: {valid_types}")
    
    return order_type


def validate_order_side(side: str) -> str:
    """Validate order side"""
    valid_sides = ["BUY", "SELL"]
    side = side.upper()
    
    if side not in valid_sides:
        raise ValidationError(f"Invalid order side: {side}. Must be one of: {valid_sides}")
    
    return side