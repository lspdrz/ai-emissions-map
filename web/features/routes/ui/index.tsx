import "server-only";
import { BandChip } from "@/features/components/BandChip";
import { EstimateLabel } from "@/features/components/EstimateLabel";
import { LetterBadge } from "@/features/components/LetterBadge";
import { RangeBar } from "@/features/components/RangeBar";
import { sortRoutes } from "@/features/routes/lib/sortRoutes";
import { fmtRange } from "@/features/utils/formatGrams";
import { loadData } from "@/lib/data/loadData";

const TH = "bg-panel px-4 py-3.5 text-left text-[13px] font-semibold text-muted";
const TD = "border-t border-rule p-4 align-top";

export function AllRoutes() {
  const data = loadData();
  const orgName = Object.fromEntries(data.organizations.map((o) => [o.slug, o.display_name]));
  const modelName = Object.fromEntries(data.models.map((m) => [m.slug, m.display_name]));
  return (
    <>
      <section className="flex max-w-[820px] flex-col gap-4">
        <h1 className="font-serif text-5xl leading-[1.1] font-medium">All routes</h1>
        <p className="text-lg leading-relaxed text-body">A route is one organization serving one model from one location.
          Each is rated on how precisely its location is disclosed, and scored on estimated emissions per 1,000 output
          tokens. Ordered from lowest to highest estimated emissions.</p>
      </section>
      <EstimateLabel gridName={data.meta.grid.name} />
      <div className="-mt-12 overflow-x-auto rounded-md border border-rule">
        <table className="w-full min-w-[1080px] border-collapse text-[15px]">
          <thead>
            <tr><th scope="col" className={TH}>Organization · model</th><th scope="col" className={TH}>Where it runs</th>
              <th scope="col" className={TH}>Disclosure</th>
              <th scope="col" className={`${TH} w-80`}>Carbon score, g CO₂e / 1k tokens</th>
              <th scope="col" className={TH}>Band</th></tr>
          </thead>
          <tbody>
            {sortRoutes(data.routes).map((r) => (
              <tr key={r.slug}>
                <td className={TD}><div className="font-semibold">{orgName[r.org]}</div>
                  <div className="text-sm text-muted">{modelName[r.model] ?? r.model}</div></td>
                <td className={TD}>{r.label}{r.default && (
                  <div><span className="mt-1.5 inline-block rounded-[3px] border border-[#a7b0bc] px-1.5 text-xs font-semibold text-muted">DEFAULT</span></div>)}</td>
                <td className={TD}><div className="flex items-start gap-2.5">
                  <LetterBadge letter={r.letter} />
                  {r.gap && <span className="max-w-[220px] text-sm leading-snug text-body">{r.gap}</span>}
                </div></td>
                <td className={TD}>{r.score ? (
                  <>
                    <div className="font-mono">{fmtRange(r.score)}</div>
                    <div className="mt-2"><RangeBar range={r.score} upper={data.meta.band_upper} /></div>
                    <div className="mt-1.5 text-[13px] text-muted">of which embodied {fmtRange(r.embodied)} g</div>
                    {r.score_lifecycle && (
                      <div className="text-[13px] text-muted">with life-cycle grid factors {fmtRange(r.score_lifecycle)} g</div>)}
                  </>
                ) : <span className="text-sm text-muted">Not scored</span>}</td>
                <td className={TD}><BandChip band={r.band} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="max-w-[900px] text-sm leading-relaxed text-muted">Bars use a logarithmic scale from 0.01 to 30 g.
        Scores are full Software Carbon Intensity estimates: energy from EcoLogits {data.meta.ecologits_version} with a
        PUE of {data.meta.pue[0]}–{data.meta.pue[1]}, times the grid&apos;s carbon intensity, plus embodied hardware
        emissions.</p>
    </>
  );
}
