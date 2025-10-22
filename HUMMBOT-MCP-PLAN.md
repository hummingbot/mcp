# hummbot: Your Own Private Trading Agent

## Executive Summary

`hummbot`, the Hummingbot MCP Server, is the new AI-optimized single point of entry for all Hummingbot users, large and small. Accessible from any MCP-aware AI application like Cursor or CLI tool like Claude Code, it helps the user deploy and manage a custom institutional-grade agentic trading system using the open source Hummingbot framework.

Architecturally, `hummbot` includes prompts and tools that dramatically simplify the installation, configuration, and usage of the Hummingbot ecosystem by providing natural language interfaces to:
- **Hummingbot-API** (always installed): CEX trading, spot & perpetuals, bot management
- **Dashboard** (optional): Web UI for visualizing bots, strategies, and performance
- **Gateway** (optional): DEX trading on Ethereum/EVM and Solana
- **CoinGecko** (optional): Market data, token discovery, pool analytics

Users interact with hummbot through a unified tool interface - they don't need to know which backend service handles their request:
```typescript
// Same tool, different venues - routed automatically
await place_order({ venue: "binance", ... })  // → Hummingbot-API
await place_order({ venue: "uniswap", ... })  // → Gateway
```

## Installation

### Adding hummbot to Claude Code and Desktop

```bash
# Clone the hummbot repository
git clone https://github.com/hummingbot/hummbot.git
cd hummbot

# Install dependencies
npm install

# Build the project
npm run build

# Add to Claude Desktop
claude mcp add hummbot node -- $(pwd)/dist/index.js
```

### Adding hummbot to Gemini / Cursor

```bash
# For Gemini Code or other MCP-compatible clients
# Add to your MCP configuration file (usually ~/.mcp.json or project .mcp.json)
{
  "mcpServers": {
    "hummbot": {
      "command": "node",
      "args": ["/path/to/hummbot/dist/index.js"],
      "env": {
        "HUMMBOT_HOME": "/path/to/hummbot-data"
      }
    }
  }
}
```

### Environment Variables

- `HUMMBOT_HOME`: Directory for storing configs, logs, and data (default: `~/.hummbot`)
- `HBAPI_URL`: Hummingbot-API URL if running externally (default: `http://localhost:8000`)
- `DASHBOARD_URL`: Dashboard URL if running externally (default: `http://localhost:3000`)
- `GATEWAY_URL`: Gateway URL if running externally (default: `http://localhost:15888`)
- `COINGECKO_API_KEY`: Your CoinGecko API key for market data

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     hummbot MCP Server                  │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Prompts   │  │    Tools    │  │  Resources  │   │
│  │             │  │             │  │             │   │
│  │ • install   │  │ • Unified   │  │ • configs   │   │
│  │ • add-keys  │  │   Interface │  │ • status    │   │
│  │ • portfolio │  │ • Auto      │  │ • logs      │   │
│  │ • place-    │  │   Routing   │  │ • docs      │   │
│  │   order     │  │             │  │             │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                         │
│         Direct connections to each service:             │
│         ┌─────────┬──────────┬──────────┬──────────┐   │
└─────────┼─────────┼──────────┼──────────┼──────────┼───┘
          │         │          │          │          │
          ▼         ▼          ▼          ▼          ▼
┌─────────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────────┐
│ Hummingbot-API  │ │ Dashboard  │ │  Gateway   │ │   CoinGecko     │
│(Always Required)│ │ (Optional) │ │ (Optional) │ │  (Optional)     │
│                 │ │            │ │            │ │                 │
│ • CEX Trading   │ │ • Web UI   │ │ • DEX      │ │ • Market Data   │
│ • Spot & Perps  │ │ • Real-time│ │   Trading  │ │ • Price Feeds   │
│ • Bot Management│ │   Charts   │ │ • Ethereum │ │ • Token Search  │
│ • Strategies    │ │ • Portfolio│ │   /EVM     │ │ • Pool Analytics│
│ • Portfolio     │ │   View     │ │ • Solana   │ │ • MCP Subprocess│
│ • HTTP REST API │ │ • HTTP     │ │ • HTTP API │ │                 │
│                 │ │   Server   │ │            │ │                 │
└─────────────────┘ └────────────┘ └────────────┘ └─────────────────┘
     Always               Optional       Optional        Optional
   Installed              Service        Service         Service
