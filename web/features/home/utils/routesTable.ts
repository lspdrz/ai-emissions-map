import type { Page, RouteRow, Sort, SortKey, TableAction, TableState } from "@/features/home/types";
import { midpoint } from "@/features/home/utils/routes";

export const DEFAULT_SORT: Sort = { key: "score", dir: 1 };
export const PER_PAGE = 10;

/** Scored routes by midpoint, cleanest first, always ahead of unscored ones. */
function byScore(a: RouteRow, b: RouteRow): number {
  if (!a.score || !b.score) return (a.score ? 0 : 1) - (b.score ? 0 : 1);
  return midpoint(a.score) - midpoint(b.score);
}

/**
 * The table's order. Flipping a column reverses what the column is about and nothing else:
 * - carbon: by midpoint (METHODOLOGY.md, Ranges); unscored routes stay last either way.
 * - disclosure: by letter; within a letter, cleanest first and unscored last, either way.
 * - organization: by organization, then model, then location; all of it reverses.
 * Ties keep the order given (Array.prototype.sort is stable).
 */
export function sortRows(rows: RouteRow[], { key, dir }: Sort): RouteRow[] {
  const compare = {
    score: (a: RouteRow, b: RouteRow) => (a.score && b.score ? dir * byScore(a, b) : byScore(a, b)),
    letter: (a: RouteRow, b: RouteRow) => dir * a.letter.localeCompare(b.letter) || byScore(a, b),
    org: (a: RouteRow, b: RouteRow) =>
      dir * (a.org.localeCompare(b.org) || a.model.localeCompare(b.model) || a.label.localeCompare(b.label)),
  }[key];
  return [...rows].sort(compare);
}

/** Clicking the active column flips it; clicking another starts it ascending. */
export function toggleSort(sort: Sort, key: SortKey): Sort {
  return key === sort.key ? { key, dir: sort.dir === 1 ? -1 : 1 } : { key, dir: 1 };
}

/** Case-insensitive substring search; surrounding spaces are ignored and an empty query matches everything. */
export function matchesQuery(text: string, query: string): boolean {
  const q = query.trim().toLowerCase();
  return !q || text.toLowerCase().includes(q);
}

/** Routes whose "organization model" matches the search. */
export function filterRows(rows: RouteRow[], query: string): RouteRow[] {
  return rows.filter((r) => matchesQuery(`${r.org} ${r.model}`, query));
}

/** One page of the list, the page number clamped to the pages there are. An empty list has one empty page. */
export function pageOf<T>(items: T[], page: number, per = PER_PAGE): Page<T> {
  const pageCount = Math.max(1, Math.ceil(items.length / per));
  const p = Math.min(Math.max(page, 0), pageCount - 1);
  const shown = items.slice(p * per, p * per + per);
  return {
    items: shown,
    page: p,
    pageCount,
    first: shown.length ? p * per + 1 : 0,
    last: shown.length ? p * per + shown.length : 0,
  };
}

/** The line under the table: "1–10 of 23 routes", or why there are none. */
export function pageLabel(total: number, first: number, last: number, query: string): string {
  if (total > 0) return `${first}–${last} of ${total} ${total === 1 ? "route" : "routes"}`;
  return query.trim() ? `No routes match “${query.trim()}”` : "No routes in this release yet";
}

/** A new search or sort goes back to page 1, so the reader never lands on an empty page. */
export function tableReducer(state: TableState, action: TableAction): TableState {
  switch (action.type) {
    case "query":
      return { ...state, query: action.query, page: 0 };
    case "sort":
      return { ...state, sort: toggleSort(state.sort, action.key), page: 0 };
    case "page":
      return { ...state, page: action.page };
  }
}
