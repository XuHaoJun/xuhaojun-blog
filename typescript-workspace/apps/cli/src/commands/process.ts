/**
 * Process conversation log command
 */

import { Command } from "commander";
import { readConversationFile } from "../utils/file-reader";
import { createClient, processConversation } from "../client/grpc-client";

export function createProcessCommand(): Command {
  const command = new Command("process");

  command
    .description("Process a conversation log and generate a blog post")
    .requiredOption("-f, --file <path>", "Path to conversation log file")
    .option("--format <format>", "File format (markdown, json, csv, text). Auto-detected if not specified")
    .option("--server <url>", "gRPC server URL", "http://localhost:50051")
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
        //   format
        // );

        // console.log("\n✓ Processing completed!");
        // console.log(`Processing ID: ${result.processing_id}`);
        // if (result.blog_post) {
        //   console.log(`Blog Post ID: ${result.blog_post.id}`);
        //   console.log(`Title: ${result.blog_post.title}`);
        // }

        // Temporary placeholder until proto generation
        console.log("\n⚠ Proto generation required (T021)");
        console.log("Please run: ./scripts/generate-proto.sh");
        console.log("\nFor now, processing is not available.");

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

