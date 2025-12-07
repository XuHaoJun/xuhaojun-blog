# Implementation Plan: AI Conversation to Blog Agent System

**Branch**: `001-conversation-blog-agent` | **Date**: 2025-12-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-conversation-blog-agent/spec.md`

## Summary

建立一個多語言專案架構的 AI 對話轉部落格系統，使用 Python (LlamaIndex + gRPC Server) 處理核心工作流，TypeScript (Next.js + gRPC Client) 提供 CLI 與 Web UI。系統將對話紀錄轉換為結構化部落格文章，包含內容萃取、審閱、延伸、糾錯與提示詞分析功能。

## Technical Context

**Language/Version**: 
- Python 3.11+ (使用 uv 管理)
- TypeScript 5.0+ (使用 pnpm workspace)

**Primary Dependencies**: 
- Python: LlamaIndex, grpcio, grpcio-tools, psycopg2-binary, pgvector, tavily-python
- TypeScript: Next.js 14+, @connectrpc/connect, @connectrpc/connect-web, shadcn/ui, TailwindCSS

**Storage**: 
- PostgreSQL 18+ with pgvector extension
- 檔案系統 (用於儲存對話紀錄與生成的部落格文章)

**Testing**: 
- Python: pytest, pytest-asyncio, pytest-mock
- TypeScript: Vitest, React Testing Library

**Target Platform**: 
- Linux/macOS (CLI)
- Web browser (Next.js UI for static generation)

**Project Type**: 
- Multi-language workspace (Python backend + TypeScript frontend)

**Performance Goals**: 
- 單一對話紀錄處理時間 < 5 分鐘 (SC-001)
- 支援 10-1000 條訊息的對話紀錄 (SC-007)
- gRPC 請求延遲 < 500ms (p95)

**Constraints**: 
- 單一使用者本地系統 (無需認證)
- 外部服務失敗時立即停止並回報錯誤 (FR-019)
- 必須支援 Markdown 輸出格式 (FR-004)

**Scale/Scope**: 
- 單一使用者處理多個對話紀錄
- 儲存完整處理歷史 (FR-021)
- 支援 JSON, CSV, 純文字輸入格式 (FR-001)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 原則 1: MVP 導向開發
- [x] 功能是否先實現最小可行版本？ → 優先實現核心工作流：內容萃取 → 審閱 → 編輯 → 輸出
- [x] 是否優先實現核心工作流？ → 先實現 User Story 1 (基本轉換) 與 User Story 5 (結構化輸出)
- [x] 是否避免在驗證前添加非必要功能？ → 延後 User Story 4 (提示詞分析) 至 P3 優先級

### 原則 2: 可測試性優先
- [x] 是否規劃單元測試（目標覆蓋率 ≥ 70%）？ → Python 與 TypeScript 都使用標準測試框架
- [x] 每個工作流步驟是否可獨立測試？ → LlamaIndex Workflow 的每個 Step 可獨立測試
- [x] 是否規劃 Mock/Stub 隔離外部依賴？ → Mock LLM API、Tavily API、PostgreSQL
- [x] 測試是否納入 CI/CD 流程？ → 規劃 GitHub Actions 自動測試

### 原則 3: 品質優先
- [x] 是否配置 linter（ESLint/Prettier）？ → TypeScript 使用 ESLint + Prettier，Python 使用 ruff + black
- [x] 是否規劃型別定義（TypeScript 或 JSDoc）？ → TypeScript 嚴格模式，Python 使用 type hints + Pydantic
- [x] 是否規劃完整的錯誤處理？ → gRPC 錯誤處理，外部服務失敗處理 (FR-019)
- [x] 是否規劃結構化日誌記錄？ → Python 使用 structlog，TypeScript 使用 pino

### 原則 4: 簡約設計
- [x] 是否避免過度設計？ → 直接使用 LlamaIndex Workflows，不自行實作 Agent 框架
- [x] 是否優先使用簡單直接的解決方案？ → PostgreSQL + pgvector 而非複雜的向量資料庫
- [x] 新依賴是否有明確理由？ → 所有依賴都有明確用途（見 Primary Dependencies）
- [x] 複雜度是否與問題規模成正比？ → 單一使用者系統，無需複雜的分散式架構

### 原則 5: 正體中文優先
- [x] 使用者介面是否使用正體中文？ → CLI 與 Web UI 都使用正體中文
- [x] 文件是否以正體中文撰寫？ → 所有文件與註解使用正體中文
- [x] 程式碼註解是否以正體中文為主？ → 程式碼註解優先使用正體中文

## Project Structure

### Documentation (this feature)

```text
specs/001-conversation-blog-agent/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── blog_agent.proto # gRPC service definition
│   └── openapi.yaml     # Optional REST API docs
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
python-workspace/
├── pyproject.toml       # uv project configuration
├── uv.lock              # Dependency lock file
├── apps/
│   └── server/
│       ├── pyproject.toml
│       ├── src/
│       │   └── blog_agent/
│       │       ├── __init__.py
│       │       ├── main.py              # gRPC server entry point
│       │       ├── workflows/
│       │       │   ├── __init__.py
│       │       │   ├── blog_workflow.py # LlamaIndex Workflow
│       │       │   ├── extractor.py     # Content extraction step
│       │       │   ├── reviewer.py      # Review step
│       │       │   ├── extender.py     # Extension step
│       │       │   └── editor.py        # Final editing step
│       │       ├── services/
│       │       │   ├── __init__.py
│       │       │   ├── llm_service.py  # LLM abstraction
│       │       │   ├── tavily_service.py # Tavily search integration
│       │       │   └── vector_store.py  # PostgreSQL + pgvector
│       │       ├── parsers/
│       │       │   ├── __init__.py
│       │       │   ├── markdown_parser.py
│       │       │   ├── json_parser.py
│       │       │   └── csv_parser.py
│       │       ├── storage/
│       │       │   ├── __init__.py
│       │       │   ├── repository.py    # Data persistence layer
│       │       │   └── models.py        # Pydantic models
│       │       └── proto/
│       │           └── blog_agent_pb2.py # Generated gRPC code
│       └── tests/
│           ├── unit/
│           ├── integration/
│           └── fixtures/
│
typescript-workspace/
├── package.json         # pnpm workspace root
├── pnpm-workspace.yaml
├── turbo.json           # Turborepo config (optional)
├── apps/
│   └── cli/
│       ├── package.json
│       ├── src/
│       │   ├── index.ts                # CLI entry point
│       │   ├── commands/
│       │   │   ├── process.ts          # Process conversation log
│       │   │   ├── list.ts             # List processed logs
│       │   │   └── retrieve.ts         # Retrieve blog post
│       │   ├── client/
│       │   │   └── grpc-client.ts      # gRPC client wrapper
│       │   └── utils/
│       │       ├── file-reader.ts      # Read markdown/JSON/CSV
│       │       └── formatter.ts        # Output formatting
│       └── tests/
│
│   └── web/                            # Optional: Web UI for browsing
│       ├── package.json
│       ├── app/                        # Next.js App Router
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   └── blog/
│       │       └── [id]/
│       │           └── page.tsx
│       ├── components/
│       │   └── ui/                     # shadcn components
│       ├── lib/
│       │   └── grpc-client.ts          # gRPC client for static generation
│       └── styles/
│           └── globals.css            # TailwindCSS
│
│   └── proto-gen/                      # Generated TypeScript from .proto
│       ├── package.json
│       └── src/
│           └── blog_agent_pb.ts
│
│   └── rpc-client/                     # Shared gRPC client package
│       ├── package.json
│       └── src/
│           └── index.ts
│
│   └── ui/                             # Shared shadcn/ui components
│       ├── package.json
│       └── src/
│           └── components/
│
packages/
├── typescript-config/                  # Shared TS configs
└── eslint-config/                      # Shared ESLint configs

