/** Display labels only; service role identifiers and evidence remain unchanged. */
import { t } from './i18n';
export function researchLabel(role: string): string {
  const labels: Record<string, string> = { market: 'Price & trend', social: 'Market sentiment', news: 'News & events', fundamentals: 'Business fundamentals' };
  return Object.hasOwn(labels, role) ? t(labels[role]) : role;
}

export function datasetLabel(dataset: string): string {
  const labels: Record<string, string> = { 'ohlcv.daily': 'Daily prices & volume',
    news: 'Recent headlines', macro: 'Economic indicator', fundamentals: 'Company filings' };
  return Object.hasOwn(labels, dataset) ? t(labels[dataset]) : dataset;
}

export function profileLabel(profile: string): string {
  const labels: Record<string, string> = { equity: 'Equity research', etf: 'ETF research',
    'large-cap-crypto': 'Large-cap crypto', 'cash-index-reference': 'Index reference',
    'futures-reference': 'Futures reference only' };
  return Object.hasOwn(labels, profile) ? t(labels[profile]) : t('Research profile unavailable');
}
