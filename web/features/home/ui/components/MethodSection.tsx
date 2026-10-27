import { BAND_BORDER } from "@/features/home/ui/components/RangeCell";
import { type Band, bandLimits } from "@/features/home/utils/bands";
import { METHODOLOGY_URL } from "@/lib/links";
import type { Meta } from "@/lib/data/types";

const RATINGS = [
  ["A", "Names the facility"],
  ["B", "Names one grid"],
  ["C", "Names several possible grids"],
  ["D", "Undisclosed"],
] as const;

const BODY = "text-[15px] leading-[1.6] text-body";
const SUBHEAD = "text-[19px] font-semibold";

/** How routes are researched, scored and rated, in brief. The versions, PUE and grid year come from meta, so the text
 *  always describes the release it sits on. */
export function MethodSection({ meta }: { meta: Meta }) {
  return (
    // The rule spans the screen; the content keeps to the page column.
    <section id="method" className="border-t border-ink">
      <div className="page-container flex flex-col gap-10 pt-14 pb-[88px]">
        <h2 className="text-[32px] font-medium tracking-[-0.02em]">Method</h2>

        <div className="flex flex-col gap-5">
          <h3 className={SUBHEAD}>Research</h3>
          <p className={BODY}>
            Each provider is researched from its own publications for information about where its models are served.
            From that evidence, each route gets a list of the places it may run. A route’s location disclosure rating is
            determined by how precisely those places are named.
          </p>
          <p className={`-mt-2 ${BODY}`}>
            A route’s derived location is then used to determine which electrical grid the model’s server is connected
            to. One known grid can give a narrow intensity range, several give a range from the cleanest to the most
            carbon-intensive. An undisclosed location cannot be scored at all.
          </p>
        </div>

        <div className="flex flex-wrap gap-x-16 gap-y-12">
          <div className="flex flex-[1_1_420px] flex-col gap-5">
            <h3 className={SUBHEAD}>Carbon intensity</h3>
            <p className="font-mono text-[28px] text-accent">(E × I) + M</p>
            <p className={BODY}>
              The Software Carbon Intensity (ISO/IEC 21031) of generating 1,000 output tokens. Energy (E) and embodied
              hardware emissions (M) are estimated with EcoLogits {meta.ecologits_version} from the model’s parameter
              counts, with a PUE range of {meta.pue[0]}–{meta.pue[1]}. Grid intensity (I) is {meta.grid.source}’s{" "}
              {meta.grid.year} life-cycle intensity for each country, US state or Chinese province the route may be
              connected to.
            </p>
            <div className="grid grid-cols-5 gap-2 font-mono text-xs">
              {bandLimits(meta.band_upper).map((limit, i) => (
                <div key={limit} className={`flex flex-col gap-0.5 border-t-4 pt-2 ${BAND_BORDER[(i + 1) as Band]}`}>
                  <span className="font-medium">{i + 1}</span>
                  <span className="text-muted">{limit}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-[1_1_420px] flex-col gap-5">
            <h3 className={SUBHEAD}>Location disclosure</h3>
            <p className={BODY}>
              Rated per route from the location the organization cites. The more precisely a route’s location is known,
              the narrower its carbon intensity range.
            </p>
            <dl className="flex flex-col">
              {RATINGS.map(([letter, meaning], i) => (
                <div
                  key={letter}
                  className={`grid grid-cols-[48px_minmax(0,1fr)] border-t py-3 text-[15px] ${i === 0 ? "border-ink" : "border-rule"} ${i === RATINGS.length - 1 ? "border-b border-b-rule" : ""}`}
                >
                  <dt className="font-mono font-medium">{letter}</dt>
                  <dd>{meaning}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        <p className={BODY}>
          Read the full methodology{" "}
          <a href={METHODOLOGY_URL} target="_blank" rel="noopener noreferrer" className="text-accent underline">
            here
          </a>
          .
        </p>
      </div>
    </section>
  );
}
