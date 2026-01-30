#!/bin/bash
# Calculate technical indicators on candle data
# Usage: ./calculate_indicator.sh --connector CONNECTOR --pair PAIR --indicator INDICATOR [--period PERIOD] [options]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
TRADING_PAIR=""
INDICATOR=""
PERIOD=14
INTERVAL="1h"
DAYS=30
# MACD specific
FAST=12
SLOW=26
SIGNAL=9
# BB specific
STD=2

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector)
            CONNECTOR="$2"
            shift 2
            ;;
        --pair)
            TRADING_PAIR="$2"
            shift 2
            ;;
        --indicator)
            INDICATOR="$2"
            shift 2
            ;;
        --period)
            PERIOD="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        --fast)
            FAST="$2"
            shift 2
            ;;
        --slow)
            SLOW="$2"
            shift 2
            ;;
        --signal)
            SIGNAL="$2"
            shift 2
            ;;
        --std)
            STD="$2"
            shift 2
            ;;
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --api-user)
            API_USER="$2"
            shift 2
            ;;
        --api-pass)
            API_PASS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Validate required arguments
if [ -z "$CONNECTOR" ]; then
    echo '{"error": "connector is required. Use --connector CONNECTOR_NAME"}'
    exit 1
fi

if [ -z "$TRADING_PAIR" ]; then
    echo '{"error": "trading pair is required. Use --pair TRADING_PAIR"}'
    exit 1
fi

if [ -z "$INDICATOR" ]; then
    echo '{"error": "indicator is required. Use --indicator [rsi|ema|sma|macd|bb|atr]"}'
    exit 1
fi

# Calculate max records needed
case "$INTERVAL" in
    *m)
        MINUTES=${INTERVAL%m}
        MAX_RECORDS=$((1440 * DAYS / MINUTES))
        ;;
    *h)
        HOURS=${INTERVAL%h}
        MAX_RECORDS=$((24 * DAYS / HOURS))
        ;;
    *d)
        MAX_RECORDS=$DAYS
        ;;
    *)
        MAX_RECORDS=$((24 * DAYS))
        ;;
esac

# Calculate timestamps for historical fetch
END_TIME=$(date +%s)
START_TIME=$((END_TIME - DAYS * 24 * 3600))

# Fetch historical candles
HISTORICAL=$(curl -s -u "$API_USER:$API_PASS" \
    -X POST "$API_URL/market-data/historical-candles" \
    -H "Content-Type: application/json" \
    -d "{\"connector_name\": \"$CONNECTOR\", \"trading_pair\": \"$TRADING_PAIR\", \"interval\": \"$INTERVAL\", \"start_time\": $START_TIME, \"end_time\": $END_TIME}" 2>/dev/null || echo "[]")

# Fetch real-time candles
REALTIME=$(curl -s -u "$API_USER:$API_PASS" \
    -X POST "$API_URL/market-data/candles" \
    -H "Content-Type: application/json" \
    -d "{\"connector_name\": \"$CONNECTOR\", \"trading_pair\": \"$TRADING_PAIR\", \"interval\": \"$INTERVAL\", \"max_records\": 100}" 2>/dev/null || echo "[]")

# Merge and deduplicate by timestamp
CANDLES=$(echo "$HISTORICAL $REALTIME" | jq -s '.[0] + .[1] | group_by(.timestamp) | map(.[0]) | sort_by(.timestamp)')

if echo "$CANDLES" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to fetch candles\", \"detail\": $CANDLES}"
    exit 1
fi

# Extract close prices (compact JSON to avoid newline issues in heredoc)
CLOSES=$(echo "$CANDLES" | jq -c '[.[].close]')
HIGHS=$(echo "$CANDLES" | jq -c '[.[].high]')
LOWS=$(echo "$CANDLES" | jq -c '[.[].low]')
VOLUMES=$(echo "$CANDLES" | jq -c '[.[].volume]')
TOTAL=$(echo "$CANDLES" | jq 'length')

