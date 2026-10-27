import type { Metadata } from "next";
import localFont from "next/font/local";
import { Footer } from "@/app/_components/Footer";
import { Navbar } from "@/app/_components/Navbar";
import "@/app/globals.css";
import { loadData } from "@/lib/data/loadData";

// Subset from the Google Fonts variable files (Latin, punctuation, arrows); licences beside them in app/fonts/.
const instrumentSans = localFont({
  src: "./fonts/InstrumentSans.woff2",
  weight: "400 700",
  variable: "--font-instrument-sans",
});
const jetbrainsMono = localFont({
  src: "./fonts/JetBrainsMono.woff2",
  weight: "100 800",
  variable: "--font-jetbrains-mono",
});

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
    <html lang="en" className={`${instrumentSans.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-ground font-sans text-ink">
        <Navbar />
        {children}
        <Footer meta={loadData().meta} />
      </body>
    </html>
  );
}
