/**
 * Shared gRPC client for Blog Agent Service
 */

import { createClient, Client } from "@connectrpc/connect";
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
  ExtractConversationFactsRequest,
  ExtractConversationFactsResponse,
} from "@blog-agent/proto-gen";

export interface BlogAgentClientConfig {
  baseUrl?: string;
}

/**
 * Blog Agent ConnectRPC client type
 */
export type BlogAgentClient = Client<typeof BlogAgentService>;

/**
 * Create a Blog Agent ConnectRPC client
 */
export function createBlogAgentClient(
  config: BlogAgentClientConfig = {}
): BlogAgentClient {
  const baseUrl = config.baseUrl || "http://localhost:50051";

  // Using Connect transport for better compatibility with web and modern backends
  const transport = createConnectTransport({
    baseUrl,
  });

  return createClient(BlogAgentService, transport);
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
  ExtractConversationFactsRequest,
  ExtractConversationFactsResponse,
};

