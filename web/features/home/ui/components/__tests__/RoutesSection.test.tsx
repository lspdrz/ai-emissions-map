import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { RouteRow } from "@/features/home/types";
import { RoutesSection } from "@/features/home/ui/components/RoutesSection";

const upper = [0.03, 0.1, 0.3, 1.0];

function row(i: number, o: Partial<RouteRow> = {}): RouteRow {
  return { slug: `r${i}`, org: `Org ${i}`, model: `Model ${i}`, label: `Place ${i}`, letter: "C", score: { low: i / 100, high: i / 50 }, ...o };
}
function render(routes: RouteRow[], initialQuery?: string) {
  return renderToStaticMarkup(<RoutesSection routes={routes} bandUpper={upper} initialQuery={initialQuery} />);
}

describe("RoutesSection", () => {
  it("is the #routes section, headed Routes, with the intro", () => {
    const html = render([row(1)]);
    expect(html).toMatch(/<section[^>]*id="routes"/);
    expect(html).toMatch(/<h2[^>]*>Routes<\/h2>/);
    expect(html).toContain("A route is an organization deploying a model at a location.");
  });

  it("shows the first 10 routes, cleanest first, with the page label", () => {
    const routes = Array.from({ length: 23 }, (_, i) => row(23 - i));
    const html = render(routes);
    expect(html).toContain("1–10 of 23 routes");
    expect(html).toContain("Org 1 · Model 1");
    expect(html).toContain("Org 10 · Model 10");
    expect(html).not.toContain("Org 11 · Model 11");
    expect(html.indexOf("Org 1 · Model 1")).toBeLessThan(html.indexOf("Org 2 · Model 2"));
  });

  it("names each sort button by its visible text, with no label hiding it", () => {
    const html = render([row(1)]);
    expect(html).not.toMatch(/<button[^>]*aria-label="Sort/);
    expect(html).toMatch(/<button[^>]*><span>Organization · model/);
    expect(html).toMatch(/<label[^>]*for="route-search"[^>]*>Search routes<\/label>/);
    expect(html).toContain('placeholder="Organization or model"');
  });

  it("shows ↑ on the active column and ↕ on the others, hidden from screen readers", () => {
    const html = render([row(1)]);
    expect(html).toContain('<span aria-hidden="true"> ↑</span>');
    expect(html).toContain('<span aria-hidden="true"> ↕</span>');
  });

  it("tells screen readers which column is sorted, and which way", () => {
    const html = render([row(1)]);
    expect(html.match(/<span class="sr-only">, sorted ascending<\/span>/g)).toHaveLength(2); // the phone and desktop carbon headers
    expect(html).not.toContain("sorted descending");
  });

  it("says no routes match, and shows none, for a search that finds none", () => {
    const html = render([row(1)], "zzz");
    expect(html).toContain("No routes match “zzz”");
    expect(html).not.toContain("Org 1 · Model 1");
  });

  it("shows the location under the organization and model, and the letter", () => {
    const html = render([row(1, { label: "OPCORE DC5, Paris", letter: "A" })]);
    expect(html).toContain("OPCORE DC5, Paris");
    expect(html).toMatch(/>A<\/span>/);
  });

  it("renders every row as not scored when nothing is scored", () => {
    const html = render([row(1, { score: null, letter: "D" })]);
    expect(html).toContain("Not scored · location undisclosed");
  });
});
