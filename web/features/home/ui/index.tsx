import "server-only";
import { HomeView } from "@/features/home/ui/components/HomeView";

/** The home page. Statically rendered at build time from data.json. */
export function Home() {
  return <HomeView />;
}
