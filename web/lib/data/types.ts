/** The shapes of data/data.json (contract aem-data/1), written by `uv run python -m build.export`. */
export const SCHEMA = "aem-data/1";

export type Range = { low: number; high: number };
export type Params = number | { min: number; max: number };

export interface Route {
  slug: string; org: string; model: string; label: string; default: boolean; scored: boolean;
  level: string; letter: string; gap: string | null; score: Range | null; score_lifecycle: Range | null; embodied: Range;
  band: [number, number] | null; served_as: string | null;
}
export interface Evidence { url: string; quotes: string[]; accessed: string; routes: string[] }
export interface Organization {
  slug: string; display_name: string; type: string; country: string | null; homepage: string;
  description: string | null; notified: string | null;
  rating: { letter: string | null; mean: number | null; spread: Record<string, number>; summary: string };
  routes: string[]; evidence: Evidence[];
}
export interface Model {
  slug: string; display_name: string; source: string | null; architecture: string | null;
  active_b: Params | null; total_b: Params | null;
}
export interface Meta {
  release_date: string; methodology_version: string; ecologits_version: string; pue: [number, number];
  band_upper: number[]; grid: { year: number | null; mock: boolean; attribution: string | null; name: string };
  counts: { organizations: number; routes: number; models: number; zones: number; scored: number };
  intensity_spread: number | null; featured_model: string | null;
}
export interface MapData { schema: typeof SCHEMA; meta: Meta; organizations: Organization[]; models: Model[]; routes: Route[] }
