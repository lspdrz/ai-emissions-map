import type { Scale } from "@/features/home/types";
import { type Band, bandOf } from "@/features/home/utils/bands";
import { formatNumber } from "@/features/home/utils/format";
import { percent, rangeMarks, shading } from "@/features/home/utils/scale";
import type { Range } from "@/lib/data/types";

/** The five band colors as Tailwind classes, spelled out so Tailwind sees them. The number is always shown beside the
 *  color, so color is never the only signal. */
export const BAND_TEXT: Record<Band, string> = {
  1: "text-band-1", 2: "text-band-2", 3: "text-band-3", 4: "text-band-4", 5: "text-band-5",
};
export const BAND_BORDER: Record<Band, string> = {
  1: "border-band-1", 2: "border-band-2", 3: "border-band-3", 4: "border-band-4", 5: "border-band-5",
};

const HATCH = "repeating-linear-gradient(135deg, var(--color-hatch) 0 1px, transparent 1px 8px)";

/** "low–high", each end in its band's color with a grey dash between; one number when both ends print the same; a
 *  grey dash for a route that is not scored. */
export function RangeNumbers({ score, bandUpper }: { score: Range | null; bandUpper: number[] }) {
  if (!score) return <span className="text-muted">—</span>;
  const low = formatNumber(score.low);
  const high = formatNumber(score.high);
  return (
    <>
      <span className={BAND_TEXT[bandOf(score.low, bandUpper)]}>{low}</span>
      {low !== high && (
        <>
          <span className="font-normal text-muted">–</span>
          <span className={BAND_TEXT[bandOf(score.high, bandUpper)]}>{high}</span>
        </>
      )}
    </>
  );
}

/** The bands behind the chart as one hard-stop gradient: bands 1, 3 and 5 shaded, 2 and 4 clear. */
function bandBackground(scale: Scale, bandUpper: number[]): string {
  const stops = shading(scale, bandUpper).map(
    (b) => `${b.band % 2 ? "var(--color-shade)" : "transparent"} ${percent(b.from)} ${percent(b.to)}`,
  );
  return `linear-gradient(to right, ${stops.join(", ")})`;
}

const LABEL = "absolute top-[calc(36%+8px)] -translate-x-1/2 font-mono text-xs font-medium whitespace-nowrap";

/** A route's cell in the range chart: a bar from low to high on the log scale, with each end's number under its dot
 *  (or both together when they would collide). A route not scored gets hatching instead; it says why only when the
 *  reason is the undisclosed location, since a route on its own generation can be unscored at any letter. */
export function RangeCell({ score, letter, scale, bandUpper }: {
  score: Range | null; letter: string; scale: Scale | null; bandUpper: number[];
}) {
  if (!score || !scale) {
    return (
      <div className="flex items-center justify-center self-stretch max-[760px]:hidden" style={{ background: HATCH }}>
        <span className="bg-ground px-2.5 py-0.5 font-mono text-[11px] text-muted">
          {letter === "D" ? "Not scored · location undisclosed" : "Not scored"}
        </span>
      </div>
    );
  }
  const m = rangeMarks(scale, score);
  return (
    <div className="relative self-stretch max-[760px]:hidden">
      <div className="absolute inset-y-0 right-2 left-[26px]" style={{ background: bandBackground(scale, bandUpper) }}>
        <div className="absolute top-[36%] -mt-px h-0.5 bg-ink" style={{ left: percent(m.left), width: percent(m.width) }}>
          <span className="absolute -top-[3px] -left-1 size-2 rounded-full bg-ink" />
          <span className="absolute -top-[3px] -right-1 size-2 rounded-full bg-ink" />
        </div>
        {m.joined ? (
          <span className={LABEL} style={{ left: percent((m.left + m.right) / 2) }}>
            <RangeNumbers score={score} bandUpper={bandUpper} />
          </span>
        ) : (
          <>
            <span className={`${LABEL} ${BAND_TEXT[bandOf(score.low, bandUpper)]}`} style={{ left: percent(m.left) }}>
              {formatNumber(score.low)}
            </span>
            <span className={`${LABEL} ${BAND_TEXT[bandOf(score.high, bandUpper)]}`} style={{ left: percent(m.right) }}>
              {formatNumber(score.high)}
            </span>
          </>
        )}
      </div>
    </div>
  );
}
