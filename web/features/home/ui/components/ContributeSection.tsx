import { CONTRIBUTING_URL, REPO_URL } from "@/lib/links";

/** How to add to the map: by pull request, with a button to the repository. */
export function ContributeSection() {
  return (
    // The rule spans the screen; the content keeps to the page column.
    <section id="contribute" className="border-t border-ink">
      <div className="page-container flex flex-wrap items-end justify-between gap-x-16 gap-y-6 pt-14 pb-[72px]">
        <div className="flex flex-[1_1_520px] flex-col gap-3">
          <h2 className="text-[32px] font-medium tracking-[-0.02em]">Contribute</h2>
          <p className="max-w-[620px] text-[17px] leading-[1.55] text-body">
            Organizations, routes, grids and models are added by pull request. See instructions on how to contribute{" "}
            <a href={CONTRIBUTING_URL} target="_blank" rel="noopener noreferrer" className="text-accent underline">
              here
            </a>
            .
          </p>
        </div>
        {/* hover:text-ground keeps the label light on the ink fill; links otherwise turn green on hover. */}
        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-12 items-center bg-ink px-[22px] text-[15px] font-medium text-ground no-underline hover:text-ground"
        >
          Open the repository ↗
        </a>
      </div>
    </section>
  );
}
