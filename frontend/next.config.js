/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
    ],
  },
  // 开发环境代理配置
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
  // 环境变量
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: 'SciAgent',
  },
  // 输出配置
  output: 'standalone',
  // 忽略 TypeScript 错误（开发环境）
  typescript: {
    ignoreBuildErrors: process.env.NODE_ENV === 'development',
  },
};

module.exports = nextConfig;