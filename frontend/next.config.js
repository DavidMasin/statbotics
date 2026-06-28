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
    PROD: process.env.PROD || "false",
    BACKEND_URL: process.env.BACKEND_URL || "",
    BUCKET_URL: process.env.BUCKET_URL || "",
    USE_BUCKET: process.env.USE_BUCKET || "",
  },
};

module.exports = nextConfig;
