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

# Install dependencies
WORKDIR /app/python-workspace/apps/server
RUN uv sync --frozen

# Expose gRPC port
EXPOSE 50051

# Run the server
CMD ["uv", "run", "python", "-m", "blog_agent.main"]

