import type { Metadata } from "next";
import { OrganizationsList } from "@/features/organizations/ui";

export const metadata: Metadata = { title: "Organizations" };

export default function OrganizationsPage() {
  return <OrganizationsList />;
}
