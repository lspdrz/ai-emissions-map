import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from "next/font/google";
import "@/app/globals.css";
import { DraftBar } from "@/app/_components/DraftBar";
import { Footer } from "@/app/_components/Footer";
import { Nav } from "@/app/_components/Nav";
import { loadData } from "@/lib/data/loadData";

// Newsreader for headings, IBM Plex Sans for text, IBM Plex Mono for numbers: the agreed design.
const newsreader = Newsreader({ variable: "--font-newsreader", subsets: ["latin"], weight: ["500", "600"] });
const plexSans = IBM_Plex_Sans({ variable: "--font-plex-sans", subsets: ["latin"], weight: ["400", "500", "600"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500"] });

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
