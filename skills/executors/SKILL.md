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

This skill manages **executors** - lightweight trading components that run directly via the Hummingbot API. Executors are the recommended starting point for new users.

## Quick Start: Setup Executor (Progressive Disclosure)

The `setup_executor.sh` script guides you through creating executors step by step:

### Step 1: List Available Executor Types

```bash
./scripts/setup_executor.sh
```

Shows all executor types with descriptions and current summary.

### Step 2: Get Config Schema

```bash
./scripts/setup_executor.sh --type position_executor
```

Shows required fields and example configuration.

### Step 3: Create Executor

```bash
./scripts/setup_executor.sh --type position_executor --config '{
    "connector_name": "hyperliquid_perpetual",
    "trading_pair": "BTC-USD",
    "side": "BUY",
    "amount": "0.001",
    "triple_barrier_config": {
        "stop_loss": "0.02",
        "take_profit": "0.04",
        "time_limit": 3600
    }
}'
```

## Executor Types

### 1. Position Executor (Recommended Start)

Single position with triple barrier risk management:
- **Stop Loss**: Exit if price moves against you
- **Take Profit**: Exit when target reached
- **Time Limit**: Exit after duration expires

```bash
./scripts/setup_executor.sh --type position_executor --config '{
    "connector_name": "hyperliquid_perpetual",
    "trading_pair": "BTC-USD",
    "side": "BUY",
    "amount": "0.001",
    "triple_barrier_config": {
        "stop_loss": "0.02",
        "take_profit": "0.04",
        "time_limit": 3600
    }
}'
```

### 2. Grid Executor

Automated grid trading with multiple buy/sell levels:

```bash
./scripts/setup_executor.sh --type grid_executor --config '{
    "connector_name": "hyperliquid_perpetual",
    "trading_pair": "BTC-USD",
    "start_price": "80000",
    "end_price": "90000",
    "total_amount_quote": "1000",
    "total_levels": 10,
    "side": "BUY"
}'
```

### 3. DCA Executor

Dollar-cost averaging with multiple entry points:

```bash
./scripts/setup_executor.sh --type dca_executor --config '{
    "connector_name": "hyperliquid_perpetual",
    "trading_pair": "BTC-USD",
    "side": "BUY",
    "total_amount_quote": "1000",
    "n_levels": 5,
    "time_limit": 86400
}'
```

### 4. TWAP Executor

Time-weighted average price for large orders with minimal market impact.

### 5. Arbitrage Executor

Cross-exchange price arbitrage.

### 6. XEMM Executor

Cross-exchange market making.

### 7. Order Executor

Simple order execution with retry logic.

## Management Scripts

### List Active Executors

```bash
./scripts/list_executors.sh [--status RUNNING] [--connector hyperliquid_perpetual]
```

### Get Executor Details

```bash
./scripts/get_executor.sh --id <executor_id>
```

### Stop Executor

```bash
# Stop and close positions
./scripts/stop_executor.sh --id <executor_id>

# Stop but keep position open
./scripts/stop_executor.sh --id <executor_id> --keep-position
```

### Get Summary Stats

```bash
./scripts/get_executors_summary.sh
```

### Manage Held Positions

```bash
# List all positions from stopped executors
./scripts/get_positions.sh

# Get specific position
./scripts/get_position.sh --connector hyperliquid_perpetual --pair BTC-USD

# Clear position (after manual close)
./scripts/clear_position.sh --connector hyperliquid_perpetual --pair BTC-USD
```

## Position Executor Configuration

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `connector_name` | string | Yes | Exchange connector |
| `trading_pair` | string | Yes | Trading pair |
| `side` | enum | Yes | BUY or SELL |
| `amount` | Decimal | Yes | Position size |
| `entry_price` | Decimal | No | Limit price (market if omitted) |
| `triple_barrier_config.stop_loss` | Decimal | No | Stop loss (e.g., 0.02 = 2%) |
| `triple_barrier_config.take_profit` | Decimal | No | Take profit percentage |
| `triple_barrier_config.time_limit` | int | No | Max duration in seconds |
| `leverage` | int | No | Leverage (default: 1) |

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
| `/executors/types/available` | GET | List executor types |
| `/executors/types/{type}/config` | GET | Get config schema |
| `/executors` | POST | Create executor |
| `/executors/search` | POST | List/filter executors |
| `/executors/summary` | GET | Get summary stats |
| `/executors/{id}` | GET | Get executor details |
| `/executors/{id}/stop` | POST | Stop executor |
| `/executors/positions/summary` | GET | Get held positions |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Unknown executor type" | Invalid type | Use Step 1 to see valid types |
| "Insufficient balance" | Not enough funds | Reduce amount or add funds |
| "Invalid trading pair" | Pair not on exchange | Check exchange for valid pairs |
| "Connector not configured" | Missing API keys | Use keys skill to add credentials |
