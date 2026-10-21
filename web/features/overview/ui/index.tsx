import "server-only";
import { OverviewView } from "@/features/overview/ui/components/OverviewView";
import { loadData } from "@/lib/data/loadData";

/** The overview: what this release holds. Statically rendered at build time from data.json. */
export function Overview() {
  return <OverviewView data={loadData()} />;
}
