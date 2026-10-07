"""Trusted durable-reservation preparation, without any browser session token."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from tradingagents._compat import UTC
from tradingagents.platform.jobs.queue import DurableJobQueue
from tradingagents.platform.persistence.models import (
    OwnerRow,
    ResearchContinuationRow,
    ResearchExecutionRow,
)

from .allowance import build_retained_observer, load_remaining_allowance
from .checkpoint_codec import SnapshotCheckpointCodec
from .continuation import ContinuationConsentStore, _canonical, _db_utc, _digest
from .initialized_preflight import prepare_recording_identity
from .linked_execution import LinkedExecutionStore
from .terminal_preparation import PreparedTerminalContinuation, load_terminal_inputs


def prepare_reserved_continuation(*, database, artifact_store, execution_id,
                                  base_config, clock=lambda: datetime.now(UTC)):
    """Rebuild actual original identity, then revalidate the complete consent.

    Preliminary read checks are not a dispatch grant. Only the actual derived
    codec can validate the full consent/checkpoint observation, followed by a
    separately committed one-time lease claim. No model/entry/claim/write here.
    """
    def reject():
        raise ValueError('reserved continuation preparation requires review') from None

    def load(session):
        consent = session.get(ResearchContinuationRow, execution_id)
        if consent is None:
            reject()
        owner = session.scalar(select(OwnerRow).where(OwnerRow.owner_id == consent.owner_id)
            .with_for_update().execution_options(populate_existing=True))
        execution = session.get(ResearchExecutionRow, execution_id)
        now = clock()
        if (owner is None or owner.status != 'active' or execution is None
                or execution.status != 'reserved'
                or (execution.owner_id, execution.source_run_id, execution.source_job_id,
                    execution.observation_hash) != (consent.owner_id, consent.source_run_id,
                    consent.source_job_id, consent.observation_hash)
                or type(now) is not datetime or now.utcoffset() is None
                or _db_utc(consent.created_at) > now):
            reject()
        payload = consent.payload
        if (payload['format'] != 'research-continuation-consent-v1'
                or payload['dispatch_enabled'] is not False or _digest(payload) != consent.observation_hash
                or payload['acknowledged_disclosures'] != ['original_allowance_retained',
                    'provider_cost_unknown', 'prior_research_unvalidated']):
            reject()
        observation = payload['observation']
        run, request, original, binding = load_terminal_inputs(session=session,
            artifact_store=artifact_store, run_id=consent.source_run_id, owner_id=consent.owner_id)
        job = DurableJobQueue(session).get(consent.source_job_id, consent.owner_id)
        allowance = load_remaining_allowance(session=session, owner_id=consent.owner_id, run_id=run.run_id)
        if (job is None or job.run_id != run.run_id or allowance.assessment_status != 'PASS'
                or observation['owner_id'] != str(consent.owner_id)
                or observation['run_id'] != str(run.run_id)
                or observation['source_job_id'] != str(job.job_id)
                or observation['source_run_hash'] != _digest(run.model_dump(mode='json'))
                or observation['source_job_hash'] != _digest(job.model_dump(mode='json'))
                or _canonical(observation['accounting']) != _canonical(asdict(allowance.accounting))):
            reject()
        return run, request, original, binding, allowance.accounting, consent.observation_hash

    try:
        if type(execution_id) is not UUID or type(base_config) is not dict:
            reject()
        with database.session(lock_timeout_seconds=5.0) as session:
            run, request, original, binding, accounting, digest = load(session)

        def boundary():
            with database.session(lock_timeout_seconds=5.0) as session:
                current = load(session)
                if current[3:] != (binding, accounting, digest):
                    reject()

        def no_publication(*args, **kwargs):
            reject()

        with database.session() as session:
            observer = build_retained_observer(session=session, owner_id=run.owner_id, run_id=run.run_id,
                expected_accounting=accounting, check_cancelled=boundary, emit=no_publication)
        request = request.model_copy(update={'execution_observer': observer})
        identity = prepare_recording_identity(observer=observer, owner_id=run.owner_id, run=run,
            request=request, base_config=deepcopy(base_config), portfolio_snapshot=original.portfolio_snapshot,
            policy=original.policy, risk_snapshots=original.risk_snapshots)
        observer.remaining_seconds()
        consents = ContinuationConsentStore(database, clock=clock,
            codec=SnapshotCheckpointCodec(fingerprint=identity.fingerprint, nodes=identity.nodes))
        executions = LinkedExecutionStore(consents)
        with executions._transaction() as (session, now):
            current = load(session)
            if current[3:] != (binding, accounting, digest):
                reject()
            consent, observation, value = executions._source(session, execution_id, now, recheck=True)
            execution = executions._execution(session, consent, observation, now)
            if execution is None or execution.status != 'reserved' or value.accounting != accounting:
                reject()
        observer.remaining_seconds()
        return PreparedTerminalContinuation(consents, value)
    except Exception:
        reject()
