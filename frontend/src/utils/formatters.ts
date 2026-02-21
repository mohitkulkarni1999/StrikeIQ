export function toPercent(value: number): number {
  if (value === null || value === undefined) return 0;
  if (value <= 1) return value * 100;
  return value;
}
