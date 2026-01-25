"""
Add Exchange prompt - Guide users through connecting exchange accounts.
"""


def register_add_exchange_prompts(mcp):
    """Register exchange connection prompts."""

    @mcp.prompt()
    def add_exchange() -> str:
        """Guide the user through connecting an exchange account with API keys.

        This prompt helps users:
        1. Choose an exchange to connect
        2. Understand what credentials are needed
        3. Safely add their API keys
        4. Verify the connection works
        """
        return """# Connect an Exchange Account

You are helping the user connect their exchange account to Hummingbot. Follow this guide carefully.

## Security Warning

**IMPORTANT**: API keys are sensitive credentials. Before proceeding:
- Never share your API keys with anyone
- Use API keys with trading permissions only (no withdrawal)
- Consider using IP whitelisting on your exchange
- For testing, start with a small amount of funds

## Step 1: List Available Exchanges

See all supported exchanges:

```
Use setup_connector() with no arguments
```

This shows:
- Spot exchanges (e.g., binance, coinbase, kucoin)
- Perpetual/futures exchanges (e.g., binance_perpetual, hyperliquid_perpetual)
- DEX connectors (via Gateway)

## Step 2: Choose Your Exchange

Common exchanges and their connector names:
- **Binance Spot**: `binance`
- **Binance Futures**: `binance_perpetual`
- **Coinbase**: `coinbase`
- **KuCoin Spot**: `kucoin`
- **KuCoin Futures**: `kucoin_perpetual`
- **Hyperliquid**: `hyperliquid_perpetual`
- **Gate.io**: `gate_io`
- **OKX**: `okx`

## Step 3: Get Required Credentials

See what credentials are needed for your chosen exchange:

```
Use setup_connector(connector="<exchange_name>")
```

This shows the exact fields required (e.g., api_key, api_secret, etc.)

## Step 4: Generate API Keys on Exchange

Go to your exchange and create API keys:

### Binance
1. Log in to Binance
2. Go to API Management (Profile > API Management)
3. Create new API key
4. Enable "Spot & Margin Trading" (and Futures if needed)
5. Consider adding IP restriction
6. Save API Key and Secret Key

### Coinbase
1. Log in to Coinbase
2. Go to Settings > API
3. Create new API key
4. Select required permissions (Trade)
5. Save API Key, Secret, and Passphrase

### KuCoin
1. Log in to KuCoin
2. Go to API Management
3. Create new API
4. Set trading permissions
5. Save API Key, Secret, and Passphrase

### Other Exchanges
Each exchange has similar process - look for "API" or "API Management" in settings.

## Step 5: Add Credentials to Hummingbot

Add your credentials (replace with your actual keys):

```
Use setup_connector(
    connector="binance",
    credentials={
        "api_key": "your_api_key_here",
        "api_secret": "your_api_secret_here"
    },
    account="master_account"
)
```

For exchanges requiring passphrase:

```
Use setup_connector(
    connector="kucoin",
    credentials={
        "api_key": "your_api_key_here",
        "api_secret": "your_api_secret_here",
        "passphrase": "your_passphrase_here"
    },
    account="master_account"
)
```

## Step 6: Verify Connection

Check that your exchange is connected and has balances:

```
Use get_portfolio_overview()
```

You should see your balances from the connected exchange.

Test getting prices:

```
Use get_prices(connector_name="binance", trading_pairs=["BTC-USDT", "ETH-USDT"])
```

## Step 7: Test Trading (Optional)

If you want to verify trading works, place a small test order:

```
Use place_order(
    connector_name="binance",
    trading_pair="BTC-USDT",
    trade_type="BUY",
    amount="$10",  # Small test amount
    order_type="MARKET"
)
```

## Multiple Accounts

You can set up multiple accounts for different purposes:

```
Use setup_connector(
    connector="binance",
    credentials={...},
    account="trading_account"
)

Use setup_connector(
    connector="kucoin",
    credentials={...},
    account="trading_account"
)
```

## Updating Credentials

If you need to update API keys:

```
Use setup_connector(
    connector="binance",
    credentials={
        "api_key": "new_api_key",
        "api_secret": "new_api_secret"
    },
    account="master_account",
    confirm_override=True  # Required to update existing
)
```

## Troubleshooting

**"Invalid API key"**: Double-check your key/secret are correct, no extra spaces

**"Permission denied"**: Ensure your API key has trading permissions enabled

**"IP not allowed"**: If you set IP restriction, add your current IP to the whitelist

**Connection timeout**: Exchange might be temporarily unavailable, try again

## Next Steps

After connecting your exchange:
- Use `get_portfolio_overview()` to see your balances
- Use `first_bot` prompt to create your first trading bot
- Use `get_prices()` to check market data

Which exchange would you like to connect?
"""

    @mcp.prompt()
    def add_wallet() -> str:
        """Guide the user through connecting a blockchain wallet for DEX trading."""
        return """# Connect a Blockchain Wallet for DEX Trading

You are helping the user connect a blockchain wallet to use decentralized exchanges (DEXs) through Hummingbot Gateway.

## Prerequisites

1. **Gateway must be running**. Check status:

```
Use manage_gateway_container(action="get_status")
```

If not running, start Gateway:

```
Use manage_gateway_container(
    action="start",
    config={
        "passphrase": "your_gateway_passphrase",
        "image": "hummingbot/gateway:latest"
    }
)
```

2. **You need a wallet with funds** on the blockchain you want to use

## Supported Blockchains

Gateway supports multiple blockchains:
- **Solana**: Fast, low fees (DEXs: Jupiter, Raydium, Meteora)
- **Ethereum**: Most liquidity (DEXs: Uniswap, 0x)
- **Other EVM chains**: Polygon, Arbitrum, BSC, etc.

## Step 1: Prepare Your Wallet

### For Solana
- Export your private key from Phantom, Solflare, or other wallet
- Private key is a base58 encoded string

### For Ethereum/EVM
- Export your private key from MetaMask or other wallet
- Private key is a hex string (starts with 0x or without)

**WARNING**: Your private key gives full access to your wallet. Only use wallets with funds you're willing to risk.

## Step 2: Add Wallet to Gateway

Add your wallet:

```
Use manage_gateway_config(
    resource_type="wallets",
    action="add",
    chain="solana",  # or "ethereum"
    private_key="your_private_key_here"
)
```

## Step 3: Verify Wallet Added

List configured wallets:

```
Use manage_gateway_config(resource_type="wallets", action="list")
```

You should see your wallet address listed.

## Step 4: Check Network Configuration

Verify the network is configured:

```
Use manage_gateway_config(resource_type="networks", action="list")
```

For Solana mainnet, the network ID is typically: `solana-mainnet-beta`

## Step 5: Test DEX Access

### For Swaps (Jupiter on Solana)

Get a price quote:

```
Use manage_gateway_swaps(
    action="quote",
    connector="jupiter",
    network="solana-mainnet-beta",
    trading_pair="SOL-USDC",
    side="BUY",
    amount="1"
)
```

### For CLMM/LP Positions (Meteora, Raydium)

List available pools:

```
Use explore_gateway_clmm_pools(
    action="list_pools",
    connector="meteora",
    search_term="SOL"
)
```

## Step 6: Execute a Test Swap (Optional)

Execute a small test swap:

```
Use manage_gateway_swaps(
    action="execute",
    connector="jupiter",
    network="solana-mainnet-beta",
    trading_pair="SOL-USDC",
    side="SELL",
    amount="0.01",  # Small test amount
    slippage_pct="1.0"
)
```

## Managing Tokens

Add custom tokens if needed:

```
Use manage_gateway_config(
    resource_type="tokens",
    action="add",
    network_id="solana-mainnet-beta",
    token_address="<token_mint_address>",
    token_symbol="TOKEN",
    token_decimals=9
)
```

## Removing a Wallet

If you need to remove a wallet:

```
Use manage_gateway_config(
    resource_type="wallets",
    action="delete",
    chain="solana",
    wallet_address="your_wallet_address"
)
```

## Security Best Practices

1. **Use a dedicated trading wallet** - Don't use your main wallet
2. **Only fund what you need** - Keep minimum necessary balance
3. **Revoke token approvals** - For EVM chains, revoke unused approvals
4. **Monitor transactions** - Check your wallet activity regularly

## Troubleshooting

**"Wallet not found"**: Check the chain name is correct (solana, ethereum, etc.)

**"Insufficient balance"**: Ensure you have enough native token for gas (SOL, ETH)

**"Network not configured"**: Add the network using manage_gateway_config

**"Transaction failed"**: Check gateway logs: `manage_gateway_container(action="get_logs")`

## Next Steps

After connecting your wallet:
- Explore available DEX pools with `explore_gateway_clmm_pools`
- Get swap quotes with `manage_gateway_swaps(action="quote", ...)`
- Check your portfolio with `get_portfolio_overview()`

Which blockchain would you like to connect?
"""
