# Data Model: AI Conversation to Blog Agent System

**Date**: 2025-12-07  
**Feature**: 001-conversation-blog-agent

## Overview

本文件定義系統的核心資料模型，包含資料庫實體、Pydantic 模型與 gRPC 訊息型別。

## Database Schema (PostgreSQL)

### conversation_logs

儲存輸入的對話紀錄。

```sql
CREATE TABLE conversation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,                    -- 原始檔案路徑
    file_format TEXT NOT NULL CHECK (file_format IN ('markdown', 'json', 'csv', 'text')),
    raw_content TEXT NOT NULL,                   -- 原始檔案內容
    parsed_content JSONB NOT NULL,               -- 解析後的結構化內容
    metadata JSONB,                             -- 額外 metadata (timestamps, participants, etc.)
    language TEXT,                               -- 偵測到的語言
    message_count INTEGER,                       -- 訊息數量
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_conversation_logs_created_at ON conversation_logs (created_at DESC);
CREATE INDEX idx_conversation_logs_language ON conversation_logs (language);
```

### blog_posts

儲存生成的部落格文章。

```sql
CREATE TABLE blog_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    content TEXT NOT NULL,                      -- Markdown 格式的內容
    metadata JSONB,                             -- 額外 metadata (author, date, etc.)
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_blog_posts_conversation_log_id ON blog_posts (conversation_log_id);
CREATE INDEX idx_blog_posts_status ON blog_posts (status);
CREATE INDEX idx_blog_posts_created_at ON blog_posts (created_at DESC);
```

### processing_history

儲存處理歷史記錄，連結對話紀錄與部落格文章。

```sql
CREATE TABLE processing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    blog_post_id UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,                         -- 如果失敗，儲存錯誤訊息
    processing_steps JSONB,                     -- 各步驟的處理結果
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_processing_history_conversation_log_id ON processing_history (conversation_log_id);
CREATE INDEX idx_processing_history_status ON processing_history (status);
CREATE INDEX idx_processing_history_started_at ON processing_history (started_at DESC);
```

### content_extracts

儲存中間處理狀態（內容萃取結果）。

```sql
CREATE TABLE content_extracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    key_insights TEXT[] NOT NULL DEFAULT '{}',
    core_concepts TEXT[] NOT NULL DEFAULT '{}',
    filtered_content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_content_extracts_conversation_log_id ON content_extracts (conversation_log_id);
```

### review_findings

儲存審閱結果。

```sql
CREATE TABLE review_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_extract_id UUID NOT NULL REFERENCES content_extracts(id) ON DELETE CASCADE,
    issues JSONB NOT NULL,                       -- 發現的問題列表
    improvement_suggestions TEXT[] NOT NULL DEFAULT '{}',
    fact_checking_needs TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_review_findings_content_extract_id ON review_findings (content_extract_id);
```

### prompt_suggestions

儲存提示詞分析結果。

```sql
CREATE TABLE prompt_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    original_prompt TEXT NOT NULL,
    analysis TEXT NOT NULL,
    better_candidates TEXT[] NOT NULL DEFAULT '{}',  -- 至少 3 個候選
    reasoning TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_prompt_suggestions_conversation_log_id ON prompt_suggestions (conversation_log_id);
```

### embeddings

儲存向量 embeddings（使用 pgvector）。

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('conversation_log', 'blog_post', 'content_extract')),
    entity_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),                     -- OpenAI ada-002 dimension
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_embeddings_entity ON embeddings (entity_type, entity_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Pydantic Models (Python)

### ConversationLog

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class ConversationLog(BaseModel):
    id: Optional[UUID] = None
    file_path: str
    file_format: str = Field(..., pattern="^(markdown|json|csv|text)$")
    raw_content: str
    parsed_content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    message_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Message(BaseModel):
    role: str  # "user" or "system" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
```

### BlogPost

```python
class BlogPost(BaseModel):
    id: Optional[UUID] = None
    conversation_log_id: UUID
    title: str
    summary: str
    tags: List[str] = Field(default_factory=list)
    content: str  # Markdown format
    metadata: Optional[Dict[str, Any]] = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### ProcessingHistory

```python
class ProcessingHistory(BaseModel):
    id: Optional[UUID] = None
    conversation_log_id: UUID
    blog_post_id: Optional[UUID] = None
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    error_message: Optional[str] = None
    processing_steps: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
```

### ContentExtract

```python
class ContentExtract(BaseModel):
    id: Optional[UUID] = None
    conversation_log_id: UUID
    key_insights: List[str] = Field(default_factory=list)
    core_concepts: List[str] = Field(default_factory=list)
    filtered_content: str
    created_at: Optional[datetime] = None
```

### ReviewFindings

```python
class ReviewFindings(BaseModel):
    id: Optional[UUID] = None
    content_extract_id: UUID
    issues: Dict[str, Any]  # Structured issues
    improvement_suggestions: List[str] = Field(default_factory=list)
    fact_checking_needs: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
```

### PromptSuggestion

```python
class PromptSuggestion(BaseModel):
    id: Optional[UUID] = None
    conversation_log_id: UUID
    original_prompt: str
    analysis: str
    better_candidates: List[str] = Field(..., min_items=3)  # At least 3 candidates (FR-012)
    reasoning: str
    created_at: Optional[datetime] = None
```

## gRPC Message Types

見 `contracts/blog_agent.proto` 檔案定義。

## Relationships

```
conversation_logs (1) ──→ (N) blog_posts
conversation_logs (1) ──→ (N) processing_history
conversation_logs (1) ──→ (N) content_extracts
conversation_logs (1) ──→ (N) prompt_suggestions
content_extracts (1) ──→ (1) review_findings
processing_history (N) ──→ (1) blog_posts
embeddings (N) ──→ (1) entity (polymorphic)
```

## Validation Rules

1. **FR-012**: `prompt_suggestions.better_candidates` 必須至少包含 3 個元素
2. **FR-017**: `conversation_logs.language` 必須是單一語言（系統自動偵測）
3. **FR-004**: `blog_posts.content` 必須是有效的 Markdown 格式
4. **FR-005**: `blog_posts` 必須包含 `title`, `summary`, `tags` 欄位

## State Transitions

### ProcessingHistory.status

```
pending → processing → completed
                ↓
             failed
```

### BlogPost.status

```
draft → published → archived
```

## Indexes for Performance

- `conversation_logs.created_at`: 支援按時間排序查詢
- `blog_posts.status`: 支援篩選已發布/草稿文章
- `embeddings.embedding`: 向量相似度搜尋（ivfflat index）

