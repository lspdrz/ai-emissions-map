import { describe, expect, it } from "vitest";
import { midpoint, operational, sortRoutes } from "@/features/overview/utils/routes";
import type { Route } from "@/lib/data/types";

function route(slug: string, sci: [number, number] | null, embodied: [number, number] = [0.05, 0.05]): Route {
  return {
    slug, org: "acme", model: "m", label: "Somewhere", default: false, letter: "B", gap: null,
    sci: sci && { low: sci[0], high: sci[1] },
    energy: { low: 0.5, high: 0.6 }, grid_intensity: null, embodied: { low: embodied[0], high: embodied[1] },
    band: null, served_as: null,
  };
}

describe("midpoint", () => {
  it("is the geometric mean of the ends", () => {
    expect(midpoint({ low: 0.01, high: 1 })).toBeCloseTo(0.1);
  });
});

describe("sortRoutes", () => {
  it("orders by geometric midpoint, not by the low end", () => {
    // Low ends say a < b; geometric midpoints (0.0447 vs 0.04) say b < a.
    const a = route("a", [0.01, 0.2]);
    const b = route("b", [0.02, 0.08]);
    expect(sortRoutes([a, b]).map((r) => r.slug)).toEqual(["b", "a"]);
  });
  it("puts routes without a carbon intensity last", () => {
    const sorted = sortRoutes([route("none", null), route("x", [0.1, 0.2])]);
    expect(sorted.map((r) => r.slug)).toEqual(["x", "none"]);
  });
});

describe("operational", () => {
  it("is the carbon intensity less the embodied part, at each end", () => {
    const r = operational(route("x", [0.086131, 0.099556], [0.056597, 0.056597]));
    expect(r?.low).toBeCloseTo(0.029534);
    expect(r?.high).toBeCloseTo(0.042959);
  });
  it("is absent when the route has no carbon intensity", () => {
    expect(operational(route("x", null))).toBeNull();
  });
});
