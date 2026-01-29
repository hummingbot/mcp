#!/bin/bash
# Get status of active bots
# Usage: ./get_bot_status.sh [--name BOT_NAME]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
BOT_NAME=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            BOT_NAME="$2"
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

# Get bot status
STATUS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/bots/status")

# Check for error
if echo "$STATUS" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to get bot status\", \"detail\": $STATUS}"
    exit 1
fi

# If specific bot requested, filter
if [ -n "$BOT_NAME" ]; then
    BOT_DATA=$(echo "$STATUS" | jq --arg name "$BOT_NAME" '.data[$name] // null')
    if [ "$BOT_DATA" = "null" ]; then
        AVAILABLE_BOTS=$(echo "$STATUS" | jq '.data | keys')
        echo "{\"error\": \"Bot '$BOT_NAME' not found\", \"available_bots\": $AVAILABLE_BOTS}"
        exit 1
    fi

    # Extract key metrics
    cat << EOF
{
    "bot_name": "$BOT_NAME",
    "status": "active",
    "controllers": $(echo "$BOT_DATA" | jq '[.controllers // {} | to_entries[] | {name: .key, pnl: .value.net_pnl_quote, volume: .value.volume_traded_quote, errors: (.value.error_logs | length)}]'),
    "total_pnl": $(echo "$BOT_DATA" | jq '[.controllers // {} | to_entries[].value.net_pnl_quote // 0] | add // 0'),
    "total_volume": $(echo "$BOT_DATA" | jq '[.controllers // {} | to_entries[].value.volume_traded_quote // 0] | add // 0'),
    "recent_errors": $(echo "$BOT_DATA" | jq '[.controllers // {} | to_entries[].value.error_logs // [] | .[-3:][]] | .[-10:]'),
    "raw_data": $BOT_DATA
}
EOF
else
    # Return all bots summary
    BOT_NAMES=$(echo "$STATUS" | jq '.data | keys')
    TOTAL_BOTS=$(echo "$STATUS" | jq '.data | length')

    SUMMARY="["
    FIRST=true
    for bot in $(echo "$BOT_NAMES" | jq -r '.[]'); do
        BOT_DATA=$(echo "$STATUS" | jq --arg name "$bot" '.data[$name]')
        TOTAL_PNL=$(echo "$BOT_DATA" | jq '[.controllers // {} | to_entries[].value.net_pnl_quote // 0] | add // 0')
        TOTAL_VOLUME=$(echo "$BOT_DATA" | jq '[.controllers // {} | to_entries[].value.volume_traded_quote // 0] | add // 0')
        CONTROLLER_COUNT=$(echo "$BOT_DATA" | jq '.controllers // {} | length')

        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            SUMMARY+=","
        fi
        SUMMARY+="{\"name\": \"$bot\", \"controllers\": $CONTROLLER_COUNT, \"pnl\": $TOTAL_PNL, \"volume\": $TOTAL_VOLUME}"
    done
    SUMMARY+="]"

    cat << EOF
{
    "total_bots": $TOTAL_BOTS,
    "bots": $SUMMARY,
    "raw_status": $STATUS
}
EOF
fi
