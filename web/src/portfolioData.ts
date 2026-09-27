import { ApiError } from './api';
import type { Policy, PortfolioSnapshot } from './Portfolio';
import { plainDecimal } from './decimal';

const text = (value: unknown) => typeof value === 'string' && value.length > 0;
const date = (value: unknown) => text(value) && Number.isFinite(Date.parse(value as string));
const amount = (value: unknown) => plainDecimal(value) !== null;
const nonnegative = (value: unknown) => { const plain = plainDecimal(value); return plain !== null && (!plain.startsWith('-') || /^-0(?:\.0+)?$/.test(plain)); };
const weight = (value: unknown) => (typeof value === 'number' || amount(value)) && Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 1;

/** Display validation only; no recomputation of NAV, allocation or risk limits. */
export function portfolioSnapshots(value: PortfolioSnapshot[]): PortfolioSnapshot[] {
  if (!Array.isArray(value) || value.some(item => !item || ![item.portfolio_id,item.base_currency,item.content_hash].every(text)
    || !date(item.as_of) || !nonnegative(item.net_asset_value) || !amount(item.realized_pnl) || !amount(item.unrealized_pnl)
    || !Array.isArray(item.cash) || item.cash.some(row=>!row || !text(row.currency) || !nonnegative(row.amount))
    || !Array.isArray(item.positions) || item.positions.some(row=>!row || !text(row.instrument_id)
      || ![row.quantity,row.market_price,row.market_value].every(nonnegative)
      || (row.average_price !== null && !nonnegative(row.average_price)) || !weight(row.weight))
    || new Set(item.positions.map(row=>row.instrument_id)).size !== item.positions.length)
    || new Set(value.map(item=>item.portfolio_id)).size !== value.length) throw new ApiError(502);
  return value;
}
export function policyHistory(value: Policy[]): Policy[] {
  if (!Array.isArray(value) || value.some(item=>!item || ![item.policy_id,item.policy_version,item.name,item.asset_class].every(text)
    || !date(item.effective_at) || !item.parameters || typeof item.parameters !== 'object' || Array.isArray(item.parameters))) throw new ApiError(502);
  return value;
}
