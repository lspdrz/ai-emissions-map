export type Band = 1 | 2 | 3 | 4 | 5;

/** A value's carbon band: the first band whose upper edge (meta.band_upper) it is below, else band 5. An edge belongs
 *  to the band above it (METHODOLOGY.md, Bands: "from 0.03 to below 0.1"). */
export function bandOf(x: number, upper: number[]): Band {
  const i = upper.findIndex((edge) => x < edge);
  return (i === -1 ? 5 : i + 1) as Band;
}

/** Each band's range, for the legend: "< 0.03", "0.03–0.1", …, "≥ 1". */
export function bandLimits(upper: number[]): string[] {
  return [
    `< ${upper[0]}`,
    ...upper.slice(1).map((edge, i) => `${upper[i]}–${edge}`),
    `≥ ${upper[upper.length - 1]}`,
  ];
}
