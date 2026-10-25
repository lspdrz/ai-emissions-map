import { OrganizationList } from "@/features/overview/ui/components/OrganizationList";
import { RoutesTable } from "@/features/overview/ui/components/RoutesTable";
import type { MapData } from "@/lib/data/types";

/** The whole release on one page: every route with its carbon intensity, every organization with its rating and evidence. */
export function OverviewView({ data }: { data: MapData }) {
  const { meta, routes, models, organizations } = data;
  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">AI Emissions Map</h1>
        <p className="text-neutral-600">
          Carbon intensities for AI serving routes, and how precisely each organization discloses where they run.
        </p>
        <p className="text-sm text-neutral-500">
          Release {meta.release_date}
          {meta.draft && " (draft)"} · methodology {meta.methodology_version} · grid data {meta.grid.source}{" "}
          {meta.grid.year} ·
          EcoLogits {meta.ecologits_version}
        </p>
      </header>

      {routes.length === 0 ? (
        <p className="mt-10 text-neutral-600">No routes in this release yet.</p>
      ) : (
        <>
          {/* Native <details>: collapsible without client JavaScript. Organizations start collapsed, routes open. */}
          <details className="group mt-10">
            <summary className="mb-4 cursor-pointer list-none text-xl font-semibold">
              <span className="inline-block w-5 transition-transform group-open:rotate-90">›</span>
              Organizations <span className="text-base font-normal text-neutral-500">({organizations.length})</span>
            </summary>
            <OrganizationList organizations={organizations} />
          </details>

          <details open className="group mt-8">
            <summary className="cursor-pointer list-none text-xl font-semibold">
              <span className="inline-block w-5 transition-transform group-open:rotate-90">›</span>
              Routes <span className="text-base font-normal text-neutral-500">({routes.length})</span>
            </summary>
            <p className="mt-1 mb-4 text-sm text-neutral-600">
              Each carbon intensity (SCI) is a life-cycle estimate from EcoLogits and Ember, in grams of CO₂e per 1,000 output tokens:
              operational (E × I) plus embodied (M), lowest first. Disclosure is rated A to D.
            </p>
            <RoutesTable routes={routes} models={models} organizations={organizations} />
          </details>
        </>
      )}

      <footer className="mt-16 border-t border-neutral-200 pt-4 text-xs text-neutral-500">
        Energy (E) and embodied emissions (M) are estimated with EcoLogits {meta.ecologits_version}, with data-center
        overhead (PUE) {meta.pue[0]}–{meta.pue[1]} for every route. Grid intensity (I) is {meta.grid.source}&apos;s
        life-cycle intensity of generation for each grid&apos;s country, US state or Chinese province, for{" "}
        {meta.grid.year} or its latest
        earlier year (CC-BY-4.0).
      </footer>
    </main>
  );
}
