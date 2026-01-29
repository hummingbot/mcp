#!/bin/bash
# Remove exchange credentials from an account
# Usage: ./remove_credentials.sh --connector CONNECTOR [--account ACCOUNT]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
ACCOUNT="master_account"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector)
            CONNECTOR="$2"
            shift 2
            ;;
        --account)
            ACCOUNT="$2"
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
if [ -z "$CONNECTOR" ]; then
    echo '{"error": "connector is required. Use --connector CONNECTOR_NAME"}'
    exit 1
fi

# Normalize connector name
CONNECTOR=$(echo "$CONNECTOR" | tr '[:upper:]' '[:lower:]' | tr '-' '_' | tr ' ' '_')

# Check if credentials exist
EXISTING=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/accounts/$ACCOUNT/credentials")
if ! echo "$EXISTING" | jq -e "index(\"$CONNECTOR\")" > /dev/null 2>&1; then
    cat << EOF
{
    "error": "Credentials for '$CONNECTOR' do not exist on account '$ACCOUNT'",
    "existing_connectors": $EXISTING
}
EOF
    exit 1
fi

# Remove credentials via API
RESPONSE=$(curl -s -X DELETE \
    -u "$API_USER:$API_PASS" \
    "$API_URL/api/v1/accounts/$ACCOUNT/credentials/$CONNECTOR")

# Verify credentials were removed
UPDATED=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/accounts/$ACCOUNT/credentials")

cat << EOF
{
    "status": "success",
    "action": "credentials_removed",
    "connector": "$CONNECTOR",
    "account": "$ACCOUNT",
    "remaining_connectors": $UPDATED
}
EOF
