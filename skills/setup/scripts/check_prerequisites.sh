#!/bin/bash
# Check prerequisites for Hummingbot deployment
# Returns JSON with status of each requirement

set -e

check_docker() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

check_docker_compose() {
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

check_git() {
    if command -v git &> /dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

check_port() {
    local port=$1
    if ! lsof -i :$port &> /dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

check_disk_space() {
    # Check for at least 5GB free space
    local free_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$free_space" -ge 5 ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Run checks
DOCKER_OK=$(check_docker)
COMPOSE_OK=$(check_docker_compose)
GIT_OK=$(check_git)
PORT_8000_OK=$(check_port 8000)
PORT_15672_OK=$(check_port 15672)
PORT_5432_OK=$(check_port 5432)
DISK_OK=$(check_disk_space)

# Determine overall status
if [ "$DOCKER_OK" = "true" ] && [ "$COMPOSE_OK" = "true" ] && [ "$GIT_OK" = "true" ] && \
   [ "$PORT_8000_OK" = "true" ] && [ "$PORT_15672_OK" = "true" ] && [ "$PORT_5432_OK" = "true" ] && \
   [ "$DISK_OK" = "true" ]; then
    READY="true"
else
    READY="false"
fi

# Output JSON
cat << EOF
{
    "ready": $READY,
    "checks": {
        "docker": $DOCKER_OK,
        "docker_compose": $COMPOSE_OK,
        "git": $GIT_OK,
        "port_8000_available": $PORT_8000_OK,
        "port_15672_available": $PORT_15672_OK,
        "port_5432_available": $PORT_5432_OK,
        "disk_space_5gb": $DISK_OK
    },
    "messages": [
        $([ "$DOCKER_OK" = "false" ] && echo '"Docker is not installed or not running",' || echo '')
        $([ "$COMPOSE_OK" = "false" ] && echo '"Docker Compose is not available",' || echo '')
        $([ "$GIT_OK" = "false" ] && echo '"Git is not installed",' || echo '')
        $([ "$PORT_8000_OK" = "false" ] && echo '"Port 8000 is already in use",' || echo '')
        $([ "$PORT_15672_OK" = "false" ] && echo '"Port 15672 is already in use",' || echo '')
        $([ "$PORT_5432_OK" = "false" ] && echo '"Port 5432 is already in use",' || echo '')
        $([ "$DISK_OK" = "false" ] && echo '"Less than 5GB disk space available",' || echo '')
        $([ "$READY" = "true" ] && echo '"All prerequisites met, ready to deploy"' || echo '"Some prerequisites not met"')
    ]
}
EOF
