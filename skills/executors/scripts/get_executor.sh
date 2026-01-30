#!/bin/bash
# Get details for a specific executor
# Usage: ./get_executor.sh --id EXECUTOR_ID

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
EXECUTOR_ID=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --id) EXECUTOR_ID="$2"; shift 2 ;;
        --api-url) API_URL="$2"; shift 2 ;;
        --api-user) API_USER="$2"; shift 2 ;;
        --api-pass) API_PASS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$EXECUTOR_ID" ]; then
    echo '{"error": "executor ID is required. Use --id EXECUTOR_ID"}'
    exit 1
fi

# Fetch executor details
RESPONSE=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/executors/$EXECUTOR_ID")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to get executor '$EXECUTOR_ID'\", \"detail\": $RESPONSE}"
    exit 1
fi

echo "$RESPONSE" | jq '.'
