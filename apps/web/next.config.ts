import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export → SPA in out/ for Azure Static Web Apps (Phase 5). No server features.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
