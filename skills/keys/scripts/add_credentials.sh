#!/bin/bash
# Add exchange credentials to an account
# Usage: ./add_credentials.sh --connector CONNECTOR --credentials '{"key": "value"}' [--account ACCOUNT] [--force]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
CREDENTIALS=""
ACCOUNT="master_account"
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector)
            CONNECTOR="$2"
            shift 2
            ;;
        --credentials)
            CREDENTIALS="$2"
            shift 2
            ;;
        --account)
            ACCOUNT="$2"
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
if [ -z "$CONNECTOR" ]; then
    echo '{"error": "connector is required. Use --connector CONNECTOR_NAME"}'
    exit 1
fi

if [ -z "$CREDENTIALS" ]; then
    echo '{"error": "credentials is required. Use --credentials JSON_OBJECT"}'
    exit 1
fi

# Normalize connector name
CONNECTOR=$(echo "$CONNECTOR" | tr '[:upper:]' '[:lower:]' | tr '-' '_' | tr ' ' '_')

# Check if credentials already exist
EXISTING=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/accounts/$ACCOUNT/credentials")
if echo "$EXISTING" | jq -e "index(\"$CONNECTOR\")" > /dev/null 2>&1; then
    if [ "$FORCE" = false ]; then
        cat << EOF
{
    "error": "Credentials for '$CONNECTOR' already exist on account '$ACCOUNT'",
    "action_required": "Use --force to override existing credentials",
    "existing_connectors": $EXISTING
}
EOF
        exit 1
    fi
fi

# Add credentials via API
RESPONSE=$(curl -s -X POST \
    -u "$API_USER:$API_PASS" \
    -H "Content-Type: application/json" \
    -d "{\"connector_name\": \"$CONNECTOR\", \"credentials\": $CREDENTIALS}" \
    "$API_URL/api/v1/accounts/$ACCOUNT/credentials")

# Check for error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "{\"error\": \"Failed to add credentials\", \"detail\": $RESPONSE}"
    exit 1
fi

# Verify credentials were added
UPDATED=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/accounts/$ACCOUNT/credentials")

cat << EOF
{
    "status": "success",
    "action": "credentials_added",
    "connector": "$CONNECTOR",
    "account": "$ACCOUNT",
    "was_override": $FORCE,
    "configured_connectors": $UPDATED
}
EOF
