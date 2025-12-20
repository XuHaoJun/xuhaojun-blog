/** @type {import('next').NextConfig} */

// Determine deployment target from environment variable
const DEPLOY_TARGET = process.env.DEPLOY_TARGET || process.env.NODE_ENV || "development";

// Base configuration shared across all environments
const baseConfig = {
  transpilePackages: ["@blog-agent/proto-gen", "@blog-agent/rpc-client", "@blog-agent/ui"],
};

// Environment-specific configurations
const configs = {
  // Development
  development: {
    ...baseConfig,
    // No static export for dev (allows hot reload, API routes, etc.)
    images: {
      unoptimized: true,
    },
  },

  // GitHub Pages
  "gh-pages": {
    ...baseConfig,
    output: "export", // Static export for static generation
    basePath: "/xuhaojun-blog",
    images: {
      unoptimized: true, // Required for static export
    },
  },
};

// Get the appropriate config
const getConfig = () => {
  const config = configs[DEPLOY_TARGET] || configs.development;

  console.log(`🚀 Using Next.js config for: ${DEPLOY_TARGET}`);

  return config;
};

const nextConfig = getConfig();

export default nextConfig;
