# Security Policy

## Supported Scope

Security fixes target the current `main` branch unless a release-specific
exception is documented.

## Reporting A Vulnerability

Do not open a public issue containing credentials, exploitable details, private
portfolio information, or a working proof of concept. Prefer GitHub's private
security advisory/reporting flow for this repository. If private reporting is
not available, contact the repository owner privately before sharing details.

Include:

- Affected commit/version and component.
- Impact and attacker prerequisites.
- Minimal reproduction steps.
- Whether secrets, private portfolio data, provider accounts, filesystem paths,
  or network destinations are exposed.
- Suggested mitigation, if known.

Never include live API keys, broker tokens, account identifiers, or private
portfolio contents in the report.

## High-Priority Classes

- Credential or secret disclosure.
- Cross-user portfolio/account data access.
- Prompt injection that can change tools, policies, destinations, or approval.
- SSRF, arbitrary file access, path traversal, or unsafe deserialization.
- Point-in-time bypass that contaminates historical evaluation.
- Risk-policy bypass or order execution without human approval.
- Dependency/container compromise affecting published artifacts.

## Development Contract

Repository security rules and verification expectations live in
`docs/ops/security-development.md`. A local or mocked test does not by itself
prove a live provider, deployment, or broker boundary secure.
