"""
Market data operations business logic.

This module provides the core business logic for market data operations including
prices, candles, funding rates, and order books.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from hummingbot_mcp.formatters import (
    format_candles_as_table,
    format_order_book_as_table,
    format_prices_as_table,
)


class CandlesFeedRequest(BaseModel):
    """Request model for managing candle feeds with progressive disclosure.

    This model supports a multi-step flow:
    1. No parameters → Show settings, available connectors, and active feeds
    2. Connector only → Show active feeds for connector, prompt for trading pair
    3. Connector + trading_pair → Start feed with default interval (1h)
    4. All parameters → Start feed with specified interval and days
    """

    connector: str | None = Field(
        default=None,
        description="Exchange connector (e.g., 'binance_perpetual'). Leave empty to list available connectors.",
    )

    trading_pair: str | None = Field(
        default=None,
        description="Trading pair (e.g., 'BTC-USDT'). Required to start a feed.",
    )

    interval: str = Field(
        default="1h",
        description="Candle interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d (default: 1h)",
    )

    days: int = Field(
        default=30,
        description="Days of historical data to fetch (default: 30)",
        ge=1,
        le=365,
    )

    @field_validator("connector")
    @classmethod
    def validate_connector(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.lower().replace(" ", "_").replace("-", "_")
        return v

    @field_validator("trading_pair")
    @classmethod
    def validate_trading_pair(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.upper().replace("_", "-").replace("/", "-")
        return v

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        if v not in valid_intervals:
            raise ValueError(f"Invalid interval '{v}'. Valid: {valid_intervals}")
        return v

    def get_flow_stage(self) -> str:
        """Determine which stage of the setup flow we're in."""
        if self.connector is None:
            return "list_connectors"
        elif self.trading_pair is None:
            return "show_connector_feeds"
        else:
            return "start_feed"


async def manage_candles_feed(client: Any, request: CandlesFeedRequest) -> dict[str, Any]:
    """Manage candle feeds with progressive disclosure.

    Flow:
    1. No params → Settings + available connectors + active feeds
    2. Connector only → Active feeds for connector + prompt for trading pair
    3. Connector + trading_pair → Start/refresh feed
    """
    flow_stage = request.get_flow_stage()

    if flow_stage == "list_connectors":
        # Step 1: Show settings, available connectors, and all active feeds
        settings = await client.market_data.get_market_data_settings()
        connectors = await client.market_data.get_available_candle_connectors()
        active_feeds = await client.market_data.get_active_feeds()

        return {
            "action": "list_connectors",
            "settings": settings,
            "connectors": connectors,
            "active_feeds": active_feeds.get("active_feeds", {}),
            "total_connectors": len(connectors),
            "total_active_feeds": len(active_feeds.get("active_feeds", {})),
            "next_step": "Provide a connector to see its feeds or start a new one",
            "example": "candles_feed(connector='binance_perpetual')",
        }

    elif flow_stage == "show_connector_feeds":
        # Step 2: Show active feeds for this connector, prompt for trading pair
        active_feeds = await client.market_data.get_active_feeds()
        all_feeds = active_feeds.get("active_feeds", {})

        # Filter feeds for this connector
        connector_feeds = {
            k: v for k, v in all_feeds.items()
            if k.startswith(request.connector)
        }

        return {
            "action": "show_connector_feeds",
            "connector": request.connector,
            "active_feeds": connector_feeds,
            "total_feeds": len(connector_feeds),
            "next_step": "Provide a trading pair to start or refresh a feed",
            "example": f"candles_feed(connector='{request.connector}', trading_pair='BTC-USDT')",
            "intervals": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "default_interval": "1h",
            "default_days": 30,
        }

    else:
        # Step 3: Start/refresh the candle feed
        # Calculate max records based on interval
        interval = request.interval
        days = request.days

        if interval.endswith("m"):
            max_records = 1440 * days
        elif interval.endswith("h"):
            max_records = 24 * days
        elif interval.endswith("d"):
            max_records = days
        elif interval.endswith("w"):
            max_records = days // 7
        else:
            max_records = 24 * days  # Default to hourly

        # Adjust for interval multiplier
        interval_num = interval[:-1]
        if interval_num and interval_num.isdigit():
            max_records = max(1, int(max_records / int(interval_num)))

        # Start the feed
        candles = await client.market_data.get_candles(
            connector_name=request.connector,
            trading_pair=request.trading_pair,
            interval=interval,
            max_records=max_records,
        )

        # Get updated active feeds
        active_feeds = await client.market_data.get_active_feeds()

        return {
            "action": "feed_started",
            "connector": request.connector,
            "trading_pair": request.trading_pair,
            "interval": interval,
            "days": days,
            "candles": candles,
            "total_candles": len(candles),
            "active_feeds": active_feeds.get("active_feeds", {}),
            "feed_key": f"{request.connector}:{request.trading_pair}:{interval}",
        }


