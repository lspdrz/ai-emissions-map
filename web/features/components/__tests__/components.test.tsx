import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { BandChip } from "@/features/components/BandChip";
import { EstimateLabel } from "@/features/components/EstimateLabel";
import { LetterBadge } from "@/features/components/LetterBadge";
import { OrganizationCard } from "@/features/components/OrganizationCard";
import { RangeAxis, RangeBar } from "@/features/components/RangeBar";

describe("shared components", () => {
  it("LetterBadge shows the letter and names it for screen readers", () => {
    const html = renderToStaticMarkup(<LetterBadge letter="C" />);
    expect(html).toContain(">C<");
    expect(html).toContain('aria-label="Location disclosure C"');
    expect(html).toContain('role="img"'); // a label on a role-less span is not announced
  });
  it("BandChip colors a span by its higher band, and says when a route is not scored", () => {
    expect(renderToStaticMarkup(<BandChip band={[4, 5]} />)).toContain("bg-band-5");
    expect(renderToStaticMarkup(<BandChip band={null} />)).toContain("Not scored");
  });
  it("RangeBar places the range on the log scale", () => {
    const html = renderToStaticMarkup(<RangeBar range={{ low: 0.01, high: 30 }} upper={[0.03, 0.1, 0.3, 1]} />);
    expect(html).toContain("left:0%");
    expect(html).toContain("width:100%");
  });
  it("RangeBar keeps a narrow range at the top of the scale inside the bar", () => {
    const html = renderToStaticMarkup(<RangeBar range={{ low: 29.9, high: 30 }} upper={[0.03, 0.1, 0.3, 1]} />);
    const left = Number(html.match(/left:([\d.]+)%/)![1]);
    const width = Number(html.match(/width:([\d.]+)%/)![1]);
    expect(left + width).toBeLessThanOrEqual(100);
    const atTop = renderToStaticMarkup(<RangeBar range={{ low: 30, high: 30 }} upper={[0.03, 0.1, 0.3, 1]} />);
    expect(Number(atTop.match(/width:([\d.]+)%/)![1])).toBeGreaterThan(0); // still visible
  });
  it("RangeBar shades the five bands behind the bar with the theme tokens", () => {
    const html = renderToStaticMarkup(<RangeBar range={{ low: 1, high: 3 }} upper={[0.03, 0.1, 0.3, 1]} shaded />);
    expect(html).toContain("linear-gradient(90deg, var(--color-shade-1) 0%");
    expect(html).toContain("var(--color-shade-5)");
  });
  it("RangeAxis labels the log scale's ticks at their positions", () => {
    const html = renderToStaticMarkup(<RangeAxis />);
    expect(html).toContain(">0.01<");
    expect(html).toContain(">30<");
    expect(html).toContain("left:0%");
    expect(html).toContain("left:100%");
  });
  it("EstimateLabel names both models the score is estimated with", () => {
    expect(renderToStaticMarkup(<EstimateLabel gridName="placeholder grid data" />))
      .toContain("Estimate (EcoLogits × placeholder grid data)");
  });
  it("OrganizationCard links to the organization's page", () => {
    const org = { slug: "acme", display_name: "Acme", type: "cloud", country: null, homepage: "https://acme.example",
      description: "Says Switzerland.", notified: null, routes: [], evidence: [],
      rating: { letter: "C", mean: 2, spread: { C: 1 }, summary: "C (1 route at C)" } };
    const html = renderToStaticMarkup(<OrganizationCard org={org} />);
    expect(html).toMatch(/href="\/organizations\/acme\/?"/); // next/link drops the slash outside a Next build
    expect(html).toContain("C (1 route at C)");
  });
});
