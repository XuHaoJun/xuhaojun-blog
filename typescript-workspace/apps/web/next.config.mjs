/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export", // Static export for static generation
  images: {
    unoptimized: true, // Required for static export
  },
  transpilePackages: ["@blog-agent/proto-gen", "@blog-agent/rpc-client", "@blog-agent/ui"],
};

export default nextConfig;
