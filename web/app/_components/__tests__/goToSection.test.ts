import { afterEach, describe, expect, it, vi } from "vitest";
import { goToSection } from "@/app/_components/Navbar";

/** A click on a navbar link, with the browser's window and document stubbed: tests run in Node, without a DOM. */
function setUp(pathname: string) {
  const section = { scrollIntoView: vi.fn(), focus: vi.fn() };
  const main = { focus: vi.fn() };
  vi.stubGlobal("window", { location: { pathname }, history: { replaceState: vi.fn() }, scrollTo: vi.fn() });
  vi.stubGlobal("document", { getElementById: vi.fn(() => section), querySelector: vi.fn(() => main) });
  const click = (href: string, keys: Partial<{ metaKey: boolean; ctrlKey: boolean; shiftKey: boolean; altKey: boolean; button: number }> = {}) => {
    const e = { button: 0, metaKey: false, ctrlKey: false, shiftKey: false, altKey: false, ...keys, preventDefault: vi.fn(), currentTarget: { href } };
    goToSection(e as never);
    return e;
  };
  return { section, main, click };
}

afterEach(() => vi.unstubAllGlobals());

describe("goToSection", () => {
  it("scrolls to the section, sets /#section and moves focus there, on the home page", () => {
    const { section, click } = setUp("/");
    const e = click("http://localhost/#method");
    expect(e.preventDefault).toHaveBeenCalled();
    expect(window.history.replaceState).toHaveBeenCalledWith(null, "", "/#method");
    expect(section.scrollIntoView).toHaveBeenCalled();
    expect(section.focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it("goes to the top with no fragment, and focuses the page's main content, for the name", () => {
    const { main, click } = setUp("/");
    click("http://localhost/");
    expect(window.history.replaceState).toHaveBeenCalledWith(null, "", "/");
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 0 });
    expect(main.focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it("leaves a modified or non-primary click to the browser, so it can open a new tab or window", () => {
    const { click } = setUp("/");
    for (const keys of [{ metaKey: true }, { ctrlKey: true }, { shiftKey: true }, { altKey: true }, { button: 1 }]) {
      expect(click("http://localhost/#method", keys).preventDefault).not.toHaveBeenCalled();
    }
  });

  it("leaves navigation to Link on any other page", () => {
    const { click } = setUp("/about/");
    expect(click("http://localhost/#method").preventDefault).not.toHaveBeenCalled();
  });
});
