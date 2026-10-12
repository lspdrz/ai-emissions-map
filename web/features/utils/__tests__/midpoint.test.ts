import { describe, expect, it } from "vitest";
import { midpoint } from "@/features/utils/midpoint";

describe("midpoint", () => {
  it("orders ranges by their geometric midpoint", () => {
    expect(midpoint({ low: 1, high: 4 })).toBe(2);
  });
});
