import type { Range } from "@/lib/data/types";

/** Two significant figures, enough for estimates that span orders of magnitude; whole numbers from 100 up. */
export function formatNumber(x: number): string {
  if (x === 0) return "0";
  if (Math.abs(x) >= 100) return Math.round(x).toString();
  return x.toPrecision(2);
}

/** "low–high", or one number when the range is a point at the shown precision. */
export function formatRange(r: Range): string {
  const low = formatNumber(r.low);
  const high = formatNumber(r.high);
  return low === high ? low : `${low}–${high}`;
}

/** A band, or a band span when the range crosses bands (METHODOLOGY.md, Bands). */
export function formatBand(band: [number, number]): string {
  return band[0] === band[1] ? `${band[0]}` : `${band[0]}–${band[1]}`;
}
