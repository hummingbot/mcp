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

3. **Pull the Docker image**:
   ```bash
   docker pull hummingbot/hummingbot-mcp:latest
   ```

4. **Configure in Claude Code or Gemini CLI**:
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
           "hummingbot/hummingbot-mcp:latest"
         ]
       }
     }
   }
   ```
   
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

## Environment Variables

The following environment variables can be set in your `.env` file for the MCP server:

| Variable | Default | Description |
|----------|---------|-------------|
| `HUMMINGBOT_API_URL` | `http://localhost:8000` | URL of the Hummingbot API server |
| `HUMMINGBOT_USERNAME` | `admin` | Username for API authentication |
| `HUMMINGBOT_PASSWORD` | `admin` | Password for API authentication |
| `HUMMINGBOT_TIMEOUT` | `30.0` | Connection timeout in seconds |
| `HUMMINGBOT_MAX_RETRIES` | `3` | Maximum number of retry attempts |
| `HUMMINGBOT_RETRY_DELAY` | `2.0` | Delay between retries in seconds |
| `HUMMINGBOT_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

**Note**: Hummingbot API server environment variables are configured directly in the `docker-compose.yml` file.

## Requirements

- Python 3.11+
- Running Hummingbot API server
- Valid Hummingbot API credentials

## Available Tools

The MCP server provides tools for:
- Account management
- Portfolio balances
- Order placement
- Position management
- Market data (prices, order books, candles)
- Funding rates

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

1. **Connection Issues**: Ensure the Hummingbot API server is running and accessible at the URL specified in your `.env` file.

2. **Authentication Errors**: Verify your username and password in the `.env` file match your Hummingbot API credentials.

3. **Docker Issues**: Make sure the `.env` file is in the same directory as your `docker-compose.yml` or specify the correct path in the Docker run command.
