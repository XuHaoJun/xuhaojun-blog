# Data Model: Display Original Content Instead of LLM-Optimized Content

**Date**: 2025-01-27  
**Feature**: 002-original-content-display

## Overview

本文件定義此功能調整涉及的資料模型變更與使用方式。此功能主要調整資料的顯示邏輯，不改變資料庫結構，但停止使用 `content_blocks` 表來儲存新文章。

## Database Schema (PostgreSQL)

### 沿用現有表格

所有表格沿用 `001-conversation-blog-agent` 的定義，無需變更：

- `conversation_logs`: 儲存原始對話紀錄，包含 `raw_content` 與 `parsed_content` (JSONB)
- `blog_posts`: 儲存生成的部落格文章
- `prompt_suggestions`: 儲存提示詞分析結果
- `content_blocks`: **不再用於新文章**，但保留表格以維持向後兼容

### content_blocks 表格狀態

**重要變更**: `content_blocks` 表格將不再用於新建立的部落格文章。

- **新文章**: 不建立 `content_blocks` 記錄
- **現有文章**: 系統會忽略已存在的 `content_blocks` 記錄，改為顯示原始對話內容
- **向後兼容**: 表格結構保留，不進行 migration 或刪除

## Pydantic Models (Python)

### ConversationMessage (新增，用於 API 回應)

```python
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class ConversationMessage(BaseModel):
    """表示對話中的單一訊息"""
    role: Literal['user', 'system', 'assistant']
    content: str  # 訊息內容（可能包含 Markdown）
    timestamp: Optional[datetime] = None  # 可選的時間戳記
```

### ConversationLog (沿用現有模型)

沿用 `001-conversation-blog-agent` 的 `ConversationLog` 模型，無需變更：

```python
class ConversationLog(BaseModel):
    id: Optional[UUID] = None
    file_path: str
    file_format: str
    raw_content: str
    parsed_content: Dict[str, Any]  # 包含 messages 陣列
    content_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    message_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**注意**: `parsed_content` 中的 `messages` 陣列格式應為：
```python
{
    "messages": [
        {
            "role": "user",
            "content": "訊息內容",
            "timestamp": "2025-01-27T10:00:00Z"  # 可選
        },
        {
            "role": "assistant",
            "content": "回應內容",
            "timestamp": "2025-01-27T10:00:05Z"  # 可選
        }
    ]
}
```

### BlogPost (沿用現有模型)

沿用 `001-conversation-blog-agent` 的 `BlogPost` 模型，無需變更。`content` 欄位保留作為向後兼容的 fallback。

### PromptSuggestion (沿用現有模型)

沿用 `001-conversation-blog-agent` 的 `PromptSuggestion` 模型，無需變更。

### ContentBlock (不再使用)

`ContentBlock` 模型保留在程式碼中，但不再用於新文章的建立。現有程式碼可能仍會查詢此模型，但結果會被忽略。

## gRPC Message Types

### ConversationMessage (新增)

```protobuf
// 對話訊息（用於前端顯示原始對話內容）
message ConversationMessage {
  string role = 1;                    // "user", "system", "assistant"
  string content = 2;                 // 訊息內容（Markdown 格式）
  string timestamp = 3;               // 可選：ISO 8601 timestamp
}
```

### GetBlogPostResponse (擴展)

```protobuf
message GetBlogPostResponse {
  BlogPost blog_post = 1;
  repeated ContentBlock content_blocks = 2;           // 保留但設為空（向後兼容）
  repeated ConversationMessage conversation_messages = 3;  // 新增：原始對話訊息
  PromptMeta prompt_meta = 4;                        // 可選：關聯的提示詞建議
}
```

**變更說明**:
- `content_blocks`: 保留欄位但設為空陣列，維持向後兼容
- `conversation_messages`: 新增欄位，包含從 `conversation_logs.parsed_content` 解析出的訊息陣列

## Relationships

```
conversation_logs (1) ──→ (N) blog_posts
conversation_logs (1) ──→ (N) prompt_suggestions
blog_posts (1) ──→ (0..N) content_blocks  [不再用於新文章]
```

**顯示邏輯**:
- `blog_posts` 透過 `conversation_log_id` 關聯到 `conversation_logs`
- 前端從 `conversation_logs.parsed_content.messages` 取得原始對話內容
- `prompt_suggestions` 透過 `conversation_log_id` 關聯，前端比對 `original_prompt` 與對話訊息

## Validation Rules

1. **FR-001**: `conversation_messages` 陣列必須包含至少一個訊息
2. **FR-002**: 每個 `ConversationMessage` 的 `role` 必須是 "user", "system", 或 "assistant"
3. **FR-010**: `conversation_messages` 中的 `content` 必須保留原始格式（Markdown、code blocks 等）
4. **FR-004**: `prompt_suggestions` 的 `original_prompt` 應該對應到對話中的 user 訊息（透過內容比對）

## Data Flow

### 後端處理流程

1. **查詢部落格文章**: 
   - 查詢 `blog_posts` 表取得文章資訊
   - 透過 `conversation_log_id` 查詢 `conversation_logs` 表
   - 從 `conversation_logs.parsed_content` 提取 `messages` 陣列
   - 查詢 `prompt_suggestions` 表取得提示詞建議

2. **轉換資料格式**:
   - 將 `parsed_content.messages` 轉換為 `ConversationMessage` 陣列
   - 將 `prompt_suggestions` 轉換為前端可用的格式
   - `content_blocks` 設為空陣列（向後兼容）

3. **回傳 gRPC 回應**:
   - `GetBlogPostResponse` 包含 `blog_post`, `conversation_messages`, `prompt_suggestions`
   - `content_blocks` 為空陣列

### 前端顯示流程

1. **接收資料**:
   - 從 `GetBlogPostResponse` 取得 `conversation_messages` 與 `prompt_suggestions`

2. **關聯提示詞建議**:
   - 比對 `prompt_suggestions.original_prompt` 與 `conversation_messages` 中的 user 訊息
   - 為匹配的訊息標記對應的提示詞建議 ID

3. **渲染 UI**:
   - `ConversationViewer` 組件顯示 `conversation_messages`
   - `PromptSidebar` 組件顯示對應的 `prompt_suggestions`
   - Intersection Observer 追蹤可見的訊息，自動更新側邊欄

## Migration Notes

**無需資料庫 migration**:
- 不修改現有表格結構
- 不刪除 `content_blocks` 表
- 不遷移現有資料

**程式碼變更**:
- 後端：停止建立 `content_blocks` 記錄
- 前端：改為顯示 `conversation_messages` 而非 `content_blocks`
- API：擴展 `GetBlogPostResponse` 以包含 `conversation_messages`

## Backward Compatibility

- **現有 API 客戶端**: `content_blocks` 欄位保留但為空，不會導致錯誤
- **現有資料**: `content_blocks` 表中的資料保留，但系統會忽略它們
- **現有文章**: 如果文章有 `content_blocks`，系統會改為顯示原始對話內容
