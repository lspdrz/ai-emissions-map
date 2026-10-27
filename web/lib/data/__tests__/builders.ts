import type { MapData, Meta, Model, Organization, Route } from "@/lib/data/types";
import { SCHEMA } from "@/lib/data/types";

/** Records valid by construction: each builder fills what a test doesn't care about, and a test overrides what it
 *  does. Like tests/builders/ in the Python pipeline. */

export function buildRoute(o: Partial<Route> = {}): Route {
  return {
    slug: "acme-m", org: "acme", model: "m", label: "Somewhere", default: false, letter: "B", gap: null,
    sci: { low: 0.1, high: 0.2 }, energy: { low: 0.5, high: 0.6 }, grid_intensity: null,
    embodied: { low: 0.05, high: 0.05 }, band: null, served_as: null, ...o,
  };
}

export function buildOrganization(o: Partial<Organization> = {}): Organization {
  return {
    slug: "acme", display_name: "Acme", type: "inference_host", country: null, homepage: "https://acme.example",
    description: null, rating: { letter: "B", mean: 2, spread: { B: 1 }, summary: "B (1 route at B)" },
    routes: [], evidence: [], ...o,
  };
}

export function buildModel(o: Partial<Model> = {}): Model {
  return { slug: "m", display_name: "M", architecture: null, active_b: null, total_b: null, ...o };
}

export function buildMeta(o: Partial<Meta> = {}): Meta {
  return {
    release_date: "2026-10-22", inputs_sha: "0".repeat(64), methodology_version: "0.1.0", ecologits_version: "0.11.2",
    pue: [1.1, 1.6], band_upper: [0.03, 0.1, 0.3, 1.0], draft: true, grid: { source: "Ember", year: 2025 },
    counts: { organizations: 0, routes: 0, models: 0, grids: 0 }, grid_intensity_spread: null, featured_model: null, ...o,
  };
}

/** A whole file. Every organization a route names, and not given, is added. Models are not: a route may name a
 *  model with no record, which the site shows by its slug. */
export function buildData(o: { routes?: Route[]; organizations?: Organization[]; models?: Model[]; meta?: Partial<Meta> } = {}): MapData {
  const routes = o.routes ?? [];
  const organizations = [...(o.organizations ?? [])];
  for (const r of routes) {
    if (!organizations.some((org) => org.slug === r.org)) organizations.push(buildOrganization({ slug: r.org, display_name: r.org }));
  }
  return { schema: SCHEMA, meta: buildMeta(o.meta), organizations, models: o.models ?? [], routes };
}
