/**
 * 分頁工具函式
 * Pagination utilities for SSG blog pages
 */

import { createServerClient } from "./grpc-client";
import type { BlogPost } from "@blog-agent/proto-gen";

/**
 * 分頁設定
 */
export const PAGINATION_CONFIG = {
  pageSize: 10, // 每頁文章數
} as const;

/**
 * 分頁資訊介面
 */
export interface PaginationInfo {
  currentPage: number;      // 目前頁碼 (1-based)
  totalPages: number;       // 總頁數
  pageSize: number;         // 每頁文章數
  totalPosts: number;       // 文章總數
  hasPrevious: boolean;     // 是否有上一頁
  hasNext: boolean;         // 是否有下一頁
}

/**
 * 單頁文章回應介面
 */
export interface BlogPostsPageResult {
  posts: BlogPost[];
  hasNext: boolean;
  nextPageToken: string;
}

/**
 * 使用 pageToken 取得特定頁面的文章（SSR 相容）
 * Fetches blog posts for a specific page using offset-based pagination
 * 
 * @param page - 頁碼 (1-based)
 * @param pageSize - 每頁文章數
 * @returns 該頁文章及是否有下一頁
 */
export async function getBlogPostsPage(
  page: number,
  pageSize: number = PAGINATION_CONFIG.pageSize
): Promise<BlogPostsPageResult> {
  const client = createServerClient();

  try {
    // pageToken 是 offset-based: pageToken = String((page - 1) * pageSize)
    const offset = (page - 1) * pageSize;
    const pageToken = offset === 0 ? "" : String(offset);

    const response = await client.listBlogPosts({
      pageSize,
      pageToken,
      statusFilter: 0, // UNSPECIFIED
    });

    const posts = response.blogPosts || [];
    const hasNext = response.nextPageToken !== "";

    return {
      posts,
      hasNext,
      nextPageToken: response.nextPageToken,
    };
  } catch (error) {
    console.error(`Failed to fetch blog posts for page ${page}:`, error);
    return {
      posts: [],
      hasNext: false,
      nextPageToken: "",
    };
  }
}

/**
 * 取得文章總數（用於 generateStaticParams 計算總頁數）
 * Gets total post count by fetching all posts once during build time
 * 
 * @returns 文章總數
 */
export async function getTotalPostCount(): Promise<number> {
  const client = createServerClient();

  try {
    // 取得所有文章以計算總數（建置時只需呼叫一次）
    const response = await client.listBlogPosts({
      pageSize: 10000,
      pageToken: "",
      statusFilter: 0,
    });

    return response.blogPosts?.length || 0;
  } catch (error) {
    console.error("Failed to fetch total post count:", error);
    return 0;
  }
}

/**
 * 取得所有部落格文章（建置時使用，僅用於 generateStaticParams）
 * Fetches all blog posts at build time
 * @deprecated 請改用 getBlogPostsPage() 取得特定頁面
 */
export async function getAllBlogPosts(): Promise<BlogPost[]> {
  const client = createServerClient();

  try {
    const response = await client.listBlogPosts({
      pageSize: 10000, // 取得所有文章
      pageToken: "",
      statusFilter: 0, // UNSPECIFIED
    });
    
    // 依建立日期降序排列（最新在前）
    const posts = response.blogPosts || [];
    return posts.sort((a, b) => {
      const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
      const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
      return dateB - dateA;
    });
  } catch (error) {
    console.error("Failed to fetch blog posts:", error);
    return [];
  }
}

/**
 * 計算分頁資訊
 */
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

/**
 * 分頁文章陣列
 */
export function paginatePosts<T>(
  posts: T[],
  page: number,
  pageSize: number = PAGINATION_CONFIG.pageSize
): T[] {
  const start = (page - 1) * pageSize;
  return posts.slice(start, start + pageSize);
}

/**
 * 產生分頁頁碼陣列（含省略號）
 * 用於 UI 顯示分頁導覽
 */
export function getPageNumbers(
  currentPage: number,
  totalPages: number,
  maxVisible = 7
): (number | "ellipsis")[] {
  if (totalPages <= maxVisible) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const pages: (number | "ellipsis")[] = [];
  const halfVisible = Math.floor((maxVisible - 3) / 2); // 扣除首頁、尾頁、當前頁

  // 總是顯示第一頁
  pages.push(1);

  // 計算開始和結束的頁碼
  let start = Math.max(2, currentPage - halfVisible);
  let end = Math.min(totalPages - 1, currentPage + halfVisible);

  // 調整以確保顯示足夠的頁碼
  if (currentPage - halfVisible <= 2) {
    end = Math.min(totalPages - 1, maxVisible - 2);
  }
  if (currentPage + halfVisible >= totalPages - 1) {
    start = Math.max(2, totalPages - maxVisible + 3);
  }

  // 加入前省略號
  if (start > 2) {
    pages.push("ellipsis");
  }

  // 加入中間頁碼
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  // 加入後省略號
  if (end < totalPages - 1) {
    pages.push("ellipsis");
  }

  // 總是顯示最後一頁
  if (totalPages > 1) {
    pages.push(totalPages);
  }

  return pages;
}

