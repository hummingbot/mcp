#!/bin/bash
# Create executor with progressive disclosure
#
# Flow:
# 1. No parameters → List available executor types
# 2. --type only → Show config schema for that type
# 3. --type + --config → Create and start the executor
#
# Usage:
#   ./setup_executor.sh                                     # Step 1: List executor types
#   ./setup_executor.sh --type position_executor            # Step 2: Show config schema
#   ./setup_executor.sh --type position_executor --config '{...}'  # Step 3: Create executor

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
        --api-url) API_URL="$2"; shift 2 ;;
        --api-user) API_USER="$2"; shift 2 ;;
        --api-pass) API_PASS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Determine flow stage
if [ -z "$EXECUTOR_TYPE" ]; then
    STAGE="list_types"
elif [ -z "$CONFIG" ]; then
    STAGE="show_schema"
else
    STAGE="create"
fi

case "$STAGE" in
    list_types)
        # Step 1: List available executor types
        TYPES=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/executors/types/available")

        if echo "$TYPES" | jq -e '.detail' > /dev/null 2>&1; then
            echo "{\"error\": \"Failed to get executor types\", \"detail\": $TYPES}"
            exit 1
        fi

        # Get current executor summary
        SUMMARY=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/executors/summary")

        cat << EOF
{
    "action": "list_types",
    "message": "Available executor types. Select one to see its configuration schema.",
    "executor_types": $(echo "$TYPES" | jq '.executor_types'),
    "current_summary": {
        "active": $(echo "$SUMMARY" | jq '.total_active'),
        "completed": $(echo "$SUMMARY" | jq '.total_completed'),
        "total_pnl": $(echo "$SUMMARY" | jq '.total_pnl_quote')
    },
    "next_step": "Call again with --type EXECUTOR_TYPE to see the configuration schema",
    "example": "./setup_executor.sh --type position_executor"
}
EOF
        ;;

    show_schema)
        # Step 2: Show configuration schema for the executor type
        SCHEMA=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/executors/types/$EXECUTOR_TYPE/config")

        if echo "$SCHEMA" | jq -e '.detail' > /dev/null 2>&1; then
            echo "{\"error\": \"Executor type '$EXECUTOR_TYPE' not found\", \"detail\": $SCHEMA}"
            exit 1
        fi

        # Extract required and optional fields
        REQUIRED_FIELDS=$(echo "$SCHEMA" | jq '[.fields[] | select(.required == true and .default == null) | .name]')
        OPTIONAL_FIELDS=$(echo "$SCHEMA" | jq '[.fields[] | select(.required != true or .default != null) | {name: .name, default: .default}]')

        # Build minimal example config
        EXAMPLE_CONFIG=$(echo "$SCHEMA" | jq --arg type "$EXECUTOR_TYPE" '
            {type: $type} +
            ([.fields[] | select(.required == true and .default == null) |
                {(.name): (
                    if .type == "string" then "your_" + .name
                    elif .type == "number" then 0
                    elif .type == "boolean" then false
                    else "your_" + .name
                    end
                )}
            ] | add // {})
        ')

        # Build a more complete example for position_executor
        if [ "$EXECUTOR_TYPE" = "position_executor" ]; then
            EXAMPLE_CONFIG='{
    "type": "position_executor",
    "connector_name": "hyperliquid_perpetual",
    "trading_pair": "BTC-USD",
    "side": "BUY",
    "amount": "0.001",
    "triple_barrier_config": {
        "stop_loss": "0.02",
        "take_profit": "0.04",
        "time_limit": 3600
    }
}'
        elif [ "$EXECUTOR_TYPE" = "grid_executor" ]; then
            EXAMPLE_CONFIG='{
    "type": "grid_executor",
    "connector_name": "hyperliquid_perpetual",
    "trading_pair": "BTC-USD",
    "start_price": "80000",
    "end_price": "90000",
    "total_amount_quote": "1000",
    "total_levels": 10,
    "side": "BUY"
}'
        elif [ "$EXECUTOR_TYPE" = "dca_executor" ]; then
            EXAMPLE_CONFIG='{
    "type": "dca_executor",
    "connector_name": "hyperliquid_perpetual",
    "trading_pair": "BTC-USD",
    "side": "BUY",
    "total_amount_quote": "1000",
    "n_levels": 5,
    "time_limit": 86400
}'
        fi

        cat << EOF
{
    "action": "show_schema",
    "message": "Configuration schema for $EXECUTOR_TYPE. Build your config and create the executor.",
    "executor_type": "$EXECUTOR_TYPE",
    "description": $(echo "$SCHEMA" | jq '.description'),
    "required_fields": $REQUIRED_FIELDS,
    "all_fields": $(echo "$SCHEMA" | jq '[.fields[] | {name: .name, type: .type, required: .required, default: .default, description: .description}]'),
    "example_config": $EXAMPLE_CONFIG,
    "next_step": "Call again with --config JSON to create the executor",
    "example": "./setup_executor.sh --type $EXECUTOR_TYPE --config '\$EXAMPLE_CONFIG'"
}
EOF
        ;;

    create)
        # Step 3: Create and start the executor

        # Ensure type is in the config
        CONFIG_WITH_TYPE=$(echo "$CONFIG" | jq --arg type "$EXECUTOR_TYPE" '. + {type: $type}')

        # Build request
        REQUEST=$(jq -n \
            --argjson config "$CONFIG_WITH_TYPE" \
            --arg account "$ACCOUNT" \
            '{executor_config: $config, account_name: $account}')

        # Create executor
        RESPONSE=$(curl -s -X POST \
            -u "$API_USER:$API_PASS" \
            -H "Content-Type: application/json" \
            -d "$REQUEST" \
            "$API_URL/executors")

        if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
            echo "{\"error\": \"Failed to create executor\", \"detail\": $RESPONSE}"
            exit 1
        fi

        # Extract key info from response
        EXECUTOR_ID=$(echo "$RESPONSE" | jq -r '.id // .executor_id // "unknown"')

        cat << EOF
{
    "action": "executor_created",
    "message": "Successfully created and started $EXECUTOR_TYPE",
    "executor_id": "$EXECUTOR_ID",
    "executor_type": "$EXECUTOR_TYPE",
    "account": "$ACCOUNT",
    "config": $CONFIG_WITH_TYPE,
    "response": $RESPONSE,
    "next_steps": [
        "Monitor with: ./get_executor.sh --id $EXECUTOR_ID",
        "Stop with: ./stop_executor.sh --id $EXECUTOR_ID",
        "List all: ./list_executors.sh"
    ]
}
EOF
        ;;
esac
