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
 *  fragment, or when it has none and the page is the one showing. Focus moves with the jump, as it does for a native
 *  fragment link, so the next Tab continues from the section. A click with a modifier key or another button is left
 *  to the browser (new tab, new window), and elsewhere the links navigate home as usual. */
export function goToSection(e: MouseEvent<HTMLAnchorElement>) {
  if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  if (window.location.pathname !== "/") return;
  e.preventDefault();
  const { hash } = new URL(e.currentTarget.href);
  window.history.replaceState(null, "", hash ? `/${hash}` : "/");
  const target = hash ? document.getElementById(hash.slice(1)) : document.querySelector("main");
  if (hash) target?.scrollIntoView();
  else window.scrollTo({ top: 0 });
  target?.focus({ preventScroll: true });
}

type NavLink = (typeof NAV_LINKS)[number];

/** One navbar link: external ones open a new tab; the others go to their section. `onNavigate` lets the phone menu
 *  close itself after a choice. */
function NavItem({ link, className, onNavigate }: { link: NavLink; className: string; onNavigate?: () => void }) {
  if ("external" in link) {
    return (
      <a href={link.href} target="_blank" rel="noopener noreferrer" onClick={onNavigate} className={className}>
        {link.label}
      </a>
    );
  }
  return (
    <Link
      href={link.href}
      onClick={(e) => {
        goToSection(e);
        onNavigate?.();
      }}
      className={className}
    >
      {link.label}
    </Link>
  );
}

/** Three lines, or a cross while the menu is open. */
function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg aria-hidden="true" width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.5">
      {open ? <path d="M5 5l12 12M17 5L5 17" /> : <path d="M3 6h16M3 11h16M3 16h16" />}
    </svg>
  );
}

/** Phones get the menu at this width and below, the same breakpoint as the routes table. */
const DESKTOP = "(min-width: 761px)";

/**
 * The site's navbar, on every page: sticky across the full width, its bottom rule appearing once the page has
 * scrolled (or the menu is open). The rule is on the outer bar so it spans the screen; the row inside keeps to the
 * page column. On phones the links fold into a menu button; the menu closes on a choice, on a press outside it, on
 * Escape, or when the window widens to desktop. `initialOpen` lets a test render the open menu; the page always starts closed.
 */
export function Navbar({ initialOpen = false }: { initialOpen?: boolean }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Publishes the bar's height as --navbar-height, which globals.css uses as the page's scroll padding, so a /#section
  // link lands below the bar. Measured, because the links wrap onto more rows on narrow screens. (The phone menu
  // drops over the page, so it never counts.)
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

  const [open, setOpen] = useState(initialOpen);
  const button = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      setOpen(false);
      button.current?.focus();
    };
    // A press anywhere outside the button and its list closes the menu; the button itself toggles it.
    const onPress = (e: PointerEvent) => {
      if (!menu.current?.contains(e.target as Node)) setOpen(false);
    };
    const desktop = window.matchMedia(DESKTOP);
    const onWiden = () => desktop.matches && setOpen(false);
    window.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPress);
    desktop.addEventListener("change", onWiden);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPress);
      desktop.removeEventListener("change", onWiden);
    };
  }, [open]);

  return (
    <div ref={bar} className={`sticky top-0 z-10 border-b bg-ground ${scrolled || open ? "border-ink" : "border-transparent"}`}>
      <header className="page-container flex items-center justify-between gap-4 pt-7 pb-1.5">
        <Link href="/" onClick={goToSection} className="text-[17px] font-semibold tracking-[-0.01em] no-underline">
          AI Emissions Map
        </Link>
        {/* Inline links: shown above 760px, hidden at 760px and below. */}
        <nav aria-label="Main" className="flex flex-wrap gap-7 text-[15px] max-[760px]:hidden">
          {NAV_LINKS.map((l) => (
            <NavItem key={l.href} link={l} className="no-underline" />
          ))}
        </nav>
        {/* Phone menu, the button and the list it opens: hidden above 760px, shown at 760px and below. The list
            drops over the page from the bar's bottom rule (the sticky bar is its containing block). */}
        <div ref={menu} className="hidden max-[760px]:block">
          <button
            ref={button}
            type="button"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen(!open)}
            className="-my-2.5 -mr-2.5 flex size-11 cursor-pointer items-center justify-center"
          >
            <MenuIcon open={open} />
          </button>
          {open && (
            <nav
              id="mobile-menu"
              aria-label="Main"
              className="absolute inset-x-0 top-[calc(100%+1px)] border-b border-ink bg-ground"
            >
              <div className="page-container flex flex-col pt-3 pb-3">
                {NAV_LINKS.map((l) => (
                  <NavItem
                    key={l.href}
                    link={l}
                    onNavigate={() => setOpen(false)}
                    className="flex min-h-11 items-center border-t border-rule text-[17px] no-underline first:border-t-0"
                  />
                ))}
              </div>
            </nav>
          )}
        </div>
      </header>
    </div>
  );
}
