# The AI Emissions Map website

A static Next.js site. Every number comes from `data/data.json`, which the Python pipeline writes; the
website holds no scoring logic. Structure and rules: `.claude/PROJECT.md`.

## Update the data

From the repository root:

```bash
uv run python -m build.export --release-date <YYYY-MM-DD> [--grid <grid CSV>]
```

This writes `web/data/data.json` and `web/data/methodology.md`; commit both. They hold only what the
website displays (ruling R-2026-10-12-b). While the grid data is a mock, the file says so and every page
shows the draft bar.

## Develop

```bash
cd web
npm install
npm run dev        # http://localhost:3000
npm run lint
npm test
npm run build      # static export to out/
npm run check      # the exported pages agree with data.json
```

## Deploy (Vercel)

Vercel builds from git. Project settings:

- **Root Directory:** `web`; framework Next.js (detected).
- **Ignored Build Step:** set in `vercel.json` (`scripts/ignore-build.sh`): a push deploys only if
  something under `web/` changed since the last deployment.
- **While it is a draft:** keep Vercel Authentication on, share it with one Shareable Link, and attach no
  custom domain (a custom production domain is not protected below the Pro plan's "All Deployments" scope).
