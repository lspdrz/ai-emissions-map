import "server-only";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BandChip } from "@/features/components/BandChip";
import { LetterBadge } from "@/features/components/LetterBadge";
import { OrganizationCard } from "@/features/components/OrganizationCard";
import { ORG_TYPES } from "@/features/constants/letters";
import { readableQuotes } from "@/features/organizations/lib/readableQuotes";
import { spreadSegments } from "@/features/organizations/lib/spreadSegments";
import { fmtRange } from "@/features/utils/formatGrams";
import { loadData } from "@/lib/data/loadData";

export function organizationSlugs(): string[] {
  return loadData().organizations.map((o) => o.slug);
}

export function organizationName(slug: string): string | null {
  return loadData().organizations.find((o) => o.slug === slug)?.display_name ?? null;
}

export function OrganizationsList() {
  const data = loadData();
  return (
    <>
      <section className="flex max-w-[820px] flex-col gap-4">
        <h1 className="font-serif text-5xl leading-[1.1] font-medium">Organizations</h1>
        <p className="text-lg leading-relaxed text-body">Each organization is rated on how precisely its own
          publications say where its routes run: the average of all its routes, shown with their spread.</p>
      </section>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(340px,1fr))] gap-6">
        {data.organizations.map((o) => <OrganizationCard key={o.slug} org={o} />)}
      </div>
    </>
  );
}

const TH = "bg-panel px-4 py-3 text-left text-[13px] font-semibold text-muted";
const TD = "border-t border-rule px-4 py-3";

export function OrganizationProfile({ slug }: { slug: string }) {
  const data = loadData();
  const org = data.organizations.find((o) => o.slug === slug);
  if (!org) notFound();
  const routes = org.routes.map((name) => data.routes.find((r) => r.slug === name)!);
  const quotes = org.evidence.flatMap((e) => readableQuotes(e.quotes).map((q) => ({ q, e })));
  return (
    <>
      <section className="flex flex-wrap items-start gap-x-12 gap-y-8">
        <div className="flex min-w-0 flex-[999_1_560px] flex-col gap-4">
          <p className="text-sm text-muted"><Link href="/organizations/">Organizations</Link> / {org.display_name}</p>
          <h1 className="font-serif text-[52px] leading-[1.08] font-medium">{org.display_name}</h1>
          {org.description && <p className="text-[19px] leading-relaxed text-body">{org.description}</p>}
          <p className="text-sm text-muted">{ORG_TYPES[org.type] ?? org.type}{org.country && ` · ${org.country}`} ·{" "}
            <a href={org.homepage}>{org.homepage.replace(/^https?:\/\//, "")}</a></p>
        </div>
        <div className="flex flex-[1_1_300px] flex-col gap-4 rounded-md border border-rule p-6">
          <span className="text-[13px] font-semibold tracking-[0.06em] text-muted">LOCATION DISCLOSURE</span>
          <div className="flex items-center gap-4">
            <LetterBadge letter={org.rating.letter} size="xl" />
            <span className="leading-relaxed text-body">{org.rating.summary}</span>
          </div>
          <div role="img" aria-label={`Spread: ${org.rating.summary}`} className="flex h-2.5 gap-0.5 overflow-hidden rounded-[5px]">
            {spreadSegments(org.rating.spread).map((s) => (
              <span key={s.letter} style={{ flex: s.count, background: `rgba(20,24,31,${s.opacity})` }} />
            ))}
          </div>
          <span className="text-[13px] text-muted">Pre-publication notice: {org.notified ? `sent ${org.notified}` : "not yet sent"}</span>
        </div>
      </section>

      {quotes.length > 0 && (
        <section className="flex flex-col gap-5">
          <h2 className="font-serif text-[32px] font-medium">What {org.display_name} discloses</h2>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-6">
            {quotes.map(({ q, e }) => (
              <figure key={`${e.url}-${q}`} className="m-0 flex flex-col gap-3 border-t-[3px] border-ink pt-4">
                <blockquote className="m-0 font-serif text-xl leading-snug">“{q}”</blockquote>
                <figcaption className="text-sm text-muted"><a href={e.url}>{new URL(e.url).hostname}</a> · checked {e.accessed}</figcaption>
              </figure>
            ))}
          </div>
        </section>
      )}

      <section className="flex flex-col gap-5">
        <h2 className="font-serif text-[32px] font-medium">Routes</h2>
        <div className="overflow-x-auto rounded-md border border-rule">
          <table className="w-full min-w-[860px] border-collapse text-[15px]">
            <thead><tr><th scope="col" className={TH}>Where it runs</th><th scope="col" className={TH}>Disclosure</th>
              <th scope="col" className={TH}>What is missing</th><th scope="col" className={TH}>g CO₂e / 1k tokens</th>
              <th scope="col" className={TH}>Band</th></tr></thead>
            <tbody>
              {routes.map((r) => (
                <tr key={r.slug}>
                  <td className={TD}>{r.label}{r.default && <span className="ml-2 rounded-[3px] border border-[#a7b0bc] px-1.5 text-xs font-semibold text-muted">DEFAULT</span>}</td>
                  <td className={TD}><LetterBadge letter={r.letter} /></td>
                  <td className={`${TD} text-sm text-body`}>{r.gap ?? "Nothing: the facility is named."}</td>
                  <td className={`${TD} font-mono`}>{r.score ? fmtRange(r.score) : "Not scored"}</td>
                  <td className={TD}><BandChip band={r.band} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Evidence that only re-verification needs (no readable quote) is still linked. */}
        <p className="text-sm text-muted">Sources: {org.evidence.map((e, i) => (
          <span key={e.url}>{i > 0 && " · "}<a href={e.url}>{new URL(e.url).pathname.replace(/\/$/, "") || new URL(e.url).hostname}</a></span>
        ))}</p>
      </section>

      <section className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-10">
        {org.rating.letter !== "A" && (
          <div className="flex flex-col gap-3">
            <h2 className="font-serif text-[26px] font-medium">How {org.display_name} could reach A</h2>
            <p className="leading-relaxed text-body">Name the data centers that serve each route, for example in a
              serving-locations file on its own domain. Committing each route to a named cloud region would already raise
              it to B.</p>
          </div>
        )}
        <div className="flex flex-col gap-3">
          <h2 className="font-serif text-[26px] font-medium">{org.display_name}&apos;s response</h2>
          <p className="leading-relaxed text-body">No response yet. Every organization is sent its draft entry and evidence
            30 days before it first appears, and may publish a statement of up to 300 words here.</p>
        </div>
      </section>
    </>
  );
}
