import { describe, expect, it } from "vitest";
import { formatBand, formatNumber, formatRange, formatSpread, typeLabel } from "@/features/home/utils/format";

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

describe("formatSpread", () => {
  it("counts the routes at each rating, A to D, two spaces apart", () => {
    expect(formatSpread({ D: 1, A: 1, C: 2, B: 1 })).toBe("1×A  1×B  2×C  1×D");
  });

  it("leaves out ratings with no routes", () => {
    expect(formatSpread({ C: 6 })).toBe("6×C");
  });
});

describe("typeLabel", () => {
  it("names each type in words", () => {
    expect(typeLabel("model_lab")).toBe("Model lab");
    expect(typeLabel("inference_host")).toBe("Inference host");
    expect(typeLabel("cloud")).toBe("Cloud");
  });

  it("shows a type it does not know as it is", () => {
    expect(typeLabel("satellite")).toBe("satellite");
  });
});
