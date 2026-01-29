"""
Technical Indicators - Compute indicators from candle data.

Supports: RSI, MACD, Bollinger Bands, SMA, EMA, ATR, VWAP
"""

from typing import Any
from datetime import datetime


# Default periods for indicators
DEFAULT_PERIODS = {
    "RSI": 14,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "BB": 20,
    "BB_STD": 2.0,
    "SMA": 20,
    "EMA": 20,
    "ATR": 14,
}

SUPPORTED_INDICATORS = ["RSI", "MACD", "BB", "SMA", "EMA", "ATR", "VWAP"]


def compute_sma(prices: list[float], period: int) -> list[float | None]:
    """Compute Simple Moving Average."""
    result = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            window = prices[i - period + 1:i + 1]
            result.append(sum(window) / period)
    return result


def compute_ema(prices: list[float], period: int) -> list[float | None]:
    """Compute Exponential Moving Average."""
    result = []
    multiplier = 2 / (period + 1)

    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        elif i == period - 1:
            # First EMA is SMA
            sma = sum(prices[:period]) / period
            result.append(sma)
        else:
            # EMA = (Close - Previous EMA) * multiplier + Previous EMA
            prev_ema = result[-1]
            if prev_ema is not None:
                ema = (prices[i] - prev_ema) * multiplier + prev_ema
                result.append(ema)
            else:
                result.append(None)
    return result


def compute_rsi(prices: list[float], period: int = 14) -> list[float | None]:
    """Compute Relative Strength Index."""
    if len(prices) < period + 1:
        return [None] * len(prices)

    result = [None] * period
    gains = []
    losses = []

    # Calculate price changes
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))

    # First RSI using SMA
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result.append(100.0)
    else:
        rs = avg_gain / avg_loss
        result.append(100 - (100 / (1 + rs)))

    # Subsequent RSI using smoothed averages
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))

    return result


def compute_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> dict[str, list[float | None]]:
    """Compute MACD (Moving Average Convergence Divergence)."""
    fast_ema = compute_ema(prices, fast_period)
    slow_ema = compute_ema(prices, slow_period)

    # MACD Line = Fast EMA - Slow EMA
    macd_line = []
    for i in range(len(prices)):
        if fast_ema[i] is not None and slow_ema[i] is not None:
            macd_line.append(fast_ema[i] - slow_ema[i])
        else:
            macd_line.append(None)

    # Signal Line = EMA of MACD Line
    macd_values = [v for v in macd_line if v is not None]
    if len(macd_values) >= signal_period:
        signal_ema = compute_ema(macd_values, signal_period)
        # Pad with Nones to align
        signal_line = [None] * (len(macd_line) - len(signal_ema)) + signal_ema
    else:
        signal_line = [None] * len(macd_line)

    # Histogram = MACD Line - Signal Line
    histogram = []
    for i in range(len(macd_line)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram.append(macd_line[i] - signal_line[i])
        else:
            histogram.append(None)

    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    }


def compute_bollinger_bands(
    prices: list[float],
    period: int = 20,
    std_dev: float = 2.0
) -> dict[str, list[float | None]]:
    """Compute Bollinger Bands."""
    sma = compute_sma(prices, period)

    upper = []
    lower = []
    middle = sma

    for i in range(len(prices)):
        if i < period - 1:
            upper.append(None)
            lower.append(None)
        else:
            window = prices[i - period + 1:i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            std = variance ** 0.5

            upper.append(mean + std_dev * std)
            lower.append(mean - std_dev * std)

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
    }


def compute_atr(
    high: list[float],
    low: list[float],
    close: list[float],
    period: int = 14
) -> list[float | None]:
    """Compute Average True Range."""
    if len(high) < 2:
        return [None] * len(high)

    true_ranges = [None]  # First TR is undefined

    for i in range(1, len(high)):
        tr = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1])
        )
        true_ranges.append(tr)

    # ATR is smoothed average of TR
    result = [None] * period
    tr_values = [v for v in true_ranges[1:period + 1] if v is not None]

    if len(tr_values) >= period:
        atr = sum(tr_values) / period
        result.append(atr)

        for i in range(period + 1, len(true_ranges)):
            if true_ranges[i] is not None:
                atr = (atr * (period - 1) + true_ranges[i]) / period
                result.append(atr)
            else:
                result.append(None)

    return result


def compute_vwap(
    high: list[float],
    low: list[float],
    close: list[float],
    volume: list[float]
) -> list[float | None]:
    """Compute Volume Weighted Average Price."""
    result = []
    cumulative_tp_vol = 0
    cumulative_vol = 0

    for i in range(len(close)):
        typical_price = (high[i] + low[i] + close[i]) / 3
        cumulative_tp_vol += typical_price * volume[i]
        cumulative_vol += volume[i]

        if cumulative_vol > 0:
            result.append(cumulative_tp_vol / cumulative_vol)
        else:
            result.append(None)

    return result


