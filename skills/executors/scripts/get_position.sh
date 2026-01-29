#!/bin/bash
# Get a specific held position
# Usage: ./get_position.sh --connector CONNECTOR --pair PAIR

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
PAIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector) CONNECTOR="$2"; shift 2 ;;
        --pair) PAIR="$2"; shift 2 ;;
        --api-url) API_URL="$2"; shift 2 ;;
        --api-user) API_USER="$2"; shift 2 ;;
        --api-pass) API_PASS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CONNECTOR" ]; then
    echo '{"error": "connector is required. Use --connector CONNECTOR"}'
    exit 1
fi

if [ -z "$PAIR" ]; then
    echo '{"error": "trading pair is required. Use --pair PAIR"}'
    exit 1
fi

# Fetch position
RESPONSE=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/executors/positions/$CONNECTOR/$PAIR")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to get position for $CONNECTOR/$PAIR\", \"detail\": $RESPONSE}"
    exit 1
fi

echo "$RESPONSE" | jq '.'
