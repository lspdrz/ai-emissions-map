# Project Guide — AI Emissions Map website

**Keep this file at 500 words or fewer.** Structure and process only; decisions belong in code comments.

## What this is

A static Next.js (App Router) site: `next build` exports every page from two files the Python pipeline
writes and commits, `data/data.json` (contract `aem-data/1`) and `data/methodology.md`. No server, no
database, no scoring logic here: every number comes from `data.json`. Routes: `/` (overview), `/routes/`,
`/organizations/` and `/organizations/<slug>/`, `/methodology/`. Deployed on Vercel from `web/`.

## Feature structure

```
features/<name>/
├── lib/              feature logic, pure and unit-tested
└── ui/
    ├── index.tsx      entry point — the only thing app/ imports
    └── components/
```

- Code shared **across** features: root `features/{constants,components,utils}/`. A helper that only one
  component needs lives with that component (the log-scale geometry lives with `RangeBar`).
- Infrastructure every feature uses: `@/lib/` (`lib/data/` loads and checks `data.json`; `loadData` is
  `server-only`).
- `app/` is routing only: one-line pages, plus the shell in `app/_components/` and `app/_constants/`.

## Import rules

- Every import uses the `@/...` alias, never `./` or `../` (eslint-enforced, autofixable).
- A file in `features/<f>` may import its own feature, `@/lib` and the shared root folders, never another
  feature.

## Styling

Tailwind v4. The design tokens (colors from the agreed design, fonts) are in `app/globals.css` `@theme`;
use their utilities (`text-muted`, `bg-band-4`, `font-serif`). Carbon bands are colors; disclosure letters
are outlined neutral badges, never colored.

## Testing

Vitest (`npm test`): logic and components (`renderToStaticMarkup`), in `__tests__/` beside the code.
After `npm run build`, `npm run check` compares the exported pages with `data.json`.

## Data and drafts

While `meta.grid.mock` is true every page shows the draft bar and is `noindex`; never hard-code either.