```

## Core Components

### 1. MCP Prompts (9 Total)

The prompts are organized into three functional groups:

#### 🚀 Setup Prompts (3)

##### 1.1 `install` - Intelligent Installation Wizard
**Purpose**: Replace complex installation workflows with guided setup

**Arguments**:
- `method`: "docker" | "source"
- `with_dashboard`: boolean (whether to include Dashboard for web UI)
- `with_gateway`: boolean (whether to include Gateway for DeFi operations)
- `with_coingecko`: boolean (whether to include CoinGecko for market data)
- `options`: {
    "HBAPI_PORT": number (default: 8000),
    "GATEWAY_PORT": number (default: 15888),
    "GATEWAY_USE_SSL": boolean (default: false)
  }

**Workflow**:
1. System requirements check
2. Docker/source installation detection
3. Ask if user wants web UI (Dashboard)
4. Ask if user wants DeFi trading capabilities (Gateway)
5. Ask if user wants market data (CoinGecko MCP)
6. Port availability verification
7. Database setup (PostgreSQL for Hummingbot-API)
8. Message broker setup (EMQX for Hummingbot-API)
9. If Dashboard included, setup Dashboard server
10. If DeFi included, setup Gateway
11. If market data included, configure CoinGecko subprocess
12. SSL certificate generation
13. Service health checks
14. Return connection details

##### 1.2 `add-keys` - Credential Management
**Purpose**: Simplified key management for exchanges and chains

**Arguments**:
- `venue`: string (e.g., "binance", "okx", "ethereum", "solana")
- `testnet`: boolean

**Workflow**:
1. Detect if venue is CEX or blockchain
2. For CEX: Guide API key creation
3. For blockchain: Guide wallet setup (private key or hardware wallet)
4. Credential format validation
5. Security recommendations
6. Encrypted storage setup
7. Connection testing
8. Balance verification

##### 1.3 `portfolio` - Comprehensive Portfolio View
**Purpose**: Unified view of all positions across CEX and DEX

**Arguments**:
- `include_cex`: boolean
- `include_dex`: boolean
- `currency`: "USD" | "EUR" | "BTC" | "ETH"
- `show_details`: boolean

**Output Structure**:
```json
{
  "total_value": 50000.00,
  "currency": "USD",
  "cex_positions": {
    "exchanges": ["binance", "okx"],
    "spot_balances": {},
    "perp_positions": {},
    "open_orders": {}
  },
  "dex_positions": {
    "chains": ["ethereum", "solana"],
    "wallet_balances": {},
    "lp_positions": {},
    "pending_txs": {}
  },
  "summary": {
    "24h_change": 2.5,
    "best_performer": "ETH",
    "risk_metrics": {}
  }
}
```

#### 💱 Trade Prompts (3)

##### 1.4 `explain` - Intelligent Documentation Assistant
**Purpose**: Context-aware explanations from Hummingbot documentation

**Arguments**:
- `query`: string (user's question or topic)
- `context`: string (optional - current task context)
- `detail_level`: "brief" | "detailed" | "examples" (default: "brief")

**Workflow**:
1. Search LLM-optimized documentation index
2. Retrieve relevant sections from multiple sources
3. Synthesize answer based on query context
4. Include practical examples when helpful
5. Provide links to detailed documentation
6. Suggest related topics or next steps

**Output Structure**:
```json
{
  "query": "how does inventory skew work",
  "answer": "Inventory skew adjusts spreads based on your asset balance...",
  "examples": [
    {
      "scenario": "High base inventory",
      "adjustment": "Tighter ask spread, wider bid spread",
      "code": "inventory_target_base_pct: 0.5"
    }
  ],
  "related_topics": [
    "Inventory risk management",
    "Order spread adjustment",
    "Market making parameters"
  ],
  "documentation_links": [
    "hummbot://docs/strategies/market-making#inventory-skew",
    "hummbot://docs/risk-management/inventory"
  ]
}
```

##### 1.5 `get-info` - Token & Market Intelligence
**Purpose**: Comprehensive token and market information

**Arguments**:
- `identifier`: string (token address, symbol, or name)
- `chain`: string (optional - for address lookup)
- `info_type`: "overview" | "markets" | "pools" | "technical" | "all"

**Workflow**:
1. Resolve token identity (symbol/address/name)
2. Query CoinGecko for comprehensive data
3. Aggregate information from multiple sources
4. Analyze liquidity and trading venues
5. Calculate key metrics and ratios
6. Generate trading recommendations

**Output Structure**:
```json
{
  "token": {
    "name": "Pepe",
    "symbol": "PEPE",
    "address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
    "chain": "ethereum",
    "decimals": 18
  },
  "market_data": {
    "price_usd": 0.00001234,
    "market_cap": 5189000000,
    "volume_24h": 892000000,
    "price_change_24h": 15.3,
    "circulating_supply": 420690000000000
  },
  "trading_venues": {
    "cex": [
      {"exchange": "Binance", "pairs": ["PEPE/USDT", "PEPE/USDC"], "volume_24h": 234000000},
      {"exchange": "OKX", "pairs": ["PEPE/USDT"], "volume_24h": 123000000}
    ],
    "dex": [
      {"protocol": "Uniswap V3", "pool": "PEPE/WETH", "tvl": 45200000, "volume_24h": 89000000},
      {"protocol": "Uniswap V2", "pool": "PEPE/USDT", "tvl": 23100000, "volume_24h": 34000000}
    ]
  },
  "liquidity_analysis": {
    "total_liquidity": 123000000,
    "liquidity_score": 8.5,
    "slippage_1k_usd": 0.02,
    "slippage_10k_usd": 0.15,
    "best_venue_large_orders": "Binance"
  },
  "trading_recommendations": [
    "High liquidity on Binance - suitable for large orders",
    "Uniswap V3 offers best DEX liquidity",
    "Consider arbitrage between CEX/DEX (1.2% spread)"
  ]
}
```

##### 1.6 `place-order` - Universal Order Placement
**Purpose**: Single interface for CEX and DEX orders

**Arguments**:
- `venue`: "cex" | "dex"
- `exchange`: string
- `pair`: string
- `side`: "buy" | "sell"
- `type`: "market" | "limit"
- `amount`: number
- `price`: number (for limit orders)
- `advanced`: {
    "time_in_force": string,
    "post_only": boolean,
    "reduce_only": boolean (perps),
    "slippage": number (DEX)
  }

#### 🤖 Automate Prompts (3)

##### 1.7 `config-strategy` - Strategy Configuration Wizard
**Purpose**: Interactive configuration of trading strategy parameters

**Arguments**:
- `controller`: string (e.g., "market_making", "arbitrage", "liquidity_mining", "cross_exchange_market_making")
- `exchange`: string (optional, for exchange-specific strategies)
- `trading_pair`: string (optional)

**Workflow**:
1. Load controller schema from Hummingbot-API
2. Present strategy description and key parameters
3. Guide through required parameters with explanations
4. Validate parameter ranges and dependencies
5. Suggest optimal values based on market conditions
6. Generate complete strategy configuration
7. Option to backtest before deployment
8. Save configuration with descriptive name

**Output Structure**:
```json
{
  "controller": "market_making",
  "config_name": "mm_btc_conservative_v1",
  "parameters": {
    "exchange": "binance",
    "trading_pair": "BTC-USDT",
    "bid_spread": 0.001,
    "ask_spread": 0.001,
    "order_amount": 0.01,
    "order_levels": 3,
    "order_level_spread": 0.001,
    "filled_order_delay": 10,
    "inventory_target_base_pct": 0.5
  },
  "risk_management": {
    "max_order_age": 1800,
    "inventory_range_multiplier": 1.0,
    "stop_loss": 0.02
  }
}
```

##### 1.8 `deploy-bot` - Bot Deployment Assistant
**Purpose**: Deploy and configure a trading bot with strategy

**Arguments**:
- `controller_config`: string (name of saved configuration from config-strategy)
- `bot_name`: string (optional, auto-generated if not provided)
- `paper_trade`: boolean (default: true for first-time users)
- `auto_start`: boolean (default: false)

**Workflow**:
1. Load controller configuration
2. Validate exchange connectivity and balances
3. Check risk parameters and position sizes
4. Create bot instance in Hummingbot-API
5. Configure monitoring and alerts
6. Set up performance tracking
7. Initialize in paper trade mode if requested
8. Return bot ID and monitoring dashboard URL

**Output Structure**:
```json
{
  "bot_id": "bot_mm_btc_001",
  "controller": "market_making",
  "status": "initialized",
  "mode": "paper_trade",
  "monitoring": {
    "dashboard_url": "http://localhost:8000/bots/bot_mm_btc_001",
    "websocket": "ws://localhost:8000/ws/bot_mm_btc_001"
  },
  "next_steps": [
    "Review bot configuration",
    "Start bot when ready",
    "Monitor performance metrics"
  ]
}
```

##### 1.9 `monitor-bot` - Real-time Bot Monitoring
**Purpose**: Interactive monitoring and control of running bots

**Arguments**:
- `bot_id`: string (specific bot ID or "all" for overview)
- `timeframe`: "1h" | "24h" | "7d" | "30d" (default: "24h")
- `metrics`: string[] (optional, specific metrics to focus on)

**Workflow**:
1. Connect to bot's real-time data stream
2. Display current status and health metrics
3. Show active orders and recent trades
4. Calculate performance statistics
5. Alert on anomalies or issues
6. Provide quick actions (pause, adjust, stop)
7. Generate performance report

**Output Structure**:
```json
{
  "bot_id": "bot_mm_btc_001",
  "status": "running",
  "uptime": "14h 23m",
  "performance": {
    "total_trades": 156,
    "profitable_trades": 98,
    "total_pnl_usd": 234.56,
    "roi_percentage": 2.34,
    "sharpe_ratio": 1.87
  },
  "current_state": {
    "active_orders": 6,
    "base_inventory": 0.502,
    "quote_inventory": 10234.56,
    "current_spread": 0.0012
  },
  "alerts": [],
  "recommendations": [
    "Consider widening spreads - volatility increased",
    "Inventory balanced - no action needed"
  ]
}
```

### 2. MCP Tools (20-30 Total)

The tools are organized by functionality, abstracting away the underlying services:

#### 2.1 Trading Tools (8)
- `place_order` - Place order on any exchange (CEX or DEX)
- `cancel_order` - Cancel order
- `get_orders` - Get open orders
- `get_trades` - Get trade history
- `get_positions` - Get positions (spot/perps/LP)
- `close_position` - Close position
- `quote_swap` - Get swap quote (DEX)
- `execute_swap` - Execute swap (DEX)

#### 2.2 Portfolio & Market Tools (6)
- `get_balances` - Get token balances (CEX/DEX)
- `get_portfolio` - Get comprehensive portfolio view
- `get_orderbook` - Get order book
- `get_candles` - Get candle data
- `get_markets` - Get available markets

#### 2.3 Bot & Strategy Tools (6)
- `list_bots` - List all bots
- `deploy_bot` - Deploy new bot
- `start_bot` - Start bot instance
- `stop_bot` - Stop bot instance
- `get_bot_status` - Get bot status
- `configure_strategy` - Configure trading strategy

#### 2.4 Configuration Tools (5)
- `list_accounts` - List trading accounts
- `add_account` - Add new account/wallet
- `remove_account` - Remove account/wallet
- `update_config` - Update configuration
- `get_config` - Get configuration

#### 2.5 System Tools (5)
- `check_health` - Check system health
- `view_logs` - View service logs
- `restart_service` - Restart service

### Optional Market Data Tools (When CoinGecko Enabled)
If user chooses to include market data during deployment, these additional tools become available:
- `search_token` - Search for tokens by name/symbol
- `get_token_info` - Get detailed token information
- `find_pools` - Find liquidity pools for a token
- `get_pool_info` - Get pool analytics
- `get_trending` - Get trending tokens/pools

### 3. MCP Resources

**Configuration Resources**
- `hummbot://config/hummingbot-api` - Hummingbot-API configuration
- `hummbot://config/gateway` - Gateway configuration (if installed)
- `hummbot://config/system` - System configuration
- `hummbot://config/coingecko` - CoinGecko settings (if enabled)

