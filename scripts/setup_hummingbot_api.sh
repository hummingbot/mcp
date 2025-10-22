#!/bin/bash

# Backend API Setup Script
# This script creates a comprehensive .env file with all configuration options
# following the Pydantic Settings structure established in config.py

set -e  # Exit on any error

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "🚀 Backend API Setup"
echo ""

echo -n "Config password [default: admin]: "
read CONFIG_PASSWORD
CONFIG_PASSWORD=${CONFIG_PASSWORD:-admin}

echo -n "API username [default: admin]: "
read USERNAME
USERNAME=${USERNAME:-admin}

echo -n "API password [default: admin]: "
read PASSWORD
PASSWORD=${PASSWORD:-admin}

echo ""
echo -e "${YELLOW}Gateway Configuration (Optional)${NC}"
echo -n "Gateway passphrase [default: admin, press Enter to skip]: "
read GATEWAY_PASSPHRASE
GATEWAY_PASSPHRASE=${GATEWAY_PASSPHRASE:-admin}

# Set paths and defaults
BOTS_PATH=$(pwd)/bots

# Use sensible defaults for everything else
DEBUG_MODE="false"
BROKER_HOST="localhost"
BROKER_PORT="1883"
BROKER_USERNAME="admin"
BROKER_PASSWORD="password"
DATABASE_URL="postgresql+asyncpg://hbot:hummingbot-api@localhost:5432/hummingbot_api"
CLEANUP_INTERVAL="300"
FEED_TIMEOUT="600"
AWS_API_KEY=""
AWS_SECRET_KEY=""
S3_BUCKET=""
LOGFIRE_ENV="dev"
BANNED_TOKENS='["NAV","ARS","ETHW","ETHF","NEWT"]'

echo ""
echo -e "${GREEN}✅ Using sensible defaults for MQTT, Database, and other settings${NC}"

echo ""
echo -e "${GREEN}📝 Creating .env file...${NC}"

# Create .env file with proper structure and comments
cat > .env << EOF
# =================================================================
# Backend API Environment Configuration
# Generated on: $(date)
# =================================================================

# =================================================================
# 🔐 Security Configuration
# =================================================================
USERNAME=$USERNAME
PASSWORD=$PASSWORD
DEBUG_MODE=$DEBUG_MODE
CONFIG_PASSWORD=$CONFIG_PASSWORD

# =================================================================
# 🔗 MQTT Broker Configuration (BROKER_*)
# =================================================================
BROKER_HOST=$BROKER_HOST
BROKER_PORT=$BROKER_PORT
BROKER_USERNAME=$BROKER_USERNAME
BROKER_PASSWORD=$BROKER_PASSWORD

# =================================================================
# 💾 Database Configuration (DATABASE_*)
# =================================================================
DATABASE_URL=$DATABASE_URL

# =================================================================
# 📊 Market Data Feed Manager Configuration (MARKET_DATA_*)
# =================================================================
MARKET_DATA_CLEANUP_INTERVAL=$CLEANUP_INTERVAL
MARKET_DATA_FEED_TIMEOUT=$FEED_TIMEOUT

# =================================================================
# ☁️ AWS Configuration (AWS_*) - Optional
# =================================================================
AWS_API_KEY=$AWS_API_KEY
AWS_SECRET_KEY=$AWS_SECRET_KEY
AWS_S3_DEFAULT_BUCKET_NAME=$S3_BUCKET

# =================================================================
# ⚙️ Application Settings
# =================================================================
LOGFIRE_ENVIRONMENT=$LOGFIRE_ENV
BANNED_TOKENS=$BANNED_TOKENS

# =================================================================
# 🌐 Gateway Configuration (GATEWAY_*) - Optional
# =================================================================
GATEWAY_PASSPHRASE=$GATEWAY_PASSPHRASE

# =================================================================
# 📁 Legacy Settings (maintained for backward compatibility)
# =================================================================
BOTS_PATH=$BOTS_PATH

EOF

echo -e "${GREEN}✅ .env file created successfully!${NC}"
echo ""

# Display configuration summary
echo -e "${BLUE}📋 Configuration Summary${NC}"
echo "======================="
echo -e "${CYAN}Security:${NC} Username: $USERNAME, Debug: $DEBUG_MODE"
echo -e "${CYAN}Broker:${NC} $BROKER_HOST:$BROKER_PORT"
echo -e "${CYAN}Database:${NC} ${DATABASE_URL%%@*}@[hidden]"
echo -e "${CYAN}Market Data:${NC} Cleanup: ${CLEANUP_INTERVAL}s, Timeout: ${FEED_TIMEOUT}s"
echo -e "${CYAN}Environment:${NC} $LOGFIRE_ENV"

if [ -n "$AWS_API_KEY" ]; then
    echo -e "${CYAN}AWS:${NC} Configured with S3 bucket: $S3_BUCKET"
else
    echo -e "${CYAN}AWS:${NC} Not configured (optional)"
fi

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""

# Check if password verification file exists
if [ ! -f "bots/credentials/master_account/.password_verification" ]; then
    echo -e "${YELLOW}📌 Note:${NC} Password verification file will be created on first startup"
    echo -e "   Location: ${BLUE}bots/credentials/master_account/.password_verification${NC}"
    echo ""
fi

echo -e "Next steps:"
echo "1. Review the .env file if needed: cat .env"
echo "2. Start services: docker compose up -d"
echo ""
echo -e "${PURPLE}💡 Pro tip:${NC} You can modify environment variables in .env file anytime"
echo -e "${PURPLE}📚 Documentation:${NC} Check config.py for all available settings"
echo -e "${PURPLE}🔒 Security:${NC} The password verification file secures bot credentials"
echo ""
echo -e "${GREEN}🐳 Starting required Docker containers and pulling Hummingbot image...${NC}"

# Create bots directory structure
mkdir -p bots/credentials/master_account
mkdir -p bots/controllers
mkdir -p bots/data

# Run docker operations in parallel
docker compose up emqx postgres -d &
docker pull hummingbot/hummingbot:latest &

# Wait for both operations to complete
wait

echo -e "${GREEN}✅ All Docker operations completed!${NC}"
echo ""
echo -e "${GREEN}🚀 Starting Hummingbot API...${NC}"
docker compose up hummingbot-api -d

echo ""
echo -e "${GREEN}✅ Hummingbot API is now running!${NC}"
echo -e "${BLUE}API URL:${NC} http://localhost:8000"
echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo ""
