/**
 * gRPC client wrapper for Blog Agent Service
 */

import { createBlogAgentClient } from "@blog-agent/rpc-client";

export interface BlogAgentClientConfig {
  baseUrl?: string;
}

/**
 * Create and configure gRPC client
 */
export function createClient(config: BlogAgentClientConfig = {}) {
  const baseUrl = config.baseUrl || process.env.GRPC_SERVER_URL || "http://localhost:50051";

  return createBlogAgentClient({ baseUrl });
}

/**
 * Process conversation log
 */
export async function processConversation(
  client: any, // TODO: Type after proto generation
  filePath: string,
  fileContent: Buffer,
  fileFormat: string,
  metadata?: Record<string, string>,
  force?: boolean // FR-034: Force regeneration flag
) {
  // TODO: Implement after proto generation
  // return await client.processConversation({
  //   file_path: filePath,
  //   file_format: mapFileFormat(fileFormat),
  //   file_content: fileContent,
  //   metadata: metadata || {},
  //   force: force || false, // FR-034
  // });

  // Temporary placeholder
  throw new Error("Proto generation required (T021)");
}

function mapFileFormat(format: string): number {
  const formatMap: Record<string, number> = {
    markdown: 1, // FILE_FORMAT_MARKDOWN
    json: 2, // FILE_FORMAT_JSON
    csv: 3, // FILE_FORMAT_CSV
    text: 4, // FILE_FORMAT_TEXT
  };

  return formatMap[format.toLowerCase()] || 1;
}

