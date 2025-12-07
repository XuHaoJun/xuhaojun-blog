import Link from "next/link";
import { createServerClient } from "@/lib/grpc-client";
import { ListBlogPostsRequest } from "@blog-agent/proto-gen";

export const revalidate = 3600; // Revalidate every hour

async function getBlogPosts() {
  const client = createServerClient();
  const request = ListBlogPostsRequest.create({
    pageSize: 100,
  });

  try {
    const response = await client.listBlogPosts(request);
    return response.blogPosts || [];
  } catch (error) {
    console.error("Failed to fetch blog posts:", error);
    return [];
  }
}

export default async function HomePage() {
  const blogPosts = await getBlogPosts();

  return (
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

        {blogPosts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400">
              目前還沒有部落格文章。使用 CLI 處理對話紀錄以生成文章。
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {blogPosts.map((post) => (
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
        )}
      </div>
    </div>
  );
}

