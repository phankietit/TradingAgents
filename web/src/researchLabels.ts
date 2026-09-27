/** Display labels only; service role identifiers and evidence remain unchanged. */
import { t } from './i18n';
export function researchLabel(role: string): string {
  const labels: Record<string, string> = { market: 'Price & trend', social: 'Market sentiment', news: 'News & events', fundamentals: 'Business fundamentals' };
  return Object.hasOwn(labels, role) ? t(labels[role]) : role;
}

export function datasetLabel(dataset: string): string {
  return dataset === 'ohlcv.daily' ? t('Daily prices & volume') : dataset;
}
