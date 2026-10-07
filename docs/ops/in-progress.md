# TradingAgents In-Progress Coordination

Use this file only when multiple active agents or worktrees need repository-local
coordination. GitHub issue/Project status remains the durable task record.

Do not add an entry during read-only audit or planning unless execution has
actually started. Remove completed entries after their PR/branch state is safely
recorded in GitHub history.

| Issue | Owner/task | Branch | Worktree | Scope | Status | Updated UTC |
| --- | --- | --- | --- | --- | --- | --- |
| R01–R14 | current thread | fix/TA-R01-research-quality | /Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents | Full51929 terminal4FAIL3302PASS retained/ownedcleanup confirmed; ownedside2ab3411 fast-forward integrated with UI212 primaryPASS and explicitV2 fixture focused103PASS; new defaultfull pending; DraftPR7/wholegoal incomplete | in-progress | 2026-10-08 |
| R08/R13 | current thread isolated polling and regression repair | fix/TA-R07-summary-provenance | /Volumes/Data/codex/worktrees/ta-r08-recovery-ui/TradingAgents | Slow-poll fab4a03 web215PASS; first-render observer21730/56649 PASS incl15s driverlag proving old total-count oracle can misclassify serial polling; <=2 first-render bound/deadlines kept, first61184 FAIL causeUNVERIFIED retained; side-only while primary37c1a42 full88556 live; broader concurrent/PG/live/operator gates open | in-progress | 2026-10-08 |

Rules:

- Read this table before editing overlapping files.
- Never modify or delete another owner's entry.
- One row owns only the scope it names, not the whole repository.
- If file or contract ownership overlaps, stop and coordinate before editing.
- Allowed status values: `in-progress`, `ready-for-pr`, `pr-open`, `blocked`,
  and `aborted`.
- Never include secrets, private portfolio data, or local credential paths.
