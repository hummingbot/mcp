#!/bin/bash
# Get current prices for trading pairs
# Usage: ./get_price.sh --connector CONNECTOR --pairs "PAIR1,PAIR2"

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
PAIRS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector)
            CONNECTOR="$2"
            shift 2
            ;;
        --pairs)
            PAIRS="$2"
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

if [ -z "$PAIRS" ]; then
    echo '{"error": "trading pairs are required. Use --pairs \"PAIR1,PAIR2\""}'
    exit 1
fi

# Convert pairs to JSON array format
PAIRS_JSON=$(echo "$PAIRS" | tr ',' '\n' | jq -R . | jq -s .)

# Fetch prices (POST request with JSON body)
RESPONSE=$(curl -s -u "$API_USER:$API_PASS" \
    -X POST "$API_URL/market-data/prices" \
    -H "Content-Type: application/json" \
    -d "{\"connector_name\": \"$CONNECTOR\", \"trading_pairs\": $PAIRS_JSON}")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to fetch prices\", \"detail\": $RESPONSE}"
    exit 1
fi

# Extract prices and timestamp from response
PRICES=$(echo "$RESPONSE" | jq '.prices')
TIMESTAMP=$(echo "$RESPONSE" | jq -r '.timestamp // 0')

# Format timestamp
if [ "$TIMESTAMP" != "0" ] && [ "$TIMESTAMP" != "null" ]; then
    TIME_STR=$(date -d "@${TIMESTAMP%.*}" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -r "${TIMESTAMP%.*}" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "N/A")
else
    TIME_STR="N/A"
fi

cat << EOF
{
    "connector": "$CONNECTOR",
    "prices": $PRICES,
    "timestamp": "$TIME_STR",
    "pairs_requested": $(echo "$PAIRS" | tr ',' '\n' | jq -R . | jq -s .)
}
EOF
