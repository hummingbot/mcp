#!/bin/bash
# Setup exchange connector with progressive disclosure
#
# Flow:
# 1. No parameters → List available exchanges and current accounts
# 2. --connector only → Show required credential fields
# 3. --connector + --credentials → Select account (shows available accounts)
# 4. --connector + --credentials + --account → Connect (with --force for override)
#
# Usage:
#   ./setup_connector.sh                                    # Step 1: List exchanges
#   ./setup_connector.sh --connector binance                # Step 2: Show required fields
#   ./setup_connector.sh --connector binance --credentials '{"api_key":"...","secret_key":"..."}'  # Step 3: Select account
#   ./setup_connector.sh --connector binance --credentials '{"api_key":"...","secret_key":"..."}' --account master_account  # Step 4: Connect

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
CONNECTOR=""
CREDENTIALS=""
ACCOUNT=""
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector) CONNECTOR="$2"; shift 2 ;;
        --credentials) CREDENTIALS="$2"; shift 2 ;;
        --account) ACCOUNT="$2"; shift 2 ;;
        --force) FORCE=true; shift ;;
        --api-url) API_URL="$2"; shift 2 ;;
        --api-user) API_USER="$2"; shift 2 ;;
        --api-pass) API_PASS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Normalize connector name if provided
if [ -n "$CONNECTOR" ]; then
    CONNECTOR=$(echo "$CONNECTOR" | tr '[:upper:]' '[:lower:]' | tr '-' '_' | tr ' ' '_')
fi

# Determine flow stage
if [ -z "$CONNECTOR" ]; then
    STAGE="list_exchanges"
elif [ -z "$CREDENTIALS" ]; then
    STAGE="show_config"
elif [ -z "$ACCOUNT" ]; then
    STAGE="select_account"
else
    STAGE="connect"
fi

