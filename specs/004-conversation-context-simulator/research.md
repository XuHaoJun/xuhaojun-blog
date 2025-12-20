# Research: ConnectRPC Integration and Fact Extraction

## Decision 1: Backend ConnectRPC Migration (Python)
- **Decision**: Migrate `blog_agent` Python server from standard `grpcio` to `connectrpc`.
- **Rationale**: ConnectRPC provides better support for HTTP/1.1 and HTTP/2, works natively with standard Python ASGI servers like Uvicorn/Starlette, and simplifies frontend-backend communication.
- **Implementation**:
    - Add `connectrpc` and `starlette` to `python-workspace/apps/server/pyproject.toml`.
    - Update `blog_agent/main.py` to use `connectrpc.asgi.Connect` and wrap it in a Starlette application.
    - Update `scripts/generate-proto.sh` to generate ConnectRPC service classes.
- **Alternatives Considered**: 
    - Staying with `grpcio`: Rejected due to complexity of web-gRPC compatibility (requires proxies like envoy or specialized libraries).
    - FastAPI: Possible, but Starlette is more lightweight and sufficient for this service.

## Decision 2: Frontend ConnectRPC Migration (TypeScript)
- **Decision**: Update `typescript-workspace` to use ConnectRPC for all RPC calls.
- **Rationale**: Seamless integration with the new backend and improved development experience with `@bufbuild/protobuf` and `@connectrpc/connect`.
- **Implementation**:
    - Add `protoc-gen-connect-es` to `typescript-workspace/packages/proto-gen/buf.gen.yaml`.
    - Update `typescript-workspace/packages/rpc-client/src/index.ts` to use `createConnectTransport`.
- **Alternatives Considered**: 
    - `grpc-web`: Rejected as ConnectRPC is the modern successor with better performance and simpler setup.

## Decision 3: Fact Extract Memory Implementation
- **Decision**: Use a LlamaIndex-based workflow for fact extraction.
- **Rationale**: The project already heavily uses LlamaIndex. A simple extraction workflow can process the conversation history and summarize it into a "fact-oriented" representation.
- **Implementation**:
    - New service `python-workspace/apps/server/src/blog_agent/services/memory.py`.
    - Use `SummaryIndex` or a custom extraction prompt with an LLM.
    - Enforce character limits by adjusting the extraction density or truncating the output.
- **Alternatives Considered**: 
    - Simple text summarization: Rejected as it might lose technical context or specific user intent needed for "simulation."

## Decision 4: Packaging Format (XML-like)
- **Decision**: Use explicit `<History>` and `<Task>` tags as clarified.
- **Rationale**: Clear separation between context and current instruction is a best practice for complex prompts.
- **Implementation**:
    - Client-side formatting logic in `conversation-viewer.tsx`.
    - Wraps historical messages in `<History>` and the target message in `<Task>`.

