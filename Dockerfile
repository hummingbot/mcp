# Stage 1: Dependencies
FROM python:3.12-slim AS deps
WORKDIR /app
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install uv
COPY pyproject.toml uv.lock README.md main.py ./
COPY hummingbot_mcp/ ./hummingbot_mcp/
RUN uv venv && uv pip install .

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    gnupg \
    lsb-release && \
    # Install Docker CLI
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-compose-plugin && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install uv

# Copy the virtual environment from the deps stage
COPY --from=deps /app/.venv /app/.venv

# Copy source code
COPY hummingbot_mcp/ ./hummingbot_mcp/
COPY README.md ./
COPY main.py ./
COPY pyproject.toml ./
COPY scripts/ ./scripts/

# Create directory for persistent config
RUN mkdir -p /root/.hummingbot_mcp

# Set environment variable to indicate we're running in Docker
ENV DOCKER_CONTAINER=true

# Volume for persistent server configuration
VOLUME ["/root/.hummingbot_mcp"]

# Run the MCP server using the pre-built venv
ENTRYPOINT ["/app/.venv/bin/python", "main.py"]
