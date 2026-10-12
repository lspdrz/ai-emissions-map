import { BAND_SHADE_VARS } from "@/features/constants/bands";
import { fmtRange } from "@/features/utils/formatGrams";
import type { Range } from "@/lib/data/types";

// The log scale every range bar shares: 0.01 g to 30 g per 1,000 tokens, three and a half orders of
// magnitude, wide enough for a small model on a clean grid and a large one on a coal-heavy grid.
// Only RangeBar and RangeAxis need positions on it, so the geometry lives here.
const SCALE_MIN = 0.01;
const SCALE_MAX = 30;
const TICKS = [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30];

/** Position (0–100%) of a value in grams on the scale, clamped. */
function pos(v: number): number {
  const lo = Math.log10(SCALE_MIN), hi = Math.log10(SCALE_MAX);
  const x = Math.min(Math.max(v, SCALE_MIN), SCALE_MAX);
  return ((Math.log10(x) - lo) / (hi - lo)) * 100;
}

/** The five bands, faintly, as a CSS gradient over the scale (edges from meta.band_upper). */
function bandShading(upper: number[]): string {
  const edges = [0, ...upper.map(pos), 100];
  const stops = BAND_SHADE_VARS.map((v, i) => `var(${v}) ${edges[i]}%, var(${v}) ${edges[i + 1]}%`);
  return `linear-gradient(90deg, ${stops.join(", ")})`;
}

/** A score range on the shared log scale; `shaded` draws the five bands behind it. */
export function RangeBar({ range, upper, shaded = false }: { range: Range; upper: number[]; shaded?: boolean }) {
  const left = pos(range.low);
  const width = Math.max(pos(range.high) - left, 0.8);
  return (
    <div role="img" aria-label={`${fmtRange(range)} grams of CO2-equivalent per 1,000 output tokens`}
         className={`relative rounded-[3px] ${shaded ? "h-[22px]" : "h-3.5 bg-[#eef1f4]"}`}
         style={shaded ? { background: bandShading(upper) } : undefined}>
      <span className={`absolute bg-ink ${shaded ? "top-[5px] h-3 rounded-md" : "top-[3px] h-2 rounded"}`}
            style={{ left: `${left}%`, width: `${width}%` }} />
    </div>
  );
}

/** The scale's tick labels, aligned with RangeBar in the same column. */
export function RangeAxis() {
  return (
    <div aria-hidden="true" className="relative h-4 font-mono">
      {TICKS.map((t) => (
        <span key={t} className="absolute -translate-x-1/2" style={{ left: `${pos(t)}%` }}>{t}</span>
      ))}
    </div>
  );
}
