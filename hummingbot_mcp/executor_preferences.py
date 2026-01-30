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

# Default template for the preferences file
DEFAULT_PREFERENCES_TEMPLATE = """# Executor Preferences

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

### Arbitrage Executor
Best for: Capturing price differences between exchanges or pairs.

**Use when:**
- You've identified price discrepancies
- You want low-risk profit from inefficiencies
- You have accounts on multiple exchanges

**Avoid when:**
- Price differences are too small to cover fees
- You don't have sufficient capital on both sides

### Grid Executor
Best for: Trading in ranging/sideways markets with multiple buy/sell levels.

**Use when:**
- Market is range-bound
- You want to profit from volatility without directional bias
- You want automated rebalancing

**Avoid when:**
- Market is strongly trending (risk of one-sided fills)
- You have limited capital (grids require capital spread across levels)

**Limit Price Logic:**
- LONG grid: `limit_price < start_price < end_price` (enter BELOW the grid range)
- SHORT grid: `end_price < start_price < limit_price` (enter ABOVE the grid range)

**Key Parameters:**
- `start_price` / `end_price`: Grid boundaries
- `limit_price`: Entry trigger price (must follow the logic above)
- `min_spread_between_orders`: Spread between grid levels (e.g., 0.0001 = 0.01%)
- `min_order_amount_quote`: Minimum order size in quote currency
- `total_amount_quote`: Total capital allocation
- `max_open_orders`: Maximum concurrent open orders

### XEMM Executor (Cross-Exchange Market Making)
Best for: Market making across multiple exchanges.

**Use when:**
- You want to provide liquidity and earn spread
- You have access to multiple exchanges
- You can manage inventory risk

**Avoid when:**
- You're new to market making
- You can't monitor positions regularly

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

```yaml
grid_executor:
  # Add your default grid executor config here
  # Remember: LONG -> limit < start < end | SHORT -> end < start < limit
  # Example for LONG grid:
  # connector_name: binance
  # trading_pair: BTC-USDT
  # side: BUY
  # start_price: 89000
  # end_price: 90000
  # limit_price: 88700  # Below start for LONG
  # min_spread_between_orders: 0.0001  # 0.01% between levels
  # min_order_amount_quote: 10
  # total_amount_quote: 1000
  # max_open_orders: 5
```

### Arbitrage Executor Defaults

```yaml
arbitrage_executor:
  # Add your default arbitrage executor config here
```

### XEMM Executor Defaults

```yaml
xemm_executor:
  # Add your default XEMM executor config here
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

        Args:
            executor_type: The executor type to update
            config: The new default configuration
        """
        content = self._read_content()

        # Create the new YAML block
        new_yaml = yaml.dump({executor_type: config}, default_flow_style=False, sort_keys=False)
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

    def get_preferences_path(self) -> str:
        """Get the path to the preferences file.

        Returns:
            String path to the preferences file
        """
        return str(self.preferences_path)

    def reset_to_defaults(self) -> None:
        """Reset the preferences file to the default template."""
        self._write_template()
        logger.info("Reset executor preferences to defaults")


# Global instance for convenience
executor_preferences = ExecutorPreferencesManager()
