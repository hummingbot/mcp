"""
Executor preferences manager for storing user defaults in markdown format.

This module manages user preferences for executor configurations stored in
a human-readable markdown file with embedded YAML blocks.

Preferences are stored at: ~/.hummingbot_mcp/executor_preferences.md
"""
import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("hummingbot-mcp")

# Default preferences directory and file
PREFERENCES_DIR = Path.home() / ".hummingbot_mcp"
PREFERENCES_FILE = PREFERENCES_DIR / "executor_preferences.md"

# Template version — bump this when documentation content changes
TEMPLATE_VERSION = "4"

# Default template for the preferences file
DEFAULT_PREFERENCES_TEMPLATE = """<!-- preferences-version: 4 -->
# Executor Preferences

This file stores your default configurations for different executor types.
You can edit this file manually or use `save_as_default=true` when creating executors.

---

## Executor Type Guide

### Position Executor
Best for: Taking directional positions with defined entry, stop-loss, and take-profit levels.

**Use when:**
- You have a clear directional view (bullish/bearish)
- You want automated stop-loss and take-profit management
- You want to define risk/reward ratios upfront

**Avoid when:**
- You want to provide liquidity (use Market Making instead)
- You need complex multi-leg strategies

### DCA Executor
Best for: Dollar-cost averaging into positions over time.

**Use when:**
- You want to accumulate a position gradually
- You want to reduce timing risk
- You're building a long-term position

**Avoid when:**
- You need immediate full position entry
- You want active trading with quick exits

### Order Executor
Best for: Placing a single buy or sell order with a specific execution strategy.

**Use when:**
- You want a one-off buy or sell with reliable execution
- You need a specific execution strategy (MARKET, LIMIT, LIMIT_MAKER, LIMIT_CHASER)
- You want simple order placement without multi-level complexity

**Avoid when:**
- You need multi-level strategies (use Grid or DCA instead)
- You want automated stop-loss/take-profit management (use Position Executor instead)

**Execution Strategies:**
- `MARKET`: Immediate execution at current market price
- `LIMIT`: Limit order at a specified price
- `LIMIT_MAKER`: Post-only limit order (rejected if it would match immediately)
- `LIMIT_CHASER`: Continuously chases best price, refreshing the limit order as the market moves

**LIMIT_CHASER Config (chaser_config):**
- `distance`: How far from best price to place the order (e.g., 0.001 = 0.1%)
- `refresh_threshold`: How far price must move before refreshing (e.g., 0.0005 = 0.05%)

### Grid Executor
Best for: Trading in ranging/sideways markets with multiple buy/sell levels.

**Use when:**
- Market is range-bound
- You want to profit from volatility without directional bias
- You want automated rebalancing

**Avoid when:**
- Market is strongly trending (risk of one-sided fills)
- You have limited capital (grids require capital spread across levels)

#### How Grid Trading Works

**LONG Grid (side: 1 = BUY):**
- Places buy limit orders below current price across the range (start_price → end_price)
- Each filled buy gets a corresponding sell order at take_profit distance
- Instead of buying base asset at once, acquires it gradually via limit orders
- If price rises above end_price → 100% quote currency, only realized profit from matched pairs
- If price drops below limit_price → grid stops, accumulated base asset held
  - `keep_position=true`: hold position (wait for recovery)
  - `keep_position=false`: close position at loss
- Take profit for levels above current price is calculated from the theoretical level price, not the entry price

**SHORT Grid (side: 2 = SELL):**
- Places sell limit orders above current price, each fill gets a buy at take_profit below
- If price drops below start_price → all profit realized
- If price rises above limit_price → grid stops, accumulated quote from sells
- Useful for selling an existing position — generates yield while exiting

**CRITICAL:** `side` must be explicitly set (1=BUY, 2=SELL). `limit_price` alone does NOT determine direction.

**Direction Rules:**
- LONG grid:  `limit_price < start_price < end_price` (limit below grid, buys low)
- SHORT grid: `start_price < end_price < limit_price` (limit above grid, sells high)

#### Parameter Reference

**Grid Structure:**
- `start_price` / `end_price`: Grid boundaries (lower/upper)
- `limit_price`: Safety boundary (LONG: below start, SHORT: above end)
- `total_amount_quote`: Capital allocated (quote currency). Must always be specified.

**Grid Density — How Many Levels:**
- `min_order_amount_quote`: Min size per order → max possible levels = `total_amount_quote / min_order_amount_quote`
- `min_spread_between_orders`: Min price distance between levels (decimal, e.g. 0.0001 = 0.01%) → max levels from spread = `price_range / (spread * mid_price)`
- **Actual levels = min(max_from_amount, max_from_spread)** — the intersection of both constraints

**Order Placement Controls:**
- `activation_bounds`: Only places orders within this % of current price (e.g. 0.001 = 0.1%). Protects liquidity, reduces rate limit usage. If not set, all orders placed at once.
- `order_frequency`: Seconds between order batches. Spaces out submissions, prevents rate limits.
- `max_orders_per_batch`: Max orders per batch. Combined with order_frequency, controls fill speed.
- `max_open_orders`: Hard cap on concurrent open orders.

**Take Profit & Risk:**
- `triple_barrier_config.take_profit`: Profit target as decimal (0.0002 = 0.02%). Distance for the opposite order on fill.
- `triple_barrier_config.open_order_type`: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER (recommended — post-only, earns maker fees)
- `triple_barrier_config.take_profit_order_type`: Same enum. 3=LIMIT_MAKER recommended.
- `coerce_tp_to_step`: When true, TP = max(grid_step, take_profit). Prevents closing before next level.

**Risk Management — limit_price + keep_position (NO stop_loss):**
- `limit_price` is the safety boundary — when price crosses it, the grid stops completely.
- `keep_position=false`: closes the accumulated position on stop → acts as a stop-loss exit.
- `keep_position=true`: holds the accumulated position on stop → wait for recovery.
- There is NO `stop_loss` parameter. Never suggest it. `limit_price` + `keep_position` is the only risk mechanism for grids.

---

## Your Default Configurations

Edit the YAML blocks below to set your preferred defaults for each executor type.
These defaults will be applied when creating new executors.

### Position Executor Defaults

```yaml
position_executor:
  # Add your default position executor config here
  # Example:
  # connector_name: binance_perpetual
  # trading_pair: BTC-USDT
  # side: BUY
  # leverage: 10
```

### DCA Executor Defaults

```yaml
dca_executor:
  # Add your default DCA executor config here
  # Example:
  # connector_name: binance
  # trading_pair: BTC-USDT
  # amounts_quote: [100, 100, 100]
  # prices: [50000, 48000, 46000]
```

### Grid Executor Defaults

Note: This is a tight scalping configuration. Adjust prices and amounts to your market.

```yaml
grid_executor:
  # connector_name: binance_perpetual
  # trading_pair: BTC-USDT
  # side: 1  # 1=BUY (LONG grid), 2=SELL (SHORT grid)
  # start_price: 89000
  # end_price: 90000
  # limit_price: 88700  # Below start for LONG
  min_spread_between_orders: 0.0001  # 0.01% between levels
  min_order_amount_quote: 6
  # total_amount_quote: 100  # Always specify — capital in quote currency
  max_open_orders: 15
  activation_bounds: 0.001  # 0.1% — only place orders near current price
  order_frequency: 5  # seconds between order batches
  max_orders_per_batch: 1
  keep_position: true
  coerce_tp_to_step: true
  triple_barrier_config:
    take_profit: 0.0002  # 0.02%
    open_order_type: 3  # LIMIT_MAKER (post-only, earns maker fees)
    take_profit_order_type: 3  # LIMIT_MAKER
```

### Order Executor Defaults

```yaml
order_executor:
  # Add your default order executor config here
  # Example:
  # connector_name: binance
  # trading_pair: BTC-USDT
  # side: 1  # 1=BUY, 2=SELL
  # amount: "0.001"
  # execution_strategy: LIMIT_MAKER
  # price: "95000"
```

---

*Last updated: Never*
"""


