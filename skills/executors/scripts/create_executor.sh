#!/bin/bash
# Create and start a new executor
# Usage: ./create_executor.sh --type EXECUTOR_TYPE --config JSON [--account ACCOUNT]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
EXECUTOR_TYPE=""
CONFIG=""
ACCOUNT="master_account"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type) EXECUTOR_TYPE="$2"; shift 2 ;;
        --config) CONFIG="$2"; shift 2 ;;
        --account) ACCOUNT="$2"; shift 2 ;;
        --connector) CONNECTOR="$2"; shift 2 ;;
        --pair) PAIR="$2"; shift 2 ;;
        --side) SIDE="$2"; shift 2 ;;
        --amount) AMOUNT="$2"; shift 2 ;;
        --stop-loss) STOP_LOSS="$2"; shift 2 ;;
        --take-profit) TAKE_PROFIT="$2"; shift 2 ;;
        --time-limit) TIME_LIMIT="$2"; shift 2 ;;
        --entry-price) ENTRY_PRICE="$2"; shift 2 ;;
        --lower-price) LOWER_PRICE="$2"; shift 2 ;;
        --upper-price) UPPER_PRICE="$2"; shift 2 ;;
        --levels) LEVELS="$2"; shift 2 ;;
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

# Build config from individual params if not provided as JSON
if [ -z "$CONFIG" ]; then
    CONFIG="{\"type\": \"$EXECUTOR_TYPE\""

    [ -n "$CONNECTOR" ] && CONFIG+=", \"connector_name\": \"$CONNECTOR\""
    [ -n "$PAIR" ] && CONFIG+=", \"trading_pair\": \"$PAIR\""
    [ -n "$SIDE" ] && CONFIG+=", \"side\": \"$SIDE\""
    [ -n "$AMOUNT" ] && CONFIG+=", \"amount\": $AMOUNT"
    [ -n "$ENTRY_PRICE" ] && CONFIG+=", \"entry_price\": $ENTRY_PRICE"
    [ -n "$STOP_LOSS" ] && CONFIG+=", \"stop_loss\": $STOP_LOSS"
    [ -n "$TAKE_PROFIT" ] && CONFIG+=", \"take_profit\": $TAKE_PROFIT"
    [ -n "$TIME_LIMIT" ] && CONFIG+=", \"time_limit\": $TIME_LIMIT"
    [ -n "$LOWER_PRICE" ] && CONFIG+=", \"start_price\": $LOWER_PRICE"
    [ -n "$UPPER_PRICE" ] && CONFIG+=", \"end_price\": $UPPER_PRICE"
    [ -n "$LEVELS" ] && CONFIG+=", \"total_levels\": $LEVELS"

    CONFIG+="}"
else
    # Ensure type is in the config
    CONFIG=$(echo "$CONFIG" | jq --arg type "$EXECUTOR_TYPE" '. + {type: $type}')
fi

# Build request
REQUEST=$(jq -n \
    --argjson config "$CONFIG" \
    --arg account "$ACCOUNT" \
    '{executor_config: $config, account_name: $account}')

# Create executor
RESPONSE=$(curl -s -X POST \
    -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$REQUEST" \
    "$API_URL/executors")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to create executor\", \"detail\": $RESPONSE}"
    exit 1
fi

cat << EOF
{
    "status": "success",
    "action": "executor_created",
    "executor_type": "$EXECUTOR_TYPE",
    "account": "$ACCOUNT",
    "response": $RESPONSE
}
EOF
