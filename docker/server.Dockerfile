FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace files
COPY python-workspace/apps/server/pyproject.toml python-workspace/apps/server/
COPY python-workspace/apps/server/uv.lock python-workspace/apps/server/
COPY python-workspace/apps/server/src/ python-workspace/apps/server/src/

# Copy proto files and script for code generation
COPY share/proto/ share/proto/
COPY scripts/generate-proto.sh scripts/

# Install dependencies (including dev dependencies)
WORKDIR /app/python-workspace/apps/server
RUN uv sync --frozen --extra dev

# Generate proto code
WORKDIR /app
RUN chmod +x scripts/generate-proto.sh && ./scripts/generate-proto.sh

# Set working directory back to the server directory for the CMD
WORKDIR /app/python-workspace/apps/server

# Expose gRPC port
EXPOSE 50051

# Run the server
CMD ["uv", "run", "python", "-m", "blog_agent.main"]

