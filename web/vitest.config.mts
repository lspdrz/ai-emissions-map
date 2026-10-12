import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const alias = {
  "@": fileURLToPath(new URL(".", import.meta.url)),
  // Outside a Next.js build "server-only" resolves to its throwing variant; Vitest runs in plain
  // Node, so point it at the package's no-op file.
  "server-only": fileURLToPath(new URL("./node_modules/server-only/empty.js", import.meta.url)),
};

export default defineConfig({
  resolve: { alias },
  test: {
    name: "unit",
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["**/node_modules/**"],
  },
});
