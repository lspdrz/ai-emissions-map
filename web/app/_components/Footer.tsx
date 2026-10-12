import type { Meta } from "@/lib/data/types";

export function Footer({ meta }: { meta: Meta }) {
  return (
    <footer className="border-t border-rule bg-panel">
      <div className="mx-auto flex max-w-[1200px] flex-wrap gap-x-10 gap-y-3 px-6 py-8 text-sm leading-relaxed text-muted">
        <span>{meta.grid.mock ? "Draft release" : "Release"} {meta.release_date} · methodology {meta.methodology_version}
          {" "}· EcoLogits {meta.ecologits_version} · PUE {meta.pue[0]}–{meta.pue[1]}</span>
        {meta.grid.attribution && <span>Grid data: {meta.grid.attribution}</span>}
        <span>Serving only. Training emissions are not assessed in this version.</span>
      </div>
    </footer>
  );
}
