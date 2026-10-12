import "server-only";
import Link from "next/link";
import { EstimateLabel } from "@/features/components/EstimateLabel";
import { OrganizationCard } from "@/features/components/OrganizationCard";
import { BAND_CHIP_CLASSES } from "@/features/constants/bands";
import { LETTERS } from "@/features/constants/letters";
import { selectFeaturedRoutes } from "@/features/overview/lib/selectFeaturedRoutes";
import { FeaturedChart } from "@/features/overview/ui/components/FeaturedChart";
import { bandRanges } from "@/features/utils/bands";
import { fmtParams } from "@/features/utils/formatGrams";
import { loadData } from "@/lib/data/loadData";

/** The overview: the claim, the release in numbers, the two scales, the featured comparison, and the
 *  organizations. Statically rendered at build time from data.json. */
export function Overview() {
  const data = loadData();
  const { meta } = data;
  const featured = selectFeaturedRoutes(data);
  const facts: [number, string][] = [
    [meta.counts.organizations, "organizations"], [meta.counts.routes, "serving routes"],
    [meta.counts.models, "models"], [meta.counts.zones, "grid zones"],
  ];
  return (
    <>
      <section className="flex max-w-[820px] flex-col gap-6">
        <p className="text-sm font-semibold tracking-[0.08em] text-muted">CARBON AND LOCATION DISCLOSURE OF AI SERVING</p>
        <h1 className="font-serif text-[40px] leading-[1.08] font-medium md:text-[56px]">Where a model runs decides much of what it emits.</h1>
        <p className="text-xl leading-relaxed text-body">
          {meta.intensity_spread !== null && meta.intensity_spread > 1 &&
            `Grid carbon intensity differs ${meta.intensity_spread}-fold between the locations in this release. `}
          We score each AI serving route on its emissions per 1,000 output tokens, and rate each provider on how
          precisely it discloses where its models run.
        </p>
      </section>

      <section aria-label="This release in numbers" className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-px border border-rule bg-rule">
        {facts.map(([n, label]) => (
          <div key={label} className="flex flex-col gap-1 bg-white p-6 text-muted">
            <span className="font-mono text-[40px] text-ink">{n}</span><span>{label}</span>
          </div>
        ))}
      </section>

      <section className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-12">
        <div className="flex flex-col gap-4">
          <h2 className="font-serif text-[30px] font-medium">Carbon score</h2>
          <p className="leading-relaxed text-body">Estimated grams of CO₂-equivalent per 1,000 output tokens: the energy the
            model needs times the carbon intensity of the route&apos;s grid, plus the hardware&apos;s embodied emissions.
            Shown as a range, with an absolute band.</p>
          <div className="flex flex-col gap-1.5">
            {bandRanges(meta.band_upper).map((text, i) => (
              <div key={text} className="flex items-center gap-3">
                <span className={`inline-flex h-8 w-11 items-center justify-center rounded font-mono font-medium ${BAND_CHIP_CLASSES[i]}`}>{i + 1}</span>
                <span className="font-mono text-sm text-body">{text}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-4">
          <h2 className="font-serif text-[30px] font-medium">Location disclosure</h2>
          <p className="leading-relaxed text-body">How precisely the provider&apos;s own publications say where a route runs.
            An organization&apos;s rating is the average of all its routes. It measures disclosure, not cleanliness.</p>
          <div className="flex flex-col gap-1.5">
            {LETTERS.map((l) => (
              <div key={l.letter} className="flex items-center gap-3">
                <span className="inline-flex size-8 items-center justify-center rounded border-2 border-ink font-serif text-xl font-semibold">{l.letter}</span>
                <span className="text-[15px] text-body">{l.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {featured && (
        <section className="flex flex-col gap-6">
          <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
            <h2 className="font-serif text-4xl font-medium">Same model, different grids</h2>
            <Link href="/routes/">All routes →</Link>
          </div>
          <p className="max-w-[820px] leading-relaxed text-body">{featured.model.display_name} on every route that serves
            it. The model is the same, so the differences come from where it runs.</p>
          <div className="flex flex-col gap-2">
            <EstimateLabel gridName={meta.grid.name} />
            <FeaturedChart routes={featured.routes} upper={meta.band_upper} />
          </div>
          <p className="text-sm leading-relaxed text-muted">Bars span the estimate&apos;s range on a logarithmic scale; the
            shading behind them marks bands 1 to 5.
            {featured.model.source === "ecologits" && featured.model.active_b !== null &&
              ` The ranges are wide where a model's size is only estimated: EcoLogits puts ${featured.model.display_name} at ` +
              `${fmtParams(featured.model.active_b)} billion active parameters, ${fmtParams(featured.model.total_b)} billion in total.`}
            {meta.grid.mock && " Placeholder grid values: zones within a country share its average."}</p>
        </section>
      )}

      <section className="flex flex-col gap-6">
        <h2 className="font-serif text-4xl font-medium">Organizations</h2>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(340px,1fr))] gap-6">
          {data.organizations.map((o) => <OrganizationCard key={o.slug} org={o} />)}
        </div>
      </section>
    </>
  );
}
