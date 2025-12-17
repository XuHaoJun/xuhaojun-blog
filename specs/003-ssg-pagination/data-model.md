# Data Model: SSG Pagination

**Feature**: 003-ssg-pagination  
**Date**: 2025-12-17

## 概述

本功能不需要新增資料庫 schema 或後端資料模型。所有分頁邏輯在前端建置時計算，使用現有的 `BlogPost` 資料結構。

## 現有資料模型 (不變)

### BlogPost

```typescript
// 來自 @blog-agent/proto-gen
interface BlogPost {
  id: string;           // UUID
  title: string;        // 文章標題
  summary: string;      // 摘要
  content: string;      // Markdown 內容
  tags: string[];       // 標籤
  status: BlogPostStatus;
  createdAt: string;    // ISO timestamp
  updatedAt: string;    // ISO timestamp
}
```

## 新增前端型別

### PaginationInfo

分頁資訊，用於傳遞給分頁元件。

```typescript
// lib/pagination.ts
export interface PaginationInfo {
  currentPage: number;      // 目前頁碼 (1-based)
  totalPages: number;       // 總頁數
  pageSize: number;         // 每頁文章數
  totalPosts: number;       // 文章總數
  hasPrevious: boolean;     // 是否有上一頁
  hasNext: boolean;         // 是否有下一頁
}
```

### PaginatedPosts

分頁後的文章資料。

```typescript
// lib/pagination.ts
export interface PaginatedPosts {
  posts: BlogPost[];        // 當頁文章
  pagination: PaginationInfo;
}
```

## 資料流

```
建置時 (Build Time)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  gRPC Server ──▶ listBlogPosts() ──▶ getAllBlogPosts()         │
│                      │                                          │
│                      ▼                                          │
│              全部 BlogPost[]                                    │
│                      │                                          │
│          ┌──────────┴──────────┐                               │
│          ▼                     ▼                                │
│   generateStaticParams()   paginatePosts()                     │
│          │                     │                                │
│          ▼                     ▼                                │
│   [1, 2, 3, ...]         PaginatedPosts                        │
│   (page numbers)         (per page data)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                      Static HTML Files
                    (/page/1, /page/2, ...)
```

## 配置

### 分頁設定

```typescript
// lib/pagination.ts
export const PAGINATION_CONFIG = {
  pageSize: 10,  // 每頁文章數，可調整
};
```

## 驗證規則

| 欄位 | 驗證規則 |
|------|----------|
| `currentPage` | 必須 >= 1 且 <= totalPages |
| `pageSize` | 必須 > 0 |
| `totalPages` | 由 `Math.ceil(totalPosts / pageSize)` 計算 |

## 狀態轉換

本功能不涉及狀態轉換。所有分頁都是在建置時靜態生成。

## 邊界條件

| 情況 | 處理方式 |
|------|----------|
| 零篇文章 | `totalPages = 0`，首頁顯示空狀態訊息 |
| 頁碼超出範圍 | 404 Not Found |
| 無效頁碼 (非數字) | 404 Not Found |
| 頁碼 = 0 或負數 | 404 Not Found |

