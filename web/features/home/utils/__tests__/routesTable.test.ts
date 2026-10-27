import { describe, expect, it } from "vitest";
import type { RouteRow } from "@/features/home/types";
import {
  DEFAULT_SORT, filterRows, matchesQuery, pageLabel, pageOf, sortRows, tableReducer, toggleSort,
} from "@/features/home/utils/routesTable";

function row(slug: string, o: Partial<RouteRow> = {}): RouteRow {
  return { slug, org: "Acme", model: "M", label: "Somewhere", letter: "C", score: { low: 0.1, high: 0.2 }, ...o };
}
const slugs = (rows: RouteRow[]) => rows.map((r) => r.slug);

describe("sortRows by carbon", () => {
  // Low ends say a < b; geometric midpoints (0.0447 vs 0.04) say b < a.
  const a = row("a", { score: { low: 0.01, high: 0.2 } });
  const b = row("b", { score: { low: 0.02, high: 0.08 } });
  const none = row("none", { score: null });

  it("orders by midpoint, not by the low end, with unscored routes last", () => {
    expect(slugs(sortRows([none, a, b], { key: "score", dir: 1 }))).toEqual(["b", "a", "none"]);
  });

  it("keeps unscored routes last when flipped", () => {
    expect(slugs(sortRows([none, a, b], { key: "score", dir: -1 }))).toEqual(["a", "b", "none"]);
  });
});

describe("sortRows by disclosure", () => {
  const rows = [
    row("d", { letter: "D", score: null }),
    row("c-dirty", { letter: "C", score: { low: 1, high: 2 } }),
    row("c-none", { letter: "C", score: null }),
    row("c-clean", { letter: "C", score: { low: 0.01, high: 0.02 } }),
    row("a", { letter: "A" }),
  ];

  it("orders A to D, cleanest first within a letter, unscored last within it", () => {
    expect(slugs(sortRows(rows, { key: "letter", dir: 1 }))).toEqual(["a", "c-clean", "c-dirty", "c-none", "d"]);
  });

  it("flips the letters only", () => {
    expect(slugs(sortRows(rows, { key: "letter", dir: -1 }))).toEqual(["d", "c-clean", "c-dirty", "c-none", "a"]);
  });
});

describe("sortRows by organization", () => {
  const rows = [
    row("b-m", { org: "Beta", model: "M" }),
    row("a-n", { org: "Alpha", model: "N" }),
    row("a-m-2", { org: "Alpha", model: "M", label: "Zone 2" }),
    row("a-m-1", { org: "Alpha", model: "M", label: "Zone 1" }),
  ];

  it("orders by organization, then model, then location", () => {
    expect(slugs(sortRows(rows, { key: "org", dir: 1 }))).toEqual(["a-m-1", "a-m-2", "a-n", "b-m"]);
  });

  it("flips the whole order", () => {
    expect(slugs(sortRows(rows, { key: "org", dir: -1 }))).toEqual(["b-m", "a-n", "a-m-2", "a-m-1"]);
  });
});

describe("toggleSort", () => {
  it("starts on carbon, lowest first", () => {
    expect(DEFAULT_SORT).toEqual({ key: "score", dir: 1 });
  });

  it("flips the direction of the active column", () => {
    expect(toggleSort({ key: "score", dir: 1 }, "score")).toEqual({ key: "score", dir: -1 });
  });

  it("starts a new column ascending", () => {
    expect(toggleSort({ key: "score", dir: -1 }, "org")).toEqual({ key: "org", dir: 1 });
  });
});

describe("search", () => {
  it("matches a substring regardless of case and surrounding spaces", () => {
    expect(matchesQuery("Anthropic Claude Opus 5.5", "  anthropic CLAUDE ")).toBe(true);
    expect(matchesQuery("Anthropic Claude Opus 5.5", "gemini")).toBe(false);
  });

  it("matches everything with an empty query", () => {
    expect(matchesQuery("Anything", "   ")).toBe(true);
  });

  it("filters routes on organization and model, not location", () => {
    const rows = [row("x", { org: "Scaleway", model: "gpt-oss-120b", label: "Paris" }), row("y", { org: "Google" })];
    expect(slugs(filterRows(rows, "scaleway gpt"))).toEqual(["x"]);
    expect(filterRows(rows, "paris")).toEqual([]);
  });
});

describe("pageOf", () => {
  const items = Array.from({ length: 23 }, (_, i) => i);

  it("cuts pages of ten and counts from 1", () => {
    expect(pageOf(items, 1)).toMatchObject({ items: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19], page: 1, pageCount: 3, first: 11, last: 20 });
  });

  it("clamps a page past the end to the last page", () => {
    expect(pageOf(items, 5)).toMatchObject({ page: 2, first: 21, last: 23 });
  });

  it("has one empty page with nothing in it", () => {
    expect(pageOf([], 3)).toEqual({ items: [], page: 0, pageCount: 1, first: 0, last: 0 });
  });
});

describe("pageLabel", () => {
  it("states the rows shown and the total", () => {
    expect(pageLabel(23, 1, 10, "")).toBe("1–10 of 23 routes");
    expect(pageLabel(1, 1, 1, "")).toBe("1–1 of 1 route");
  });

  it("says no routes match a search that finds none", () => {
    expect(pageLabel(0, 0, 0, "zzz")).toBe("No routes match “zzz”");
  });

  it("says there are no routes when there is no search", () => {
    expect(pageLabel(0, 0, 0, " ")).toBe("No routes in this release yet");
  });
});

describe("tableReducer", () => {
  const start = { query: "", sort: DEFAULT_SORT, page: 2 };

  it("returns to page 1 on a new search", () => {
    expect(tableReducer(start, { type: "query", query: "goo" })).toEqual({ query: "goo", sort: DEFAULT_SORT, page: 0 });
  });

  it("returns to page 1 on a new sort", () => {
    expect(tableReducer(start, { type: "sort", key: "org" })).toEqual({ query: "", sort: { key: "org", dir: 1 }, page: 0 });
  });

  it("goes to a page", () => {
    expect(tableReducer(start, { type: "page", page: 0 }).page).toBe(0);
  });
});
