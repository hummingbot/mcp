#!/bin/bash
# List connectors that support candle data
# Usage: ./list_candle_connectors.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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

# Get list of connectors that support candles
CONNECTORS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/market-data/candle-connectors")

# Check for error
if echo "$CONNECTORS" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to get candle connectors\", \"detail\": $CONNECTORS}"
    exit 1
fi

cat << EOF
{
    "connectors": $CONNECTORS,
    "total": $(echo "$CONNECTORS" | jq 'length'),
    "supported_intervals": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
}
EOF
