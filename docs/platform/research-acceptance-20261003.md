# Research acceptance checkpoint — 2026-10-03

Branch `fix/TA-R01-research-quality`, source
`c705cad32c3e6579c94942d8131ea32f0ac34def`. Private platform candidate remains
incomplete; Draft PR #7 remains draft. No deployment, provider/risk-limit
change, historical rewrite, worker restart or paid/vendor call.

## R08 recovery fingerprint construction prerequisite

New internal `recovery_fingerprint.py` is not wired to the worker, API or CLI.
It constructs a separate digest; existing API config_hash and immutable run
history remain unchanged. Owner/run/instrument/as-of/ordered analysts, source
IDs/freshness and revalidated payload hashes bind to the original request.
The digest includes source manifests, full portfolio/policy content, rendered
book, risk-source content hashes, language/allowance, effective configuration,
native graph options/analyst plan, supplied resolved-client descriptors,
actual Python-package source bytes and installed runtime/dependency versions.

| Gate | Status | Evidence |
| --- | --- | --- |
| Identity construction / mismatch rejection | PASS | 44 focused tests, 5.47 s: effective config/model/provider/endpoint, owner/instrument/date/roles, source changes/corruption/future availability, original run/allowance/prompt, runtime, risk and full book/policy binding |
| Existing JSON codec coupling | PASS | Changed risk-round fingerprint rejects previously encoded checkpoint before model reentry; client factory explicitly forbidden in this test |
| Privacy and relocation | PASS | Returns digest only, no SDK/network initialization. Credential-bearing/invalid URLs and common credential fields/unknown config keys rejected; fixed error text. Output/cache/memory paths do not change research identity; no CLI memory read |
| Actual runtime identity | PASS | Source-byte changes alter digest without changing Git HEAD or package version; Python and installed distribution versions bind. Package-source symlinks rejected, no env/credential file read |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,924 tests + 88 subtests, 20 skips, 22 warnings, 131.46 s; Python 3.14.7/macOS, clean c705cad source throughout gate |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby issue-template YAML load |
| PostgreSQL/optional providers | UNVERIFIED | Same 18 PostgreSQL, missing Bedrock dependency and live DeepSeek-key gates skipped |
| Web/CLI activation or live acceptance | NOT_IN_SCOPE | New internal prerequisite only; no frontend change, new recovery route, queue retry, supervisor integration or runtime restart |
| Trusted resolved-client attestation | UNVERIFIED | Mandatory descriptor binds endpoint/class/non-secret effective SDK-option hashes, but caller supplies it. Actual client initialization must derive/attest these fields before production use |
| Durable authorized recovery | UNVERIFIED | Owner-readable load/authentication, checkpoint-byte integrity, state/context validation, parent lease-fenced synchronous commit/ack, continuation consent and retained accounting remain open |
| Financial/MT acceptance | UNVERIFIED | No live report produced; earlier manual semantic/editorial failures unchanged |
| NQ=F | BLOCKED | Owner's contract/roll-source hold unchanged; no substitute |

Fingerprint equality is not authentication, a signature, policy approval, source
coverage proof or permission to spend. Full risk-series semantics still require
the existing replay checks; rendered book must be constructed from trusted DB
instrument mappings. Hashing both supplied inputs does not attest their origin.
Actual initialized-client settings must be observed, not invented from API
declarations or supplied by browser/model content. No worker path consumes this
component yet; no exhausted allowance is reset or increased.

The runtime digest deliberately invalidates on any package-Python or installed
distribution-version change. Restore a compatible environment on another
machine; do not waive this conservatively broad identity check. Synthetic test
fixtures establish binding mechanics, not provider billing, determinism,
investment correctness or release readiness. The full R01–R14 goal remains open.

Next: derive trusted effective-client descriptors, then integrate the private
durable saver and supervised parent commit/ack, preserving execution_started
and explicit continuation consent. See `research-recovery-contract.md` and
`HANDOFF.md`; older dated receipts remain immutable.

## Initialized-client observation follow-up

Source `a120d5f33d6ed3653da187b470bf3f6c276ce638`, same branch/worktree,
clean source throughout full gate. No new dependencies, provider/endpoint/prompt/
risk-limit change, worker restart, private-history rewrite or paid/vendor call.
New internal adapter constructs descriptors from initialized OpenAI-compatible
sync SDK clients, rather than inventing effective settings from config alone.

