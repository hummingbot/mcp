"""
Candles Feed prompt - Set up and monitor real-time candle data feeds.
"""


def register_candles_feed_prompts(mcp):
    """Register candles feed prompts."""

    @mcp.prompt()
    def candles_feed() -> str:
        """Set up and monitor real-time candle data feeds for technical analysis.

        This prompt helps users:
        1. List available connectors and active feeds
        2. Start candle feeds for trading pairs
        3. Compute technical indicators
        """
        return '''# Candles Feed Manager

You are helping the user set up and monitor candle data feeds for technical analysis.

The `candles_feed` tool uses progressive disclosure:
- Call with no args to see available connectors and active feeds
- Call with connector to see feeds for that exchange
- Call with connector + trading_pair to start a feed

## Step 1: List Available Connectors

See what exchanges support candle feeds and check active feeds:

```
Use candles_feed()
```

This shows:
- Available connectors that support candle data
- Currently active feeds with status
- Settings (timeout, cleanup intervals)

## Step 2: Check Connector Feeds

See active feeds for a specific connector:

```
Use candles_feed(connector="binance_perpetual")
```

This shows:
- Active feeds for that connector
- Available intervals (1m, 5m, 15m, 1h, 4h, 1d)
- Default settings

## Step 3: Start a Candle Feed

Start a new feed or refresh an existing one:

```
Use candles_feed(
    connector="binance_perpetual",
    trading_pair="BTC-USDT",
    interval="1h",
    days=30
)
```

Parameters:
- **connector**: Exchange name (e.g., binance_perpetual, hyperliquid_perpetual)
- **trading_pair**: Pair to track (e.g., BTC-USDT, ETH-USD)
- **interval**: Candle interval (default: 1h)
- **days**: Historical data (default: 30, max: 365)

The API automatically maintains the feed after starting.

## Step 4: Compute Technical Indicators

Once a feed is running, compute indicators:

```
Use get_technical_indicator(
    connector_name="binance_perpetual",
    trading_pair="BTC-USDT",
    interval="1h",
    indicators=["RSI", "MACD", "BB"]
)
```

### Supported Indicators

| Indicator | Description | Default Period |
|-----------|-------------|----------------|
| RSI | Relative Strength Index | 14 |
| MACD | Moving Avg Convergence Divergence | 12/26/9 |
| BB | Bollinger Bands | 20, 2 std |
| SMA | Simple Moving Average | 20 |
| EMA | Exponential Moving Average | 20 |
| ATR | Average True Range | 14 |
| VWAP | Volume Weighted Avg Price | - |

### Custom Periods

```
Use get_technical_indicator(
    connector_name="binance_perpetual",
    trading_pair="BTC-USDT",
    interval="1h",
    indicators=["RSI", "SMA", "EMA"],
    periods={"RSI": 21, "SMA": 50, "EMA": 200}
)
```

---

## Common Intervals

| Interval | Use Case |
|----------|----------|
| `1m` | Scalping, high-frequency |
| `5m` | Short-term trading |
| `15m` | Intraday trading |
| `1h` | Swing trading (recommended) |
| `4h` | Position trading |
| `1d` | Long-term analysis |

---

## Example Workflow

```
User: "Set up a feed for ETH-USDT and show me the RSI"

1. Start the feed:
   candles_feed(connector="binance_perpetual", trading_pair="ETH-USDT")

2. Compute indicators:
   get_technical_indicator(
       connector_name="binance_perpetual",
       trading_pair="ETH-USDT",
       interval="1h",
       indicators=["RSI", "MACD", "BB"]
   )
```

---

Would you like to see available connectors or start a candle feed?
'''
