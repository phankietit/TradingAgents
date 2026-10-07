import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import RunForm from './RunForm';
import LanguageSwitch from './LanguageSwitch';
const catalog = [{ instrument_id: 'aapl', canonical_symbol: 'AAPL', display_name: 'Apple', asset_class: 'equity', tradability: 'investable', venue: 'NASDAQ', quote_currency: 'USD', timezone: 'America/New_York', session_calendar: 'XNAS', benchmark_symbol: 'SPY' }];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const source = { snapshot: { snapshot_id: 'source1', dataset: 'ohlcv.daily', vendor: 'TEST FIXTURE', source_end: '2026-09-01T00:00:00Z', quality_status: 'OK' }, metadata_eligible: true, ineligibility_reasons: [], supported_analysts: ['market'] };
afterEach(() => vi.unstubAllGlobals());

// Exercise the visible staged journey; never query hidden panels to bypass it.
async function visitData(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: /^(Prepare market data|Chuẩn bị dữ liệu thị trường)$/ }));
}
async function inspectSources(user: ReturnType<typeof userEvent.setup>) {
  await visitData(user);
  await user.click(screen.getByRole('button', { name: /^(Choose saved sources|Chọn nguồn đã lưu)$/ }));
}
async function visitReview(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: /^(Review & authorize|Kiểm tra & cấp phép)$/ }));
}
async function visitScope(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: /^(Research scope|Phạm vi nghiên cứu)$/ }));
}

it.each(['stocktwits','reddit'])('prepares original social feeds independently with %s first and resets AI consent',async first=>{
  const now=new Date().toISOString();
  const make=(vendor:string,id:string)=>({snapshot:{snapshot_id:id,dataset:'social',vendor,source_end:now,quality_status:'OK',metadata:{posts:3}},metadata_eligible:true,ineligibility_reasons:[],supported_analysts:['social']});
  const rows=[make('stocktwits','old-stocktwits'),make('reddit','old-reddit')];
  const fetch=vi.fn(async(url:string,init?:RequestInit)=>{
    if(url.includes('/analysis-profile'))return json({allowed_analysts:['market','social','news'],investable:true});
    if(url.includes('/snapshots?'))return json([source,...rows]);
    if(url.endsWith('/auth/csrf'))return json({csrf_token:'test'});
    if(url.endsWith('/prepare-social')){
      const {vendor}=JSON.parse(init!.body as string);expect(['stocktwits','reddit']).toContain(vendor);
      const row=make(vendor,`new-${vendor}`);rows.push(row);
      return json({status:'ready',snapshot:row.snapshot,analysis_as_of:now,reused:false});
    }
    return json([]);
  });
  vi.stubGlobal('fetch',fetch);const user=userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/>);
  await inspectSources(user);
  const group=await screen.findByRole('group',{name:'Market sentiment'});
  for(const box of within(group).getAllByRole('checkbox'))await user.click(box);
  await visitReview(user);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await visitData(user);
  const names={stocktwits:'Add StockTwits discussions',reddit:'Add Reddit discussions'};
  await user.click(screen.getByRole('button',{name:names[first as keyof typeof names]}));
  await screen.findByText(/StockTwits · Discussion posts are ready|Reddit · Discussion posts are ready/);
  await visitReview(user);
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  await visitData(user);
  await user.click(screen.getByRole('button',{name:names[first==='stocktwits'?'reddit':'stocktwits']}));
  await waitFor(()=>expect(within(group).getAllByRole('checkbox').filter(item=>(item as HTMLInputElement).checked)).toHaveLength(2));
  expect(screen.getByText(/Selected discussion feeds:/).textContent).toContain('stocktwits');
  expect(screen.getByText(/Selected discussion feeds:/).textContent).toContain('reddit');
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/runs'))).toBe(false);
  const selected=within(group).getAllByRole('checkbox').filter(item=>(item as HTMLInputElement).checked);
  expect(selected.every(item=>item.closest('label')?.textContent?.includes('stocktwits')||item.closest('label')?.textContent?.includes('reddit'))).toBe(true);
});

