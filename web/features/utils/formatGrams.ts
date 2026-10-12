import type { Params, Range } from "@/lib/data/types";

export function fmtG(v: number): string {
  if (v >= 10) return v.toFixed(1);
  if (v >= 1) return v.toFixed(2);
  return String(Number(v.toPrecision(2)));
}

export function fmtRange(r: Range): string {
  const a = fmtG(r.low), b = fmtG(r.high);
  return a === b ? a : `${a}–${b}`;
}

export function fmtParams(p: Params | null): string {
  if (p === null) return "unknown";
  return typeof p === "number" ? `${p}` : `${p.min}–${p.max}`;
}