| Gate | Status | Evidence |
| --- | --- | --- |
| Initialized SDK endpoint/options | PASS | Actual NormalizedChatOpenAI/MiniMax SDK instances with synthetic credentials; effective wire params, scalar/per-phase timeout, root retries and response settings hash. Mutation changes identity; descriptors exclude the credential |
| No model/network invocation | PASS | All new fixtures forbid sync/async HTTP send and model invoke; close both SDK clients. No vendor calls |
| Fail-closed configuration | PASS | Unreviewed object, declared custom headers/query/transports and credential-bearing extra-body rejected; fixed error text, no credential echo |
| SDK normalization / builder coupling | PASS | SDK-appended slash accepted; host/path/extra slash/query/credential changes rejected. Actual descriptor builds fingerprint; retry mutation changes it |
| Focused local gate | PASS | `.venv/bin/python -m pytest -q tests/test_initialized_client_binding.py tests/test_recovery_fingerprint.py --disable-warnings`: 62 passed, 4.21 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q`: 1,942 passed + 88 subtests, 20 skipped, 22 warnings, 102.05 s; Python 3.14.7/macOS, exact a120d5f source |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML load of issue templates |
| Initial focused attempt | FAIL | Timeout assertion assumed SDK stored httpx.Timeout but it stored float 600; corrected test to interpret scalar, adapter already handled both. Initial import-order Ruff finding corrected before source commit |
| Full transport attestation | UNVERIFIED | Worker-controlled initialization/provenance, post-construction SDK/header/HTTP mutations, async invocation and other provider SDKs require review before production use |
| PostgreSQL/optional providers | UNVERIFIED | 18 missing TEST_POSTGRES_URL gates, missing langchain_aws and absent live DeepSeek key; skips not passes |
| Web recovery / durable storage | UNVERIFIED | No worker/API/CLI integration, private saver, lease-fenced commit/ack, continuation consent or crash accounting enabled |
| Live financial/MT acceptance | UNVERIFIED | No new report or paid run; earlier FAIL evidence unchanged |
| NQ=F live acceptance | BLOCKED | Owner's contract/roll-source hold unchanged |

The adapter observes selected safe initialized settings, not all possible
transport mutations. Its exact class allowlist does not attest construction
origin or ownership. It must not be treated as a browser-controlled recovery
permission. Next: trusted construction/mutation guards and durable supervised
parent commit/ack, with existing no-blind-replay and consent/accounting gates.
R01–R14 remains incomplete; no CI or public deployment.

## Private checkpoint persistence follow-up

Source `77b32d81a84f6abb4e5705fdd6a8e3e63e6c8852`, same branch/worktree,
clean throughout full regression. Migration `0011_research_checkpoints` adds
a separate recovery-only table; existing report/artifact/decision readers are
unchanged. No private owner DB was migrated, no runtime restarted, no provider,
endpoint, risk limit or execution authority changed. No AI/vendor call.

| Gate | Status | Evidence |
| --- | --- | --- |
| Private persistent records | PASS | Real disposable SQLite migration and database reopen retain restricted JSON; raw messages/reasoning absent; generic artifacts table empty |
| Commit-before-ACK | PASS | Real publication transaction rollback after flush yields no return receipt and no stored row; normal ACK only after transaction exits |
| Lease/cancellation fences | PASS | Real JobExecutionContext rejects expired lease, wrong worker, cancellation and recorded heartbeat failure; zero checkpoint rows |
| Owner/run/thread/hash/identity | PASS | Wrong owner/thread cannot write or read; changed fingerprint, corrupt latest bytes or checkpoint ID rejected without fallback |
| Append/idempotency | PASS | Same bytes return existing receipt; completed pending-write revision increments sequence and leaves original bytes unchanged; missing history returns None |
| Migration roundtrip | PASS | Fixture downgrade to 0010 and upgrade to head removes/recreates only new table; existing run/job can still accept checkpoint. No real historical data touched |
| Focused local gate | PASS | `.venv/bin/python -m pytest -q tests/test_private_checkpoint_store.py tests/test_snapshot_checkpoint_codec.py tests/test_durable_jobs.py tests/test_platform_persistence.py --disable-warnings`: 72 passed, 2 PostgreSQL skips, 7.20 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,955 tests + 88 subtests passed, 20 skipped, 22 warnings, 121.18 s; Python 3.14.7/macOS, clean 77b32d8 source |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Initial formatting gate | FAIL | Two import-order findings fixed before source commit; focused behavior gate had no failures |
| PostgreSQL/concurrent durability | UNVERIFIED | No TEST_POSTGRES_URL; new store not characterized under PostgreSQL or concurrent writer/crash workload |
| Native saver / production bridge | UNVERIFIED | No LangGraph saver or supervisor RPC invokes this store; separate-process write/ACK crash and accounting still required |
| Continuation authority | UNVERIFIED | Trusted fingerprint/client construction, original allowance accounting, explicit owner consent/idempotency and operational UI remain open; store/readability is not permission to continue |
| Runtime migration/deployment | NOT_IN_SCOPE | Only fresh disposable test DBs changed; no existing private DB, worker, public deployment or CI |
| Financial/translation/live | UNVERIFIED | No new report, existing manual FAIL not cured by storage tests; BTC/AAPL acceptance outstanding |
| NQ=F | BLOCKED | Owner's contract/roll-source hold unchanged |

The parent-only internal service must receive trusted original context; its
arguments are not authenticated browser inputs. DB commit/rollback tests are
not native process crash or provider-billing proof. The next integration must
preserve execution_started and no-blind-replay, refuse uncertain checkpoints,
and not increase/reset the original allowance. R01–R14 remains open.
