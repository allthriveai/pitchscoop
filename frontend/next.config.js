/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*', // Proxy to backend
      },
      {
        source: '/mcp/:path*',
        destination: 'http://localhost:8000/mcp/:path*', // Proxy MCP tools
      },
    ]
  },
}

module.exports = nextConfig