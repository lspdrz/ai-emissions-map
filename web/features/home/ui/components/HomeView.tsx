import type { HomeData } from "@/features/home/types";
import { ContributeSection } from "@/features/home/ui/components/ContributeSection";
import { MethodSection } from "@/features/home/ui/components/MethodSection";
import { OrganizationsSection } from "@/features/home/ui/components/OrganizationsSection";
import { RoutesSection } from "@/features/home/ui/components/RoutesSection";

/** The home page: every section on one page, every number from data.json. The navbar comes from the root layout. */
export function HomeView({ homeData }: { homeData: HomeData }) {
  const { meta, routes, organizations } = homeData;
  return (
    // Sections span the screen so their top rules do; each keeps its content to the page column.
    // tabIndex -1: the navbar's name moves focus here (app/_components/Navbar.tsx), without adding a tab stop.
    <main tabIndex={-1} className="outline-none">
      <div className="page-container">
        <p className="mt-0.5 max-w-[400px] text-[15px] leading-[1.6] text-body">
          is an open source project tracking the carbon emissions of AI deployments across the world.
        </p>
      </div>
      <RoutesSection routes={routes} bandUpper={meta.band_upper} />
      <OrganizationsSection organizations={organizations} />
      <MethodSection meta={meta} />
      <ContributeSection />
    </main>
  );
}
