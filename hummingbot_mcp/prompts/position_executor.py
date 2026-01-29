"""
Position Executor prompts - Guide users through creating and managing position executors.
"""


def register_position_executor_prompts(mcp):
    """Register position executor prompts."""

    @mcp.prompt()
    def position_executor() -> str:
        """Create and manage position executors with Triple Barrier risk management.

        This prompt helps users:
        1. Detect connected exchanges
        2. Configure position parameters (pair, side, amount, leverage)
        3. Set up Triple Barrier (stop loss, take profit, time limit)
        4. Create and monitor position executors
        """
        return '''# Position Executor

You are helping the user create and manage position executors with Triple Barrier risk management.

## Step 1: Detect Connected Exchanges

First, check which exchanges the user has connected:

```
Use get_portfolio_overview()
```

From the results:
- Identify all connectors with balances
- Use the FIRST connector found as the default exchange
- Show user their available balance on that exchange
- If no exchanges connected, guide them to use `setup_connector`

Example response:
"Found [exchange] with $[balance] available. Using this for your position."

## Step 2: Gather Parameters from User

Ask the user for:

1. **Trading Pair** - e.g., BTC-USDT, ETH-USD (format depends on exchange)
2. **Side** - LONG (buy) or SHORT (sell)
3. **Amount** - Position size in quote currency (e.g., $100) or base currency
4. **Leverage** - e.g., 1, 5, 10, 20 (default: 1 for spot, higher for perpetuals)
5. **Stop Loss** - Optional, as percentage (e.g., 2% = 0.02)
6. **Take Profit** - Optional, as percentage (e.g., 4% = 0.04)
7. **Time Limit** - Optional, in hours (converted to seconds)

Suggest sensible defaults:
- Stop Loss: 2% (0.02)
- Take Profit: 4% (0.04) - 2:1 reward/risk ratio
- Time Limit: 24 hours (86400 seconds)

## Step 3: Fetch Current Price

```
Use get_prices(connector_name="<EXCHANGE>", trading_pairs=["<PAIR>"])
```

Show the user current price before confirming.

## Step 4: Set Leverage (for perpetuals)

If using a perpetual exchange (connector name contains "_perpetual"):

```
Use set_account_position_mode_and_leverage(
    account_name="master_account",
    connector_name="<EXCHANGE>",
    trading_pair="<PAIR>",
    leverage=<LEVERAGE>
)
```

## Step 5: Confirm Parameters

Display summary and ask for confirmation:

```
Position Executor Summary
=========================
Exchange: [connector]
Trading Pair: [pair]
Side: [LONG/SHORT]
Amount: [amount]
Leverage: [x]
Current Price: $[price]

Risk Management (Triple Barrier):
- Stop Loss: [%] ($[price])
- Take Profit: [%] ($[price])
- Time Limit: [hours]

Estimated Position Value: $[amount * leverage]

Confirm? (y/n)
```

## Step 6: Create Position Executor

```
Use create_executor(
    executor_config={
        "type": "position_executor",
        "connector_name": "<EXCHANGE>",
        "trading_pair": "<PAIR>",
        "side": <SIDE>,
        "amount": "<AMOUNT>",
        "leverage": <LEVERAGE>,
        "triple_barrier_config": {
            "stop_loss": "<STOP_LOSS>",
            "take_profit": "<TAKE_PROFIT>",
            "time_limit": <TIME_LIMIT_SECONDS>,
            "open_order_type": 2,
            "take_profit_order_type": 2,
            "stop_loss_order_type": 1,
            "time_limit_order_type": 1
        }
    },
    account_name="master_account"
)
```

---

## Position Executor Config Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `connector_name` | string | Exchange connector (e.g., binance_perpetual) |
| `trading_pair` | string | e.g., BTC-USDT, ETH-USD |
| `side` | enum | 1=BUY (long), 2=SELL (short) |
| `amount` | number/string | Position size in base currency |

### Optional Fields with Defaults

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | `position_executor` | Executor type |
| `leverage` | integer | `1` | Leverage multiplier |
| `entry_price` | number/string | `null` | Limit entry price (null=market) |
| `triple_barrier_config` | object | see below | Risk management |

### Triple Barrier Config (Risk Management)

The Triple Barrier method provides automatic position management:

```
    Take-Profit ═══════════════════════════════════  (+1)
                        Price Movement
    Entry ●─────────────────────────────────────
                                            │
    Stop-Loss ═════════════════════════════════════  (-1)
                                            │
                                      Time Limit (0)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `stop_loss` | number/string | `null` | Stop loss % (0.02 = 2%) |
| `take_profit` | number/string | `null` | Take profit % (0.04 = 4%) |
| `time_limit` | integer | `null` | Auto-close after seconds |
| `trailing_stop` | object | `null` | Trailing stop config |
| `open_order_type` | enum | `2` | 1=MARKET, 2=LIMIT |
| `take_profit_order_type` | enum | `1` | 1=MARKET, 2=LIMIT |
| `stop_loss_order_type` | enum | `1` | 1=MARKET, 2=LIMIT |
| `time_limit_order_type` | enum | `1` | 1=MARKET, 2=LIMIT |

### Trailing Stop (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `activation_price` | number/string | Price to activate trailing |
| `trailing_delta` | number/string | Trail distance as decimal |

---

## Step 7: Monitor Position

After creating, record starting balance and monitor:

```
Use get_portfolio_overview(connector_names=["<EXCHANGE>"])
```

### Status Format

```
Position Executor Monitor
=========================
ID: [short_id]
Status: [RUNNING/STOPPED]

Position:
- [LONG/SHORT] [amount] [pair] @ $[entry_price]
- Unrealized PnL: $[amount] ([pct]%)

Risk Management:
- Stop Loss: $[price] ([pct]% away)
- Take Profit: $[price] ([pct]% away)
- Time Remaining: [hours:mins]

Current Price: $[price]
Last Updated: [timestamp]
```

### Exit Conditions

Position closes automatically when ANY barrier is hit:
- **+1 (Take Profit)**: Price reached target
- **-1 (Stop Loss)**: Price hit stop
- **0 (Time Limit)**: Time expired

### User Commands

| Command | Action |
|---------|--------|
| `status` | Show current position status |
| `stop` | Close position at market |
| `keep position` | Stop executor, keep position |
| `done` | Stop monitoring |

### Final Report

When position closes:

```
Position Closed
===============
Exit Reason: [Take Profit / Stop Loss / Time Limit / Manual]
Entry Price: $[entry]
Exit Price: $[exit]

Result:
- Gross PnL: $[amount] ([pct]%)
- Fees: $[fees]
- Net PnL: $[net]

Final Balance: $[balance]
Starting Balance: $[start]
Net Change: $[diff]
```

---

## Risk/Reward Guidelines

| Style | Stop Loss | Take Profit | Ratio |
|-------|-----------|-------------|-------|
| Conservative | 1% | 2-3% | 1:2-3 |
| Moderate | 2% | 4-6% | 1:2-3 |
| Aggressive | 3% | 9%+ | 1:3+ |

**Tip**: Always ensure take profit > stop loss for positive expected value.

---

## Important Rules

1. **Detect exchange automatically** - Use first connected exchange
2. **Always show current price** - Before confirming position
3. **Confirm before creating** - Show all parameters
4. **Record starting balance** - For accurate final P&L
5. **Monitor until closed** - Track position until exit

---

What trading pair would you like to open a position on?
'''
