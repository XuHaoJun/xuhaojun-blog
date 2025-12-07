# Research: AI Conversation to Blog Agent System

**Date**: 2025-12-07  
**Feature**: 001-conversation-blog-agent

## Research Questions & Findings

### 1. LlamaIndex Workflows 實作模式

**Question**: 如何實作 LlamaIndex Workflows 來處理對話轉部落格的工作流？

**Decision**: 使用 LlamaIndex 的 `Workflow` 類別與 `@step` 裝飾器建立多步驟工作流

**Rationale**: 
- LlamaIndex Workflows 提供清晰的步驟定義與事件傳遞機制
- 支援非同步處理，適合長時間運行的 AI 工作流
- 每個步驟可獨立測試與除錯

**Alternatives considered**:
- AgentRunner: 較舊的 API，靈活性較低
- 自行實作工作流引擎: 增加複雜度，違反簡約設計原則

**Implementation Notes**:
- 使用 `StartEvent`, `StopEvent`, 自定義 `Event` 類別
- 每個步驟返回下一個步驟的事件
- 使用 `Context` 收集多個步驟的結果

**References**:
- LlamaIndex Workflows Documentation
- 設計參考: `2025-12-07_15-48-13_Gemini_Google_Gemini.md` 中的工作流架構

---

### 2. Python gRPC Server 設定

**Question**: 如何在 Python 中設定 gRPC server 並與 LlamaIndex 整合？

**Decision**: 使用 `grpcio` 與 `grpcio-tools` 建立 gRPC server，使用 Connect-Web 協議

**Rationale**:
- Connect-Web 提供更好的 Web 整合與型別安全
- 支援 streaming 回應（適合長時間處理）
- 與 TypeScript Connect-Web client 完美整合

**Alternatives considered**:
- 傳統 gRPC: 需要額外的 gRPC-Web proxy
- REST API: 型別安全性較弱，需要額外的 OpenAPI 生成

**Implementation Notes**:
- 使用 Protocol Buffers 定義服務介面
- 使用 `grpcio-tools` 生成 Python 與 TypeScript 程式碼
- Server 使用 async/await 處理非同步請求
- 參考 tripvota 的 Rust gRPC server 架構，但改用 Python

**References**:
- Connect-Web Python Server Guide
- tripvota `rust-workspace/apps/server/` 架構參考

---

### 3. Tavily API 整合

**Question**: 如何整合 Tavily API 進行內容延伸與事實查核？

**Decision**: 使用 `tavily-python` SDK 作為 LlamaIndex 的 Tool

**Rationale**:
- Tavily 專為 AI 應用設計，提供結構化的搜尋結果
- 支援事實查核與內容延伸兩種使用場景
- API 簡單易用，符合簡約設計原則

**Alternatives considered**:
- Google Search API: 需要更複雜的設定與認證
- Serper API: 功能類似，但 Tavily 更專注於 AI 應用

**Implementation Notes**:
- 將 Tavily 包裝成 LlamaIndex `FunctionTool`
- 在工作流的 `extender.py` 步驟中使用
- 錯誤處理：API 失敗時觸發 FR-019（停止處理並回報錯誤）

**References**:
- Tavily Python SDK Documentation
- LlamaIndex Tool Integration Guide

---

### 4. PostgreSQL + pgvector 設定

**Question**: 如何設定 PostgreSQL 與 pgvector 作為向量儲存？

**Decision**: 使用 PostgreSQL 18+ 與 pgvector extension，透過 `psycopg2` 與 `pgvector` Python 套件存取

**Rationale**:
- 單一資料庫同時處理結構化資料與向量搜尋
- pgvector 成熟穩定，社群支援良好
- 符合簡約設計（不需要額外的向量資料庫服務）

**Alternatives considered**:
- Pinecone: 專用向量資料庫，但增加運維複雜度
- Chroma: 輕量級，但功能較少

**Implementation Notes**:
- 使用 Docker Compose 設定 PostgreSQL + pgvector
- 參考 tripvota 的 `docker/postgresql-ext.Dockerfile`
- 使用 LlamaIndex 的 `PostgresVectorStore` 整合
- 儲存對話紀錄的 embeddings 與生成的部落格文章

**References**:
- pgvector Documentation
- tripvota `docker/postgresql-ext.Dockerfile` 設定
- LlamaIndex PostgresVectorStore Guide

---

### 5. Next.js 靜態生成與 gRPC Client

**Question**: 如何在 Next.js 中使用 gRPC client 進行靜態生成？

**Decision**: 使用 `@connectrpc/connect-web` 與 `@connectrpc/connect-next` 在 build time 呼叫 gRPC

