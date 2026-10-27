import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { OrgCard } from "@/features/home/types";
import { OrganizationsSection } from "@/features/home/ui/components/OrganizationsSection";

function card(o: Partial<OrgCard> = {}): OrgCard {
  return { slug: "pub", name: "Public AI", type: "inference_host", letter: "C", mean: 1.5, routeCount: 4, spread: { A: 1, B: 1, C: 1, D: 1 }, ...o };
}

describe("OrganizationsSection", () => {
  it("is the #organizations section, headed Organizations, with the intro and search", () => {
    const html = renderToStaticMarkup(<OrganizationsSection organizations={[card()]} />);
    expect(html).toMatch(/<section[^>]*id="organizations"/);
    expect(html).toMatch(/<h2[^>]*>Organizations<\/h2>/);
    expect(html).toContain("Each organization’s location disclosure rating is the average of its routes’ ratings");
    expect(html).toMatch(/<label[^>]*for="org-search"[^>]*>Search organizations<\/label>/);
    expect(html).toContain('placeholder="Organization name"');
  });

  it("shows each card's name, type, letter, route count and spread", () => {
    const html = renderToStaticMarkup(<OrganizationsSection organizations={[card()]} />);
    expect(html).toMatch(/<h3[^>]*>Public AI<\/h3>/);
    expect(html).toContain(">Inference host<");
    expect(html).toMatch(/aria-label="Rating C"[^>]*>C</);
    expect(html).toMatch(/Routes<\/dt><dd[^>]*>4</);
    expect(html).toMatch(/Spread<\/dt><dd[^>]*>1×A {2}1×B {2}1×C {2}1×D</);
  });

  it("shows a dash for an organization with no rating", () => {
    const html = renderToStaticMarkup(<OrganizationsSection organizations={[card({ letter: null, mean: null })]} />);
    expect(html).toMatch(/aria-label="Not rated"[^>]*>–</);
  });

  it("says no organizations match, and shows none, for a search that finds none", () => {
    const html = renderToStaticMarkup(<OrganizationsSection organizations={[card()]} initialQuery="zzz" />);
    expect(html).toContain("No organizations match “zzz”");
    expect(html).not.toContain("<h3");
  });

  it("finds an organization by part of its name, in any case", () => {
    const html = renderToStaticMarkup(<OrganizationsSection organizations={[card(), card({ slug: "g", name: "Google" })]} initialQuery=" PUBLIC" />);
    expect(html).toContain(">Public AI<");
    expect(html).not.toContain(">Google<");
  });
});
