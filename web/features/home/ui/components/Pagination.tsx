const BUTTON = "min-h-11 min-w-11 cursor-pointer font-mono text-[13px] disabled:cursor-default";

/** The line under the table: what is shown on the left; Prev, the page numbers and Next on the right. Every button
 *  is at least 44px square. */
export function Pagination({ label, page, pageCount, onPage }: {
  label: string; page: number; pageCount: number; onPage: (page: number) => void;
}) {
  const atFirst = page === 0;
  const atLast = page === pageCount - 1;
  return (
    <nav aria-label="Routes pages" className="flex flex-wrap items-center justify-between gap-4 font-mono text-[13px]">
      <span className="text-muted">{label}</span>
      <div className="flex items-center gap-1">
        <button type="button" disabled={atFirst} onClick={() => onPage(page - 1)} className={`${BUTTON} px-3 ${atFirst ? "text-disabled" : "text-ink"}`}>
          ← Prev
        </button>
        {Array.from({ length: pageCount }, (_, i) => (
          <button
            key={i}
            type="button"
            aria-label={`Page ${i + 1}`}
            aria-current={i === page ? "page" : undefined}
            onClick={() => onPage(i)}
            className={`${BUTTON} border ${i === page ? "border-ink bg-ink text-ground" : "border-transparent text-ink"}`}
          >
            {i + 1}
          </button>
        ))}
        <button type="button" disabled={atLast} onClick={() => onPage(page + 1)} className={`${BUTTON} px-3 ${atLast ? "text-disabled" : "text-ink"}`}>
          Next →
        </button>
      </div>
    </nav>
  );
}
