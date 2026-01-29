#!/bin/bash
# Deploy a trading bot with specified controller configurations
# Usage: ./deploy_bot.sh --name BOT_NAME --configs "config1,config2" [--account ACCOUNT] [--max-drawdown AMOUNT]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
BOT_NAME=""
CONFIGS=""
ACCOUNT="master_account"
MAX_GLOBAL_DRAWDOWN=""
MAX_CONTROLLER_DRAWDOWN=""
IMAGE="hummingbot/hummingbot:latest"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            BOT_NAME="$2"
            shift 2
            ;;
        --configs)
            CONFIGS="$2"
            shift 2
            ;;
        --account)
            ACCOUNT="$2"
            shift 2
            ;;
        --max-drawdown)
            MAX_GLOBAL_DRAWDOWN="$2"
            shift 2
            ;;
        --max-controller-drawdown)
            MAX_CONTROLLER_DRAWDOWN="$2"
            shift 2
            ;;
        --image)
            IMAGE="$2"
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
if [ -z "$BOT_NAME" ]; then
    echo '{"error": "bot name is required. Use --name BOT_NAME"}'
    exit 1
fi

if [ -z "$CONFIGS" ]; then
    echo '{"error": "configs are required. Use --configs \"config1,config2\""}'
    exit 1
fi

# Convert comma-separated configs to JSON array
CONFIGS_ARRAY=$(echo "$CONFIGS" | tr ',' '\n' | jq -R . | jq -s .)

# Verify configs exist
for config in $(echo "$CONFIGS_ARRAY" | jq -r '.[]'); do
    CHECK=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controller-configs/$config")
    if echo "$CHECK" | jq -e '.detail' > /dev/null 2>&1; then
        echo "{\"error\": \"Configuration '$config' not found\"}"
        exit 1
    fi
done

# Build deploy request
DEPLOY_REQUEST="{\"instance_name\": \"$BOT_NAME\", \"controllers_config\": $CONFIGS_ARRAY, \"credentials_profile\": \"$ACCOUNT\", \"image\": \"$IMAGE\""

if [ -n "$MAX_GLOBAL_DRAWDOWN" ]; then
    DEPLOY_REQUEST+=", \"max_global_drawdown_quote\": $MAX_GLOBAL_DRAWDOWN"
fi

if [ -n "$MAX_CONTROLLER_DRAWDOWN" ]; then
    DEPLOY_REQUEST+=", \"max_controller_drawdown_quote\": $MAX_CONTROLLER_DRAWDOWN"
fi

DEPLOY_REQUEST+="}"

# Deploy bot
RESPONSE=$(curl -s -X POST \
    -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$DEPLOY_REQUEST" \
    "$API_URL/api/v1/bots/deploy")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to deploy bot\", \"detail\": $RESPONSE}"
    exit 1
fi

# Wait a moment for bot to start
sleep 2

# Get bot status
STATUS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/bots/status")

cat << EOF
{
    "status": "success",
    "action": "bot_deployed",
    "bot_name": "$BOT_NAME",
    "controllers": $CONFIGS_ARRAY,
    "account": "$ACCOUNT",
    "image": "$IMAGE",
    "deployment_response": $RESPONSE,
    "current_status": $STATUS
}
EOF
