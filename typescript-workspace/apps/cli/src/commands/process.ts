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
    .option(
      "--format <format>",
      "File format (markdown, json, csv, text). Auto-detected if not specified"
    )
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
        const result = await processConversation(
          client,
          options.file,
          fileResult.content,
          format,
          undefined // metadata
          // options.force // force flag (FR-034)
        );

        console.log("\n✓ Processing completed!");
        console.log(`Processing ID: ${result.processingId}`);

        if (result.blogPost) {
          const blogPost: BlogPostMetadata = {
            id: result.blogPost.id,
            conversation_log_id: result.blogPost.conversationLogId,
            title: result.blogPost.title,
            summary: result.blogPost.summary,
            tags: result.blogPost.tags || [],
            content: result.blogPost.content,
            metadata: result.blogPost.metadata ? result.blogPost.metadata : undefined,
            status: result.blogPost.status.toString(),
            created_at: result.blogPost.createdAt,
            updated_at: result.blogPost.updatedAt,
          };

          // Display structured metadata
          console.log("\n" + formatBlogPostMetadata(blogPost));

          // Export Markdown if requested
          if (options.exportMarkdown) {
            const markdown = formatBlogPostAsMarkdown(blogPost);
            await fs.writeFile(options.exportMarkdown, markdown, "utf-8");
            console.log(`\n✓ Markdown exported to: ${options.exportMarkdown}`);
          }

          // Export metadata JSON if requested
          if (options.exportMetadata) {
            const metadataJson = JSON.stringify(blogPost, null, 2);
            await fs.writeFile(options.exportMetadata, metadataJson, "utf-8");
            console.log(`\n✓ Metadata exported to: ${options.exportMetadata}`);
          }
        }
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
