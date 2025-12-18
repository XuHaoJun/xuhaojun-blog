# Tasks: Conversation Context Simulator (Manual Simulator)

**Feature Name**: Conversation Context Simulator
**Implementation Plan**: `specs/004-conversation-context-simulator/plan.md`
**Created**: 2025-12-19

## Phase 1: Setup (Initialization)

- [x] T001 [P] Add ConnectRPC and Starlette dependencies in `python-workspace/apps/server/pyproject.toml`
- [x] T002 [P] Update `share/proto/blog_agent.proto` with the `ExtractConversationFacts` RPC and messages in `share/proto/blog_agent.proto`
- [x] T003 [P] Update `scripts/generate-proto.sh` to support ConnectRPC generation for Python in `scripts/generate-proto.sh`
- [x] T004 [P] Update `typescript-workspace/packages/proto-gen/buf.gen.yaml` to include `protoc-gen-connect-es` plugin in `typescript-workspace/packages/proto-gen/buf.gen.yaml`
- [x] T005 Run `./scripts/generate-proto.sh` to generate the updated Python and TypeScript RPC code

## Phase 2: Foundational (ConnectRPC Migration)

- [x] T006 [P] Update `python-workspace/apps/server/src/blog_agent/main.py` to use `connectrpc.asgi.Connect` and Starlette for the server in `python-workspace/apps/server/src/blog_agent/main.py`
- [x] T007 [P] Update `typescript-workspace/packages/rpc-client/src/index.ts` to use `createConnectTransport` from `@connectrpc/connect-web` in `typescript-workspace/packages/rpc-client/src/index.ts`
- [x] T008 [P] Update Next.js API route or gRPC client initialization in `typescript-workspace/apps/web/lib/grpc-client.ts` to ensure compatibility with ConnectRPC in `typescript-workspace/apps/web/lib/grpc-client.ts`

## Phase 3: [US1] One-Click Context Export (Priority: P1)

**Story Goal**: Allow users to copy full conversation history in structured XML-like tags.
**Independent Test**: Click copy on a message and verify clipboard contains `<History>` and `<Task>` blocks with correct roles/content.

- [x] T009 [P] [US1] Create a helper utility for formatting conversation history with XML-like tags in `typescript-workspace/apps/web/lib/context-formatter.ts`
- [x] T010 [US1] Implement the "Copy" icon button and its click handler in `typescript-workspace/apps/web/components/conversation-viewer.tsx`
- [x] T011 [US1] Integrate `sonner` or existing toast system to display "Copied to clipboard" in `typescript-workspace/apps/web/components/conversation-viewer.tsx`

## Phase 4: [US2] Compressed Context for Long Conversations (Priority: P2)

**Story Goal**: Implement fact extraction to compress long histories within token limits.
**Independent Test**: Select "Compressed version", set limit, and verify clipboard contains a summarized fact list.

- [x] T012 [P] [US2] Implement `MemoryService` using LlamaIndex for fact extraction in `python-workspace/apps/server/src/blog_agent/services/memory.py`
- [x] T013 [US2] Implement the `ExtractConversationFacts` RPC handler in `python-workspace/apps/server/src/blog_agent/main.py`
- [x] T014 [US2] Create a modal or form component for entering the compression limit (default 5000) in `typescript-workspace/apps/web/components/compression-limit-form.tsx`
- [x] T015 [US2] Implement the compression workflow (API call -> Toast/Warning -> Copy) in `typescript-workspace/apps/web/components/conversation-viewer.tsx`
- [x] T016 [US2] Add UI indicators for length threshold warnings in `typescript-workspace/apps/web/components/conversation-viewer.tsx`

## Phase 5: [US3] Selective Original/Compressed Copy (Priority: P3)

**Story Goal**: Provide a menu to choose between original and compressed versions.
**Independent Test**: Hover over a message, open the "More" menu, and successfully trigger both copy types.

- [x] T017 [US3] Add a "More" (ellipsis) icon and a dropdown menu using `@radix-ui/react-dropdown-menu` in `typescript-workspace/apps/web/components/conversation-viewer.tsx`
- [x] T018 [US3] Connect the dropdown menu items to the "Copy Original" and "Copy Compressed" handlers in `typescript-workspace/apps/web/components/conversation-viewer.tsx`

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T019 Ensure all error states (API failure, timeout) are handled with user-friendly messages in `typescript-workspace/apps/web/components/conversation-viewer.tsx`
- [x] T020 [P] Add unit tests for `MemoryService` fact extraction logic in `python-workspace/apps/server/tests/test_memory_service.py`
- [x] T021 [P] Add unit tests for context formatting utility in `typescript-workspace/apps/web/tests/context-formatter.test.ts`

## Implementation Strategy

- **MVP First**: Prioritize Phase 1-3 to deliver the core "Copy" functionality first.
- **Incremental Delivery**: Phase 4 and 5 add the advanced compression and selective UI features once the basic transport and copy logic are stable.
- **ConnectRPC First**: Ensure the transport migration is completed and verified before building the new UI features.

## Dependencies

1. **Setup (Phase 1)** must be completed first to enable code generation.
2. **Foundational (Phase 2)** must be completed to ensure frontend and backend can communicate via ConnectRPC.
3. **Phase 3 (US1)** can be implemented immediately after Phase 2.
4. **Phase 4 (US2)** depends on the backend `ExtractConversationFacts` RPC being implemented.
5. **Phase 5 (US3)** depends on both US1 and US2 being functional to provide both options in the menu.

## Parallel Execution Examples

- **Backend vs Frontend Setup**: T001 (Backend deps) and T004 (Frontend deps) can run in parallel.
- **Transport Migration**: T006 (Backend ConnectRPC) and T007 (Frontend ConnectRPC) can run in parallel.
- **Utility Logic**: T009 (Formatter) and T012 (Memory Service) can run in parallel.
- **Testing**: T020 and T021 can run in parallel at the end.

