import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import ValuationSources from './ValuationSources';
afterEach(()=>vi.unstubAllGlobals());
const evidence = {portfolio_id:'portfolio',portfolio_content_hash:'hash',sources:[{vendor:'Synthetic QA',dataset:'ohlcv.daily',quote:{instrument_id:'asset',price:'198.02',currency:'USD',quality_status:'OK',source_at:'2026-09-25T00:00:00Z',observed_at:'2026-09-26T00:00:00Z',snapshot_id:'snapshot',content_hash:'sourcehash'}}]};
it('loads source receipt only when requested and keeps audit IDs collapsed',async()=>{
  const fetch=vi.fn(async()=>new Response(JSON.stringify(evidence))); vi.stubGlobal('fetch',fetch);
  render(<ValuationSources id="portfolio" hash="hash" catalog={[]} />);
  expect(fetch).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'View valuation sources'}));
  expect(await screen.findByText(/198.02 USD/)).toBeTruthy();
  expect(screen.getByText('sourcehash').closest('details')?.open).toBe(false);
  expect(screen.getByText(/not a live quote/)).toBeTruthy();
});
it.each([{}, {...evidence,portfolio_content_hash:'wrong'}])('withholds malformed or mismatched evidence',async data=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify(data))));
  render(<ValuationSources id="portfolio" hash="hash" catalog={[]} />);
  await userEvent.click(screen.getByRole('button',{name:'View valuation sources'}));
  expect(await screen.findByText(/Valuation sources unavailable/)).toBeTruthy();
  expect(screen.queryByText(/198.02 USD/)).toBeNull();
});
it('explains missing legacy receipt without substituting a price',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:404})));
  render(<ValuationSources id="portfolio" hash="hash" catalog={[]} />);
  await userEvent.click(screen.getByRole('button',{name:'View valuation sources'}));
  expect(await screen.findByText(/no source receipt/)).toBeTruthy();
});
