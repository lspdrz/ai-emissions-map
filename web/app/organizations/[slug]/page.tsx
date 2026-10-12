import type { Metadata } from "next";
import { OrganizationProfile, organizationName, organizationSlugs } from "@/features/organizations/ui";

export function generateStaticParams() {
  return organizationSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: PageProps<"/organizations/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  return { title: organizationName(slug) ?? "Organization" };
}

export default async function OrganizationPage({ params }: PageProps<"/organizations/[slug]">) {
  const { slug } = await params;
  return <OrganizationProfile slug={slug} />;
}
