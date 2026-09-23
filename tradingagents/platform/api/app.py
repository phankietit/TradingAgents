"""Authenticated FastAPI contract for private portfolio decision support."""

from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time
from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

import anyio
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    Security,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyCookie
from sqlalchemy import text
from sqlalchemy.orm import Session

from tradingagents.contracts import (
    TERMINAL_RUN_EVENTS,
    DecisionCandidate,
    InstrumentContract,
    JobRecord,
    JobStatus,
    RunEvent,
    RunEventType,
    RunManifest,
    RunStatus,
)
from tradingagents.platform.artifacts import (
    ArtifactIntegrityError,
    ArtifactService,
    LocalArtifactStore,
)
from tradingagents.platform.auth import InvalidCredentials, OwnerAuth, OwnerPrincipal
from tradingagents.platform.events import RunEventNotFound, RunEventStore
from tradingagents.platform.jobs import DurableJobQueue, JobConflict
from tradingagents.platform.persistence import Database, PlatformRepository

from .schemas import (
    LoginRequest,
    LoginResponse,
    OwnerResponse,
    RunAcceptedResponse,
    RunCreateRequest,
    StatusResponse,
)
from .settings import ApiSettings

API_PREFIX = "/api/v1"
SESSION_COOKIE = "ta_session"
CSRF_COOKIE = "ta_csrf"
CSRF_HEADER = "X-CSRF-Token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
cookie_scheme = APIKeyCookie(name=SESSION_COOKIE, auto_error=False)


def _now(settings: ApiSettings) -> datetime:
    value = settings.clock()
    if value.tzinfo is None:
        raise RuntimeError("API clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


def _config_hash(settings: ApiSettings, analysts: tuple[str, ...]) -> str:
    value = json.dumps(
        {
            "llm_provider": settings.llm_provider,
            "quick_model": settings.quick_model,
            "deep_model": settings.deep_model,
            "prompt_version": settings.prompt_version,
            "selected_analysts": analysts,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _session(request: Request) -> Iterator[Session]:
    database: Database = request.app.state.database
    with database.session() as session:
        yield session


def _settings(request: Request) -> ApiSettings:
    return request.app.state.settings


SessionDependency = Annotated[Session, Depends(_session)]
CookieDependency = Annotated[str | None, Security(cookie_scheme)]


def _current_owner(
    request: Request,
    token: CookieDependency,
    session: SessionDependency,
) -> OwnerPrincipal:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        )
    try:
        return OwnerAuth(session).authenticate_session(token, now=_now(_settings(request)))
    except InvalidCredentials as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        ) from error


OwnerDependency = Annotated[OwnerPrincipal, Depends(_current_owner)]


def _csrf_owner(
    request: Request,
    owner: OwnerDependency,
    session: SessionDependency,
    csrf_header: str | None = Header(default=None, alias=CSRF_HEADER),
) -> OwnerPrincipal:
    token = request.cookies.get(SESSION_COOKIE, "")
    csrf_cookie = request.cookies.get(CSRF_COOKIE, "")
    if (
        csrf_header is None
        or not secrets_compare(csrf_header, csrf_cookie)
        or not OwnerAuth(session).validate_csrf(token, csrf_header)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    return owner


def secrets_compare(left: str, right: str) -> bool:
    """Constant-time compare kept local to avoid logging either token."""

    return secrets.compare_digest(left, right)


CsrfOwnerDependency = Annotated[OwnerPrincipal, Depends(_csrf_owner)]


def _stream_owner(request: Request, token: CookieDependency) -> OwnerPrincipal:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        )
    database: Database = request.app.state.database
    with database.session() as session:
        try:
            return OwnerAuth(session).authenticate_session(token, now=_now(_settings(request)))
        except InvalidCredentials as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
            ) from error


StreamOwnerDependency = Annotated[OwnerPrincipal, Depends(_stream_owner)]


def _sse_event(event: RunEvent) -> str:
    return (
        f"id: {event.sequence}\n"
        f"event: {event.event_type.value}\n"
        f"data: {event.model_dump_json()}\n\n"
    )


