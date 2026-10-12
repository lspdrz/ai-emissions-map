import type { Metadata } from "next";
import { Methodology } from "@/features/methodology/ui";

export const metadata: Metadata = { title: "Methodology" };

export default function MethodologyPage() {
  return <Methodology />;
}
