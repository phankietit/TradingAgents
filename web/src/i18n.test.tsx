import { act, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import ts from 'typescript';
import { setLocale, t } from './i18n';
import { vietnamese } from './messages';
import LanguageSwitch from './LanguageSwitch';
import App from './App';
import Markets from './Markets';
import Portfolio, { decimal } from './Portfolio';
import Decisions from './Decisions';
import ArtifactPreview from './ArtifactPreview';
import { number, timestamp } from './data';
import { qualityLabel, reviewStatus, riskReason } from './financialLabels';

afterEach(() => { vi.unstubAllGlobals(); window.location.hash = ''; });
const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });

it('localizes login without clearing input or sending credentials on language change', async () => {
  const fetch = vi.fn(async () => json({}, 401)); vi.stubGlobal('fetch', fetch);
  const user = userEvent.setup(); render(<App />);
  const email = await screen.findByLabelText('Owner email');
  await user.type(email, 'fixture@example.invalid');
  const password = screen.getByLabelText('Password'); await user.type(password, 'synthetic-only-password');
  const count = fetch.mock.calls.length;
  await user.click(screen.getByRole('button', { name: /VI/ }));
  expect(document.documentElement.lang).toBe('vi');
  expect(localStorage.getItem('tradingagents.ui-language.v1')).toBe('vi');
  expect(screen.getByRole('button', { name: 'Đăng nhập' })).toBeTruthy();
  expect((screen.getByLabelText('Mật khẩu') as HTMLInputElement).value).toBe('synthetic-only-password');
  expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe('fixture@example.invalid');
  expect(fetch.mock.calls.length).toBe(count);
  expect(JSON.stringify(localStorage)).not.toContain('synthetic-only-password');
  await user.click(screen.getByRole('button', { name: /EN/ }));
  expect(screen.getByRole('button', { name: 'Sign in' })).toBeTruthy();
});

it('keeps asset group values stable when translated options are selected', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json([])));
  render(<><LanguageSwitch /><Markets /></>);
  fireEvent.click(screen.getByRole('button', { name: /VI/ }));
  const group = screen.getByLabelText('Nhóm tài sản') as HTMLSelectElement;
  fireEvent.change(group, { target: { value: 'Stocks' } });
  expect(group.value).toBe('Stocks');
  expect(group.selectedOptions[0].textContent).toBe('Cổ phiếu');
  expect(await screen.findByText(/Chưa có danh mục tài sản/)).toBeTruthy();
});

it.each([[Portfolio, 'Chưa có bản định giá danh mục'], [Decisions, 'Chọn đề xuất']] as const)('translates empty financial workspaces without implying zero data', async (View, title) => {
  vi.stubGlobal('fetch', vi.fn(async () => json([]))); setLocale('vi');
  render(<View />); expect(await screen.findByRole('heading', { name: title })).toBeTruthy();
});

it('preserves six data failure states, exact decimals, UTC and private source text', () => {
  setLocale('vi');
  expect(new Set(['OK', 'STALE', 'NO_DATA', 'COVERAGE_GAP', 'INVALID', 'UNAVAILABLE'].map(qualityLabel)).size).toBe(6);
  expect(reviewStatus('ready_for_approval')).not.toBe(reviewStatus('approved'));
  expect(decimal('-12345678901234567890.001')).toBe('-12.345.678.901.234.567.890,001');
  expect(number(1234.5)).toBe('1.234,50');
  expect(timestamp('2026-09-01T00:00:00Z')).toBe('2026-09-01 00:00:00 UTC');
  expect(riskReason('max_position_weight', 'FAIL', 'max_position_weight FAIL')).toContain('không đáp ứng');
  expect(riskReason('max_correlation', 'REVIEW', 'Private original reason')).toBe('Private original reason');
  expect(t('__proto__')).toBe('__proto__');
});

it('preserves original bilingual and legacy reports byte-for-text across UI languages', async () => {
  const narrative = 'English: Risk −10%, AAPL, USD.\nTiếng Việt: Rủi ro −10%, AAPL, USD.\n<img src=x onerror=alert(1)>';
  vi.stubGlobal('fetch', vi.fn(async () => json({ run_id: 'run', decision_id: '12345678-1234-1234-1234-123456789abc', profile: 'equity', reference_only: false,
    selected_analysts: ['market'], snapshot_attestation: 'PASS', narrative, structured_narrative: null, report_language: 'en-vi' })));
  render(<><LanguageSwitch /><ArtifactPreview runId="run" artifact={{ artifact_id: 'report', kind: 'analysis_report', media_type: 'application/json', content_hash: 'fixture', byte_size: 500, created_at: '2026-09-01' }} /></>);
  fireEvent.click(screen.getByRole('button', { name: 'Inspect analysis report' }));
  await screen.findByText(/English: Risk/);
  const original = document.querySelector('.narrative')!;
  expect(original.textContent).toBe(narrative);
  fireEvent.click(screen.getByRole('button', { name: /VI/ }));
  expect(original.textContent).toBe(narrative);
  expect(screen.getByText(/Báo cáo gốc · Ngôn ngữ yêu cầu: Anh \+ Việt/)).toBeTruthy();
  expect(document.querySelector('img')).toBeNull();
});

it('works when preference storage is blocked and does not persist other data', () => {
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  render(<LanguageSwitch />);
  act(() => setLocale('vi'));
  expect(screen.getByRole('button', { name: /VI/ }).getAttribute('aria-pressed')).toBe('true');
  expect(t('Markets')).toBe('Thị trường');
});

it('has Vietnamese copy for every literal translation call in application source', () => {
  const missing: string[] = [];
  for (const file of readdirSync('src').filter(name => /\.tsx?$/.test(name) && !name.includes('.test.'))) {
    const source = ts.createSourceFile(file, readFileSync(`src/${file}`, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    function visit(node: ts.Node) {
      if (ts.isCallExpression(node) && node.expression.getText(source) === 't' && node.arguments[0] && ts.isStringLiteral(node.arguments[0])) {
        const key = node.arguments[0].text.trim();
        if (!Object.hasOwn(vietnamese, key)) missing.push(`${file}: ${key}`);
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
  }
  expect(missing).toEqual([]);
});
