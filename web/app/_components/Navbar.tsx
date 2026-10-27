"use client";

import Link from "next/link";
import { type MouseEvent, useEffect, useRef, useState } from "react";
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

/** On the home page every link scrolls itself: to its section (the URL becoming /#section), or, for the name, to the
 *  top with no fragment. Left to Link and the browser, a click does nothing when the URL already ends in that
 *  fragment, or when it has none and the page is the one showing. Elsewhere the links navigate home as usual. */
function goToSection(e: MouseEvent<HTMLAnchorElement>) {
  if (window.location.pathname !== "/") return;
  e.preventDefault();
  const { hash } = new URL(e.currentTarget.href);
  window.history.replaceState(null, "", hash ? `/${hash}` : "/");
  if (hash) document.getElementById(hash.slice(1))?.scrollIntoView();
  else window.scrollTo({ top: 0 });
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

  // Publishes the bar's height as --navbar-height, which globals.css uses as the page's scroll padding, so a /#section
  // link lands below the bar. Measured, because the links wrap onto more rows on narrow screens.
  const bar = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = bar.current;
    if (!el) return;
    const publish = () => document.documentElement.style.setProperty("--navbar-height", `${el.offsetHeight}px`);
    publish();
    // A page opened at /#section was scrolled by the browser before this ran, with no padding yet: jump again.
    if (window.location.hash) document.getElementById(window.location.hash.slice(1))?.scrollIntoView();
    const observer = new ResizeObserver(publish);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={bar} className={`sticky top-0 z-10 border-b bg-ground ${scrolled ? "border-ink" : "border-transparent"}`}>
      <header className="page-container flex flex-wrap items-center justify-between gap-4 pt-7 pb-1.5">
        <Link href="/" onClick={goToSection} className="text-[17px] font-semibold tracking-[-0.01em] no-underline">
          AI Emissions Map
        </Link>
        <nav aria-label="Main" className="flex flex-wrap gap-7 text-[15px]">
          {NAV_LINKS.map((l) =>
            "external" in l ? (
              <a key={l.href} href={l.href} target="_blank" rel="noopener noreferrer" className="no-underline">
                {l.label}
              </a>
            ) : (
              <Link key={l.href} href={l.href} onClick={goToSection} className="no-underline">
                {l.label}
              </Link>
            ),
          )}
        </nav>
      </header>
    </div>
  );
}
