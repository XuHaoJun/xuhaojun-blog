/**
 * gRPC client wrapper for Blog Agent Service
 */

import { BlogAgentClient, createBlogAgentClient } from "@blog-agent/rpc-client";

export interface BlogAgentClientConfig {
  baseUrl?: string;
}

/**
 * Create and configure gRPC client
 */
export function createClient(config: BlogAgentClientConfig = {}) {
  return createBlogAgentClient();
}

/**
 * Process conversation log
 */
export async function processConversation(
  client: BlogAgentClient,
  filePath: string,
  fileContent: Buffer,
  fileFormat: string,
  metadata?: Record<string, string>,
  force?: boolean // FR-034: Force regeneration flag
) {
  return await client.processConversation({
    filePath: filePath,
    fileFormat: mapFileFormat(fileFormat),
    fileContent: fileContent,
    metadata: metadata || {},
    // force: force || false, // FR-034
  });
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
