import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Pagination } from "@/features/home/ui/components/Pagination";

const noop = () => {};

describe("Pagination", () => {
  it("fills the current page and disables Prev on the first page", () => {
    const html = renderToStaticMarkup(<Pagination label="1–10 of 23 routes" page={0} pageCount={3} onPage={noop} />);
    expect(html).toContain("1–10 of 23 routes");
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*>← Prev<\/button>/);
    expect(html).toMatch(/<button[^>]*aria-current="page"[^>]*>1<\/button>/);
    expect(html).not.toMatch(/<button[^>]*disabled=""[^>]*>Next →<\/button>/);
  });

  it("disables Next on the last page", () => {
    const html = renderToStaticMarkup(<Pagination label="" page={2} pageCount={3} onPage={noop} />);
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*>Next →<\/button>/);
  });

  it("numbers every page", () => {
    const html = renderToStaticMarkup(<Pagination label="" page={0} pageCount={3} onPage={noop} />);
    expect((html.match(/aria-label="Page \d"/g) ?? []).length).toBe(3);
  });
});
