"""
First Trade / Executor prompts - Guide users through their first trades using executors.
"""


def register_first_bot_prompts(mcp):
    """Register first trade/executor prompts."""

    @mcp.prompt()
    def first_trade() -> str:
        """Guide the user through their first trade using executors.

        This prompt helps users:
        1. Start with a simple order using Order Executor
        2. Learn about Position Executor with Triple Barrier risk management
        3. Monitor and manage positions
        """
        return """# Your First Trade with Hummingbot

You are helping the user execute their first trade using Hummingbot's executor system.
Executors are smart trading algorithms that handle order placement and position management automatically.

## Prerequisites Check

Before trading, verify:
1. Hummingbot API is running (use `check_status` prompt if unsure)
2. At least one exchange is connected with funds

Check connected exchanges and balances:
```
Use get_portfolio_overview() to see balances across all exchanges
```

If no exchange is connected, use the `add_exchange` prompt first.

---

## Part 1: Your First Order (Order Executor)

Let's start simple. The **Order Executor** places a single order with retry logic - perfect for your first trade.

### Step 1: Get Current Price

```
Use get_prices(connector_name="binance_perpetual", trading_pairs=["BTC-USDT"])
```

### Step 2: Place Your First Order

**Example: Buy 0.001 BTC at market price**

```
Use create_executor({
    "type": "order_executor",
    "connector_name": "binance_perpetual",
    "trading_pair": "BTC-USDT",
    "side": "BUY",
    "amount": "0.001"
})
```

**Parameters:**
- `type`: "order_executor" for simple orders
- `connector_name`: Your exchange (e.g., "binance_perpetual", "hyperliquid_perpetual")
- `trading_pair`: The pair to trade (e.g., "BTC-USDT")
- `side`: "BUY" or "SELL"
- `amount`: Order size in base currency

### Step 3: Verify Your Order

```
Use list_executors(is_active=True)
Use get_portfolio_overview()
```

**Congratulations!** You've placed your first order. The Order Executor handles:
- Order submission with retry on failures
- Status tracking
- Basic error handling

---

## Part 2: Advanced Trades with Position Executor

Now let's level up. The **Position Executor** adds professional risk management using the **Triple Barrier Method**.

### What is the Triple Barrier Method?

The Triple Barrier Method was invented by **Marcos López de Prado**, a renowned quantitative researcher. It's described in his book "Advances in Financial Machine Learning" and documented at https://www.quantresearch.org/Innovations.htm

**The Three Barriers:**

```
Price
↑
│     ┌─────────────────────────────────────────────────┐
│     │                                                 │
│     │  ═══════════════════════════════════════════    │ ← Take-Profit Barrier (+1)
│     │                     ╭─╮                         │   (Upper horizontal barrier)
│     │                    ╱   ╲      ╭─────            │
│     │              ╭────╯     ╰╮   ╱                  │
│     │             ╱             ╲ ╱                   │
│     │  ●────────╯               ╰╯                    │ ← Entry Point
│     │  Entry                                          │
│     │                                                 │
│     │  ═══════════════════════════════════════════    │ ← Stop-Loss Barrier (-1)
│     │                                                 │   (Lower horizontal barrier)
│     └────────────────────────────────────────────|────┘
│                                              Time Limit
│                                              Barrier (0)
│                                         (Vertical barrier)
└─────────────────────────────────────────────────────────→ Time
```

**How it works:**
1. **Take-Profit (+1)**: Position closes automatically when price rises to your target
2. **Stop-Loss (-1)**: Position closes automatically when price falls to your limit
3. **Time Limit (0)**: Position closes automatically after time expires (regardless of profit/loss)

The position exits when it touches ANY of the three barriers first.

### Why Use Triple Barrier?

- **Defined Risk**: You know your maximum loss before entering
- **Automatic Execution**: No need to watch charts constantly
- **Prevents "Forever Positions"**: Time limit ensures positions don't stay open indefinitely
- **Backtesting Labels**: The method also provides clear labels (+1, -1, 0) for machine learning

### Step 1: Create a Position with Risk Management

**Example: Long BTC with 2% stop loss and 4% take profit**

```
Use create_executor({
    "type": "position_executor",
    "connector_name": "binance_perpetual",
    "trading_pair": "BTC-USDT",
    "side": "BUY",
    "amount": "0.001",
    "triple_barrier_config": {
        "stop_loss": "0.02",
        "take_profit": "0.04",
        "time_limit": 86400
    }
})
```

**Parameters explained:**
- `side`: "BUY" for long, "SELL" for short
- `amount`: Position size in base currency
- `triple_barrier_config`:
  - `stop_loss`: Exit if loss reaches this % (0.02 = 2%)
  - `take_profit`: Exit if profit reaches this % (0.04 = 4%)
  - `time_limit`: Auto-close after this many seconds (86400 = 24 hours)

### Step 2: Monitor Your Position

```
Use list_executors(is_active=True)
Use get_executor(executor_id="<your_executor_id>")
```

### Step 3: Managing the Position

**To close early (market exit):**
```
Use stop_executor(executor_id="<your_executor_id>", keep_position=False)
```

**To stop monitoring but keep position:**
```
Use stop_executor(executor_id="<your_executor_id>", keep_position=True)
```

---

## Risk/Reward Guidelines

| Style | Stop Loss | Take Profit | Risk:Reward |
|-------|-----------|-------------|-------------|
| Conservative | 1% | 2-3% | 1:2-3 |
| Moderate | 2% | 4-6% | 1:2-3 |
| Aggressive | 3% | 9%+ | 1:3+ |

**Key Principle**: Your take profit should be larger than your stop loss to be profitable over time, even if you're wrong more than 50% of the time.

---

## Next Steps

After mastering these:
1. **Grid Executor**: For range-bound markets
2. **DCA Executor**: For gradual position building
3. **TWAP Executor**: For large orders with minimal market impact

Use `get_executor_types()` to see all available executors.

Which exchange and trading pair would you like to trade? I'll help you place your first order.
"""

    @mcp.prompt()
    def list_strategies() -> str:
        """List and explain all available executor types."""
        return """# Available Executor Types

You are helping the user understand the different executor types available in Hummingbot.

## Get Available Types

First, let's see what executor types are available:

```
Use get_executor_types()
```

## Executor Types Overview

### 1. Order Executor (Simplest)

**What it does:** Places a single order with retry logic.

**Best for:**
- Simple buy/sell orders
- Getting started with trading
- When you don't need automatic stop loss/take profit

**Key parameters:**
- `side`: BUY or SELL
- `amount`: Order size
- Optional: `price` for limit orders

**Example:**
```json
{
    "type": "order_executor",
    "connector_name": "binance_perpetual",
    "trading_pair": "BTC-USDT",
    "side": "BUY",
    "amount": "0.01"
}
```

Get full schema: `get_executor_schema("order_executor")`

---

### 2. Position Executor (Most Popular)

**What it does:** Opens a position with automatic risk management using the **Triple Barrier Method** (invented by Marcos López de Prado).

**The Three Barriers:**
```
    Take-Profit ═══════════════════════════════════  (+1)
                        Price Movement
    Entry ●─────────────────────────────────────
                                            │
    Stop-Loss ═════════════════════════════════════  (-1)
                                            │
                                      Time Limit (0)
```

Position exits when ANY barrier is touched:
- **+1**: Price hits take profit
- **-1**: Price hits stop loss
- **0**: Time limit expires

**Best for:**
- Directional trading (going long or short)
- Trades with defined risk management
- Set-and-forget trading

**Key parameters:**
- `side`: BUY (long) or SELL (short)
- `amount`: Position size
- `triple_barrier_config`: Stop loss, take profit, time limit

**Example:**
```json
{
    "type": "position_executor",
    "connector_name": "binance_perpetual",
    "trading_pair": "BTC-USDT",
    "side": "BUY",
    "amount": "0.01",
    "triple_barrier_config": {
        "stop_loss": "0.02",
        "take_profit": "0.04",
        "time_limit": 3600
    }
}
```

Get full schema: `get_executor_schema("position_executor")`

---

### 3. Grid Executor

**What it does:** Places multiple buy/sell orders at different price levels.

**Best for:**
- Range-bound markets
- Accumulating or distributing positions
- Markets without strong trends

**Key parameters:**
- `start_price`, `end_price`: Price range for the grid
- `n_levels`: Number of grid levels
- `total_amount_quote`: Total capital to deploy

Get full schema: `get_executor_schema("grid_executor")`

---

### 4. DCA Executor

**What it does:** Dollar-cost averages into a position over time or price levels.

**Best for:**
- Reducing timing risk
- Accumulating long-term positions
- Averaging into volatile markets

**Key parameters:**
- `n_levels`: Number of DCA entries
- `total_amount_quote`: Total to invest
- Time or price intervals between entries

Get full schema: `get_executor_schema("dca_executor")`

---

### 5. TWAP Executor

**What it does:** Executes a large order in smaller chunks over time.

**Best for:**
- Large orders that would move the market
- Minimizing market impact
- Algorithmic order execution

**Key parameters:**
- `total_duration`: Time to execute over
- `n_levels`: Number of sub-orders
- `total_amount_quote`: Total order size

Get full schema: `get_executor_schema("twap_executor")`

---

### 6. Arbitrage Executor

**What it does:** Exploits price differences between exchanges.

**Best for:**
- Risk-free profit from price discrepancies
- Multi-exchange setups
- Professional market making

Get full schema: `get_executor_schema("arbitrage_executor")`

---

### 7. XEMM Executor

**What it does:** Cross-exchange market making - provide liquidity on one exchange, hedge on another.

**Best for:**
- Professional market making
- Multi-exchange arbitrage
- Advanced trading strategies

Get full schema: `get_executor_schema("xemm_executor")`

---

## Choosing the Right Executor

| Goal | Recommended Executor |
|------|---------------------|
| Simple order | Order Executor |
| Trade with stop loss/take profit | Position Executor |
| Sideways/ranging market | Grid Executor |
| Build position gradually | DCA Executor |
| Large order execution | TWAP Executor |
| Multi-exchange profit | Arbitrage / XEMM |

**For beginners:** Start with Order Executor, then graduate to Position Executor.

## Get Configuration Details

To see all parameters for any executor type:

```
Use get_executor_schema("<executor_type>")
```

Which executor type interests you? I can help you understand the configuration and create one.
"""

    @mcp.prompt()
    def quick_trade() -> str:
        """Quick reference for placing common trades."""
        return """# Quick Trade Reference

You are helping the user execute common trades quickly.

## Simple Order (Order Executor)

**Market buy:**
```
Use create_executor({
    "type": "order_executor",
    "connector_name": "<exchange>",
    "trading_pair": "<PAIR>",
    "side": "BUY",
    "amount": "<size>"
})
```

**Market sell:**
```
Use create_executor({
    "type": "order_executor",
    "connector_name": "<exchange>",
    "trading_pair": "<PAIR>",
    "side": "SELL",
    "amount": "<size>"
})
```

---

## Position with Risk Management (Position Executor)

**Long with stop loss/take profit:**
```
Use create_executor({
    "type": "position_executor",
    "connector_name": "<exchange>",
    "trading_pair": "<PAIR>",
    "side": "BUY",
    "amount": "<size>",
    "triple_barrier_config": {
        "stop_loss": "0.02",
        "take_profit": "0.04",
        "time_limit": 86400
    }
})
```

**Short with stop loss/take profit:**
```
Use create_executor({
    "type": "position_executor",
    "connector_name": "<exchange>",
    "trading_pair": "<PAIR>",
    "side": "SELL",
    "amount": "<size>",
    "triple_barrier_config": {
        "stop_loss": "0.02",
        "take_profit": "0.04",
        "time_limit": 86400
    }
})
```

---

## Check Before Trading

1. **Get current price:**
   ```
   Use get_prices(connector_name="<exchange>", trading_pairs=["<PAIR>"])
   ```

2. **Check your balance:**
   ```
   Use get_portfolio_overview()
   ```

3. **See active positions:**
   ```
   Use list_executors(is_active=True)
   ```

---

## Common Exchanges

- Spot: `binance`, `coinbase`, `kucoin`
- Perpetuals: `binance_perpetual`, `hyperliquid_perpetual`, `bybit_perpetual`

## Common Pairs

- BTC-USDT, ETH-USDT, SOL-USDT
- BTC-USD, ETH-USD (for USD-margined perpetuals)

---

## Stop Loss / Take Profit Guidelines

| Risk Level | Stop Loss | Take Profit | Ratio |
|------------|-----------|-------------|-------|
| Conservative | 1% | 2% | 1:2 |
| Moderate | 2% | 4% | 1:2 |
| Aggressive | 3% | 6% | 1:2 |

---

## Manage Positions

**List active:**
```
Use list_executors(is_active=True)
```

**Close position:**
```
Use stop_executor(executor_id="<id>", keep_position=False)
```

**Get summary:**
```
Use get_executors_summary()
```

What would you like to trade?
"""
