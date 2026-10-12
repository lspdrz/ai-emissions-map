/** Carbon bands 1–5. Classes are full literals so Tailwind finds them; colors are the @theme tokens in
 *  app/globals.css. White text on the two darkest bands. */
export const BAND_CHIP_CLASSES = [
  "bg-band-1 text-ink",
  "bg-band-2 text-ink",
  "bg-band-3 text-ink",
  "bg-band-4 text-white",
  "bg-band-5 text-white",
] as const;

/** The faint shades drawn behind range bars, one per band. */
export const BAND_SHADE_VARS = ["--color-shade-1", "--color-shade-2", "--color-shade-3", "--color-shade-4", "--color-shade-5"] as const;
