#!/bin/bash
# Get required credential fields for a specific connector
# Usage: ./get_connector_config.sh --connector CONNECTOR_NAME

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector)
            CONNECTOR="$2"
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

if [ -z "$CONNECTOR" ]; then
    echo '{"error": "connector is required. Use --connector CONNECTOR_NAME"}'
    exit 1
fi

# Normalize connector name (lowercase, underscores)
CONNECTOR=$(echo "$CONNECTOR" | tr '[:upper:]' '[:lower:]' | tr '-' '_' | tr ' ' '_')

# Get config map for the connector
CONFIG_MAP=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/connectors/$CONNECTOR/config-map")

# Check for error
if echo "$CONFIG_MAP" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Connector '$CONNECTOR' not found\", \"detail\": $CONFIG_MAP}"
    exit 1
fi

# Build example credentials object
EXAMPLE_CREDS="{"
FIRST=true
for field in $(echo "$CONFIG_MAP" | jq -r '.[]'); do
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        EXAMPLE_CREDS+=","
    fi
    EXAMPLE_CREDS+="\"$field\": \"your_$field\""
done
EXAMPLE_CREDS+="}"

# Output result
cat << EOF
{
    "connector": "$CONNECTOR",
    "required_fields": $CONFIG_MAP,
    "example_credentials": $EXAMPLE_CREDS,
    "documentation_hint": "Generate API keys from the exchange's API management page"
}
EOF
