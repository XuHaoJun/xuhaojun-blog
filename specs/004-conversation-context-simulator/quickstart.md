# Quickstart: Conversation Context Simulator

This guide covers the setup for the Manual Simulator feature and the ConnectRPC migration.

## Backend Setup (Python)

1. **Install Dependencies**:
   ```bash
   cd python-workspace/apps/server
   uv add connectrpc starlette uvicorn
   ```

2. **Generate ConnectRPC Code**:
   ```bash
   # Update your generate-proto.sh to include connectrpc generation
   ./scripts/generate-proto.sh
   ```

3. **Run Server**:
   ```bash
   # The server now runs as an ASGI app
   uv run python -m blog_agent.main
   ```

## Frontend Setup (TypeScript)

1. **Install Generator Plugins**:
   Ensure `protoc-gen-connect-es` is installed in `typescript-workspace`.

2. **Generate Clients**:
   ```bash
   cd typescript-workspace/packages/proto-gen
   pnpm generate
   ```

3. **Verify Client Configuration**:
   The `@blog-agent/rpc-client` should be configured to use `createConnectTransport`.

## Feature Verification

1. Open the blog post viewer.
2. Hover over any message in the conversation side-by-side view.
3. Click the **Copy** icon to copy the full structured history up to that point.
4. Click the **More** icon and select **Compressed version** to open the compression limit form.
5. Set a limit (e.g., 2000) and click **Confirm** to copy a fact-extracted version.

