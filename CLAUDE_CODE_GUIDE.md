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

---

## Trading with Executors

Executors are smart trading algorithms that handle order placement, position management, and risk controls. This is the primary way to execute trades.

### Executor Progression

| Level | Executor | Description |
|-------|----------|-------------|
| 1. Beginner | `order_executor` | Simple order placement with retry logic |
| 2. Intermediate | `position_executor` | Positions with automatic stop loss, take profit, time limit |
| 3. Advanced | `grid_executor`, `dca_executor`, `twap_executor` | Sophisticated multi-order strategies |
| 4. Pro | `arbitrage_executor`, `xemm_executor` | Multi-exchange strategies |

---

## Step 1: Your First Order (Order Executor)

Start with the simplest executor - place a market order:

**Buy BTC:**
```
Create an order executor to buy 0.001 BTC on Binance perpetual
```

**Sell ETH:**
```
Create an order executor to sell 0.1 ETH on Hyperliquid
```

The Order Executor:
- Places your order with automatic retry on failures
- Tracks order status
- Handles basic error recovery

---

## Step 2: Trades with Risk Management (Position Executor)

Once comfortable with basic orders, graduate to Position Executor for professional risk management.

### The Triple Barrier Method

Position Executor uses the **Triple Barrier Method**, invented by **Marcos López de Prado** (documented at https://www.quantresearch.org/Innovations.htm).

![Triple Barrier Method](docs/triple_barrier_method.webp)

**The Three Barriers:**

| Barrier | Trigger | Label | Description |
|---------|---------|-------|-------------|
| Take-Profit | Price rises to target | +1 | Upper horizontal barrier (green) |
| Stop-Loss | Price falls to limit | -1 | Lower horizontal barrier (red) |
| Time Limit | Time expires | 0 | Vertical barrier (blue) |

The position automatically closes when ANY barrier is touched first.

### Position Executor Examples

**Long with stop loss and take profit:**
```
Create a position executor to buy 0.01 BTC on Binance perpetual with:
- 2% stop loss
- 4% take profit
- 24 hour time limit
```

**Short ETH with risk management:**
```
Open a short position on ETH-USDT with 0.1 ETH, 3% stop loss, 6% take profit
```

### Why Triple Barrier?

1. **Defined Risk**: Know your maximum loss before entering
2. **Automatic Execution**: No need to watch charts constantly
3. **Prevents "Forever Positions"**: Time limit closes stale positions
4. **Machine Learning Ready**: Clear labels (+1, -1, 0) for backtesting

---

## All Executor Types

| Type | Description | Use Case |
|------|-------------|----------|
| `order_executor` | Single order with retry logic | Simple buy/sell |
| `position_executor` | Position with Triple Barrier risk management | Directional trading |
| `grid_executor` | Multiple orders at price levels | Range-bound markets |
| `dca_executor` | Dollar-cost averaging entries | Gradual accumulation |
| `twap_executor` | Time-weighted order execution | Large orders |
| `arbitrage_executor` | Cross-exchange arbitrage | Price discrepancies |
| `xemm_executor` | Cross-exchange market making | Liquidity provision |

---

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

---

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

---

## Risk Management Guidelines

### Stop Loss / Take Profit Ratios

| Style | Stop Loss | Take Profit | Risk:Reward |
|-------|-----------|-------------|-------------|
| Conservative | 1% | 2-3% | 1:2-3 |
| Moderate | 2% | 4-6% | 1:2-3 |
| Aggressive | 3% | 9%+ | 1:3+ |

**Key Principle**: Take profit should exceed stop loss to be profitable over time, even with <50% win rate.

### Best Practices

1. **Start with Order Executor** - Master simple orders first
2. **Graduate to Position Executor** - Add risk management
3. **Always use stop losses** - Triple Barrier makes this easy
4. **Start small** - Test with small amounts before scaling
5. **Check balances** - Ensure sufficient funds before trading
6. **Monitor executors** - Use `list_executors` to track positions

---

## Configuration

### Setting Leverage

```
Set leverage to 5x for BTC-USDT on Binance perpetual
```

### Position Mode

```
Set position mode to hedge on Binance perpetual
```

### View Executor Schema

To see all configuration options:

```
Show me the configuration options for position_executor
```

---

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

### View Logs

```
Show me the logs for my active bots
```

---

## Resources

- [Hummingbot Documentation](https://hummingbot.org/docs/)
- [Triple Barrier Method - Marcos López de Prado](https://www.quantresearch.org/Innovations.htm)
- [Hummingbot API Repository](https://github.com/hummingbot/hummingbot-api)
- [MCP Server Repository](https://github.com/hummingbot/mcp)