async def get_prices(
    client: Any, connector_name: str, trading_pairs: list[str]
) -> dict[str, Any]:
    """
    Get latest prices for trading pairs.

    Args:
        client: Hummingbot API client
        connector_name: Exchange connector name
        trading_pairs: List of trading pairs

    Returns:
        Dictionary containing prices data and formatted table
    """
    prices = await client.market_data.get_prices(
        connector_name=connector_name, trading_pairs=trading_pairs
    )

    # Format prices as table
    prices_table = format_prices_as_table(prices)

    timestamp = prices.get("timestamp", 0)
    time_str = (
        datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        if timestamp
        else "N/A"
    )

    return {
        "prices": prices,
        "prices_table": prices_table,
        "connector_name": connector_name,
        "timestamp": time_str,
    }


async def get_candles(
    client: Any,
    connector_name: str,
    trading_pair: str,
    interval: str = "1h",
    days: int = 30,
) -> dict[str, Any]:
    """
    Get candle data for a trading pair.

    Args:
        client: Hummingbot API client
        connector_name: Exchange connector name
        trading_pair: Trading pair
        interval: Candle interval (e.g., '1h', '5m', '1d')
        days: Number of days of historical data

    Returns:
        Dictionary containing candles data and formatted table

    Raises:
        ValueError: If connector doesn't support candles or interval is invalid
    """
    # Check if connector supports candle data
    available_connectors = await client.market_data.get_available_candle_connectors()
    if connector_name not in available_connectors:
        raise ValueError(
            f"Connector '{connector_name}' does not support candle data. "
            f"Available connectors: {available_connectors}"
        )

    # Calculate max records based on interval
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
            f"Unsupported interval format: {interval}. "
            f"Use '1m', '5m', '15m', '30m', '1h', '4h', '1d', or '1w'."
        )

    # Adjust for interval multiplier
    interval_num = interval[:-1]
    if interval_num:
        max_records = int(max_records / int(interval_num))

    # Fetch candles
    candles = await client.market_data.get_candles(
        connector_name=connector_name,
        trading_pair=trading_pair,
        interval=interval,
        max_records=max_records,
    )

    # Format candles as table
    candles_table = format_candles_as_table(candles)

    return {
        "candles": candles,
        "candles_table": candles_table,
        "connector_name": connector_name,
        "trading_pair": trading_pair,
        "interval": interval,
        "total_candles": len(candles),
    }


