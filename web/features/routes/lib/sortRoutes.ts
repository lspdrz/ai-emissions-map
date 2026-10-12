import { midpoint } from "@/features/utils/midpoint";
import type { Route } from "@/lib/data/types";

/** Scored routes by estimate (geometric midpoint), lowest first; unscored routes after, by name. */
export function sortRoutes(routes: Route[]): Route[] {
  return [...routes].sort((a, b) => {
    if (a.score && b.score) return midpoint(a.score) - midpoint(b.score);
    if (a.score) return -1;
    if (b.score) return 1;
    return a.slug.localeCompare(b.slug);
  });
}
