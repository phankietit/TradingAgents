import { t, useLocale } from './i18n';
import { useEffect, useState } from 'react';
import { SessionBoundary } from './auth';
import { errorMessage } from './api';
import type { Owner } from './api';
import Markets from './Markets';
import Analysis from './Analysis';
import Portfolio from './Portfolio';
import Decisions from './Decisions';
import ViewBoundary from './ViewBoundary';
import LanguageSwitch from './LanguageSwitch';

const pages = ['Markets', 'Analysis', 'Portfolio', 'Decisions'] as const;
const descriptions = {
  Markets: 'A clearer view of the market.', Analysis: 'From evidence to a considered view.',
  Portfolio: 'Your capital, in context.', Decisions: 'Conviction, with the evidence to question it.',
};
type Page = typeof pages[number];
function currentPage(): Page | null {
  const slug = window.location.hash.slice(1).split('?')[0] || '/markets';
  return pages.find(page => `/${page.toLowerCase()}` === slug) ?? null;
}

function Workspace({ owner, logout }: { owner: Owner; logout: () => Promise<void> }) {
  useLocale();
  const [page, setPage] = useState(currentPage);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  useEffect(() => {
    const update = () => setPage(currentPage());
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);
  async function signOut() {
    setPending(true); setError('');
    try { await logout(); } catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(false); }
  }
  return <div className="workspace">
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>{t("Skip to content")}</a>
    <aside className="rail">
      <div className="wordmark"><span className="brand-mark" aria-hidden="true">t.</span>TradingAgents</div>
      <p className="rail-caption">{t('PRIVATE RESEARCH')}</p>
      <nav aria-label={t("Workspace")}>{pages.map((name, index) => <a key={name} href={`#/${name.toLowerCase()}`} aria-current={page === name ? "page" : undefined}>
        <svg className="nav-icon" aria-hidden="true" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">{index === 0 ? <path d="M3 15V9m5 6V4m5 11V7m4 8V2" /> : index === 1 ? <><rect x="4" y="2" width="12" height="16" rx="2" /><path d="M7 6h6M7 10h6m-6 4h3" /></> : index === 2 ? <><rect x="2" y="6" width="16" height="11" rx="2" /><path d="M7 6V3h6v3M2 11h16m-9 0v2h2v-2" /></> : <><circle cx="10" cy="10" r="7" /><path d="m6.5 10 2.5 2.5 4.5-5" /></>}</svg>{t(name)}
      </a>)}</nav>
      <div className="account"><span className="muted">{t("Owner account")}</span><span className="owner-email">{owner.email}</span>
        <button onClick={signOut} disabled={pending}>{pending ? t("Signing out…") : t("Sign out")}</button>
        {error ? <p role="alert" className="danger">{t(error)}</p> : null}
      </div>
    </aside>
    <main id="main-content" tabIndex={-1}>
      <header className="workspace-header"><div><p className="eyebrow">{t('YOUR RESEARCH WORKSPACE')}</p><h1>{t(page ?? 'Page not found')}</h1>{page ? <p className="page-description">{t(descriptions[page])}</p> : null}</div><LanguageSwitch /></header>
      <div className="page-content">
        <ViewBoundary key={page}>
        {page === 'Markets' ? <Markets /> : page === 'Analysis' ? <Analysis /> : page === 'Portfolio' ? <Portfolio /> : page === 'Decisions' ? <Decisions /> : <section className="empty-state"><h2>{t("This workspace does not exist")}</h2>
          <p>{page ? t("Session authentication is active. Data views are not available in this implementation checkpoint.") : t("Choose a workspace from the navigation.")}</p>
        </section>}
        </ViewBoundary>
      </div>
      <footer className="workspace-footer">{t("Decision support · No order execution")}</footer>
    </main>
  </div>;
}

export default function App() {
  useLocale();
  return <SessionBoundary>{(owner, logout) => <Workspace key={owner.owner_id} owner={owner} logout={logout} />}</SessionBoundary>;
}
