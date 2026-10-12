/** The location disclosure scale (A–E): what the organization's own publications establish. */
export const LETTERS = [
  { letter: "A", text: "The named data center or centers", value: 4 },
  { letter: "B", text: "A cloud or provider region", value: 3 },
  { letter: "C", text: "A single country", value: 2 },
  { letter: "D", text: "A set of possible countries", value: 1 },
  { letter: "E", text: "Nothing, or only press reports", value: 0 },
] as const;

export const ORG_TYPES: Record<string, string> = {
  model_lab: "Model lab",
  inference_host: "Inference host",
  cloud: "Cloud provider",
  public_compute: "Public compute center",
  aggregator: "Aggregator",
};
