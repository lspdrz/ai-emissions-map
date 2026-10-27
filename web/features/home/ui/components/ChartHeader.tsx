import type { ReactNode } from "react";
import type { Scale } from "@/features/home/types";
import { percent, position } from "@/features/home/utils/scale";

/** The chart column's header: its sort button and the scale's tick values. Ticks sit inside the same insets as the
 *  bars (26px left, 8px right); the label is pulled 13px left so it starts where the first tick's label starts. */
export function ChartHeader({ scale, label, active, onSort }: {
  scale: Scale | null; label: ReactNode; active: boolean; onSort: () => void;
}) {
  return (
    <div className="-mb-1.5 flex flex-col justify-end gap-1.5 self-stretch pt-0 pr-2 pb-3 pl-[26px] max-[760px]:hidden">
      <button
        type="button"
        onClick={onSort}
        className={`-ml-[13px] cursor-pointer self-start whitespace-nowrap ${active ? "text-ink" : "text-muted"}`}
      >
        {label}
      </button>
      <div className="relative h-3.5">
        {scale?.ticks.map((t) => (
          <span key={t} className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: percent(position(scale, t)) }}>
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
