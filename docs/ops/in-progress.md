# TradingAgents In-Progress Coordination

Use this file only when multiple active agents or worktrees need repository-local
coordination. GitHub issue/Project status remains the durable task record.

Do not add an entry during read-only audit or planning unless execution has
actually started. Remove completed entries after their PR/branch state is safely
recorded in GitHub history.

| Issue | Owner/task | Branch | Worktree | Scope | Status | Updated UTC |
| --- | --- | --- | --- | --- | --- | --- |
| R01–R14 | current thread | fix/TA-R01-research-quality | /Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents | V2/operator/session sidec32662f integrated after uninstrumented full73101 PASS on cfd31da and owned cleanup; integrated native resume/full/browser/live/UX/operator acceptance pending; Draft PR7; whole goal incomplete | in-progress | 2026-10-08 |
| R08 | current thread isolated UI | fix/TA-R07-summary-provenance | /Volumes/Data/codex/worktrees/ta-r08-recovery-ui/TradingAgents | Compact mobile context289de45 build/lint/default190/serial190 and synthetic desktop/mobile readback PASS; prior timeout/viewport FAIL receipts preserved; side-only pending primary frozen full51929 and broader UI-process/decision/live/operator acceptance | in-progress | 2026-10-08 |

Rules:

- Read this table before editing overlapping files.
- Never modify or delete another owner's entry.
- One row owns only the scope it names, not the whole repository.
- If file or contract ownership overlaps, stop and coordinate before editing.
- Allowed status values: `in-progress`, `ready-for-pr`, `pr-open`, `blocked`,
  and `aborted`.
- Never include secrets, private portfolio data, or local credential paths.
