"""
First Trade / Executor prompts - Guide users through their first trades using executors.
"""


def register_first_bot_prompts(mcp):
    """Register first trade/executor prompts."""

    @mcp.prompt()
    def first_trade() -> str:
        """Guide the user through their first trade using executors.

        This prompt helps users:
        1. Understand executors (smart trading algorithms)
        2. Choose the right executor type
        3. Create their first position with risk management
        4. Monitor and manage the position
        """
        return """# Your First Trade with Hummingbot

You are helping the user execute their first trade using Hummingbot's executor system.
Executors are smart trading algorithms that handle order placement and risk management automatically.

## Prerequisites Check

Before trading, verify:
1. Hummingbot API is running (use `check_status` prompt if unsure)
2. At least one exchange is connected with funds

Check connected exchanges and balances:
```
Use get_portfolio_overview() to see balances across all exchanges
```

If no exchange is connected, use the `add_exchange` prompt first.

## Step 1: Understand Executors

Executors are smarter than simple orders. They provide:
- **Automatic risk management** (stop loss, take profit)
- **Position tracking** across multiple orders
- **Time limits** to auto-close stale positions

The main executor for directional trading is the **Position Executor**.

## Step 2: Get Current Price

Before trading, check the current price:

```
Use get_prices(connector_name="binance_perpetual", trading_pairs=["BTC-USDT"])
```

## Step 3: Create Your First Position

Let's create a position with automatic stop loss and take profit.

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
- `type`: "position_executor" for directional trades
- `connector_name`: Your exchange (e.g., "binance_perpetual", "hyperliquid_perpetual")
- `trading_pair`: The pair to trade (e.g., "BTC-USDT")
- `side`: "BUY" for long, "SELL" for short
- `amount`: Position size in base currency
- `triple_barrier_config`:
  - `stop_loss`: Exit if price drops this % (0.02 = 2%)
  - `take_profit`: Exit if price rises this % (0.04 = 4%)
  - `time_limit`: Auto-close after this many seconds (86400 = 24 hours)

## Step 4: Monitor Your Position

Check your active executors:

```
Use list_executors(is_active=True)
```

Get details on a specific executor:

```
Use get_executor(executor_id="<your_executor_id>")
```

Get overall summary:

```
Use get_executors_summary()
```

## Step 5: Manage Your Position

**To close early (take profit/loss):**

```
Use stop_executor(executor_id="<your_executor_id>", keep_position=False)
```

**To stop the executor but keep the position open:**

```
Use stop_executor(executor_id="<your_executor_id>", keep_position=True)
```

## Risk Management Tips

1. **Start small**: Use small amounts until comfortable
2. **Always set stop loss**: The triple_barrier_config protects you
3. **Use time limits**: Prevent positions from staying open forever
4. **Check balances**: Ensure sufficient margin for perpetuals

## What the Executor Handles Automatically

Once created, the executor:
- Places your entry order (market or limit)
- Monitors price for stop loss / take profit triggers
- Exits the position when any barrier is hit
- Tracks and reports your PnL

## Next Steps

After your first trade:
- Try different stop loss / take profit ratios
- Experiment with limit entries (add `entry_price` parameter)
- Explore other executor types with `get_executor_types()`

Which exchange and trading pair would you like to trade? I'll help you create your first position.
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

### 1. Position Executor (Most Common)

**What it does:** Opens a single position with automatic stop loss, take profit, and time limit.

**Best for:**
- Directional trading (going long or short)
- Swing trades with defined risk
- Trades where you want automatic exits

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

### 2. Grid Executor

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

### 3. DCA Executor

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

### 4. TWAP Executor

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

### 5. Arbitrage Executor

**What it does:** Exploits price differences between exchanges.

**Best for:**
- Risk-free profit from price discrepancies
- Multi-exchange setups
- Professional market making

Get full schema: `get_executor_schema("arbitrage_executor")`

### 6. XEMM Executor

**What it does:** Cross-exchange market making - provide liquidity on one exchange, hedge on another.

**Best for:**
- Professional market making
- Multi-exchange arbitrage
- Advanced trading strategies

Get full schema: `get_executor_schema("xemm_executor")`

## Choosing the Right Executor

**For beginners:** Start with Position Executor
- Simple to understand
- Clear risk management
- Good for learning

**For accumulation:** Use DCA Executor
- Reduces timing risk
- Good for long-term positions

**For sideways markets:** Use Grid Executor
- Profits from oscillation
- Good when direction is unclear

**For large orders:** Use TWAP Executor
- Minimizes market impact
- Better execution prices

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

## Quick Position Trade

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

## Common Exchanges

- Spot: `binance`, `coinbase`, `kucoin`
- Perpetuals: `binance_perpetual`, `hyperliquid_perpetual`, `bybit_perpetual`

## Common Pairs

- BTC-USDT, ETH-USDT, SOL-USDT
- BTC-USD, ETH-USD (for USD-margined perpetuals)

## Stop Loss / Take Profit Guidelines

| Risk Level | Stop Loss | Take Profit | Ratio |
|------------|-----------|-------------|-------|
| Conservative | 1% | 2% | 1:2 |
| Moderate | 2% | 4% | 1:2 |
| Aggressive | 3% | 6% | 1:2 |

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
