import { readFileSync } from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { OrganizationList } from "@/features/overview/ui/components/OrganizationList";
import { parseData } from "@/lib/data/parseData";

const fixture = () =>
  parseData(JSON.parse(readFileSync(path.join(process.cwd(), "lib/data/__tests__/fixtures/data.json"), "utf8")));

describe("OrganizationList", () => {
  it("shows each organization's rating with its spread", () => {
    expect(renderToStaticMarkup(<OrganizationList organizations={fixture().organizations} />)).toContain(
      "C (1 route at C)",
    );
  });

  it("links the name to the homepage and gives the type and country in words", () => {
    const html = renderToStaticMarkup(<OrganizationList organizations={fixture().organizations} />);
    expect(html).toContain('href="https://acme.example"');
    expect(html).toContain("Inference host · CH");
  });

  it("shows the description when there is one", () => {
    const orgs = fixture().organizations;
    orgs[0].description = "Names its data centers.";
    expect(renderToStaticMarkup(<OrganizationList organizations={orgs} />)).toContain("Names its data centers.");
  });
});
