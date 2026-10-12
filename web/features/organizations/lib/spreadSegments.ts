import { LETTERS } from "@/features/constants/letters";

/** The rating spread as a bar: one segment per letter present, A to E, darker for better disclosure. */
export function spreadSegments(spread: Record<string, number>) {
  return LETTERS.filter((l) => spread[l.letter]).map((l) => ({
    letter: l.letter, count: spread[l.letter], opacity: 0.25 + 0.15 * l.value,
  }));
}
