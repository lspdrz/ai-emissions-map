# Project Guide — AI Emissions Map website

**Keep this file at 500 words or fewer.** Structure and process only; decisions belong in code comments.

## What this is

A static Next.js (App Router) site: `next build` exports every page from `data/data.json` (contract
`aem-data/1`), which the Python pipeline writes and commits. No server, no database, no scoring logic here:
every number comes from `data.json`. Routes: `/` (overview). Deployed on Vercel from `web/`.

The site is being redesigned from scratch: it holds the data loading and one plain page, nothing more.
What the site must show is set by `docs/METHODOLOGY.md` at the repository root: its Presentation section, the
midpoint sort key (Ranges), the served model beside the offered name (Where a route runs) and the versions each
release states (Versions). Read them before designing a page.

## Feature structure

```
features/<name>/
├── lib/              feature services: what the feature reads from data.json (via @/lib/data), unit-tested
├── utils/            the feature's pure helpers (formatting, sorting), unit-tested
└── ui/
    ├── index.tsx      entry point — the only thing app/ imports
    └── components/
```

- Code shared **across** features: root `features/{constants,components,utils}/`, created when a second
  feature needs it. A helper that only one component needs lives with that component.
- Infrastructure every feature uses: `@/lib/` (`lib/data/` loads and checks `data.json`; `loadData` is
  `server-only`).
- `app/` is routing only: one-line pages and the root layout.

## Import rules

- Every import uses the `@/...` alias, never `./` or `../` (eslint-enforced, autofixable).
- A file in `features/<f>` may import its own feature, `@/lib` and the shared root folders, never another
  feature.

## Styling

Tailwind v4, imported in `app/globals.css`. No design tokens yet: they come with the new design.

## Testing

Vitest (`npm test`): logic and components (`renderToStaticMarkup`), in `__tests__/` beside the code.

## Data and drafts

While `meta.draft` is true every page is `noindex` (the root layout's metadata); never hard-code it.
