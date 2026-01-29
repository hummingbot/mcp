---
name: hummingbot-setup
description: Deploy and configure Hummingbot infrastructure including Condor, API server, Gateway, and all required services
version: 1.0.0
author: Hummingbot Foundation
triggers:
  - deploy hummingbot
  - setup hummingbot
  - install hummingbot
  - start api server
  - configure gateway
  - install condor
---

# Hummingbot Setup Skill

This skill handles the complete deployment and configuration of Hummingbot infrastructure. It provides step-by-step guidance through the installation process, based on the official [hummingbot/deploy](https://github.com/hummingbot/deploy) setup script.

## Installation Overview

The Hummingbot stack consists of:

| Component | Description |
|-----------|-------------|
| **Condor** | Telegram bot interface for trading |
| **Hummingbot API** | REST API server for bot management |
| **PostgreSQL** | Database for configurations and history |
| **EMQX** | MQTT broker for real-time communication |
| **Gateway** | (Optional) DEX trading on Solana, Ethereum |

## Progressive Installation Steps

Use these scripts to guide users through installation one step at a time:

### Step 1: Check System Requirements

```bash
./scripts/step1_detect_system.sh
```

Detects:
- Operating system (Linux, macOS)
- Architecture (amd64, arm64)
- Available disk space (needs 2GB+)

### Step 2: Check Dependencies

```bash
./scripts/step2_check_dependencies.sh
```

Checks for:
- git
- curl
- docker
- docker-compose (plugin or standalone)
- make

### Step 3: Install Missing Dependencies

```bash
./scripts/step3_install_dependency.sh --dep docker
./scripts/step3_install_dependency.sh --dep docker-compose
./scripts/step3_install_dependency.sh --dep git
./scripts/step3_install_dependency.sh --dep make
```

Installs individual dependencies based on detected package manager.

### Step 4: Check Docker Status

```bash
./scripts/step4_check_docker.sh
```

Verifies:
- Docker daemon is running
- Docker Compose is available
- User has permissions

### Step 5: Clone Repositories

```bash
# Clone Condor (Telegram bot)
./scripts/step5_clone_repo.sh --repo condor

# Clone Hummingbot API
./scripts/step5_clone_repo.sh --repo api
```

### Step 6: Setup Components

```bash
# Setup Condor environment
./scripts/step6_setup_component.sh --component condor

# Setup Hummingbot API
./scripts/step6_setup_component.sh --component api
```

### Step 7: Deploy Services

```bash
# Deploy Condor
./scripts/step7_deploy_component.sh --component condor

# Deploy Hummingbot API
./scripts/step7_deploy_component.sh --component api
```

### Step 8: Verify Installation

```bash
./scripts/step8_verify_installation.sh
```

Checks all services are running and healthy.

## Quick Installation

For users who want to run everything at once:

```bash
# Full installation (Condor + API)
./scripts/deploy_full_stack.sh

# API only installation
./scripts/deploy_full_stack.sh --api-only

# Upgrade existing installation
./scripts/deploy_full_stack.sh --upgrade
```

## Workflow for Agent-Guided Installation

When helping a user install Hummingbot, follow this workflow:

### 1. Initial Assessment

```bash
./scripts/step1_detect_system.sh
```

Tell the user:
- Their detected OS and architecture
- Whether they have enough disk space
- What will be installed

### 2. Dependency Check

```bash
./scripts/step2_check_dependencies.sh
```

If dependencies are missing:
- List what's missing
- Explain each dependency's purpose
- Offer to install them

### 3. Install Each Missing Dependency

For each missing dependency:
```bash
./scripts/step3_install_dependency.sh --dep <name>
```

Explain:
- What's being installed
- Any permissions needed (sudo)
- Progress and completion

### 4. Verify Docker

```bash
./scripts/step4_check_docker.sh
```

If Docker isn't running:
- Explain how to start it
- On macOS: "Open Docker Desktop"
- On Linux: `sudo systemctl start docker`

### 5. Choose Components

Ask the user:
- "Do you want Condor (Telegram bot interface)?" → Most users: Yes
- "Do you want Hummingbot API?" → Required for trading bots

### 6. Clone and Setup

For each chosen component:
```bash
./scripts/step5_clone_repo.sh --repo <component>
./scripts/step6_setup_component.sh --component <component>
```

Explain:
- What's being downloaded
- Configuration being created
- Any prompts they need to answer

### 7. Deploy

```bash
./scripts/step7_deploy_component.sh --component <component>
```

This may take a few minutes as Docker images are pulled.

### 8. Verify and Provide Next Steps

```bash
./scripts/step8_verify_installation.sh
```

Tell the user:
- Services running and their URLs
- How to access Condor via Telegram
- How to view logs
- How to upgrade in the future

## Component Details

### Condor (Telegram Bot)

Repository: https://github.com/hummingbot/condor.git

After installation:
1. Open Telegram
2. Search for your bot (configured during setup)
3. Use `/config` to add API servers
4. Use `/start` to begin trading

### Hummingbot API

Repository: https://github.com/hummingbot/hummingbot-api.git

After installation:
- API URL: http://localhost:8000
- Docs: http://localhost:8000/docs
- Default credentials: admin/admin

### Gateway (Optional)

For DEX trading, Gateway provides blockchain connectivity:

```bash
./scripts/deploy_gateway.sh --chain solana --network mainnet-beta
```

Supported chains:
- Solana (Jupiter, Raydium, Meteora)
- Ethereum (Uniswap, 0x)
- Various L2s (Arbitrum, Base, Optimism)

## Troubleshooting

### Docker Issues

**Docker not running (macOS):**
```bash
open -a Docker
# Wait for Docker Desktop to start
```

**Docker not running (Linux):**
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

**Permission denied:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Installation Failures

**Clone failed:**
- Check internet connection
- Try: `git clone --depth 1 <repo>`

**Make setup failed:**
- Check for error messages
- Ensure all dependencies installed
- Try running manually: `cd <dir> && make setup`

**Deploy failed:**
- Check Docker is running
- Check disk space
- View logs: `docker compose logs`

### Port Conflicts

| Port | Service | Solution |
|------|---------|----------|
| 8000 | API | `lsof -i :8000` then stop conflicting process |
| 5432 | PostgreSQL | Stop local PostgreSQL |
| 1883 | EMQX | Stop local MQTT broker |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INSTALL_DIR` | `$HOME` | Installation directory |
| `API_REPO` | github.com/hummingbot/hummingbot-api | API repository URL |
| `CONDOR_REPO` | github.com/hummingbot/condor | Condor repository URL |

## Reference

The original setup script is available at:
- `references/original_setup.sh`
- Source: https://github.com/hummingbot/deploy/blob/main/setup.sh

This skill breaks down that monolithic script into modular steps for better agent guidance.
