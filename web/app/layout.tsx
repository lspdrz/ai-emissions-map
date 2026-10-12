import type { Metadata } from "next";
import localFont from "next/font/local";
import "@/app/globals.css";
import { DraftBar } from "@/app/_components/DraftBar";
import { Footer } from "@/app/_components/Footer";
import { Nav } from "@/app/_components/Nav";
import { loadData } from "@/lib/data/loadData";

// Newsreader for headings, IBM Plex Sans for text, IBM Plex Mono for numbers: the agreed design.
// Self-hosted (latin subsets from Fontsource 5.3.0, SIL Open Font License; licences beside the files):
// next/font/google broke the Vercel build (vercel/next.js#99114), and this also keeps the build offline.
const newsreader = localFont({
  variable: "--font-newsreader",
  src: [
    { path: "./fonts/newsreader-latin-500-normal.woff2", weight: "500" },
    { path: "./fonts/newsreader-latin-600-normal.woff2", weight: "600" },
  ],
});
const plexSans = localFont({
  variable: "--font-plex-sans",
  src: [
    { path: "./fonts/ibm-plex-sans-latin-400-normal.woff2", weight: "400" },
    { path: "./fonts/ibm-plex-sans-latin-500-normal.woff2", weight: "500" },
    { path: "./fonts/ibm-plex-sans-latin-600-normal.woff2", weight: "600" },
  ],
});
const plexMono = localFont({
  variable: "--font-plex-mono",
  src: [
    { path: "./fonts/ibm-plex-mono-latin-400-normal.woff2", weight: "400" },
    { path: "./fonts/ibm-plex-mono-latin-500-normal.woff2", weight: "500" },
  ],
});

export const metadata: Metadata = {
  title: { default: "AI Emissions Map", template: "%s · AI Emissions Map" },
  description: "Carbon scores for AI serving routes and location-disclosure ratings for the organizations that run them.",
  robots: { index: false, follow: false }, // a draft: remove when the map goes public
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  const { meta } = loadData();
  return (
    <html lang="en" className={`${newsreader.variable} ${plexSans.variable} ${plexMono.variable}`}>
      <body>
        {meta.grid.mock && <DraftBar />}
        <Nav />
        <main className="mx-auto flex max-w-[1200px] flex-col gap-16 px-6 pt-14 pb-24">{children}</main>
        <Footer meta={meta} />
      </body>
    </html>
  );
}
