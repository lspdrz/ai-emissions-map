import { readFileSync } from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { RoutesTable } from "@/features/overview/ui/components/RoutesTable";
import { parseData } from "@/lib/data/parseData";
import type { MapData } from "@/lib/data/types";

const fixture = () =>
  parseData(JSON.parse(readFileSync(path.join(process.cwd(), "lib/data/__tests__/fixtures/data.json"), "utf8")));

const render = (data: MapData) =>
  renderToStaticMarkup(<RoutesTable routes={data.routes} models={data.models} organizations={data.organizations} />);

describe("RoutesTable", () => {
  it("shows each route's carbon intensity with its band and parts", () => {
    const html = render(fixture());
    expect(html).toContain("0.075–0.084 g");
    expect(html).toContain("Band 2");
    expect(html).toContain("operational 0.018–0.027 + embodied 0.057");
  });

  it("names the organization and the model, not their slugs", () => {
    const html = render(fixture());
    expect(html).toContain("Acme");
    expect(html).toContain(">M<");
  });

  it("gives each route's disclosure gap as the letter's tooltip", () => {
    expect(render(fixture())).toMatch(/title="The grid is disclosed, not the facility\."[^>]*>B</);
  });

  it("shows the offered name beside the served model", () => {
    const data = fixture();
    data.routes[0].served_as = "vendor/M-Instruct";
    expect(render(data)).toContain("offered as vendor/M-Instruct");
  });

  it("says not calculated, with no band, when a route has no carbon intensity", () => {
    const data = fixture();
    data.routes[0] = { ...data.routes[0], sci: null, band: null };
    const html = render(data);
    expect(html).toContain("not calculated");
    expect(html).not.toContain("Band ");
  });
});
