#!/bin/bash
# List all available exchange connectors and current account credentials
# Usage: ./list_connectors.sh [--api-url URL] [--api-user USERNAME] [--api-pass PASSWORD]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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

# Get list of available connectors
CONNECTORS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/connectors")

# Get list of accounts
ACCOUNTS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/accounts")

# Get credentials for each account
ACCOUNT_CREDENTIALS="{"
FIRST_ACCOUNT=true

for account in $(echo "$ACCOUNTS" | jq -r '.[]'); do
    CREDS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/accounts/$account/credentials")

    if [ "$FIRST_ACCOUNT" = true ]; then
        FIRST_ACCOUNT=false
    else
        ACCOUNT_CREDENTIALS+=","
    fi

    ACCOUNT_CREDENTIALS+="\"$account\": $CREDS"
done

ACCOUNT_CREDENTIALS+="}"

# Output combined result
cat << EOF
{
    "available_connectors": $CONNECTORS,
    "total_connectors": $(echo "$CONNECTORS" | jq 'length'),
    "accounts": $ACCOUNTS,
    "configured_credentials": $ACCOUNT_CREDENTIALS
}
EOF
