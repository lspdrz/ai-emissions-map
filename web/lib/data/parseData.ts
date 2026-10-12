import { SCHEMA, type MapData } from "@/lib/data/types";

function fail(message: string): never {
  throw new Error(`data.json: ${message}. Regenerate it with \`uv run python -m build.export\`.`);
}

/** Checks the contract the pages rely on; a malformed file fails the build, never a page. */
export function parseData(raw: unknown): MapData {
  if (typeof raw !== "object" || raw === null) fail("not a JSON object");
  const data = raw as MapData;
  if (data.schema !== SCHEMA) fail(`schema is ${JSON.stringify(data.schema)}, expected "${SCHEMA}"`);
  if (typeof data.meta !== "object" || data.meta === null) fail("no meta");
  for (const key of ["organizations", "models", "routes"] as const) {
    if (!Array.isArray(data[key])) fail(`${key} is not a list`);
  }
  const orgs = new Set(data.organizations.map((o) => o.slug));
  for (const r of data.routes) {
    if (!r.label) fail(`route ${r.slug} has no label`);
    if (!orgs.has(r.org)) fail(`route ${r.slug} names organization ${r.org}, which is not in the file`);
  }
  return data;
}
