/** The quoted passages worth showing as quotations. Evidence `shows` fields also quote short fragments
 *  that matter to re-verification but read badly on a page (a table row's name, a line of code), so keep
 *  only passages of at least six words. */
export function readableQuotes(quotes: string[]): string[] {
  return quotes.filter((q) => q.split(/\s+/).filter((w) => /^[A-Za-z][A-Za-z'’-]*[.,;:]?$/.test(w)).length >= 6);
}