class ExecutorPreferencesManager:
    """Manager for executor preferences stored in markdown format."""

    def __init__(self, preferences_path: Path | None = None):
        """Initialize the preferences manager.

        Args:
            preferences_path: Custom path for preferences file. Defaults to ~/.hummingbot_mcp/executor_preferences.md
        """
        self.preferences_path = preferences_path or PREFERENCES_FILE
        self._ensure_preferences_exist()

    def _ensure_preferences_exist(self) -> None:
        """Create preferences directory and file if they don't exist."""
        # Create directory if it doesn't exist
        self.preferences_path.parent.mkdir(parents=True, exist_ok=True)

        # Create default preferences file if it doesn't exist
        if not self.preferences_path.exists():
            self._write_template()
            logger.info(f"Created default executor preferences at {self.preferences_path}")

    def _write_template(self) -> None:
        """Write the default template to the preferences file."""
        self.preferences_path.write_text(DEFAULT_PREFERENCES_TEMPLATE)

    def _read_content(self) -> str:
        """Read the preferences file content."""
        if not self.preferences_path.exists():
            self._write_template()
        return self.preferences_path.read_text()

    def _write_content(self, content: str) -> None:
        """Write content to the preferences file."""
        self.preferences_path.write_text(content)

    def _parse_yaml_blocks(self, content: str) -> dict[str, dict[str, Any]]:
        """Parse YAML blocks from markdown content.

        Args:
            content: Markdown content with embedded YAML blocks

        Returns:
            Dictionary mapping executor type to its configuration
        """
        # Pattern to match YAML code blocks
        yaml_pattern = r'```yaml\s*\n([\s\S]*?)```'

        defaults = {}
        matches = re.findall(yaml_pattern, content)

        for yaml_content in matches:
            try:
                parsed = yaml.safe_load(yaml_content)
                if parsed and isinstance(parsed, dict):
                    # Each YAML block should have executor_type as the top-level key
                    for executor_type, config in parsed.items():
                        if config and isinstance(config, dict):
                            defaults[executor_type] = config
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML block: {e}")
                continue

        return defaults

    def get_executor_guide(self, executor_type: str) -> str | None:
        """Extract the documentation guide section for a specific executor type.

        Reads the preferences file and returns the markdown section under
        '## Executor Type Guide' that corresponds to the given executor type
        (e.g. 'grid_executor' → '### Grid Executor' section).

        Args:
            executor_type: The executor type (e.g., 'grid_executor')

        Returns:
            The markdown content of the guide section, or None if not found.
        """
        content = self._read_content()

        # Map executor_type to section header prefix
        # Some names don't title-case cleanly (DCA, XEMM), so use known mappings
        _section_names = {
            "dca_executor": "DCA Executor",
        }
        section_name = _section_names.get(
            executor_type,
            executor_type.replace("_", " ").title(),
        )
        # Match from ### {Name}... up to the next ### at the same level or --- separator
        # The header may have extra text after the name (e.g. "XEMM Executor (Cross-Exchange ...)")
        pattern = rf'(### {re.escape(section_name)}[^\n]*\n[\s\S]*?)(?=\n### |\n---)'
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
        return None

    def get_defaults(self, executor_type: str) -> dict[str, Any]:
        """Get default configuration for an executor type.

        Args:
            executor_type: The executor type (e.g., 'position_executor', 'dca_executor')

        Returns:
            Dictionary of default configuration values, or empty dict if none set
        """
        content = self._read_content()
        all_defaults = self._parse_yaml_blocks(content)
        return all_defaults.get(executor_type, {})

    def get_all_defaults(self) -> dict[str, dict[str, Any]]:
        """Get all default configurations.

        Returns:
            Dictionary mapping executor types to their default configurations
        """
        content = self._read_content()
        return self._parse_yaml_blocks(content)

    def update_defaults(self, executor_type: str, config: dict[str, Any]) -> None:
        """Update default configuration for an executor type.

        Merges new config with existing defaults so that only the provided
        keys are updated while previously saved keys are preserved.

        Args:
            executor_type: The executor type to update
            config: The configuration keys to update (merged with existing defaults)
        """
        content = self._read_content()

        # Merge with existing defaults so we don't lose previously saved keys
        existing_defaults = self.get_defaults(executor_type)
        merged_config = {**existing_defaults, **config}

        # Create the new YAML block
        new_yaml = yaml.dump({executor_type: merged_config}, default_flow_style=False, sort_keys=False)
        new_block = f"```yaml\n{new_yaml}```"

        # Pattern to find the existing block for this executor type
        # Look for ```yaml followed by the executor type key
        pattern = rf'```yaml\s*\n{re.escape(executor_type)}:[\s\S]*?```'

        if re.search(pattern, content):
            # Replace existing block
            content = re.sub(pattern, new_block, content)
        else:
            # Append new block before the last "---" separator or at the end
            # Find the appropriate section to add the block
            section_header = f"### {executor_type.replace('_', ' ').title()} Defaults"
            if section_header in content:
                # Find the section and add after the header
                pattern = rf'({re.escape(section_header)}\s*\n\n)```yaml[\s\S]*?```'
                if re.search(pattern, content):
                    content = re.sub(pattern, rf'\1{new_block}', content)
                else:
                    # Section exists but no yaml block, add it
                    content = content.replace(
                        section_header,
                        f"{section_header}\n\n{new_block}"
                    )
            else:
                # No section found, append before the footer
                footer_pattern = r'\n---\s*\n\*Last updated:'
                if re.search(footer_pattern, content):
                    content = re.sub(
                        footer_pattern,
                        f"\n### {executor_type.replace('_', ' ').title()} Defaults\n\n{new_block}\n\n---\n\n*Last updated:",
                        content
                    )
                else:
                    # Just append at the end
                    content += f"\n\n### {executor_type.replace('_', ' ').title()} Defaults\n\n{new_block}\n"

        # Update the last updated timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = re.sub(
            r'\*Last updated:.*\*',
            f'*Last updated: {timestamp}*',
            content
        )

        self._write_content(content)
        logger.info(f"Updated defaults for {executor_type}")

    def merge_with_defaults(self, executor_type: str, user_config: dict[str, Any]) -> dict[str, Any]:
        """Merge user configuration with stored defaults.

        User-provided values take precedence over defaults.

        Args:
            executor_type: The executor type
            user_config: User-provided configuration

        Returns:
            Merged configuration with defaults filled in
        """
        defaults = self.get_defaults(executor_type)
        merged = {**defaults, **user_config}
        return merged

    def get_raw_content(self) -> str:
        """Get the raw markdown content of the preferences file.

        Returns:
            The full text content of the preferences file
        """
        return self._read_content()

    def save_content(self, content: str) -> None:
        """Save raw content to the preferences file.

        This replaces the entire file content, allowing the AI to make
        intelligent edits (add notes, organize by exchange, etc.).

        Args:
            content: The complete markdown content to write
        """
        self._write_content(content)
        logger.info("Saved preferences file content")

    def get_preferences_path(self) -> str:
        """Get the path to the preferences file.

        Returns:
            String path to the preferences file
        """
        return str(self.preferences_path)

    def get_template_version(self) -> str | None:
        """Read the preferences-version from the file.

        Returns:
            The version string if found, or None if no version comment is present.
        """
        content = self._read_content()
        match = re.search(r'<!--\s*preferences-version:\s*(\S+)\s*-->', content)
        return match.group(1) if match else None

    def needs_documentation_update(self) -> bool:
        """Check if the preferences file has outdated documentation.

        Returns:
            True if the file version is older than TEMPLATE_VERSION or missing.
        """
        file_version = self.get_template_version()
        if file_version is None:
            return True
        return file_version != TEMPLATE_VERSION

    def reset_to_defaults(self) -> dict[str, dict[str, Any]]:
        """Reset the preferences file to the default template, preserving user YAML configs.

        Saves all current YAML configurations, writes the new template,
        then re-applies each saved config.

        Returns:
            Dictionary of preserved configs (executor_type -> config dict).
        """
        # Save current YAML configs before resetting
        preserved = self.get_all_defaults()

        # Write the new template
        self._write_template()

        # Re-apply each saved config
        for executor_type, config in preserved.items():
            if config:
                self.update_defaults(executor_type, config)

        logger.info(
            f"Reset executor preferences to defaults, preserved {len(preserved)} config(s)"
        )
        return preserved


# Global instance for convenience
executor_preferences = ExecutorPreferencesManager()
