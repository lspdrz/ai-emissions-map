import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { selectFeaturedRoutes } from "@/features/overview/lib/selectFeaturedRoutes";
import { parseData } from "@/lib/data/parseData";

const data = () => parseData(JSON.parse(readFileSync(new URL("../../../../lib/data/__tests__/fixtures/data.json", import.meta.url), "utf8")));

describe("selectFeaturedRoutes", () => {
  it("needs at least two scored routes for the featured model", () => {
    expect(selectFeaturedRoutes(data())).toBeNull();
  });
  it("returns the featured model's scored routes, lowest estimate first", () => {
    const d = data();
    d.routes.push({ ...d.routes[0], slug: "acme-m-2", score: { low: 0.01, high: 0.02 } });
    const featured = selectFeaturedRoutes(d)!;
    expect(featured.model.slug).toBe("m");
    expect(featured.routes.map((r) => r.slug)).toEqual(["acme-m-2", "acme-m"]);
  });
});
