/**
 * Retrieve blog posts command (T088)
 */

import { Command } from "commander";
import * as fs from "fs/promises";
import { createClient } from "../client/grpc-client";
import {
  formatBlogPostMetadata,
  formatBlogPostAsMarkdown,
  BlogPostMetadata,
} from "../utils/formatter";

export function createRetrieveCommand(): Command {
  const command = new Command("retrieve");

  command
    .description("Retrieve blog posts")
    .option("--server <url>", "gRPC server URL", "http://localhost:50051")
    .option("--id <id>", "Retrieve a specific blog post by ID")
    .option("--list", "List all blog posts")
    .option("--page-size <number>", "Number of items per page (for --list)", "100")
    .option("--page-token <token>", "Page token for pagination (for --list)", "0")
    .option("--status <status>", "Filter by status (draft, published, archived) (for --list)")
    .option("--export-markdown <path>", "Export blog post as Markdown file (for --id)")
    .action(async (options) => {
      try {
        if (!options.id && !options.list) {
          console.error("Error: Either --id or --list must be specified");
          process.exit(1);
        }

        if (options.id && options.list) {
          console.error("Error: Cannot use --id and --list together");
          process.exit(1);
        }

        console.log("Connecting to server...");

        // Create client
        const client = createClient({ baseUrl: options.server });

        if (options.id) {
          // Retrieve specific blog post
          console.log(`Fetching blog post: ${options.id}...`);

          // TODO: Uncomment after proto generation
          // const result = await client.getBlogPost({
          //   blog_post_id: options.id,
          // });

          // if (result.blog_post) {
          //   const blogPost: BlogPostMetadata = {
          //     id: result.blog_post.id,
          //     conversation_log_id: result.blog_post.conversation_log_id,
          //     title: result.blog_post.title,
          //     summary: result.blog_post.summary,
          //     tags: result.blog_post.tags || [],
          //     content: result.blog_post.content,
          //     metadata: result.blog_post.metadata ? JSON.parse(result.blog_post.metadata) : undefined,
          //     status: result.blog_post.status,
          //     created_at: result.blog_post.created_at,
          //     updated_at: result.blog_post.updated_at,
          //   };

          //   console.log("\n✓ Blog post retrieved!\n");
          //   console.log(formatBlogPostMetadata(blogPost));

          //   // Export Markdown if requested
          //   if (options.exportMarkdown) {
          //     const markdown = formatBlogPostAsMarkdown(blogPost);
          //     await fs.writeFile(options.exportMarkdown, markdown, "utf-8");
          //     console.log(`\n✓ Markdown exported to: ${options.exportMarkdown}`);
          //   }
          // } else {
          //   console.error("\n✗ Blog post not found");
          //   process.exit(1);
          // }

          // Temporary placeholder
          console.log("\n⚠ Proto generation required (T021)");
          console.log("Please run: ./scripts/generate-proto.sh");
          console.log("\nFor now, retrieval is not available.");

        } else if (options.list) {
          // List blog posts
          console.log("Fetching blog posts...");

          // TODO: Uncomment after proto generation
          // const result = await client.listBlogPosts({
          //   page_size: parseInt(options.pageSize, 10),
          //   page_token: options.pageToken,
          //   status_filter: options.status ? mapStatusToProto(options.status) : undefined,
          // });

          // console.log(`\n✓ Found ${result.total_count} blog post(s)\n`);

          // if (result.blog_posts && result.blog_posts.length > 0) {
          //   console.log("部落格文章列表 (Blog Posts):\n");
          //   result.blog_posts.forEach((post, index) => {
          //     console.log(`${index + 1}. ${post.title}`);
          //     console.log(`   ID: ${post.id}`);
          //     console.log(`   摘要: ${post.summary.substring(0, 100)}${post.summary.length > 100 ? "..." : ""}`);
          //     if (post.tags && post.tags.length > 0) {
          //       console.log(`   標籤: ${post.tags.join(", ")}`);
          //     }
          //     if (post.status) {
          //       console.log(`   狀態: ${post.status}`);
          //     }
          //     if (post.created_at) {
          //       console.log(`   建立時間: ${post.created_at}`);
          //     }
          //     console.log("");
          //   });

          //   if (result.next_page_token) {
          //     console.log(`\n下一頁 token: ${result.next_page_token}`);
          //     console.log("使用 --page-token 參數來取得下一頁");
          //   }
          // } else {
          //   console.log("沒有找到部落格文章");
          // }

          // Temporary placeholder
          console.log("\n⚠ Proto generation required (T021)");
          console.log("Please run: ./scripts/generate-proto.sh");
          console.log("\nFor now, listing is not available.");
        }

      } catch (error: any) {
        console.error("\n✗ Retrieval failed:");
        console.error(error.message);
        if (error.stack) {
          console.error("\nStack trace:");
          console.error(error.stack);
        }
        process.exit(1);
      }
    });

  return command;
}

// Helper function to map status string to proto enum
function mapStatusToProto(status: string): number {
  const statusMap: Record<string, number> = {
    draft: 1,       // BLOG_POST_STATUS_DRAFT
    published: 2,   // BLOG_POST_STATUS_PUBLISHED
    archived: 3,    // BLOG_POST_STATUS_ARCHIVED
  };
  return statusMap[status.toLowerCase()] || 0;
}

