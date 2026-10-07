# Continuation checkpoint — 2026-10-08

This is a dated navigation checkpoint for the private R01–R14 draft, not a
release verdict or timeless statement of current Git/runtime state. Refresh
the remote branches, PR and [HANDOFF](../../HANDOFF.md) before continuing.
Read [AGENTS](../../AGENTS.md) and the [routing map](../ops/agent-map.md) first.

## Source and integration boundary

| Source | Verified checkpoint at this writing | Meaning |
| --- | --- | --- |
| `fix/TA-R01-research-quality` | `796c4178c3c710fba32eb20651c5ace7d46e71a7` | Primary candidate, frozen for the Python 3.12 full gate |
| `fix/TA-R07-summary-provenance` | `718563a2281857fa08a70f7a38aca038690f8f0c` | Side checkpoint; pending-cancel UX application commit is `a6917d31d5bc650a215c3731cf43f61b9d275a02`, not yet integrated into primary |
| `origin/main` | `7dfec4d20709a702b130f3ba5813f097a930ffe6` | Integration/release line, not the unfinished draft |

[PR #7](https://github.com/phankietit/TradingAgents/pull/7) remains OPEN/DRAFT.
No main merge, deployment, release or production-ready declaration is implied.
This document is a later side-branch documentation change, not part of the
listed source checkpoints. Do not reset or overwrite dirty work to match them.

## Evidence to preserve

| Gate | Exact source and result | Boundary |
| --- | --- | --- |
| Default full PostgreSQL/Python 3.14.7 | `37c1a423ef20e53b6fab692021fdd440279f4ade`: PASS, 3,306 tests + 88 subtests; 2 optional checks UNVERIFIED; 3,355.28 seconds | Prior four-test FAIL receipt is retained; not a supported-version matrix or live financial pass |
| Integrated web build/lint/full tests | `cf37fde9aa2c2e2400854c14d5525eb7b8ab1878`: PASS, 221 tests / 29 files | Backend source comparison with `37c1a42` passed; no newly executed full backend gate at `cf37fde` |
| Fresh noneditable installed package, Python 3.12.14 | Archive `b3779f8bdd9893a301f127a4d4f8812152c6f3df`: PASS, isolated imports/resources, pip check, API/worker/CLI help | No private environment/runtime copied; smoke is not the full installed-package suite |
| Default full PostgreSQL/Python 3.12.14 | Frozen primary `796c4178c3c710fba32eb20651c5ace7d46e71a7`: UNVERIFIED, session `41168` still live when checked | Source-checkout tests use the fresh interpreter; await terminal output and owned cleanup before changing primary |
| Side pending-cancel UX | `a6917d31d5bc650a215c3731cf43f61b9d275a02`: PASS, build/lint/225 tests and scoped real-PG EN/VI browser cancellation | Synthetic graph, one run POST / one cancel POST, no model/vendor calls; not general cancellation/recovery or final-report acceptance |

Commands, retained failures, runtime details and cleanup receipts are in
[HANDOFF](../../HANDOFF.md) and the PR comments. Local session/PID/container
identifiers are not portable to another machine. Confirm the original process's
terminal state with its operator; silence or a polling timeout does not authorize
restarting, killing or modifying its frozen checkout.

## Continuing on another machine

1. Inspect fetched branches, exact SHA, dirty state and
   [ownership](../ops/in-progress.md). Preserve the side integration boundary.
   Do not infer that a Git clone contains the owner's investment workspace.
2. Follow [local startup](local-web-startup.md), [.env.example](../../.env.example)
   and [local verification](local-verification.md) for the chosen environment.
   Keep real keys/contact details in ignored local files or a secret manager.
   Confirm existing provider/model/configuration rather than selecting a new one.
3. Git contains source and redacted receipts, **not** `.env`, database, artifact
   store, snapshots, reports, checkpoints or private portfolio history. A source
   clone is not a restored workspace. Never substitute synthetic fixtures for
   investment data or bootstrap/reset an existing owner database.
4. For owner data, use the [backup/restore contract](operator-backup-restore.md).
   It is a procedure, not an implemented backup CLI or passed operator gate.
   Source/new empty target, authenticated encryption, destination/key custody,
   retention, maintenance window and worker restart require owner decisions.
   Public Git handoff does not approve private transfer or paid-job replay.
5. Keep workers off until restore/session/job/checkpoint/budget uncertainty is
   audited and restart is approved. API startup alone does not stop other workers.
   A copied reservation or consent does not authorize a new paid attempt.

## Still required for the full goal

- R05/R06 live financial output and R12 live Vietnamese editorial quality retain
  their FAIL evidence. New local guards/tests do not erase those failures.
- R07 general qualitative/causal/predictive entailment is UNVERIFIED. Correct
  source IDs alone do not prove that a conclusion follows from those sources.
- R08 broader native cancellation/race/retry/expiry/recovery, R11 complete
  professional live journey and final-report UX, and R13 remaining runtime
  coverage require their own evidence.
- R14 authenticated encrypted transfer, key recovery, copied-session fencing,
  active/queued work audit, restored browser readback and authorized restart are
  UNVERIFIED; scoped synthetic restore tests cannot waive them.
- NQ=F live acceptance remains owner-BLOCKED pending eligible active-contract/
  rollover metadata. Do not substitute an index or add a provider.
- Actual SEC contact for AAPL and fresh authorization for further paid BTC/AAPL
  acceptance runs remain pending at this checkpoint. Do not invent a contact,
  spend automatically, reduce the original flow or change provider/model.

The goal remains ACTIVE and keeps the complete R01–R14 scope. Continue safe
local work while respecting external gates; do not redefine completion around
the passing subset. No CI, broker/execution, public deployment, provider/risk
change or private-history overwrite is authorized.
