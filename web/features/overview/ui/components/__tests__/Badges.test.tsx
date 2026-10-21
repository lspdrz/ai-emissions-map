import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { BandBadge, LetterBadge } from "@/features/overview/ui/components/Badges";

describe("BandBadge", () => {
  it("shows one band", () => {
    expect(renderToStaticMarkup(<BandBadge band={[2, 2]} />)).toContain("Band 2");
  });

  it("shows the span when a range crosses bands", () => {
    expect(renderToStaticMarkup(<BandBadge band={[1, 4]} />)).toContain("Band 1–4");
  });
});

describe("LetterBadge", () => {
  it("shows its hint as a tooltip", () => {
    const html = renderToStaticMarkup(<LetterBadge letter="B" hint="The grid is disclosed, not the facility." />);
    expect(html).toContain('title="The grid is disclosed, not the facility."');
    expect(html).toContain(">B<");
  });

  it("has no tooltip without a hint", () => {
    expect(renderToStaticMarkup(<LetterBadge letter="A" hint={null} />)).not.toContain("title=");
  });

  it("shows a dash when there is no letter", () => {
    expect(renderToStaticMarkup(<LetterBadge letter={null} />)).toContain(">–<");
  });
});
