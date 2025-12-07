/**
 * Shared gRPC client for Blog Agent Service
 */

import { createPromiseClient, PromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { BlogAgentService } from "@blog-agent/proto-gen";
import type {
  ProcessConversationRequest,
  ProcessConversationResponse,
  ListConversationLogsRequest,
  ListConversationLogsResponse,
  GetConversationLogRequest,
  GetConversationLogResponse,
  GetBlogPostRequest,
  GetBlogPostResponse,
  GetBlogPostWithPromptsResponse,
  ListBlogPostsRequest,
  ListBlogPostsResponse,
  GetProcessingHistoryRequest,
  GetProcessingHistoryResponse,
} from "@blog-agent/proto-gen";

export interface BlogAgentClientConfig {
  baseUrl?: string;
}

/**
 * Blog Agent gRPC client type
 */
export type BlogAgentClient = PromiseClient<typeof BlogAgentService>;

/**
 * Create a Blog Agent gRPC client
 */
export function createBlogAgentClient(
  config: BlogAgentClientConfig = {}
): BlogAgentClient {
  const baseUrl = config.baseUrl || "http://localhost:50051";

  const transport = createConnectTransport({
    baseUrl,
    useBinaryFormat: true,
  });

  return createPromiseClient(BlogAgentService, transport);
}

// Export types for convenience
export type {
  ProcessConversationRequest,
  ProcessConversationResponse,
  ListConversationLogsRequest,
  ListConversationLogsResponse,
  GetConversationLogRequest,
  GetConversationLogResponse,
  GetBlogPostRequest,
  GetBlogPostResponse,
  GetBlogPostWithPromptsResponse,
  ListBlogPostsRequest,
  ListBlogPostsResponse,
  GetProcessingHistoryRequest,
  GetProcessingHistoryResponse,
};

