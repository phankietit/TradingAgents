# TradingAgents Release Readiness Contract

## Release Classes

| Class | Meaning |
| --- | --- |
| Research package | Python package/CLI usable for manual research |
| Private platform | Authenticated owner-only web/API/worker system |
| Paper decision system | Portfolio ledger and simulated orders, no real money |
| Live decision support | Current data and owner-approved proposals, no automatic execution |
| Live execution | Broker orders; out of scope until separately approved |

Every release must name its class. Never describe a research-package release as
a production portfolio or trading release.

## Current Candidate Boundary

The current repository may release the research package/CLI after its existing
test, lint, and clean-install gates pass. It is not currently eligible for a
private-platform, paper-portfolio, or live-execution designation.

## General Release Gates

- Candidate is a fixed, reviewed commit SHA.
- Worktree is clean except documented release artifacts outside Git.
- Scope-appropriate verification is current on that SHA.
- Changelog and user-facing docs match actual behavior.
- Dependency and runtime requirements are explicit.
- No secret, portfolio file, cache, checkpoint, generated report, or model
  artifact is committed or packaged unintentionally.
- Known failures and blocked external gates are listed.
- Performance language matches the available evidence.

## Private Platform Gates

In addition to general gates:

- Authentication and owner authorization.
- Durable database, job queue, artifact storage, backup, and restore.
- Immutable per-run configuration and evidence manifest.
- Private-data redaction in logs and analytics.
- Security/threat-model review and operational monitoring.
- Rollback and incident procedures.

## Paper Decision Gates

- Deterministic portfolio ledger and order simulator.
- Cash, fills, fees, slippage, corporate actions, and reconciliation.
- Risk-limit invariants and kill switch.
- Explicit paper labels in UI, logs, and exports.
- No path from paper approval to a live broker credential.

## Live Boundary

Live broker integration and execution require a new approved contract. They may
not be introduced as a small extension to research or paper scope. Until that
contract exists:

- No broker write credential.
- No order submission endpoint.
- No scheduled automatic execution.
- No model-controlled approval.
- No claim that generated decisions are suitable for unattended trading.

## Release Evidence

The handoff must include:

- Release class, version, branch, and full SHA.
- Included issues/PRs.
- Verification matrix with exact statuses.
- Runtime/provider/data limitations.
- Security and data-integrity results.
- Deployment/publication state.
- Owner actions still required.

A release is not complete merely because artifacts were built. Publication,
deployment, live-provider configuration, and owner approvals remain separate
gates.
