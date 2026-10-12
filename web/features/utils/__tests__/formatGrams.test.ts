import { describe, expect, it } from "vitest";
import { fmtG, fmtParams, fmtRange } from "@/features/utils/formatGrams";

describe("formatGrams", () => {
  it("formats grams with sensible precision", () => {
    expect(fmtG(0.075)).toBe("0.075");
    expect(fmtG(0.69)).toBe("0.69");
    expect(fmtG(2.5)).toBe("2.50");
    expect(fmtG(10.54)).toBe("10.5");
  });
  it("collapses a point range", () => {
    expect(fmtRange({ low: 0.057, high: 0.057 })).toBe("0.057");
    expect(fmtRange({ low: 0.69, high: 10.54 })).toBe("0.69–10.5");
  });
  it("formats parameter counts", () => {
    expect(fmtParams(70)).toBe("70");
    expect(fmtParams({ min: 90, max: 240 })).toBe("90–240");
    expect(fmtParams(null)).toBe("unknown");
  });
});
