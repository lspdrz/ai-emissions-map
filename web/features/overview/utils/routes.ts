import type { Range, Route } from "@/lib/data/types";

/** The geometric midpoint of a score: the sort key only, never displayed (METHODOLOGY.md, Ranges). */
export function midpoint(r: Range): number {
  return Math.sqrt(r.low * r.high);
}

/** Scored routes from lowest to highest midpoint, then the routes that are not scored. */
export function sortRoutes(routes: Route[]): Route[] {
  return [...routes].sort((a, b) => {
    if (!a.score || !b.score) return (a.score ? 0 : 1) - (b.score ? 0 : 1);
    return midpoint(a.score) - midpoint(b.score);
  });
}

/**
 * The operational part, E × I. Each end of the score is (E × I) + M at that end, so subtracting M recovers it
 * exactly without recomputing anything the pipeline computed.
 */
export function operational(route: Route): Range | null {
  if (!route.score) return null;
  return { low: route.score.low - route.embodied.low, high: route.score.high - route.embodied.high };
}
