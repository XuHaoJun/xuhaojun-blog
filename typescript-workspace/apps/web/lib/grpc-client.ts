/**
 * gRPC client configuration for Next.js static generation
 * This client is used during build time for static generation
 */

import { createBlogAgentClient, type BlogAgentClient } from "@blog-agent/rpc-client";

const GRPC_SERVER_URL =
  process.env.GRPC_SERVER_URL || "http://localhost:50051";

/**
 * Create a gRPC client for server-side use (Next.js static generation)
 * This should only be used in server components or API routes
 */
export function createServerClient(): BlogAgentClient {
  return createBlogAgentClient({
    baseUrl: GRPC_SERVER_URL,
  });
}

/**
 * Get the gRPC server URL
 */
export function getGrpcServerUrl(): string {
  return GRPC_SERVER_URL;
}

