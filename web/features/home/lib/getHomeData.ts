import type { HomeData, OrgCard, RouteRow } from "@/features/home/types";
import { loadData } from "@/lib/data/loadData";
import type { MapData } from "@/lib/data/types";

/** Best rating first (highest mean), then by name; organizations with no rating last. */
function byRating(a: OrgCard, b: OrgCard): number {
  if (a.mean === null || b.mean === null) return (a.mean === null ? 1 : 0) - (b.mean === null ? 1 : 0) || a.name.localeCompare(b.name);
  return b.mean - a.mean || a.name.localeCompare(b.name);
}

/** The home page's view of data.json: each route with its organization's and model's display names resolved (a model
 *  with no record shows its slug; order is left to the table), and each organization's card, best rated first. */
export function getHomeData(data: MapData = loadData()): HomeData {
  const orgName = new Map(data.organizations.map((o) => [o.slug, o.display_name]));
  const modelName = new Map(data.models.map((m) => [m.slug, m.display_name]));
  return {
    meta: data.meta,
    routes: data.routes.map<RouteRow>((r) => ({
      slug: r.slug,
      org: orgName.get(r.org) ?? r.org,
      model: modelName.get(r.model) ?? r.model,
      label: r.label,
      letter: r.letter,
      score: r.sci,
    })),
    organizations: data.organizations
      .map<OrgCard>((o) => ({
        slug: o.slug,
        name: o.display_name,
        type: o.type,
        letter: o.rating.letter,
        mean: o.rating.mean,
        routeCount: o.routes.length,
        spread: o.rating.spread,
      }))
      .sort(byRating),
  };
}
