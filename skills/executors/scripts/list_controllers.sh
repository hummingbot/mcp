#!/bin/bash
# List available controllers and their configurations
# Usage: ./list_controllers.sh [--type TYPE]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONTROLLER_TYPE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            CONTROLLER_TYPE="$2"
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

# Get list of controllers
CONTROLLERS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controllers")

# Get list of configurations
CONFIGS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/controller-configs")

# Filter by type if specified
if [ -n "$CONTROLLER_TYPE" ]; then
    FILTERED=$(echo "$CONTROLLERS" | jq --arg type "$CONTROLLER_TYPE" '.[$type] // []')
    CONTROLLERS="{\"$CONTROLLER_TYPE\": $FILTERED}"
fi

# Count configs per controller
CONFIG_COUNTS="{"
FIRST=true
for controller in $(echo "$CONTROLLERS" | jq -r 'to_entries[].value[]'); do
    COUNT=$(echo "$CONFIGS" | jq --arg name "$controller" '[.[] | select(.controller_name == $name)] | length')
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        CONFIG_COUNTS+=","
    fi
    CONFIG_COUNTS+="\"$controller\": $COUNT"
done
CONFIG_COUNTS+="}"

# Output result
cat << EOF
{
    "controllers": $CONTROLLERS,
    "total_configs": $(echo "$CONFIGS" | jq 'length'),
    "configs_per_controller": $CONFIG_COUNTS,
    "configurations": $(echo "$CONFIGS" | jq '[.[] | {id: .id, controller_name: .controller_name, controller_type: .controller_type}]')
}
EOF
