#!/bin/bash
# Generate Python and TypeScript code from Protocol Buffers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROTO_DIR="$REPO_ROOT/share/proto"
PYTHON_OUT="$REPO_ROOT/python-workspace/apps/server/src/blog_agent/proto"
TYPESCRIPT_OUT="$REPO_ROOT/typescript-workspace/apps/proto-gen/src"

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

# Check if protoc is available
if ! command -v protoc &> /dev/null; then
  echo "Error: protoc not found. Install protoc first: https://grpc.io/docs/protoc-installation/"
  echo "Creating placeholder file..."
  cat > "$TYPESCRIPT_OUT/blog_agent_pb.ts" << 'EOF'
// Placeholder - Install protoc and run 'pnpm generate-proto' in typescript-workspace
// This file will be generated from share/proto/blog_agent.proto
export {};
EOF
  exit 1
fi

# Check if tools are installed in typescript-workspace
cd "$TYPESCRIPT_WORKSPACE"
if [ -d "node_modules/@bufbuild/protoc-gen-es" ] && [ -d "node_modules/@bufbuild/protoc-gen-connect-es" ]; then
  # Use pnpm to run locally installed tools
  echo "Using locally installed proto code generators..."
  
  # Generate protobuf messages with protoc-gen-es
  protoc \
    --proto_path="$PROTO_DIR" \
    --plugin=protoc-gen-es="$TYPESCRIPT_WORKSPACE/node_modules/.bin/protoc-gen-es" \
    --es_out="$TYPESCRIPT_OUT" \
    "$PROTO_DIR/blog_agent.proto"
  
  # Generate Connect RPC services with protoc-gen-connect-es
  protoc \
    --proto_path="$PROTO_DIR" \
    --plugin=protoc-gen-connect-es="$TYPESCRIPT_WORKSPACE/node_modules/.bin/protoc-gen-connect-es" \
    --connect-es_out="$TYPESCRIPT_OUT" \
    "$PROTO_DIR/blog_agent.proto"
  
  echo "✓ TypeScript code generated with local protoc-gen-es and protoc-gen-connect-es"
elif command -v buf &> /dev/null; then
  # Fallback to buf if available
  cd "$REPO_ROOT"
  buf generate "$PROTO_DIR"
  echo "✓ TypeScript code generated with buf"
else
  echo "Error: proto code generators not found."
  echo "  Run: cd typescript-workspace && pnpm install"
  echo "  Or install buf: https://buf.build/docs/installation"
  echo "Creating placeholder file..."
  cat > "$TYPESCRIPT_OUT/blog_agent_pb.ts" << 'EOF'
// Placeholder - Run 'pnpm install' in typescript-workspace, then 'pnpm generate-proto'
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

