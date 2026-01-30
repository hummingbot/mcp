#!/bin/bash
# List executors with optional filtering
# Usage: ./list_executors.sh [--status STATUS] [--connector CONNECTOR] [--pair PAIR] [--type TYPE]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
STATUS=""
CONNECTOR=""
PAIR=""
EXECUTOR_TYPE=""
LIMIT=50

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --status) STATUS="$2"; shift 2 ;;
        --connector) CONNECTOR="$2"; shift 2 ;;
        --pair) PAIR="$2"; shift 2 ;;
        --type) EXECUTOR_TYPE="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --api-url) API_URL="$2"; shift 2 ;;
        --api-user) API_USER="$2"; shift 2 ;;
        --api-pass) API_PASS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Build filter request
FILTER="{\"limit\": $LIMIT"
[ -n "$STATUS" ] && FILTER+=", \"status\": \"$STATUS\""
[ -n "$CONNECTOR" ] && FILTER+=", \"connector_names\": [\"$CONNECTOR\"]"
[ -n "$PAIR" ] && FILTER+=", \"trading_pairs\": [\"$PAIR\"]"
[ -n "$EXECUTOR_TYPE" ] && FILTER+=", \"executor_types\": [\"$EXECUTOR_TYPE\"]"
FILTER+="}"

# Search executors
RESPONSE=$(curl -s -X POST \
    -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$FILTER" \
    "$API_URL/executors/search")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to list executors\", \"detail\": $RESPONSE}"
    exit 1
fi

echo "$RESPONSE" | jq '.'