case "$STAGE" in
    list_exchanges)
        # Step 1: List available connectors and current account status
        CONNECTORS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/connectors/")
        ACCOUNTS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/")

        # Get credentials for each account
        ACCOUNT_STATUS="{"
        FIRST=true
        for account in $(echo "$ACCOUNTS" | jq -r '.[]'); do
            CREDS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/$account/credentials")
            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                ACCOUNT_STATUS+=","
            fi
            ACCOUNT_STATUS+="\"$account\": $CREDS"
        done
        ACCOUNT_STATUS+="}"

        cat << EOF
{
    "action": "list_exchanges",
    "message": "Available exchange connectors. Select one to see required credentials.",
    "connectors": $CONNECTORS,
    "total_connectors": $(echo "$CONNECTORS" | jq 'length'),
    "current_accounts": $ACCOUNT_STATUS,
    "next_step": "Call again with --connector CONNECTOR_NAME to see required credential fields",
    "example": "./setup_connector.sh --connector binance"
}
EOF
        ;;

    show_config)
        # Step 2: Show required credential fields for the connector
        CONFIG_MAP=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/connectors/$CONNECTOR/config-map")

        if echo "$CONFIG_MAP" | jq -e '.detail' > /dev/null 2>&1; then
            echo "{\"error\": \"Connector '$CONNECTOR' not found\", \"detail\": $CONFIG_MAP}"
            exit 1
        fi

        # Build example credentials from config map (use -c for compact output)
        EXAMPLE_CREDS=$(echo "$CONFIG_MAP" | jq -c 'to_entries | map({(.key): "your_\(.key)"}) | add')
        REQUIRED_FIELDS=$(echo "$CONFIG_MAP" | jq -c '[to_entries[] | select(.value.required == true) | .key]')
        OPTIONAL_FIELDS=$(echo "$CONFIG_MAP" | jq -c '[to_entries[] | select(.value.required != true) | .key]')
        FIELD_DETAILS=$(echo "$CONFIG_MAP" | jq -c '.')

        # Escape the example credentials for the command example
        EXAMPLE_CREDS_ESCAPED=$(echo "$EXAMPLE_CREDS" | sed 's/"/\\"/g')

        cat << EOF
{
    "action": "show_config",
    "message": "Required credentials for $CONNECTOR. Provide these to continue setup.",
    "connector": "$CONNECTOR",
    "required_fields": $REQUIRED_FIELDS,
    "optional_fields": $OPTIONAL_FIELDS,
    "field_details": $FIELD_DETAILS,
    "example_credentials": $EXAMPLE_CREDS,
    "next_step": "Call again with --credentials JSON to select an account",
    "example": "./setup_connector.sh --connector $CONNECTOR --credentials '$EXAMPLE_CREDS_ESCAPED'"
}
EOF
        ;;

    select_account)
        # Step 3: Show available accounts to select from
        ACCOUNTS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/")

        # Check which accounts already have this connector
        ACCOUNT_STATUS="["
        FIRST=true
        for account in $(echo "$ACCOUNTS" | jq -r '.[]'); do
            CREDS=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/$account/credentials")
            HAS_CONNECTOR=$(echo "$CREDS" | jq -e "index(\"$CONNECTOR\")" > /dev/null 2>&1 && echo "true" || echo "false")

            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                ACCOUNT_STATUS+=","
            fi
            ACCOUNT_STATUS+="{\"account\": \"$account\", \"has_$CONNECTOR\": $HAS_CONNECTOR}"
        done
        ACCOUNT_STATUS+="]"

        cat << EOF
{
    "action": "select_account",
    "message": "Ready to connect $CONNECTOR. Select an account to add credentials to.",
    "connector": "$CONNECTOR",
    "credentials_provided": true,
    "accounts": $ACCOUNT_STATUS,
    "default_account": "master_account",
    "next_step": "Call again with --account ACCOUNT_NAME to complete setup",
    "example": "./setup_connector.sh --connector $CONNECTOR --credentials '...' --account master_account",
    "note": "Use --force to override if connector already exists on the account"
}
EOF
        ;;

    connect)
        # Step 4: Actually connect the exchange

        # Check if credentials already exist
        EXISTING=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/$ACCOUNT/credentials")
        HAS_CONNECTOR=$(echo "$EXISTING" | jq -e "index(\"$CONNECTOR\")" > /dev/null 2>&1 && echo "true" || echo "false")

        if [ "$HAS_CONNECTOR" = "true" ] && [ "$FORCE" = "false" ]; then
            cat << EOF
{
    "action": "requires_confirmation",
    "message": "WARNING: Connector '$CONNECTOR' already exists for account '$ACCOUNT'",
    "account": "$ACCOUNT",
    "connector": "$CONNECTOR",
    "existing_connectors": $EXISTING,
    "warning": "Adding credentials will override the existing connector configuration",
    "next_step": "Add --force to override existing credentials",
    "example": "./setup_connector.sh --connector $CONNECTOR --credentials '...' --account $ACCOUNT --force"
}
EOF
            exit 0
        fi

        # Add credentials via API
        RESPONSE=$(curl -s -X POST \
            -u "$API_USER:$API_PASS" \
            -H "Content-Type: application/json" \
            -d "{\"connector_name\": \"$CONNECTOR\", \"credentials\": $CREDENTIALS}" \
            "$API_URL/accounts/$ACCOUNT/credentials")

        if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
            echo "{\"error\": \"Failed to add credentials\", \"detail\": $RESPONSE}"
            exit 1
        fi

        # Verify credentials were added
        UPDATED=$(curl -s -u "$API_USER:$API_PASS" "$API_URL/accounts/$ACCOUNT/credentials")

        ACTION_TYPE="credentials_added"
        MESSAGE_ACTION="connected"
        if [ "$HAS_CONNECTOR" = "true" ]; then
            ACTION_TYPE="credentials_overridden"
            MESSAGE_ACTION="updated"
        fi

        cat << EOF
{
    "action": "$ACTION_TYPE",
    "message": "Successfully $MESSAGE_ACTION $CONNECTOR exchange to account $ACCOUNT",
    "account": "$ACCOUNT",
    "connector": "$CONNECTOR",
    "was_override": $HAS_CONNECTOR,
    "configured_connectors": $UPDATED,
    "next_step": "Exchange is now ready for trading. Use get_portfolio_overview to verify the connection."
}
EOF
        ;;
esac
