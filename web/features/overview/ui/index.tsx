import "server-only";
import { loadData } from "@/lib/data/loadData";

/** The overview: what this release holds. Statically rendered at build time from data.json. */
export function Overview() {
  const { meta } = loadData();
  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="text-3xl font-semibold">AI Emissions Map</h1>
      <p>
        Release {meta.release_date}: {meta.counts.routes} routes from {meta.counts.organizations} organizations,{" "}
        {meta.counts.models} models and {meta.counts.grids} grids.
      </p>
    </main>
  );
}
