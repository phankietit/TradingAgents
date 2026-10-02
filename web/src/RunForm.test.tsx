import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import RunForm from './RunForm';
import LanguageSwitch from './LanguageSwitch';
const catalog = [{ instrument_id: 'aapl', canonical_symbol: 'AAPL', display_name: 'Apple', asset_class: 'equity', tradability: 'investable', venue: 'NASDAQ', quote_currency: 'USD', timezone: 'America/New_York', session_calendar: 'XNAS', benchmark_symbol: 'SPY' }];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const source = { snapshot: { snapshot_id: 'source1', dataset: 'ohlcv.daily', vendor: 'TEST FIXTURE', source_end: '2026-09-01T00:00:00Z', quality_status: 'OK' }, metadata_eligible: true, ineligibility_reasons: [], supported_analysts: ['market'] };
afterEach(() => vi.unstubAllGlobals());
function setup(stale = false) {
  const fetch = vi.fn(async (url: string) => {
    if (url.includes('/portfolios?')) return json([{ portfolio_id: 'portfolio1', as_of: '2026-09-01T00:00:00Z', base_currency: 'USD', positions: [], cash: [], net_asset_value:'10000',realized_pnl:'0',unrealized_pnl:'0',content_hash:'fixture-hash' }]);
    if (url.includes('/policies?')) return json([{ policy_id: 'policy1', policy_version: '1', name: 'Fixture policy', asset_class: 'equity', effective_at: '2026-08-01T00:00:00Z', parameters: {} }]);
    if (url.includes('/analysis-profile')) return json({ name: 'equity', allowed_analysts: ['market', 'news'], investable: true });
    if (url.includes('/snapshots?')) return json([{ ...source, metadata_eligible: !stale, ineligibility_reasons: stale ? ['stale'] : [] }]);
    if (url.endsWith('/auth/csrf')) return json({ csrf_token: 'test-csrf' });
    return json({}, 503);
  });
  vi.stubGlobal('fetch', fetch); return fetch;
}
it('defaults to 30 minutes, resets paid consent and uses a new key for changed allowance', async () => {
  const fetch=setup();const user=userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  const picker=screen.getByRole('combobox',{name:'Research time allowance'});
  expect((picker as HTMLSelectElement).value).toBe('1800');
  await user.click(await within(await screen.findByRole('group',{name:'Price & trend'})).findByRole('checkbox'));
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(screen.getByRole('button',{name:'Queue analysis'}));await screen.findByRole('alert');
  await user.selectOptions(picker,'3600');
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  expect(screen.getByText(/not an exact completion timer/)).toBeTruthy();
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(screen.getByRole('button',{name:'Queue analysis'}));await screen.findByRole('alert');
  const posts=(fetch.mock.calls as unknown as [string,RequestInit][]).filter(([url])=>url.endsWith('/runs'));
  expect(posts).toHaveLength(2);
  expect(JSON.parse(posts[0][1].body as string).execution_limits).toEqual({wall_seconds:1800,model_calls:128});
  expect(JSON.parse(posts[1][1].body as string).execution_limits).toEqual({wall_seconds:3600,model_calls:128});
  expect(posts[0][1].headers).not.toEqual(posts[1][1].headers);
});
it('requires evidence and explicit paid-call authorization', async () => {
  setup(); const user = userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  const group = await screen.findByRole('group', { name: 'Price & trend' });
  expect((screen.getByRole('button', { name: 'Queue analysis' }) as HTMLButtonElement).disabled).toBe(true);
  await user.click(await within(group).findByRole('checkbox'));
  expect((screen.getByRole('button', { name: 'Queue analysis' }) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('checkbox', { name: /I authorize/ }));
  expect((screen.getByRole('button', { name: 'Queue analysis' }) as HTMLButtonElement).disabled).toBe(false);
});
it('discloses delayed source cutoff before paid consent in both languages', async () => {
  const delayed = { ...source, snapshot: { ...source.snapshot, metadata: { freshness: 'delayed' } } };
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.includes('/analysis-profile')) return json({allowed_analysts:['market'], investable:true});
    if (url.includes('/snapshots?')) return json([delayed]);
    return json([]);
  }));
  const user = userEvent.setup();
  render(<><LanguageSwitch /><RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} /></>);
  expect(await screen.findByText(/Source publication is delayed/)).toBeTruthy();
  expect((screen.getByRole('button', {name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('button', {name:/VI/}));
  expect(await screen.findByText(/Nguồn cập nhật chậm một nến ngày/)).toBeTruthy();
});
it('keeps report language independent of UI and resets consent when changing generation language', async () => {
  const fetch = setup(); const user = userEvent.setup();
  render(<><LanguageSwitch /><RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} /></>);
  await user.click(await within(await screen.findByRole('group', { name: 'Price & trend' })).findByRole('checkbox'));
  await user.click(screen.getByRole('checkbox', { name: /I authorize/ }));
  expect((screen.getByLabelText('Report language') as HTMLSelectElement).value).toBe('en-vi');
  await user.click(screen.getByRole('button', { name: /VI/ }));
  expect((screen.getByLabelText('Ngôn ngữ báo cáo') as HTMLSelectElement).value).toBe('en-vi');
  expect((screen.getByRole('button', { name: 'Gửi phân tích' }) as HTMLButtonElement).disabled).toBe(false);
  await user.selectOptions(screen.getByLabelText('Ngôn ngữ báo cáo'), 'vi');
  expect((screen.getByRole('button', { name: 'Gửi phân tích' }) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('checkbox', { name: /Tôi cho phép/ }));
  await user.click(screen.getByRole('button', { name: 'Gửi phân tích' }));
  await screen.findByRole('alert');
  const calls = fetch.mock.calls as unknown as [string, RequestInit][];
  expect(JSON.parse(calls.find(([url]) => url.endsWith('/runs'))![1].body as string).report_language).toBe('vi');
});
it('withholds price snapshots from news and pins risk request to portfolio time', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  const news = await screen.findByRole('group', {name:'News & events'});
  expect(within(news).queryByRole('checkbox')).toBeNull();
  expect(within(news).getByText('No suitable saved sources for this research area. It will not be included.')).toBeTruthy();
  await user.click(screen.getByRole('checkbox', {name:/Evaluate against my portfolio/}));
  await user.selectOptions(screen.getByLabelText('Portfolio snapshot'), 'portfolio1');
  expect((screen.getByLabelText('Research date & time (UTC)') as HTMLInputElement).value).toBe('2026-09-01T00:00');
  expect((screen.getByLabelText('Research date & time (UTC)') as HTMLInputElement).disabled).toBe(true);
  await user.selectOptions(screen.getByLabelText('Risk policy version'), 'policy1:1');
  await user.type(screen.getByLabelText('Owner target weight (0–1)'), '0.2');
  await user.click(await within(screen.getByRole('group', {name:'Price & trend'})).findByRole('checkbox'));
  await user.click(screen.getByRole('checkbox', {name:/I authorize/}));
  await user.click(screen.getByRole('button', {name:'Queue analysis'}));
  await screen.findByRole('alert');
  const calls = fetch.mock.calls as unknown as [string, RequestInit][];
  const body = JSON.parse(calls.find(([url]) => url.endsWith('/runs'))![1].body as string);
  expect(body.analysis_as_of).toBe('2026-09-01T00:00:00Z');
  expect(body.decision_inputs).toMatchObject({ portfolio_snapshot_id:'portfolio1', policy_id:'policy1', policy_version:'1', requested_target_weight:0.2, risk_snapshot_ids:[] });
});
it('uses explicit UTC date controls and keeps advanced freshness unchanged',async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  const date = screen.getByLabelText('Research date & time (UTC)');
  fireEvent.change(date,{target:{value:'2026-08-31T13:45:12.123'}});
  expect((screen.getByLabelText('Maximum source age (seconds)') as HTMLInputElement).value).toBe('604800');
  expect(screen.getByLabelText('Maximum source age (seconds)').closest('details')?.open).toBe(false);
  await user.click(await within(await screen.findByRole('group',{name:'Price & trend'})).findByRole('checkbox'));
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(screen.getByRole('button',{name:'Queue analysis'}));
  await screen.findByRole('alert');
  const calls = fetch.mock.calls as unknown as [string, RequestInit][];
  const body = JSON.parse(calls.find(([url])=>url.endsWith('/runs'))![1].body as string);
  expect(body.analysis_as_of).toBe('2026-08-31T13:45:12.123Z');
  expect(body.decision_inputs.source_max_age_seconds).toEqual({market:604800});
  fireEvent.change(date,{target:{value:''}});
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
});
it('disables stale evidence', async () => {
  setup(true); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  const group = await screen.findByRole('group', { name: 'Price & trend' });
  expect((await within(group).findByRole('checkbox') as HTMLInputElement).disabled).toBe(true);
});
it('reuses idempotency key on unchanged failed submission', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  const group = await screen.findByRole('group', { name: 'Price & trend' });
  await user.click(await within(group).findByRole('checkbox'));
  await user.click(screen.getByRole('checkbox', { name: /I authorize/ }));
  await user.click(screen.getByRole('button', { name: 'Queue analysis' }));
  await screen.findByRole('alert');
  await user.click(screen.getByRole('button', { name: 'Queue analysis' }));
  await screen.findByRole('alert');
  const calls = fetch.mock.calls as unknown as [string, RequestInit][];
  const submissions = calls.filter(([url]) => url.endsWith('/runs'));
  expect(submissions).toHaveLength(2);
  expect(submissions[0][1].headers).toEqual(submissions[1][1].headers);
  expect(JSON.parse(submissions[0][1].body as string).selected_analysts).toEqual(['market']);
});

