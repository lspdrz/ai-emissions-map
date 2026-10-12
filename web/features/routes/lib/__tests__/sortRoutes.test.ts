import { describe, expect, it } from "vitest";
import { sortRoutes } from "@/features/routes/lib/sortRoutes";
import type { Route } from "@/lib/data/types";

const route = (slug: string, score: [number, number] | null): Route => ({
  slug, org: "o", model: "m", label: slug, default: false, scored: !!score, level: "country", letter: "C",
  gap: null, score: score && { low: score[0], high: score[1] }, embodied: { low: 0, high: 0 }, band: null, served_as: null,
});

describe("sortRoutes", () => {
  it("orders scored routes by estimate, lowest first, and unscored routes last by name", () => {
    const sorted = sortRoutes([route("z-unscored", null), route("high", [3, 12]), route("a-unscored", null), route("low", [0.07, 0.08])]);
    expect(sorted.map((r) => r.slug)).toEqual(["low", "high", "a-unscored", "z-unscored"]);
  });
});
