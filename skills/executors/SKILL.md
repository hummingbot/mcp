---
name: hummingbot-executors
description: Create and manage trading executors directly via API - no Docker bots required
version: 1.0.0
author: Hummingbot Foundation
triggers:
  - create executor
  - run executor
  - position executor
  - grid executor
  - dca executor
  - stop loss
  - take profit
  - simple trading
---

# Hummingbot Executors Skill

This skill manages **executors** - lightweight trading components that run directly via the Hummingbot API without requiring Docker containers or full bot deployment. Executors are the recommended starting point for new users.

## Why Executors?

| Feature | Executors | Controllers (Bots) |
|---------|-----------|-------------------|
| **Complexity** | Simple | Advanced |
| **Setup** | API call only | Docker + config |
| **Use case** | Single trades, simple strategies | Complex multi-strategy bots |
| **Learning curve** | Low | High |

**Start with executors**, graduate to controllers when you need more sophistication.

## Executor Types

### 1. Position Executor (Recommended Start)

Single position with triple barrier risk management:
- **Stop Loss**: Exit if price moves against you
- **Take Profit**: Exit when target reached
- **Time Limit**: Exit after duration expires

```bash
./scripts/create_executor.sh \
    --type position_executor \
    --connector binance_perpetual \
    --pair BTC-USDT \
    --side BUY \
    --amount 0.001 \
    --stop-loss 0.02 \
    --take-profit 0.04
```

### 2. Grid Executor

Automated grid trading with multiple buy/sell levels:

```bash
./scripts/create_executor.sh \
    --type grid_executor \
    --connector binance \
    --pair ETH-USDT \
    --lower-price 2000 \
    --upper-price 2500 \
    --levels 10 \
    --amount 0.1
```

### 3. DCA Executor

Dollar-cost averaging with multiple entry points:

```bash
./scripts/create_executor.sh \
    --type dca_executor \
    --connector binance \
    --pair BTC-USDT \
    --side BUY \
    --total-amount 1000 \
    --num-orders 5 \
    --interval 3600
```

### 4. TWAP Executor

Time-weighted average price for large orders:

```bash
./scripts/create_executor.sh \
    --type twap_executor \
    --connector binance \
    --pair BTC-USDT \
    --side BUY \
    --amount 1.0 \
    --duration 3600 \
    --num-orders 10
```

### 5. Arbitrage Executor

Cross-exchange price arbitrage:

```bash
./scripts/create_executor.sh \
    --type arbitrage_executor \
    --maker-connector binance \
    --taker-connector kucoin \
    --pair BTC-USDT \
    --min-profit 0.001
```

### 6. XEMM Executor

Cross-exchange market making:

```bash
./scripts/create_executor.sh \
    --type xemm_executor \
    --maker-connector binance \
    --taker-connector kucoin \
    --pair BTC-USDT \
    --spread 0.002
```

### 7. Order Executor

Simple order execution with retry logic:

```bash
./scripts/create_executor.sh \
    --type order_executor \
    --connector binance \
    --pair BTC-USDT \
    --side BUY \
    --amount 0.01 \
    --order-type LIMIT \
    --price 40000
```

## Capabilities

### 1. List Available Executor Types

```bash
./scripts/list_executor_types.sh
```

Returns all supported executor types with descriptions.

### 2. Get Executor Config Schema

```bash
./scripts/get_executor_schema.sh --type position_executor
```

Returns required/optional fields for each executor type.

### 3. Create Executor

```bash
./scripts/create_executor.sh \
    --type <executor_type> \
    --config '{"connector_name": "...", "trading_pair": "...", ...}'
```

### 4. List Active Executors

```bash
./scripts/list_executors.sh [--status RUNNING] [--connector binance]
```

### 5. Get Executor Details

```bash
./scripts/get_executor.sh --id <executor_id>
```

### 6. Stop Executor

```bash
# Stop and close positions
./scripts/stop_executor.sh --id <executor_id>

# Stop but keep position open
./scripts/stop_executor.sh --id <executor_id> --keep-position
```

### 7. Get Executor Summary

```bash
./scripts/get_executors_summary.sh
```

Returns aggregate PnL, volume, counts by type.

### 8. Manage Held Positions

```bash
# List all positions from stopped executors
./scripts/get_positions.sh

# Get specific position
./scripts/get_position.sh --connector binance_perpetual --pair BTC-USDT

# Clear position (after manual close)
./scripts/clear_position.sh --connector binance_perpetual --pair BTC-USDT
```

## Workflow: Your First Trade

### Step 1: Check executor types

```bash
./scripts/list_executor_types.sh
```

### Step 2: Get schema for position executor

```bash
./scripts/get_executor_schema.sh --type position_executor
```

### Step 3: Create a position executor

```bash
./scripts/create_executor.sh \
    --type position_executor \
    --connector binance_perpetual \
    --pair BTC-USDT \
    --side BUY \
    --amount 0.001 \
    --entry-price 42000 \
    --stop-loss 0.02 \
    --take-profit 0.04 \
    --time-limit 3600
```

### Step 4: Monitor the executor

```bash
./scripts/get_executor.sh --id <returned_executor_id>
```

### Step 5: Stop early if needed

```bash
./scripts/stop_executor.sh --id <executor_id>
```

## Position Executor Configuration

The position executor is the most common starting point:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `connector_name` | string | Yes | Exchange connector |
| `trading_pair` | string | Yes | Trading pair |
| `side` | enum | Yes | BUY or SELL |
| `amount` | Decimal | Yes | Position size |
| `entry_price` | Decimal | No | Limit price (market if omitted) |
| `stop_loss` | Decimal | No | Stop loss percentage (e.g., 0.02 = 2%) |
| `take_profit` | Decimal | No | Take profit percentage |
| `time_limit` | int | No | Max duration in seconds |
| `trailing_stop` | object | No | Trailing stop configuration |

### Triple Barrier Explained

```
                    Take Profit (exit with gain)
                    ────────────────────────
                         ↑
         Price moves up  │
                         │
Entry ──────────────────●──────────────────── Time Limit (exit)
                         │
         Price moves down│
                         ↓
                    ────────────────────────
                    Stop Loss (exit with loss)
```

The position exits when ANY barrier is hit first.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/executors/types/available` | GET | List executor types |
| `/api/v1/executors/types/{type}/config` | GET | Get config schema |
| `/api/v1/executors` | POST | Create executor |
| `/api/v1/executors/search` | POST | List/filter executors |
| `/api/v1/executors/summary` | GET | Get summary stats |
| `/api/v1/executors/{id}` | GET | Get executor details |
| `/api/v1/executors/{id}/stop` | POST | Stop executor |
| `/api/v1/executors/positions/summary` | GET | Get held positions |
| `/api/v1/executors/positions/{connector}/{pair}` | GET/DELETE | Manage position |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Unknown executor type" | Invalid type | Use list_executor_types.sh |
| "Insufficient balance" | Not enough funds | Reduce amount or add funds |
| "Invalid trading pair" | Pair not on exchange | Check exchange for valid pairs |
| "Connector not configured" | Missing API keys | Use keys skill to add credentials |

## Next Steps

Once comfortable with executors, you can:
1. **Combine executors**: Run multiple executors simultaneously
2. **Graduate to controllers**: Use the controllers skill for complex strategies
3. **Build agents**: Create AI agents that manage executors based on market conditions
