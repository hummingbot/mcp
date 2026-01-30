#!/bin/bash
# Fetch candlestick (OHLCV) data for a trading pair
# Usage: ./get_candles.sh --connector CONNECTOR --pair TRADING_PAIR [--interval INTERVAL] [--days DAYS]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
TRADING_PAIR=""
INTERVAL="1h"
DAYS=30

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
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
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

# Validate interval
case "$INTERVAL" in
    1m|5m|15m|30m|1h|4h|1d|1w)
        ;;
    *)
        echo '{"error": "Invalid interval. Use 1m, 5m, 15m, 30m, 1h, 4h, 1d, or 1w"}'
        exit 1
        ;;
esac

# Calculate max_records based on interval
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
    *w)
        MAX_RECORDS=$((DAYS / 7))
        ;;
esac

# Fetch candles
CANDLES=$(curl -s -u "$API_USER:$API_PASS" \
    "$API_URL/api/v1/market-data/candles?connector_name=$CONNECTOR&trading_pair=$TRADING_PAIR&interval=$INTERVAL&max_records=$MAX_RECORDS")

# Check for error
if echo "$CANDLES" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to fetch candles\", \"detail\": $CANDLES}"
    exit 1
fi

# Get candle count
TOTAL=$(echo "$CANDLES" | jq 'length')

# Get latest candle stats
if [ "$TOTAL" -gt 0 ]; then
    LATEST=$(echo "$CANDLES" | jq '.[-1]')
    FIRST=$(echo "$CANDLES" | jq '.[0]')
    LATEST_CLOSE=$(echo "$LATEST" | jq '.close')
    FIRST_CLOSE=$(echo "$FIRST" | jq '.close')

    # Calculate price change
    CHANGE=$(echo "scale=4; ($LATEST_CLOSE - $FIRST_CLOSE) / $FIRST_CLOSE * 100" | bc 2>/dev/null || echo "0")

    # Get high/low for period
    HIGH=$(echo "$CANDLES" | jq '[.[].high] | max')
    LOW=$(echo "$CANDLES" | jq '[.[].low] | min')
    TOTAL_VOLUME=$(echo "$CANDLES" | jq '[.[].volume] | add')
else
    LATEST="null"
    CHANGE="0"
    HIGH="0"
    LOW="0"
    TOTAL_VOLUME="0"
fi

cat << EOF
{
    "connector": "$CONNECTOR",
    "trading_pair": "$TRADING_PAIR",
    "interval": "$INTERVAL",
    "days": $DAYS,
    "total_candles": $TOTAL,
    "summary": {
        "latest_close": $LATEST_CLOSE,
        "period_high": $HIGH,
        "period_low": $LOW,
        "price_change_pct": $CHANGE,
        "total_volume": $TOTAL_VOLUME
    },
    "latest_candle": $LATEST,
    "candles": $CANDLES
}
EOF
