/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  images: {
    domains: [
      // imgur
      "i.imgur.com",
      // instagram, through TBA
      "www.thebluealliance.com",
    ],
  },
  env: {
    PROD: process.env.PROD || "True",
  },
};

module.exports = nextConfig;
