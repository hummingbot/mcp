# hummbot MCP Server - ASCII Slide Mockups

## Published artifact: https://claude.ai/public/artifacts/8e72a776-498f-44ed-83a9-98354c8b4306

## Slide 1: Title

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                                                                     │
│                                                                     │
│                              hummbot                                │
│                                                                     │
│                                                                     │
│                Your Own Private Trading Agent                       │
│                                                                     │
│                                                                     │
│         ┌───────────────────────────────────────────────┐         │
│         │                                               │         │
│         │  An AI-native command that helps you     │         │
│         │  deploy and manage a powerful custom
             agentic trading system, powered by Hummingbot │         │
│         └───────────────────────────────────────────────┘         │
│                                                                     │
│                                                                     │
│                 🚀 Deploy  •  💱 Trade  •  🤖 Automate             │
│                                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 2: The Problem

```
┌─────────────────────────────────────────────────────────────────────┐
│              Building a Trading Firm: Before vs After               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────┬───────────────────────────────┐  │
│  │        BEFORE 😰             │         AFTER 😊              │  │
│  ├─────────────────────────────┼───────────────────────────────┤  │
│  │                             │                               │  │
│  │  💼 Hire Developers         │  🤖 Use Your AI Assistant     │  │
│  │  • Build trading infra      │  • CLI (Claude Code, Gemini)  │  │
│  │  • Connect to exchanges     │  • Apps (Cursor, ChatGPT)     │  │
│  │  • Implement strategies     │                               │  │
│  │  Cost: $50,000+             │  Cost: $0                     │  │
│  │                             │                               │  │
│  │  👥 Hire Market Makers      │  📱 Natural Language          │  │
│  │  • Configure strategies     │  • "Install hummbot"        │  │
│  │  • Monitor positions        │  • "Trade BTC/USDT"           │  │
│  │  • Manage risk              │  • "Run market making bot"    │  │
│  │  Cost: $50,000+             │  Cost: $0                     │  │
│  │                             │                               │  │
│  │  🔧 Ongoing Maintenance     │  🚀 Regular Releases           │  │
│  │  • Fix bugs                 │  • Open source community      │  │
│  │  • Security updates         │  • No maintenance needed      │  │
│  │                             │                               │  │
│  │  💰 Total Cost: $100,000+   │  💰 Total Cost: FREE!         │  │
│  │  ⏱️ Time to Launch: Months   │  ⏱️ Time to Launch: 15 min    │  │
│  │                             │                               │  │
│  └─────────────────────────────┴───────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 3: What is hummbot?

```
┌─────────────────────────────────────────────────────────────────────┐
│                         What is hummbot?                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│     ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│     │   Claude   │   │   Cursor   │   │   ChatGPT  │   │   Gemini   │
│     │     👤     │   │     👤     │   │     👤     │   │     👤     │
│     └─────┬──────┘   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
│           │                 │                 │                 │
│           └─────────────────┴─────────────────┴─────────────────┘
│                                      │                              
│                                      ▼                              
│                  ┌────────────────────────────┐                    
│                  │    hummbot MCP Server      │                    
│                  │ Your Trading Infrastructure │                    
│                  └────────────────────────────┘                    
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │      Deploy and manage your institutional-grade              │  │
│  │            agentic trading system                            │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  🚀 Deploy          │  💱 Trade            │  📊 Analyze    │  │
│  │  • Setup trading    │  • CEX: Binance,    │  • Portfolio   │  │
│  │    infrastructure   │    OKX, Coinbase    │    tracking    │  │
│  │  • Install bots     │  • DEX: Uniswap,    │  • Market data │  │
│  │  • Configure APIs   │    Jupiter, Raydium │  • Performance │  │
│  │                     │                      │                │  │
│  │  🔐 Secure          │  🤖 Automate        │  🎯 Optimize   │  │
│  │  • Encrypted keys   │  • Trading bots     │  • Strategies  │  │
│  │  • Hardware wallet  │  • Market making    │  • Parameters  │  │
│  │  • API management   │  • Arbitrage        │  • Risk mgmt   │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  AI-optimized single point of entry for all Hummingbot users       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 4: Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Intelligent Architecture                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─────────────────────────────────────────────────────────┐       │
│ │                     hummbot MCP Server                    │       │
│ │                                                           │       │
│ │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │       │
│ │  │   Prompts   │  │    Tools    │  │  Resources  │     │       │
│ │  ├─────────────┤  ├─────────────┤  ├─────────────┤     │       │
│ │  │ • install   │  │ place_order │  │ • configs   │     │       │
│ │  │ • add-keys  │  │ get_balance │  │ • status    │     │       │
│ │  │ • portfolio │  │ deploy_bot  │  │ • logs      │     │       │
│ │  │ • place-    │  │ cancel_order│  │ • docs      │     │       │
│ │  │   order     │  │ + 20 more   │  │             │     │       │
│ │  └─────────────┘  └─────────────┘  └─────────────┘     │       │
│ │                                                           │       │
│ │         Direct connections to each service:               │       │
│ └─────┬──────────┬────────────┬───────────┬────────────────┘       │
│       │          │            │           │                        │
│       ▼          ▼            ▼           ▼                        │
│ ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│ │Hummingbot │ │Dashboard │ │ Gateway  │ │CoinGecko │             │
│ │    API    │ │(Optional)│ │(Optional)│ │(Optional)│             │
│ │ (REQUIRED)│ │          │ │          │ │          │             │
│ │           │ │ • Web UI │ │ • DEX    │ │ • Market │             │
│ │ • CEX     │ │ • Charts │ │   Trading│ │   Data   │             │
│ │   Trading │ │ • P&L    │ │ • ETH &  │ │ • Prices │             │
│ │ • Bot Mgmt│ │          │ │   Solana │ │ • Pools  │             │
│ └───────────┘ └──────────┘ └──────────┘ └──────────┘             │
│                                                             │       │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 5: The Four Modules

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Understanding the Four Modules                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │               Hummingbot-API (Always Required)               │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  🏛️ The Foundation                                          │  │
│  │                                                              │  │
│  │  • Connects to all major CEXs (Binance, OKX, Coinbase...)  │  │
│  │  • Manages trading bots and strategies                      │  │
│  │  • Handles spot and perpetual trading                       │  │
│  │  • Provides unified API for all operations                  │  │
│  │  • Includes backtesting and paper trading                  │  │
│  │                                                              │  │
│  │  📍 Runs on: http://localhost:8000                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  Gateway (Optional)                          │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  🌉 The DeFi Bridge                                         │  │
│  │                                                              │  │
│  │  • Connects to DEXs on Ethereum and Solana                 │  │
│  │  • Supports Uniswap, Jupiter, Raydium, and more           │  │
│  │  • Manages blockchain wallets and transactions             │  │
│  │  • Handles gas optimization and slippage                   │  │
│  │  • Enables cross-chain trading strategies                  │  │
│  │                                                              │  │
│  │  📍 Runs on: http://localhost:15888                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  Dashboard (Optional)                         │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  📊 The Web Interface                                        │  │
│  │                                                              │  │
│  │  • Real-time visualization of bots and strategies           │  │
│  │  • Portfolio tracking across all exchanges                  │  │
│  │  • Performance metrics and analytics                        │  │
│  │  • Trade history and P&L reporting                          │  │
│  │  • Remote monitoring from any browser                       │  │
│  │                                                              │  │
│  │  📍 Runs on: http://localhost:3000                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  CoinGecko (Optional)                        │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  📊 The Market Intelligence                                  │  │
│  │                                                              │  │
│  │  • Real-time price data across all markets                 │  │
│  │  • Token discovery and contract verification               │  │
│  │  • Liquidity pool analytics                                │  │
│  │  • Market trends and opportunities                          │  │
│  │  • Historical data for strategy optimization               │  │
│  │                                                              │  │
│  │  📍 Runs as: MCP subprocess                                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 6: Installation Demo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Installation Demo                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  First, clone and build hummbot:                                   │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │  $ git clone https://github.com/hummingbot/hummbot.git  │      │
│  │  $ cd hummbot && npm install && npm run build           │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              Claude Desktop                              │      │
│  ├─────────────────────────────────────────────────────────┤      │
│  │  $ claude mcp add hummbot node -- $(pwd)/dist/index.js  │      │
│  │  ✅ Ready! Use /hummbot:install                         │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              Cursor & VSCode                             │      │
│  ├─────────────────────────────────────────────────────────┤      │
│  │  Add to .cursorrules or .vscode/settings.json:          │      │
│  │  {                                                       │      │
│  │    "mcpServers": {                                      │      │
│  │      "hummbot": {                                       │      │
│  │        "command": "node",                               │      │
│  │        "args": ["./hummbot/dist/index.js"]             │      │
│  │      }                                                  │      │
│  │    }                                                    │      │
│  │  }                                                       │      │
│  │  ✅ Ready! Use @hummbot in chat                         │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              Claude Code                                 │      │
│  ├─────────────────────────────────────────────────────────┤      │
│  │  Edit ~/.mcp.json:                                      │      │
│  │  {                                                       │      │
│  │    "mcpServers": {                                      │      │
│  │      "hummbot": {                                       │      │
│  │        "command": "node",                               │      │
│  │        "args": ["/path/to/hummbot/dist/index.js"]      │      │
│  │      }                                                  │      │
│  │    }                                                    │      │
│  │  }                                                       │      │
│  │  ✅ Ready! Use /hummbot:install                         │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 7: 9 Powerful Prompts

