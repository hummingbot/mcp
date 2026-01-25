# Hummingbot MCP - Claude Code User Guide

This guide shows Claude Code users how to use the Hummingbot MCP server for cryptocurrency trading.

## Quick Start

Once the MCP server is configured, you can interact with Hummingbot using natural language. Claude Code has access to all trading tools automatically.

### Check Your Setup

```
Show me my portfolio overview
```

```
What exchanges do I have connected?
```

### Connect an Exchange

```
Help me connect my Binance account
```

The MCP server will guide you through the credential setup process.

## Trading with Executors

Executors are smart trading algorithms that handle order placement, position management, and risk controls automatically. This is the primary way to execute trades.

### Available Executor Types

| Type | Description | Use Case |
|------|-------------|----------|
| `position_executor` | Single position with stop loss, take profit, time limit | Directional trading with risk management |
| `grid_executor` | Grid trading with multiple buy/sell levels | Range-bound market trading |
| `dca_executor` | Dollar-cost averaging with multiple entries | Gradual position building |
| `twap_executor` | Time-weighted average price execution | Large orders with minimal market impact |
| `arbitrage_executor` | Cross-exchange price arbitrage | Exploiting price differences |
| `xemm_executor` | Cross-exchange market making | Providing liquidity across exchanges |

### Position Executor Example

The position executor is the most common way to place a trade with built-in risk management.

**Example: Long BTC with stop loss and take profit**

```
Create a position executor to buy 0.01 BTC on Binance perpetual with:
- 2% stop loss
- 4% take profit
- 1 hour time limit
```

This creates an executor with:
- Automatic stop loss at -2%
- Automatic take profit at +4%
- Position closes after 1 hour if neither is hit

**Example: Short ETH with trailing stop**

```
Open a short position on ETH-USDT with 0.1 ETH, 3% trailing stop
```

### Grid Executor Example

```
Set up a grid executor for SOL-USDT between $150-$200 with 10 grid levels and $100 per level
```

### DCA Executor Example

```
Create a DCA executor to accumulate 1 ETH over 24 hours in 6 orders
```

## Managing Executors

### List Active Executors

```
Show me all my active executors
```

```
List executors for BTC-USDT
```

### Get Executor Details

```
Show me details of executor abc123
```

### Stop an Executor

```
Stop executor abc123
```

```
Stop executor abc123 but keep the position open
```

### Get Summary Statistics

```
Show me my executor performance summary
```

## Quick Reference Commands

### Market Data

```
What's the price of BTC on Binance?
```

```
Show me the ETH-USDT order book on Hyperliquid
```

```
Get 1-hour candles for SOL-USDT
```

```
What's the funding rate for BTC perpetual?
```

### Portfolio

```
Show my balances
```

```
Show my open positions
```

```
Show my active orders
```

### Simple Orders (Without Executor)

For quick market orders without risk management:

```
Buy $100 of ETH on Binance
```

```
Sell 0.5 SOL at market price
```

## Configuration Tips

### Setting Leverage

```
Set leverage to 5x for BTC-USDT on Binance perpetual
```

### Position Mode

```
Set position mode to hedge on Binance perpetual
```

## Executor Configuration Schema

To see all available options for an executor type:

```
Show me the configuration options for position_executor
```

### Key Position Executor Fields

| Field | Required | Description |
|-------|----------|-------------|
| `connector_name` | Yes | Exchange (e.g., "binance_perpetual") |
| `trading_pair` | Yes | Pair (e.g., "BTC-USDT") |
| `side` | Yes | 1=BUY, 2=SELL |
| `amount` | Yes | Position size in base currency |
| `entry_price` | No | Limit price (market if omitted) |
| `leverage` | No | Leverage multiplier (default: 1) |
| `triple_barrier_config.stop_loss` | No | Stop loss as decimal (0.02 = 2%) |
| `triple_barrier_config.take_profit` | No | Take profit as decimal (0.04 = 4%) |
| `triple_barrier_config.time_limit` | No | Time limit in seconds |

## Best Practices

1. **Always use stop losses** - Position executors make this easy with triple barrier config
2. **Start small** - Test with small amounts before scaling up
3. **Check your balances** - Ensure sufficient funds before creating executors
4. **Monitor active executors** - Use `list_executors` to track your positions
5. **Use appropriate executor types** - Grid for ranging markets, position for directional trades

## Troubleshooting

### "Cannot connect to API"

```
Check the Hummingbot API status
```

### "Exchange not configured"

```
Help me connect my exchange account
```

### "Insufficient balance"

```
Show my balances on Binance
```

### View Executor Logs

```
Show me the logs for my active bots
```

## Advanced: Bot Deployment

For more complex strategies, you can deploy full bots with controllers:

```
Show me available trading strategies
```

```
Help me deploy a market making bot
```

Controllers provide more sophisticated logic but executors are recommended for most trading needs.

## Resources

- [Hummingbot Documentation](https://hummingbot.org/docs/)
- [Hummingbot API Repository](https://github.com/hummingbot/hummingbot-api)
- [MCP Server Repository](https://github.com/hummingbot/mcp)
