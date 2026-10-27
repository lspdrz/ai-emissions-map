import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Footer } from "@/app/_components/Footer";
import { buildMeta } from "@/lib/data/__tests__/builders";

describe("Footer", () => {
  it("credits the grid data and EcoLogits from meta", () => {
    const meta = buildMeta({ grid: { source: "Ember", year: 2031 }, ecologits_version: "9.9.9" });
    expect(renderToStaticMarkup(<Footer meta={meta} />)).toContain("Ember 2031 (CC-BY-4.0) · EcoLogits 9.9.9");
  });

  it("dates the licence by the release year", () => {
    expect(renderToStaticMarkup(<Footer meta={buildMeta({ release_date: "2027-01-05" })} />)).toContain("MIT License · 2027");
  });

  it("never shows the release date, draft flag or methodology version", () => {
    const meta = buildMeta({ release_date: "2027-01-05", methodology_version: "4.5.6", draft: true });
    const html = renderToStaticMarkup(<Footer meta={meta} />);
    expect(html).not.toContain("2027-01-05");
    expect(html).not.toContain("4.5.6");
    expect(html.toLowerCase()).not.toContain("draft");
  });
});
