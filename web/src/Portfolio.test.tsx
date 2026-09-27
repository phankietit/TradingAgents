import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import Portfolio, { decimal } from './Portfolio';
afterEach(() => vi.unstubAllGlobals());
it('formats exact decimal values without rounding through floats', () => {
  expect(decimal('123456789123456789.123456')).toBe('123,456,789,123,456,789.123456');
  expect(decimal(null)).toBe('Unavailable');
  expect(decimal('')).toBe('Unavailable');
  expect(decimal('1E-8')).toBe('0.00000001');
  expect(decimal('1.234E+4')).toBe('12,340');
  expect(decimal('0E-8')).toBe('0.00000000');
  expect(decimal('1e9999999')).toBe('Unavailable');
});
it('shows missing portfolio rather than zero valuation', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('[]')));
  render(<Portfolio />);
  expect(await screen.findByText('No portfolio snapshot')).toBeTruthy();
  expect(screen.queryByText('Net asset value')).toBeNull();
});
it('renders stored cash NAV and missing cost basis', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url.includes('/portfolios') ? [{
    portfolio_id: 'fixture', as_of: '2026-09-01T00:00:00Z', base_currency: 'USD', net_asset_value: '10000.01', realized_pnl: '0', unrealized_pnl: '1.01', content_hash: 'sha256:fixture',
    cash: [{ currency: 'USD', amount: '9000' }], positions: [{ instrument_id: 'aapl', quantity: '10', average_price: null, market_price: '100.001', market_value: '1000.01', weight: .100001 }],
  }] : []))));
  render(<Portfolio />);
  expect(await screen.findByText('10,000.01')).toBeTruthy();
  expect(screen.getByText('Unavailable')).toBeTruthy();
  expect(screen.getByRole('region', { name: 'Portfolio holdings' })).toBeTruthy();
});
it('withholds malformed portfolio payload instead of treating it as zero or crashing', async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.includes('/portfolios') ? {unexpected:'private-source-content'} : []))));
  render(<Portfolio />);
  expect(await screen.findByRole('alert')).toBeTruthy();
  expect(screen.queryByText('No portfolio snapshot')).toBeNull();
  expect(screen.queryByRole('region',{name:'Portfolio holdings'})).toBeNull();
  expect(screen.queryByText('private-source-content')).toBeNull();
});
it('summarizes financial policy limits without hiding original parameters or inventing zeros',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.includes('/policies') ? [{policy_id:'policy-fixture',policy_version:'1',name:'Synthetic policy',asset_class:'equity',effective_at:'2026-09-01T00:00:00Z',parameters:{max_position_weight:.3,max_correlation:.8,min_cash_weight:null,unknown_setting:'preserved'}}] : []))));
  render(<Portfolio />);
  expect(await screen.findByText('30.00%')).toBeTruthy();
  expect(screen.getByText('0.8')).toBeTruthy();
  expect(screen.getByText('Unavailable — check policy details')).toBeTruthy();
  expect(screen.getByText(/"unknown_setting": "preserved"/).closest('details')?.open).toBe(false);
});
