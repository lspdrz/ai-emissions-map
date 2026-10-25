import type { Range, Route } from "@/lib/data/types";

/** The geometric midpoint of a carbon intensity: the sort key only, never displayed (METHODOLOGY.md, Ranges). */
export function midpoint(r: Range): number {
  return Math.sqrt(r.low * r.high);
}

/** Routes with a carbon intensity from lowest to highest midpoint, then the routes without one. */
export function sortRoutes(routes: Route[]): Route[] {
  return [...routes].sort((a, b) => {
    if (!a.sci || !b.sci) return (a.sci ? 0 : 1) - (b.sci ? 0 : 1);
    return midpoint(a.sci) - midpoint(b.sci);
  });
}

/**
 * The operational part, E × I. Each end of the carbon intensity is (E × I) + M at that end, so subtracting M recovers it
 * exactly without recomputing anything the pipeline computed.
 */
export function operational(route: Route): Range | null {
  if (!route.sci) return null;
  return { low: route.sci.low - route.embodied.low, high: route.sci.high - route.embodied.high };
}
