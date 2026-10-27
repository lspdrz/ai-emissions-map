import { describe, expect, it } from "vitest";
import { niceScale, percent, position, rangeMarks, shading } from "@/features/home/utils/scale";

const upper = [0.03, 0.1, 0.3, 1.0];
const wide = { min: 0.01, max: 30, ticks: [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30] };

describe("niceScale", () => {
  it("rounds the lowest low down and the highest high up to the 1–3 steps", () => {
    expect(niceScale([{ low: 0.012, high: 0.08 }, { low: 0.67, high: 10.606 }])).toEqual(wide);
  });

  it("keeps an end that is already on a step", () => {
    expect(niceScale([{ low: 0.1, high: 3 }])).toEqual({ min: 0.1, max: 3, ticks: [0.1, 0.3, 1, 3] });
  });

  it("widens a single point by one step", () => {
    expect(niceScale([{ low: 0.3, high: 0.3 }])).toEqual({ min: 0.3, max: 1, ticks: [0.3, 1] });
  });

  it("has no scale without a scored route", () => {
    expect(niceScale([])).toBeNull();
  });
});

describe("position", () => {
  it("places the ends at 0 and 100 percent", () => {
    expect(position(wide, 0.01)).toBe(0);
    expect(position(wide, 30)).toBe(100);
  });

  it("is logarithmic", () => {
    const s = { min: 0.1, max: 10, ticks: [] };
    expect(position(s, 1)).toBeCloseTo(50);
  });

  it("keeps values outside the scale on its edges", () => {
    expect(position(wide, 100)).toBe(100);
    expect(position(wide, 0.001)).toBe(0);
  });
});

describe("shading", () => {
  it("cuts the scale into the bands it spans", () => {
    expect(shading(wide, upper).map((b) => b.band)).toEqual([1, 2, 3, 4, 5]);
  });

  it("starts and ends with the scale, not the band edges", () => {
    const bands = shading({ min: 0.1, max: 1, ticks: [] }, upper);
    expect(bands).toHaveLength(2);
    expect(bands[0]).toMatchObject({ from: 0, band: 3 });
    expect(bands[0].to).toBeCloseTo(47.7, 1);
    expect(bands[1]).toMatchObject({ to: 100, band: 4 });
  });
});

describe("rangeMarks", () => {
  it("joins the labels of ends less than 8% of the chart apart", () => {
    expect(rangeMarks(wide, { low: 0.08, high: 0.091 }).joined).toBe(true);
  });

  it("joins the labels of ends that print the same", () => {
    expect(rangeMarks(wide, { low: 0.3001, high: 0.3004 }).joined).toBe(true);
  });

  it("splits the labels of ends far apart", () => {
    const m = rangeMarks(wide, { low: 0.677, high: 9.032 });
    expect(m.joined).toBe(false);
    expect(m.width).toBeCloseTo(m.right - m.left);
  });

  it("keeps a point visible", () => {
    expect(rangeMarks(wide, { low: 0.3, high: 0.3 }).width).toBe(0.4);
  });
});

describe("percent", () => {
  it("writes a CSS percentage with two decimals", () => {
    expect(percent(2.7850774602681256)).toBe("2.79%");
    expect(percent(100)).toBe("100.00%");
  });
});
