/**
 * 首頁
 * Homepage - displays the same content as /page/1 (alias)
 */

import { BlogPostList } from "@/components/blog-post-list";
import { BlogPagination } from "@/components/blog-pagination";
import { PaginationHead } from "@/components/pagination-head";
import {
  getBlogPostsPage,
  getTotalPostCount,
  getPaginationInfo,
  PAGINATION_CONFIG,
} from "@/lib/pagination";

/**
 * 生成頁面 metadata
 * Note: rel="next" link is rendered via PaginationHead component
 */
export function generateMetadata() {
  return {
    title: "Blog Agent",
    description: "AI Conversation to Blog Posts - 使用 AI 將對話紀錄轉換為部落格文章",
    alternates: {
      canonical: "/",
    },
  };
}

export default async function HomePage() {
  // 使用 pageToken 取得第一頁的文章（SSR 相容）
  const { posts } = await getBlogPostsPage(1, PAGINATION_CONFIG.pageSize);
  
  // 取得總文章數以計算分頁資訊
  const totalPosts = await getTotalPostCount();
  const pagination = getPaginationInfo(totalPosts, 1);

  return (
    <>
      <PaginationHead pagination={pagination} isHomePage />
      <div className="min-h-screen bg-white dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-12">
          <header className="mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              Blog Agent
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              AI Conversation to Blog Posts
            </p>
          </header>

          <BlogPostList posts={posts} />
          <BlogPagination pagination={pagination} isHomePage />
        </div>
      </div>
    </>
  );
}
