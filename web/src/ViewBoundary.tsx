import { Component } from 'react';
import type { ReactNode } from 'react';

/** Keep navigation/session controls available; never display raw exceptions. */
export default class ViewBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) return <section className="empty-state" role="alert">
      <h2>This view could not be displayed</h2>
      <p>No financial conclusion is available from this view. You can retry or choose another workspace. No action will be submitted automatically.</p>
      <button onClick={() => this.setState({ failed: false })}>Retry display</button>
    </section>;
    return this.props.children;
  }
}
