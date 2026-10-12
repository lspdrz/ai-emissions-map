/** A band or band span in words: "5", "4–5", or "Not scored". */
export function bandLabel(band: [number, number] | null): string {
  if (!band) return "Not scored";
  return band[0] === band[1] ? String(band[0]) : `${band[0]}–${band[1]}`;
}

/** Each band's range in words, from the release's band edges (meta.band_upper). */
export function bandRanges(upper: number[]): string[] {
  return [
    `below ${upper[0]} g`,
    ...upper.slice(1).map((u, i) => `${upper[i]} to ${u} g`),
    `${upper[upper.length - 1]} g or more`,
  ];
}