share/
└── proto/
    └── blog_agent.proto                # gRPC service definition (shared)

scripts/
├── generate-proto.sh                   # Generate Python & TS from .proto
└── setup-dev.sh                        # Development environment setup

docker/
├── postgresql.Dockerfile               # PostgreSQL + pgvector
└── server.Dockerfile                   # Python gRPC server

docker-compose.yaml                     # Local development stack
```

**Structure Decision**: 
採用多語言 workspace 架構，參考 tripvota 專案結構：
- `python-workspace/` 使用 uv 管理 Python 專案，包含 gRPC server 與 LlamaIndex workflows
- `typescript-workspace/` 使用 pnpm workspace，包含 CLI 應用與可選的 Web UI
- `share/proto/` 存放共用的 Protocol Buffers 定義
- 使用 gRPC 作為 Python 與 TypeScript 之間的通信協議，支援高效能與型別安全

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 多語言專案結構 | Python (LlamaIndex) 與 TypeScript (Next.js) 各有優勢，需要整合 | 單一語言無法同時滿足 AI 工作流 (Python) 與現代 Web 開發 (TypeScript) 的需求 |
| gRPC 而非 REST | 需要型別安全的跨語言通信，支援 streaming | REST API 需要額外的 OpenAPI 生成與驗證，且型別安全性較弱 |
| PostgreSQL + pgvector | 需要向量搜尋功能，但保持簡單的資料庫架構 | 專用的向量資料庫 (如 Pinecone) 增加運維複雜度，且不符合簡約設計原則 |
