import { notFound } from "next/navigation";
import { create } from "@bufbuild/protobuf";
import { createServerClient } from "@/lib/grpc-client";
import { GetBlogPostRequestSchema, ListBlogPostsRequestSchema } from "@blog-agent/proto-gen";
import { BlogPostClient } from "@/app/blog/[id]/blog-post-client";
import { BlogMetadata } from "@/components/blog-metadata";

import "@/styles/prism-plus.css";
import "@/styles/prism-xonokai.css";

export const revalidate = 3600; // Revalidate every hour

async function getBlogPost(id: string) {
  const client = createServerClient();
  const request = create(GetBlogPostRequestSchema, {
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
  const request = create(ListBlogPostsRequestSchema, {
    pageSize: 100,
    pageToken: "",
    statusFilter: 0, // UNSPECIFIED
  });

  try {
    const response = await client.listBlogPosts(request);
    return (response.blogPosts || []).map((post: { id: string }) => ({
      id: post.id,
    }));
  } catch (error) {
    console.error("Failed to generate static params:", error);
    return [];
  }
}

export default async function BlogPostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = await getBlogPost(id);

  if (!data || !data.blogPost) {
    notFound();
  }

  const { blogPost, contentBlocks } = data;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header - Full Width */}
        <header className="mb-8 max-w-4xl mx-auto">
          <BlogMetadata blogPost={blogPost} />
        </header>

        {/* Main Content - 70/30 Layout on Desktop */}
        <BlogPostClient blogPost={blogPost} contentBlocks={contentBlocks || []} />
      </div>
    </div>
  );
}
