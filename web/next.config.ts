import type { NextConfig } from "next";

// A static export: every page is generated at `next build` from data/data.json, which
// `uv run python -m build` writes. No server, no database.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
};

export default nextConfig;
