import { BAND_CHIP_CLASSES } from "@/features/constants/bands";
import { bandLabel } from "@/features/utils/bands";

/** A carbon band or band span, colored by its higher band. */
export function BandChip({ band }: { band: [number, number] | null }) {
  if (!band) return <span className="text-sm text-muted">Not scored</span>;
  return (
    <span className={`inline-flex h-[30px] min-w-11 items-center justify-center rounded px-2 font-mono font-medium ${BAND_CHIP_CLASSES[band[1] - 1]}`}>
      {bandLabel(band)}
    </span>
  );
}
