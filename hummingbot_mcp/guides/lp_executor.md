### LP Executor
Manages liquidity provider positions on CLMM DEXs (Meteora, Raydium).
Opens positions within price bounds, monitors range status, tracks fees.

**Use when:**
- Providing liquidity on Solana DEXs
- Want automated position monitoring and fee tracking
- Earning trading fees from LP positions

**Avoid when:**
- Trading on CEX (use other executors)
- Want directional exposure only
- Not familiar with impermanent loss risks

#### State Machine

```
NOT_ACTIVE → OPENING → IN_RANGE ↔ OUT_OF_RANGE → CLOSING → COMPLETE
```

- **NOT_ACTIVE**: Initial state, no position yet
- **OPENING**: Transaction submitted to open position
- **IN_RANGE**: Position active, current price within bounds
- **OUT_OF_RANGE**: Position active but price outside bounds (no fees earned)
- **CLOSING**: Transaction submitted to close position
- **COMPLETE**: Position closed, executor finished

#### Key Parameters

**Required:**
- `connector_name`: CLMM connector in `connector/clmm` format (e.g., `meteora/clmm`, `raydiumclmm/clmm`)
  - **IMPORTANT:** Must include the `/clmm` suffix — using just `meteora` will fail
- `trading_pair`: Token pair (e.g., `SOL-USDC`)
- `pool_address`: Pool contract address
- `lower_price` / `upper_price`: Price range bounds

**Liquidity:**
- `base_amount`: Amount of base token to provide
- `quote_amount`: Amount of quote token to provide
- `side`: Position side (0=BOTH, 1=BUY/quote-only, 2=SELL/base-only)

**Position Management:**
- `keep_position=false` (default): Close LP position when executor stops
- `keep_position=true`: Leave position open on-chain, stop monitoring only

#### Meteora Strategy Types (extra_params.strategyType)

- `0`: **Spot** — Uniform liquidity across range
- `1`: **Curve** — Concentrated around current price
- `2`: **Bid-Ask** — Liquidity at range edges

#### Important: Managing Positions

**Always use the executor tool (`manage_executors`) to open and close LP positions — NOT the gateway CLMM tool directly.**

- Opening/closing via `manage_gateway_clmm` bypasses the executor state machine and leaves the database out of sync
- Use `manage_executors` with `action="stop"` to properly close positions and update executor status
- If a position is closed externally (via gateway or UI), manually mark the executor as `TERMINATED` in the database
