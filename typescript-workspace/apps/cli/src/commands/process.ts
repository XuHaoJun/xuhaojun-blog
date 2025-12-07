/**
 * Process conversation log command
 */

import { Command } from "commander";
import * as fs from "fs/promises";
import * as path from "path";
import { readConversationFile } from "../utils/file-reader";
import { createClient, processConversation } from "../client/grpc-client";
import {
  formatBlogPostMetadata,
  formatBlogPostAsMarkdown,
  BlogPostMetadata,
} from "../utils/formatter";

export function createProcessCommand(): Command {
  const command = new Command("process");

  command
    .description("Process a conversation log and generate a blog post")
    .requiredOption("-f, --file <path>", "Path to conversation log file")
    .option("--format <format>", "File format (markdown, json, csv, text). Auto-detected if not specified")
    .option("--server <url>", "gRPC server URL", "http://localhost:50051")
    .option("--force", "Force regeneration even if file content hasn't changed (FR-034)", false)
    .option("--export-markdown <path>", "Export blog post as Markdown file with frontmatter")
    .option("--export-metadata <path>", "Export metadata as JSON file")
    .action(async (options) => {
      try {
        console.log(`Reading file: ${options.file}`);

        // Read file
        const fileResult = await readConversationFile(options.file);
        const format = options.format || fileResult.format;

        console.log(`Detected format: ${format}`);
        console.log("Connecting to server...");

        // Create client
        const client = createClient({ baseUrl: options.server });

        console.log("Processing conversation...");

        // Process
        // TODO: Uncomment after proto generation
        // const result = await processConversation(
        //   client,
        //   options.file,
        //   fileResult.content,
        //   format,
        //   undefined, // metadata
        //   options.force // force flag (FR-034)
        // );

        // console.log("\n✓ Processing completed!");
        // console.log(`Processing ID: ${result.processing_id}`);
        
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

        //   // Display structured metadata
        //   console.log("\n" + formatBlogPostMetadata(blogPost));

        //   // Export Markdown if requested
        //   if (options.exportMarkdown) {
        //     const markdown = formatBlogPostAsMarkdown(blogPost);
        //     await fs.writeFile(options.exportMarkdown, markdown, "utf-8");
        //     console.log(`\n✓ Markdown exported to: ${options.exportMarkdown}`);
        //   }

        //   // Export metadata JSON if requested
        //   if (options.exportMetadata) {
        //     const metadataJson = JSON.stringify(blogPost, null, 2);
        //     await fs.writeFile(options.exportMetadata, metadataJson, "utf-8");
        //     console.log(`\n✓ Metadata exported to: ${options.exportMetadata}`);
        //   }
        // }

        // Temporary placeholder until proto generation
        console.log("\n⚠ Proto generation required (T021)");
        console.log("Please run: ./scripts/generate-proto.sh");
        console.log("\nFor now, processing is not available.");
        console.log("\nNote: Once proto generation is complete, this command will:");
        console.log("  - Display structured metadata (title, summary, tags, timestamps, participants)");
        console.log("  - Support --export-markdown to export blog post with frontmatter");
        console.log("  - Support --export-metadata to export metadata as JSON");

      } catch (error: any) {
        console.error("\n✗ Processing failed:");
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

