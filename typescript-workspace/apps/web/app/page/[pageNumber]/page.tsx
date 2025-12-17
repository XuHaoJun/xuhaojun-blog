/**
 * 分頁路由
 * Paginated blog posts route (/page/1, /page/2, ...)
 */

import { notFound } from "next/navigation";
import { BlogPostList } from "@/components/blog-post-list";
import { BlogPagination } from "@/components/blog-pagination";
import { PaginationHead } from "@/components/pagination-head";
import {
  getBlogPostsPage,
  getTotalPostCount,
  getPaginationInfo,
  PAGINATION_CONFIG,
} from "@/lib/pagination";

interface PageProps {
  params: Promise<{ pageNumber: string }>;
}

/**
 * 生成所有分頁的靜態參數
 * 使用 getTotalPostCount() 計算總頁數
 */
export async function generateStaticParams() {
  const totalPosts = await getTotalPostCount();
  const totalPages = Math.max(1, Math.ceil(totalPosts / PAGINATION_CONFIG.pageSize));

  return Array.from({ length: totalPages }, (_, i) => ({
    pageNumber: String(i + 1),
  }));
}

/**
 * 生成頁面 metadata
 */
export async function generateMetadata({ params }: PageProps) {
  const { pageNumber } = await params;
  const page = parseInt(pageNumber, 10);

  if (isNaN(page) || page < 1) {
    return { title: "Page Not Found" };
  }

  // 使用 pageToken 取得該頁資料以判斷是否有效
  const totalPosts = await getTotalPostCount();
  const pagination = getPaginationInfo(totalPosts, page);

  if (page > pagination.totalPages) {
    return { title: "Page Not Found" };
  }

  const title = page === 1 ? "Blog Agent" : `Blog Agent - 第 ${page} 頁`;
  const description = `部落格文章列表 - 第 ${page} 頁，共 ${pagination.totalPages} 頁`;

  return {
    title,
    description,
    alternates: {
      canonical: `/page/${page}`,
    },
  };
}

export default async function PaginatedPage({ params }: PageProps) {
  const { pageNumber } = await params;
  const page = parseInt(pageNumber, 10);

  // 驗證頁碼
  if (isNaN(page) || page < 1) {
    notFound();
  }

  // 使用 pageToken 取得特定頁面的文章（SSR 相容）
  const { posts, hasNext } = await getBlogPostsPage(page, PAGINATION_CONFIG.pageSize);
  
  // 取得總文章數以計算分頁資訊
  const totalPosts = await getTotalPostCount();
  const pagination = getPaginationInfo(totalPosts, page);

  // 頁碼超出範圍
  if (page > pagination.totalPages) {
    notFound();
  }

  return (
    <>
      <PaginationHead pagination={pagination} />
      <div className="min-h-screen bg-white dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-12">
          <header className="mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              Blog Agent
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              AI Conversation to Blog Posts
            </p>
            {pagination.totalPages > 1 && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                第 {page} 頁，共 {pagination.totalPages} 頁
              </p>
            )}
          </header>

          <BlogPostList posts={posts} />
          <BlogPagination pagination={pagination} />
        </div>
      </div>
    </>
  );
}