def create_app(settings: ApiSettings) -> FastAPI:
    database = Database(settings.database_url)
    artifact_store = LocalArtifactStore(settings.artifact_root)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        database.dispose()

    app = FastAPI(
        title="TradingAgents Private Platform API",
        version="1.0.0",
        description="Authenticated decision-support API. No broker execution endpoints.",
        lifespan=lifespan,
    )
    app.state.database = database
    app.state.artifact_store = artifact_store
    app.state.settings = settings

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, error: RequestValidationError):
        detail = [
            {"type": item["type"], "loc": item["loc"], "msg": item["msg"]}
            for item in error.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": detail},
        )

    @app.middleware("http")
    async def browser_security(request: Request, call_next):
        if request.method in UNSAFE_METHODS:
            origin = request.headers.get("origin")
            if origin != settings.allowed_origin.rstrip("/"):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "origin validation failed"},
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health/live", response_model=StatusResponse, tags=["health"])
    def live() -> StatusResponse:
        return StatusResponse(status="ok")

    @app.get("/health/ready", response_model=StatusResponse, tags=["health"])
    def ready(session: SessionDependency) -> StatusResponse:
        try:
            session.execute(text("SELECT 1"))
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="not ready"
            ) from error
        return StatusResponse(status="ready")

    @app.post(f"{API_PREFIX}/auth/login", response_model=LoginResponse, tags=["auth"])
    def login(
        payload: LoginRequest,
        response: Response,
        session: SessionDependency,
    ) -> LoginResponse:
        try:
            issued = OwnerAuth(session, session_ttl=settings.session_ttl).login(
                payload.email, payload.password, now=_now(settings)
            )
        except InvalidCredentials as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials"
            ) from error
        response.set_cookie(
            SESSION_COOKIE,
            issued.token,
            httponly=True,
            secure=settings.secure_cookies,
            samesite="strict",
            path=API_PREFIX,
            max_age=int(settings.session_ttl.total_seconds()),
        )
        response.set_cookie(
            CSRF_COOKIE,
            issued.csrf_token,
            httponly=False,
            secure=settings.secure_cookies,
            samesite="strict",
            path=API_PREFIX,
            max_age=int(settings.session_ttl.total_seconds()),
        )
        return LoginResponse(
            owner_id=issued.principal.owner_id,
            email=issued.principal.email,
            expires_at=issued.expires_at,
        )

    @app.post(f"{API_PREFIX}/auth/logout", response_model=StatusResponse, tags=["auth"])
    def logout(
        request: Request,
        response: Response,
        _owner: CsrfOwnerDependency,
        session: SessionDependency,
    ) -> StatusResponse:
        OwnerAuth(session).revoke_session(
            request.cookies.get(SESSION_COOKIE, ""), now=_now(settings)
        )
        response.delete_cookie(SESSION_COOKIE, path=API_PREFIX)
        response.delete_cookie(CSRF_COOKIE, path=API_PREFIX)
        return StatusResponse(status="logged_out")

    @app.get(f"{API_PREFIX}/auth/me", response_model=OwnerResponse, tags=["auth"])
    def me(owner: OwnerDependency) -> OwnerResponse:
        return OwnerResponse(owner_id=owner.owner_id, email=owner.email)

    @app.get(
        f"{API_PREFIX}/instruments",
        response_model=list[InstrumentContract],
        tags=["instruments"],
    )
    def list_instruments(
        _owner: OwnerDependency,
        session: SessionDependency,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> tuple[InstrumentContract, ...]:
        return PlatformRepository(session).list_instruments(limit=limit)

    @app.post(
        f"{API_PREFIX}/runs",
        response_model=RunAcceptedResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["runs"],
    )
    def create_run(
        payload: RunCreateRequest,
        owner: CsrfOwnerDependency,
        session: SessionDependency,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=128),
    ) -> RunAcceptedResponse:
        timestamp = _now(settings)
        if payload.analysis_as_of.astimezone(UTC) > timestamp:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="future as_of"
            )
        if len(payload.selected_analysts) != len(set(payload.selected_analysts)) or any(
            analyst not in settings.allowed_analysts for analyst in payload.selected_analysts
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="selected_analysts contains duplicate or unsupported values",
            )

        auth = OwnerAuth(session)
        auth.lock_owner(owner.owner_id)
        repository = PlatformRepository(session)
        instrument = repository.get_instrument(payload.instrument_id)
        if instrument is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="instrument not found"
            )
        config_hash = _config_hash(settings, payload.selected_analysts)
        job_payload = {
            "instrument_id": str(instrument.instrument_id),
            "analysis_as_of": payload.analysis_as_of.astimezone(UTC).isoformat(),
            "selected_analysts": list(payload.selected_analysts),
            "config_hash": config_hash,
        }
        queue = DurableJobQueue(session)
        existing_job = queue.get_by_idempotency(owner.owner_id, idempotency_key)
        if existing_job:
            if existing_job.payload != job_payload:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="idempotency key already used for different input",
                )
            existing_run = repository.get_run(existing_job.run_id, owner.owner_id)
            if existing_run is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="idempotent run is unavailable",
                )
            return RunAcceptedResponse(run=existing_run, job=existing_job)

        run = RunManifest(
            run_id=uuid4(),
            owner_id=owner.owner_id,
            instrument_id=instrument.instrument_id,
            analysis_as_of=payload.analysis_as_of,
            status=RunStatus.QUEUED,
            created_at=timestamp,
            selected_analysts=payload.selected_analysts,
            llm_provider=settings.llm_provider,
            quick_model=settings.quick_model,
            deep_model=settings.deep_model,
            config_hash=config_hash,
            prompt_version=settings.prompt_version,
        )
        repository.save_run(run)
        try:
            job = queue.enqueue(
                owner_id=owner.owner_id,
                run_id=run.run_id,
                idempotency_key=idempotency_key,
                payload=job_payload,
                max_attempts=settings.max_job_attempts,
                now=timestamp,
            )
        except JobConflict as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="job conflict"
            ) from error
        RunEventStore(session).append(
            owner_id=owner.owner_id,
            run_id=run.run_id,
            event_type=RunEventType.RUN_QUEUED,
            occurred_at=timestamp,
            payload={
                "job_id": str(job.job_id),
                "instrument_id": str(instrument.instrument_id),
            },
        )
        return RunAcceptedResponse(run=run, job=job)

    @app.get(f"{API_PREFIX}/runs", response_model=list[RunManifest], tags=["runs"])
    def list_runs(
        owner: OwnerDependency,
        session: SessionDependency,
        limit: int = Query(default=50, ge=1, le=200),
    ) -> tuple[RunManifest, ...]:
        return PlatformRepository(session).list_runs(owner.owner_id, limit=limit)

    @app.get(f"{API_PREFIX}/runs/{{run_id}}", response_model=RunManifest, tags=["runs"])
    def get_run(
        run_id: UUID,
        owner: OwnerDependency,
        session: SessionDependency,
    ) -> RunManifest:
        run = PlatformRepository(session).get_run(run_id, owner.owner_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        return run

    @app.get(f"{API_PREFIX}/runs/{{run_id}}/events", tags=["runs"])
    def stream_run_events(
        request: Request,
        run_id: UUID,
        owner: StreamOwnerDependency,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    ) -> StreamingResponse:
        if last_event_id is None:
            cursor = 0
        else:
            try:
                cursor = int(last_event_id)
            except ValueError as error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Last-Event-ID must be a non-negative integer",
                ) from error
            if cursor < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Last-Event-ID must be a non-negative integer",
                )

        with database.session() as session:
            if PlatformRepository(session).get_run(run_id, owner.owner_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")

        async def generate():
            sequence = cursor
            last_keepalive = time.monotonic()
            yield f"retry: {settings.event_retry_milliseconds}\n\n"
            while True:
                if await request.is_disconnected():
                    return

                def load_batch(after_sequence: int = sequence):
                    with database.session() as session:
                        try:
                            events = RunEventStore(session).list_after(
                                owner.owner_id,
                                run_id,
                                after_sequence=after_sequence,
                                limit=100,
                            )
                        except RunEventNotFound:
                            return None, None
                        run = PlatformRepository(session).get_run(run_id, owner.owner_id)
                        return events, run

                events, run = await anyio.to_thread.run_sync(load_batch)
                if events is None:
                    return
                for event in events:
                    sequence = event.sequence
                    yield _sse_event(event)
                    if event.event_type in TERMINAL_RUN_EVENTS:
                        return
                if run is None or run.status in {
                    RunStatus.SUCCEEDED,
                    RunStatus.FAILED,
                    RunStatus.CANCELLED,
                }:
                    return
                now_monotonic = time.monotonic()
                if now_monotonic - last_keepalive >= settings.event_keepalive_interval:
                    yield ": keep-alive\n\n"
                    last_keepalive = now_monotonic
                await asyncio.sleep(settings.event_poll_interval)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(
        f"{API_PREFIX}/runs/{{run_id}}/cancel",
        response_model=JobRecord,
        tags=["runs"],
    )
    def cancel_run(
        run_id: UUID,
        owner: CsrfOwnerDependency,
        session: SessionDependency,
    ) -> JobRecord:
        repository = PlatformRepository(session)
        run = repository.get_run(run_id, owner.owner_id)
        job = DurableJobQueue(session).get_by_run(run_id, owner.owner_id)
        if run is None or job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        timestamp = _now(settings)
        cancelled = DurableJobQueue(session).request_cancel(
            job.job_id, owner.owner_id, now=timestamp
        )
        if cancelled is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        event_type = None
        if (
            job.status in {JobStatus.QUEUED, JobStatus.RETRY_WAIT}
            and cancelled.status is JobStatus.CANCELLED
        ):
            event_type = RunEventType.RUN_CANCELLED
        elif job.status is JobStatus.RUNNING and cancelled.status is JobStatus.CANCEL_REQUESTED:
            event_type = RunEventType.RUN_CANCEL_REQUESTED
        if event_type is not None:
            RunEventStore(session).append(
                owner_id=owner.owner_id,
                run_id=run_id,
                event_type=event_type,
                occurred_at=timestamp,
                payload={"job_id": str(job.job_id)},
            )
        if cancelled.status is JobStatus.CANCELLED and run.status is RunStatus.QUEUED:
            repository.save_run(
                run.model_copy(
                    update={
                        "status": RunStatus.CANCELLED,
                        "started_at": timestamp,
                        "completed_at": timestamp,
                    }
                )
            )
        return cancelled

    @app.get(f"{API_PREFIX}/jobs/{{job_id}}", response_model=JobRecord, tags=["jobs"])
    def get_job(
        job_id: UUID,
        owner: OwnerDependency,
        session: SessionDependency,
    ) -> JobRecord:
        job = DurableJobQueue(session).get(job_id, owner.owner_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
        return job

    @app.get(
        f"{API_PREFIX}/decisions",
        response_model=list[DecisionCandidate],
        tags=["decisions"],
    )
    def list_decisions(
        owner: OwnerDependency,
        session: SessionDependency,
        limit: int = Query(default=50, ge=1, le=200),
    ) -> tuple[DecisionCandidate, ...]:
        return PlatformRepository(session).list_decisions(owner.owner_id, limit=limit)

    @app.get(
        f"{API_PREFIX}/decisions/{{decision_id}}",
        response_model=DecisionCandidate,
        tags=["decisions"],
    )
    def get_decision(
        decision_id: UUID,
        owner: OwnerDependency,
        session: SessionDependency,
    ) -> DecisionCandidate:
        decision = PlatformRepository(session).get_decision(decision_id, owner.owner_id)
        if decision is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="decision not found")
        return decision

    @app.get(f"{API_PREFIX}/artifacts/{{artifact_id}}", tags=["artifacts"])
    def get_artifact(
        artifact_id: UUID,
        owner: OwnerDependency,
        session: SessionDependency,
    ) -> Response:
        service = ArtifactService(artifact_store, PlatformRepository(session))
        try:
            result = service.read(artifact_id, owner.owner_id)
        except ArtifactIntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="artifact integrity check failed"
            ) from error
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact not found")
        manifest, content = result
        return Response(
            content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{manifest.artifact_id}"'},
        )

    return app
