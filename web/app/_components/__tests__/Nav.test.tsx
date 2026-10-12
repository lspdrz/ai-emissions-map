import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { Nav } from "@/app/_components/Nav";
import { NAV_LINKS } from "@/app/_constants/navLinks";

// next/link drops the trailing slash outside a Next build (the static export adds it back), so
// hrefs are matched with or without it.
const hrefOf = (href: string) => new RegExp(`href="${href.replace(/\/$/, "")}/?"`);

vi.mock("next/navigation", () => ({ usePathname: () => "/organizations/google/" }));

describe("Nav", () => {
  it("renders the home link and one link per NAV_LINKS entry", () => {
    const html = renderToStaticMarkup(<Nav />);
    expect((html.match(/<a /g) ?? []).length).toBe(NAV_LINKS.length + 1);
    for (const { href, label } of NAV_LINKS) {
      expect(html).toMatch(hrefOf(href));
      expect(html).toContain(label);
    }
  });
  it("marks the section of the current page, including its sub-pages", () => {
    const active = (renderToStaticMarkup(<Nav />).match(/<a [^>]*aria-current="page"[^>]*>/g) ?? []);
    expect(active).toHaveLength(1);
    expect(active[0]).toMatch(hrefOf("/organizations/"));
  });
});
