# MCP Hummingbot Server

An MCP (Model Context Protocol) server that enables Claude to interact with Hummingbot for automated cryptocurrency trading across multiple exchanges.

## Installation & Configuration

### Option 1: Using uv (Recommended for Development)

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and install dependencies**:
   ```bash
   git clone <repository-url>
   cd mcp
   uv sync
   ```

3. **Set environment variables**:
   ```bash
   export HUMMINGBOT_API_URL="http://localhost:15888"
   export HUMMINGBOT_USERNAME="your-username"
   export HUMMINGBOT_PASSWORD="your-password"
   export DEFAULT_ACCOUNT="master_account"
   ```

4. **Configure in Claude Code**:
   ```json
   {
     "mcpServers": {
       "mcp-hummingbot": {
         "type": "stdio",
         "command": "uv",
         "args": [
           "--directory",
           "/path/to/mcp",
           "run",
           "main.py"
         ],
         "env": {
           "HUMMINGBOT_API_URL": "http://localhost:15888",
           "HUMMINGBOT_USERNAME": "your-username",
           "HUMMINGBOT_PASSWORD": "your-password"
         }
       }
     }
   }
   ```

### Option 2: Using Python Directly

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure in Claude Code**:
   ```json
   {
     "mcpServers": {
       "mcp-hummingbot": {
         "type": "stdio",
         "command": "python",
         "args": ["/path/to/mcp/main.py"],
         "env": {
           "HUMMINGBOT_API_URL": "http://localhost:15888",
           "HUMMINGBOT_USERNAME": "your-username",
           "HUMMINGBOT_PASSWORD": "your-password"
         }
       }
     }
   }
   ```

### Option 3: Using Docker (Recommended for Production)

1. **Build the Docker image**:
   ```bash
   docker build -t mcp-hummingbot .
   ```

2. **Configure in Claude Code**:
   ```json
   {
     "mcpServers": {
       "hummingbot": {
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "-i",
           "--network", "host",
           "-e", "HUMMINGBOT_API_URL=http://localhost:15888",
           "-e", "HUMMINGBOT_USERNAME=your-username",
           "-e", "HUMMINGBOT_PASSWORD=your-password",
           "mcp-hummingbot"
         ]
       }
     }
   }
   ```

### Cloud Deployment with Docker

For cloud deployment where both Hummingbot API and MCP server run on the same server:

1. **Create a docker-compose.yml**:
   ```yaml
   version: '3.8'
   services:
     hummingbot-api:
       image: hummingbot/backend-api:latest
       ports:
         - "15888:15888"
       environment:
         - CONFIG_FOLDER_PATH=/config
       volumes:
         - ./hummingbot_files:/app
   
     mcp-server:
       build: .
       stdin_open: true
       tty: true
       environment:
         - HUMMINGBOT_API_URL=http://hummingbot-api:15888
         - HUMMINGBOT_USERNAME=${HUMMINGBOT_USERNAME}
         - HUMMINGBOT_PASSWORD=${HUMMINGBOT_PASSWORD}
       depends_on:
         - hummingbot-api
   ```

2. **Deploy**:
   ```bash
   docker-compose up -d
   ```

3. **Configure Claude Code to connect remotely** (requires MCP to support remote connections - currently stdio only).

## Requirements

- Python 3.11+
- Running Hummingbot instance with API enabled
- Valid Hummingbot API credentials

## Available Tools

The MCP server provides tools for:
- Account management
- Portfolio balances
- Order placement
- Position management
- Market data (prices, order books, candles)
- Funding rates