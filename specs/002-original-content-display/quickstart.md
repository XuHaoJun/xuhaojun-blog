# Quick Start Guide: Display Original Content Instead of LLM-Optimized Content

**Date**: 2025-01-27  
**Feature**: 002-original-content-display

## Overview

此功能調整將部落格文章顯示從 LLM 優化的內容區塊改為顯示原始對話內容。系統停止生成優化的內容區塊，改為直接顯示對話紀錄中的原始訊息。

## Prerequisites

- 已完成 `001-conversation-blog-agent` 功能的實作
- PostgreSQL 資料庫已設定並包含 `conversation_logs`, `blog_posts`, `prompt_suggestions` 表
- Python 3.11+ 與 TypeScript 5.0+ 開發環境已設定
- gRPC server 與 Next.js Web UI 已部署

## Quick Start

### 1. 更新 gRPC Protocol Buffers 定義

更新 `share/proto/blog_agent.proto`：

```protobuf
// 新增 ConversationMessage 訊息類型
message ConversationMessage {
  string role = 1;                    // "user", "system", "assistant"
  string content = 2;                // 訊息內容（Markdown 格式）
  string timestamp = 3;               // 可選：ISO 8601 timestamp
}

// 更新 GetBlogPostWithPromptsResponse
message GetBlogPostWithPromptsResponse {
  BlogPost blog_post = 1;
  repeated ContentBlock content_blocks = 2;  // 保留但設為空（向後兼容）
  repeated ConversationMessage conversation_messages = 3;  // 新增
  repeated PromptSuggestion prompt_suggestions = 4;  // 新增
}
```

重新生成 gRPC 程式碼：
```bash
./scripts/generate-proto.sh
```

### 2. 後端修改

#### 2.1 修改 `editor.py` - 移除內容區塊生成

```python
# python-workspace/apps/server/src/blog_agent/workflows/editor.py

@step
async def edit(self, ev: ReviewEvent) -> EditEvent:
    # ... existing code ...
    
    # 移除以下程式碼：
    # content_blocks = await self._create_content_blocks(
    #     blog_content, prompt_suggestion
    # )
    
    return EditEvent(
        blog_post=blog_post,
        conversation_log_id=conversation_log_id,
        prompt_suggestion=prompt_suggestion,
        # 移除 content_blocks
    )
```

#### 2.2 修改 `blog_service.py` - 調整 GetBlogPostWithPrompts

```python
# python-workspace/apps/server/src/blog_agent/services/blog_service.py

async def get_blog_post_with_prompts(self, blog_post_id: str) -> GetBlogPostWithPromptsResponse:
    # 取得部落格文章
    blog_post = await self.blog_post_repo.get_by_id(blog_post_id)
    
    # 取得對話紀錄
    conversation_log = await self.conversation_log_repo.get_by_id(
        blog_post.conversation_log_id
    )
    
    # 解析對話訊息
    parsed_content = conversation_log.parsed_content
    messages = parsed_content.get("messages", [])
    conversation_messages = [
        ConversationMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg.get("timestamp")
        )
        for msg in messages
    ]
    
    # 取得提示詞建議
    prompt_suggestions = await self.prompt_suggestion_repo.get_by_conversation_log_id(
        blog_post.conversation_log_id
    )
    
    return GetBlogPostWithPromptsResponse(
        blog_post=blog_post,
        content_blocks=[],  # 設為空陣列（向後兼容）
        conversation_messages=conversation_messages,
        prompt_suggestions=prompt_suggestions
    )
```

### 3. 前端修改

#### 3.1 建立 `ConversationViewer` 組件

```typescript
// typescript-workspace/apps/web/components/conversation-viewer.tsx

interface ConversationMessage {
  role: 'user' | 'system' | 'assistant';
  content: string;
  timestamp?: string;
}

export function ConversationViewer({ 
  messages,
  onMessageHover,
  onMessageLeave 
}: {
  messages: ConversationMessage[];
  onMessageHover?: (index: number) => void;
  onMessageLeave?: () => void;
}) {
  return (
    <div className="space-y-4">
      {messages.map((msg, index) => (
        <div
          key={index}
          id={`message-${index}`}
          className={cn(
            "p-4 rounded-lg",
            msg.role === 'user' && "bg-blue-50 dark:bg-blue-900/20",
            msg.role === 'assistant' && "bg-gray-50 dark:bg-gray-800"
          )}
          onMouseEnter={() => onMessageHover?.(index)}
          onMouseLeave={onMessageLeave}
        >
          <div className="text-sm font-semibold mb-2">
            {msg.role === 'user' ? '👤 使用者' : '🤖 AI'}
          </div>
          <MyReactMarkdown content={msg.content} />
        </div>
      ))}
    </div>
  );
}
```

