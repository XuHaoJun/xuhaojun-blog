/**
 * 文章列表元件
 * Blog post list component for paginated pages
 */

import Link from "next/link";
import type { BlogPost } from "@blog-agent/proto-gen";

interface BlogPostListProps {
  posts: BlogPost[];
}

export function BlogPostList({ posts }: BlogPostListProps) {
  if (posts.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          目前還沒有部落格文章。使用 CLI 處理對話紀錄以生成文章。
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {posts.map((post) => (
        <article
          key={post.id}
          className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-lg transition-shadow"
        >
          <Link href={`/blog/${post.id}`}>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2 hover:text-blue-600 dark:hover:text-blue-400">
              {post.title || "無標題"}
            </h2>
          </Link>
          {post.summary && (
            <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
              {post.summary}
            </p>
          )}
          <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
            {post.tags && post.tags.length > 0 && (
              <div className="flex gap-2">
                {post.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            {post.createdAt && (
              <time dateTime={post.createdAt}>
                {new Date(post.createdAt).toLocaleDateString("zh-TW")}
              </time>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}

