// Checks the exported pages against the data: every page exists and says what the data says.
import { existsSync, readFileSync } from "node:fs";

const data = JSON.parse(readFileSync("data/data.json", "utf8"));
const failures = [];
const expect = (cond, message) => { if (!cond) failures.push(message); };
const page = (p) => {
  const f = `out/${p}`;
  if (!existsSync(f)) { failures.push(`missing ${f}`); return ""; }
  return readFileSync(f, "utf8");
};

// Overview
const home = page("index.html");
expect(home.includes("PLACEHOLDER GRID DATA") === data.meta.grid.mock, "draft bar shown if and only if the grid is a mock");
expect(home.includes('name="robots" content="noindex'), "draft pages are noindex");
for (const o of data.organizations) expect(home.includes(o.display_name), `overview names ${o.display_name}`);
for (const [key, label] of [["organizations", "organizations"], ["routes", "serving routes"], ["models", "models"], ["zones", "grid zones"]]) {
  // The number next to its own label, so a stray "11" elsewhere in the page cannot satisfy it.
  expect(home.includes(`>${data.meta.counts[key]}</span><span>${label}</span>`), `overview shows ${data.meta.counts[key]} ${label}`);
}

// All routes
const fmtG = (v) => (v >= 10 ? v.toFixed(1) : v >= 1 ? v.toFixed(2) : String(Number(v.toPrecision(2))));
const fmtRange = (r) => (fmtG(r.low) === fmtG(r.high) ? fmtG(r.low) : `${fmtG(r.low)}–${fmtG(r.high)}`);
const routesPage = page("routes/index.html");
expect(routesPage.includes(`Estimate (EcoLogits × ${data.meta.grid.name})`), "routes page labels scores as estimates");
for (const r of data.routes.filter((x) => x.score)) {
  expect(routesPage.includes(fmtRange(r.score)), `routes page shows ${r.slug}'s score ${fmtRange(r.score)}`);
  expect(routesPage.includes(fmtRange(r.score_lifecycle)), `routes page shows ${r.slug}'s life-cycle score`);
}
for (const r of data.routes) expect(routesPage.includes(r.label), `routes page lists ${r.slug} as "${r.label}"`);

// Organizations
const orgsPage = page("organizations/index.html");
for (const o of data.organizations) {
  expect(orgsPage.includes(o.display_name), `organizations page names ${o.display_name}`);
  const p = page(`organizations/${o.slug}/index.html`);
  expect(p.includes(o.display_name), `${o.slug} page has its name`);
  expect(p.includes(o.rating.summary), `${o.slug} page shows its rating summary`);
  for (const e of o.evidence) expect(p.includes(e.url), `${o.slug} page links ${e.url}`);
}

// Methodology
const method = page("methodology/index.html");
expect(method.includes("The carbon score"), "methodology page renders the full methodology");
expect(!/\{n_[a-z_]+\}/.test(method), "no unfilled placeholder on the methodology page");

if (failures.length) {
  console.error(failures.map((f) => `FAIL ${f}`).join("\n"));
  process.exit(1);
}
console.log("check passed: the exported pages agree with data.json");
