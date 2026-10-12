const SIZES = { sm: "size-7 text-base", md: "size-8 text-xl", lg: "size-14 text-[32px]", xl: "size-[72px] text-[44px]" };

/** A disclosure letter: outlined and neutral, so it never reads as a carbon band. */
export function LetterBadge({ letter, size = "sm" }: { letter: string | null; size?: keyof typeof SIZES }) {
  return (
    <span role="img" aria-label={letter ? `Location disclosure ${letter}` : "Not rated"}
          className={`inline-flex flex-none items-center justify-center rounded border-2 border-ink font-serif font-semibold text-ink ${SIZES[size]}`}>
      {letter ?? "–"}
    </span>
  );
}
