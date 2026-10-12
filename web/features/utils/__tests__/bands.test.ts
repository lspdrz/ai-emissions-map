import { describe, expect, it } from "vitest";
import { bandLabel, bandRanges } from "@/features/utils/bands";

describe("bands", () => {
  it("labels a band or a band span", () => {
    expect(bandLabel([4, 5])).toBe("4–5");
    expect(bandLabel([5, 5])).toBe("5");
    expect(bandLabel(null)).toBe("Not scored");
  });
  it("describes each band's range from the release's band edges", () => {
    expect(bandRanges([0.03, 0.1, 0.3, 1])).toEqual(
      ["below 0.03 g", "0.03 to 0.1 g", "0.1 to 0.3 g", "0.3 to 1 g", "1 g or more"]);
  });
});