it('prepares current evidence without AI and requires fresh consent before submitting', async () => {
  let prepared = false;
  const now = new Date().toISOString();
  const fetch = vi.fn(async (url: string) => {
    if (url.includes('/analysis-profile')) return json({allowed_analysts:['market'], investable:true});
    if (url.includes('/snapshots?')) return json(prepared ? [source] : []);
    if (url.endsWith('/auth/csrf')) return json({csrf_token:'test'});
    if (url.endsWith('/prepare-data')) { prepared=true; return json({status:'ready',snapshot:source.snapshot,analysis_as_of:now,reused:false}); }
    if (url.includes('/portfolios?') || url.includes('/policies?')) return json([]);
    return json({},503);
  });
  vi.stubGlobal('fetch',fetch);
  const user=userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/>);
  await screen.findByText(/To continue, prepare/);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(screen.getByRole('button',{name:'Prepare latest prices'}));
  await screen.findByText(/Prices are ready/);
  await waitFor(()=>expect((screen.getByRole('group',{name:'Price & trend'}).querySelector('input') as HTMLInputElement).checked).toBe(true));
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/runs'))).toBe(false);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(false);
});

it('adds recent news as a separate, non-exhaustive source without starting AI', async () => {
  const now = new Date().toISOString();
  const headline = { snapshot: { snapshot_id: 'news1', dataset: 'news', vendor: 'yfinance',
    source_end: now, quality_status: 'OK', metadata: { coverage: 'recent_feed_not_exhaustive' } },
    metadata_eligible: true, ineligibility_reasons: [], supported_analysts: ['news'] };
  let newsPrepared = false;
  const fetch = vi.fn(async (url: string) => {
    if (url.includes('/analysis-profile')) return json({allowed_analysts:['market','news'], investable:true});
    if (url.includes('/snapshots?')) return json(newsPrepared ? [source, headline] : [source]);
    if (url.endsWith('/auth/csrf')) return json({csrf_token:'test'});
    if (url.endsWith('/prepare-news')) {
      newsPrepared = true;
      return json({status:'ready',snapshot:headline.snapshot,analysis_as_of:now,reused:false});
    }
    if (url.includes('/portfolios?') || url.includes('/policies?')) return json([]);
    return json({},503);
  });
  vi.stubGlobal('fetch',fetch);
  const user = userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  await user.click(await within(await screen.findByRole('group',{name:'Price & trend'})).findByRole('checkbox'));
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(await screen.findByRole('button',{name:'Add recent headlines'}));
  expect(await screen.findByText(/not a complete record of all news/)).toBeTruthy();
  await waitFor(() => expect((within(screen.getByRole('group',{name:'News & events'})).getByRole('checkbox') as HTMLInputElement).checked).toBe(true));
  expect((within(screen.getByRole('group',{name:'Price & trend'})).getByRole('checkbox') as HTMLInputElement).checked).toBe(true);
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/runs'))).toBe(false);
});

