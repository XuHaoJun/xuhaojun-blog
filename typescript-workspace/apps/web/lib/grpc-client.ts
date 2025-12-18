/**
 * ConnectRPC client configuration for Next.js server-side logic
 * This client is used during build time for static generation and in API routes.
 */

import { createBlogAgentClient, type BlogAgentClient } from "@blog-agent/rpc-client";

const GRPC_SERVER_URL =
  process.env.GRPC_SERVER_URL || "http://localhost:50051";

/**
 * Create a ConnectRPC client for server-side use
 * This should only be used in server components or API routes
 */
export function createServerClient(): BlogAgentClient {
  return createBlogAgentClient({
    baseUrl: GRPC_SERVER_URL,
  });
}

/**
 * Get the RPC server URL
 */
export function getGrpcServerUrl(): string {
  return GRPC_SERVER_URL;
}

