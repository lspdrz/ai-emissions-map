import { describe, expect, it } from "vitest";
import { readableQuotes } from "@/features/organizations/lib/readableQuotes";
import { spreadSegments } from "@/features/organizations/lib/spreadSegments";

describe("readableQuotes", () => {
  it("keeps sentences and drops fragments such as table row names and code", () => {
    expect(readableQuotes([
      "Requests submitted to a global endpoint may be processed in any Google Cloud location around the world",
      "Gemini 3.5 Flash ( gemini-3.5-flash )",
      "export GOOGLE_CLOUD_LOCATION = global",
      "strictly covers data residency within EU member states",
    ])).toEqual([
      "Requests submitted to a global endpoint may be processed in any Google Cloud location around the world",
      "strictly covers data residency within EU member states",
    ]);
  });
});

describe("spreadSegments", () => {
  it("orders letters A to E, darker for better disclosure", () => {
    const segments = spreadSegments({ D: 2, C: 8 });
    expect(segments.map((s) => [s.letter, s.count])).toEqual([["C", 8], ["D", 2]]);
    expect(segments[0].opacity).toBeGreaterThan(segments[1].opacity);
  });
});
