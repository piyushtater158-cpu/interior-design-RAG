export function revLabel(index: number) {
  return `rev.${String(index + 1).padStart(2, '0')}`;
}

export function timestamp(ms: number) {
  const delta = Date.now() - ms;
  if (delta < 60_000) return 'just now';
  if (delta < 3_600_000) return `${Math.floor(delta / 60_000)}m ago`;
  if (delta < 86_400_000) return `${Math.floor(delta / 3_600_000)}h ago`;
  return `${Math.floor(delta / 86_400_000)}d ago`;
}

export function creditsFor(amountInr: number, rateInr: number): number {
  if (!Number.isFinite(amountInr) || !Number.isFinite(rateInr) || rateInr <= 0) return 0;
  return Math.floor(amountInr / rateInr);
}

export function inrFor(credits: number, rateInr: number): number {
  if (!Number.isFinite(credits) || !Number.isFinite(rateInr) || rateInr <= 0) return 0;
  return Math.round(credits * rateInr);
}

export function formatInr(amount: number): string {
  const n = Math.round(amount);
  return `₹${n.toLocaleString('en-IN')}`;
}
