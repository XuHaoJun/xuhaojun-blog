# Contracts: SSG Pagination

**Feature**: 003-ssg-pagination  
**Date**: 2025-12-17

## 概述

本功能不需要新增或修改 API contracts。

使用現有的 `ListBlogPosts` gRPC API，在建置時取得所有文章資料並在前端計算分頁。

## 現有 API (不變)

### ListBlogPosts

```protobuf
// share/proto/blog_agent.proto

message ListBlogPostsRequest {
  int32 page_size = 1;
  string page_token = 2;
  BlogPostStatus status_filter = 3;
}

message ListBlogPostsResponse {
  repeated BlogPost blog_posts = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}
```

## 未來考量

如果文章數量增長至數千篇，可考慮新增：

1. `GetBlogPostCount` - 取得文章總數
2. 精確的 `total_count` 回傳值

目前實作以一次取得所有文章的方式處理，對於 < 1000 篇文章效能可接受。

