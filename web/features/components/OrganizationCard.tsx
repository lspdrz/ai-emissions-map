import Link from "next/link";
import { LetterBadge } from "@/features/components/LetterBadge";
import type { Organization } from "@/lib/data/types";

export function OrganizationCard({ org }: { org: Organization }) {
  return (
    <Link href={`/organizations/${org.slug}/`}
          className="flex items-start gap-5 rounded-md border border-rule p-6 text-ink no-underline hover:border-muted hover:text-ink">
      <LetterBadge letter={org.rating.letter} size="lg" />
      <span className="flex flex-col gap-1.5">
        <span className="font-serif text-2xl font-semibold">{org.display_name}</span>
        <span className="text-sm text-muted">{org.rating.summary}</span>
        {org.description && <span className="leading-relaxed text-body">{org.description}</span>}
      </span>
    </Link>
  );
}
