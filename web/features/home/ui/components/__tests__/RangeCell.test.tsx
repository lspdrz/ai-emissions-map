import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { RangeCell, RangeNumbers } from "@/features/home/ui/components/RangeCell";

const upper = [0.03, 0.1, 0.3, 1.0];
const scale = { min: 0.01, max: 30, ticks: [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30] };

describe("RangeCell", () => {
  it("colors each end by its band, under its own dot", () => {
    const html = renderToStaticMarkup(<RangeCell score={{ low: 0.11, high: 2.7 }} letter="C" scale={scale} bandUpper={upper} />);
    expect(html).toMatch(/class="[^"]*text-band-3[^"]*"[^>]*>0\.11</);
    expect(html).toMatch(/class="[^"]*text-band-5[^"]*"[^>]*>2\.7</);
  });

  it("writes positions with two decimals, so server and browser render the same styles", () => {
    const html = renderToStaticMarkup(<RangeCell score={{ low: 0.012498, high: 0.081 }} letter="C" scale={scale} bandUpper={upper} />);
    expect(html).not.toMatch(/\d\.\d{3,}%/);
    expect(html).toContain("left:2.79%");
  });

  it("joins close ends into one label with a grey dash", () => {
    const html = renderToStaticMarkup(<RangeCell score={{ low: 0.08, high: 0.091 }} letter="B" scale={scale} bandUpper={upper} />);
    expect(html).toMatch(/text-band-2[^>]*>0\.080<\/span><span[^>]*text-muted[^>]*>–<\/span><span[^>]*text-band-2[^>]*>0\.091</);
  });

  it("hatches an unscored D route and says the location is undisclosed", () => {
    const html = renderToStaticMarkup(<RangeCell score={null} letter="D" scale={scale} bandUpper={upper} />);
    expect(html).toContain("repeating-linear-gradient");
    expect(html).toContain("Not scored · location undisclosed");
  });

  it("says only “Not scored” for an unscored route that is not D", () => {
    const html = renderToStaticMarkup(<RangeCell score={null} letter="A" scale={scale} bandUpper={upper} />);
    expect(html).toContain(">Not scored<");
  });
});

describe("RangeNumbers", () => {
  it("shows one number when both ends print the same", () => {
    const html = renderToStaticMarkup(<RangeNumbers score={{ low: 0.3001, high: 0.3004 }} bandUpper={upper} />);
    expect(html).not.toContain("–");
    expect(html).toContain(">0.30<");
  });

  it("shows a muted dash for an unscored route", () => {
    expect(renderToStaticMarkup(<RangeNumbers score={null} bandUpper={upper} />)).toMatch(/text-muted[^>]*>—</);
  });
});
