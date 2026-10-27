import type { HomeData } from "@/features/home/types";
import { loadData } from "@/lib/data/loadData";
import type { MapData } from "@/lib/data/types";

/** The home page's view of data.json: each route with its organization's and model's display names resolved. A model
 *  with no record shows its slug. Order is left to the table. */
export function getHomeData(data: MapData = loadData()): HomeData {
  const orgName = new Map(data.organizations.map((o) => [o.slug, o.display_name]));
  const modelName = new Map(data.models.map((m) => [m.slug, m.display_name]));
  return {
    meta: data.meta,
    routes: data.routes.map((r) => ({
      slug: r.slug,
      org: orgName.get(r.org) ?? r.org,
      model: modelName.get(r.model) ?? r.model,
      label: r.label,
      letter: r.letter,
      score: r.score,
    })),
  };
}
