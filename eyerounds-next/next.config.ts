import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'eyerounds.org',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;