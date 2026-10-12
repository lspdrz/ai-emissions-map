import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { DraftBar } from "@/app/_components/DraftBar";

describe("DraftBar", () => {
  it("says the grid data is a placeholder and not for distribution", () => {
    const html = renderToStaticMarkup(<DraftBar />);
    expect(html).toContain("PLACEHOLDER GRID DATA");
    expect(html).toContain("Not for distribution");
  });
});
