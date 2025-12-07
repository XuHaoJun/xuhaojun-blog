import type { BlogPost } from "@blog-agent/proto-gen";

interface BlogMetadataProps {
  blogPost: BlogPost;
}

export function BlogMetadata({ blogPost }: BlogMetadataProps) {
  return (
    <header className="mb-8">
      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4 font-serif">
        {blogPost.title || "無標題"}
      </h1>

      {blogPost.summary && (
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
          {blogPost.summary}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
        {blogPost.tags && blogPost.tags.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {blogPost.tags.map((tag, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {blogPost.createdAt && (
          <time dateTime={blogPost.createdAt} className="flex items-center">
            <span className="mr-1">📅</span>
            {new Date(blogPost.createdAt).toLocaleDateString("zh-TW", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </time>
        )}

        {blogPost.updatedAt && blogPost.updatedAt !== blogPost.createdAt && (
          <time dateTime={blogPost.updatedAt} className="flex items-center">
            <span className="mr-1">🔄</span>
            更新於{" "}
            {new Date(blogPost.updatedAt).toLocaleDateString("zh-TW", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </time>
        )}
      </div>
    </header>
  );
}

