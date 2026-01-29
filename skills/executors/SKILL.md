---
name: hummingbot-executors
description: Create and manage trading executors (controllers) and deploy trading bots
version: 1.0.0
author: Hummingbot Foundation
triggers:
  - create executor
  - deploy bot
  - list controllers
  - start bot
  - stop bot
  - grid trading
  - market making
  - directional trading
---

# Hummingbot Executors Skill

This skill manages trading executors (controllers) and bot deployment. Executors are the core trading logic components that define how trades are executed.

## Prerequisites

- Hummingbot API server must be running (use the setup skill)
- Exchange credentials configured (use the keys skill)

## Executor Types

### 1. Directional Trading

Controllers that trade based on market direction signals:

| Controller | Description |
|------------|-------------|
| `bollinger_v1` | Bollinger Bands breakout strategy |
| `macd_bb_v1` | MACD + Bollinger Bands combination |
| `trend_following` | EMA crossover trend following |
| `dman_v3` | Dynamic market making with trend |

### 2. Market Making

Controllers that provide liquidity:

| Controller | Description |
|------------|-------------|
| `pmm_simple` | Pure market making |
| `pmm_dynamic` | Dynamic spread market making |
| `xemm` | Cross-exchange market making |
| `grid_strike` | Grid trading executor |

### 3. Generic

Utility controllers:

| Controller | Description |
|------------|-------------|
| `dca` | Dollar cost averaging |
| `twap` | Time-weighted average price |
| `grid` | Simple grid trading |

## Capabilities

### 1. List Controllers

View available controller types and configurations:

```bash
./scripts/list_controllers.sh
```

### 2. Describe Controller

Get detailed information about a specific controller:

```bash
./scripts/describe_controller.sh --name bollinger_v1
```

Output includes:
- Controller code
- Configuration parameters with types and defaults
- Existing configurations

### 3. Create Configuration

Create a new controller configuration:

```bash
./scripts/create_config.sh \
    --name my_grid_config \
    --controller grid_strike \
    --type market_making \
    --config '{
        "connector_name": "binance_perpetual",
        "trading_pair": "BTC-USDT",
        "grid_levels": 10,
        "grid_spread": 0.01,
        "order_amount": 0.001
    }'
```

### 4. Deploy Bot

Deploy a bot with one or more controller configurations:

```bash
./scripts/deploy_bot.sh \
    --name my_trading_bot \
    --configs "my_grid_config,my_trend_config" \
    --account master_account \
    --max-drawdown 100
```

### 5. Manage Bot Execution

Start, stop, or manage running bots:

```bash
# Stop entire bot
./scripts/manage_bot.sh --name my_trading_bot --action stop

# Stop specific controllers
./scripts/manage_bot.sh --name my_trading_bot --action stop_controllers --controllers "my_grid_config"

# Start controllers
./scripts/manage_bot.sh --name my_trading_bot --action start_controllers --controllers "my_grid_config"
```

### 6. Get Bot Status

Check status of running bots:

```bash
./scripts/get_bot_status.sh
```

## Configuration Parameters

### Common Parameters

All controllers share these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `connector_name` | string | Exchange connector (e.g., "binance") |
| `trading_pair` | string | Trading pair (e.g., "BTC-USDT") |
| `manual_kill_switch` | bool | Enable/disable controller |

### Grid Trading Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `grid_levels` | int | 10 | Number of grid levels |
| `grid_spread` | Decimal | 0.01 | Spread between levels (1%) |
| `order_amount` | Decimal | - | Amount per order |
| `upper_price` | Decimal | - | Upper price bound |
| `lower_price` | Decimal | - | Lower price bound |

### Market Making Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bid_spread` | Decimal | 0.001 | Bid spread from mid price |
| `ask_spread` | Decimal | 0.001 | Ask spread from mid price |
| `order_amount` | Decimal | - | Order size |
| `order_levels` | int | 1 | Number of order levels |
| `order_level_spread` | Decimal | 0.01 | Spread between levels |

### Directional Trading Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `position_size` | Decimal | - | Size of each position |
| `stop_loss` | Decimal | 0.02 | Stop loss percentage |
| `take_profit` | Decimal | 0.04 | Take profit percentage |
| `trailing_stop` | bool | false | Enable trailing stop |

## Workflow: Creating a Grid Trading Bot

1. **List available controllers**
   ```bash
   ./scripts/list_controllers.sh --type market_making
   ```

2. **Describe the grid controller**
   ```bash
   ./scripts/describe_controller.sh --name grid_strike
   ```

3. **Create configuration**
   ```bash
   ./scripts/create_config.sh \
       --name btc_grid_1 \
       --controller grid_strike \
       --type market_making \
       --config '{
           "connector_name": "binance_perpetual",
           "trading_pair": "BTC-USDT",
           "grid_levels": 20,
           "grid_spread": 0.005,
           "order_amount": 0.001,
           "upper_price": 100000,
           "lower_price": 90000
       }'
   ```

4. **Deploy bot**
   ```bash
   ./scripts/deploy_bot.sh \
       --name btc_grid_bot \
       --configs "btc_grid_1" \
       --account master_account
   ```

5. **Monitor status**
   ```bash
   ./scripts/get_bot_status.sh --name btc_grid_bot
   ```

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/controllers` | GET | List all controllers |
| `/api/v1/controllers/{type}/{name}` | GET | Get controller code |
| `/api/v1/controllers/{type}/{name}/config-template` | GET | Get config template |
| `/api/v1/controller-configs` | GET | List configurations |
| `/api/v1/controller-configs/{name}` | GET/POST/DELETE | Manage config |
| `/api/v1/bots/deploy` | POST | Deploy bot |
| `/api/v1/bots/status` | GET | Get active bots status |
| `/api/v1/bots/{name}/stop` | POST | Stop bot |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Controller not found" | Invalid controller name | Use list_controllers to see available |
| "Invalid configuration" | Missing required params | Check describe_controller for requirements |
| "Bot already exists" | Duplicate bot name | Use different name or stop existing |
| "Insufficient balance" | Not enough funds | Reduce order_amount or add funds |
