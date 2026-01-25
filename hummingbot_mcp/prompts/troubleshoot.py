"""
Troubleshoot prompt - Help diagnose and fix common issues.
"""


def register_troubleshoot_prompts(mcp):
    """Register troubleshooting prompts."""

    @mcp.prompt()
    def troubleshoot() -> str:
        """Diagnose and fix common issues with Hummingbot API and trading bots.

        This prompt helps users:
        1. Identify the type of problem
        2. Run diagnostic checks
        3. Apply fixes for common issues
        """
        return """# Troubleshooting Guide

You are helping the user diagnose and fix issues with their Hummingbot setup. Let's systematically identify and resolve the problem.

## Step 1: Identify the Problem Category

Ask the user which category their issue falls into:

1. **Installation/Startup Issues** - API won't start, Docker problems
2. **Connection Issues** - Can't connect to API, MCP not working
3. **Exchange Issues** - API keys not working, can't fetch data
4. **Bot Issues** - Bot not starting, unexpected behavior
5. **Gateway/DEX Issues** - DEX operations failing
6. **Performance Issues** - Slow responses, timeouts

## Diagnostic Commands

Run these based on the problem category:

### For Installation/Startup Issues

Check Docker containers:
```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "hummingbot|postgres|emqx"
```

Check container logs:
```bash
docker compose -f ~/hummingbot-api/docker-compose.yml logs --tail=50 hummingbot-api
```

Check if ports are in use:
```bash
lsof -i :8000
lsof -i :5432
```

### For Connection Issues

Test API health:
```bash
curl -s http://localhost:8000/health
```

Test authentication:
```bash
curl -s -X POST http://localhost:8000/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

Check MCP configuration:
```
Use configure_api_servers() to see configured servers
```

### For Exchange Issues

List configured connectors:
```
Use setup_connector() with no arguments
```

Check portfolio (tests exchange connectivity):
```
Use get_portfolio_overview()
```

Test market data:
```
Use get_prices(connector_name="<exchange>", trading_pairs=["BTC-USDT"])
```

### For Bot Issues

Check active bots:
```
Use get_active_bots_status()
```

Check bot logs:
```
Use get_bot_logs(bot_name="<bot_name>", log_type="error", limit=20)
```

Check controller configs:
```
Use explore_controllers(action="describe", config_name="<config_name>")
```

### For Gateway/DEX Issues

Check Gateway status:
```
Use manage_gateway_container(action="get_status")
```

Check Gateway logs:
```
Use manage_gateway_container(action="get_logs", tail=50)
```

Check wallets:
```
Use manage_gateway_config(resource_type="wallets", action="list")
```

---

## Common Issues and Solutions

### Issue: "Connection refused" or "Cannot connect to API"

**Cause**: API server not running or wrong URL

**Solutions**:
1. Check if containers are running: `docker ps | grep hummingbot`
2. Start services: `cd ~/hummingbot-api && make deploy`
3. Verify URL in MCP config: `configure_api_servers()`
4. If running MCP in Docker on Mac/Windows, use `host.docker.internal` instead of `localhost`

### Issue: "Authentication failed"

**Cause**: Wrong username/password

**Solutions**:
1. Check credentials in `~/hummingbot-api/.env`
2. Update MCP config: `configure_api_servers(action="modify", name="...", username="...", password="...")`
3. Reset to defaults: USERNAME=admin, PASSWORD=admin

### Issue: "Invalid API key" from exchange

**Cause**: API keys incorrect or expired

**Solutions**:
1. Verify keys on exchange website
2. Check permissions are correct (trading enabled)
3. Re-add with: `setup_connector(connector="...", credentials={...}, confirm_override=True)`
4. Check if IP whitelisting is blocking

### Issue: Bot not placing orders

**Cause**: Various - check logs

**Solutions**:
1. Check bot logs: `get_bot_logs(bot_name="...", log_type="error")`
2. Verify sufficient balance: `get_portfolio_overview()`
3. Check trading pair exists on exchange
4. Verify controller isn't stopped: check `manual_kill_switch` in config

### Issue: "Insufficient balance"

**Cause**: Not enough funds or funds in wrong account

**Solutions**:
1. Check balances: `get_portfolio_overview()`
2. Verify correct account is being used
3. Ensure bot config uses available balance
4. For perpetuals, check margin requirements

### Issue: Gateway not starting

**Cause**: Docker issues or port conflicts

**Solutions**:
1. Check Docker: `docker ps`
2. Check port 15888: `lsof -i :15888`
3. Check logs: `manage_gateway_container(action="get_logs")`
4. Restart: `manage_gateway_container(action="restart")`

### Issue: DEX transaction failed

**Cause**: Slippage, insufficient gas, or RPC issues

**Solutions**:
1. Increase slippage: set `slippage_pct="2.0"` or higher
2. Check native token balance for gas (SOL, ETH)
3. Check Gateway logs for specific error
4. Try again - blockchain RPCs can be unreliable

### Issue: Slow performance or timeouts

**Cause**: Resource constraints or network issues

**Solutions**:
1. Check Docker resources: `docker stats`
2. Restart services: `cd ~/hummingbot-api && make stop && make deploy`
3. Check exchange API status (some exchanges have maintenance)
4. Increase timeouts if needed

---

## Full Reset Procedure

If nothing else works, perform a full reset:

```bash
cd ~/hummingbot-api

# Stop everything
make stop

# Remove all data (WARNING: loses all configs and history)
docker compose down -v

# Fresh start
make setup
make deploy
```

Then reconfigure:
1. Add exchange credentials with `setup_connector`
2. Recreate configs with `modify_controllers`
3. Deploy bots with `deploy_bot_with_controllers`

---

What issue are you experiencing? Describe the problem and any error messages you see.
"""

    @mcp.prompt()
    def reset_all() -> str:
        """Guide through completely resetting the Hummingbot API installation."""
        return """# Complete Reset Guide

You are helping the user perform a complete reset of their Hummingbot API installation. This will remove all data and start fresh.

## WARNING

This will **DELETE ALL DATA** including:
- Exchange API credentials
- Bot configurations
- Trading history
- Controller configs

Only proceed if:
- Other troubleshooting has failed
- You want a completely fresh start
- You have backed up any important configurations

## Step 1: Stop All Services

```bash
cd ~/hummingbot-api
make stop
```

Verify everything is stopped:
```bash
docker ps | grep hummingbot
```

## Step 2: Remove All Data

Remove containers and volumes:
```bash
cd ~/hummingbot-api
docker compose down -v
```

This removes:
- All containers
- Database data
- EMQX data
- Any persistent volumes

## Step 3: Optional - Remove Repository

If you want a completely clean start:

```bash
cd ~
rm -rf hummingbot-api
```

Then re-clone:
```bash
git clone https://github.com/hummingbot/hummingbot-api.git
cd hummingbot-api
```

## Step 4: Fresh Setup

Run setup with new configuration:

```bash
cd ~/hummingbot-api
make setup
```

Enter your desired:
- USERNAME (or accept default: admin)
- PASSWORD (or accept default: admin)
- CONFIG_PASSWORD (encrypts credentials)

## Step 5: Deploy Services

Start all services:

```bash
make deploy
```

Wait for services to initialize (about 30 seconds).

## Step 6: Verify Installation

Check services are running:
```bash
docker ps | grep hummingbot
```

Test API:
```bash
curl http://localhost:8000/health
```

## Step 7: Reconfigure

Now you need to set up everything again:

### Add Exchange Credentials

```
Use setup_connector(connector="binance", credentials={...})
```

### Create Bot Configurations

```
Use modify_controllers(action="upsert", target="config", ...)
```

### Deploy Bots

```
Use deploy_bot_with_controllers(...)
```

## Step 8: Verify MCP Connection

Check MCP is connected:
```
Use configure_api_servers()
```

Test a simple operation:
```
Use get_portfolio_overview()
```

---

Your Hummingbot API should now be completely reset and ready for fresh configuration.

Would you like help reconfiguring your exchanges and bots?
"""

    @mcp.prompt()
    def check_logs() -> str:
        """Guide through checking various logs for debugging."""
        return """# Log Analysis Guide

You are helping the user check and analyze logs to debug issues.

## Types of Logs

### 1. Hummingbot API Logs

View API server logs:
```bash
docker compose -f ~/hummingbot-api/docker-compose.yml logs --tail=100 hummingbot-api
```

Follow logs in real-time:
```bash
docker compose -f ~/hummingbot-api/docker-compose.yml logs -f hummingbot-api
```

### 2. Database Logs

View PostgreSQL logs:
```bash
docker compose -f ~/hummingbot-api/docker-compose.yml logs --tail=50 postgres
```

### 3. EMQX (MQTT) Logs

View message broker logs:
```bash
docker compose -f ~/hummingbot-api/docker-compose.yml logs --tail=50 emqx
```

### 4. Bot Logs (via MCP)

Get all logs for a bot:
```
Use get_bot_logs(bot_name="<bot_name>", log_type="all", limit=50)
```

Get only error logs:
```
Use get_bot_logs(bot_name="<bot_name>", log_type="error", limit=20)
```

Search logs for specific term:
```
Use get_bot_logs(bot_name="<bot_name>", search_term="error", limit=50)
```

### 5. Gateway Logs

Get Gateway container logs:
```
Use manage_gateway_container(action="get_logs", tail=100)
```

## Common Log Patterns

### Error Patterns to Look For

**Connection errors:**
- "Connection refused"
- "timeout"
- "ECONNREFUSED"

**Authentication errors:**
- "401 Unauthorized"
- "Invalid API key"
- "Authentication failed"

**Trading errors:**
- "Insufficient balance"
- "Order rejected"
- "Invalid trading pair"

**Gateway errors:**
- "RPC error"
- "Transaction failed"
- "Slippage exceeded"

## Log Analysis Workflow

1. **Identify timeframe**: When did the issue occur?

2. **Check API logs first**: Most issues show here
   ```bash
   docker compose -f ~/hummingbot-api/docker-compose.yml logs --since="1h" hummingbot-api
   ```

3. **Check specific bot logs**: If bot-related
   ```
   Use get_bot_logs(bot_name="...", log_type="error")
   ```

4. **Check Gateway logs**: If DEX-related
   ```
   Use manage_gateway_container(action="get_logs")
   ```

5. **Look for patterns**: Repeated errors, specific times, specific operations

## Sharing Logs for Help

If you need to share logs:

1. **Redact sensitive info**: Remove API keys, addresses, passwords
2. **Include context**: What were you trying to do?
3. **Include timestamps**: When did it happen?
4. **Include full error**: Don't truncate error messages

---

What logs would you like to check? Describe what you're trying to debug.
"""
