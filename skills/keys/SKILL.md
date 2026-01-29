---
name: hummingbot-keys
description: Manage exchange API keys and credentials for Hummingbot trading accounts
version: 1.0.0
author: Hummingbot Foundation
triggers:
  - add api key
  - remove api key
  - list exchanges
  - setup exchange
  - connect binance
  - connect coinbase
  - add credentials
---

# Hummingbot Keys Skill

This skill manages exchange API keys and credentials for Hummingbot. It supports listing available exchanges, adding credentials, and removing them.

## Prerequisites

- Hummingbot API server must be running (use the setup skill first)
- API server credentials (username/password)

## Capabilities

### 1. List Available Exchanges

See all supported exchange connectors:

```bash
./scripts/list_connectors.sh
```

Output includes:
- All available exchange connectors (binance, coinbase, kraken, etc.)
- Currently configured connectors per account
- Required credential fields for each connector

### 2. Get Connector Requirements

Before adding credentials, check what fields are required:

```bash
./scripts/get_connector_config.sh --connector binance
```

Example output:
```json
{
    "connector": "binance",
    "required_fields": [
        "binance_api_key",
        "binance_api_secret"
    ]
}
```

### 3. Add Exchange Credentials

Add API keys for an exchange:

```bash
./scripts/add_credentials.sh \
    --connector binance \
    --account master_account \
    --credentials '{"binance_api_key": "YOUR_KEY", "binance_api_secret": "YOUR_SECRET"}'
```

### 4. Remove Exchange Credentials

Remove credentials for an exchange:

```bash
./scripts/remove_credentials.sh \
    --connector binance \
    --account master_account
```

### 5. List Account Credentials

See which exchanges are configured for an account:

```bash
./scripts/list_account_credentials.sh --account master_account
```

## Supported Exchanges

### Centralized Exchanges (CEX)

| Exchange | Connector Name | Required Fields |
|----------|----------------|-----------------|
| Binance | `binance` | api_key, api_secret |
| Binance US | `binance_us` | api_key, api_secret |
| Binance Perpetual | `binance_perpetual` | api_key, api_secret |
| Coinbase | `coinbase_advanced_trade` | api_key, api_secret |
| Kraken | `kraken` | api_key, api_secret |
| KuCoin | `kucoin` | api_key, api_secret, passphrase |
| Gate.io | `gate_io` | api_key, api_secret |
| OKX | `okx` | api_key, api_secret, passphrase |
| Bybit | `bybit` | api_key, api_secret |
| Hyperliquid | `hyperliquid` | api_key, api_secret |

### Decentralized Exchanges (DEX)

DEX connectors are managed through Gateway. See the setup skill for Gateway configuration.

| Exchange | Connector Name | Chain |
|----------|----------------|-------|
| Jupiter | `jupiter` | Solana |
| Raydium | `raydium` | Solana |
| Meteora | `meteora` | Solana |
| Uniswap | `uniswap` | Ethereum/L2s |

## Workflow: Adding Exchange Credentials

When the user wants to add exchange credentials:

1. **List available connectors** to confirm the exchange is supported
2. **Get connector config** to show required credential fields
3. **Prompt for credentials** - never log or echo sensitive values
4. **Add credentials** to the specified account
5. **Verify** the credentials were added successfully

### Example Conversation Flow

**User**: "I want to trade on Binance"

**Agent**:
1. Run `./scripts/get_connector_config.sh --connector binance`
2. Tell user: "To connect Binance, I need your API key and secret. You can generate these at https://www.binance.com/en/my/settings/api-management"
3. User provides credentials
4. Run `./scripts/add_credentials.sh --connector binance --credentials '{"binance_api_key": "...", "binance_api_secret": "..."}'`
5. Confirm: "Binance is now connected to your master_account"

## Security Notes

- **Never log credentials** - credentials should only be passed to scripts, never echoed
- **Use secure input** - when prompting for credentials, use password-style input
- **Credentials are encrypted** - Hummingbot encrypts all stored credentials
- **API key permissions** - recommend users create keys with minimal required permissions

## API Endpoints Used

The scripts call these Hummingbot API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/connectors` | GET | List available connectors |
| `/api/v1/connectors/{name}/config-map` | GET | Get required credential fields |
| `/api/v1/accounts` | GET | List accounts |
| `/api/v1/accounts/{name}/credentials` | GET | List account credentials |
| `/api/v1/accounts/{name}/credentials` | POST | Add credentials |
| `/api/v1/accounts/{name}/credentials/{connector}` | DELETE | Remove credentials |

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid credentials" | Wrong API key/secret | Verify credentials are correct |
| "Connector not found" | Typo in connector name | Use list_connectors to see valid names |
| "Account not found" | Account doesn't exist | Use default "master_account" or create account |
| "Credentials already exist" | Connector already configured | Use --force to override or remove first |
