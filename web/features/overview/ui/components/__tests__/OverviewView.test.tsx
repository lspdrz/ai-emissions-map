import { readFileSync } from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { OverviewView } from "@/features/overview/ui/components/OverviewView";
import { parseData } from "@/lib/data/parseData";

const fixture = () =>
  parseData(JSON.parse(readFileSync(path.join(process.cwd(), "lib/data/__tests__/fixtures/data.json"), "utf8")));

describe("OverviewView", () => {
  it("states the versions behind the release", () => {
    const html = renderToStaticMarkup(<OverviewView data={fixture()} />);
    expect(html).toContain("methodology 0.1.0");
    expect(html).toContain("grid data 2025");
    expect(html).toContain("EcoLogits 0.11.2");
  });

  it("puts organizations first, collapsed, and routes below, open", () => {
    const html = renderToStaticMarkup(<OverviewView data={fixture()} />);
    const sections = [...html.matchAll(/<details([^>]*)>\s*<summary[^>]*>[\s\S]*?(Organizations|Routes)/g)];
    expect(sections.map((m) => m[2])).toEqual(["Organizations", "Routes"]);
    expect(sections.map((m) => /\sopen/.test(m[1]))).toEqual([false, true]);
  });

  it("counts the organizations and routes in each section's heading", () => {
    const html = renderToStaticMarkup(<OverviewView data={fixture()} />);
    expect(html).toMatch(/Organizations <span[^>]*>\(1\)/);
    expect(html).toMatch(/Routes <span[^>]*>\(1\)/);
  });

  it("says so when the release has no routes", () => {
    const data = { ...fixture(), routes: [], organizations: [] };
    const html = renderToStaticMarkup(<OverviewView data={data} />);
    expect(html).toContain("No routes in this release yet.");
    expect(html).not.toContain("<details");
  });
});
