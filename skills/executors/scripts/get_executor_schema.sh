#!/bin/bash
# Get configuration schema for a specific executor type
# Usage: ./get_executor_schema.sh --type EXECUTOR_TYPE

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
EXECUTOR_TYPE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type) EXECUTOR_TYPE="$2"; shift 2 ;;
        --api-url) API_URL="$2"; shift 2 ;;
        --api-user) API_USER="$2"; shift 2 ;;
        --api-pass) API_PASS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$EXECUTOR_TYPE" ]; then
    echo '{"error": "executor type is required. Use --type EXECUTOR_TYPE"}'
    exit 1
fi

# Fetch schema
RESPONSE=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/executors/types/$EXECUTOR_TYPE/config")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to get schema for '$EXECUTOR_TYPE'\", \"detail\": $RESPONSE}"
    exit 1
fi

echo "$RESPONSE" | jq '.'
