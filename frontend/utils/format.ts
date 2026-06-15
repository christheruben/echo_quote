export function fmt(sym: string, val: number) {
  if (!isFinite(val)) return `${sym}—`;

  if (val >= 1_000_000) {
    return `${sym}${(val / 1_000_000).toFixed(2)}M`;
  }

  if (val >= 1_000) {
    return `${sym}${(val / 1_000).toFixed(1)}k`;
  }

  return `${sym}${Math.round(val)}`;
}