it('does not turn failed Reddit into neutral sentiment or remove StockTwits, and shows Vietnamese',async()=>{
  const now=new Date().toISOString();
  const row={snapshot:{snapshot_id:'social-one',dataset:'social',vendor:'stocktwits',source_end:now,quality_status:'OK',metadata:{posts:3}},metadata_eligible:true,ineligibility_reasons:[],supported_analysts:['social']};
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>{
    if(url.includes('/analysis-profile'))return json({allowed_analysts:['social'],investable:true});
    if(url.includes('/snapshots?'))return json([row]);
    if(url.endsWith('/auth/csrf'))return json({csrf_token:'test'});
    if(url.endsWith('/prepare-social'))return json({status:'unavailable',snapshot:null,analysis_as_of:now});
    return json([]);
  }));
  const user=userEvent.setup();render(<><LanguageSwitch/><RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/></>);
  await inspectSources(user);
  const group=await screen.findByRole('group',{name:'Market sentiment'});
  await user.click(within(group).getByRole('checkbox'));
  await visitReview(user);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await visitData(user);
  await user.click(screen.getByRole('button',{name:'Add Reddit discussions'}));
  await screen.findByText(/Reddit · This discussion source is unavailable/);
  expect((within(group).getByRole('checkbox') as HTMLInputElement).checked).toBe(true);
  await visitReview(user);
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  await visitData(user);
  await user.click(screen.getByRole('button',{name:/VI/}));
  expect(await screen.findByText(/Reddit · Chưa kết nối được nguồn thảo luận/)).toBeTruthy();
  await visitReview(user);
  expect((screen.getByRole('button',{name:'Gửi phân tích'}) as HTMLButtonElement).disabled).toBe(true);
});

it.each(['macro-first', 'headlines-first'])('preserves distinct economic and headline sources through %s preparation and explicit consent', async order => {
  const now=new Date().toISOString();
  const macro={snapshot:{snapshot_id:'macro-new',dataset:'macro',vendor:'fred',source_end:now,quality_status:'OK',
    metadata:{series_id:'DGS10',units:'Percent',last_observation_date:'2026-10-02',vintage_date:'2026-10-02'}},metadata_eligible:true,ineligibility_reasons:[],supported_analysts:['news']};
  const news={...macro,snapshot:{snapshot_id:'news-new',dataset:'news',vendor:'yfinance',source_end:now,quality_status:'OK'}};
  const oldMacro={...macro,snapshot:{...macro.snapshot,snapshot_id:'macro-old'}};
  const oldNews={...news,snapshot:{...news.snapshot,snapshot_id:'news-old'}};
  let macroReady=false,newsReady=false;
  const fetch=vi.fn(async (url:string,init?:RequestInit)=>{
    if(url.includes('/analysis-profile'))return json({allowed_analysts:['market','news'],investable:true});
    if(url.includes('/snapshots?'))return json([source,oldMacro,oldNews,...(macroReady?[macro]:[]),...(newsReady?[news]:[])]);
    if(url.endsWith('/auth/csrf'))return json({csrf_token:'test'});
    if(url.endsWith('/prepare-macro')){expect(JSON.parse(init!.body as string)).toEqual({series_id:'DGS10',lookback_days:365});macroReady=true;return json({status:'ready',snapshot:macro.snapshot,analysis_as_of:now,reused:false});}
    if(url.endsWith('/prepare-news')){newsReady=true;return json({status:'ready',snapshot:news.snapshot,analysis_as_of:now,reused:false});}
    if(url.includes('/portfolios?')||url.includes('/policies?'))return json([]);
    return json({},503);
  });
  vi.stubGlobal('fetch',fetch);
  const user=userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/>);
  await inspectSources(user);
  const newsGroup=await screen.findByRole('group',{name:'News & events'});
  await user.click(within(newsGroup).getAllByRole('checkbox')[0]);
  await user.click(within(newsGroup).getAllByRole('checkbox')[1]);
  await visitReview(user);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await visitData(user);
  const first=order==='macro-first'?'Add economic context':'Add recent headlines';
  const second=order==='macro-first'?'Add recent headlines':'Add economic context';
  await user.click(screen.getByRole('button',{name:first}));
  await screen.findByText(order==='macro-first'?/Economic data is ready/:/Recent headlines are ready/);
  await visitReview(user);
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  await visitData(user);
  await user.click(screen.getByRole('button',{name:second}));
  await screen.findByText(order==='macro-first'?/Recent headlines are ready/:/Economic data is ready/);
  await waitFor(()=>expect(within(newsGroup).getAllByRole('checkbox').filter(input=>(input as HTMLInputElement).checked)).toHaveLength(2));
  expect(screen.getByText(/Economic data does not replace news coverage/).textContent).toContain('DGS10');
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/runs'))).toBe(false);
  await visitReview(user);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(screen.getByRole('button',{name:'Queue analysis'}));
  const posted=fetch.mock.calls.find(([url])=>url.endsWith('/runs'))!;
  expect(JSON.parse(posted[1]!.body as string).decision_inputs.snapshots_by_analyst.news).toEqual(expect.arrayContaining(['macro-new','news-new']));
  expect(JSON.parse(posted[1]!.body as string).decision_inputs.snapshots_by_analyst.news).toHaveLength(2);
});

