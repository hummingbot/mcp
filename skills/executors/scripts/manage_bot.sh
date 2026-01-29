#!/bin/bash
# Manage bot execution (stop, start/stop controllers)
# Usage: ./manage_bot.sh --name BOT_NAME --action [stop|stop_controllers|start_controllers] [--controllers "ctrl1,ctrl2"]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
BOT_NAME=""
ACTION=""
CONTROLLERS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            BOT_NAME="$2"
            shift 2
            ;;
        --action)
            ACTION="$2"
            shift 2
            ;;
        --controllers)
            CONTROLLERS="$2"
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

if [ -z "$ACTION" ]; then
    echo '{"error": "action is required. Use --action [stop|stop_controllers|start_controllers]"}'
    exit 1
fi

case "$ACTION" in
    stop)
        # Stop and archive the entire bot
        RESPONSE=$(curl -s -X POST \
            -u "$API_USER:$API_PASS" \
            "$API_URL/api/v1/bots/$BOT_NAME/stop")

        cat << EOF
{
    "status": "success",
    "action": "bot_stopped",
    "bot_name": "$BOT_NAME",
    "response": $RESPONSE
}
EOF
        ;;

    stop_controllers)
        if [ -z "$CONTROLLERS" ]; then
            echo '{"error": "controllers are required for stop_controllers action. Use --controllers \"ctrl1,ctrl2\""}'
            exit 1
        fi

        # Convert to array and stop each controller
        RESULTS="["
        FIRST=true
        IFS=',' read -ra CTRL_ARRAY <<< "$CONTROLLERS"
        for ctrl in "${CTRL_ARRAY[@]}"; do
            # Set manual_kill_switch to true
            RESPONSE=$(curl -s -X PATCH \
                -u "$API_USER:$API_PASS" \
                -H "Content-Type: application/json" \
                -d '{"manual_kill_switch": true}' \
                "$API_URL/api/v1/bots/$BOT_NAME/controllers/$ctrl")

            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                RESULTS+=","
            fi
            RESULTS+="{\"controller\": \"$ctrl\", \"result\": $RESPONSE}"
        done
        RESULTS+="]"

        cat << EOF
{
    "status": "success",
    "action": "controllers_stopped",
    "bot_name": "$BOT_NAME",
    "controllers": $(echo "$CONTROLLERS" | tr ',' '\n' | jq -R . | jq -s .),
    "results": $RESULTS
}
EOF
        ;;

    start_controllers)
        if [ -z "$CONTROLLERS" ]; then
            echo '{"error": "controllers are required for start_controllers action. Use --controllers \"ctrl1,ctrl2\""}'
            exit 1
        fi

        # Convert to array and start each controller
        RESULTS="["
        FIRST=true
        IFS=',' read -ra CTRL_ARRAY <<< "$CONTROLLERS"
        for ctrl in "${CTRL_ARRAY[@]}"; do
            # Set manual_kill_switch to false
            RESPONSE=$(curl -s -X PATCH \
                -u "$API_USER:$API_PASS" \
                -H "Content-Type: application/json" \
                -d '{"manual_kill_switch": false}' \
                "$API_URL/api/v1/bots/$BOT_NAME/controllers/$ctrl")

            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                RESULTS+=","
            fi
            RESULTS+="{\"controller\": \"$ctrl\", \"result\": $RESPONSE}"
        done
        RESULTS+="]"

        cat << EOF
{
    "status": "success",
    "action": "controllers_started",
    "bot_name": "$BOT_NAME",
    "controllers": $(echo "$CONTROLLERS" | tr ',' '\n' | jq -R . | jq -s .),
    "results": $RESULTS
}
EOF
        ;;

    *)
        echo "{\"error\": \"Invalid action '$ACTION'. Use stop, stop_controllers, or start_controllers\"}"
        exit 1
        ;;
esac
