import { describe, expect, it } from "vitest";
import { formatBand, formatNumber, formatRange } from "@/features/overview/utils/format";

describe("formatNumber", () => {
  it("keeps two significant figures", () => {
    expect(formatNumber(0.086131)).toBe("0.086");
    expect(formatNumber(0.099556)).toBe("0.10");
    expect(formatNumber(0.876705)).toBe("0.88");
  });
  it("rounds to whole numbers from 100 up", () => {
    expect(formatNumber(1234.5)).toBe("1235");
  });
  it("writes zero plainly", () => {
    expect(formatNumber(0)).toBe("0");
  });
});

describe("formatRange", () => {
  it("joins two ends with a dash", () => {
    expect(formatRange({ low: 0.086131, high: 0.099556 })).toBe("0.086–0.10");
  });
  it("shows one number when both ends round the same", () => {
    expect(formatRange({ low: 49, high: 49 })).toBe("49");
  });
});

describe("formatBand", () => {
  it("shows one band, or the span a range crosses", () => {
    expect(formatBand([2, 2])).toBe("2");
    expect(formatBand([2, 3])).toBe("2–3");
  });
});
