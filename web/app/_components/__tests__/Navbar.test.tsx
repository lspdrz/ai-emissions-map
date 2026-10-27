import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { NAV_LINKS, Navbar } from "@/app/_components/Navbar";
import { REPO_URL } from "@/lib/links";

describe("Navbar", () => {
  it("links the name to the home page, with no fragment", () => {
    expect(renderToStaticMarkup(<Navbar />)).toMatch(/<a[^>]*href="\/"[^>]*>AI Emissions Map<\/a>/);
  });

  it("opens GitHub in a new tab", () => {
    const html = renderToStaticMarkup(<Navbar />);
    const newTab = (html.match(/<a [^>]*>/g) ?? []).filter((tag) => tag.includes('target="_blank"'));
    expect(newTab).toHaveLength(1);
    expect(newTab[0]).toContain(`href="${REPO_URL}"`);
    expect(newTab[0]).toContain('rel="noopener noreferrer"');
  });

  it("renders each NAV_LINKS entry", () => {
    const html = renderToStaticMarkup(<Navbar />);
    for (const { href, label } of NAV_LINKS) {
      expect(html).toContain(`href="${href}"`);
      expect(html).toContain(label);
    }
    expect((html.match(/<a /g) ?? []).length).toBe(NAV_LINKS.length + 1);
  });

  it("hides the inline links on phones and shows a menu button there instead", () => {
    const html = renderToStaticMarkup(<Navbar />);
    expect(html).toMatch(/<nav aria-label="Main" class="[^"]*max-\[760px\]:hidden/);
    expect(html).toMatch(/<div class="hidden max-\[760px\]:block"><button[^>]*aria-expanded="false"[^>]*aria-controls="mobile-menu"[^>]*aria-label="Open menu"/);
  });

  it("renders no menu until it is opened", () => {
    expect(renderToStaticMarkup(<Navbar />)).not.toContain('id="mobile-menu"');
  });

  it("lists every link in the open menu, inside the phone-only wrapper, and the button offers to close it", () => {
    const html = renderToStaticMarkup(<Navbar initialOpen />);
    expect(html).toMatch(/<div class="hidden max-\[760px\]:block">[\s\S]*id="mobile-menu"[\s\S]*<\/nav><\/div><\/header>/);
    const menu = html.slice(html.indexOf('id="mobile-menu"'));
    for (const { href } of NAV_LINKS) expect(menu).toContain(`href="${href}"`);
    expect(html).toMatch(/<button[^>]*aria-expanded="true"[^>]*aria-label="Close menu"/);
  });

  it("starts with no bottom line", () => {
    const html = renderToStaticMarkup(<Navbar />);
    expect(html).toContain("border-transparent");
    expect(html).not.toContain("border-ink");
  });
});
