import { useId, useState } from 'react';
import { number, timestamp } from './data';
import { t, useLocale } from './i18n';

interface Point { closed_at: string; session_date: string | null; price: number }
export interface ReportHistory { snapshot_id: string; quote_currency: string; price_basis: string; points: Point[] }
export function reportHistories(value: unknown): ReportHistory[] {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > 16) throw new Error('Invalid saved chart');
  return value.map(item => {
    if (!item || typeof item.snapshot_id !== 'string' || typeof item.quote_currency !== 'string'
      || !['close', 'adjusted_close'].includes(item.price_basis) || !Array.isArray(item.points)
      || item.points.length < 1 || item.points.length > 100000
      || item.points.some((p: Point, i: number) => !p || !Number.isFinite(p.price) || p.price <= 0
        || !Number.isFinite(Date.parse(p.closed_at))
        || (p.session_date !== null && !/^\d{4}-\d{2}-\d{2}$/.test(p.session_date))
        || (i > 0 && Date.parse(p.closed_at) <= Date.parse(item.points[i - 1].closed_at)))) throw new Error('Invalid saved chart');
    return item as ReportHistory;
  });
}

export default function ResearchChart({ history }: { history: ReportHistory }) {
  useLocale();
  const [days, setDays] = useState(365);
  const [selection, setSelection] = useState<number | null>(null);
  const id = useId();
  const last = history.points[history.points.length - 1];
  const cutoff = days === 0 ? -Infinity : Date.parse(last.closed_at) - days * 86400000;
  const points = history.points.filter(point => Date.parse(point.closed_at) >= cutoff);
  const prices = points.map(point => point.price);
  const low = prices.reduce((a, b) => Math.min(a, b), Infinity);
  const high = prices.reduce((a, b) => Math.max(a, b), -Infinity);
  const startTime = Date.parse(points[0].closed_at);
  const elapsed = Date.parse(last.closed_at) - startTime || 1;
  const x = (point: Point) => 30 + (Date.parse(point.closed_at) - startTime) / elapsed * 730;
  const y = (point: Point) => 220 - (point.price - low) / (high - low || 1) * 180;
  const active = points[Math.min(selection ?? points.length - 1, points.length - 1)];
  const path = points.map(point => `${x(point).toFixed(2)},${y(point).toFixed(2)}`).join(' ');
  return <section className="report-chart" aria-label={t('Saved research price history')}>
    <div className="chart-toolbar"><div><span className="eyebrow">{t('Price context')} · {history.quote_currency}</span><p className="chart-price">{number(active.price)} <small>{active.session_date ?? timestamp(active.closed_at)}</small></p></div>
      <div className="chart-ranges" aria-label={t('Chart window')}>{[[30, '1M'], [90, '3M'], [365, '1Y'], [0, 'All']].map(([value, label]) => <button key={value} aria-pressed={days === value} onClick={() => { setDays(Number(value)); setSelection(null); }}>{t(String(label))}</button>)}</div>
    </div>
    <figure><div className="chart-scale"><span>{t('Low')}: {number(low)}</span><span>{t('High')}: {number(high)} {history.quote_currency}</span></div><svg viewBox="0 0 790 260" role="img" aria-labelledby={id}>
      <title id={id}>{t('Saved research price history')} · {history.quote_currency} · {t(history.price_basis)}</title>
      {[0, .5, 1].map(ratio => <line key={ratio} x1="30" x2="760" y1={40 + ratio * 180} y2={40 + ratio * 180} stroke="var(--border)" strokeDasharray="3 5" />)}
      <polyline points={path} fill="none" stroke="#b8c7a2" strokeWidth="2" vectorEffect="non-scaling-stroke" />
      <line x1={x(active)} x2={x(active)} y1="35" y2="225" stroke="#77886c" strokeDasharray="3 4" />
      <circle cx={x(active)} cy={y(active)} r="4" fill="#e4e8d9" />
    </svg><figcaption>{t('Saved prices, not live quotes.')} {t(history.price_basis)} · {t('Closed through')} {timestamp(last.closed_at)}</figcaption></figure>
    <label className="chart-scrubber">{t('Inspect a saved candle')}<input aria-label={t('Inspect a saved candle')} type="range" min="0" max={points.length - 1} value={selection ?? points.length - 1} onChange={event => setSelection(Number(event.target.value))} /></label>
    <details><summary>{t('Chart source')}</summary><p className="mono caption">{history.snapshot_id}</p><p className="muted caption">{t('Trading-day labels and close timestamps are distinct. Legacy sources may not contain a trading-day label.')}</p></details>
  </section>;
}
