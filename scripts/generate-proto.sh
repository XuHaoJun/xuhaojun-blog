#!/bin/bash
# Generate Python and TypeScript code from Protocol Buffers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROTO_DIR="$REPO_ROOT/share/proto"
PYTHON_OUT="$REPO_ROOT/python-workspace/apps/server/src/blog_agent/proto"
TYPESCRIPT_OUT="$REPO_ROOT/typescript-workspace/packages/proto-gen/src"

echo "Generating gRPC code from Protocol Buffers..."

# Generate Python code
echo "Generating Python code..."
mkdir -p "$PYTHON_OUT"

PYTHON_WORKSPACE="$REPO_ROOT/python-workspace"
PYTHON_SERVER="$PYTHON_WORKSPACE/apps/server"

# Try to use uv from python-workspace/apps/server first
if command -v uv &> /dev/null && [ -d "$PYTHON_SERVER" ]; then
  cd "$PYTHON_SERVER"
  # Try to run grpc_tools.protoc using uv
  if uv run python -m grpc_tools.protoc --version &> /dev/null; then
    echo "Using grpcio-tools from python-workspace/apps/server (uv)..."
    uv run python -m grpc_tools.protoc \
      --proto_path="$PROTO_DIR" \
      --python_out="$PYTHON_OUT" \
      --grpc_python_out="$PYTHON_OUT" \
      "$PROTO_DIR/blog_agent.proto"
    
    # Create __init__.py files
    touch "$PYTHON_OUT/__init__.py"
    echo "✓ Python code generated with uv"
  elif python3 -m grpc_tools.protoc --version &> /dev/null; then
    # Fallback to system-wide grpc_tools
    python3 -m grpc_tools.protoc \
      --proto_path="$PROTO_DIR" \
      --python_out="$PYTHON_OUT" \
      --grpc_python_out="$PYTHON_OUT" \
      "$PROTO_DIR/blog_agent.proto"
    
    # Create __init__.py files
    touch "$PYTHON_OUT/__init__.py"
    echo "✓ Python code generated with system grpc_tools"
  else
    echo "Error: grpc_tools.protoc not found."
    echo "  Run: cd python-workspace && uv sync"
    echo "  Or install: pip install grpcio-tools"
    echo "Creating placeholder files..."
    touch "$PYTHON_OUT/__init__.py"
    cat > "$PYTHON_OUT/blog_agent_pb2.py" << 'EOF'
# Placeholder - Run 'uv sync' in python-workspace, then run generate-proto.sh
# This file will be generated from share/proto/blog_agent.proto
EOF
    cat > "$PYTHON_OUT/blog_agent_pb2_grpc.py" << 'EOF'
# Placeholder - Run 'uv sync' in python-workspace, then run generate-proto.sh
# This file will be generated from share/proto/blog_agent.proto
EOF
    exit 1
  fi
elif python3 -m grpc_tools.protoc --version &> /dev/null; then
  # Fallback to system-wide grpc_tools if uv is not available
  python3 -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$PYTHON_OUT" \
    --grpc_python_out="$PYTHON_OUT" \
    "$PROTO_DIR/blog_agent.proto"
  
  # Create __init__.py files
  touch "$PYTHON_OUT/__init__.py"
  echo "✓ Python code generated with system grpc_tools"
else
  echo "Error: grpc_tools.protoc not found."
  echo "  Run: cd python-workspace && uv sync"
  echo "  Or install: pip install grpcio-tools"
  echo "Creating placeholder files..."
  touch "$PYTHON_OUT/__init__.py"
  cat > "$PYTHON_OUT/blog_agent_pb2.py" << 'EOF'
# Placeholder - Run 'uv sync' in python-workspace, then run generate-proto.sh
# This file will be generated from share/proto/blog_agent.proto
EOF
  cat > "$PYTHON_OUT/blog_agent_pb2_grpc.py" << 'EOF'
# Placeholder - Run 'uv sync' in python-workspace, then run generate-proto.sh
# This file will be generated from share/proto/blog_agent.proto
EOF
  exit 1
fi

# Generate TypeScript code
echo "Generating TypeScript code..."
mkdir -p "$TYPESCRIPT_OUT"

TYPESCRIPT_WORKSPACE="$REPO_ROOT/typescript-workspace"
PROTO_GEN_DIR="$TYPESCRIPT_WORKSPACE/packages/proto-gen"

# Check if pnpm is available
if ! command -v pnpm &> /dev/null; then
  echo "Error: pnpm not found. Install pnpm first: https://pnpm.io/installation"
  echo "Creating placeholder file..."
  cat > "$TYPESCRIPT_OUT/blog_agent_pb.ts" << 'EOF'
// Placeholder - Install pnpm and run 'pnpm install' in typescript-workspace
// This file will be generated from share/proto/blog_agent.proto
export {};
EOF
  exit 1
fi

# Check if proto-gen package exists
if [ ! -d "$PROTO_GEN_DIR" ]; then
  echo "Error: proto-gen package not found at $PROTO_GEN_DIR"
  echo "Creating placeholder file..."
  cat > "$TYPESCRIPT_OUT/blog_agent_pb.ts" << 'EOF'
// Placeholder - proto-gen package not found
// This file will be generated from share/proto/blog_agent.proto
export {};
EOF
  exit 1
fi

# Use pnpm generate to run buf generate
cd "$PROTO_GEN_DIR"
echo "Running pnpm generate in proto-gen package..."
if pnpm generate; then
  echo "✓ TypeScript code generated with pnpm generate"
else
  echo "Error: Failed to generate TypeScript code."
  echo "  Make sure dependencies are installed: cd typescript-workspace && pnpm install"
  echo "Creating placeholder file..."
  cat > "$TYPESCRIPT_OUT/blog_agent_pb.ts" << 'EOF'
// Placeholder - Run 'pnpm install' in typescript-workspace, then run generate-proto.sh
// This file will be generated from share/proto/blog_agent.proto
export {};
EOF
  exit 1
fi

echo ""
echo "✓ Code generation complete!"
echo "  Python: $PYTHON_OUT"
echo "  TypeScript: $TYPESCRIPT_OUT"
echo ""
echo "Note: If you see placeholder files, install required tools and run this script again."

