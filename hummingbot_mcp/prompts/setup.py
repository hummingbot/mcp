"""
Setup prompt - Guide users through installing and running Hummingbot API.
"""


def register_setup_prompts(mcp):
    """Register setup-related prompts."""

    @mcp.prompt()
    def setup() -> str:
        """Guide the user through installing and running Hummingbot API from scratch.

        This prompt helps users:
        1. Check prerequisites (Docker, Git)
        2. Clone the hummingbot-api repository
        3. Run make setup to configure environment
        4. Run make deploy to start all services
        5. Verify the API is accessible at localhost:8000
        """
        return """# Hummingbot API Setup Guide

You are helping the user install and run Hummingbot API. Follow these steps carefully:

## Step 1: Check Prerequisites

First, verify the user has the required tools installed:

```bash
# Check Docker
docker --version

# Check Docker Compose
docker compose version

# Check Git
git --version
```

If any are missing, guide the user to install them:
- Docker: https://docs.docker.com/get-docker/
- Git: https://git-scm.com/downloads

## Step 2: Clone the Repository

Check if the repository already exists:

```bash
ls -la ~/hummingbot-api
```

If it doesn't exist, clone it:

```bash
cd ~
git clone https://github.com/hummingbot/hummingbot-api.git
cd hummingbot-api
```

If it exists, pull the latest changes:

```bash
cd ~/hummingbot-api
git pull origin main
```

## Step 3: Run Setup

Run the setup command to create the .env file:

```bash
cd ~/hummingbot-api
make setup
```

This will prompt for:
- USERNAME (default: admin)
- PASSWORD (default: admin)
- CONFIG_PASSWORD (encrypts bot credentials)

Use defaults for testing, or set secure passwords for production.

## Step 4: Deploy Services

Start all services with Docker:

```bash
cd ~/hummingbot-api
make deploy
```

This starts:
- Hummingbot API (port 8000)
- PostgreSQL database (port 5432)
- EMQX MQTT broker (port 1883)

## Step 5: Verify Installation

Check that all services are running:

```bash
docker ps | grep hummingbot
```

Test the API endpoint:

```bash
curl -s http://localhost:8000/health | head -20
```

Open the Swagger docs in a browser:
- URL: http://localhost:8000/docs

## Step 6: Configure MCP Connection

Now configure the MCP server to connect to the API. If you're running the MCP server locally (not in Docker), use:

```
HUMMINGBOT_API_URL=http://localhost:8000
```

If running MCP in Docker on Mac/Windows:

```
HUMMINGBOT_API_URL=http://host.docker.internal:8000
```

Use the `configure_api_servers` tool to verify or update the connection:
- Call `configure_api_servers()` with no arguments to see current configuration
- Call `configure_api_servers(action="add", name="local", host="localhost", port=8000)` to add a server

## Troubleshooting

If services fail to start:

```bash
# Check logs
docker compose logs hummingbot-api

# Reset everything and try again
docker compose down -v
make deploy
```

---

After completing these steps, the user should have:
- Hummingbot API running at http://localhost:8000
- Swagger docs accessible at http://localhost:8000/docs
- MCP server connected and ready to use

Next steps: Use `setup_connector` to add exchange credentials, or `/grid_executor` or `/position_executor` to create a trading bot.
"""

    @mcp.prompt()
    def check_status() -> str:
        """Check the status of Hummingbot API services and connectivity."""
        return """# Check Hummingbot API Status

You are helping the user verify their Hummingbot API installation is working correctly.

## Step 1: Check Docker Containers

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "hummingbot|postgres|emqx"
```

Expected containers:
- hummingbot-api (port 8000)
- postgres (port 5432)
- emqx (port 1883, 18083)

## Step 2: Test API Health

```bash
curl -s http://localhost:8000/health
```

Should return a JSON response with status information.

## Step 3: Test API Authentication

```bash
curl -s -X POST http://localhost:8000/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

Should return an access token if credentials are correct.

## Step 4: Check MCP Connection

Use the `configure_api_servers()` tool to verify the MCP server configuration:
- Shows all configured API servers
- Indicates which one is the default
- Shows connection status

## Step 5: Test MCP Tools

Try a simple MCP tool to verify end-to-end connectivity:

Use `setup_connector()` with no arguments - this should list available exchanges.

## Common Issues

1. **Container not running**: Run `cd ~/hummingbot-api && make deploy`
2. **Port already in use**: Check what's using port 8000: `lsof -i :8000`
3. **Database connection failed**: Reset with `docker compose down -v && make deploy`
4. **MCP can't connect**: Check HUMMINGBOT_API_URL in your .env file

Report the results of each check so we can diagnose any issues.
"""
