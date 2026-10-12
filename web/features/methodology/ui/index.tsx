import "server-only";
import { fullMethodology, renderMarkdown } from "@/features/methodology/lib/renderMethodology";
import { loadData, loadMethodology } from "@/lib/data/loadData";

export async function Methodology() {
  const { meta } = loadData();
  const html = await renderMarkdown(fullMethodology(loadMethodology()));
  return (
    <div className="flex max-w-[860px] flex-col gap-10">
      <h1 className="font-serif text-[52px] leading-[1.08] font-medium">Methodology</h1>
      {meta.grid.mock && (
        <section className="flex flex-col gap-3 rounded-md border-2 border-ink p-6">
          <h2 className="text-lg font-semibold">What is placeholder in this draft</h2>
          <p className="leading-relaxed text-body">The grid intensities{meta.grid.attribution && ` (${meta.grid.attribution})`}.
            They are country-level and production-based where the method calls for consumption-based values, and every
            zone within a country shares that country&apos;s value. They will be replaced with Electricity Maps data.
            Energy, embodied emissions and every location rating are computed exactly as they will be at release.</p>
        </section>
      )}
      {/* The repository's own docs/methodology.md, rendered and sanitized at build time. */}
      <article className="methodology" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
