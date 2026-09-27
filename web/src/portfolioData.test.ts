import { expect, it } from 'vitest';
import { portfolioSnapshots, policyHistory } from './portfolioData';
import type { PortfolioSnapshot, Policy } from './Portfolio';

const saved: PortfolioSnapshot = {portfolio_id:'p',as_of:'2026-09-27T00:00:00Z',base_currency:'USD',net_asset_value:'123456789123456789.123456',realized_pnl:'-1.01',unrealized_pnl:'1',content_hash:'hash',cash:[{currency:'USD',amount:'0'}],positions:[{instrument_id:'a',quantity:'1',average_price:null,market_price:'1',market_value:'1',weight:'0.1'}]};
it('preserves exact decimal strings and valid zero/negative P&L without recomputing',()=>{
  const data=[saved]; expect(portfolioSnapshots(data)).toBe(data);
  expect(data[0].net_asset_value).toBe('123456789123456789.123456');
  expect(portfolioSnapshots([{...saved,net_asset_value:'1E-8',cash:[{currency:'USD',amount:'-0.00'}]}])[0].net_asset_value).toBe('1E-8');
});
it.each([null,{},[{...saved,cash:null}],[{...saved,positions:{}}],[{...saved,net_asset_value:'NaN'}],[{...saved,net_asset_value:100}],[{...saved,positions:[{...saved.positions[0],weight:''}]}],[{...saved,positions:[saved.positions[0],saved.positions[0]]}],[saved,saved]])('rejects malformed portfolio display shape',value=>{
  expect(()=>portfolioSnapshots(value as PortfolioSnapshot[])).toThrow();
});
it.each([null,{},[{policy_id:'id'}],[{policy_id:'id',policy_version:'1',name:'p',asset_class:'equity',effective_at:'2026-09-27',parameters:[]}]])('rejects malformed policy histories',value=>{
  expect(()=>policyHistory(value as Policy[])).toThrow();
});
