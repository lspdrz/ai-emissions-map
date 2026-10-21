import { formatRange } from "@/features/overview/utils/format";
import { operational, sortRoutes } from "@/features/overview/utils/routes";
import { BandBadge, LetterBadge } from "@/features/overview/ui/components/Badges";
import type { Flags, Model, Organization, Route } from "@/lib/data/types";

const FLAG_TEXT: Record<keyof Flags, string> = {
  gas: "Grid value counts CO₂ only",
  year: "Grid value is from an older year",
};

export function RoutesTable({ routes, models, organizations }: {
  routes: Route[]; models: Model[]; organizations: Organization[];
}) {
  const modelName = new Map(models.map((m) => [m.slug, m.display_name]));
  const orgName = new Map(organizations.map((o) => [o.slug, o.display_name]));
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="border-b border-neutral-300 text-neutral-600">
          <tr>
            <th className="py-2 pr-4 font-medium">Organization and model</th>
            <th className="py-2 pr-4 font-medium">Location</th>
            <th className="py-2 pr-4 font-medium">Disclosure</th>
            <th className="py-2 pr-4 font-medium">Carbon score</th>
            <th className="py-2 font-medium">Inputs</th>
          </tr>
        </thead>
        <tbody>
          {sortRoutes(routes).map((r) => {
            const op = operational(r);
            const model = modelName.get(r.model) ?? r.model;
            return (
              <tr key={r.slug} className="border-b border-neutral-200 align-top">
                <td className="py-3 pr-4">
                  <div className="font-medium">{orgName.get(r.org) ?? r.org}</div>
                  <div>{model}</div>
                  {r.served_as && r.served_as !== model && (
                    <div className="text-neutral-500">offered as {r.served_as}</div>
                  )}
                </td>
                <td className="py-3 pr-4">{r.label}{r.default && <div className="text-neutral-500">default</div>}</td>
                <td className="py-3 pr-4">
                  <LetterBadge letter={r.letter} hint={r.gap} />
                </td>
                <td className="py-3 pr-4">
                  {r.score && r.band ? (
                    <>
                      <div className="whitespace-nowrap text-base font-semibold tabular-nums">
                        {formatRange(r.score)} g
                      </div>
                      <BandBadge band={r.band} />
                      {op && (
                        <div className="mt-1 whitespace-nowrap text-neutral-500 tabular-nums">
                          operational {formatRange(op)} + embodied {formatRange(r.embodied)}
                        </div>
                      )}
                      {r.score_lifecycle && (
                        <div className="whitespace-nowrap text-neutral-500 tabular-nums">
                          life-cycle {formatRange(r.score_lifecycle)} g
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-neutral-500">not scored</div>
                  )}
                </td>
                <td className="py-3 whitespace-nowrap text-neutral-600 tabular-nums">
                  <div>E {formatRange(r.energy)} Wh</div>
                  {r.intensity && <div>I {formatRange(r.intensity)} g/kWh</div>}
                  <div>M {formatRange(r.embodied)} g</div>
                  {(Object.keys(r.flags) as (keyof Flags)[]).map((flag) => (
                    <div key={flag} className="text-amber-700">
                      {FLAG_TEXT[flag]}: {r.flags[flag]?.join(", ")}
                    </div>
                  ))}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
