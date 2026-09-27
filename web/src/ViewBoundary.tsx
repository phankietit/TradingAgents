import { t } from './i18n';
import { Component } from 'react';
import type { ReactNode } from 'react';

/** Keep navigation/session controls available; never display raw exceptions. */
export default class ViewBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) return <section className="empty-state" role="alert">
      <h2>{t("This view could not be displayed")}</h2>
      <p>{t("No financial conclusion is available from this view. You can retry or choose another workspace. No action will be submitted automatically.")}</p>
      <button onClick={() => this.setState({ failed: false })}>{t("Retry display")}</button>
      <p className="muted caption">{t('If the app was updated, reload to obtain the latest version. Unsaved form entries will be cleared.')}</p>
      <button onClick={() => window.location.reload()}>{t('Reload application')}</button>
    </section>;
    return this.props.children;
  }
}
