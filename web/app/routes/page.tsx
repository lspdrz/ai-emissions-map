import type { Metadata } from "next";
import { AllRoutes } from "@/features/routes/ui";

export const metadata: Metadata = { title: "All routes" };

export default function RoutesPage() {
  return <AllRoutes />;
}
