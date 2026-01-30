#!/bin/bash
# Stop a running executor
# Usage: ./stop_executor.sh --id EXECUTOR_ID [--keep-position]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
EXECUTOR_ID=""
KEEP_POSITION=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --id) EXECUTOR_ID="$2"; shift 2 ;;
        --keep-position) KEEP_POSITION=true; shift ;;
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

# Build request body
REQUEST=$(jq -n --argjson keep "$KEEP_POSITION" '{keep_position: $keep}')

# Stop executor
RESPONSE=$(curl -s -X POST \
    -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$REQUEST" \
    "$API_URL/executors/$EXECUTOR_ID/stop")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to stop executor '$EXECUTOR_ID'\", \"detail\": $RESPONSE}"
    exit 1
fi

cat << EOF
{
    "status": "success",
    "action": "executor_stopped",
    "executor_id": "$EXECUTOR_ID",
    "keep_position": $KEEP_POSITION,
    "response": $RESPONSE
}
EOF
