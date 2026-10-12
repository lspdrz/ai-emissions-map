import { remark } from "remark";
import remarkGfm from "remark-gfm";
import remarkHtml from "remark-html";

const HEADING = "## Full methodology";

/** The body of docs/methodology.md's second section, which the Methodology page shows. */
export function fullMethodology(md: string): string {
  const i = md.indexOf(HEADING);
  if (i < 0) throw new Error(`methodology.md: no "${HEADING}" section. Regenerate data/ with \`uv run python -m build.export\`.`);
  return md.slice(i + HEADING.length).trim();
}

/** Markdown to HTML at build time; remark-html sanitizes the output. */
export async function renderMarkdown(md: string): Promise<string> {
  return String(await remark().use(remarkGfm).use(remarkHtml).process(md));
}
