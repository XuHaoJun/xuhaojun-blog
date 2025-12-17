# Research: SSG Pagination

**Feature**: 003-ssg-pagination  
**Date**: 2025-12-17

## 研究項目

### 1. Next.js App Router 靜態分頁最佳實踐

**Decision**: 使用 `generateStaticParams()` 在建置時生成所有分頁路由

**Rationale**: 
- Next.js 16 App Router 原生支援 `generateStaticParams()` 用於靜態路由生成
- 專案已設定 `output: "export"` 進行完全靜態匯出
- 現有 `app/blog/[id]/page.tsx` 已使用此模式，保持一致性

**Alternatives Considered**:
- ISR (Incremental Static Regeneration): 不適用，因 `output: "export"` 不支援
- Client-side pagination: 違反 SSG 需求，增加首次載入延遲

### 2. 分頁路由結構

**Decision**: 採用 `/page/[pageNumber]` 路由，首頁 `/` 作為 page 1 別名

**Rationale**:
- 符合 Hugo 風格慣例 (`/page/1`, `/page/2`)
- SEO 友善：每頁有獨立 URL
- 首頁保持乾淨 URL，避免 redirect

**Alternatives Considered**:
- Query string (`/?page=2`): SSG 不支援動態 query string
- `/posts/page/2`: 增加不必要的 URL 深度

### 3. 文章資料取得策略

**Decision**: 建置時一次取得所有文章，本地計算分頁

**Rationale**:
- 現有 API `ListBlogPosts` 的 `total_count` 不是精確總數
- 文章數量預期 < 1000，一次取得效能可接受
- 避免修改後端 API

**Implementation**:
```typescript
// lib/pagination.ts
export async function getAllBlogPosts() {
  const client = createServerClient();
  const response = await client.listBlogPosts({
    pageSize: 10000, // 取得所有文章
    pageToken: "",
    statusFilter: 0,
  });
  return response.blogPosts || [];
}

export function paginatePosts(posts: BlogPost[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize;
  return posts.slice(start, start + pageSize);
}

export function getTotalPages(totalPosts: number, pageSize: number) {
  return Math.ceil(totalPosts / pageSize);
}
```

**Alternatives Considered**:
- 新增 `GetTotalPostCount` API: 增加後端工作量
- 多次 API 呼叫分頁取得: 建置時間增加，複雜度增加

### 4. 首頁與分頁共用邏輯

**Decision**: 抽取 `BlogPostList` 和 `BlogPagination` 元件，首頁與 `/page/[n]` 共用

**Rationale**:
- DRY 原則：避免重複程式碼
- 一致的 UI/UX 體驗
- 方便未來維護

**Component Structure**:
```
components/
├── blog-post-list.tsx    # 文章卡片列表
└── blog-pagination.tsx   # 分頁導覽 (包裝 shadcn pagination)
```

### 5. SEO Metadata 策略

**Decision**: 使用 Next.js `generateMetadata()` 動態生成每頁 metadata

**Rationale**:
- 支援 canonical URL、rel="prev/next"
- 每頁可有獨特標題 (如 "Blog - Page 2")
- 符合 SEO 最佳實踐

**Implementation**:
```typescript
export async function generateMetadata({ params }) {
  const pageNumber = parseInt(params.pageNumber);
  return {
    title: pageNumber === 1 ? "Blog" : `Blog - Page ${pageNumber}`,
    alternates: {
      canonical: pageNumber === 1 ? "/" : `/page/${pageNumber}`,
    },
  };
}
```

### 6. 分頁導覽 UI

**Decision**: 使用現有 shadcn pagination 元件，顯示 prev/next + 頁碼 + 省略號

**Rationale**:
- 已有 `@blog-agent/ui` 中的 pagination 元件
- 符合 clarification session 中的決定
- 無需額外依賴

**Navigation Rules**:
- 首頁 `/`: 顯示 "Page 1"，下一頁連結到 `/page/2`
- `/page/1`: 上一頁不顯示，與首頁內容相同但 URL 不同
- `/page/n`: 上一頁連結到 `/page/n-1`，下一頁連結到 `/page/n+1`
- 最後一頁: 下一頁不顯示

## 技術決策總結

| 項目 | 決策 | 理由 |
|------|------|------|
| SSG 機制 | `generateStaticParams()` | Next.js 原生支援，專案已有先例 |
| 路由結構 | `/page/[pageNumber]` | Hugo 風格，SEO 友善 |
| 資料取得 | 建置時一次取得全部 | 避免後端修改，效能可接受 |
| 元件架構 | 抽取共用元件 | DRY 原則，維護性 |
| SEO | `generateMetadata()` | 動態標題、canonical URL |
| 分頁 UI | shadcn pagination | 現有元件，無需額外依賴 |

