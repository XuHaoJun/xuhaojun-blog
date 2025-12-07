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

# Check if grpc_tools.protoc is available
if python3 -m grpc_tools.protoc --version &> /dev/null; then
  python3 -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$PYTHON_OUT" \
    --grpc_python_out="$PYTHON_OUT" \
    "$PROTO_DIR/blog_agent.proto"
  
  # Create __init__.py files
  touch "$PYTHON_OUT/__init__.py"
  echo "✓ Python code generated"
else
  echo "Warning: grpc_tools.protoc not found. Install with: pip install grpcio-tools"
  echo "Creating placeholder files..."
  touch "$PYTHON_OUT/__init__.py"
  cat > "$PYTHON_OUT/blog_agent_pb2.py" << 'EOF'
# Placeholder - Run: python3 -m grpc_tools.protoc to generate actual code
# This file will be generated from share/proto/blog_agent.proto
EOF
  cat > "$PYTHON_OUT/blog_agent_pb2_grpc.py" << 'EOF'
# Placeholder - Run: python3 -m grpc_tools.protoc to generate actual code
# This file will be generated from share/proto/blog_agent.proto
EOF
fi

# Generate TypeScript code
echo "Generating TypeScript code..."
mkdir -p "$TYPESCRIPT_OUT"

# Check if buf is available
if command -v buf &> /dev/null; then
  cd "$REPO_ROOT"
  buf generate "$PROTO_DIR"
  echo "✓ TypeScript code generated with buf"
elif command -v protoc &> /dev/null && npm list -g @bufbuild/protoc-gen-es &> /dev/null; then
  # Use protoc with connect-es plugin
  npx @bufbuild/protoc-gen-es \
    --proto_path="$PROTO_DIR" \
    --es_out="$TYPESCRIPT_OUT" \
    "$PROTO_DIR/blog_agent.proto"
  echo "✓ TypeScript code generated with protoc-gen-es"
else
  echo "Warning: buf or protoc-gen-es not found."
  echo "  Install buf: https://buf.build/docs/installation"
  echo "  Or install: npm install -g @bufbuild/protoc-gen-es @bufbuild/protoc-gen-connect-es"
  echo "Creating placeholder file..."
  cat > "$TYPESCRIPT_OUT/blog_agent_pb.ts" << 'EOF'
// Placeholder - Run generate-proto.sh after installing buf or protoc-gen-es
// This file will be generated from share/proto/blog_agent.proto
export {};
EOF
fi

echo ""
echo "✓ Code generation complete!"
echo "  Python: $PYTHON_OUT"
echo "  TypeScript: $TYPESCRIPT_OUT"
echo ""
echo "Note: If you see placeholder files, install required tools and run this script again."

