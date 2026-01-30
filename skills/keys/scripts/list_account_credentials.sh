#!/bin/bash
# List credentials configured for an account
# Usage: ./list_account_credentials.sh [--account ACCOUNT]

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
ACCOUNT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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

# If no account specified, list all accounts and their credentials
if [ -z "$ACCOUNT" ]; then
    ACCOUNTS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/")

    RESULT="{"
    FIRST=true

    for account in $(echo "$ACCOUNTS" | jq -r '.[]'); do
        CREDS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/$account/credentials")

        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            RESULT+=","
        fi

        RESULT+="\"$account\": {\"connectors\": $CREDS, \"count\": $(echo "$CREDS" | jq 'length')}"
    done

    RESULT+="}"

    cat << EOF
{
    "accounts": $ACCOUNTS,
    "total_accounts": $(echo "$ACCOUNTS" | jq 'length'),
    "credentials_by_account": $RESULT
}
EOF
else
    # Get credentials for specific account
    CREDS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/$ACCOUNT/credentials")

    # Check for error
    if echo "$CREDS" | jq -e '.detail' > /dev/null 2>&1; then
        echo "{\"error\": \"Account '$ACCOUNT' not found\", \"detail\": $CREDS}"
        exit 1
    fi

    cat << EOF
{
    "account": "$ACCOUNT",
    "connectors": $CREDS,
    "count": $(echo "$CREDS" | jq 'length')
}
EOF
fi
