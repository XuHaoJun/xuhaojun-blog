/**
 * List conversation logs command (T087)
 */

import { Command } from "commander";
import { createClient } from "../client/grpc-client";

export function createListCommand(): Command {
  const command = new Command("list");

  command
    .description("List processed conversation logs")
    .option("--server <url>", "gRPC server URL", "http://localhost:50051")
    .option("--page-size <number>", "Number of items per page", "100")
    .option("--page-token <token>", "Page token for pagination", "0")
    .option("--language <lang>", "Filter by language (e.g., 'zh-TW', 'en')")
    .action(async (options) => {
      try {
        console.log("Connecting to server...");

        // Create client
        const client = createClient({ baseUrl: options.server });

        console.log("Fetching conversation logs...");

        // TODO: Uncomment after proto generation
        // const result = await client.listConversationLogs({
        //   page_size: parseInt(options.pageSize, 10),
        //   page_token: options.pageToken,
        //   language_filter: options.language || undefined,
        // });

        // console.log(`\n✓ Found ${result.total_count} conversation log(s)\n`);

        // if (result.conversation_logs && result.conversation_logs.length > 0) {
        //   console.log("對話紀錄列表 (Conversation Logs):\n");
        //   result.conversation_logs.forEach((log, index) => {
        //     console.log(`${index + 1}. ${log.file_path}`);
        //     console.log(`   ID: ${log.id}`);
        //     console.log(`   格式: ${log.file_format}`);
        //     if (log.language) {
        //       console.log(`   語言: ${log.language}`);
        //     }
        //     if (log.message_count) {
        //       console.log(`   訊息數量: ${log.message_count}`);
        //     }
        //     if (log.created_at) {
        //       console.log(`   建立時間: ${log.created_at}`);
        //     }
        //     console.log("");
        //   });

        //   if (result.next_page_token) {
        //     console.log(`\n下一頁 token: ${result.next_page_token}`);
        //     console.log("使用 --page-token 參數來取得下一頁");
        //   }
        // } else {
        //   console.log("沒有找到對話紀錄");
        // }

        // Temporary placeholder until proto generation
        console.log("\n⚠ Proto generation required (T021)");
        console.log("Please run: ./scripts/generate-proto.sh");
        console.log("\nFor now, listing is not available.");
        console.log("\nNote: Once proto generation is complete, this command will:");
        console.log("  - List all processed conversation logs");
        console.log("  - Support pagination with --page-size and --page-token");
        console.log("  - Support language filtering with --language");

      } catch (error: any) {
        console.error("\n✗ Listing failed:");
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

