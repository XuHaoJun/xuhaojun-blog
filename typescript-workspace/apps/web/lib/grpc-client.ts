/**
 * ConnectRPC client configuration for Next.js server-side logic
 * This client is used during build time for static generation and in API routes.
 */

import { createBlogAgentClient, type BlogAgentClient } from "@blog-agent/rpc-client";

/**
 * Create a ConnectRPC client for server-side use
 * This should only be used in server components or API routes
 */
export function createServerClient(): BlogAgentClient {
  return createBlogAgentClient();
}

/**
 * Get the RPC server URL
 */
export function getGrpcServerUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:50051";
}