def compute_indicators(
    candles: list[dict[str, Any]],
    indicators: list[str],
    periods: dict[str, int] | None = None
) -> dict[str, Any]:
    """
    Compute multiple technical indicators from candle data.

    Args:
        candles: List of candle dicts with timestamp, open, high, low, close, volume
        indicators: List of indicator names to compute
        periods: Custom periods for indicators (optional)

    Returns:
        Dict with indicator results and candle data
    """
    if not candles:
        raise ValueError("No candle data provided")

    # Merge default periods with custom periods
    params = DEFAULT_PERIODS.copy()
    if periods:
        params.update(periods)

    # Extract price arrays
    timestamps = [c["timestamp"] for c in candles]
    opens = [c["open"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]
    volumes = [c["volume"] for c in candles]

    results = {
        "timestamps": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "indicators": {},
    }

    for indicator in indicators:
        indicator_upper = indicator.upper()

        if indicator_upper == "RSI":
            period = params.get("RSI", 14)
            results["indicators"][f"RSI_{period}"] = compute_rsi(closes, period)

        elif indicator_upper == "MACD":
            macd_result = compute_macd(
                closes,
                params.get("MACD_FAST", 12),
                params.get("MACD_SLOW", 26),
                params.get("MACD_SIGNAL", 9),
            )
            results["indicators"]["MACD"] = macd_result["macd"]
            results["indicators"]["MACD_SIGNAL"] = macd_result["signal"]
            results["indicators"]["MACD_HIST"] = macd_result["histogram"]

        elif indicator_upper == "BB":
            period = params.get("BB", 20)
            std = params.get("BB_STD", 2.0)
            bb_result = compute_bollinger_bands(closes, period, std)
            results["indicators"][f"BB_UPPER_{period}"] = bb_result["upper"]
            results["indicators"][f"BB_MIDDLE_{period}"] = bb_result["middle"]
            results["indicators"][f"BB_LOWER_{period}"] = bb_result["lower"]

        elif indicator_upper == "SMA":
            period = params.get("SMA", 20)
            results["indicators"][f"SMA_{period}"] = compute_sma(closes, period)

        elif indicator_upper == "EMA":
            period = params.get("EMA", 20)
            results["indicators"][f"EMA_{period}"] = compute_ema(closes, period)

        elif indicator_upper == "ATR":
            period = params.get("ATR", 14)
            results["indicators"][f"ATR_{period}"] = compute_atr(highs, lows, closes, period)

        elif indicator_upper == "VWAP":
            results["indicators"]["VWAP"] = compute_vwap(highs, lows, closes, volumes)

    return results


def get_latest_indicator_values(results: dict[str, Any]) -> dict[str, float | None]:
    """Extract the latest (most recent) value for each indicator."""
    latest = {}

    for name, values in results.get("indicators", {}).items():
        if values:
            # Find the last non-None value
            for v in reversed(values):
                if v is not None:
                    latest[name] = round(v, 4)
                    break
            else:
                latest[name] = None
        else:
            latest[name] = None

    # Add latest price
    closes = results.get("close", [])
    if closes:
        latest["CLOSE"] = closes[-1]

    return latest


def format_indicator_results(
    results: dict[str, Any],
    connector: str,
    trading_pair: str,
    interval: str,
    limit: int = 10
) -> str:
    """Format indicator results as a readable table."""
    lines = [
        f"Technical Indicators: {trading_pair} ({interval})",
        f"Connector: {connector}",
        "=" * 70,
        "",
        "Latest Values:",
        "-" * 40,
    ]

    latest = get_latest_indicator_values(results)
    for name, value in latest.items():
        if value is not None:
            lines.append(f"  {name}: {value}")
        else:
            lines.append(f"  {name}: N/A (insufficient data)")

    # Add interpretation
    lines.extend(["", "Interpretation:", "-" * 40])

    rsi_key = [k for k in latest.keys() if k.startswith("RSI_")]
    if rsi_key and latest[rsi_key[0]] is not None:
        rsi = latest[rsi_key[0]]
        if rsi > 70:
            lines.append(f"  RSI ({rsi}): OVERBOUGHT - potential sell signal")
        elif rsi < 30:
            lines.append(f"  RSI ({rsi}): OVERSOLD - potential buy signal")
        else:
            lines.append(f"  RSI ({rsi}): NEUTRAL")

    if "MACD" in latest and "MACD_SIGNAL" in latest:
        macd = latest["MACD"]
        signal = latest["MACD_SIGNAL"]
        if macd is not None and signal is not None:
            if macd > signal:
                lines.append(f"  MACD: BULLISH (MACD {macd:.4f} > Signal {signal:.4f})")
            else:
                lines.append(f"  MACD: BEARISH (MACD {macd:.4f} < Signal {signal:.4f})")

    bb_upper = [k for k in latest.keys() if k.startswith("BB_UPPER_")]
    bb_lower = [k for k in latest.keys() if k.startswith("BB_LOWER_")]
    if bb_upper and bb_lower and "CLOSE" in latest:
        upper = latest[bb_upper[0]]
        lower = latest[bb_lower[0]]
        close = latest["CLOSE"]
        if upper and lower and close:
            if close > upper:
                lines.append(f"  BB: Price above upper band - OVERBOUGHT")
            elif close < lower:
                lines.append(f"  BB: Price below lower band - OVERSOLD")
            else:
                bb_pct = (close - lower) / (upper - lower) * 100
                lines.append(f"  BB: Price at {bb_pct:.1f}% of band range")

    # Recent data table
    lines.extend(["", f"Recent Data (last {limit} candles):", "-" * 70])

    timestamps = results.get("timestamps", [])[-limit:]
    closes = results.get("close", [])[-limit:]

    # Build header
    header = "Timestamp           | Close"
    for name in results.get("indicators", {}).keys():
        header += f" | {name[:10]:>10}"
    lines.append(header)
    lines.append("-" * len(header))

    # Build rows
    start_idx = len(results.get("timestamps", [])) - limit
    for i, (ts, close) in enumerate(zip(timestamps, closes)):
        dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        row = f"{dt} | {close:>10.2f}"

        for name, values in results.get("indicators", {}).items():
            idx = start_idx + i
            if idx < len(values) and values[idx] is not None:
                row += f" | {values[idx]:>10.4f}"
            else:
                row += f" | {'N/A':>10}"

        lines.append(row)

    lines.append("=" * 70)
    lines.append(f"Total candles in storage: {len(results.get('timestamps', []))}")

    return "\n".join(lines)
