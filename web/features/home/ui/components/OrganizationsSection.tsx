"use client";

import { useState } from "react";
import type { OrgCard as Card } from "@/features/home/types";
import { OrgCard } from "@/features/home/ui/components/OrgCard";
import { SearchInput } from "@/features/home/ui/components/SearchInput";
import { matchesQuery } from "@/features/home/utils/routesTable";

/** Every organization as a card, best rated first, searchable by name. `initialQuery` lets a test render a search. */
export function OrganizationsSection({ organizations, initialQuery = "" }: { organizations: Card[]; initialQuery?: string }) {
  const [query, setQuery] = useState(initialQuery);
  const shown = organizations.filter((c) => matchesQuery(c.name, query));

  return (
    // The rule spans the screen; the content keeps to the page column.
    <section id="organizations" className="border-t border-ink">
      <div className="page-container flex flex-col gap-10 pt-14 pb-[88px]">
        <div className="flex flex-col gap-3">
          <h2 className="text-[32px] font-medium tracking-[-0.02em]">Organizations</h2>
          <p className="max-w-[640px] text-[17px] leading-[1.55] text-body">
            Each organization’s location disclosure rating is the average of its routes’ ratings, from A (names the
            facility) to D (undisclosed).
          </p>
        </div>

        <div className="-mb-2">
          <SearchInput id="org-search" label="Search organizations" placeholder="Organization name" value={query} onChange={setQuery} />
        </div>

        {shown.length === 0 && <p className="text-[15px] text-muted">No organizations match “{query.trim()}”.</p>}
        <div className="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-8">
          {shown.map((c) => (
            <OrgCard key={c.slug} card={c} />
          ))}
        </div>
      </div>
    </section>
  );
}
