#!/bin/bash
# Step 2: Check for required dependencies
# Returns JSON with dependency status

set -e

check_command() {
    if command -v "$1" &> /dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

# Check each dependency
GIT_OK=$(check_command git)
CURL_OK=$(check_command curl)
DOCKER_OK=$(check_command docker)
MAKE_OK=$(check_command make)

# Check docker-compose (either plugin or standalone)
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_OK="true"
    DOCKER_COMPOSE_TYPE="plugin"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_OK="true"
    DOCKER_COMPOSE_TYPE="standalone"
else
    DOCKER_COMPOSE_OK="false"
    DOCKER_COMPOSE_TYPE="none"
fi

# Build missing list
MISSING=()
[ "$GIT_OK" = "false" ] && MISSING+=("git")
[ "$CURL_OK" = "false" ] && MISSING+=("curl")
[ "$DOCKER_OK" = "false" ] && MISSING+=("docker")
[ "$DOCKER_COMPOSE_OK" = "false" ] && MISSING+=("docker-compose")
[ "$MAKE_OK" = "false" ] && MISSING+=("make")

# Determine overall status
if [ ${#MISSING[@]} -eq 0 ]; then
    ALL_OK="true"
else
    ALL_OK="false"
fi

# Convert missing array to JSON
MISSING_JSON=$(printf '%s\n' "${MISSING[@]}" | jq -R . | jq -s .)

cat << EOF
{
    "all_dependencies_met": $ALL_OK,
    "dependencies": {
        "git": {
            "installed": $GIT_OK,
            "purpose": "Clone repositories"
        },
        "curl": {
            "installed": $CURL_OK,
            "purpose": "Download files and make API calls"
        },
        "docker": {
            "installed": $DOCKER_OK,
            "purpose": "Run containerized services"
        },
        "docker_compose": {
            "installed": $DOCKER_COMPOSE_OK,
            "type": "$DOCKER_COMPOSE_TYPE",
            "purpose": "Orchestrate multi-container deployments"
        },
        "make": {
            "installed": $MAKE_OK,
            "purpose": "Run build and setup commands"
        }
    },
    "missing": $MISSING_JSON,
    "missing_count": ${#MISSING[@]},
    "next_step": $([ "$ALL_OK" = "true" ] && echo '"All dependencies installed. Proceed to step 4 (check Docker status)."' || echo '"Install missing dependencies using step3_install_dependency.sh"')
}
EOF