**Status Resources**
- `hummbot://logs/services` - All services status
- `hummbot://status/bots` - All bots status
- `hummbot://status/connections` - Exchange/chain connections
- `hummbot://status/market-data` - Market data feed status

**Documentation Resources**
- `hummbot://docs/llm` - LLM-optimized documentation index

### 4. LLM-Optimized Documentation

The `explain` prompt requires an LLM-optimized version of the Hummingbot documentation. This will be generated using `mkdocs-llms-txt` plugin:

**Implementation Approach**:
1. Add `mkdocs-llms-txt` to the https://github.com/hummingbot/hummingbot-site repository
2. Configure the plugin in `mkdocs.yml`:
   ```yaml
   plugins:
     - llms.txt:
         output_file: "llms.txt"
         include_meta: true
         include_nav: true
         hierarchical: true
   ```
3. The plugin will generate a structured text file optimized for LLM consumption
4. hummbot MCP server will download and index this file during initialization
5. The `explain` prompt will use vector search to find relevant sections
6. Periodic updates will ensure documentation stays current

**Benefits**:
- Structured format optimized for LLM understanding
- Preserves documentation hierarchy and relationships
- Includes metadata for better context
- Enables semantic search across all documentation
- Reduces token usage while improving accuracy

## Implementation Details

