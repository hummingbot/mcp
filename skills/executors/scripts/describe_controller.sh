#!/bin/bash
# Describe a specific controller with its code and configuration template
# Usage: ./describe_controller.sh --name CONTROLLER_NAME [--config CONFIG_NAME]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONTROLLER_NAME=""
CONFIG_NAME=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            CONTROLLER_NAME="$2"
            shift 2
            ;;
        --config)
            CONFIG_NAME="$2"
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

if [ -z "$CONTROLLER_NAME" ]; then
    echo '{"error": "controller name is required. Use --name CONTROLLER_NAME"}'
    exit 1
fi

# Get list of controllers to find the type
CONTROLLERS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controllers")

# Find controller type
CONTROLLER_TYPE=""
for type in "directional_trading" "market_making" "generic"; do
    if echo "$CONTROLLERS" | jq -e --arg type "$type" --arg name "$CONTROLLER_NAME" '.[$type] | index($name)' > /dev/null 2>&1; then
        CONTROLLER_TYPE="$type"
        break
    fi
done

if [ -z "$CONTROLLER_TYPE" ]; then
    echo "{\"error\": \"Controller '$CONTROLLER_NAME' not found\"}"
    exit 1
fi

# Get controller code
CONTROLLER_CODE=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controllers/$CONTROLLER_TYPE/$CONTROLLER_NAME")

# Get config template
TEMPLATE=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controllers/$CONTROLLER_TYPE/$CONTROLLER_NAME/config-template")

# Get existing configs for this controller
CONFIGS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controller-configs")
CONTROLLER_CONFIGS=$(echo "$CONFIGS" | jq --arg name "$CONTROLLER_NAME" '[.[] | select(.controller_name == $name) | .id]')

# Get specific config details if requested
CONFIG_DETAILS="null"
if [ -n "$CONFIG_NAME" ]; then
    CONFIG_DETAILS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controller-configs/$CONFIG_NAME")
fi

# Format template for readability
PARAMS_TABLE=""
for key in $(echo "$TEMPLATE" | jq -r 'keys[]'); do
    if [ "$key" != "id" ] && [ "$key" != "controller_name" ] && [ "$key" != "controller_type" ]; then
        TYPE=$(echo "$TEMPLATE" | jq -r --arg k "$key" '.[$k].type // "unknown"')
        DEFAULT=$(echo "$TEMPLATE" | jq -r --arg k "$key" '.[$k].default // "None"')
        PARAMS_TABLE+="$key|$TYPE|$DEFAULT\n"
    fi
done

# Output result
cat << EOF
{
    "controller_name": "$CONTROLLER_NAME",
    "controller_type": "$CONTROLLER_TYPE",
    "existing_configs": $CONTROLLER_CONFIGS,
    "config_count": $(echo "$CONTROLLER_CONFIGS" | jq 'length'),
    "template": $TEMPLATE,
    "config_details": $CONFIG_DETAILS,
    "code_preview": $(echo "$CONTROLLER_CODE" | head -100 | jq -Rs .)
}
EOF
