"use client";

import Link from "next/link";
import { type MouseEvent, useEffect, useState } from "react";
import { REPO_URL } from "@/lib/links";

/** The navbar's links, in display order. The sections are on the home page, so they work from any page; the
 *  external one opens in a new tab. */
export const NAV_LINKS = [
  { href: "/#routes", label: "Routes" },
  { href: "/#organizations", label: "Organizations" },
  { href: "/#method", label: "Method" },
  { href: "/#contribute", label: "Contribute" },
  { href: REPO_URL, label: "GitHub ↗", external: true },
] as const;

/** On the home page the name scrolls back to the top and drops any #section from the URL; Link alone would keep the
 *  scroll position, since the page is already showing. Elsewhere it navigates home as usual. */
function backToTop(e: MouseEvent<HTMLAnchorElement>) {
  if (window.location.pathname !== "/") return;
  e.preventDefault();
  window.history.replaceState(null, "", "/");
  window.scrollTo({ top: 0 });
}

/** The site's navbar, on every page: sticky across the full width, its bottom rule appearing once the page has
 *  scrolled. The rule is on the outer bar so it spans the screen; the row inside keeps to the page column. */
export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className={`sticky top-0 z-10 border-b bg-ground ${scrolled ? "border-ink" : "border-transparent"}`}>
      <header className="page-container flex flex-wrap items-center justify-between gap-4 pt-7 pb-1.5">
        <Link href="/" onClick={backToTop} className="text-[17px] font-semibold tracking-[-0.01em] no-underline">
          AI Emissions Map
        </Link>
        <nav aria-label="Main" className="flex flex-wrap gap-7 text-[15px]">
          {NAV_LINKS.map((l) =>
            "external" in l ? (
              <a key={l.href} href={l.href} target="_blank" rel="noopener noreferrer" className="no-underline">
                {l.label}
              </a>
            ) : (
              <Link key={l.href} href={l.href} className="no-underline">
                {l.label}
              </Link>
            ),
          )}
        </nav>
      </header>
    </div>
  );
}
