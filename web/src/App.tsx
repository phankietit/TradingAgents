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
      <div className="wordmark">TradingAgents<span className="brand-dot" aria-hidden="true" /></div>
      <nav aria-label={t("Workspace")}>{pages.map((name, index) => <a key={name} href={`#/${name.toLowerCase()}`} aria-current={page === name ? "page" : undefined}>
        <span className="nav-index" aria-hidden="true">0{index + 1}</span>{t(name)}
      </a>)}</nav>
      <div className="account"><span className="muted">{t("Owner account")}</span><span className="owner-email">{owner.email}</span>
        <button onClick={signOut} disabled={pending}>{pending ? t("Signing out…") : t("Sign out")}</button>
        {error ? <p role="alert" className="danger">{t(error)}</p> : null}
      </div>
    </aside>
    <main id="main-content" tabIndex={-1}>
      <header className="workspace-header"><h1>{t(page ?? 'Page not found')}</h1><LanguageSwitch /></header>
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