it('discloses failed economic coverage in Vietnamese and never selects it or starts AI',async()=>{
  const fetch=setup();
  fetch.mockImplementation(async(url:string)=>{
    if(url.includes('/analysis-profile'))return json({allowed_analysts:['market','news'],investable:true});
    if(url.includes('/snapshots?'))return json([source]);
    if(url.endsWith('/auth/csrf'))return json({csrf_token:'test'});
    if(url.endsWith('/prepare-macro'))return json({status:'coverage_gap',snapshot:null,analysis_as_of:new Date().toISOString(),reused:false});
    return json([]);
  });
  const user=userEvent.setup();
  render(<><LanguageSwitch/><RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/></>);
  await visitData(user);
  await user.click(await screen.findByRole('button',{name:'Add economic context'}));
  expect(await screen.findByText(/no observations in the requested history window/)).toBeTruthy();
  await user.click(screen.getByRole('button',{name:/VI/}));
  expect(await screen.findByText(/không có số liệu trong khoảng lịch sử yêu cầu/)).toBeTruthy();
  await visitReview(user);
  expect((screen.getByRole('button',{name:'Gửi phân tích'}) as HTMLButtonElement).disabled).toBe(true);
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/runs'))).toBe(false);
});
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
it('shows exact current request context and all selected sources before paid consent', async () => {
  const fetch = setup(); const user = userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/>);
  await inspectSources(user);
  const group = await screen.findByRole('group',{name:'Price & trend'});
  await user.click(within(group).getByRole('checkbox'));
  await visitReview(user);
  const summary = screen.getByRole('region',{name:'Analysis request summary'});
  expect(within(summary).getByText('AAPL — Apple')).toBeTruthy();
  expect(within(summary).getByText('English + Vietnamese')).toBeTruthy();
  expect(within(summary).getByText('Asset research only')).toBeTruthy();
  expect(within(summary).getByText(/Daily prices & volume · TEST FIXTURE/)).toBeTruthy();
  expect(within(summary).getByText(/Source data through: 2026-09-01/)).toBeTruthy();
  expect(within(summary).getByText('Not included')).toBeTruthy();
  expect(summary.compareDocumentPosition(screen.getByRole('checkbox',{name:/I authorize/})) & Node.DOCUMENT_POSITION_CONTAINED_BY).toBeTruthy();
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await visitScope(user);
  await user.selectOptions(screen.getByLabelText('Report language'),'vi');
  await visitReview(user);
  expect(within(summary).getByText('Vietnamese')).toBeTruthy();
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/runs'))).toBe(false);
});
it('moves focus to review without changing consent, collecting sources or starting AI', async () => {
  const fetch = setup(); const user = userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/>);
  await inspectSources(user);
  await screen.findByRole('group',{name:'Price & trend'});
  await visitReview(user);
  const summary = screen.getByRole('region',{name:'Analysis request summary'});
  const scroll = vi.fn(); summary.scrollIntoView = scroll;
  await visitScope(user);
  await user.click(screen.getByRole('button',{name:'Review & authorize'}));
  expect(scroll).toHaveBeenCalledWith({block:'start'});
  expect(document.activeElement).toBe(summary);
  expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/runs') || /\/prepare-/.test(url))).toBe(false);
});
it('shows selected portfolio, governed policy and owner allocation in the consent brief', async () => {
  setup(); const user = userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()}/>);
  await inspectSources(user);
  await screen.findByRole('group',{name:'Price & trend'});
  await user.click(screen.getByRole('checkbox',{name:/Evaluate against my portfolio/}));
  await user.selectOptions(screen.getByLabelText('Portfolio snapshot'),'portfolio1');
  await user.selectOptions(screen.getByLabelText('Risk policy version'),'policy1:1');
  await user.type(screen.getByLabelText('Owner target weight (0–1)'),'0.2');
  await visitReview(user);
  const summary = screen.getByRole('region',{name:'Analysis request summary'});
  expect(within(summary).getByText('Portfolio policy evaluation')).toBeTruthy();
  expect(within(summary).getByText(/USD · 2026-09-01/)).toBeTruthy();
  expect(within(summary).getByText('Fixture policy · v1')).toBeTruthy();
  expect(within(summary).getByText('20.00%')).toBeTruthy();
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
});
it.each([false,true])('opens saved-source review without collecting, selecting or authorizing anything (stale=%s)', async stale => {
  const fetch=setup(stale); const user=userEvent.setup();
  const original=Object.getOwnPropertyDescriptor(HTMLElement.prototype,'scrollIntoView');
  const scroll=vi.fn();
  Object.defineProperty(HTMLElement.prototype,'scrollIntoView',{value:scroll,configurable:true});
  try {
    render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
    await visitData(user);
    const inspector=screen.getByText('Inspect or change evidence sources').closest('details')!;
    expect(inspector.open).toBe(false);
    await user.click(screen.getByRole('button',{name:'Choose saved sources'}));
    const group=await screen.findByRole('group',{name:'Price & trend'});
    expect(inspector.open).toBe(true);
    expect(scroll).toHaveBeenCalledWith({block:'start'});
    expect(document.activeElement).toBe(inspector.querySelector('summary'));
    const box=within(group).getByRole('checkbox') as HTMLInputElement;
    expect(box.checked).toBe(false); expect(box.disabled).toBe(stale);
    await visitReview(user);
    expect((screen.getByRole('checkbox',{name:/I authorize/}) as HTMLInputElement).checked).toBe(false);
    expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
    expect(fetch.mock.calls.some(([url])=>url.includes('/prepare-') || url.endsWith('/runs'))).toBe(false);
  } finally {
    if(original) Object.defineProperty(HTMLElement.prototype,'scrollIntoView',original);
    else Reflect.deleteProperty(HTMLElement.prototype,'scrollIntoView');
  }
});
it('defaults to 30 minutes, resets paid consent and uses a new key for changed allowance', async () => {
  const fetch=setup();const user=userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  await inspectSources(user);
  await user.click(await within(await screen.findByRole('group',{name:'Price & trend'})).findByRole('checkbox'));
  await visitReview(user);
  const picker=screen.getByRole('combobox',{name:'Research time allowance'});
  expect((picker as HTMLSelectElement).value).toBe('1800');
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
  await inspectSources(user);
  const group = await screen.findByRole('group', { name: 'Price & trend' });
  await visitReview(user);
  expect((screen.getByRole('button', { name: 'Queue analysis' }) as HTMLButtonElement).disabled).toBe(true);
  await visitData(user);
  await user.click(await within(group).findByRole('checkbox'));
  await visitReview(user);
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
  await inspectSources(user);
  expect(await screen.findByText(/Source publication is delayed/)).toBeTruthy();
  await visitReview(user);
  expect((screen.getByRole('button', {name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  await visitData(user);
  await user.click(screen.getByRole('button', {name:/VI/}));
  expect(await screen.findByText(/Nguồn cập nhật chậm một nến ngày/)).toBeTruthy();
});
it('keeps report language independent of UI and resets consent when changing generation language', async () => {
  const fetch = setup(); const user = userEvent.setup();
  render(<><LanguageSwitch /><RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} /></>);
  expect((screen.getByLabelText('Report language') as HTMLSelectElement).value).toBe('en-vi');
  await inspectSources(user);
  await user.click(await within(await screen.findByRole('group', { name: 'Price & trend' })).findByRole('checkbox'));
  await visitReview(user);
  await user.click(screen.getByRole('checkbox', { name: /I authorize/ }));
  await visitScope(user);
  expect((screen.getByLabelText('Report language') as HTMLSelectElement).value).toBe('en-vi');
  await user.click(screen.getByRole('button', { name: /VI/ }));
  expect((screen.getByLabelText('Ngôn ngữ báo cáo') as HTMLSelectElement).value).toBe('en-vi');
  await visitReview(user);
  expect((screen.getByRole('button', { name: 'Gửi phân tích' }) as HTMLButtonElement).disabled).toBe(false);
  await visitScope(user);
  await user.selectOptions(screen.getByLabelText('Ngôn ngữ báo cáo'), 'vi');
  await visitReview(user);
  expect((screen.getByRole('button', { name: 'Gửi phân tích' }) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('checkbox', { name: /Tôi cho phép/ }));
  await user.click(screen.getByRole('button', { name: 'Gửi phân tích' }));
  await screen.findByRole('alert');
  const calls = fetch.mock.calls as unknown as [string, RequestInit][];
  expect(JSON.parse(calls.find(([url]) => url.endsWith('/runs'))![1].body as string).report_language).toBe('vi');
});
it('withholds price snapshots from news and pins risk request to portfolio time', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  await inspectSources(user);
  const news = await screen.findByRole('group', {name:'News & events'});
  expect(within(news).queryByRole('checkbox')).toBeNull();
  expect(within(news).getByText('No suitable saved sources for this research area. It will not be included.')).toBeTruthy();
  await user.click(screen.getByRole('checkbox', {name:/Evaluate against my portfolio/}));
  await user.selectOptions(screen.getByLabelText('Portfolio snapshot'), 'portfolio1');
  await visitScope(user);
  expect((screen.getByLabelText('Research date & time (UTC)') as HTMLInputElement).value).toBe('2026-09-01T00:00');
  expect((screen.getByLabelText('Research date & time (UTC)') as HTMLInputElement).disabled).toBe(true);
  await visitData(user);
  await user.selectOptions(screen.getByLabelText('Risk policy version'), 'policy1:1');
  await user.type(screen.getByLabelText('Owner target weight (0–1)'), '0.2');
  await user.click(await within(screen.getByRole('group', {name:'Price & trend'})).findByRole('checkbox'));
  await visitReview(user);
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
  await inspectSources(user);
  const advanced = screen.getByText('Advanced data settings');
  expect(advanced.closest('details')?.open).toBe(false);
  await user.click(advanced);
  expect((screen.getByLabelText('Maximum source age (seconds)') as HTMLInputElement).value).toBe('604800');
  expect(screen.getByLabelText('Maximum source age (seconds)').closest('details')?.open).toBe(true);
  await user.click(await within(await screen.findByRole('group',{name:'Price & trend'})).findByRole('checkbox'));
  await visitReview(user);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await user.click(screen.getByRole('button',{name:'Queue analysis'}));
  await screen.findByRole('alert');
  const calls = fetch.mock.calls as unknown as [string, RequestInit][];
  const body = JSON.parse(calls.find(([url])=>url.endsWith('/runs'))![1].body as string);
  expect(body.analysis_as_of).toBe('2026-08-31T13:45:12.123Z');
  expect(body.decision_inputs.source_max_age_seconds).toEqual({market:604800});
  await visitScope(user);
  fireEvent.change(date,{target:{value:''}});
  await visitReview(user);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
});
it('disables stale evidence', async () => {
  setup(true); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  await inspectSources(userEvent.setup());
  const group = await screen.findByRole('group', { name: 'Price & trend' });
  expect((await within(group).findByRole('checkbox') as HTMLInputElement).disabled).toBe(true);
});
it('reuses idempotency key on unchanged failed submission', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  await inspectSources(user);
  const group = await screen.findByRole('group', { name: 'Price & trend' });
  await user.click(await within(group).findByRole('checkbox'));
  await visitReview(user);
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
  await visitReview(user);
  await screen.findByText(/To continue, prepare/);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await inspectSources(user);
  await user.click(screen.getByRole('button',{name:'Prepare latest prices'}));
  await screen.findByText(/Prices are ready/);
  await waitFor(()=>expect((screen.getByRole('group',{name:'Price & trend'}).querySelector('input') as HTMLInputElement).checked).toBe(true));
  await visitReview(user);
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
  await inspectSources(user);
  await user.click(await within(await screen.findByRole('group',{name:'Price & trend'})).findByRole('checkbox'));
  await visitReview(user);
  await user.click(screen.getByRole('checkbox',{name:/I authorize/}));
  await visitData(user);
  await user.click(await screen.findByRole('button',{name:'Add recent headlines'}));
  expect(await screen.findByText(/not a complete record of all news/)).toBeTruthy();
  await waitFor(() => expect((within(screen.getByRole('group',{name:'News & events'})).getByRole('checkbox') as HTMLInputElement).checked).toBe(true));
  expect((within(screen.getByRole('group',{name:'Price & trend'})).getByRole('checkbox') as HTMLInputElement).checked).toBe(true);
  await visitReview(user);
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
  await inspectSources(user);
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
  await inspectSources(user);
  await user.click(await screen.findByRole('button',{name:'Add SEC fundamentals'}));
  expect(await screen.findByText(/reported US GAAP tags, not a complete company profile/)).toBeTruthy();
  await waitFor(() => expect((within(screen.getByRole('group',{name:'Business fundamentals'})).getByRole('checkbox') as HTMLInputElement).checked).toBe(true));
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/runs'))).toBe(false);
  await visitReview(user);
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
  await visitData(user);
  await user.click(screen.getByRole('button',{name:'Prepare latest prices'}));
  await screen.findByText(/Data is not ready yet. Retrying automatically/);
  await visitReview(user);
  expect((screen.getByRole('button',{name:'Queue analysis'}) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('button',{name:'Stop automatic retries'}));
  await visitData(user);
  await screen.findByText(/Automatic retries stopped/);
});
