# TradingAgents In-Progress Coordination

Use this file only when multiple active agents or worktrees need repository-local
coordination. GitHub issue/Project status remains the durable task record.

Do not add an entry during read-only audit or planning unless execution has
actually started. Remove completed entries after their PR/branch state is safely
recorded in GitHub history.

| Issue | Owner/task | Branch | Worktree | Scope | Status | Updated UTC |
| --- | --- | --- | --- | --- | --- | --- |
| R01–R14 | current thread | fix/TA-R01-research-quality | /Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents | Full88556 at37c1a42 terminal3306PASS/88subtests/2optionalUNVERIFIED, ownedcleanup confirmed; prior4FAIL retained; ownedside fast-forward cf37fde after terminal, backend unchanged, exact integrated build/lint221webPASS; live/financial/VI/operator/version gates open, DraftPR7 wholegoal incomplete | in-progress | 2026-10-08 |
| R08/R13/R14 | current thread isolated polling, regression repair and handoff | fix/TA-R07-summary-provenance | /Volumes/Data/codex/worktrees/ta-r08-recovery-ui/TradingAgents | 0d1dbc2 artifact identity isolation: red5FAIL retained, focused41PASS/cleanbuildlint221PASS/browser73027 PASS; original fabPG9230 scopedPASS/earlierFAIL retained; ownedfixture24423 cleanup confirmed; ingestion guide reconciled with implemented SEC/FRED/social and per-source deadlines, docs-only; general cancel/retry/native/live/operator gates open; side-only primary37c1a42 full88556 live/latest40% | in-progress | 2026-10-08 |

Rules:

- Read this table before editing overlapping files.
- Never modify or delete another owner's entry.
- One row owns only the scope it names, not the whole repository.
- If file or contract ownership overlaps, stop and coordinate before editing.
- Allowed status values: `in-progress`, `ready-for-pr`, `pr-open`, `blocked`,
  and `aborted`.
- Never include secrets, private portfolio data, or local credential paths.
