"use client";

import { useReducer } from "react";
import type { RouteRow, SortKey } from "@/features/home/types";
import { ChartHeader } from "@/features/home/ui/components/ChartHeader";
import { Pagination } from "@/features/home/ui/components/Pagination";
import { RangeCell, RangeNumbers } from "@/features/home/ui/components/RangeCell";
import { SearchInput } from "@/features/home/ui/components/SearchInput";
import {
  DEFAULT_SORT, filterRows, pageLabel, pageOf, sortRows, tableReducer,
} from "@/features/home/utils/routesTable";
import { niceScale } from "@/features/home/utils/scale";

/** Three columns on desktop (name, letter, chart); on phones the chart gives way to a plain numbers column, which
 *  desktop never shows. Header and rows share it so the columns line up. */
const GRID =
  "grid grid-cols-[300px_68px_minmax(0,1fr)] gap-x-8 max-[760px]:grid-cols-[minmax(0,1fr)_76px_96px] max-[760px]:gap-x-3";
const HEADER_BUTTON = "flex min-h-8 cursor-pointer flex-col justify-end pb-1.5";

/**
 * Every route, searchable, sortable and paged. The scale comes from all routes (not the page shown) so bars stay put
 * while the reader searches. `initialQuery` lets a test render a search; the page always starts empty.
 */
export function RoutesSection({ routes, bandUpper, initialQuery = "" }: {
  routes: RouteRow[]; bandUpper: number[]; initialQuery?: string;
}) {
  const scale = niceScale(routes.flatMap((r) => (r.score ? [r.score] : [])));
  const [state, dispatch] = useReducer(tableReducer, { query: initialQuery, sort: DEFAULT_SORT, page: 0 });
  const matches = sortRows(filterRows(routes, state.query), state.sort);
  const shown = pageOf(matches, state.page);

  // The arrow is for the eye; screen readers hear the state in words, on the active column only.
  const sortMark = (key: SortKey) => (
    <>
      <span aria-hidden="true"> {state.sort.key !== key ? "↕" : state.sort.dir === 1 ? "↑" : "↓"}</span>
      {state.sort.key === key && (
        <span className="sr-only">, sorted {state.sort.dir === 1 ? "ascending" : "descending"}</span>
      )}
    </>
  );
  const tone = (key: SortKey) => (state.sort.key === key ? "text-ink" : "text-muted");
  const sortBy = (key: SortKey) => () => dispatch({ type: "sort", key });

  return (
    <section id="routes" tabIndex={-1} className="page-container outline-none flex flex-col gap-8 pt-14 pb-[88px]">
      <div className="flex flex-col gap-3">
        <h2 className="text-[32px] font-medium tracking-[-0.02em]">Routes</h2>
        <p className="text-[17px] leading-[1.55] text-body">
          A route is an organization deploying a model at a location. An example is Anthropic’s (organization) Claude
          Opus 5.5 (model) deployed on servers connected to the United States’ electrical grid (location). Carbon
          emissions are measured based on the grid’s carbon intensity in a range of grams of CO₂e per 1,000 output
          tokens. Locations are rated by how public the servers’ locations are, which determines the electrical grid
          they use.
        </p>
      </div>

      <div className="-mb-2">
        <SearchInput
          id="route-search"
          label="Search routes"
          placeholder="Organization or model"
          value={state.query}
          onChange={(query) => dispatch({ type: "query", query })}
        />
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[900px] max-[760px]:min-w-0">
          <div className={`${GRID} items-end border-b border-ink pb-1.5 font-mono text-[11px] text-muted`}>
            <button type="button" onClick={sortBy("org")}
              className={`${HEADER_BUTTON} justify-self-start text-left whitespace-nowrap max-[760px]:whitespace-normal ${tone("org")}`}>
              <span>Organization · model{sortMark("org")}</span>
            </button>
            <button type="button" onClick={sortBy("letter")}
              className={`${HEADER_BUTTON} items-center justify-self-center text-center ${tone("letter")}`}>
              <span>Location</span>
              <span className="whitespace-nowrap">disclosure{sortMark("letter")}</span>
            </button>
            <button type="button" onClick={sortBy("score")}
              className={`${HEADER_BUTTON} hidden items-end justify-self-end text-right max-[760px]:flex ${tone("score")}`}>
              <span className="whitespace-nowrap">g CO₂e per</span>
              <span className="whitespace-nowrap">1k tokens{sortMark("score")}</span>
            </button>
            <ChartHeader scale={scale} label={<>g CO₂e per 1k tokens{sortMark("score")}</>} active={state.sort.key === "score"} onSort={sortBy("score")} />
          </div>

          {shown.items.map((r) => (
            <div key={r.slug} className={`${GRID} items-center border-b border-rule`}>
              <div className="min-w-0 py-[9px]">
                <div className="truncate text-sm font-medium">
                  {r.org} · {r.model}
                </div>
                <div className="truncate text-xs text-muted">{r.label}</div>
              </div>
              <div className="flex justify-center">
                <span className="flex size-[26px] items-center justify-center border border-ink font-mono text-[13px]">{r.letter}</span>
              </div>
              <div className="hidden justify-end text-right font-mono text-[13px] font-medium whitespace-nowrap max-[760px]:flex">
                <RangeNumbers score={r.score} bandUpper={bandUpper} />
              </div>
              <RangeCell score={r.score} letter={r.letter} scale={scale} bandUpper={bandUpper} />
            </div>
          ))}
        </div>
      </div>

      <Pagination
        label={pageLabel(matches.length, shown.first, shown.last, state.query)}
        page={shown.page}
        pageCount={shown.pageCount}
        onPage={(page) => dispatch({ type: "page", page })}
      />
    </section>
  );
}
