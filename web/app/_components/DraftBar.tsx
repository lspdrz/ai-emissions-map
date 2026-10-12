/** Shown on every page while the release's grid data is a mock (meta.grid.mock). */
export function DraftBar() {
  return (
    <div role="note" className="flex flex-wrap items-center justify-center gap-3 bg-ink px-6 py-3 text-sm leading-normal text-white">
      <strong className="rounded-[3px] bg-draft px-2 py-[3px] text-xs tracking-[0.06em] text-ink">DRAFT · PLACEHOLDER GRID DATA</strong>
      <span>Location ratings are from captured evidence. Carbon scores use placeholder grid values, to be replaced
        with Electricity Maps data. Not for distribution.</span>
    </div>
  );
}
