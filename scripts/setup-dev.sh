#!/bin/bash
# Development environment setup script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Setting up development environment..."

# Check for required tools
command -v uv >/dev/null 2>&1 || { echo "Error: uv is required but not installed. Install from https://astral.sh/uv"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "Error: pnpm is required but not installed. Install with: npm install -g pnpm"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Warning: docker is not installed. Docker is optional but recommended."; }

# Setup Python environment
echo "Setting up Python workspace..."
cd "$REPO_ROOT/python-workspace"
if [ ! -d ".venv" ]; then
  uv venv
fi
source .venv/bin/activate || source .venv/Scripts/activate  # Windows compatibility
uv sync

# Setup TypeScript environment
echo "Setting up TypeScript workspace..."
cd "$REPO_ROOT/typescript-workspace"
pnpm install

# Generate Protocol Buffers code
echo "Generating Protocol Buffers code..."
cd "$REPO_ROOT"
./scripts/generate-proto.sh

# Setup database (if docker is available)
if command -v docker >/dev/null 2>&1; then
  echo "Starting PostgreSQL with pgvector..."
  cd "$REPO_ROOT"
  docker-compose up -d db
  echo "Waiting for database to be ready..."
  sleep 5
fi

echo "✓ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set up environment variables (.env files)"
echo "  2. Run database migrations: cd python-workspace/apps/server && uv run python -m blog_agent.storage.migrations.init_db"
echo "  3. Start the gRPC server: cd python-workspace/apps/server && uv run python -m blog_agent.main"

