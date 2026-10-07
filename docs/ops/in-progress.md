# TradingAgents In-Progress Coordination

Use this file only when multiple active agents or worktrees need repository-local
coordination. GitHub issue/Project status remains the durable task record.

Do not add an entry during read-only audit or planning unless execution has
actually started. Remove completed entries after their PR/branch state is safely
recorded in GitHub history.

| Issue | Owner/task | Branch | Worktree | Scope | Status | Updated UTC |
| --- | --- | --- | --- | --- | --- | --- |
| R01–R14 | current thread | fix/TA-R01-research-quality | /Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents | Canonical report/localization remediation, operational UX, live BTC/AAPL/NQ acceptance; Draft PR #7 | in-progress | 2026-10-07 |
| R14 | current thread, isolated API entrypoint | fix/TA-R14-api-startup | /Volumes/Data/codex/worktrees/ta-r08-recovery-ui/TradingAgents | Fix installed API help/argument admission before environment/service startup; primary e3b837b frozen under full3309, no integration until terminal | in-progress | 2026-10-07 |

Rules:

- Read this table before editing overlapping files.
- Never modify or delete another owner's entry.
- One row owns only the scope it names, not the whole repository.
- If file or contract ownership overlaps, stop and coordinate before editing.
- Allowed status values: `in-progress`, `ready-for-pr`, `pr-open`, `blocked`,
  and `aborted`.
- Never include secrets, private portfolio data, or local credential paths.