async def get_funding_rate(
    client: Any, connector_name: str, trading_pair: str
) -> dict[str, Any]:
    """
    Get funding rate for a perpetual trading pair.

    Args:
        client: Hummingbot API client
        connector_name: Exchange connector name (must have '_perpetual')
        trading_pair: Trading pair

    Returns:
        Dictionary containing funding rate data

    Raises:
        ValueError: If connector is not a perpetual connector
    """
    if "_perpetual" not in connector_name:
        raise ValueError(
            f"Connector '{connector_name}' is not a perpetual connector. "
            f"Funding rates are only available for perpetual connectors."
        )

    # Fetch funding rate
    funding_rate = await client.market_data.get_funding_info(
        connector_name=connector_name, trading_pair=trading_pair
    )

    # Format data
    next_funding_time = funding_rate.get("next_funding_time", 0)
    time_str = (
        datetime.fromtimestamp(next_funding_time).strftime("%Y-%m-%d %H:%M:%S")
        if next_funding_time
        else "N/A"
    )

    rate = funding_rate.get("funding_rate", 0)
    rate_pct = rate * 100  # Convert to percentage

    return {
        "connector_name": connector_name,
        "trading_pair": trading_pair,
        "funding_rate": rate,
        "funding_rate_pct": rate_pct,
        "mark_price": funding_rate.get("mark_price", 0),
        "index_price": funding_rate.get("index_price", 0),
        "next_funding_time": time_str,
    }


async def get_active_feeds(client: Any) -> dict[str, Any]:
    """
    Get information about currently active market data feeds.

    Args:
        client: Hummingbot API client

    Returns:
        Dictionary containing active feeds information
    """
    return await client.market_data.get_active_feeds()


async def get_order_book(
    client: Any,
    connector_name: str,
    trading_pair: str,
    query_type: Literal[
        "snapshot",
        "volume_for_price",
        "price_for_volume",
        "quote_volume_for_price",
        "price_for_quote_volume",
    ],
    query_value: float | None = None,
    is_buy: bool = True,
) -> dict[str, Any]:
    """
    Get order book data for a trading pair.

    Args:
        client: Hummingbot API client
        connector_name: Exchange connector name
        trading_pair: Trading pair
        query_type: Type of order book query
        query_value: Value for query (required for non-snapshot queries)
        is_buy: Whether to analyze buy or sell side

    Returns:
        Dictionary containing order book data

    Raises:
        ValueError: If query_value is missing for non-snapshot queries
    """
    if query_type == "snapshot":
        # Get full order book snapshot
        order_book = await client.market_data.get_order_book(
            connector_name=connector_name, trading_pair=trading_pair
        )

        # Format order book as table
        order_book_table = format_order_book_as_table(order_book)

        timestamp = order_book.get("timestamp", 0)
        time_str = (
            datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            if timestamp
            else "N/A"
        )

        return {
            "query_type": "snapshot",
            "order_book": order_book,
            "order_book_table": order_book_table,
            "connector_name": connector_name,
            "trading_pair": trading_pair,
            "timestamp": time_str,
        }
    else:
        # Handle query-based requests
        if query_value is None:
            raise ValueError(f"query_value must be provided for query_type '{query_type}'")

        # Execute appropriate query
        if query_type == "volume_for_price":
            result = await client.market_data.get_volume_for_price(
                connector_name=connector_name,
                trading_pair=trading_pair,
                price=query_value,
                is_buy=is_buy,
            )
        elif query_type == "price_for_volume":
            result = await client.market_data.get_price_for_volume(
                connector_name=connector_name,
                trading_pair=trading_pair,
                volume=query_value,
                is_buy=is_buy,
            )
        elif query_type == "quote_volume_for_price":
            result = await client.market_data.get_quote_volume_for_price(
                connector_name=connector_name,
                trading_pair=trading_pair,
                price=query_value,
                is_buy=is_buy,
            )
        elif query_type == "price_for_quote_volume":
            result = await client.market_data.get_price_for_quote_volume(
                connector_name=connector_name,
                trading_pair=trading_pair,
                quote_volume=query_value,
                is_buy=is_buy,
            )
        else:
            raise ValueError(f"Unsupported query type: {query_type}")

        side_str = "BUY" if is_buy else "SELL"

        return {
            "query_type": query_type,
            "result": result,
            "connector_name": connector_name,
            "trading_pair": trading_pair,
            "query_value": query_value,
            "side": side_str,
        }
