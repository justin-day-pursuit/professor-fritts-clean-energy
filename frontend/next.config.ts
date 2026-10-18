/**
 * Next.js build and dev settings for the frontend app.
 * Turbopack CSS loading and prefetch options live here; npm scripts in package.json call next dev/build.
 * Adjust only when upgrading Next or changing how CSS or caching behaves.
 */
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The design page used to live at /plan-mockup. Old links still work and land on the home page.
  async redirects() {
    return [{ source: "/plan-mockup", destination: "/", permanent: false }];
  },
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
