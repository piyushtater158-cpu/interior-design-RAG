/** @type {import('next').NextConfig} */
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const backendHost = new URL(backendUrl).hostname;

module.exports = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: 'http',  hostname: backendHost },
      { protocol: 'https', hostname: backendHost },
      { protocol: 'https', hostname: '*.supabase.co' },
    ],
  },
};
