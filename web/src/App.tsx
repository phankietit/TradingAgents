import { useEffect, useState } from 'react';
import { SessionBoundary } from './auth';
import { errorMessage } from './api';
import type { Owner } from './api';
import Markets from './Markets';
import Analysis from './Analysis';

const pages = ['Markets', 'Analysis', 'Portfolio', 'Decisions'] as const;
type Page = typeof pages[number];
function currentPage(): Page | null {
  const slug = window.location.hash.slice(1).split('?')[0] || '/markets';
  return pages.find(page => `/${page.toLowerCase()}` === slug) ?? null;
}

function Workspace({ owner, logout }: { owner: Owner; logout: () => Promise<void> }) {
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
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>Skip to content</a>
    <aside className="rail">
      <div className="wordmark">TradingAgents<span className="brand-dot" aria-hidden="true" /></div>
      <nav aria-label="Workspace">{pages.map((name, index) => <a key={name} href={`#/${name.toLowerCase()}`} aria-current={page === name ? 'page' : undefined}>
        <span className="nav-index" aria-hidden="true">0{index + 1}</span>{name}
      </a>)}</nav>
      <div className="account"><span className="muted">Owner account</span><span className="owner-email">{owner.email}</span>
        <button onClick={signOut} disabled={pending}>{pending ? 'Signing out…' : 'Sign out'}</button>
        {error ? <p role="alert" className="danger">{error}</p> : null}
      </div>
    </aside>
    <main id="main-content" tabIndex={-1}>
      <header className="workspace-header"><h1>{page ?? 'Page not found'}</h1><span className="muted">Local research workspace</span></header>
      <div className="page-content">
        {page === 'Markets' ? <Markets /> : page === 'Analysis' ? <Analysis /> : <section className="empty-state"><h2>{page ? `${page} workspace is being connected` : 'This workspace does not exist'}</h2>
          <p>{page ? 'Session authentication is active. Data views are not available in this implementation checkpoint.' : 'Choose a workspace from the navigation.'}</p>
        </section>}
      </div>
      <footer className="workspace-footer">Decision support · No order execution</footer>
    </main>
  </div>;
}

export default function App() {
  return <SessionBoundary>{(owner, logout) => <Workspace key={owner.owner_id} owner={owner} logout={logout} />}</SessionBoundary>;
}
