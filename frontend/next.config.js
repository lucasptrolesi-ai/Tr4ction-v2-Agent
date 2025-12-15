/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/backend/:path*",
        destination: `${backendUrl}/:path*`
      }
    ];
  }
};

module.exports = nextConfig;
