import { midpoint } from "@/features/utils/midpoint";
import type { MapData, Model, Route } from "@/lib/data/types";

/** The "same model, different grids" comparison: the featured model's scored routes, lowest estimate
 *  first. Null unless there are at least two to compare. */
export function selectFeaturedRoutes(data: MapData): { model: Model; routes: Route[] } | null {
  const model = data.models.find((m) => m.slug === data.meta.featured_model);
  if (!model) return null;
  const routes = data.routes
    .filter((r) => r.model === model.slug && r.score)
    .sort((a, b) => midpoint(a.score!) - midpoint(b.score!));
  return routes.length > 1 ? { model, routes } : null;
}
