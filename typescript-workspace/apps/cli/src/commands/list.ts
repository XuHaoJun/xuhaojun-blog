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

        const result = await client.listConversationLogs({
          pageSize: parseInt(options.pageSize, 10),
          pageToken: options.pageToken,
          languageFilter: options.language || undefined,
        });

        console.log(`\n✓ Found ${result.totalCount} conversation log(s)\n`);

        if (result.conversationLogs && result.conversationLogs.length > 0) {
          console.log("對話紀錄列表 (Conversation Logs):\n");
          result.conversationLogs.forEach((log, index) => {
            console.log(`${index + 1}. ${log.filePath}`);
            console.log(`   ID: ${log.id}`);
            console.log(`   格式: ${log.fileFormat}`);
            if (log.language) {
              console.log(`   語言: ${log.language}`);
            }
            if (log.messageCount) {
              console.log(`   訊息數量: ${log.messageCount}`);
            }
            if (log.createdAt) {
              console.log(`   建立時間: ${log.createdAt}`);
            }
            console.log("");
          });

          if (result.nextPageToken) {
            console.log(`\n下一頁 token: ${result.nextPageToken}`);
            console.log("使用 --page-token 參數來取得下一頁");
          }
        } else {
          console.log("沒有找到對話紀錄");
        }
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
