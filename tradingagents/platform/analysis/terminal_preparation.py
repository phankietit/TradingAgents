"""Internal authenticated control-plane preparation; no consent or model entry."""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from tradingagents._compat import UTC
from tradingagents.contracts import RunStatus
from tradingagents.platform.analysis.allowance import (
    build_retained_observer,
    load_remaining_allowance,
)
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.continuation import (
    ContinuationConsentStore,
    ContinuationObservation,
    _digest,
)
from tradingagents.platform.analysis.engine import AnalysisRequest
from tradingagents.platform.analysis.initialized_preflight import prepare_recording_identity
from tradingagents.platform.analysis.recording_sources import load_original_recording_sources
from tradingagents.platform.analysis.snapshots import load_snapshot_context
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.jobs.decision_pipeline import load_run_portfolio
from tradingagents.platform.persistence import PlatformRepository


@dataclass(frozen=True, repr=False)
class PreparedTerminalContinuation:
    consents: ContinuationConsentStore
    observation: ContinuationObservation


def prepare_terminal_continuation(*, database, artifact_store, run_id, base_config,
                                  session_token, csrf_token, clock=lambda: datetime.now(UTC)):
    """Derive trusted codec from original owner-readable inputs/actual SDKs.

    Locked authentication is read-only (unlike authenticate_session's last_seen
    update). No locks span SDK preparation. No observer/cap/codec/client/hash is
    supplied by the browser. Preparation is not consent/allocation/dispatch.
    """
    def reject():
        raise ValueError('terminal continuation preparation requires review') from None

    def authenticate(session):
        return OwnerAuth(session).lock_authenticated_consent(session_token, csrf_token, now=clock())

    def load(session, owner_id):
        repo = PlatformRepository(session, artifact_store=artifact_store)
        run = repo.get_run(run_id, owner_id)
        if (run is None or run.status not in {RunStatus.FAILED, RunStatus.CANCELLED}
                or run.decision_inputs is None):
            reject()
        artifacts = ArtifactService(artifact_store, repo)
        instrument = repo.get_instrument(run.instrument_id)
        if instrument is None:
            reject()
        sources = load_snapshot_context(artifacts, run, run.decision_inputs.snapshots_by_analyst)
        original = load_original_recording_sources(repository=repo, artifacts=artifacts, run=run)
        overrides = {'llm_provider': run.llm_provider, 'quick_think_llm': run.quick_model,
                     'deep_think_llm': run.deep_model}
        if run.report_language is not None:
            overrides['output_language'] = {'en': 'English', 'vi': 'Vietnamese',
                                           'en-vi': 'English and Vietnamese'}[run.report_language]
        request = AnalysisRequest(instrument=instrument, analysis_date=run.analysis_as_of.date(),
            selected_analysts=run.selected_analysts, snapshot_context=sources,
            portfolio=load_run_portfolio(repo, run), config_overrides=overrides)
        binding = _digest({'run': run.model_dump(mode='json'), 'request': request.model_dump(mode='json'),
            'book': original.portfolio_snapshot.model_dump(mode='json') if original.portfolio_snapshot else None,
            'policy': original.policy.model_dump(mode='json') if original.policy else None,
            'risk': [item.model_dump(mode='json') for item in original.risk_snapshots]})
        return run, request, original, binding

    try:
        if type(run_id) is not UUID or type(base_config) is not dict:
            reject()
        with database.session(lock_timeout_seconds=5.0) as session:
            owner = authenticate(session).owner_id
            run, request, original, binding = load(session, owner)
            allowance = load_remaining_allowance(session=session, owner_id=owner, run_id=run_id)
            if allowance.assessment_status != 'PASS':
                reject()
            accounting = allowance.accounting

        def boundary():
            with database.session(lock_timeout_seconds=5.0) as session:
                if authenticate(session).owner_id != owner:
                    reject()
                current = load_remaining_allowance(session=session, owner_id=owner, run_id=run_id)
                if current.accounting != accounting or current.assessment_status != 'PASS':
                    reject()

        def no_publication(*args, **kwargs):
            reject()  # A control-plane probe cannot emit research/accounting.

        with database.session() as session:
            observer = build_retained_observer(session=session, owner_id=owner, run_id=run_id,
                expected_accounting=accounting, check_cancelled=boundary, emit=no_publication)
        request = request.model_copy(update={'execution_observer': observer})
        identity = prepare_recording_identity(observer=observer, owner_id=owner, run=run,
            request=request, base_config=deepcopy(base_config), portfolio_snapshot=original.portfolio_snapshot,
            policy=original.policy, risk_snapshots=original.risk_snapshots)
        observer.remaining_seconds()
        codec = SnapshotCheckpointCodec(fingerprint=identity.fingerprint, nodes=identity.nodes)
        consents = ContinuationConsentStore(database, codec=codec, clock=clock)
        with database.session(lock_timeout_seconds=5.0) as session:
            if authenticate(session).owner_id != owner or load(session, owner)[3] != binding:
                reject()
            observation = consents.observe(session=session, owner_id=owner, run_id=run_id)
            if observation.accounting != accounting:
                reject()
        observer.remaining_seconds()
        return PreparedTerminalContinuation(consents, observation)
    except Exception:
        reject()  # Never expose credential, storage, SDK or source exceptions.
