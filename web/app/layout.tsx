import type { Metadata } from "next";
import "@/app/globals.css";
import { loadData } from "@/lib/data/loadData";

export function generateMetadata(): Metadata {
  const { meta } = loadData();
  return {
    title: { default: "AI Emissions Map", template: "%s · AI Emissions Map" },
    description:
      "Carbon intensities for AI serving routes and location-disclosure ratings for the organizations that run them.",
    // A draft is never indexed: providers have not had their notice (DRAFT in build/constants/config.py).
    robots: meta.draft ? { index: false, follow: false } : undefined,
  };
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
