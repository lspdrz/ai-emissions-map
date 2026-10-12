"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_LINKS } from "@/app/_constants/navLinks";

/** The header: the map's name and its sections. A section is marked current on its own page and its
 *  sub-pages (an organization's page marks Organizations). */
export function Nav() {
  const pathname = usePathname();
  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    const base = href.replace(/\/$/, "");
    return pathname === base || pathname.startsWith(`${base}/`);
  };
  return (
    <header className="border-b border-rule">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-x-8 gap-y-4 px-6 py-[18px]">
        <Link href="/" className="font-serif text-2xl font-semibold text-ink no-underline">AI Emissions Map</Link>
        <nav aria-label="Main" className="flex flex-wrap gap-x-6 gap-y-2 text-[15px]">
          {NAV_LINKS.map((l) => (
            <Link key={l.href} href={l.href} aria-current={isActive(l.href) ? "page" : undefined}
                  className={`py-2.5 no-underline ${isActive(l.href) ? "font-semibold text-ink" : ""}`}>
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