```
┌─────────────────────────────────────────────────────────────────────┐
│                        9 Powerful Prompts                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    🚀 Setup (3)                              │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  /hummbot:install         Install trading infrastructure     │  │
│  │  /hummbot:add-keys        Connect exchanges & wallets        │  │
│  │  /hummbot:portfolio       View complete holdings             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    💱 Trade (3)                              │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  /hummbot:explain         Get help on any trading topic      │  │
│  │  /hummbot:get-info        Token data & market intelligence   │  │
│  │  /hummbot:place-order     Execute trades on CEX/DEX          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    🤖 Automate (3)                           │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  /hummbot:config-strategy  Configure trading strategies      │  │
│  │  /hummbot:deploy-bot       Launch automated trading bots     │  │
│  │  /hummbot:monitor-bot      Track performance in real-time    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 8: Setup Prompts Demo

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Setup Prompts in Action                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:install                                │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Install Hummingbot for me"                             │  │
│  │                                                              │  │
│  │  🤖 "I'll help you install Hummingbot! Let me ask:          │  │
│  │      1. Docker or Source? [Docker]                          │  │
│  │      2. Include web UI? [Yes]                               │  │
│  │      3. Include DEX trading? [Yes]                          │  │
│  │      4. Include market data? [Yes]"                         │  │
│  │                                                              │  │
│  │  ▓▓▓▓▓▓▓▓▓▓░░░░░ Installing components...                 │  │
│  │                                                              │  │
│  │  ✅ All services installed and healthy!                     │  │
│  │     • Hummingbot-API: http://localhost:8000                │  │
│  │     • Dashboard: http://localhost:3000                      │  │
│  │     • Gateway: http://localhost:15888                      │  │
│  │     • CoinGecko: Active                                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:add-keys                               │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Add my Binance API keys"                               │  │
│  │                                                              │  │
│  │  🤖 "Setting up Binance API keys:                           │  │
│  │      1. Go to Binance.com → API Management                 │  │
│  │      2. Create API key with spot trading enabled           │  │
│  │      3. Enter your API key: ****                           │  │
│  │      4. Enter your secret: ****"                            │  │
│  │                                                              │  │
│  │  ✅ Connected! Balance: 0.5 BTC, 10,000 USDT               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:portfolio                              │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Show me my complete portfolio"                          │  │
│  │                                                              │  │
│  │  🤖 Total Portfolio Value: $125,432 (+2.34%)                │  │
│  │                                                              │  │
│  │  CEX Holdings: $81,912     │ DEX Holdings: $43,520         │  │
│  │  • Binance: $45,123        │ • Ethereum: $28,456          │  │
│  │  • OKX: $36,789            │ • Solana: $15,123            │  │
│  │                                                              │  │
│  │  Best Performer: SOL +12.3% | Risk Score: Low              │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 9: Trade Prompts Demo

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Trade Prompts in Action                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:explain                                │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Explain inventory skew in market making"               │  │
│  │                                                              │  │
│  │  🤖 "Inventory skew adjusts your bid/ask spreads based      │  │
│  │      on your current inventory to manage risk:              │  │
│  │                                                              │  │
│  │      • High BTC inventory → Tighter ask, wider bid         │  │
│  │      • Low BTC inventory → Tighter bid, wider ask          │  │
│  │                                                              │  │
│  │      Example: If target is 50% BTC but you have 70%:       │  │
│  │      - Ask spread: 0.08% (sell more aggressively)          │  │
│  │      - Bid spread: 0.12% (buy less aggressively)           │  │
│  │                                                              │  │
│  │  📚 Related: Risk Management, Order Spreads                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:get-info                               │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Get info on PEPE token"                                │  │
│  │                                                              │  │
│  │  🤖 PEPE Token Analysis:                                     │  │
│  │     • Price: $0.00001234 (+15.3% 24h)                      │  │
│  │     • Market Cap: $5.2B | Volume: $892M                    │  │
│  │                                                              │  │
│  │     Best Venues:                                            │  │
│  │     • CEX: Binance PEPE/USDT - $234M vol                   │  │
│  │     • DEX: Uniswap V3 PEPE/WETH - $89M vol                 │  │
│  │                                                              │  │
│  │     💡 1.2% CEX/DEX spread - arbitrage opportunity!        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:place-order                            │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Buy 0.1 BTC on Binance"                                │  │
│  │                                                              │  │
│  │  🤖 "Placing market buy order for 0.1 BTC..."               │  │
│  │                                                              │  │
│  │  ✅ Order Executed!                                          │  │
│  │     • Bought: 0.1 BTC                                       │  │
│  │     • Price: $63,482                                        │  │
│  │     • Total: $6,348.20 USDT                                 │  │
│  │     • Order ID: 12345678                                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 10: Automate Prompts Demo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Automate Prompts in Action                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:config-strategy                        │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Configure a market making strategy for ETH/USDT"       │  │
│  │                                                              │  │
│  │  🤖 "Let's configure your market making strategy:           │  │
│  │      Exchange: Binance                                       │  │
│  │      Pair: ETH/USDT                                         │  │
│  │      Spread: 0.1% (recommended for ETH)                     │  │
│  │      Order Amount: 0.5 ETH                                  │  │
│  │      Inventory Target: 50% (balanced)                       │  │
│  │      Max Order Age: 30 seconds                              │  │
│  │                                                              │  │
│  │  ✅ Config saved as 'mm_eth_balanced_v1'"                   │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:deploy-bot                             │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Deploy bot with mm_eth_balanced_v1"                    │  │
│  │                                                              │  │
│  │  🤖 "Deploying bot with your configuration..."              │  │
│  │                                                              │  │
│  │  ✅ Bot deployed: bot_mm_eth_001                            │  │
│  │     • Status: Running (Paper Trade Mode)                    │  │
│  │     • Strategy: Market Making                               │  │
│  │     • Pair: ETH/USDT                                        │  │
│  │     • Dashboard: http://localhost:8000/bots/bot_mm_eth_001  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              /hummbot:monitor-bot                            │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  👤 "Monitor bot_mm_eth_001"                                │  │
│  │                                                              │  │
│  │  📊 Live Performance (24h):                                  │  │
│  │                                                              │  │
│  │  • Trades: 156         • Win Rate: 62.8%                   │  │
│  │  • PnL: +$234.56       • APR: 8.7%                         │  │
│  │  • Volume: 78.5 ETH    • Sharpe: 1.87                      │  │
│  │                                                              │  │
│  │  Active Orders: 6/6    Inventory: 49.8% ETH (Balanced ✓)   │  │
│  │                                                              │  │
│  │  💡 "Market stable - maintaining current spreads"           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 11: Unified Bot Management

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Unified Bot Management                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Complete Bot Lifecycle - From Strategy to Profits                 │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 1: Configure Strategy                                   │  │
│  │ 👤 "/hummbot:config-strategy market_making"                  │  │
│  │ 🤖 Strategy configured: mm_btc_conservative_v1               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                           ↓                                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 2: Deploy Bot                                           │  │
│  │ 👤 "/hummbot:deploy-bot mm_btc_conservative_v1"              │  │
│  │ 🤖 Bot deployed: bot_mm_btc_001 (Paper Trade Mode)          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                           ↓                                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 3: Monitor Performance                                  │  │
│  │ 👤 "/hummbot:monitor-bot bot_mm_btc_001"                     │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  📊 Live Dashboard                 Status: 🟢 RUNNING       │  │
│  │                                                              │  │
│  │  ┌──────────────────────┬──────────────────────┐           │  │
│  │  │     Buy Orders       │     Sell Orders      │           │  │
│  │  ├──────────────────────┼──────────────────────┤           │  │
│  │  │ $63,450 | 0.01 BTC  │ $63,550 | 0.01 BTC  │           │  │
│  │  │ $63,400 | 0.01 BTC  │ $63,600 | 0.01 BTC  │           │  │
│  │  │ $63,350 | 0.01 BTC  │ $63,650 | 0.01 BTC  │           │  │
│  │  └──────────────────────┴──────────────────────┘           │  │
│  │                                                              │  │
│  │  Performance:           │  Risk Metrics:                   │  │
│  │  • Trades: 127         │  • Inventory: Balanced ✓         │  │
│  │  • PnL: +$234.56       │  • Max Drawdown: 1.2%           │  │
│  │  • APR: 8.7%           │  • Sharpe Ratio: 1.87           │  │
│  │                                                              │  │
│  │  💡 "Widening spreads due to increased volatility"          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 12: Real-time Market Data

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Real-time Market Data                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  👤 "Find the best liquidity pools for PEPE token"                 │
│                                                                     │
│  🤖 Searching for PEPE liquidity pools...                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Top PEPE Liquidity Pools                        │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  1. Uniswap V3 - PEPE/WETH                                  │  │
│  │     ├─ TVL: $45.2M          ├─ 24h Volume: $12.3M          │  │
│  │     ├─ APR: 34.5%           └─ Price: $0.00001234          │  │
│  │     │                                                        │  │
│  │     │  Liquidity Distribution                               │  │
│  │     │     ▁▂▄█████▄▂▁                                      │  │
│  │     │  0.00001  Price  0.00002                             │  │
│  │                                                              │  │
│  │  2. Uniswap V2 - PEPE/USDC                                  │  │
│  │     ├─ TVL: $23.1M          ├─ 24h Volume: $5.6M           │  │
│  │     ├─ APR: 18.2%           └─ Price: $0.00001235          │  │
│  │                                                              │  │
│  │  3. SushiSwap - PEPE/ETH                                    │  │
│  │     ├─ TVL: $8.9M           ├─ 24h Volume: $2.1M           │  │
│  │     ├─ APR: 22.1%           └─ Price: $0.00001232          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Price Trend (7d)                          │  │
│  │  $0.000015 ┼                           ╱─╲                  │  │
│  │  $0.000012 ┼─────────────────────────────╲─                │  │
│  │  $0.000009 ┼                                                │  │
│  │            └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─                 │  │
│  │            -7d                        Now                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  💡 Recommendation: Uniswap V3 has best liquidity & volume        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Slide 13: Benefits & Next Steps

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Why Choose hummbot?                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Key Benefits                              │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  ⚡ Fast Setup          │  🧠 AI-Optimized Design          │  │
│  │  15 min vs 5 hours     │  Built for MCP & LLMs             │  │
│  │                         │                                    │  │
│  │  🔄 Unified Interface   │  📈 Progressive Growth            │  │
│  │  CEX + DEX in one      │  Start simple, scale up           │  │
│  │                         │                                    │  │
│  │  🔐 Secure by Default   │  🌍 Open Source                   │  │
│  │  Encrypted storage      │  Community driven                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Get Started Today!                        │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  1. Install hummbot:                                         │  │
│  │     $ claude mcp add hummbot                                 │  │
│  │                                                              │  │
│  │  2. Install your trading infrastructure:                     │  │
│  │     "Install Hummingbot for me"                              │  │
│  │                                                              │  │
│  │  3. Start trading:                                           │  │
│  │     "Place a buy order for 0.1 BTC on Binance"              │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                      Resources                               │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  📚 Website:   https://humm.bot                              │  │
│  │  💬 Discord:   discord.gg/hummingbot                        │  │
│  │  🐦 Twitter:   @hummingbot_org                              │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```