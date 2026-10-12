import { describe, expect, it } from "vitest";
import { fullMethodology, renderMarkdown } from "@/features/methodology/lib/renderMethodology";

describe("methodology", () => {
  it("takes the full methodology section without its heading", () => {
    const md = "## Summary\nShort.\n\n## Full methodology\n\nThe body.\n\n### Part\nMore.";
    expect(fullMethodology(md)).toBe("The body.\n\n### Part\nMore.");
  });
  it("fails loudly when the section is missing", () => {
    expect(() => fullMethodology("## Summary\nOnly.")).toThrow(/Full methodology/);
  });
  it("renders markdown, including tables", async () => {
    const html = await renderMarkdown("**SCI**\n\n| a | b |\n|---|---|\n| 1 | 2 |");
    expect(html).toContain("<strong>SCI</strong>");
    expect(html).toContain("<table>");
  });
});
