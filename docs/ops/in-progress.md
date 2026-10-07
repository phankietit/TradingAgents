# TradingAgents In-Progress Coordination

Use this file only when multiple active agents or worktrees need repository-local
coordination. GitHub issue/Project status remains the durable task record.

Do not add an entry during read-only audit or planning unless execution has
actually started. Remove completed entries after their PR/branch state is safely
recorded in GitHub history.

| Issue | Owner/task | Branch | Worktree | Scope | Status | Updated UTC |
| --- | --- | --- | --- | --- | --- | --- |
| R01–R14 | current thread | fix/TA-R01-research-quality | /Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents | Canonical report/localization, native reliability, operational UX and live acceptance; Draft PR7; full18967 terminal PASS instrumented02ed0cc, owned PG cleanup confirmed; staged UX integrated2766a48 afterwards; whole goal incomplete | in-progress | 2026-10-08 |
| R11 | current thread, isolated UX continuation | fix/TA-R11-staged-workspace | /Volumes/Data/codex/worktrees/ta-r08-recovery-ui/TradingAgents | Staged setup integrated into primary after full18967 terminal; exact side2a8d739 web179PASS; professional whole journey and live quality still open; no overlapping side edits while primary owns integration | in-progress | 2026-10-08 |
| R14 | current thread, isolated dependency patch | fix/TA-R14-source-map-patch | /Volumes/Data/codex/worktrees/ta-r08-recovery-ui/TradingAgents | source-map-js GHSA-68fv-2mgg-jv7q patch only, base dc66744; source-map parser regressions and full web verification; no provider/graph/policy change | in-progress | 2026-10-08 |

Rules:

- Read this table before editing overlapping files.
- Never modify or delete another owner's entry.
- One row owns only the scope it names, not the whole repository.
- If file or contract ownership overlaps, stop and coordinate before editing.
- Allowed status values: `in-progress`, `ready-for-pr`, `pr-open`, `blocked`,
  and `aborted`.
- Never include secrets, private portfolio data, or local credential paths.