**Rationale**:
- Connect-Web 支援瀏覽器與 Node.js 環境
- 可在 Next.js build time 執行，生成靜態頁面
- 型別安全，與 Protocol Buffers 定義同步

**Alternatives considered**:
- REST API: 需要額外的 API 層，增加複雜度
- 直接讀取資料庫: 違反分層架構原則

**Implementation Notes**:
- 在 `next.config.mjs` 中設定 gRPC client
- 使用 `generateStaticParams` 在 build time 取得所有部落格文章
- CLI 應用也使用相同的 gRPC client 套件

**References**:
- Connect-Web Next.js Integration Guide
- Next.js Static Generation Documentation

---

### 6. 多語言專案結構 (uv + pnpm)

**Question**: 如何組織 Python (uv) 與 TypeScript (pnpm) 的多語言專案？

**Decision**: 使用獨立的 workspace 目錄，共用 `share/proto/` 目錄存放 Protocol Buffers 定義

**Rationale**:
- uv 與 pnpm 各自管理依賴，避免衝突
- 共用 proto 定義確保型別一致性
- 參考 tripvota 的成熟架構模式

**Alternatives considered**:
- 單一 monorepo 工具 (如 Nx): 增加學習曲線與複雜度
- 分離的 repository: 增加維護成本

**Implementation Notes**:
- `python-workspace/` 使用 uv 管理，包含 `pyproject.toml`
- `typescript-workspace/` 使用 pnpm workspace，包含 `pnpm-workspace.yaml`
- `share/proto/` 存放 `.proto` 檔案
- 使用 script 自動生成 Python 與 TypeScript 程式碼

**References**:
- tripvota 專案結構 (`rust-workspace/` + `typescript-workspace/`)
- uv Documentation
- pnpm Workspace Guide

---

### 7. 對話紀錄解析 (Markdown/JSON/CSV)

**Question**: 如何解析不同格式的對話紀錄？

**Decision**: 實作多個 parser，支援 Gemini 匯出的 Markdown 格式、JSON、CSV

**Rationale**:
- 不同 AI 平台匯出格式不同，需要彈性支援
- Gemini 匯出的 Markdown 格式包含 frontmatter 與結構化內容
- JSON/CSV 為常見的資料交換格式

**Alternatives considered**:
- 強制單一格式: 降低使用者體驗
- 使用通用解析器: 可能無法正確處理特定格式的語意

**Implementation Notes**:
- 實作 `MarkdownParser` 解析 Gemini 匯出格式（參考 `2025-12-07_15-30-59_Gemini_Google_Gemini.md`）
- 實作 `JSONParser` 與 `CSVParser` 處理標準格式
- 所有 parser 輸出統一的 `ConversationLog` Pydantic 模型
- 自動偵測檔案格式

**References**:
- 範例對話紀錄: `2025-12-07_15-30-59_Gemini_Google_Gemini.md`
- Pydantic Documentation

---

### 8. 錯誤處理與外部服務失敗

**Question**: 如何處理外部服務（LLM、Tavily）失敗的情況？

**Decision**: 實作完整的錯誤處理，外部服務失敗時立即停止並回報錯誤（符合 FR-019）

**Rationale**:
- 確保資料一致性，避免部分處理的狀態
- 明確的錯誤訊息幫助使用者理解問題
- 符合 spec 中的 FR-019 要求

**Alternatives considered**:
- 優雅降級: 可能產生不完整的輸出，違反品質優先原則
- 重試機制: 增加複雜度，且 spec 明確要求失敗即停止

**Implementation Notes**:
- 使用 try-except 捕捉所有外部 API 呼叫
- 記錄結構化錯誤日誌
- 回傳明確的錯誤訊息給 CLI/Web UI
- 不儲存部分處理的結果

**References**:
- Python Error Handling Best Practices
- gRPC Error Codes

---

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Python Runtime | Python | 3.11+ | LlamaIndex workflows |
| Package Manager | uv | Latest | Python dependency management |
| AI Framework | LlamaIndex | Latest | Agent workflows |
| gRPC Framework | grpcio + Connect-Web | Latest | Cross-language communication |
| Vector Store | PostgreSQL + pgvector | 18+ / 0.8+ | Embedding storage |
| Search API | Tavily | Latest | Content extension & fact-checking |
| TypeScript Runtime | Node.js | 20+ | CLI & Web UI |
| Package Manager | pnpm | Latest | TypeScript dependency management |
| Web Framework | Next.js | 14+ | Static site generation |
| UI Framework | React | 18+ | Web interface |
| UI Components | shadcn/ui | Latest | Pre-built components |
| Styling | TailwindCSS | Latest | Utility-first CSS |

## Open Questions Resolved

所有技術決策已完成，無待解決的開放問題。

