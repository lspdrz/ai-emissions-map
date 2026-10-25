import { formatRange } from "@/features/overview/utils/format";
import { operational, sortRoutes } from "@/features/overview/utils/routes";
import { BandBadge, LetterBadge } from "@/features/overview/ui/components/Badges";
import type { Model, Organization, Route } from "@/lib/data/types";

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
            <th className="py-2 pr-4 font-medium">Carbon intensity (SCI)</th>
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
                  {r.sci && r.band ? (
                    <>
                      <div className="whitespace-nowrap text-base font-semibold tabular-nums">
                        {formatRange(r.sci)} g
                      </div>
                      <BandBadge band={r.band} />
                      {op && (
                        <div className="mt-1 whitespace-nowrap text-neutral-500 tabular-nums">
                          operational {formatRange(op)} + embodied {formatRange(r.embodied)}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-neutral-500">not calculated</div>
                  )}
                </td>
                <td className="py-3 whitespace-nowrap text-neutral-600 tabular-nums">
                  <div>E {formatRange(r.energy)} Wh</div>
                  {r.grid_intensity && <div>I {formatRange(r.grid_intensity)} g/kWh</div>}
                  <div>M {formatRange(r.embodied)} g</div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
