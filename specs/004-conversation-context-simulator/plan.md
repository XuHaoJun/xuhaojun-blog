# Implementation Plan: Conversation Context Simulator (Manual Simulator)

**Branch**: `004-conversation-context-simulator` | **Date**: 2025-12-19 | **Spec**: `specs/004-conversation-context-simulator/spec.md`
**Input**: Feature specification from `/specs/004-conversation-context-simulator/spec.md`

## Summary

Implement a "Manual Simulator" feature that allows users to export conversation history in a structured format (XML-like tags) for use in other LLM web UIs. The implementation includes a "Fact Extract Memory" backend service for history compression, a UI for managing compression limits, and a transition of the existing gRPC transport layer to ConnectRPC for both frontend (TypeScript) and backend (Python).

ConnectRPC will be integrated using `connectrpc` for Python (ASGI) and `@connectrpc/connect` for ES. The backend will use LlamaIndex workflows for fact extraction to ensure high-quality context simulation.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript 5.9+, React 19+ (Next.js 16)
**Primary Dependencies**: 
- **Backend**: `connectrpc`, `starlette` (or `fastapi`), `llama-index`
- **Frontend**: `@connectrpc/connect`, `@connectrpc/connect-web`, `@blog-agent/rpc-client`, `sonner` (for toast)
**Storage**: PostgreSQL (via existing repositories for fact extraction)
**Testing**: `pytest`, `vitest`
**Target Platform**: Linux Server, Web Browser
**Project Type**: Web Application (Monorepo)
**Performance Goals**: < 200ms for context packaging (non-compressed), < 5s for fact extraction/compression
**Constraints**: < 5000 characters for default compressed history, structured XML-like output format
**Scale/Scope**: Per-message interaction in `ConversationViewer`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 原則 1: MVP 導向開發
- [x] 功能是否先實現最小可行版本？
- [x] 是否優先實現核心工作流？
- [x] 是否避免在驗證前添加非必要功能？

### 原則 2: 可測試性優先
- [x] 是否規劃單元測試（目標覆蓋率 ≥ 70%）？
- [x] 每個工作流步驟是否可獨立測試？
- [x] 是否規劃 Mock/Stub 隔離外部依賴？
- [x] 測試是否納入 CI/CD 流程？

### 原則 3: 品質優先
- [x] 是否配置 linter（ESLint/Prettier）？
- [x] 是否規劃型別定義（TypeScript 或 JSDoc）？
- [x] 是否規劃完整的錯誤處理？
- [x] 是否規劃結構化日誌記錄？

### 原則 4: 簡約設計
- [x] 是否避免過度設計？
- [x] 是否優先使用簡單直接的解決方案？
- [x] 新依賴是否有明確理由？
- [x] 複雜度是否與問題規模成正比？

### 原則 5: 正體中文優先
- [x] 使用者介面是否使用正體中文？
- [x] 文件是否以正體中文撰寫？
- [x] 程式碼註解是否以正體中文為主？

## Project Structure

### Documentation (this feature)

```text
specs/004-conversation-context-simulator/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # ConnectRPC integration & Fact extraction research
├── data-model.md        # Updated message/history structures
├── quickstart.md        # Setup guide for ConnectRPC
└── contracts/           # Updated blog_agent.proto and generated code
```

### Source Code (repository root)

```text
python-workspace/apps/server/
├── src/blog_agent/
│   ├── proto/           # Generated ConnectRPC Python code
│   ├── main.py          # Updated to start ConnectRPC server (via Starlette)
│   └── services/
│       └── memory.py    # New Fact Extract Memory service
└── pyproject.toml       # Added connectrpc dependencies

typescript-workspace/
├── packages/
│   ├── proto-gen/       # Updated with ConnectRPC plugin for ES
│   └── rpc-client/      # Updated to use ConnectRPC transport
└── apps/web/
    └── components/
        └── conversation-viewer.tsx # Manual Simulator UI
```

**Structure Decision**: Web application with monorepo structure. Updates span shared `share/proto`, the Python backend, and the TypeScript frontend/shared packages.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
