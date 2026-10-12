import type { Range } from "@/lib/data/types";

/** The sort key for a score range: its geometric midpoint. Never displayed. */
export function midpoint(r: Range): number {
  return Math.sqrt(r.low * r.high);
}
