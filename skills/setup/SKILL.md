---
name: hummingbot-setup
description: Deploy and configure Hummingbot infrastructure including API server, Gateway, and all required services
version: 1.0.0
author: Hummingbot Foundation
triggers:
  - deploy hummingbot
  - setup hummingbot
  - install hummingbot
  - start api server
  - configure gateway
---

# Hummingbot Setup Skill

This skill handles the complete deployment and configuration of Hummingbot infrastructure. It manages Docker containers, API server setup, Gateway configuration, and health verification.

## Prerequisites

Before using this skill, ensure:
- Docker Desktop is installed and running
- Git is available (for cloning repositories)
- Ports 8000 (API), 15672 (EMQX), 5432 (PostgreSQL) are available

## Capabilities

### 1. Full Stack Deployment

Deploy the complete Hummingbot stack with a single command:

```bash
./scripts/deploy_full_stack.sh
```

This deploys:
- **hummingbot-api**: REST API server for bot management
- **PostgreSQL**: Database for storing configurations and history
- **EMQX**: MQTT broker for real-time communication
- **Gateway** (optional): For DEX trading on Solana, Ethereum, etc.

### 2. Individual Component Management

For granular control, deploy components individually:

```bash
# Check prerequisites
./scripts/check_prerequisites.sh

# Deploy just the API server
./scripts/deploy_api_server.sh

# Deploy Gateway for DEX trading
./scripts/deploy_gateway.sh --chain solana --network mainnet-beta

# Verify all services are healthy
./scripts/health_check.sh
```

### 3. Configuration Management

```bash
# Set API server credentials
./scripts/configure_api.sh --username admin --password <secure_password>

# Configure Telegram bot integration
./scripts/configure_telegram.sh --token <bot_token> --chat_id <chat_id>
```

## API Endpoints

Once deployed, the Hummingbot API is available at:

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000` | API server base URL |
| `http://localhost:8000/docs` | OpenAPI documentation |
| `http://localhost:8000/health` | Health check endpoint |

### Authentication

All API requests require Basic Auth:
```bash
curl -u admin:password http://localhost:8000/api/v1/accounts
```

## Deployment Workflow

When asked to deploy Hummingbot, follow this sequence:

1. **Check Prerequisites**
   - Verify Docker is running
   - Check port availability
   - Ensure sufficient disk space

2. **Clone Repository** (if not present)
   ```bash
   git clone https://github.com/hummingbot/hummingbot-api.git
   cd hummingbot-api
   ```

3. **Configure Environment**
   - Set API credentials in `.env`
   - Configure database connection
   - Set up MQTT broker settings

4. **Deploy Services**
   ```bash
   docker compose up -d
   ```

5. **Verify Deployment**
   - Check all containers are running
   - Test API health endpoint
   - Verify database connectivity

6. **Report Status**
   - Provide API URL and credentials
   - List running containers
   - Show any warnings or errors

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find and stop process using port 8000
lsof -i :8000
kill -9 <PID>
```

**Docker not running:**
```bash
# Start Docker Desktop or daemon
open -a Docker  # macOS
sudo systemctl start docker  # Linux
```

**Database connection failed:**
```bash
# Check PostgreSQL container logs
docker logs hummingbot-postgres
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_USERNAME` | admin | API authentication username |
| `API_PASSWORD` | admin | API authentication password |
| `DATABASE_URL` | postgresql://... | PostgreSQL connection string |
| `EMQX_HOST` | localhost | MQTT broker host |
| `GATEWAY_PASSPHRASE` | - | Passphrase for Gateway wallet encryption |

## Scripts Reference

| Script | Description |
|--------|-------------|
| `deploy_full_stack.sh` | Deploy complete Hummingbot stack |
| `deploy_api_server.sh` | Deploy only API server and dependencies |
| `deploy_gateway.sh` | Deploy Gateway for DEX trading |
| `check_prerequisites.sh` | Verify system requirements |
| `health_check.sh` | Check health of all services |
| `configure_api.sh` | Configure API server settings |
| `stop_all.sh` | Stop all Hummingbot containers |
| `cleanup.sh` | Remove all containers and volumes |
