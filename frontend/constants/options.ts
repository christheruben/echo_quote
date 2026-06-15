export const EFFICIENCY_OPTIONS = [
  { value: 0.18, label: "Standard (18%)" },
  { value: 0.21, label: "Premium (21%)" },
  { value: 0.23, label: "High-end (23%)" },
] as const;

export const USABLE_OPTIONS = [
  { value: 0.5, label: "50% — typical pitched" },
  { value: 0.65, label: "65% — good orientation" },
  { value: 0.8, label: "80% — flat / ideal" },
] as const;