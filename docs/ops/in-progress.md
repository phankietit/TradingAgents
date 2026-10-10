# TradingAgents In-Progress Coordination

Use this file only when multiple active agents or worktrees need repository-local
coordination. GitHub issue/Project status remains the durable task record.

Do not add an entry during read-only audit or planning unless execution has
actually started. Remove completed entries after their PR/branch state is safely
recorded in GitHub history.

| Issue | Owner/task | Branch | Worktree | Scope | Status | Updated UTC |
| --- | --- | --- | --- | --- | --- | --- |
| R01–R14 | current thread | fix/TA-R01-research-quality | /Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents | Frozen c0268c7 full3.10 session65550 terminal3306PASS/88subtests/2optionalUNVERIFIED, ownedcleanup confirmed; full3.12/3.14/web and encrypted source-migration receipts retained; original matrix3.11/3.13 open; no API/worker restart or approved paid runs submitted, separate restart approval pending; live/financial/VI/broader restore/runtime gates open, DraftPR7 whole goal incomplete | in-progress | 2026-10-10 |

Rules:

- Read this table before editing overlapping files.
- Never modify or delete another owner's entry.
- One row owns only the scope it names, not the whole repository.
- If file or contract ownership overlaps, stop and coordinate before editing.
- Allowed status values: `in-progress`, `ready-for-pr`, `pr-open`, `blocked`,
  and `aborted`.
- Never include secrets, private portfolio data, or local credential paths.
