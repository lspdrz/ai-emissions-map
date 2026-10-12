/** Every carbon score is an estimate from two models: EcoLogits for energy and embodied emissions, and the
 *  grid data for carbon intensity. Named wherever scores appear (spec §10). */
export function EstimateLabel({ gridName }: { gridName: string }) {
  // One string, so the exported HTML holds the phrase whole (no React text-node marker inside it).
  return <span className="text-sm text-muted">{`Estimate (EcoLogits × ${gridName})`}</span>;
}
