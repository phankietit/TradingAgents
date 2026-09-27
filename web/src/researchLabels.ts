/** Display labels only; service role identifiers and evidence remain unchanged. */
export function researchLabel(role: string): string {
  const labels: Record<string, string> = { market: 'Price & trend', social: 'Market sentiment', news: 'News & events', fundamentals: 'Business fundamentals' };
  return Object.hasOwn(labels, role) ? labels[role] : role;
}

export function datasetLabel(dataset: string): string {
  return dataset === 'ohlcv.daily' ? 'Daily prices & volume' : dataset;
}
