# Reimagining Bots

## Executive Summary

This plan outlines the evolution from the current controller-based bot architecture to a modular **Skills + Agents** paradigm. The new architecture enables AI agents to compose trading strategies from reusable skills, making sophisticated trading accessible and enabling a community-driven ecosystem.

---

## Motivation: The Complexity Problem

> *"Running automated trading bots can be complex."*
> — [Hummingbot YouTube Tutorial](https://youtu.be/Y7-tX1OKfKs?si=ywgE53Tr8rNtGSUI)

### The Current Reality

Setting up and running automated trading bots remains a significant barrier for most traders. Despite Hummingbot's powerful capabilities, the onboarding experience demands substantial technical expertise:

#### Technical Barriers

| Barrier | Description |
|---------|-------------|
| **Command-Line Interface** | No graphical interface; CLI can be "daunting" for non-technical users |
| **Docker Knowledge** | Recommended installation requires Docker familiarity and container management |
| **Multi-Component Setup** | Full deployment involves 4+ containers: API server, PostgreSQL, EMQX broker, Gateway |
| **API Key Management** | Each exchange requires generating, securing, and configuring API credentials |
| **Gateway Complexity** | DEX trading adds blockchain engineering requirements: wallets, SSL certificates, chain configs |

#### Setup Steps for a Basic Bot

A typical Hummingbot deployment requires:

```
1. Install Docker Desktop
2. Clone hummingbot-api repository
3. Run setup script (pulls 4+ Docker images)
4. Configure Telegram bot (optional but recommended)
5. Set API server credentials
6. Generate and add exchange API keys
7. Configure connectors for each exchange
8. (For DEX) Set up Gateway with:
   - Wallet configuration
   - Chain/network selection
   - Connector configuration (Jupiter, Uniswap, etc.)
   - SSL certificates for production
9. Create controller configuration
10. Deploy and monitor bot
```

#### Who Gets Left Behind

According to [community reviews](https://yourrobotrader.com/en/hummingbot-review/):

- *"The initial setup may require technical knowledge, especially for users unfamiliar with command-line interfaces."*
- *"HummingBot does not have a user-friendly interface... The onboarding is brutal for users without any technical expertise."*
- *"Launching a bot can be a difficult task for those who do not have any prior experience with GitHub, coding, and using various applications."*
- *"Users who lack the expertise... should stick to using services that have customizable ready-made robots that you can launch in a couple of clicks."*

### The Opportunity

The gap between "a couple of clicks" and "multi-container Docker deployment" represents a massive opportunity. **AI agents can bridge this gap** by:

1. **Abstracting complexity** — Natural language replaces CLI commands
2. **Progressive disclosure** — Only show what's needed, when it's needed
3. **Error recovery** — AI can diagnose and fix configuration issues
4. **Guided setup** — Step-by-step assistance instead of documentation diving

### Vision

Transform the experience from:
```
"Read the docs → Install Docker → Clone repo → Configure YAML → Debug errors → Deploy"
```

To:
```
"Tell the agent what you want to trade → Agent handles the rest"
```

---

## Why Skills Over MCP: A Critical Design Decision

This architecture adopts the **Agent Skills** pattern rather than expanding the existing MCP server. This is a deliberate choice based on extensive analysis of both approaches.

### Background: MCP vs Skills

| Aspect | MCP (Model Context Protocol) | Agent Skills |
|--------|------------------------------|--------------|
| **What it is** | Protocol for connecting AI to external services | Markdown files teaching AI how to do things |
| **Analogy** | "The plumbing" — what tools are available | "The brain" — how to use tools effectively |
| **Created by** | Anthropic (2024) | Anthropic (2025), now an [open standard](https://agentskills.io) |
| **Adoption** | Wide (Claude, Cursor, many tools) | Growing (Microsoft, OpenAI, GitHub, Cursor, VS Code) |

### The Context Window Problem

As [Simon Willison notes](https://simonwillison.net/2025/Oct/16/claude-skills/):

> *"GitHub's official MCP on its own famously consumes tens of thousands of tokens of context."*

**MCP Context Cost:**
- Simple tools: ~150-250 tokens each
- Medium tools: ~300-500 tokens each
- Complex tools: ~500-800 tokens each
- Full Playwright MCP: **~8,000-10,000 tokens**
- GitHub MCP: **~20,000+ tokens**

**Skills Context Cost:**
- Skill metadata only: **~100 tokens**
- Full skill (when activated): **<5,000 tokens**
- Script execution output only (code never enters context)

The current Hummingbot MCP server has 24 tools. At current rates, that's potentially **12,000-20,000 tokens** just for tool definitions—before any actual work begins.

### Installation Complexity

**MCP Installation:**
```bash
# Requires running server processes
npm install @modelcontextprotocol/server-xyz
# Configure .mcp.json with server paths
# Manage server lifecycle (start/stop/restart)
# Handle authentication between client and servers
# Debug connection issues
```

**Skills Installation:**
```bash
# Just files in a directory
~/.claude/skills/
  my-skill/
    SKILL.md      # Instructions + metadata
    scripts/      # Optional executable scripts
    references/   # Optional documentation
```

As [Armin Ronacher observes](https://lucumr.pocoo.org/2025/12/13/skills-vs-mcp/):

> *"The skills pattern outperforms MCP in current practice, primarily because it leverages existing agent capabilities without introducing new tool-definition mechanisms."*

### Progressive Disclosure

Skills employ **lazy loading**:

1. **Initially**: Only skill names and brief descriptions load (~100 tokens per skill)
2. **On relevance**: Full SKILL.md content loads (<5k tokens)
3. **On execution**: Scripts run, only **output** enters context (code stays out)

This means an agent can have access to **hundreds of skills** without overwhelming context—impossible with eager-loaded MCP tools.

### Why Not a Hybrid Approach?

One might think: "Use Skills for knowledge, MCP for execution." This doesn't work because **MCP tools are always loaded into context**, regardless of whether they're used. Adding Skills on top of MCP doesn't reduce context consumption—it increases it.

### Our Approach: Skills Replace MCP

Skills call the **Hummingbot API directly** via scripts, completely bypassing MCP:

```
┌─────────────────────────────────────────────────────────────┐
│                        SKILLS LAYER                          │
│                                                              │
│   • Procedural knowledge (how to trade, when to rebalance)  │
│   • Strategy logic (entry/exit conditions, risk rules)      │
│   • Workflow orchestration (setup sequences, diagnostics)   │
│   • Domain expertise (indicator interpretation, sizing)     │
│                                                              │
│   Context cost: ~100-5000 tokens per active skill           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Scripts call API directly
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    HUMMINGBOT API                            │
│                                                              │
│   • REST endpoints for all trading operations               │
│   • Exchange connectivity (CEX + DEX via Gateway)           │
│   • Bot orchestration and management                        │
│   • Market data and portfolio queries                       │
│                                                              │
│   No MCP overhead — direct HTTP calls from skill scripts    │
└─────────────────────────────────────────────────────────────┘
```

**Key insight**: Skills contain scripts that make direct API calls. The agent never loads tool definitions—it loads skill instructions that tell it *how* to call endpoints.

### The Setup Skill: Bootstrapping the Stack

The **Setup Skill** is critical—it handles deploying the Hummingbot API server itself:

```yaml
skill: setup
description: Deploy and configure Hummingbot infrastructure

scripts:
  - deploy_api_server.sh    # Docker compose up
  - configure_connectors.sh # Exchange API setup
  - deploy_gateway.sh       # DEX infrastructure
  - health_check.sh         # Verify all services

workflow:
  1. Check Docker prerequisites
  2. Deploy API server (PostgreSQL, EMQX, API)
  3. Configure exchange connectors
  4. (Optional) Deploy Gateway for DEX
  5. Verify all endpoints responding
  6. Return connection details to agent
```

This creates a clean bootstrap sequence:
1. Agent loads Setup Skill (~100 tokens)
2. Agent runs setup scripts (output only enters context)
3. API server is now running
4. Other skills can call API endpoints directly

### Simon Willison's Prediction

> *"I'm expecting a Cambrian explosion in Skills that will make this year's MCP rush look pedestrian by comparison."*
> — [Simon Willison, October 2025](https://simonwillison.net/2025/Oct/16/claude-skills/)

By building on Skills now, we position Hummingbot at the forefront of this shift.

### References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Simon Willison: Claude Skills are awesome](https://simonwillison.net/2025/Oct/16/claude-skills/)
- [Armin Ronacher: Skills vs Dynamic MCP Loadouts](https://lucumr.pocoo.org/2025/12/13/skills-vs-mcp/)
- [Claude Blog: Skills Explained](https://claude.com/blog/skills-explained)
- [IntuitionLabs: Claude Skills vs MCP Technical Comparison](https://intuitionlabs.ai/articles/claude-skills-vs-mcp)
- [DEV.to: Skills, MCPs, and Commands](https://dev.to/gvegacl/skills-mcps-and-commands-are-the-same-context-engineering-trend-49dp)

---

## Current Architecture (Legacy)

The existing Hummingbot architecture follows a monolithic controller pattern:

```
┌─────────────────────────────────────────────────────┐
│                    CONTROLLER                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   On-Tick   │  │ Indicators  │  │  Algorithm  │  │
│  │    Loop     │──│  (RSI, MA,  │──│   Logic     │  │
│  │             │  │   etc.)     │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                         │                            │
│                    ┌────▼────┐                       │
│                    │  Params │                       │
│                    └─────────┘                       │
└─────────────────────────────────────────────────────┘
```

### Limitations

| Component | Issue |
|-----------|-------|
| **On-Tick Loop** | Tightly coupled to controller; hard to reuse across strategies |
| **Indicators** | Embedded in controller code; duplicated across bots |
| **Algorithm** | Monolithic; difficult to modify without understanding entire codebase |
| **Params** | Scattered across config files; no unified management |

---

## New Architecture: Skills + Agents

### Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              AGENTS                                      │
│                                                                          │
│  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐   │
│  │ trend-following-   │  │   panda-lp-bot     │  │  market-maker    │   │
│  │      bot           │  │                    │  │                  │   │
│  └─────────┬──────────┘  └─────────┬──────────┘  └────────┬─────────┘   │
│            │                       │                      │              │
│            ▼                       ▼                      ▼              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    AGENT LOGIC (Markdown)                        │    │
│  │   • Natural language strategy description                        │    │
│  │   • Skill composition rules                                      │    │
│  │   • Risk parameters & constraints                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              SKILLS                                      │
│                                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │  Indicator   │ │    Grid      │ │    Setup     │ │   Data       │   │
│  │   Skills     │ │  Executors   │ │    Skill     │ │   Feeds      │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │    Keys      │ │ Controllers  │ │   Servers    │ │  Executors   │   │
│  │  Management  │ │  Management  │ │  Management  │ │  Management  │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          MCP SERVER                                      │
│                  (Deterministic Endpoints)                               │
│                                                                          │
│         Maps Skills → Condor Menu Items → Hummingbot API                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Skills Framework

### Definition

A **Skill** is a self-contained, reusable capability that:
- Wraps deterministic MCP endpoints
- Maps directly to Condor menu items
- Can be composed by agents
- Has well-defined inputs/outputs

### Core Skills

#### 1. Keys Management Skill
```yaml
skill: keys
description: Manage API keys and credentials for exchanges and services
endpoints:
  - list_keys
  - add_key
  - remove_key
  - verify_key
condor_menu: Settings > API Keys
```

#### 2. Controllers Management Skill
```yaml
skill: controllers
description: Create, modify, and manage trading controllers
endpoints:
  - explore_controllers
  - modify_controllers
  - get_controller_status
condor_menu: Strategies > Controllers
```

#### 3. Servers Management Skill
```yaml
skill: servers
description: Configure and manage Hummingbot API servers
endpoints:
  - configure_api_servers
  - health_check
  - switch_server
condor_menu: Settings > Servers
```

#### 4. Executors Management Skill
```yaml
skill: executors
description: Manage order execution engines
endpoints:
  - list_executors
  - configure_executor
  - start_executor
  - stop_executor
types:
  - grid_executor
  - dca_executor
  - twap_executor
  - arbitrage_executor
condor_menu: Execution > Executors
```

#### 5. Data Feeds Skill
```yaml
skill: data_feeds
description: Access market data streams and historical data
endpoints:
  - get_prices
  - get_candles
  - get_order_book
  - get_funding_rate
  - subscribe_ticker
condor_menu: Data > Market Data
```

### Advanced Skills

#### 6. Indicator Skill
```yaml
skill: indicators
description: Technical analysis indicators
capabilities:
  - create_indicator:
      types: [RSI, MACD, BB, EMA, SMA, ATR, VWAP]
      custom: true
  - combine_indicators
  - get_signals
example:
  agent_request: "Create RSI(14) indicator for BTC-USDT"
  skill_response:
    indicator_id: "rsi_btc_14"
    current_value: 45.2
    signal: "neutral"
```

#### 7. Grid Executors Skill
```yaml
skill: grid_executors
description: Grid trading execution strategies
capabilities:
  - create_grid:
      params:
        - price_bounds (upper, lower)
        - num_levels
        - amount_per_level
        - rebalance_threshold
  - monitor_grid
  - adjust_grid
  - close_grid
example:
  agent_request: "Create 10-level grid from $90k to $100k"
  skill_response:
    grid_id: "grid_btc_001"
    levels: [90000, 91111, ..., 100000]
    status: "active"
```

#### 8. Setup Skill
```yaml
skill: setup
description: End-to-end environment setup
capabilities:
  - full_deploy:
      description: "Executes complete deploy script functionality"
      fallback: true
  - individual_steps:
      - setup_docker
      - configure_network
      - initialize_database
      - setup_connectors
      - deploy_gateway
      - start_api_server
      - health_check_all
workflow:
  1. Check prerequisites
  2. Run individual setup steps
  3. On failure: use fallback (full deploy script)
  4. Verify all components healthy
```

---

## Agents Framework

### Definition

An **Agent** is an AI-powered trading entity that:
- Has strategy logic defined in **Markdown files**
- Composes multiple **Skills** to execute strategies
- Operates autonomously within defined constraints
- Can be certified and funded

### Agent Logic in Markdown

Each agent's strategy is defined in a human-readable markdown file:

```markdown
# trend-following-bot.md

## Strategy Overview
Trend-following strategy using EMA crossovers with dynamic position sizing.

## Skills Required
- indicators (EMA, ATR)
- executors (market_orders)
- data_feeds (candles, prices)
- keys (exchange_api)

## Entry Conditions
- EMA(20) crosses above EMA(50)
- ATR(14) > 2% of price (volatility filter)
- Volume > 20-period average

## Exit Conditions
- EMA(20) crosses below EMA(50)
- Stop loss: 2 * ATR below entry
- Take profit: 3 * ATR above entry

## Position Sizing
- Base position: 2% of portfolio
- Scale with confidence: 1-3%
- Max positions: 3

## Risk Parameters
| Parameter | Value |
|-----------|-------|
| Max drawdown | 10% |
| Daily loss limit | 3% |
| Max position size | 5% |
```

### Agent Execution Flow

```
┌─────────────────┐
│   Agent Logic   │
│   (Markdown)    │
└────────┬────────┘
         │ Parse & Validate
         ▼
┌─────────────────┐
│  Skill Resolver │ ─── Identifies required skills
└────────┬────────┘
         │ Compose
         ▼
┌─────────────────┐
│  Skill Executor │ ─── Orchestrates skill calls
└────────┬────────┘
         │ Monitor
         ▼
┌─────────────────┐
│ Risk Manager    │ ─── Enforces constraints
└────────┬────────┘
         │ Execute
         ▼
┌─────────────────┐
│   MCP Server    │ ─── Deterministic execution
└─────────────────┘
```

---

## Reference Agents

### 1. trend-following-bot

**Purpose**: Capture directional moves using technical indicators

```markdown
# trend-following-bot

## Skills
- indicators: EMA, RSI, ATR
- data_feeds: candles (1h, 4h)
- executors: market_orders, stop_loss

## Markets
- BTC-USDT perpetual
- ETH-USDT perpetual

## Logic
1. Calculate EMA(20) and EMA(50) on 4h candles
2. Generate signal on crossover
3. Confirm with RSI not overbought/oversold
4. Size position based on ATR
5. Set trailing stop at 2*ATR
```

### 2. panda-lp-bot

**Purpose**: Automated liquidity provision on DEX CLMM pools

```markdown
# panda-lp-bot

## Skills
- data_feeds: pool_stats, prices
- executors: clmm_positions
- indicators: volatility_bands

## Pools
- SOL-USDC on Meteora
- ETH-USDC on Uniswap v3

## Logic
1. Monitor pool fee APR and volume
2. Calculate optimal price range (±2σ from current price)
3. Open position when fee APR > 50%
4. Rebalance when price exits 80% of range
5. Collect fees every 24h
6. Close position when impermanent loss > fees earned
```

### 3. market-maker (xrpliquid-miner)

**Purpose**: Provide liquidity on order books with grid strategy

```markdown
# market-maker

## Skills
- data_feeds: order_book, trades
- executors: grid_executor
- indicators: spread_analyzer

## Markets
- Selected XRP Liquid pairs
- Low-spread perpetual markets

## Logic
1. Analyze order book depth and spread
2. Deploy grid: 20 levels, ±1% from mid
3. Adjust grid based on inventory
4. Target: 0.5% spread capture
5. Max inventory: $10k per side
```

---

## Repository Structure

### Skills Repository (`hummingbot-skills`)

```
hummingbot-skills/
├── README.md
├── pyproject.toml
├── skills/
│   ├── __init__.py
│   ├── base.py              # BaseSkill class
│   ├── keys/
│   │   ├── __init__.py
│   │   └── skill.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── skill.py
│   ├── servers/
│   │   ├── __init__.py
│   │   └── skill.py
│   ├── executors/
│   │   ├── __init__.py
│   │   ├── skill.py
│   │   └── types/
│   │       ├── grid.py
│   │       ├── dca.py
│   │       └── twap.py
│   ├── data_feeds/
│   │   ├── __init__.py
│   │   └── skill.py
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── skill.py
│   │   └── types/
│   │       ├── rsi.py
│   │       ├── ema.py
│   │       └── atr.py
│   ├── grid_executors/
│   │   ├── __init__.py
│   │   └── skill.py
│   └── setup/
│       ├── __init__.py
│       ├── skill.py
│       └── fallback/
│           └── deploy_script.sh
├── registry/
│   └── skills.yml           # Skill registry with Condor mappings
└── tests/
    └── ...
```

### Agents Repository (`hummingbot-agents`)

```
hummingbot-agents/
├── README.md
├── pyproject.toml
├── agents/
│   ├── __init__.py
│   ├── base.py              # BaseAgent class
│   ├── loader.py            # Markdown parser
│   ├── executor.py          # Skill orchestration
│   └── risk_manager.py      # Constraint enforcement
├── strategies/
│   ├── trend-following-bot.md
│   ├── panda-lp-bot.md
│   └── market-maker.md
├── certified/               # Botcamp-certified agents
│   ├── hummingbot-miner/
│   │   ├── strategy.md
│   │   └── config.yml
│   ├── xrpliquid-miner/
│   │   ├── strategy.md
│   │   └── config.yml
│   └── market-maker/
│       ├── strategy.md
│       └── config.yml
├── templates/
│   └── agent-template.md
└── tests/
    └── ...
```

---

## Condor Menu Integration

Skills map directly to Condor menu items for seamless UI integration:

```yaml
# condor_menu_mapping.yml

menu:
  Settings:
    API Keys: skills.keys
    Servers: skills.servers

  Strategies:
    Controllers: skills.controllers
    Indicators: skills.indicators

  Execution:
    Executors: skills.executors
    Grid Trading: skills.grid_executors

  Data:
    Market Data: skills.data_feeds
    Historical: skills.data_feeds.history

  Deploy:
    Full Setup: skills.setup.full_deploy
    Components: skills.setup.individual_steps

  Agents:
    Certified: agents.certified
    Custom: agents.strategies
    Competition: agents.botcamp
```

---

## Botcamp Competition

### Overview

A live trading competition showcasing certified agents, funded and monitored in real-time.

### Structure

| Aspect | Details |
|--------|---------|
| **Funding** | $1,000 USDC per certified agent |
| **Duration** | 1 week, starting at Demo Day |
| **Format** | Livestreamed performance tracking |
| **Reporting** | Automated tweet bot for updates |

### Competition Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     BOTCAMP COMPETITION                          │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   Certified  │   │   Funded     │   │   Live       │        │
│  │   Agents     │──▶│   Accounts   │──▶│   Trading    │        │
│  │              │   │   $1k USDC   │   │              │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│         │                                     │                  │
│         ▼                                     ▼                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                MONITORING DASHBOARD                   │       │
│  │                                                       │       │
│  │  • Real-time PnL tracking                            │       │
│  │  • Trade-by-trade visualization                      │       │
│  │  • Risk metric monitoring                            │       │
│  │  • Leaderboard rankings                              │       │
│  └──────────────────────────────────────────────────────┘       │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                   TWEET BOT                           │       │
│  │                                                       │       │
│  │  @HummingbotComp:                                    │       │
│  │  "Hour 24 Update:                                     │       │
│  │   🥇 trend-following-bot: +4.2%                      │       │
│  │   🥈 panda-lp-bot: +3.1%                             │       │
│  │   🥉 market-maker: +2.8%                             │       │
│  │   Live: hummingbot.io/botcamp"                       │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Certification Requirements

To be certified for Botcamp competition, agents must:

1. **Strategy Review**
   - Clear markdown documentation
   - Defined entry/exit logic
   - Explicit risk parameters

2. **Backtesting**
   - Positive expectancy over 6 months
   - Sharpe ratio > 1.0
   - Max drawdown < 20%

3. **Paper Trading**
   - 2 weeks minimum paper trading
   - Execution quality validation
   - Error handling verification

4. **Risk Compliance**
   - Position limits enforced
   - Stop loss mechanisms active
   - Circuit breakers configured

### Tweet Bot Specifications

```python
# tweet_bot_config.py

TWEET_SCHEDULE = {
    "hourly_update": "0 * * * *",      # Every hour
    "trade_alert": "on_trade",          # On significant trades
    "daily_summary": "0 9 * * *",       # Daily at 9 AM
    "milestone": "on_milestone",        # On PnL milestones
}

TEMPLATES = {
    "hourly": """
⏰ Hour {hour} Update

{leaderboard}

📊 Total Volume: ${total_volume:,.0f}
📈 Best Trade: {best_trade}

🔴 Live: hummingbot.io/botcamp
    """,

    "trade_alert": """
🚨 Trade Alert!

{agent_name} just {action}
{pair}: {size} @ ${price}

Current PnL: {pnl_percent}%

🔴 Watch live: hummingbot.io/botcamp
    """,
}
```

---

## Integrating Skills into Your Agent

This section explains how to add Hummingbot skills to your AI agent, following the [Agent Skills integration guide](https://agentskills.io/integrate-skills).

### Integration Approaches

**Filesystem-Based Agents** (Claude Code, Cursor, terminal tools):
- Skills activate when the model reads `SKILL.md` via shell commands
- Example: `cat /path/to/skills/executors/SKILL.md`
- Scripts execute via standard shell commands

**Tool-Based Agents** (custom implementations):
- Implement tools for skill discovery and activation
- Load skill metadata into context at startup
- Execute scripts through your tool framework

### Step 1: Clone the Repository

```bash
git clone https://github.com/hummingbot/mcp.git
cd mcp/skills
```

### Step 2: Discover Skills at Startup

Parse only the YAML frontmatter from each `SKILL.md` to keep context minimal:

```python
import yaml
from pathlib import Path

def discover_skills(skills_dir: str) -> list:
    """Scan for skills, extracting only metadata."""
    skills = []
    for skill_folder in Path(skills_dir).iterdir():
        skill_file = skill_folder / "SKILL.md"
        if skill_file.exists():
            content = skill_file.read_text()
            # Extract YAML frontmatter
            if content.startswith("---"):
                end = content.find("---", 3)
                frontmatter = yaml.safe_load(content[3:end])
                skills.append({
                    "name": frontmatter.get("name"),
                    "description": frontmatter.get("description"),
                    "triggers": frontmatter.get("triggers", []),
                    "path": str(skill_file)
                })
    return skills
```

### Step 3: Inject into System Prompt

Include available skills in your agent's system prompt:

```xml
<available_skills>
  <skill>
    <name>hummingbot-setup</name>
    <description>Deploy and configure Hummingbot infrastructure</description>
    <location>/home/user/mcp/skills/setup/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-keys</name>
    <description>Manage exchange API credentials</description>
    <location>/home/user/mcp/skills/keys/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-executors</name>
    <description>Create and manage trading executors</description>
    <location>/home/user/mcp/skills/executors/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-candles</name>
    <description>Market data and technical indicators</description>
    <location>/home/user/mcp/skills/candles/SKILL.md</location>
  </skill>
</available_skills>
```

### Step 4: Match User Intent to Skills

When a user request matches a skill's triggers or description, load the full skill:

```python
def activate_skill(skill_path: str) -> str:
    """Load complete skill instructions into context."""
    return Path(skill_path).read_text()

# Example: User says "I want to create a position executor"
# Agent recognizes "executor" trigger → loads executors skill
skill_content = activate_skill("/home/user/mcp/skills/executors/SKILL.md")
```

### Step 5: Execute Skill Scripts

Skills include shell scripts that call the Hummingbot API directly:

```bash
# Example: Create a position executor
./skills/executors/scripts/create_executor.sh \
    --type position_executor \
    --connector binance_perpetual \
    --pair BTC-USDT \
    --side BUY \
    --amount 0.001 \
    --stop-loss 0.02 \
    --take-profit 0.04
```

### CLI Helper: Generate Prompt XML

```bash
#!/bin/bash
# Generate <available_skills> XML from skills directory

SKILLS_DIR="${1:-./skills}"

echo "<available_skills>"
for skill_dir in "$SKILLS_DIR"/*/; do
    if [ -f "$skill_dir/SKILL.md" ]; then
        name=$(grep "^name:" "$skill_dir/SKILL.md" | head -1 | cut -d':' -f2- | xargs)
        desc=$(grep "^description:" "$skill_dir/SKILL.md" | head -1 | cut -d':' -f2- | xargs)
        echo "  <skill>"
        echo "    <name>$name</name>"
        echo "    <description>$desc</description>"
        echo "    <location>$(realpath "$skill_dir/SKILL.md")</location>"
        echo "  </skill>"
    fi
done
echo "</available_skills>"
```

### Context Efficiency Summary

| What | Context Cost |
|------|--------------|
| Skill metadata (startup) | ~100 tokens per skill |
| Full skill (on activation) | <5,000 tokens |
| Script execution | Output only |
| **Total for 4 skills** | **~400 tokens** (vs ~20,000 for MCP) |

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create `hummingbot-skills` repository structure
- [ ] Implement `BaseSkill` class with MCP integration
- [ ] Port existing MCP tools to skill format
- [ ] Create skill registry with Condor mappings

### Phase 2: Core Skills (Weeks 3-4)
- [ ] Implement Keys Management Skill
- [ ] Implement Controllers Management Skill
- [ ] Implement Servers Management Skill
- [ ] Implement Data Feeds Skill
- [ ] Implement Setup Skill with fallback

### Phase 3: Advanced Skills (Weeks 5-6)
- [ ] Implement Indicator Skill
- [ ] Implement Grid Executors Skill
- [ ] Implement Executors Management Skill
- [ ] Create skill composition framework

### Phase 4: Agents Framework (Weeks 7-8)
- [ ] Create `hummingbot-agents` repository structure
- [ ] Implement markdown strategy parser
- [ ] Build skill orchestration engine
- [ ] Implement risk manager

### Phase 5: Reference Agents (Weeks 9-10)
- [ ] Develop trend-following-bot
- [ ] Develop panda-lp-bot
- [ ] Develop market-maker
- [ ] Certification testing

### Phase 6: Botcamp Competition (Weeks 11-12)
- [ ] Set up competition infrastructure
- [ ] Implement monitoring dashboard
- [ ] Build tweet bot
- [ ] Demo Day launch

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Skills implemented | 10+ core skills |
| Certified agents | 5+ for first competition |
| Competition participation | 10+ certified agents |
| Average agent PnL | > 0% (capital preservation) |
| Community engagement | 1000+ livestream viewers |
| Tweet impressions | 100k+ over competition week |

---

## Appendix: MCP Server Integration

The Skills framework builds on the existing MCP server capabilities:

### Current MCP Tools → Skills Mapping

| MCP Tool | Skill |
|----------|-------|
| `configure_api_servers` | servers |
| `setup_connector` | keys |
| `explore_controllers` | controllers |
| `modify_controllers` | controllers |
| `deploy_bot_with_controllers` | executors |
| `get_prices`, `get_candles` | data_feeds |
| `manage_gateway_clmm_positions` | executors (clmm) |
| `manage_gateway_swaps` | executors (swaps) |

### New Skills Required

| Skill | MCP Extensions Needed |
|-------|----------------------|
| indicators | New tool: `create_indicator`, `get_indicator_value` |
| grid_executors | New tool: `create_grid`, `monitor_grid`, `adjust_grid` |
| setup | New tool: `run_setup_step`, `verify_setup` |

---

*Document Version: 1.0*
*Last Updated: 2026-01-29*
*Author: Hummingbot Foundation*
