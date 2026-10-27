import type { Scale } from "@/features/home/types";
import { bandOf } from "@/features/home/utils/bands";
import { formatNumber } from "@/features/home/utils/format";
import type { Range } from "@/lib/data/types";

/** Labels of two ends closer than this (percent of the chart) would overlap, so they print as one "low–high". */
const JOIN_BELOW = 8;
/** A bar is never drawn narrower than this (percent), so a point still shows. */
const MIN_WIDTH = 0.4;

/** The 1–3 steps (…0.01, 0.03, 0.1, 0.3, 1, 3…) from one decade below `lo` to one above `hi`. toPrecision(1) keeps
 *  3 × 10⁻¹ at 0.3 rather than 0.30000000000000004, so steps compare equal to the data. */
function steps(lo: number, hi: number): number[] {
  const out: number[] = [];
  for (let k = Math.floor(Math.log10(lo)) - 1; k <= Math.ceil(Math.log10(hi)) + 1; k++) {
    for (const m of [1, 3]) out.push(Number((m * 10 ** k).toPrecision(1)));
  }
  return out;
}

/** The chart's scale for these ranges: from the step at or below the lowest low to the step at or above the highest
 *  high, so both ends sit on a tick. Computed from every route, never the shown page, so bars don't move as the
 *  reader searches or pages. Null without a range to show. */
export function niceScale(ranges: Range[]): Scale | null {
  // A log scale has no place for zero, negatives or NaN, and steps() would never finish on them.
  ranges = ranges.filter((r) => r.low > 0 && Number.isFinite(r.low) && r.high > 0 && Number.isFinite(r.high));
  if (ranges.length === 0) return null;
  const lo = Math.min(...ranges.map((r) => r.low));
  const hi = Math.max(...ranges.map((r) => r.high));
  const all = steps(lo, hi);
  const min = all.filter((s) => s <= lo).at(-1)!;
  let max = all.find((s) => s >= hi)!;
  if (max === min) max = all[all.indexOf(min) + 1];
  return { min, max, ticks: all.filter((s) => s >= min && s <= max) };
}

/** Where a value sits on the scale, in percent from the left; values outside it stay on its edges. */
export function position(scale: Scale, x: number): number {
  const p = ((Math.log10(x) - Math.log10(scale.min)) / (Math.log10(scale.max) - Math.log10(scale.min))) * 100;
  return Math.min(100, Math.max(0, p));
}

/** The carbon bands the scale spans, as percent spans, for the chart's alternating background. */
export function shading(scale: Scale, upper: number[]): { from: number; to: number; band: number }[] {
  const edges = [scale.min, ...upper.filter((u) => u > scale.min && u < scale.max), scale.max];
  return edges.slice(0, -1).map((edge, i) => ({
    from: position(scale, edge),
    to: position(scale, edges[i + 1]),
    band: bandOf(edge, upper),
  }));
}

/** A range's bar on the chart: its ends and width in percent, and whether its two labels print as one. */
export function rangeMarks(scale: Scale, r: Range): { left: number; right: number; width: number; joined: boolean } {
  const left = position(scale, r.low);
  const right = position(scale, r.high);
  const joined = formatNumber(r.low) === formatNumber(r.high) || right - left < JOIN_BELOW;
  return { left, right, width: Math.max(right - left, MIN_WIDTH), joined };
}

/** A position as a CSS percentage, to two decimals. Inline styles carry it from server HTML to the browser, so it must
 *  print the same on both: full-precision floats did not, and broke hydration. */
export function percent(p: number): string {
  return `${p.toFixed(2)}%`;
}
