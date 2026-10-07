"""Owner control-plane routes; reservation is not worker dispatch or approval."""

from copy import deepcopy
from secrets import compare_digest
from threading import Lock
from uuid import UUID

from fastapi import HTTPException, Request

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.platform.analysis.continuation import _digest, _payload
from tradingagents.platform.analysis.linked_execution import LinkedExecutionStore
from tradingagents.platform.analysis.terminal_preparation import prepare_terminal_continuation
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.persistence import PlatformRepository

from .schemas import (
    ContinuationConsentRequest,
    ContinuationPreparationResponse,
    ContinuationReservationResponse,
)


def mount_continuation_routes(app, *, settings, database, artifact_store):
    """Close read-only auth transactions before bounded original SDK preparation.

    Do not use the ordinary owner dependency: it flushes session last_seen and
    holds its writer lock until request end. Trusted preparation takes that same
    lock in independent transactions. No browser-supplied codec/config is used.
    """
    preparation_lock = Lock()

    def credentials(request, run_id):
        token = request.cookies.get("ta_session")
        if not token:
            raise HTTPException(401, "authentication required")
        csrf = request.headers.get("X-CSRF-Token")
        cookie = request.cookies.get("ta_csrf")
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
