# Quickstart: SSG Pagination

**Feature**: 003-ssg-pagination  
**Date**: 2025-12-17

## 先決條件

- Node.js 20+
- pnpm 9+
- gRPC 服務運行於 `http://localhost:50051`

## 開發環境設定

```bash
# 1. 切換到功能分支
git checkout 003-ssg-pagination

# 2. 安裝依賴
cd typescript-workspace
pnpm install

# 3. 確認 gRPC 服務已啟動
# (在另一個終端)
cd python-workspace/apps/server
uv run python -m blog_agent.main

# 4. 啟動開發伺服器
cd typescript-workspace/apps/web
pnpm dev
```

## 測試分頁

### 本地開發

```bash
# 開發模式下瀏覽
open http://localhost:3000/           # 首頁 (page 1)
open http://localhost:3000/page/1     # 第一頁
open http://localhost:3000/page/2     # 第二頁
```

### 靜態建置

```bash
# 建置靜態網站
cd typescript-workspace/apps/web
pnpm build

# 檢查生成的頁面
ls -la out/page/

# 預覽靜態網站
npx serve out
```

## 核心檔案

### 分頁工具函式

```typescript
// lib/pagination.ts
import { createServerClient } from "./grpc-client";

export const PAGINATION_CONFIG = {
  pageSize: 10,
};

export interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalPosts: number;
  hasPrevious: boolean;
  hasNext: boolean;
}

export async function getAllBlogPosts() {
  const client = createServerClient();
  const response = await client.listBlogPosts({
    pageSize: 10000,
    pageToken: "",
    statusFilter: 0,
  });
  return response.blogPosts || [];
}

export function getPaginationInfo(
  totalPosts: number,
  currentPage: number,
  pageSize = PAGINATION_CONFIG.pageSize
): PaginationInfo {
  const totalPages = Math.max(1, Math.ceil(totalPosts / pageSize));
  return {
    currentPage,
    totalPages,
    pageSize,
    totalPosts,
    hasPrevious: currentPage > 1,
    hasNext: currentPage < totalPages,
  };
}

export function paginatePosts<T>(posts: T[], page: number, pageSize: number): T[] {
  const start = (page - 1) * pageSize;
  return posts.slice(start, start + pageSize);
}
```

### 分頁路由

```typescript
// app/page/[pageNumber]/page.tsx
import { notFound } from "next/navigation";
import { getAllBlogPosts, getPaginationInfo, paginatePosts, PAGINATION_CONFIG } from "@/lib/pagination";
import { BlogPostList } from "@/components/blog-post-list";
import { BlogPagination } from "@/components/blog-pagination";

export async function generateStaticParams() {
  const posts = await getAllBlogPosts();
  const totalPages = Math.ceil(posts.length / PAGINATION_CONFIG.pageSize);
  
  return Array.from({ length: totalPages }, (_, i) => ({
    pageNumber: String(i + 1),
  }));
}

export default async function PageRoute({ params }: { params: Promise<{ pageNumber: string }> }) {
  const { pageNumber } = await params;
  const page = parseInt(pageNumber, 10);
  
  if (isNaN(page) || page < 1) {
    notFound();
  }

  const allPosts = await getAllBlogPosts();
  const pagination = getPaginationInfo(allPosts.length, page);
  
  if (page > pagination.totalPages) {
    notFound();
  }

  const posts = paginatePosts(allPosts, page, pagination.pageSize);

  return (
    <div>
      <BlogPostList posts={posts} />
      <BlogPagination pagination={pagination} />
    </div>
  );
}
```

### 首頁 (Page 1 別名)

```typescript
// app/page.tsx
import { getAllBlogPosts, getPaginationInfo, paginatePosts } from "@/lib/pagination";
import { BlogPostList } from "@/components/blog-post-list";
import { BlogPagination } from "@/components/blog-pagination";

export default async function HomePage() {
  const allPosts = await getAllBlogPosts();
  const pagination = getPaginationInfo(allPosts.length, 1);
  const posts = paginatePosts(allPosts, 1, pagination.pageSize);

  return (
    <div>
      <BlogPostList posts={posts} />
      <BlogPagination pagination={pagination} isHomePage />
    </div>
  );
}
```

## 調整分頁大小

```typescript
// lib/pagination.ts
export const PAGINATION_CONFIG = {
  pageSize: 5,  // 改為每頁 5 篇
};
```

## 驗證 SEO Metadata

```bash
# 檢查 HTML head 中的 metadata
curl -s http://localhost:3000/page/2 | grep -E '<title>|rel="(prev|next|canonical)"'
```

## 常見問題

### Q: 開發模式下分頁連結是 404?

開發模式下 `generateStaticParams` 不會預先生成所有路由。確認：
1. gRPC 服務有回傳文章資料
2. 重新啟動開發伺服器

### Q: 建置時出現 API 錯誤?

確認 `NEXT_PUBLIC_API_URL` 環境變數正確設定：

```bash
NEXT_PUBLIC_API_URL=http://localhost:50051 pnpm build
```

### Q: 如何測試零文章情況?

暫時停止 gRPC 服務或清空資料庫，重新建置：

```bash
# gRPC 服務回傳空陣列時，僅生成首頁
pnpm build
ls out/page/  # 應該是空的
```

