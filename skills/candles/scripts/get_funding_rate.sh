#!/bin/bash
# Get funding rate for perpetual trading pairs
# Usage: ./get_funding_rate.sh --connector CONNECTOR_PERPETUAL --pair TRADING_PAIR

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
TRADING_PAIR=""

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
    echo '{"error": "connector is required. Use --connector CONNECTOR_NAME (must be perpetual)"}'
    exit 1
fi

if [ -z "$TRADING_PAIR" ]; then
    echo '{"error": "trading pair is required. Use --pair TRADING_PAIR"}'
    exit 1
fi

# Check if connector is perpetual
if [[ "$CONNECTOR" != *"perpetual"* ]]; then
    echo "{\"error\": \"Connector '$CONNECTOR' is not a perpetual connector. Funding rates are only available for perpetual connectors (e.g., binance_perpetual)\"}"
    exit 1
fi

# Fetch funding rate
FUNDING=$(curl -s -u "$API_USER:$API_PASS" \
    "$API_URL/api/v1/market-data/funding-info?connector_name=$CONNECTOR&trading_pair=$TRADING_PAIR")

# Check for error
if echo "$FUNDING" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to fetch funding rate\", \"detail\": $FUNDING}"
    exit 1
fi

# Extract and format data
FUNDING_RATE=$(echo "$FUNDING" | jq '.funding_rate // 0')
MARK_PRICE=$(echo "$FUNDING" | jq '.mark_price // 0')
INDEX_PRICE=$(echo "$FUNDING" | jq '.index_price // 0')
NEXT_FUNDING_TIME=$(echo "$FUNDING" | jq '.next_funding_time // 0')

# Calculate funding rate percentage
FUNDING_PCT=$(echo "scale=6; $FUNDING_RATE * 100" | bc 2>/dev/null || echo "0")

# Calculate annualized rate (3 funding periods per day * 365)
ANNUAL_PCT=$(echo "scale=2; $FUNDING_PCT * 3 * 365" | bc 2>/dev/null || echo "0")

# Format next funding time
if [ "$NEXT_FUNDING_TIME" != "0" ] && [ "$NEXT_FUNDING_TIME" != "null" ]; then
    NEXT_TIME_STR=$(date -d "@$NEXT_FUNDING_TIME" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -r "$NEXT_FUNDING_TIME" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "N/A")
else
    NEXT_TIME_STR="N/A"
fi

# Determine sentiment
if (( $(echo "$FUNDING_RATE > 0.0001" | bc -l 2>/dev/null || echo 0) )); then
    SENTIMENT="bullish (longs pay shorts)"
elif (( $(echo "$FUNDING_RATE < -0.0001" | bc -l 2>/dev/null || echo 0) )); then
    SENTIMENT="bearish (shorts pay longs)"
else
    SENTIMENT="neutral"
fi

cat << EOF
{
    "connector": "$CONNECTOR",
    "trading_pair": "$TRADING_PAIR",
    "funding_rate": $FUNDING_RATE,
    "funding_rate_pct": $FUNDING_PCT,
    "annualized_rate_pct": $ANNUAL_PCT,
    "mark_price": $MARK_PRICE,
    "index_price": $INDEX_PRICE,
    "next_funding_time": "$NEXT_TIME_STR",
    "sentiment": "$SENTIMENT",
    "interpretation": "Current funding rate of ${FUNDING_PCT}% means ${SENTIMENT}"
}
EOF
