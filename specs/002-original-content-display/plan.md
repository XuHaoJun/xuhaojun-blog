# Implementation Plan: Display Original Content Instead of LLM-Optimized Content

**Branch**: `002-original-content-display` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-original-content-display/spec.md`

## Summary

調整部落格文章顯示功能，從顯示 LLM 優化的內容區塊改為顯示原始對話內容。系統將停止生成優化的內容區塊，改為直接從對話紀錄中提取並顯示原始對話內容。UI/UX 採用 Side-by-Side Layout（桌面 70/30，行動裝置堆疊），左側顯示原始對話內容，右側顯示提示詞修改建議。

## Technical Context

**Language/Version**: 
- Python 3.11+ (使用 uv 管理)
- TypeScript 5.0+ (使用 pnpm workspace)

**Primary Dependencies**: 
- Python: grpcio, grpcio-tools, psycopg2-binary (沿用現有依賴)
- TypeScript: Next.js 14+, @connectrpc/connect, @connectrpc/connect-web, shadcn/ui, TailwindCSS (沿用現有依賴)

**Storage**: 
- PostgreSQL 18+ (沿用現有資料庫)
- 使用現有的 `conversation_logs` 表存取原始對話內容 (`raw_content`, `parsed_content`)
- 使用現有的 `prompt_suggestions` 表存取提示詞建議
- `content_blocks` 表將不再用於新文章（向後兼容，忽略現有資料）

**Testing**: 
- Python: pytest, pytest-asyncio, pytest-mock (沿用現有測試框架)
- TypeScript: Vitest, React Testing Library (沿用現有測試框架)

**Target Platform**: 
- Web browser (Next.js UI for static generation)
- Linux/macOS (CLI，如需要)

**Project Type**: 
- Multi-language workspace (Python backend + TypeScript frontend，沿用現有架構)

**Performance Goals**: 
- 原始對話內容載入時間 < 500ms (p95)
- Side-by-Side Layout 響應式切換流暢無延遲
- Intersection Observer 追蹤效能不影響滾動體驗

**Constraints**: 
- 必須向後兼容現有部落格文章（忽略已存在的優化內容區塊）
- 必須保留現有的 Side-by-Side Layout UI/UX 模式
- 必須支援現有的 Intersection Observer 實作
- 不遷移或刪除現有資料庫中的 `content_blocks` 資料

**Scale/Scope**: 
- 單一使用者系統（沿用現有架構）
- 支援顯示任意長度的對話紀錄
- 支援現有所有對話紀錄格式（Markdown, JSON, CSV）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 原則 1: MVP 導向開發
- [x] 功能是否先實現最小可行版本？ → 優先實現核心功能：顯示原始對話內容、移除優化區塊生成
- [x] 是否優先實現核心工作流？ → 先實現 User Story 1 (顯示原始內容) 與 User Story 3 (移除優化區塊)
- [x] 是否避免在驗證前添加非必要功能？ → 保持現有 UI/UX 模式，不新增額外功能

### 原則 2: 可測試性優先
- [x] 是否規劃單元測試（目標覆蓋率 ≥ 70%）？ → 沿用現有測試框架，新增前端組件測試
- [x] 每個工作流步驟是否可獨立測試？ → 前端組件可獨立測試，後端修改可透過現有測試覆蓋
- [x] 是否規劃 Mock/Stub 隔離外部依賴？ → Mock gRPC client、對話紀錄資料
- [x] 測試是否納入 CI/CD 流程？ → 沿用現有 CI/CD 流程

### 原則 3: 品質優先
- [x] 是否配置 linter（ESLint/Prettier）？ → 沿用現有 ESLint + Prettier 配置
- [x] 是否規劃型別定義（TypeScript 或 JSDoc）？ → TypeScript 嚴格模式，沿用現有型別定義
- [x] 是否規劃完整的錯誤處理？ → 處理對話紀錄不存在、格式錯誤等情況
- [x] 是否規劃結構化日誌記錄？ → 沿用現有日誌記錄機制

### 原則 4: 簡約設計
- [x] 是否避免過度設計？ → 直接修改現有組件，不重新設計架構
- [x] 是否優先使用簡單直接的解決方案？ → 重用現有 UI 組件與布局模式
- [x] 新依賴是否有明確理由？ → 不新增依賴，沿用現有技術棧
- [x] 複雜度是否與問題規模成正比？ → 修改範圍限於顯示邏輯，不影響整體架構

### 原則 5: 正體中文優先
- [x] 使用者介面是否使用正體中文？ → 沿用現有正體中文 UI
- [x] 文件是否以正體中文撰寫？ → 所有文件與註解使用正體中文
- [x] 程式碼註解是否以正體中文為主？ → 程式碼註解優先使用正體中文

## Project Structure

### Documentation (this feature)

```text
specs/002-original-content-display/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── blog_agent.proto # Updated gRPC service definition (if needed)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

沿用現有的專案結構，主要修改以下檔案：

```text
python-workspace/apps/server/src/blog_agent/
├── workflows/
│   └── editor.py        # 修改：移除 content_blocks 生成邏輯
├── services/
│   └── blog_service.py  # 修改：調整 GetBlogPost 回應，不包含 content_blocks
└── storage/
    └── repository.py    # 修改：調整查詢邏輯，不查詢 content_blocks

typescript-workspace/apps/web/
├── app/blog/[id]/
│   ├── page.tsx         # 修改：從 conversation_log 取得原始內容
│   └── blog-post-client.tsx  # 修改：顯示原始對話內容而非 content_blocks
└── components/
    ├── markdown-renderer.tsx  # 修改：支援顯示原始對話訊息
    ├── conversation-viewer.tsx  # 新增：顯示原始對話內容的組件
    └── prompt-sidebar.tsx      # 沿用：顯示提示詞建議（無需修改）
```

**Structure Decision**: 
沿用現有的多語言 workspace 架構：
- `python-workspace/` 使用 uv 管理 Python 專案，包含 gRPC server
- `typescript-workspace/` 使用 pnpm workspace，包含 Web UI
- `share/proto/` 存放共用的 Protocol Buffers 定義（如需要更新）
- 主要修改集中在顯示邏輯，不改變整體架構

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

無違反憲章原則的情況。此功能為現有系統的調整，不增加額外複雜度。
