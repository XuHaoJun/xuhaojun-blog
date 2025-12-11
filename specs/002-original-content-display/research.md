# Research: Display Original Content Instead of LLM-Optimized Content

**Date**: 2025-01-27  
**Feature**: 002-original-content-display

## Research Questions & Findings

### 1. 原始對話內容的資料結構與存取方式

**Question**: 如何從 `conversation_logs` 表取得並解析原始對話內容？

**Decision**: 使用現有的 `conversation_logs.parsed_content` (JSONB) 欄位，其中包含結構化的訊息陣列，每個訊息包含 `role` (user/system/assistant) 與 `content` 欄位。

**Rationale**: 
- `parsed_content` 已經包含解析後的結構化資料，無需重新解析
- 現有的 parser 已經將對話紀錄轉換為統一格式
- 可以直接使用現有的 `ConversationLog` Pydantic 模型

**Alternatives considered**:
- 使用 `raw_content`: 需要重新解析，增加複雜度
- 建立新的解析邏輯: 違反簡約設計原則，重複現有功能

**Implementation Notes**:
- 在 gRPC service 的 `GetBlogPost` 方法中，同時查詢 `conversation_logs` 表
- 將 `parsed_content` 轉換為前端可用的格式
- 前端組件接收訊息陣列並渲染為對話格式

**References**:
- 現有資料模型: `specs/001-conversation-blog-agent/data-model.md`
- `ConversationLog` Pydantic 模型: `python-workspace/apps/server/src/blog_agent/storage/models.py`

---

### 2. 前端顯示原始對話內容的 UI 組件設計

**Question**: 如何設計組件來顯示原始對話內容，同時保持與提示詞建議的 Side-by-Side Layout？

**Decision**: 建立新的 `ConversationViewer` 組件，顯示結構化的對話訊息，每個訊息包含角色標籤與內容。重用現有的 `PromptSidebar` 組件。

**Rationale**: 
- 分離關注點：對話顯示與提示詞建議分開處理
- 保持現有的 Side-by-Side Layout 模式
- 可重用現有的 Intersection Observer 實作來追蹤可見的訊息區段

**Alternatives considered**:
- 修改現有的 `MarkdownRenderer`: 會增加複雜度，違反單一職責原則
- 完全重新設計 UI: 違反簡約設計原則，不必要的大幅變更

**Implementation Notes**:
- `ConversationViewer` 接收訊息陣列，每個訊息包含 `role` 與 `content`
- 使用 TailwindCSS 樣式區分不同角色的訊息（user vs assistant）
- 支援 Markdown 渲染（使用現有的 `MyReactMarkdown` 組件）
- 為每個訊息區段添加 ID，供 Intersection Observer 追蹤

**References**:
- 現有 UI 組件: `typescript-workspace/apps/web/components/markdown-renderer.tsx`
- Side-by-Side Layout 實作: `typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx`

---

### 3. 提示詞建議與原始對話內容的關聯方式

**Question**: 如何將提示詞建議與原始對話中的特定訊息關聯？

**Decision**: 使用 `prompt_suggestions.conversation_log_id` 關聯到對話紀錄，並透過訊息內容比對或訊息索引來確定對應關係。

**Rationale**: 
- `prompt_suggestions` 表已經有 `conversation_log_id` 欄位，可以關聯到對話紀錄
- `prompt_suggestions.original_prompt` 可以與對話中的 user 訊息比對
- 如果無法精確比對，則顯示所有提示詞建議在側邊欄

**Alternatives considered**:
- 在資料庫中新增關聯欄位: 需要 migration，增加複雜度
- 完全分離顯示: 失去上下文關聯，降低使用者體驗

**Implementation Notes**:
- 在後端查詢時，同時取得 `prompt_suggestions` 資料
- 前端比對 `original_prompt` 與對話中的 user 訊息
- 如果找到匹配，在對應訊息旁顯示提示圖標
- Intersection Observer 追蹤可見的訊息，自動更新側邊欄顯示對應的提示詞建議

**References**:
- 現有資料模型: `specs/001-conversation-blog-agent/data-model.md` - `prompt_suggestions` 表定義
- Intersection Observer 實作: `typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx`

---

### 4. 後端工作流中移除內容區塊生成的影響

**Question**: 移除 `content_blocks` 生成後，對現有工作流有何影響？

**Decision**: 在 `editor.py` 的 `BlogEditor` 類別中，移除 `_create_content_blocks` 方法的呼叫，不再生成內容區塊。保留 `blog_post.content` 欄位作為向後兼容的 fallback。

**Rationale**: 
- `content_blocks` 的生成是在編輯步驟中進行的，移除不影響其他步驟
- `blog_post.content` 欄位仍然存在，可用於向後兼容
- 不影響現有的資料庫結構，只是不再寫入新資料

**Alternatives considered**:
- 刪除 `content_blocks` 表: 需要 migration，且可能影響現有資料
- 保留生成但標記為 deprecated: 增加不必要的複雜度

**Implementation Notes**:
- 修改 `editor.py` 中的 `edit` 方法，移除 `content_blocks` 相關邏輯
- `EditEvent` 不再包含 `content_blocks` 欄位（或設為空陣列）
- 確保不影響其他工作流步驟的正常運作

**References**:
- 現有工作流: `python-workspace/apps/server/src/blog_agent/workflows/editor.py`
- `EditEvent` 定義: `python-workspace/apps/server/src/blog_agent/workflows/blog_workflow.py`

---

### 5. gRPC API 回應格式的調整

**Question**: `GetBlogPost` API 回應是否需要調整以包含原始對話內容？

**Decision**: 擴展 `GetBlogPostResponse` 訊息，新增 `conversation_messages` 欄位，包含結構化的對話訊息陣列。保留 `content_blocks` 欄位但設為空（向後兼容）。

**Rationale**: 
- 向後兼容：保留現有欄位，避免破壞現有客戶端
- 新增欄位：明確提供原始對話內容
- 型別安全：使用 Protocol Buffers 確保型別一致性

**Alternatives considered**:
- 完全移除 `content_blocks`: 會破壞向後兼容性
- 使用新的 API 端點: 增加複雜度，不符合簡約設計

**Implementation Notes**:
- 在 `blog_agent.proto` 中新增 `ConversationMessage` 訊息類型
- 在 `GetBlogPostResponse` 中新增 `repeated ConversationMessage conversation_messages` 欄位
- 後端查詢時同時取得 `conversation_logs` 資料並轉換為 `ConversationMessage` 陣列

**References**:
- 現有 gRPC 定義: `share/proto/blog_agent.proto`
- gRPC service 實作: `python-workspace/apps/server/src/blog_agent/main.py`

---

## Technology Stack Summary

沿用 `001-conversation-blog-agent` 的技術棧，無新增技術：

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Python Runtime | Python | 3.11+ | gRPC server |
| Package Manager | uv | Latest | Python dependency management |
| gRPC Framework | grpcio + Connect-Web | Latest | Cross-language communication |
| Database | PostgreSQL | 18+ | Data storage |
| TypeScript Runtime | Node.js | 20+ | Web UI |
| Package Manager | pnpm | Latest | TypeScript dependency management |
| Web Framework | Next.js | 14+ | Static site generation |
| UI Framework | React | 18+ | Web interface |
| UI Components | shadcn/ui | Latest | Pre-built components |
| Styling | TailwindCSS | Latest | Utility-first CSS |

## Open Questions Resolved

所有技術決策已完成，無待解決的開放問題。此功能為現有系統的調整，主要涉及顯示邏輯的修改，不涉及新的技術選擇。
