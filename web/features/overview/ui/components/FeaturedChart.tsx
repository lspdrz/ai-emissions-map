import { LetterBadge } from "@/features/components/LetterBadge";
import { RangeAxis, RangeBar } from "@/features/components/RangeBar";
import { fmtRange } from "@/features/utils/formatGrams";
import type { Route } from "@/lib/data/types";

const ROW = "grid grid-cols-[260px_40px_minmax(360px,1fr)_150px] items-center gap-4";

/** "Same model, different grids": one row per route, every bar on the same log scale. */
export function FeaturedChart({ routes, upper }: { routes: Route[]; upper: number[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-rule p-6">
      <div className="flex min-w-[860px] flex-col gap-2.5">
        <div className={`${ROW} text-[13px] text-muted`}>
          <span>Where it runs</span><span>Discl.</span>
          <RangeAxis />
          <span className="text-right">g CO₂e / 1k tokens</span>
        </div>
        {routes.map((r) => (
          <div key={r.slug} className={`${ROW} min-h-9`}>
            <span>{r.label}{r.default && <Tag>DEFAULT</Tag>}</span>
            <LetterBadge letter={r.letter} />
            <RangeBar range={r.score!} upper={upper} shaded />
            <span className="text-right font-mono text-sm">{fmtRange(r.score!)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return <span className="ml-2 rounded-[3px] border border-[#a7b0bc] px-1.5 py-px text-xs font-semibold whitespace-nowrap text-muted">{children}</span>;
}
