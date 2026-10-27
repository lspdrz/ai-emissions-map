import { describe, expect, it } from "vitest";
import { midpoint } from "@/features/home/utils/routes";

describe("midpoint", () => {
  it("is the geometric mean of the ends", () => {
    expect(midpoint({ low: 0.01, high: 1 })).toBeCloseTo(0.1);
  });
});
