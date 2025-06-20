/** @type {import('next').NextConfig} */
const { PHASE_DEVELOPMENT_SERVER, PHASE_TEST } = require('next/constants');

const dev = process.env.BUILD_TYPE === 'dev' ? 'dev-' : '';

const OPEN_CORS_HEADERS = [
  {
    key: 'Access-Control-Allow-Origin',
    value: '*',
  },
  {
    key: 'Access-Control-Allow-Methods',
    value: 'GET, POST, PUT, DELETE, OPTIONS',
  },
  {
    key: 'Access-Control-Allow-Headers',
    value: 'Content-Type, Authorization, Origin',
  },
];

module.exports = (phase, { defaultConfig }) => {
  const isDev  = phase === PHASE_DEVELOPMENT_SERVER;
  const isTest = phase === PHASE_TEST || 'CI' in process.env;

  return {
    // Only use the real CDN in production; in dev/test load from localhost
    assetPrefix: isDev || isTest
      ? undefined
      : `https://${dev}cdn.commanderspellbook.com`,

    reactStrictMode: true,
    trailingSlash: true,
    productionBrowserSourceMaps: true,

    // Expose these env vars to the browser
    env: {
      NEXT_PUBLIC_EDITOR_BACKEND_URL: isDev
        ? 'http://backend:8000'
        : process.env.NEXT_PUBLIC_EDITOR_BACKEND_URL,
      NEXT_PUBLIC_LLM_SERVER_URL: isDev
        ? 'http://localhost:8000'
        : process.env.NEXT_PUBLIC_LLM_SERVER_URL,
    },

    images: {
      unoptimized: true,
    },

    serverRuntimeConfig: {
      PROJECT_ROOT: __dirname,
    },

    webpack(webpackConfig) {
      return {
        ...webpackConfig,
        optimization: {
          minimize: false, // prevent minification issues
        },
      };
    },

    async headers() {
      return [
        {
          source: '/embed.js',
          headers: OPEN_CORS_HEADERS,
        },
      ];
    },

    sassOptions: {
      silenceDeprecations: ['legacy-js-api'],
    },

    async redirects() {
      return [
        {
          source: '/ads.txt',
          destination: 'https://adstxt.mediavine.com/sites/commander-spellbook/ads.txt',
          permanent: false,
        },
        {
          source: '/how-to-submit-a-combo',
          destination: '/submit-a-combo',
          permanent: true,
        },
      ];
    },
  };
};
