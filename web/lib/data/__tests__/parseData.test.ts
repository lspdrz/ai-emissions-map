import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parseData } from "@/lib/data/parseData";

const fixture = () => JSON.parse(readFileSync(new URL("fixtures/data.json", import.meta.url), "utf8"));

describe("parseData", () => {
  it("accepts the current contract", () => {
    expect(parseData(fixture()).routes[0].slug).toBe("acme-m");
  });
  it("rejects another contract version, naming the expected one", () => {
    expect(() => parseData({ ...fixture(), schema: "aem-data/0" })).toThrow(/aem-data\/1/);
  });
  it("rejects a route whose organization is missing", () => {
    const raw = fixture();
    raw.routes[0].org = "nobody";
    expect(() => parseData(raw)).toThrow(/acme-m.*nobody/);
  });
  it("rejects a route without a label", () => {
    const raw = fixture();
    delete raw.routes[0].label;
    expect(() => parseData(raw)).toThrow(/acme-m.*label/);
  });
});
