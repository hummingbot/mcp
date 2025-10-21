# MCP Hummingbot Server

An MCP (Model Context Protocol) server that enables Claude and Gemini CLI to interact with Hummingbot for automated cryptocurrency trading across multiple exchanges.

## Installation & Configuration

### Option 1: Using uv (Recommended for Development)

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and install dependencies**:
   ```bash
   git clone https://github.com/hummingbot/mcp
   cd mcp
   uv sync
   ```

3. **Create a .env file**:
   ```bash
   cp .env.example .env
   ```

4. **Edit the .env file** with your Hummingbot API credentials:
   ```env
   HUMMINGBOT_API_URL=http://localhost:8000
   HUMMINGBOT_USERNAME=admin
   HUMMINGBOT_PASSWORD=admin
   ```

5. **Configure in Claude Code or Gemini CLI**:
   ```json
   {
     "mcpServers": {
       "hummingbot-mcp": {
         "type": "stdio",
         "command": "uv",
         "args": [
           "--directory",
           "/path/to/mcp",
           "run",
           "main.py"
         ]
       }
     }
   }
   ```
   
   **Note**: Make sure to replace `/path/to/mcp` with the actual path to your MCP directory.

### Option 2: Using Docker (Recommended for Production)

1. **Create a .env file**:
   ```bash
   touch .env
   ```

2. **Edit the .env file** with your Hummingbot API credentials:
   ```env
   HUMMINGBOT_API_URL=http://localhost:8000
   HUMMINGBOT_USERNAME=admin
   HUMMINGBOT_PASSWORD=admin
   ```

   **Important**: When running the MCP server in Docker and connecting to a Hummingbot API on your host:
   - **Linux**: Use `--network host` (see below) to allow the container to access `localhost:8000`
   - **Mac/Windows**: Change `HUMMINGBOT_API_URL` to `http://host.docker.internal:8000`

3. **Pull the Docker image**:
   ```bash
   docker pull hummingbot/hummingbot-mcp:latest
   ```

4. **Configure in Claude Code or Gemini CLI**:

   **For Linux (using --network host)**:
   ```json
   {
     "mcpServers": {
       "hummingbot-mcp": {
         "type": "stdio",
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "-i",
           "--network",
           "host",
           "--env-file",
           "/path/to/mcp/.env",
           "-v",
           "$HOME/.hummingbot_mcp:/root/.hummingbot_mcp",
           "hummingbot/hummingbot-mcp:latest"
         ]
       }
     }
   }
   ```

   **For Mac/Windows**:
   ```json
   {
     "mcpServers": {
       "hummingbot-mcp": {
         "type": "stdio",
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "-i",
           "--env-file",
           "/path/to/mcp/.env",
           "-v",
           "$HOME/.hummingbot_mcp:/root/.hummingbot_mcp",
           "hummingbot/hummingbot-mcp:latest"
         ]
       }
     }
   }
   ```
   (Remember to set `HUMMINGBOT_API_URL=http://host.docker.internal:8000` in your `.env` file)

   **Note**: Make sure to replace `/path/to/mcp` with the actual path to your MCP directory.

### Cloud Deployment with Docker Compose

For cloud deployment where both Hummingbot API and MCP server run on the same server:

1. **Create a .env file**:
   ```bash
   touch .env
   ```

2. **Edit the .env file** with your Hummingbot API credentials:
   ```env
   HUMMINGBOT_API_URL=http://localhost:8000
   HUMMINGBOT_USERNAME=admin
   HUMMINGBOT_PASSWORD=admin
   ```

3. **Create a docker-compose.yml**:
   ```yaml
   services:
     hummingbot-api:
       container_name: hummingbot-api
       image: hummingbot/hummingbot-api:latest
       ports:
         - "8000:8000"
       volumes:
         - ./bots:/hummingbot-api/bots
         - /var/run/docker.sock:/var/run/docker.sock
       environment:
         - USERNAME=admin
         - PASSWORD=admin
         - BROKER_HOST=emqx
         - DATABASE_URL=postgresql+asyncpg://hbot:hummingbot-api@postgres:5432/hummingbot_api
       networks:
         - emqx-bridge
       depends_on:
         - postgres
   
     mcp-server:
       container_name: hummingbot-mcp
       image: hummingbot/hummingbot-mcp:latest
       stdin_open: true
       tty: true
       env_file:
         - .env
       environment:
         - HUMMINGBOT_API_URL=http://hummingbot-api:8000
       depends_on:
         - hummingbot-api
       networks:
         - emqx-bridge
   
     # Include other services from hummingbot-api docker-compose.yml as needed
     emqx:
       container_name: hummingbot-broker
       image: emqx:5
       restart: unless-stopped
       environment:
         - EMQX_NAME=emqx
         - EMQX_HOST=node1.emqx.local
         - EMQX_CLUSTER__DISCOVERY_STRATEGY=static
         - EMQX_CLUSTER__STATIC__SEEDS=[emqx@node1.emqx.local]
         - EMQX_LOADED_PLUGINS="emqx_recon,emqx_retainer,emqx_management,emqx_dashboard"
       volumes:
         - emqx-data:/opt/emqx/data
         - emqx-log:/opt/emqx/log
         - emqx-etc:/opt/emqx/etc
       ports:
         - "1883:1883"
         - "8883:8883"
         - "8083:8083"
         - "8084:8084"
         - "8081:8081"
         - "18083:18083"
         - "61613:61613"
       networks:
         emqx-bridge:
           aliases:
             - node1.emqx.local
       healthcheck:
         test: [ "CMD", "/opt/emqx/bin/emqx_ctl", "status" ]
         interval: 5s
         timeout: 25s
         retries: 5
   
     postgres:
       container_name: hummingbot-postgres
       image: postgres:15
       restart: unless-stopped
       environment:
         - POSTGRES_DB=hummingbot_api
         - POSTGRES_USER=hbot
         - POSTGRES_PASSWORD=hummingbot-api
       volumes:
         - postgres-data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
       networks:
         - emqx-bridge
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U hbot -d hummingbot_api"]
         interval: 10s
         timeout: 5s
         retries: 5

   networks:
     emqx-bridge:
       driver: bridge

   volumes:
     emqx-data: { }
     emqx-log: { }
     emqx-etc: { }
     postgres-data: { }
   ```

