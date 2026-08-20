/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@diya/shared'],
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'maplibre-gl': 'maplibre-gl',
    };
    return config;
  },
};

module.exports = nextConfig;
