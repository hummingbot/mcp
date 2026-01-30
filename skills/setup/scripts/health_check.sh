#!/bin/bash
# Health check for all Hummingbot services
# Usage: ./health_check.sh [--api-url URL] [--api-user USERNAME] [--api-pass PASSWORD]

API_URL="${API_URL:-http://localhost:8000}"
API_USER="${API_USER:-admin}"
API_PASS="${API_PASS:-admin}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --api-user)
            API_USER="$2"
            shift 2
            ;;
        --api-pass)
            API_PASS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

check_api_health() {
    local response
    local http_code

    response=$(curl -s -w "\n%{http_code}" -u "$API_USER:$API_PASS" "$API_URL/health" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "200" ]; then
        echo "healthy"
    else
        echo "unhealthy"
    fi
}

check_docker_container() {
    local container_name=$1
    local status

    status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "not_found")

    if [ "$status" = "healthy" ]; then
        echo "healthy"
    elif [ "$status" = "not_found" ]; then
        # Check if container exists but doesn't have health check
        if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            echo "running"
        else
            echo "not_running"
        fi
    else
        echo "$status"
    fi
}

# Check services
API_STATUS=$(check_api_health)
POSTGRES_STATUS=$(check_docker_container "hummingbot-postgres")
EMQX_STATUS=$(check_docker_container "hummingbot-emqx")
GATEWAY_STATUS=$(check_docker_container "hummingbot-gateway")

# Determine overall health
if [ "$API_STATUS" = "healthy" ]; then
    OVERALL="healthy"
elif [ "$API_STATUS" = "unhealthy" ] && [ "$POSTGRES_STATUS" != "not_running" ]; then
    OVERALL="degraded"
else
    OVERALL="unhealthy"
fi

# Output JSON
cat << EOF
{
    "overall": "$OVERALL",
    "services": {
        "api_server": {
            "status": "$API_STATUS",
            "url": "$API_URL"
        },
        "postgresql": {
            "status": "$POSTGRES_STATUS"
        },
        "emqx": {
            "status": "$EMQX_STATUS"
        },
        "gateway": {
            "status": "$GATEWAY_STATUS"
        }
    },
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
