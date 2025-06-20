/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          }
        ]
      }
    ];
  },

  // Environment variables for client
  env: {
    DASHBOARD_AUTH_ENABLED: process.env.DASHBOARD_AUTH_ENABLED || 'true',
    JANE_IP: process.env.JANE_IP || '192.168.1.17',
    MOTOKO_IP: process.env.MOTOKO_IP || '192.168.1.12'
  },

  // Redirect root to dashboard
  async redirects() {
    return [
      {
        source: '/',
        destination: '/dashboard',
        permanent: false
      }
    ];
  }
};

module.exports = nextConfig;
