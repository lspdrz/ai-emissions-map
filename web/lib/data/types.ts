/** The shapes of data/data.json (contract aem-data/1), written by `uv run python -m build release`. */
export const SCHEMA = "aem-data/1";

export type Range = { low: number; high: number };
export type Params = number | { min: number; max: number };

export interface Route {
  slug: string; org: string; model: string; label: string; default: boolean;
  letter: string; gap: string | null; score: Range | null; score_lifecycle: Range | null;
  energy: Range; intensity: Range | null; embodied: Range;
  band: [number, number] | null; served_as: string | null; flags: Flags;
}
/** What a reader must be told about the grid values behind a score: each flag names the grids it concerns. */
export type Flags = Partial<Record<"gas" | "year", string[]>>;
export interface Evidence { url: string; quotes: string[]; accessed: string; routes: string[] }
export interface Organization {
  slug: string; display_name: string; type: string; country: string | null; homepage: string;
  description: string | null;
  rating: { letter: string | null; mean: number | null; spread: Record<string, number>; summary: string };
  routes: string[]; evidence: Evidence[];
}
export interface Model {
  slug: string; display_name: string; architecture: string | null;
  active_b: Params | null; total_b: Params | null;
}
export interface Meta {
  release_date: string; inputs_sha: string; methodology_version: string; ecologits_version: string; pue: [number, number];
  band_upper: number[]; draft: boolean; grid: { year: number };
  counts: { organizations: number; routes: number; models: number; grids: number };
  intensity_spread: number | null; featured_model: string | null;
}
export interface MapData { schema: typeof SCHEMA; meta: Meta; organizations: Organization[]; models: Model[]; routes: Route[] }
