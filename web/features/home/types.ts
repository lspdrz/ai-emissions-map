import type { Meta, Range } from "@/lib/data/types";

/** One row of the routes table: names already resolved for display. `score` is null for a route not scored. */
export interface RouteRow {
  slug: string;
  org: string;
  model: string;
  label: string;
  letter: string;
  score: Range | null;
}

/** What the home page shows, shaped from data.json by getHomeData. */
export interface HomeData {
  meta: Meta;
  routes: RouteRow[];
}

/** The range chart's log scale: its ends, and the tick values between them (the 1–3 steps). */
export interface Scale {
  min: number;
  max: number;
  ticks: number[];
}

export type SortKey = "org" | "letter" | "score";
export interface Sort {
  key: SortKey;
  dir: 1 | -1;
}

/** The routes table's state: the search, the sort and the page (0-based). */
export interface TableState {
  query: string;
  sort: Sort;
  page: number;
}
export type TableAction =
  | { type: "query"; query: string }
  | { type: "sort"; key: SortKey }
  | { type: "page"; page: number };

/** One page of a list. `first` and `last` count from 1, and are 0 when the list is empty. */
export interface Page<T> {
  items: T[];
  page: number;
  pageCount: number;
  first: number;
  last: number;
}
