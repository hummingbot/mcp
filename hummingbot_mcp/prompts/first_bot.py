"""
First Trade / Bot prompts - Guide users through their first trades using bots.

Terminology:
- "Bot" = Executor (user-friendly term for lightweight trading algorithms)
- "Controller" = Strategy template (the code/logic)
- "Controller Configuration" = Parameters for a controller (trading pair, amounts, etc.)
- "Controller Instance" = Running deployment with one or more controller configs
"""


def register_first_bot_prompts(mcp):
    """Register first trade/bot prompts."""

    @mcp.prompt()
    def first_trade() -> str:
        """Guide the user through their first trade using bots.

        This prompt helps users:
        1. Start with a simple order using Order Bot
        2. Learn about Position Bot with Triple Barrier risk management
        3. Monitor and manage positions
        """
        return """# Your First Trade with Hummingbot

You are helping the user execute their first trade using Hummingbot's bot system.
Bots are smart trading algorithms that handle order placement and position management automatically.

**Terminology Note**: When the user says "bot", they mean an executor. Use the executor tools
(create_executor, list_executors, etc.) but refer to them as "bots" in conversation.

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

## Part 1: Your First Order (Order Bot)

Let's start simple. The **Order Bot** places a single order with retry logic - perfect for your first trade.

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

Tell the user: "Creating an Order Bot to buy 0.001 BTC..."

**Parameters:**
- `type`: "order_executor" (this creates an Order Bot)
- `connector_name`: Your exchange (e.g., "binance_perpetual", "hyperliquid_perpetual")
- `trading_pair`: The pair to trade (e.g., "BTC-USDT")
- `side`: "BUY" or "SELL"
- `amount`: Order size in base currency

### Step 3: Verify Your Order

```
Use list_executors(is_active=True)
Use get_portfolio_overview()
```

**Congratulations!** You've created your first Order Bot. It handles:
- Order submission with retry on failures
- Status tracking
- Basic error handling

---

## Part 2: Advanced Trades with Position Bot

Now let's level up. The **Position Bot** adds professional risk management using the **Triple Barrier Method**.

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

### Step 1: Create a Position Bot with Risk Management

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

Tell the user: "Creating a Position Bot with 2% stop loss and 4% take profit..."

**Parameters explained:**
- `side`: "BUY" for long, "SELL" for short
- `amount`: Position size in base currency
- `triple_barrier_config`:
  - `stop_loss`: Exit if loss reaches this % (0.02 = 2%)
  - `take_profit`: Exit if profit reaches this % (0.04 = 4%)
  - `time_limit`: Auto-close after this many seconds (86400 = 24 hours)

### Step 2: Monitor Your Position Bot

```
Use list_executors(is_active=True)
Use get_executor(executor_id="<bot_id>")
```

Tell user: "Here are your active bots..." or "Here's the status of your Position Bot..."

### Step 3: Managing the Position Bot

**To close early (market exit):**
```
Use stop_executor(executor_id="<bot_id>", keep_position=False)
```
Tell user: "Stopping the bot and closing the position..."

**To stop monitoring but keep position:**
```
Use stop_executor(executor_id="<bot_id>", keep_position=True)
```
Tell user: "Stopping the bot but keeping the position open..."

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

After mastering these bots:
1. **Grid Bot**: For range-bound markets
2. **DCA Bot**: For gradual position building
3. **TWAP Bot**: For large orders with minimal market impact

Use `get_executor_types()` to see all available bot types.

For advanced strategies with custom logic, explore **Controllers** using `explore_controllers()`.

Which exchange and trading pair would you like to trade? I'll help you create your first bot.
"""

    @mcp.prompt()
    def list_strategies() -> str:
        """List and explain all available bot types and controllers."""
        return """# Available Trading Strategies

You are helping the user understand the different bot types and controllers available in Hummingbot.

**Terminology:**
- **Bots** = Executors (lightweight trading algorithms)
- **Controllers** = Strategy templates (the code/logic)
- **Controller Configurations** = Parameters for a controller
- **Controller Instances** = Running deployments with one or more configs

## Part 1: Bot Types

Bots are simple, focused trading algorithms. Get available types:

```
Use get_executor_types()
```

### 1. Order Bot (Simplest)

**What it does:** Places a single order with retry logic.

**Best for:**
- Simple buy/sell orders
- Getting started with trading
- When you don't need automatic stop loss/take profit

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

### 2. Position Bot (Most Popular)

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

### 3. Grid Bot

**What it does:** Places multiple buy/sell orders at different price levels.

**Best for:**
- Range-bound markets
- Accumulating or distributing positions
- Markets without strong trends

Get full schema: `get_executor_schema("grid_executor")`

---

### 4. DCA Bot

**What it does:** Dollar-cost averages into a position over time or price levels.

**Best for:**
- Reducing timing risk
- Accumulating long-term positions
- Averaging into volatile markets

Get full schema: `get_executor_schema("dca_executor")`

---

### 5. TWAP Bot

**What it does:** Executes a large order in smaller chunks over time.

**Best for:**
- Large orders that would move the market
- Minimizing market impact
- Algorithmic order execution

Get full schema: `get_executor_schema("twap_executor")`

---

### 6. Arbitrage Bot

**What it does:** Exploits price differences between exchanges.

**Best for:**
- Risk-free profit from price discrepancies
- Multi-exchange setups

Get full schema: `get_executor_schema("arbitrage_executor")`

---

### 7. XEMM Bot

**What it does:** Cross-exchange market making - provide liquidity on one exchange, hedge on another.

**Best for:**
- Professional market making
- Multi-exchange strategies

Get full schema: `get_executor_schema("xemm_executor")`

---

## Part 2: Controllers (Advanced)

Controllers are advanced strategy templates for sophisticated trading.

**How Controllers Work:**
1. **Controller** = Strategy template (the code/logic)
2. **Controller Configuration** = Parameters for that strategy (pair, amounts, spreads)
3. **Controller Instance** = Running deployment with one or more configs

```
Use explore_controllers(action="list")
```

### Controller Types

- **directional_trading**: Trade based on technical indicators (Bollinger, MACD, Supertrend)
- **market_making**: Provide liquidity with configurable spreads (PMM strategies)
- **generic**: Multi-purpose strategies (grid strike, arbitrage, stat arb)

### When to Use Controllers vs Bots

| Scenario | Use |
|----------|-----|
| Simple trade with stop loss | Position Bot |
| Grid trading | Grid Bot |
| Custom indicator-based strategy | Controller |
| Multiple strategies running together | Controller |
| Need advanced configuration | Controller |

### Exploring Controllers

```
# List all controllers
Use explore_controllers(action="list")

# See controller details and its configurations
Use explore_controllers(action="describe", controller_name="pmm_simple")

# See a specific configuration
Use explore_controllers(action="describe", config_name="pmm_btc_config")
```

### Creating a Controller Configuration

```
# First explore the controller to see required parameters
Use explore_controllers(action="describe", controller_name="pmm_simple")

# Then create a configuration
Use modify_controllers(
    action="upsert",
    target="config",
    config_name="my_pmm_config",
    config_data={
        "controller_name": "pmm_simple",
        "connector_name": "binance_perpetual",
        "trading_pair": "BTC-USDT",
        ...
    }
)
```

### Deploying a Controller Instance

```
Use deploy_bot_with_controllers(
    bot_name="my_market_maker",
    controllers_config=["my_pmm_config"]  # Can include multiple configs
)
```

---

## Choosing the Right Strategy

| Goal | Recommended |
|------|-------------|
| Simple order | Order Bot |
| Trade with stop loss/take profit | Position Bot |
| Sideways/ranging market | Grid Bot |
| Build position gradually | DCA Bot |
| Large order execution | TWAP Bot |
| Multi-exchange profit | Arbitrage Bot |
| Custom strategy logic | Controller |

**For beginners:** Start with Order Bot, then graduate to Position Bot.

Which strategy interests you? I can help you understand the configuration and get started.
"""

    @mcp.prompt()
    def quick_trade() -> str:
        """Quick reference for placing common trades."""
        return """# Quick Trade Reference

You are helping the user execute common trades quickly.

**Remember**: When user says "bot", use executor tools but refer to them as "bots".

## Simple Order (Order Bot)

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
Say: "Creating an Order Bot to buy <size> <PAIR>..."

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
Say: "Creating an Order Bot to sell <size> <PAIR>..."

---

## Position with Risk Management (Position Bot)

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
Say: "Creating a Position Bot with 2% stop loss and 4% take profit..."

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
Say: "Creating a short Position Bot with 2% stop loss and 4% take profit..."

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

3. **See active bots:**
   ```
   Use list_executors(is_active=True)
   ```
   Say: "Here are your active bots..."

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

## Manage Bots

**List active bots:**
```
Use list_executors(is_active=True)
```
Say: "Here are your active bots..."

**Stop a bot and close position:**
```
Use stop_executor(executor_id="<id>", keep_position=False)
```
Say: "Stopping the bot and closing the position..."

**Get bot summary:**
```
Use get_executors_summary()
```
Say: "Here's your bot performance summary..."

What would you like to trade?
"""