#### 3.2 修改 `blog-post-client.tsx`

```typescript
// typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx

export function BlogPostClient({
  blogPost,
  conversationMessages,
  promptSuggestions,
}: {
  blogPost: BlogPost;
  conversationMessages: ConversationMessage[];
  promptSuggestions: PromptSuggestion[];
}) {
  // 使用訊息索引而非 block ID
  const messageIds = conversationMessages
    .map((_, index) => index)
    .filter((index) => {
      // 找出有對應提示詞建議的訊息
      const msg = conversationMessages[index];
      return msg.role === 'user' && promptSuggestions.some(
        ps => ps.originalPrompt === msg.content
      );
    });

  const activeMessageId = useIntersectionObserver(messageIds, {
    enabled: messageIds.length > 0,
  });

  return (
    <div className="flex flex-col lg:flex-row gap-8">
      {/* Left Column - Original Conversation (70% on desktop) */}
      <article className="flex-1 lg:w-[70%]">
        <ConversationViewer
          messages={conversationMessages}
          onMessageHover={(index) => setHoveredMessageId(index)}
          onMessageLeave={() => setHoveredMessageId(undefined)}
        />
      </article>

      {/* Right Column - Prompt Sidebar (30% on desktop) */}
      {promptSuggestions.length > 0 && (
        <PromptSidebar
          promptSuggestions={promptSuggestions}
          conversationMessages={conversationMessages}
          activeMessageId={activeMessageId}
        />
      )}
    </div>
  );
}
```

#### 3.3 修改 `page.tsx` - 更新資料取得

```typescript
// typescript-workspace/apps/web/app/blog/[id]/page.tsx

export default async function BlogPostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = await getBlogPostWithPrompts(id);

  if (!data || !data.blogPost) {
    notFound();
  }

  const { blogPost, conversationMessages, promptSuggestions } = data;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <header className="mb-8 max-w-4xl mx-auto">
          <BlogMetadata blogPost={blogPost} />
        </header>

        <BlogPostClient
          blogPost={blogPost}
          conversationMessages={conversationMessages || []}
          promptSuggestions={promptSuggestions || []}
        />
      </div>
    </div>
  );
}
```

### 4. 測試

#### 4.1 後端測試

```python
# python-workspace/apps/server/tests/test_blog_service.py

async def test_get_blog_post_with_prompts_returns_conversation_messages():
    # 建立測試資料
    conversation_log = await create_test_conversation_log()
    blog_post = await create_test_blog_post(conversation_log.id)
    
    # 呼叫服務
    response = await blog_service.get_blog_post_with_prompts(blog_post.id)
    
    # 驗證
    assert len(response.conversation_messages) > 0
    assert response.conversation_messages[0].role in ['user', 'system', 'assistant']
    assert len(response.content_blocks) == 0  # 應為空
```

#### 4.2 前端測試

```typescript
// typescript-workspace/apps/web/components/__tests__/conversation-viewer.test.tsx

describe('ConversationViewer', () => {
  it('renders conversation messages correctly', () => {
    const messages = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there!' }
    ];
    
    render(<ConversationViewer messages={messages} />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });
});
```

## Verification Checklist

- [ ] gRPC proto 定義已更新並重新生成
- [ ] 後端 `GetBlogPostWithPrompts` 回傳 `conversation_messages`
- [ ] 後端不再建立 `content_blocks` 記錄
- [ ] 前端 `ConversationViewer` 組件正確顯示對話訊息
- [ ] Side-by-Side Layout 正常運作（桌面 70/30，行動裝置堆疊）
- [ ] Intersection Observer 正確追蹤可見訊息
- [ ] 提示詞建議正確關聯到對應的 user 訊息
- [ ] 向後兼容：現有文章仍可正常顯示（使用原始對話內容）

## Troubleshooting

### 問題：對話訊息未顯示

**可能原因**: `parsed_content` 格式不正確

**解決方案**: 檢查 `conversation_logs.parsed_content` 是否包含 `messages` 陣列，每個訊息應有 `role` 與 `content` 欄位。

### 問題：提示詞建議未關聯

**可能原因**: `original_prompt` 與對話訊息內容不完全匹配

**解決方案**: 實作模糊比對或正規化（移除空白、標點符號）來比對提示詞與訊息。

### 問題：Side-by-Side Layout 在行動裝置顯示異常

**可能原因**: CSS 響應式斷點設定錯誤

**解決方案**: 確認 TailwindCSS 的 `lg:` 斷點（1024px）正確設定，行動裝置使用 `flex-col` 堆疊。

## Next Steps

1. 部署後端變更
2. 部署前端變更
3. 驗證現有文章仍可正常顯示
4. 監控錯誤日誌，確認無向後兼容問題
