import { describe, expect, it } from "vitest";
import { getHomeData } from "@/features/home/lib/getHomeData";
import { buildData, buildModel, buildOrganization, buildRoute } from "@/lib/data/__tests__/builders";

describe("getHomeData", () => {
  it("gives each route its organization and model names, location, letter and score", () => {
    const data = buildData({
      routes: [buildRoute({ slug: "acme-m", org: "acme", model: "m", label: "Paris", letter: "A", score: { low: 0.04, high: 0.05 } })],
      organizations: [buildOrganization({ slug: "acme", display_name: "Acme Cloud" })],
      models: [buildModel({ slug: "m", display_name: "Model M" })],
    });
    expect(getHomeData(data).routes).toEqual([
      { slug: "acme-m", org: "Acme Cloud", model: "Model M", label: "Paris", letter: "A", score: { low: 0.04, high: 0.05 } },
    ]);
  });

  it("keeps an unscored route, with no score", () => {
    const data = buildData({ routes: [buildRoute({ letter: "D", score: null })] });
    expect(getHomeData(data).routes[0]).toMatchObject({ letter: "D", score: null });
  });

  it("names a model with no record by its slug", () => {
    const data = buildData({ routes: [buildRoute({ model: "mystery-7b" })] });
    expect(getHomeData(data).routes[0].model).toBe("mystery-7b");
  });

  it("passes meta through", () => {
    const data = buildData({ meta: { ecologits_version: "9.9.9" } });
    expect(getHomeData(data).meta.ecologits_version).toBe("9.9.9");
  });
});
