import { notFound } from "next/navigation";
import { createServerClient } from "@/lib/grpc-client";
import { GetBlogPostRequest, ListBlogPostsRequest } from "@blog-agent/proto-gen";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { BlogMetadata } from "@/components/blog-metadata";

export const revalidate = 3600; // Revalidate every hour

async function getBlogPost(id: string) {
  const client = createServerClient();
  const request = GetBlogPostRequest.create({
    blogPostId: id,
  });

  try {
    const response = await client.getBlogPostWithPrompts(request);
    return response;
  } catch (error) {
    console.error("Failed to fetch blog post:", error);
    return null;
  }
}

export async function generateStaticParams() {
  const client = createServerClient();
  const request = ListBlogPostsRequest.create({
    pageSize: 100,
  });

  try {
    const response = await client.listBlogPosts(request);
    return (response.blogPosts || []).map((post) => ({
      id: post.id,
    }));
  } catch (error) {
    console.error("Failed to generate static params:", error);
    return [];
  }
}

export default async function BlogPostPage({
  params,
}: {
  params: { id: string };
}) {
  const data = await getBlogPost(params.id);

  if (!data || !data.blogPost) {
    notFound();
  }

  const { blogPost, contentBlocks } = data;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <article className="max-w-4xl mx-auto">
          <BlogMetadata blogPost={blogPost} />
          <div className="mt-8 prose prose-lg dark:prose-invert max-w-none">
            <MarkdownRenderer
              content={blogPost.content || ""}
              contentBlocks={contentBlocks || []}
            />
          </div>
        </article>
      </div>
    </div>
  );
}

