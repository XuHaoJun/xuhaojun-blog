/**
 * Shared gRPC client for Blog Agent Service
 */

import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
// Import generated proto types (will be available after T022)
// import { BlogAgentService } from "@blog-agent/proto-gen";

export interface BlogAgentClientConfig {
  baseUrl?: string;
}

/**
 * Create a Blog Agent gRPC client
 */
export function createBlogAgentClient(config: BlogAgentClientConfig = {}) {
  const baseUrl = config.baseUrl || "http://localhost:50051";

  const transport = createConnectTransport({
    baseUrl,
    useBinaryFormat: true,
  });

  // Return client (will be uncommented after proto generation)
  // return createPromiseClient(BlogAgentService, transport);
  return null as any; // Temporary placeholder
}

export type { BlogAgentClient } from "./types";

