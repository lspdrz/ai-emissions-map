import { LetterBadge } from "@/features/overview/ui/components/Badges";
import type { Organization } from "@/lib/data/types";

const TYPE_TEXT: Record<string, string> = {
  model_lab: "Model lab",
  inference_host: "Inference host",
  cloud: "Cloud",
  public_compute: "Public compute",
};

export function OrganizationList({ organizations }: { organizations: Organization[] }) {
  return (
    <ul className="space-y-6">
      {organizations.map((o) => (
        <li key={o.slug}>
          <div className="flex items-center gap-3">
            <LetterBadge letter={o.rating.letter} />
            <a href={o.homepage} className="text-lg font-semibold underline-offset-2 hover:underline">
              {o.display_name}
            </a>
            <span className="text-sm text-neutral-500">
              {[TYPE_TEXT[o.type] ?? o.type, o.country].filter(Boolean).join(" · ")}
            </span>
          </div>
          <p className="mt-1 text-sm text-neutral-600">{o.rating.summary}</p>
          {o.description && <p className="mt-2">{o.description}</p>}
        </li>
      ))}
    </ul>
  );
}