# Calculate indicator using Python (for accurate calculations)
calculate_with_python() {
    python3 << PYTHON_SCRIPT
import json
import sys

closes = json.loads('$CLOSES')
highs = json.loads('$HIGHS')
lows = json.loads('$LOWS')
volumes = json.loads('$VOLUMES')
indicator = '$INDICATOR'
period = int('$PERIOD')
fast = int('$FAST')
slow = int('$SLOW')
signal_period = int('$SIGNAL')
std_dev = float('$STD')

def sma(data, period):
    if len(data) < period:
        return None
    return sum(data[-period:]) / period

def ema(data, period):
    if len(data) < period:
        return None
    multiplier = 2 / (period + 1)
    ema_val = sum(data[:period]) / period
    for price in data[period:]:
        ema_val = (price - ema_val) * multiplier + ema_val
    return ema_val

def rsi(data, period):
    if len(data) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(data)):
        change = data[i] - data[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(data, fast_period, slow_period, signal_period):
    if len(data) < slow_period:
        return None, None, None
    fast_ema = ema(data, fast_period)
    slow_ema = ema(data, slow_period)
    macd_line = fast_ema - slow_ema

    # Calculate signal line (EMA of MACD)
    macd_values = []
    for i in range(slow_period, len(data)):
        subset = data[:i+1]
        f = ema(subset, fast_period)
        s = ema(subset, slow_period)
        macd_values.append(f - s)

    signal_line = ema(macd_values, signal_period) if len(macd_values) >= signal_period else macd_line
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram

def bollinger_bands(data, period, std_multiplier):
    if len(data) < period:
        return None, None, None
    middle = sma(data, period)
    variance = sum((x - middle) ** 2 for x in data[-period:]) / period
    std = variance ** 0.5
    upper = middle + (std_multiplier * std)
    lower = middle - (std_multiplier * std)
    return upper, middle, lower

def atr(highs, lows, closes, period):
    if len(closes) < period + 1:
        return None
    tr_values = []
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i] - closes[i-1])
        tr_values.append(max(hl, hc, lc))
    return sum(tr_values[-period:]) / period

result = {}
current_price = closes[-1] if closes else 0

if indicator == 'rsi':
    value = rsi(closes, period)
    if value is not None:
        if value > 70:
            sig = 'overbought'
        elif value < 30:
            sig = 'oversold'
        else:
            sig = 'neutral'
        result = {
            'indicator': 'rsi',
            'period': period,
            'current_value': round(value, 2),
            'signal': sig,
            'interpretation': {
                'overbought_threshold': 70,
                'oversold_threshold': 30,
                'description': f'RSI at {round(value, 2)} indicates {sig} conditions'
            }
        }

elif indicator == 'ema':
    value = ema(closes, period)
    if value is not None:
        trend = 'bullish' if current_price > value else 'bearish'
        result = {
            'indicator': 'ema',
            'period': period,
            'current_value': round(value, 2),
            'current_price': round(current_price, 2),
            'signal': trend,
            'distance_pct': round((current_price - value) / value * 100, 2)
        }

elif indicator == 'sma':
    value = sma(closes, period)
    if value is not None:
        trend = 'bullish' if current_price > value else 'bearish'
        result = {
            'indicator': 'sma',
            'period': period,
            'current_value': round(value, 2),
            'current_price': round(current_price, 2),
            'signal': trend,
            'distance_pct': round((current_price - value) / value * 100, 2)
        }

elif indicator == 'macd':
    macd_line, signal_line, histogram = macd(closes, fast, slow, signal_period)
    if macd_line is not None:
        sig = 'bullish' if histogram > 0 else 'bearish'
        result = {
            'indicator': 'macd',
            'parameters': {'fast': fast, 'slow': slow, 'signal': signal_period},
            'current_values': {
                'macd_line': round(macd_line, 4),
                'signal_line': round(signal_line, 4),
                'histogram': round(histogram, 4)
            },
            'signal': sig,
            'interpretation': f'MACD {"above" if histogram > 0 else "below"} signal line, {sig} momentum'
        }

elif indicator == 'bb':
    upper, middle, lower = bollinger_bands(closes, period, std_dev)
    if upper is not None:
        bandwidth = (upper - lower) / middle
        if current_price > upper:
            position = 'above_upper'
        elif current_price < lower:
            position = 'below_lower'
        else:
            position = 'middle'
        result = {
            'indicator': 'bb',
            'period': period,
            'std': std_dev,
            'current_values': {
                'upper': round(upper, 2),
                'middle': round(middle, 2),
                'lower': round(lower, 2),
                'current_price': round(current_price, 2)
            },
            'position': position,
            'bandwidth': round(bandwidth, 4)
        }

elif indicator == 'atr':
    value = atr(highs, lows, closes, period)
    if value is not None:
        atr_pct = (value / current_price) * 100
        result = {
            'indicator': 'atr',
            'period': period,
            'current_value': round(value, 4),
            'current_price': round(current_price, 2),
            'atr_percent': round(atr_pct, 2),
            'interpretation': f'ATR of {round(value, 4)} ({round(atr_pct, 2)}% of price) indicates {"high" if atr_pct > 3 else "normal"} volatility'
        }

else:
    result = {'error': f'Unknown indicator: {indicator}'}

result['connector'] = '$CONNECTOR'
result['trading_pair'] = '$TRADING_PAIR'
result['interval'] = '$INTERVAL'
result['candles_used'] = len(closes)

print(json.dumps(result, indent=2))
PYTHON_SCRIPT
}

# Run calculation
calculate_with_python
