import type { Meta } from "@/lib/data/types";

/** The site's footer, on every page: the data sources and the licence. The year is the release's, from meta; no
 *  release date, draft flag or methodology version appears on the page. */
export function Footer({ meta }: { meta: Meta }) {
  return (
    // The rule spans the screen; the content keeps to the page column.
    <footer className="border-t border-ink">
      <div className="page-container flex flex-wrap justify-between gap-3 pt-6 pb-10 font-mono text-xs text-muted">
        <span>
          {meta.grid.source} {meta.grid.year} (CC-BY-4.0) · EcoLogits {meta.ecologits_version}
        </span>
        <span>MIT License · {meta.release_date.slice(0, 4)}</span>
      </div>
    </footer>
  );
}
