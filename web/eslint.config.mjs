import { readdirSync } from "node:fs";
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import noRelativeImportPaths from "eslint-plugin-no-relative-import-paths";

/**
 * Project structure (the eu-trade-explorer layout)
 *
 *   app/         Routing only: one-line pages that render a feature's ui/index.tsx.
 *   features/    One folder per capability:
 *     <feature>/
 *       ui/        React. index.tsx is the entry point and the only thing app/ imports.
 *       lib/       The feature's services: what it reads from data.json, through @/lib/data.
 *       utils/     The feature's pure helpers (formatting, sorting), no data access.
 *   features/{constants,components,utils}/  shared across features.
 *   lib/         Infrastructure every feature uses: the data loader (lib/data/).
 *
 * Import direction: app → features/<f>/ui → features/<f>/lib → @/lib
 * Features never import each other. Every import uses the `@/` alias.
 */

const NO_UI = { group: ["**/ui/**"], message: "lib/ and utils/ must not import from ui/." };

// Root-level folders under features/ that are shared, not features.
const SHARED_ROOT_DIRS = ["constants", "components", "hooks", "utils"];
const FEATURE_DIRS = readdirSync("features", { withFileTypes: true })
  .filter((d) => d.isDirectory() && !SHARED_ROOT_DIRS.includes(d.name))
  .map((d) => d.name);

const FEATURE_ISOLATION = {
  rules: {
    "import/no-restricted-paths": [
      "error",
      {
        zones: FEATURE_DIRS.map((f) => ({
          target: `./features/${f}`,
          from: "./features",
          except: [`./${f}`, ...SHARED_ROOT_DIRS.map((d) => `./${d}`)],
          message: "Features are independent: no cross-feature imports. Promote shared code to a root features/ folder.",
        })),
      },
    ],
  },
};

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),

  // Every import uses the `@/` alias: no relative paths.
  {
    plugins: { "no-relative-import-paths": noRelativeImportPaths },
    rules: {
      "no-relative-import-paths/no-relative-import-paths": ["error", { allowSameFolder: false, prefix: "@" }],
    },
  },

  // Only once a feature exists: ESLint rejects the rule with no zones.
  ...(FEATURE_DIRS.length ? [{ files: ["features/**"], ...FEATURE_ISOLATION }] : []),

  // Fonts are self-hosted with next/font/local: Turbopack's next/font/google loader fails whenever Google
  // Fonts answers with `/l/font?kit=…&v=…` URLs (vercel/next.js#99114), which broke the first Vercel build.
  {
    rules: {
      "no-restricted-imports": ["error", { paths: [{ name: "next/font/google",
        message: "Self-host fonts with next/font/local (app/fonts/); next/font/google breaks Turbopack builds." }] }],
    },
  },

  // app/ is routing only: it may import a feature's ui/ entry point, @/lib and the app shell, never a
  // feature's internals or the shared features/ folders. (Repeats the font ban: the last
  // no-restricted-imports that matches a file replaces earlier ones.)
  {
    files: ["app/**"],
    rules: {
      "no-restricted-imports": ["error", {
        paths: [{ name: "next/font/google",
          message: "Self-host fonts with next/font/local (app/fonts/); next/font/google breaks Turbopack builds." }],
        patterns: [{ regex: "^@/features/(?![a-z0-9-]+/ui$)",
          message: "app/ imports only a feature's ui/ entry point (@/features/<name>/ui)." }],
      }],
    },
  },

  {
    files: ["features/**/lib/**", "features/**/utils/**", "lib/**"],
    rules: { "no-restricted-imports": ["error", { patterns: [NO_UI] }] },
  },
]);

export default eslintConfig;
