# Stage 1: Dependencies
FROM python:3.12-slim AS deps
WORKDIR /app
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install uv
COPY pyproject.toml uv.lock hummingbot_mcp/ README.md ./
RUN uv venv && uv pip install .

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install uv

# Copy the virtual environment from the deps stage
COPY --from=deps /app/.venv /app/.venv

# Copy source code
COPY hummingbot_mcp/ ./hummingbot_mcp/
COPY README.md ./
COPY main.py ./
COPY pyproject.toml ./

# Set environment variable to indicate we're running in Docker
ENV DOCKER_CONTAINER=true

# Run the MCP server using the pre-built venv
ENTRYPOINT ["/app/.venv/bin/python", "main.py"]
