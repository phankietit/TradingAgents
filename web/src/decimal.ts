/** Expand serialized decimals for display without binary floating-point conversion. */
export function plainDecimal(value: unknown): string | null {
  if (typeof value !== 'string' || value.length > 1000) return null;
  const match = /^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(value);
  if (!match) return null;
  const exponent = Number(match[4] ?? 0);
  if (!Number.isInteger(exponent) || Math.abs(exponent) > 1000) return null;
  const digits = match[2] + (match[3] ?? '');
  const point = match[2].length + exponent;
  const expanded = point <= 0 ? `0.${'0'.repeat(-point)}${digits}`
    : point >= digits.length ? digits + '0'.repeat(point - digits.length)
    : `${digits.slice(0, point)}.${digits.slice(point)}`;
  return match[1] + expanded.replace(/^0+(?=\d)/, '');
}
