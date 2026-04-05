/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone", // required for Docker multi-stage build

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
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: blob:; font-src 'self' data: https://fonts.gstatic.com; connect-src 'self' https: ws: wss:; frame-ancestors 'self'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests",
          },
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=()" },
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