4. **Deploy**:
   ```bash
   docker compose up -d
   ```

5. **Configure in Claude Code or Gemini CLI to connect to existing container**:
   ```json
   {
     "mcpServers": {
       "hummingbot-mcp": {
         "type": "stdio",
         "command": "docker",
         "args": [
           "exec",
           "-i",
           "hummingbot-mcp",
           "uv",
           "run",
           "main.py"
         ]
       }
     }
   }
   ```
   
   **Note**: Replace `hummingbot-mcp` with your actual container name. You can find the container name by running:
   ```bash
   docker ps
   ```

## Managing Multiple API Servers

The MCP server now supports managing multiple Hummingbot API servers. This is useful when you have multiple deployments or environments.

### Initial Setup

On first run, the server creates a default server from environment variables (or uses `http://localhost:8000` with default credentials). Configuration is stored in `~/.hummingbot_mcp/servers.yml`.

### Using the configure_api_servers Tool

```
# List all configured servers
configure_api_servers()

# Add a new server using full URL
configure_api_servers(
    action="add",
    name="production",
    url="http://prod-server:8000",
    username="admin",
    password="secure_password"
)

# Add a server using just port (defaults to localhost)
configure_api_servers(
    action="add",
    name="local_8001",
    port=8001,
    username="admin",
    password="secure_password"
)

# Add a server using default port 8000
configure_api_servers(
    action="add",
    name="local_default",
    username="admin",
    password="secure_password"
)

# Switch to a different server
configure_api_servers(action="set_default", name="production")

# Remove a server
configure_api_servers(action="remove", name="old_server")
```

All subsequent API calls will use the currently selected default server.

## Environment Variables

The following environment variables can be set in your `.env` file for the MCP server:

| Variable | Default | Description |
|----------|---------|-------------|
| `HUMMINGBOT_API_URL` | `http://localhost:8000` | Initial default API server URL (used only on first run) |
| `HUMMINGBOT_USERNAME` | `admin` | Initial username (used only on first run) |
| `HUMMINGBOT_PASSWORD` | `admin` | Initial password (used only on first run) |
| `HUMMINGBOT_TIMEOUT` | `30.0` | Connection timeout in seconds |
| `HUMMINGBOT_MAX_RETRIES` | `3` | Maximum number of retry attempts |
| `HUMMINGBOT_RETRY_DELAY` | `2.0` | Delay between retries in seconds |
| `HUMMINGBOT_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

**Note**: After initial setup, use the `configure_api_servers` tool to manage servers. Environment variables are only used to create the initial default server.

## Requirements

- Python 3.11+
- Running Hummingbot API server
- Valid Hummingbot API credentials

## Available Tools

The MCP server provides tools for:

### Server Management
- **configure_api_servers**: Manage multiple Hummingbot API server connections
  - List all configured servers
  - Add new servers with credentials
  - Set default server (automatically reconnects client)
  - Remove servers
  - Configuration persists in `~/.hummingbot_mcp/servers.yml`

### Trading & Account Management
- Account management and connector setup
- Portfolio balances and distribution
- Order placement and management
- Position management
- Market data (prices, order books, candles)
- Funding rates
- Bot deployment and management
- Controller configuration

## Development

To run the server in development mode:

```bash
uv run main.py
```

To run tests:

```bash
uv run pytest
```

## Troubleshooting

The MCP server now provides **comprehensive error messages** to help diagnose connection and authentication issues:

### Connection Errors

If you see error messages like:
- `❌ Cannot reach Hummingbot API at <url>` - The API server is not running or not accessible
- `❌ Authentication failed when connecting to Hummingbot API` - Incorrect username or password
- `❌ Failed to connect to Hummingbot API` - Generic connection failure

The error messages will include:
- The exact URL being used
- Your configured username (password is masked)
- Specific suggestions on how to fix the issue
- References to tools like `configure_api_servers`

### Common Solutions

1. **API Not Running**:
   - Ensure your Hummingbot API server is running
   - Verify the API is accessible at the configured URL

2. **Wrong Credentials**:
   - Use `configure_api_servers` tool to update server credentials
   - Or check your `.env` file configuration

3. **Wrong URL**:
   - Use `configure_api_servers` tool to update the server URL
   - For Docker on Mac/Windows, use `host.docker.internal` instead of `localhost`

4. **Docker Network Issues**:
   - On Linux, use `--network host` in your Docker configuration
   - On Mac/Windows, use `host.docker.internal:8000` as the API URL

### Error Prevention

The MCP server will:
- **Not retry** on authentication failures (401 errors) - it will immediately tell you the credentials are wrong
- **Retry** on connection failures with helpful messages about what might be wrong
- **Provide context** about whether you're running in Docker and suggest appropriate fixes
- **Guide you** to the right tools (`configure_api_servers`) to fix issues
