import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MethodSection } from "@/features/home/ui/components/MethodSection";
import { METHODOLOGY_URL } from "@/lib/links";
import { buildMeta } from "@/lib/data/__tests__/builders";

describe("MethodSection", () => {
  it("is the #method section, headed Method, with Research, Carbon intensity and Location disclosure", () => {
    const html = renderToStaticMarkup(<MethodSection meta={buildMeta()} />);
    expect(html).toMatch(/<section[^>]*id="method"/);
    expect(html).toMatch(/<h2[^>]*>Method<\/h2>/);
    for (const h of ["Research", "Carbon intensity", "Location disclosure"]) expect(html).toMatch(new RegExp(`<h3[^>]*>${h}</h3>`));
    expect(html).toContain("(E × I) + M");
  });

  it("fills the EcoLogits version, PUE range and Ember year from meta", () => {
    const meta = buildMeta({ ecologits_version: "9.9.9", pue: [1.2, 1.7], grid: { source: "Ember", year: 2031 } });
    const html = renderToStaticMarkup(<MethodSection meta={meta} />);
    expect(html).toContain("EcoLogits 9.9.9");
    expect(html).toContain("PUE range of 1.2–1.7");
    expect(html).toContain("Ember’s 2031 life-cycle intensity");
  });

  it("shows a legend entry per band, with its range", () => {
    const html = renderToStaticMarkup(<MethodSection meta={buildMeta({ band_upper: [0.03, 0.1, 0.3, 1.0] })} />);
    for (const n of [1, 2, 3, 4, 5]) expect(html).toContain(`border-band-${n}`);
    expect(html).toContain("&lt; 0.03");
    expect(html).toContain("≥ 1");
  });

  it("lists the four ratings A to D", () => {
    const html = renderToStaticMarkup(<MethodSection meta={buildMeta()} />);
    expect(html).toMatch(/>A<\/dt><dd[^>]*>Names the facility</);
    expect(html).toMatch(/>B<\/dt><dd[^>]*>Names one grid</);
    expect(html).toMatch(/>C<\/dt><dd[^>]*>Names several possible grids</);
    expect(html).toMatch(/>D<\/dt><dd[^>]*>Undisclosed</);
  });

  it("links “here” to the full methodology, in a new tab", () => {
    const html = renderToStaticMarkup(<MethodSection meta={buildMeta()} />);
    expect(html).toMatch(new RegExp(`<a[^>]*href="${METHODOLOGY_URL}"[^>]*target="_blank"[^>]*>here</a>`));
  });
});
