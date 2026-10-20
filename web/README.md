# The AI Emissions Map website

A static Next.js site. Every number comes from `data/data.json`, which the Python pipeline writes; the
website holds no scoring logic. Structure and rules: `.claude/PROJECT.md`.

## Update the data

From the repository root:

```bash
uv run python -m build score
uv run python -m build release
```

This writes `web/data/data.json` when anything it shows or depends on changed; commit it. It holds only what the website displays.
While the release is a draft (`meta.draft`), every page is `noindex`.

## Develop

```bash
cd web
npm install
npm run dev        # http://localhost:3000
npm run lint
npm test
npm run build      # static export to out/
```

## Deploy (Vercel)

Vercel builds from git. Project settings:

- **Root Directory:** `web`; framework Next.js (detected).
- **Builds:** every push deploys; there is no Ignored Build Step.
- **While it is a draft:** keep Vercel Authentication on, share it with one Shareable Link, and attach no
  custom domain (a custom production domain is not protected below the Pro plan's "All Deployments" scope).