### Project Structure (Following Gateway MCP Pattern)
```
hummbot/
├── src/
│   ├── index.ts                 # MCP server entry point
│   ├── server.ts                # Server configuration and setup
│   ├── version.ts               # Version management
│   ├── types.ts                 # TypeScript type definitions
│   ├── schema.ts                # Zod schemas for validation
│   ├── toolDefinitions.ts       # Tool metadata and schemas
│   ├── tools.ts                 # Tool handler implementations
│   ├── promptDefinitions.ts     # Prompt metadata and schemas
│   ├── prompts.ts               # Prompt handler implementations
│   ├── resources.ts             # Resource handlers
│   ├── services/
│   │   ├── api-clients/
│   │   │   ├── hummingbot-api-client.ts  # HBAPI HTTP client
│   │   │   └── gateway-client.ts         # Gateway HTTP client
│   │   ├── subprocess-manager.ts          # Manages subprocesses
│   │   ├── deployment-manager.ts          # Deployment orchestration
│   │   ├── docker-manager.ts              # Docker operations
│   │   ├── config-manager.ts              # Configuration management
│   │   └── tool-router.ts                 # Routes tools to services
│   ├── utils/
│   │   ├── tool-registry.ts     # Central tool registration
│   │   ├── validators.ts        # Input validation helpers
│   │   ├── formatters.ts        # Output formatting
│   │   └── crypto.ts            # Encryption utilities
│   └── resources/
│       ├── docs/                # Static documentation
│       ├── api-endpoints.json   # API reference
│       └── strategies.json      # Strategy catalog
├── templates/
│   ├── docker-compose/
│   │   ├── full-stack.yml       # Complete setup
│   │   ├── cex-only.yml         # Hummingbot-API only
│   │   └── cex-dex.yml          # HBAPI + Gateway
│   ├── configs/
│   │   ├── hummingbot-api/      # HBAPI config templates
│   │   └── gateway/             # Gateway config templates
│   └── scripts/
│       ├── install-deps.sh      # Install dependencies
│       └── health-check.sh      # Health monitoring
├── test/
│   ├── test-server.ts           # Test MCP server
│   ├── test-tools.ts            # Test tool implementations
│   └── test-deployment.ts       # Test deployment flows
├── docs/
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   └── TROUBLESHOOTING.md
├── package.json
├── tsconfig.json
└── README.md
```

