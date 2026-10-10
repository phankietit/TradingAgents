import { t, useLocale } from './i18n';
import { useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { ApiError, errorMessage, mutate, request, SESSION_EXPIRED, validateOwner } from './api';
import type { Owner } from './api';
import LanguageSwitch from './LanguageSwitch';

export function SessionBoundary({ children }: { children: (owner: Owner, logout: () => Promise<void>) => ReactNode }) {
  useLocale();
  const [owner, setOwner] = useState<Owner | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const expired = () => { setOwner(null); setError('Your session ended. Sign in again.'); };
    window.addEventListener(SESSION_EXPIRED, expired);
    setLoading(true);
    request<Owner>('/auth/me', { signal: controller.signal })
      .then(validateOwner).then(value => { if (!controller.signal.aborted) { setOwner(value); setError(''); } })
      .catch(cause => {
        if (!controller.signal.aborted) setError(cause instanceof ApiError && cause.status === 401 ? '' : errorMessage(cause));
      }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); window.removeEventListener(SESSION_EXPIRED, expired); };
  }, [attempt]);
  if (loading) return <main className="session-screen" aria-busy="true"><p role="status">{t("Restoring your session…")}</p></main>;
  if (!owner) return <Login initialError={error} onLogin={setOwner} onRetry={() => setAttempt(value => value + 1)} />;
  return children(owner, async () => {
    await mutate('/auth/logout');
    setOwner(null); setError('');
  });
}

function Login({ initialError, onLogin, onRetry }: { initialError: string; onLogin: (owner: Owner) => void; onRetry: () => void }) {
  useLocale();
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    setPending(true); setError('');
    try {
      const value = await request<Owner>('/auth/login', { method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: fields.get('email'), password: fields.get('password') }),
      });
      form.reset(); onLogin(validateOwner(value));
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 401 ? 'Email or password is incorrect.' : errorMessage(cause));
      const password = form.elements.namedItem('password');
      if (password instanceof HTMLInputElement) { password.value = ''; password.focus(); }
    } finally { setPending(false); }
  }
  return <main className="session-screen"><section className="login" aria-labelledby="login-title">
    <div className="wordmark">TradingAgents<span className="brand-dot" aria-hidden="true" /></div>
    <LanguageSwitch />
    <h1 id="login-title">{t("Your research workspace.")}</h1>
    <p className="muted">{t("Sign in to review markets, evidence and portfolio decisions.")}</p>
    <form onSubmit={submit} aria-busy={pending}>
      <label>{t("Owner email")}<input name="email" type="email" autoComplete="username" required maxLength={254} disabled={pending} /></label>
      <label>{t("Password")}<input name="password" type="password" autoComplete="current-password" required maxLength={1024} disabled={pending} /></label>
      {error || initialError ? <p className="notice danger" role="alert">{t(error || initialError)}</p> : null}
      <button className="primary" disabled={pending}>{pending ? t("Signing in…") : t("Sign in")}</button>
    </form>
    {initialError ? <button className="text-button" onClick={onRetry}>{t("Retry connection")}</button> : null}
    <p className="login-footer">{t("Local research workspace")}<br />{t("Decision support · No order execution")}</p>
  </section></main>;
}
