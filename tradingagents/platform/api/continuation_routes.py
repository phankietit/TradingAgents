"""Owner control-plane routes; reservation is not worker dispatch or approval."""

from copy import deepcopy
from secrets import compare_digest
from threading import Lock
from uuid import UUID

from fastapi import HTTPException, Query, Request
from sqlalchemy import select, text

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.platform.analysis.continuation import _db_utc, _digest, _payload
from tradingagents.platform.analysis.linked_execution import LinkedExecutionStore
from tradingagents.platform.analysis.linked_results import read_linked_completion
from tradingagents.platform.analysis.preparation_refusals import validate_refusal
from tradingagents.platform.analysis.terminal_preparation import prepare_terminal_continuation
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import (
    ResearchContinuationRow,
    ResearchExecutionCompletionRow,
    ResearchExecutionRow,
    ResearchPreparationRefusalRow,
)

from .schemas import (
    ContinuationConsentRequest,
    ContinuationDiscoveryResponse,
    ContinuationPreparationResponse,
    ContinuationReservationResponse,
    ContinuationStateResponse,
)


def mount_continuation_routes(app, *, settings, database, artifact_store):
    """Close read-only auth transactions before bounded original SDK preparation.

    Do not use the ordinary owner dependency: it flushes session last_seen and
    holds its writer lock until request end. Trusted preparation takes that same
    lock in independent transactions. No browser-supplied codec/config is used.
    """
    preparation_lock = Lock()

    def credentials(request, run_id, *, mutating=True):
        token = request.cookies.get("ta_session")
        if not token:
            raise HTTPException(401, "authentication required")
        csrf = request.headers.get("X-CSRF-Token")
        cookie = request.cookies.get("ta_csrf")
        if not mutating and csrf is None:
            csrf = cookie
        if not csrf or not cookie or not compare_digest(csrf.encode(), cookie.encode()):
            raise HTTPException(403, "CSRF validation failed")
        try:
            with database.session(lock_timeout_seconds=5.0) as session:
                principal = OwnerAuth(session).lock_authenticated_consent(token, csrf, now=settings.clock())
                run = PlatformRepository(session).get_run(run_id, principal.owner_id)
                if run is None:
                    raise HTTPException(404, "run not found")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(401, "authentication required") from None
        return token, csrf

    def state(session, execution, now):
        refusal = session.get(ResearchPreparationRefusalRow, execution.execution_id)
        if refusal is not None:
            validate_refusal(refusal, execution=execution, now=now)
        completed = read_linked_completion(session=session, artifact_store=artifact_store,
            owner_id=execution.owner_id, execution_id=execution.execution_id)
        return ContinuationStateResponse(run_id=execution.source_run_id, execution_id=execution.execution_id,
            status="completed" if completed is not None else execution.status,
            preparation_requires_review=refusal is not None,
            lease_expired=execution.lease_expires_at is not None and _db_utc(execution.lease_expires_at) <= now,
            attempt=execution.attempt,
            report_artifact_id=completed.report_artifact_id if completed is not None else None,
            evidence_artifact_id=completed.evidence_artifact_id if completed is not None else None,
            decision_id=completed.decision_id if completed is not None else None)

    def load_control(session, run_id, execution_id, token, csrf):
        now = settings.clock()
        owner = OwnerAuth(session).lock_authenticated_consent(token, csrf, now=now)
        row = session.get(ResearchContinuationRow, execution_id)
        if row is None or row.owner_id != owner.owner_id or row.source_run_id != run_id:
            raise HTTPException(404, "continuation not found")
        consent, observation = LinkedExecutionStore._control_source(session, execution_id, now, owner_id=owner.owner_id)
        execution = LinkedExecutionStore._execution(session, consent, observation, now)
        if execution is None:
            raise HTTPException(404, "continuation not found")
        return execution, now

    @app.get("/api/v1/runs/{run_id}/continuations", response_model=ContinuationDiscoveryResponse,
             tags=["runs"])
    def discover_continuations(run_id: UUID, request: Request,
                               limit: int = Query(default=20, ge=1, le=50),
                               before_attempt: int | None = Query(default=None, ge=2, le=1_000_000)):
        token, csrf = credentials(request, run_id, mutating=False)
        try:
            with database.session(lock_timeout_seconds=5.0) as session:
                now = settings.clock()
                owner = OwnerAuth(session).lock_authenticated_consent(token, csrf, now=now)
                query = select(ResearchExecutionRow.execution_id).where(
                    ResearchExecutionRow.owner_id == owner.owner_id,
                    ResearchExecutionRow.source_run_id == run_id)
                if before_attempt is not None:
                    query = query.where(ResearchExecutionRow.attempt < before_attempt)
                identities = session.scalars(query.order_by(ResearchExecutionRow.attempt.desc()).limit(limit + 1)).all()
                items = []
                for identity in identities[:limit]:
                    execution, observed_at = load_control(session, run_id, identity, token, csrf)
                    items.append(state(session, execution, observed_at))
                return ContinuationDiscoveryResponse(items=tuple(items), has_more=len(identities) > limit)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(409, "continuation requires review") from None

    @app.get("/api/v1/runs/{run_id}/continuations/{execution_id}",
             response_model=ContinuationStateResponse, tags=["runs"])
    def get_continuation(run_id: UUID, execution_id: UUID, request: Request):
        token, csrf = credentials(request, run_id, mutating=False)
        try:
            with database.session(lock_timeout_seconds=5.0) as session:
                execution, now = load_control(session, run_id, execution_id, token, csrf)
                return state(session, execution, now)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(409, "continuation requires review") from None

    @app.post("/api/v1/runs/{run_id}/continuations/{execution_id}/cancel",
              response_model=ContinuationStateResponse, tags=["runs"])
    def cancel_continuation(run_id: UUID, execution_id: UUID, request: Request):
        token, csrf = credentials(request, run_id)
        try:
            with database.session(lock_timeout_seconds=5.0) as session:
                if session.bind.dialect.name == "sqlite":
                    session.execute(text("BEGIN IMMEDIATE"))
                execution, now = load_control(session, run_id, execution_id, token, csrf)
                if session.get(ResearchExecutionCompletionRow, execution_id) is not None:
                    raise ValueError("completion cannot be cancelled")
                if execution.status == "reserved":
                    execution.status = "cancelled"
                elif execution.status == "leased":
                    execution.status = "cancel_requested"
                execution.updated_at = now
                session.flush()
                return state(session, execution, now)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(409, "continuation requires review") from None

    def prepare(run_id, token, csrf):
        config = deepcopy(DEFAULT_CONFIG)
        config.update(data_cache_dir=str(artifact_store.root / "worker-runtime" / "cache"),
                      results_dir=str(artifact_store.root / "worker-runtime" / "reports"))
        return prepare_terminal_continuation(database=database, artifact_store=artifact_store,
            run_id=run_id, base_config=config, session_token=token, csrf_token=csrf,
            clock=settings.clock)

    @app.post("/api/v1/runs/{run_id}/continuation/prepare",
              response_model=ContinuationPreparationResponse, tags=["runs"])
    def prepare_continuation(run_id: UUID, request: Request):
        token, csrf = credentials(request, run_id)
        if not preparation_lock.acquire(blocking=False):
            raise HTTPException(409, "continuation preparation busy")
        try:
            prepared = prepare(run_id, token, csrf)
            accounting = prepared.observation.accounting
            return ContinuationPreparationResponse(
                run_id=run_id, observation_hash=_digest(_payload(prepared.observation)),
                remaining_wall_seconds=accounting.original_wall_seconds - accounting.elapsed_upper_bound,
                remaining_model_calls=accounting.original_model_calls - accounting.started_calls)
        except Exception:
            raise HTTPException(409, "continuation requires review") from None
        finally:
            preparation_lock.release()

    @app.post("/api/v1/runs/{run_id}/continuations",
              response_model=ContinuationReservationResponse, tags=["runs"])
    def reserve_continuation(run_id: UUID, request: Request, body: ContinuationConsentRequest):
        token, csrf = credentials(request, run_id)
        if not preparation_lock.acquire(blocking=False):
            raise HTTPException(409, "continuation preparation busy")
        try:
            prepared = prepare(run_id, token, csrf)
            if not compare_digest(body.observation_hash, _digest(_payload(prepared.observation))):
                raise ValueError("stale observation")
            consent = prepared.consents.record(session_token=token, csrf_token=csrf,
                expected_observation=prepared.observation, idempotency_key=body.idempotency_key,
                confirm_continue=body.confirm_continue)
            reservation = LinkedExecutionStore(prepared.consents).allocate(
                execution_id=consent.execution_id, session_token=token, csrf_token=csrf)
            return ContinuationReservationResponse(run_id=run_id,
                execution_id=reservation.execution_id, status=reservation.status)
        except Exception:
            raise HTTPException(409, "continuation requires review") from None
        finally:
            preparation_lock.release()
