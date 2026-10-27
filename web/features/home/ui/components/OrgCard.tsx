import type { OrgCard as Card } from "@/features/home/types";
import { formatSpread, typeLabel } from "@/features/home/utils/format";

/** One organization: its name and type, its rating letter, and how many routes it has at each rating. */
export function OrgCard({ card }: { card: Card }) {
  return (
    <article className="flex flex-col gap-3 border-t border-ink pt-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 flex-col gap-1">
          <h3 className="text-[21px] font-medium tracking-[-0.01em]">{card.name}</h3>
          <p className="text-sm text-muted">{typeLabel(card.type)}</p>
        </div>
        <span aria-label={card.letter ? `Rating ${card.letter}` : "Not rated"} className="font-mono text-[40px] leading-none font-medium">
          {card.letter ?? "–"}
        </span>
      </div>
      <dl className="grid grid-cols-2 gap-2 font-mono text-xs">
        <div className="flex flex-col gap-0.5">
          <dt className="text-muted">Routes</dt>
          <dd className="text-sm">{card.routeCount}</dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="text-muted">Spread</dt>
          {/* whitespace-pre keeps the two spaces between counts. */}
          <dd className="text-sm whitespace-pre">{formatSpread(card.spread)}</dd>
        </div>
      </dl>
    </article>
  );
}
