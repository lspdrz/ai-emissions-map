import "server-only";
import { readFileSync } from "node:fs";
import path from "node:path";
import { parseData } from "@/lib/data/parseData";
import type { MapData } from "@/lib/data/types";

const DATA_DIR = path.join(process.cwd(), "data");

/** Reads and checks data/data.json at build time. */
export function loadData(file = path.join(DATA_DIR, "data.json")): MapData {
  return parseData(JSON.parse(readFileSync(file, "utf8")));
}

/** data/methodology.md, copied from docs/methodology.md by `build.export` with its placeholders filled. */
export function loadMethodology(file = path.join(DATA_DIR, "methodology.md")): string {
  return readFileSync(file, "utf8");
}