it('does not select an empty recent-news feed', async () => {
  const fetch = setup();
  fetch.mockImplementation(async (url:string) => {
    if (url.includes('/analysis-profile')) return json({allowed_analysts:['market','news'],investable:true});
    if (url.includes('/snapshots?')) return json([source]);
    if (url.endsWith('/auth/csrf')) return json({csrf_token:'test'});
    if (url.endsWith('/prepare-news')) return json({status:'no_data',snapshot:null,analysis_as_of:new Date().toISOString(),reused:false});
    return json([]);
  });
  const user = userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  await user.click(await screen.findByRole('button',{name:'Add recent headlines'}));
  expect(await screen.findByText(/News research was not selected/)).toBeTruthy();
  expect(within(screen.getByRole('group',{name:'News & events'})).queryByRole('checkbox')).toBeNull();
});

it('prepares AAPL SEC facts separately with a filing-specific freshness limit and no AI call', async () => {
  const now = new Date().toISOString();
  const fundamental = { snapshot: { snapshot_id: 'sec1', dataset: 'fundamentals', vendor: 'sec_edgar',
    source_end: '2026-07-30T00:00:00Z', quality_status: 'OK', metadata: { vintage: 'current_retrieval_filed_date_filter' } },
    metadata_eligible: true, ineligibility_reasons: [], supported_analysts: ['fundamentals'] };
  let prepared = false;
  const fetch = vi.fn(async (url: string) => {
    if (url.includes('/analysis-profile')) return json({allowed_analysts:['market','fundamentals'], investable:true});
    if (url.includes('/snapshots?')) return json(url.includes('max_age_seconds=31536000')
      ? prepared ? [fundamental] : [] : [source]);
    if (url.endsWith('/auth/csrf')) return json({csrf_token:'test'});
    if (url.endsWith('/prepare-fundamentals')) {
      prepared = true;
      return json({status:'ready',snapshot:fundamental.snapshot,analysis_as_of:now,reused:false});
    }
    if (url.includes('/portfolios?') || url.includes('/policies?')) return json([]);
    return json({},503);
  });
  vi.stubGlobal('fetch', fetch);
  const user = userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  await user.click(await screen.findByRole('button',{name:'Add SEC fundamentals'}));
  expect(await screen.findByText(/reported US GAAP tags, not a complete company profile/)).toBeTruthy();
  await waitFor(() => expect((within(screen.getByRole('group',{name:'Business fundamentals'})).getByRole('checkbox') as HTMLInputElement).checked).toBe(true));
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/runs'))).toBe(false);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(screen.getByRole('button',{name:'Queue analysis'}));
  const calls = fetch.mock.calls as unknown as [string, RequestInit][];
  const body = JSON.parse(calls.find(([url])=>url.endsWith('/runs'))![1].body as string);
  expect(body.decision_inputs.source_max_age_seconds).toEqual({fundamentals:31536000});
});

it('explains source failure and keeps AI submission disabled',async()=>{
  const fetch=setup();
  fetch.mockImplementation(async (url:string)=>{
    if(url.includes('/analysis-profile')) return json({allowed_analysts:['market'],investable:true});
    if(url.includes('/snapshots?')) return json([]);
    if(url.endsWith('/auth/csrf')) return json({csrf_token:'test'});
    if(url.endsWith('/prepare-data')) return json({status:'coverage_gap',snapshot:null,analysis_as_of:new Date().toISOString(),reused:false});
    return json([]);
  });
  const user=userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/>);
  await user.click(screen.getByRole('button',{name:'Prepare latest prices'}));
  await screen.findByText(/Data is not ready yet. Retrying automatically/);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('button',{name:'Stop automatic retries'}));
  await screen.findByText(/Automatic retries stopped/);
});