### Key Technologies (Aligned with Gateway MCP)
- **Language**: TypeScript
- **MCP SDK**: @modelcontextprotocol/sdk
- **Schema Validation**: Zod (like Gateway MCP)
- **HTTP Client**: Fetch API or similar lightweight client
- **Docker SDK**: Dockerode for container management
- **Process Management**: Native child_process for subprocesses
- **Configuration**: YAML/JSON with Zod validation
- **Transport**: StdioServerTransport for MCP communication
- **Architecture**: Modular with clear separation of definitions/handlers

### Service Integration Architecture

The hummbot MCP server connects directly to each service independently:

#### Hummingbot-API Integration (Always Required)
- **Type**: REST API server (http://localhost:8000)
- **Purpose**: CEX trading, bot management, strategies
- **Integration**: Direct HTTP client with typed endpoints
- **Authentication**: API key based
- **Note**: This is the only mandatory service - always installed

#### Dashboard Integration (Optional)
- **Type**: Web server (http://localhost:3000)
- **Purpose**: Web UI for visualization and monitoring
- **Integration**: Starts/stops Dashboard server, connects via HTTP
- **Features**: Real-time charts, portfolio view, bot monitoring
- **Authentication**: Shared with Hummingbot-API

#### Gateway Integration (Optional)
- **Type**: REST API server (http://localhost:15888 or https if SSL enabled)
- **Purpose**: DEX trading on Ethereum/EVM and Solana
- **Integration**: Direct HTTP client with typed endpoints
- **Authentication**: Passphrase based
- **SSL Support**: Optional, disabled by default for easier local development

#### CoinGecko Integration (Optional)
- **Type**: Pure MCP server (subprocess)
- **Purpose**: Market data, token discovery, pool analytics
- **Integration**: StdioClientTransport subprocess
- **Pattern**: Same as Gateway MCP's CoinGecko integration

```typescript
// Service manager handles independent connections to each service
class ServiceManager {
  private hbApiClient: HummingbotApiClient;
  private dashboardClient?: DashboardClient;
  private gatewayClient?: GatewayApiClient;
  private coingeckoProcess?: ChildProcess;
  private coingeckoClient?: Client;
  
  async initialize(options: InstallOptions) {
    // Hummingbot-API is always required - direct connection
    this.hbApiClient = new HummingbotApiClient({
      url: options.hbApiUrl || process.env.HBAPI_URL || 'http://localhost:8000',
      apiKey: options.hbApiKey
    });
    
    // Dashboard is optional - direct connection
    if (options.with_dashboard) {
      this.dashboardClient = new DashboardClient({
        url: options.dashboardUrl || process.env.DASHBOARD_URL || 'http://localhost:3000',
        apiUrl: this.hbApiClient.url  // Dashboard needs to know where Hummingbot-API is
      });
      await this.dashboardClient.start();
    }
    
    // Gateway is optional - direct connection
    if (options.with_gateway) {
      this.gatewayClient = new GatewayApiClient({
        url: options.gatewayUrl || process.env.GATEWAY_URL || 'http://localhost:15888',
        passphrase: options.gatewayPassphrase
      });
    }
    
    // CoinGecko is optional - runs as MCP subprocess
    if (options.with_coingecko) {
      await this.startCoinGeckoSubprocess(options.coingeckoApiKey);
    }
  }
  
  private async startCoinGeckoSubprocess(apiKey?: string) {
    const transport = new StdioClientTransport({
      command: 'npx',
      args: ['-y', '@coingecko/coingecko-mcp@latest'],
      env: { 
        COINGECKO_DEMO_API_KEY: apiKey,
        PATH: process.env.PATH 
      }
    });
    
    this.coingeckoClient = new Client({
      name: 'hummbot',
      version: '1.0.0'
    });
    
    await this.coingeckoClient.connect(transport);
    // Proxy CoinGecko tools with consistent naming
  }
}
```

### Deployment Strategies

#### Docker Deployment Flow
```typescript
async function installWithDocker(options: InstallOptions) {
  // 1. Check Docker installation
  await checkDockerInstalled();
  
  // 2. Determine components to install
  const components = ['hummingbot-api'];  // Always required
  if (options.with_dashboard) components.push('dashboard');
  if (options.with_gateway) components.push('gateway');
  
  // 3. Pull/build images
  if (options.usePrebuilt) {
    await pullImages(components.map(c => `hummingbot/${c}:latest`));
  } else {
    await buildImages(components);
  }
  
  // 4. Generate docker-compose with custom ports and SSL settings
  const composeConfig = generateDockerCompose({
    ...options,
    ports: {
      hbapi: options.options?.HBAPI_PORT || 8000,
      gateway: options.options?.GATEWAY_PORT || 15888
    },
    gatewayUseSsl: options.options?.GATEWAY_USE_SSL || false
  });
  
  // 5. Setup volumes and networks
  await setupDockerEnvironment();
  
  // 6. Start services
  await dockerCompose.up(composeConfig);
  
  // 7. Wait for health checks
  await waitForServices(components);
  
  // 8. Initialize databases
  await initializePostgres();
  await initializeEMQX();
  
  // 9. Configure CoinGecko if requested
  if (options.with_coingecko) {
    await configureCoinGecko();
  }
  
  return getConnectionDetails();
}
```

#### Source Deployment Flow
```typescript
async function installFromSource(options: InstallOptions) {
  // 1. Check Node.js version
  await checkNodeVersion('>=20.0.0');
  
  // 2. Determine components
  const components = ['hummingbot-api'];  // Always required
  if (options.with_dashboard) components.push('dashboard');
  if (options.with_gateway) components.push('gateway');
  
  // 3. Clone repositories
  for (const component of components) {
    await cloneRepository(component, options.branch);
  }
  
  // 4. Install dependencies
  await installDependencies(components);
  
  // 5. Build projects
  await buildProjects(components);
  
  // 6. Setup databases
  await setupPostgres();
  await setupEMQX();
  
  // 7. Configure services with ports
  await configureServices({
    ...options,
    ports: {
      hbapi: options.options?.HBAPI_PORT || 8000,
      gateway: options.options?.GATEWAY_PORT || 15888
    }
  });
  
  // 8. Start with PM2
  await pm2.start(generatePM2Config(options));
  
  // 9. Configure CoinGecko if requested
  if (options.with_coingecko) {
    await configureCoinGecko();
  }
  
  // 10. Health checks
  await waitForServices(components);
  
  return getConnectionDetails();
}
```

### Security Considerations

1. **Credential Storage**
   - All credentials encrypted with user passphrase
   - Separate encryption keys for CEX and DEX
   - Hardware wallet support for DEX operations

2. **API Communication**
   - HTTPS by default in production
   - HTTP allowed only in development mode
   - API key rotation support

3. **Access Control**
   - MCP approval required for sensitive operations
   - Read-only resources for non-sensitive data
   - Audit logging for all operations

### User Experience Improvements

1. **Simplified Onboarding**
   ```
   User: "Help me set up Hummingbot"
   Assistant: "I'll help you deploy Hummingbot. Let me ask you a few questions:
   
   1. Installation method:
      - Docker (recommended for beginners)
      - From source (for developers)
   
   2. Do you want to trade on decentralized exchanges (DeFi)?
      - Yes (installs Gateway for Ethereum, Solana, etc.)
      - No (CEX only)
   
   3. Do you want real-time market data and token discovery?
      - Yes (includes CoinGecko for prices, pools, trends)
      - No (basic trading only)
   
   Based on your choices, I'll set up everything automatically."
   ```

2. **Intelligent Defaults**
   - Auto-detect system capabilities
   - Recommend Docker for beginners
   - Suggest testnet for first-time users
   - Preset optimal resource limits

3. **Progressive Disclosure**
   - Start with minimal options
   - Expose advanced settings only when needed
   - Provide sensible defaults for everything

4. **Real-time Feedback**
   - Live installation progress updates
   - Clear error messages with solutions
   - Health status indicators
   - Performance metrics dashboard

## Development Roadmap

### Phase 1: Core MCP Infrastructure (Week 1)
- [ ] Repository setup following Gateway MCP patterns
- [ ] Basic MCP server with tools, prompts, resources
- [ ] Zod schema definitions
- [ ] Tool registry and router implementation
- [ ] Test harness setup

### Phase 2: Hummingbot-API Integration (Week 2)
- [ ] HTTP client for Hummingbot-API
- [ ] CEX trading tools (place_order, cancel_order, etc.)
- [ ] Bot management tools
- [ ] Portfolio aggregation
- [ ] Error handling and retries

### Phase 3: Deployment System (Weeks 3-4)
- [ ] Install prompt implementation
- [ ] Docker detection and management
- [ ] Docker-compose generation
- [ ] PostgreSQL and EMQX setup automation
- [ ] Health check implementation

### Phase 4: Optional Services (Week 5)
- [ ] Gateway integration (HTTP client + optional subprocess)
- [ ] CoinGecko subprocess integration
- [ ] Subprocess lifecycle management
- [ ] Tool routing for DEX operations

### Phase 5: User Experience (Week 6)
- [ ] Interactive prompts (add-keys, portfolio, place-order)
- [ ] Resource handlers for configs/status/docs
- [ ] Progress feedback and error messages
- [ ] CLI integration testing

### Phase 6: Production Readiness (Week 7)
- [ ] Comprehensive test suite
- [ ] Documentation (README, QUICKSTART, API reference)
- [ ] Example workflows
- [ ] Performance optimization
- [ ] Security audit

### Phase 7: Advanced Features (Future)
- [ ] Strategy builder prompt
- [ ] Backtesting integration
- [ ] Multi-bot orchestration
- [ ] Cloud deployment options
- [ ] Web UI integration

## Key Architecture Benefits

### Unified Tool Interface

Users don't need to know which backend service handles their request. Each tool internally determines the appropriate service:
- CEX operations → Hummingbot-API (always available)
- DEX operations → Gateway (if installed)
- Market data → CoinGecko (if enabled)
- Visualization → Dashboard (if installed)

### Service Abstraction
```typescript
// User calls a single tool
await place_order({
  venue: "binance",  // Routes to Hummingbot-API
  pair: "BTC/USDT",
  side: "buy",
  amount: 0.1
});

await place_order({
  venue: "uniswap",  // Routes to Gateway
  pair: "ETH/USDC",
  side: "sell",
  amount: 1.0
});
```

## Technical Implementation Notes

### Following Gateway MCP Patterns
1. **Separation of Concerns**: Keep tool definitions separate from handlers
2. **Schema-First**: Use Zod for all parameter validation
3. **Tool Registry**: Central registration system for all tools
4. **Resource Pattern**: Use `hummbot://` URI scheme for read-only access
5. **Subprocess Management**: StdioClientTransport for MCP services

### Key Differences from Gateway MCP
1. **Multi-Service**: Routes to multiple backends (HBAPI, Gateway)
2. **Deployment Focus**: Heavy emphasis on installation/setup
3. **Bot Management**: Includes strategy and bot lifecycle tools
4. **Progressive Complexity**: Start with CEX, add DEX/data as needed

### Integration Points
```typescript
// Example: How tools determine which service to use
class PlaceOrderTool {
  async execute(params: PlaceOrderParams) {
    const venue = params.venue || params.exchange;
    
    // Each tool knows which service to connect to
    if (this.isCexVenue(venue)) {
      // Direct connection to Hummingbot-API
      return await this.serviceManager.hbApiClient.placeOrder(params);
    } else if (this.isDexVenue(venue)) {
      // Direct connection to Gateway
      if (!this.serviceManager.gatewayClient) {
        throw new Error('Gateway not installed. Run install prompt.');
      }
      return await this.serviceManager.gatewayClient.placeOrder(params);
    }
  }
}

// Example: Portfolio tool aggregates from multiple services
class PortfolioTool {
  async execute(params: PortfolioParams) {
    const results = [];
    
    // Always query Hummingbot-API (CEX positions)
    results.push(await this.serviceManager.hbApiClient.getPositions());
    
    // Query Gateway if available (DEX positions)
    if (this.serviceManager.gatewayClient) {
      results.push(await this.serviceManager.gatewayClient.getBalances());
    }
    
    // Aggregate and format results
    return this.formatPortfolio(results);
  }
}
```

## Conclusion

hummbot represents a paradigm shift in how users interact with the Hummingbot ecosystem. By providing a unified MCP interface that abstracts away service complexity, we enable:

1. **Simplified Onboarding**: One command to set up everything
2. **Unified Trading**: Same tools work for CEX and DEX
3. **Progressive Learning**: Start simple, add features as needed
4. **AI-Native Design**: Built for LLM interaction from the ground up

The architecture ensures users focus on trading strategies rather than infrastructure, while maintaining the flexibility and power that advanced users require.