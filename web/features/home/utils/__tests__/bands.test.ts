import { describe, expect, it } from "vitest";
import { bandLimits, bandOf } from "@/features/home/utils/bands";

const upper = [0.03, 0.1, 0.3, 1.0];

describe("bandOf", () => {
  it("is the first band whose upper edge the value is below", () => {
    expect(bandOf(0.012, upper)).toBe(1);
    expect(bandOf(0.299, upper)).toBe(3);
  });

  it("puts a value on an edge in the band above it", () => {
    expect(bandOf(0.03, upper)).toBe(2);
    expect(bandOf(1, upper)).toBe(5);
  });

  it("puts everything from the last edge up in band 5", () => {
    expect(bandOf(10.6, upper)).toBe(5);
  });
});

describe("bandLimits", () => {
  it("states each band's range from its edges", () => {
    expect(bandLimits([0.03, 0.1, 0.3, 1.0])).toEqual(["< 0.03", "0.03–0.1", "0.1–0.3", "0.3–1", "≥ 1"]);
  });
});
