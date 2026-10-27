import type { HomeData } from "@/features/home/types";
import { RoutesSection } from "@/features/home/ui/components/RoutesSection";

/** The home page: every section on one page, every number from data.json. The navbar comes from the root layout. */
export function HomeView({ homeData }: { homeData: HomeData }) {
  const { meta, routes } = homeData;
  return (
    <main className="page-container">
      <p className="mt-0.5 max-w-[400px] text-[15px] leading-[1.6] text-body">
        is an open source project tracking the carbon emissions of AI deployments across the world.
      </p>
      <RoutesSection rows={routes} bandUpper={meta.band_upper} />
    </main>
  );
}
