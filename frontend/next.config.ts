import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit .next/standalone: a self-contained server plus only the node_modules
  // files the app actually traces to. The Docker runtime stage copies that
  // instead of installing dependencies, which keeps the image small and means
  // the container never runs an install at start-up.
  output: "standalone",

  // Without this, tracing walks up to the repository root (there is a
  // package.json there) and nests the output under .next/standalone/frontend,
  // while a Docker build whose context is only this directory emits it flat.
  // Pinning the root keeps the layout identical in both places.
  outputFileTracingRoot: path.resolve(import.meta.dirname),
};

export default nextConfig;
