import { formatBand } from "@/features/overview/utils/format";

// A numbered color scale for carbon bands, letters in plain outline for disclosure, so the two are never
// confused (METHODOLOGY.md, Presentation).
const BAND_COLORS: Record<number, string> = {
  1: "bg-emerald-100 text-emerald-900",
  2: "bg-lime-100 text-lime-900",
  3: "bg-yellow-100 text-yellow-900",
  4: "bg-orange-100 text-orange-900",
  5: "bg-red-100 text-red-900",
};

export function BandBadge({ band }: { band: [number, number] }) {
  const span = band[0] === band[1] ? BAND_COLORS[band[0]] : "bg-gradient-to-r from-lime-100 to-orange-100";
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-sm font-medium tabular-nums ${span}`}>
      Band {formatBand(band)}
    </span>
  );
}

/** A disclosure letter; `hint` (a route's gap) shows as the browser's tooltip on hover. */
export function LetterBadge({ letter, hint }: { letter: string | null; hint?: string | null }) {
  return (
    <span
      title={hint ?? undefined}
      className={`inline-flex size-7 items-center justify-center rounded border border-current text-sm font-semibold ${
        hint ? "cursor-help" : ""
      }`}
    >
      {letter ?? "–"}
    </span>
  );
}
