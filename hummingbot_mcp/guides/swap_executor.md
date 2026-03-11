### Swap Executor
**Execute single swaps on Gateway AMM connectors with retry logic.**

Executes token swaps on Gateway-connected DEXs (Jupiter, Raydium, etc.) with
built-in retry handling for transaction timeouts and failures.

**Use when:**
- Executing a single token swap on Solana DEXs
- Need reliable swap execution with automatic retries
- Trading via Gateway AMM connectors

**Avoid when:**
- Need complex trading strategies (use other executors)
- Want to manage LP positions (use lp_executor)
- Trading on CEX (use order_executor)

#### State Machine

```
NOT_STARTED → EXECUTING → COMPLETED (success)
                       → FAILED (max retries)
```

- **NOT_STARTED**: Initial state, swap not yet attempted
- **EXECUTING**: Swap submitted, waiting for confirmation (with retries)
- **COMPLETED**: Swap successfully completed
- **FAILED**: Swap failed after max retry attempts

#### Key Parameters

**Required:**
- `connector_name`: Gateway router connector (e.g., `jupiter/router`)
- `trading_pair`: Token pair (e.g., `SOL-USDC`)
- `side`: `BUY` (1) or `SELL` (2)
- `amount`: Amount of base token to swap

**Optional:**
- `slippage_pct`: Override default slippage tolerance

#### Side (Trade Direction)

**BUY (side=1 or "BUY"):**
- Buy base token using quote token
- Example: BUY SOL-USDC means buy SOL, pay USDC
- `amount` specifies how much SOL you want to receive

**SELL (side=2 or "SELL"):**
- Sell base token to receive quote token
- Example: SELL SOL-USDC means sell SOL, receive USDC
- `amount` specifies how much SOL you want to sell

#### Example Configurations

**Buy SOL with USDC:**
```yaml
swap_executor:
  connector_name: jupiter/router
  trading_pair: SOL-USDC
  side: BUY
  amount: "1.0"  # Buy 1 SOL
```

**Sell SOL for USDC:**
```yaml
swap_executor:
  connector_name: jupiter/router
  trading_pair: SOL-USDC
  side: SELL
  amount: "0.5"  # Sell 0.5 SOL
```

**With custom slippage:**
```yaml
swap_executor:
  connector_name: jupiter/router
  trading_pair: SOL-USDC
  side: BUY
  amount: "1.0"
  slippage_pct: "1.0"  # 1% slippage tolerance
```

#### Retry Behavior

The SwapExecutor uses the GatewayRetryMixin for robust error handling:

- **Transaction timeouts**: Automatically retries (chain congestion)
- **Price movement errors**: Retries without counting against max retries
- **Slippage errors**: Retries without counting against max retries
- **Max retries**: Default 10 attempts before failing

#### Custom Info (Executor Response)

When querying an executor, the `custom_info` field contains:
- `state`: Current state (NOT_STARTED, EXECUTING, COMPLETED, FAILED)
- `side`: BUY or SELL
- `amount`: Requested amount
- `executed_amount`: Actual executed amount
- `executed_price`: Average execution price (quote per base)
- `tx_fee`: Transaction fee paid
- `tx_hash`: Transaction signature/hash (Solana transaction ID)
- `exchange_order_id`: Same as tx_hash (for compatibility)
- `current_retries`: Number of retries so far
- `max_retries_reached`: True if executor gave up

#### Important Notes

- **Gateway Required**: SwapExecutor requires a running Gateway instance with the AMM connector configured
- **Atomic Operation**: Swaps are atomic - they either complete fully or not at all
- **No P&L Tracking**: Single swaps don't track P&L (no entry/exit pair)
- **Fee Tracking**: Transaction fees are tracked and reported
