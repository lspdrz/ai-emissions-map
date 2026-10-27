import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ContributeSection } from "@/features/home/ui/components/ContributeSection";
import { CONTRIBUTING_URL, REPO_URL } from "@/lib/links";

describe("ContributeSection", () => {
  it("is the #contribute section, headed Contribute", () => {
    const html = renderToStaticMarkup(<ContributeSection />);
    expect(html).toMatch(/<section[^>]*id="contribute"/);
    expect(html).toMatch(/<h2[^>]*>Contribute<\/h2>/);
    expect(html).toContain("Organizations, routes, grids and models are added by pull request.");
  });

  it("links “here” to CONTRIBUTING.md, in a new tab", () => {
    const html = renderToStaticMarkup(<ContributeSection />);
    expect(html).toMatch(new RegExp(`<a[^>]*href="${CONTRIBUTING_URL}"[^>]*target="_blank"[^>]*>here</a>`));
  });

  it("links the button to the repository, in a new tab", () => {
    const html = renderToStaticMarkup(<ContributeSection />);
    expect(html).toMatch(new RegExp(`<a[^>]*href="${REPO_URL}"[^>]*target="_blank"[^>]*>Open the repository ↗</a>`));
  });
});
