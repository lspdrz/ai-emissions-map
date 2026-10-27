import { describe, expect, it } from "vitest";
import { getHomeData } from "@/features/home/lib/getHomeData";
import { buildData, buildModel, buildOrganization, buildRoute } from "@/lib/data/__tests__/builders";

describe("getHomeData", () => {
  it("gives each route its organization and model names, location, letter and score", () => {
    const data = buildData({
      routes: [buildRoute({ slug: "acme-m", org: "acme", model: "m", label: "Paris", letter: "A", sci: { low: 0.04, high: 0.05 } })],
      organizations: [buildOrganization({ slug: "acme", display_name: "Acme Cloud" })],
      models: [buildModel({ slug: "m", display_name: "Model M" })],
    });
    expect(getHomeData(data).routes).toEqual([
      { slug: "acme-m", org: "Acme Cloud", model: "Model M", label: "Paris", letter: "A", score: { low: 0.04, high: 0.05 } },
    ]);
  });

  it("keeps an unscored route, with no score", () => {
    const data = buildData({ routes: [buildRoute({ letter: "D", sci: null })] });
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

describe("getHomeData organizations", () => {
  it("gives each card its name, type, rating, route count and spread", () => {
    const data = buildData({
      organizations: [buildOrganization({
        slug: "pub", display_name: "Public AI", type: "inference_host", routes: [],
        rating: { letter: "C", mean: 1.5, spread: { A: 1, D: 1 }, summary: "" },
      })],
    });
    expect(getHomeData(data).organizations).toEqual([
      { slug: "pub", name: "Public AI", type: "inference_host", letter: "C", mean: 1.5, routeCount: 0, spread: { A: 1, D: 1 } },
    ]);
  });

  it("orders cards by mean, best first, then by name, with unrated organizations last", () => {
    const org = (display_name: string, mean: number | null) =>
      buildOrganization({ slug: display_name, display_name, rating: { letter: null, mean, spread: {}, summary: "" } });
    const data = buildData({
      organizations: [org("Empty", null), org("Google", 1), org("Public AI", 1.5), org("DeepSeek", 1), org("Scaleway", 3)],
    });
    expect(getHomeData(data).organizations.map((o) => o.name)).toEqual(["Scaleway", "Public AI", "DeepSeek", "Google", "Empty"]);
  });

  it("counts an organization's routes", () => {
    const data = buildData({
      routes: [buildRoute({ slug: "a" }), buildRoute({ slug: "b" })],
      organizations: [buildOrganization({ routes: ["a", "b"] })],
    });
    expect(getHomeData(data).organizations[0].routeCount).toBe(2);
  });
});
