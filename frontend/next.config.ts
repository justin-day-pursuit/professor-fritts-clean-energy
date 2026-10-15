/**
 * Next.js build and dev settings for the frontend app.
 * Turbopack CSS loading and prefetch options live here; npm scripts in package.json call next dev/build.
 * Adjust only when upgrading Next or changing how CSS or caching behaves.
 */
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
