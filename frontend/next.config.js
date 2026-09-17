/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Left as the default (non-standalone) output so the same build works
  // both in the Docker image below and on Amplify Hosting's Next.js SSR
  // compute, which expects a normal `.next` build output.
};

module.exports = nextConfig;
