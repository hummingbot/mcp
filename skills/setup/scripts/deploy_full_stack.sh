#!/bin/bash
# Deploy the complete Hummingbot stack
# Usage: ./deploy_full_stack.sh [--with-gateway] [--api-user USERNAME] [--api-pass PASSWORD]

set -e

# Default values
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"
WITH_GATEWAY=false
REPO_DIR="${HUMMINGBOT_API_DIR:-$HOME/hummingbot-api}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-gateway)
            WITH_GATEWAY=true
            shift
            ;;
        --api-user)
            API_USER="$2"
            shift 2
            ;;
        --api-pass)
            API_PASS="$2"
            shift 2
            ;;
        --repo-dir)
            REPO_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Hummingbot Full Stack Deployment ==="

# Step 1: Check prerequisites
echo ""
echo "Step 1: Checking prerequisites..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREREQ_RESULT=$("$SCRIPT_DIR/check_prerequisites.sh")
READY=$(echo "$PREREQ_RESULT" | grep -o '"ready": [^,]*' | cut -d' ' -f2)

if [ "$READY" != "true" ]; then
    echo "Prerequisites not met:"
    echo "$PREREQ_RESULT"
    exit 1
fi
echo "All prerequisites met."

# Step 2: Clone or update repository
echo ""
echo "Step 2: Setting up repository..."
if [ -d "$REPO_DIR" ]; then
    echo "Repository exists at $REPO_DIR, pulling latest..."
    cd "$REPO_DIR"
    git pull origin main || echo "Warning: Could not pull latest changes"
else
    echo "Cloning hummingbot-api repository..."
    git clone https://github.com/hummingbot/hummingbot-api.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Step 3: Configure environment
echo ""
echo "Step 3: Configuring environment..."
if [ -f .env.example ] && [ ! -f .env ]; then
    cp .env.example .env
fi

# Update credentials in .env if it exists
if [ -f .env ]; then
    # Use sed to update or add credentials
    if grep -q "^API_USERNAME=" .env; then
        sed -i.bak "s/^API_USERNAME=.*/API_USERNAME=$API_USER/" .env
    else
        echo "API_USERNAME=$API_USER" >> .env
    fi

    if grep -q "^API_PASSWORD=" .env; then
        sed -i.bak "s/^API_PASSWORD=.*/API_PASSWORD=$API_PASS/" .env
    else
        echo "API_PASSWORD=$API_PASS" >> .env
    fi
    rm -f .env.bak
fi

# Step 4: Pull Docker images
echo ""
echo "Step 4: Pulling Docker images..."
docker compose pull

# Step 5: Start services
echo ""
echo "Step 5: Starting services..."
if [ "$WITH_GATEWAY" = true ]; then
    docker compose --profile gateway up -d
else
    docker compose up -d
fi

# Step 6: Wait for services to be healthy
echo ""
echo "Step 6: Waiting for services to be healthy..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -u "$API_USER:$API_PASS" http://localhost:8000/health > /dev/null 2>&1; then
        echo "API server is healthy!"
        break
    fi
    echo "Waiting for API server... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Warning: API server health check timed out"
fi

# Step 7: Output status
echo ""
echo "=== Deployment Complete ==="
echo ""

# Get container status
CONTAINERS=$(docker compose ps --format json 2>/dev/null || docker compose ps)

cat << EOF
{
    "status": "deployed",
    "api_url": "http://localhost:8000",
    "api_docs": "http://localhost:8000/docs",
    "credentials": {
        "username": "$API_USER",
        "password": "$API_PASS"
    },
    "gateway_enabled": $WITH_GATEWAY,
    "repo_dir": "$REPO_DIR",
    "next_steps": [
        "Add exchange API keys using the keys skill",
        "Create a controller configuration",
        "Deploy your first trading bot"
    ]
}
EOF
