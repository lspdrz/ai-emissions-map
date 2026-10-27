import type { Range } from "@/lib/data/types";

/** The geometric midpoint of a score: the sort key only, never displayed (METHODOLOGY.md, Ranges). */
export function midpoint(r: Range): number {
  return Math.sqrt(r.low * r.high);
}
