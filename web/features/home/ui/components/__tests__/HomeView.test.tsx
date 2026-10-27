import { readFileSync } from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { HomeView } from "@/features/home/ui/components/HomeView";
import { parseData } from "@/lib/data/parseData";

const fixture = () =>
  parseData(JSON.parse(readFileSync(path.join(process.cwd(), "lib/data/__tests__/fixtures/data.json"), "utf8")));

describe("HomeView", () => {
  it("never shows the release, draft flag or methodology version", () => {
    const data = fixture();
    const html = renderToStaticMarkup(<HomeView />);
    expect(html).not.toContain(data.meta.release_date);
    expect(html).not.toContain(data.meta.methodology_version);
    expect(html.toLowerCase()).not.toContain("draft");
  });
});
