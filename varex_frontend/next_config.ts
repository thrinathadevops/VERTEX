// PATH: varex-frontend/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",          // required for Docker multi-stage build

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.cloudfront.net",  // AWS CloudFront CDN
      },
      {
        protocol: "https",
        hostname: "varex-assets.s3.ap-south-1.amazonaws.com",
      },
    ],
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options",        value: "SAMEORIGIN"              },
          { key: "X-Content-Type-Options",  value: "nosniff"                 },
          { key: "Referrer-Policy",         value: "no-referrer-when-downgrade" },
          { key: "Permissions-Policy",      value: "camera=(), microphone=()" },
        ],
      },
    ];
  },

  async redirects() {
    return [
      { source: "/blog/devsecops", destination: "/blog/devops", permanent: true },
    ];
  },
};

export default nextConfig;
