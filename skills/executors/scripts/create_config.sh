#!/bin/bash
# Create a new controller configuration
# Usage: ./create_config.sh --name CONFIG_NAME --controller CONTROLLER_NAME --type CONTROLLER_TYPE --config JSON

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONFIG_NAME=""
CONTROLLER_NAME=""
CONTROLLER_TYPE=""
CONFIG_DATA=""
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            CONFIG_NAME="$2"
            shift 2
            ;;
        --controller)
            CONTROLLER_NAME="$2"
            shift 2
            ;;
        --type)
            CONTROLLER_TYPE="$2"
            shift 2
            ;;
        --config)
            CONFIG_DATA="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
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
if [ -z "$CONFIG_NAME" ]; then
    echo '{"error": "config name is required. Use --name CONFIG_NAME"}'
    exit 1
fi

if [ -z "$CONTROLLER_NAME" ]; then
    echo '{"error": "controller name is required. Use --controller CONTROLLER_NAME"}'
    exit 1
fi

if [ -z "$CONTROLLER_TYPE" ]; then
    echo '{"error": "controller type is required. Use --type [directional_trading|market_making|generic]"}'
    exit 1
fi

if [ -z "$CONFIG_DATA" ]; then
    echo '{"error": "config data is required. Use --config JSON_OBJECT"}'
    exit 1
fi

# Check if config already exists
EXISTING=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controller-configs/$CONFIG_NAME")
if ! echo "$EXISTING" | jq -e '.detail' > /dev/null 2>&1; then
    if [ "$FORCE" = false ]; then
        cat << EOF
{
    "error": "Configuration '$CONFIG_NAME' already exists",
    "existing_config": $EXISTING,
    "action_required": "Use --force to override"
}
EOF
        exit 1
    fi
fi

# Build full config object
FULL_CONFIG=$(echo "$CONFIG_DATA" | jq --arg id "$CONFIG_NAME" --arg cn "$CONTROLLER_NAME" --arg ct "$CONTROLLER_TYPE" '. + {id: $id, controller_name: $cn, controller_type: $ct}')

# Validate config
VALIDATION=$(curl -s -X POST \
    -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$FULL_CONFIG" \
    "$API_URL/api/v1/controllers/$CONTROLLER_TYPE/$CONTROLLER_NAME/validate-config")

if echo "$VALIDATION" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Invalid configuration\", \"validation_error\": $VALIDATION}"
    exit 1
fi

# Create or update config
RESPONSE=$(curl -s -X POST \
    -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "$FULL_CONFIG" \
    "$API_URL/api/v1/controller-configs/$CONFIG_NAME")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to create configuration\", \"detail\": $RESPONSE}"
    exit 1
fi

# Get created config
CREATED=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controller-configs/$CONFIG_NAME")

cat << EOF
{
    "status": "success",
    "action": "config_created",
    "config_name": "$CONFIG_NAME",
    "controller_name": "$CONTROLLER_NAME",
    "controller_type": "$CONTROLLER_TYPE",
    "configuration": $CREATED
}
EOF
