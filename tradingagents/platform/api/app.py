"""Authenticated FastAPI contract for private portfolio decision support."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
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
    AssetClass,
    DecisionActorType,
    DecisionCandidate,
    DecisionLifecycleEvent,
    DecisionStatus,
    InstrumentContract,
    JobRecord,
    JobStatus,
    RunEvent,
    RunEventType,
    RunManifest,
    RunStatus,
    Tradability,
)
from tradingagents.platform.artifacts import (
    ArtifactIntegrityError,
    ArtifactService,
    LocalArtifactStore,
)
from tradingagents.platform.auth import InvalidCredentials, OwnerAuth, OwnerPrincipal
from tradingagents.platform.decisions import DecisionLifecycle
from tradingagents.platform.events import RunEventNotFound, RunEventStore
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.jobs import DurableJobQueue, JobConflict
from tradingagents.platform.market_data import (
    InsufficientBenchmarkCoverage,
    TimeSeriesSnapshotService,
    TimeSeriesUnavailable,
    build_time_series_view,
    slice_time_series,
)
from tradingagents.platform.observability import MetricsRegistry, request_id_scope
from tradingagents.platform.persistence import (
    AmbiguousInstrumentAlias,
    Database,
    PlatformRepository,
)

from .schemas import (
    DecisionStateResponse,
    DecisionTransitionRequest,
    InstrumentDetailResponse,
    LoginRequest,
    LoginResponse,
    OwnerResponse,
    RunAcceptedResponse,
    RunCreateRequest,
    StatusResponse,
    TimeSeriesResponse,
)
from .settings import ApiSettings

API_PREFIX = "/api/v1"
SESSION_COOKIE = "ta_session"
CSRF_COOKIE = "ta_csrf"
CSRF_HEADER = "X-CSRF-Token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
cookie_scheme = APIKeyCookie(name=SESSION_COOKIE, auto_error=False)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
logger = logging.getLogger("tradingagents.platform.api")


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
    metrics = MetricsRegistry()

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
    app.state.metrics = metrics

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
    async def platform_request(request: Request, call_next):
        supplied_request_id = request.headers.get("X-Request-ID", "")
        request_id = (
            supplied_request_id
            if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
            else str(uuid4())
        )
        started = time.perf_counter()
        response = None
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        with request_id_scope(request_id):
            try:
                if request.method in UNSAFE_METHODS and request.headers.get(
                    "origin"
                ) != settings.allowed_origin.rstrip("/"):
                    response = JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "origin validation failed"},
                    )
                else:
                    response = await call_next(request)
                status_code = response.status_code
            finally:
                route_object = request.scope.get("route")
                route = getattr(route_object, "path", "unmatched")
                duration = time.perf_counter() - started
                metrics.observe_http(
                    method=request.method,
                    route=route,
                    status_code=status_code,
                    duration=duration,
                )
                logger.log(
                    logging.ERROR if status_code >= 500 else logging.INFO,
                    "http_request",
                    extra={
                        "method": request.method,
                        "route": route,
                        "status_code": status_code,
                        "duration_ms": round(duration * 1000, 3),
                    },
                )
        if response is None:
            raise RuntimeError("request completed without a response")
        response.headers["X-Request-ID"] = request_id
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

    @app.get(f"{API_PREFIX}/observability/metrics", tags=["observability"])
    def observability_metrics(_owner: OwnerDependency) -> Response:
        return Response(
            metrics.render(),
            media_type="text/plain; version=0.0.4",
        )

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
        asset_class: AssetClass | None = None,
        tradability: Tradability | None = None,
        venue: str | None = Query(default=None, min_length=1, max_length=64),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> tuple[InstrumentContract, ...]:
        return InstrumentMaster(PlatformRepository(session)).list(
            asset_class=asset_class,
            tradability=tradability,
            venue=venue,
            limit=limit,
        )

    @app.get(
        f"{API_PREFIX}/instruments/resolve",
        response_model=InstrumentDetailResponse,
        tags=["instruments"],
    )
    def resolve_instrument(
        _owner: OwnerDependency,
        session: SessionDependency,
        alias: str = Query(min_length=1, max_length=128),
        namespace: str | None = Query(
            default=None,
            min_length=1,
            max_length=32,
            pattern=r"^[a-z0-9][a-z0-9_.-]*$",
        ),
    ) -> InstrumentDetailResponse:
        repository = PlatformRepository(session)
        try:
            instrument = InstrumentMaster(repository).resolve(alias, namespace=namespace)
        except AmbiguousInstrumentAlias as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="instrument alias is ambiguous; provide namespace",
            ) from error
        if instrument is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="instrument not found",
            )
        return InstrumentDetailResponse(
            instrument=instrument,
            aliases=repository.list_instrument_aliases(instrument.instrument_id),
        )

    @app.get(
        f"{API_PREFIX}/instruments/{{instrument_id}}",
        response_model=InstrumentDetailResponse,
        tags=["instruments"],
    )
    def get_instrument(
        instrument_id: UUID,
        _owner: OwnerDependency,
        session: SessionDependency,
    ) -> InstrumentDetailResponse:
        repository = PlatformRepository(session)
        instrument = repository.get_instrument(instrument_id)
        if instrument is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="instrument not found",
            )
        return InstrumentDetailResponse(
            instrument=instrument,
            aliases=repository.list_instrument_aliases(instrument.instrument_id),
        )

    @app.get(
        f"{API_PREFIX}/instruments/{{instrument_id}}/timeseries",
        response_model=TimeSeriesResponse,
        tags=["market-data"],
    )
    def get_time_series(
        instrument_id: UUID,
        owner: OwnerDependency,
        session: SessionDependency,
        dataset: str = Query(default="ohlcv.daily", min_length=1, max_length=128),
        as_of: datetime | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        benchmark_instrument_id: UUID | None = None,
    ) -> TimeSeriesResponse:
        requested_as_of = as_of or _now(settings)
        if requested_as_of.tzinfo is None or requested_as_of.astimezone(UTC) > _now(settings):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="as_of must be timezone-aware and not in the future",
            )
        repository = PlatformRepository(session)
        if repository.get_instrument(instrument_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="instrument not found",
            )
        snapshots = TimeSeriesSnapshotService(
            repository,
            ArtifactService(artifact_store, repository),
        )
        try:
            snapshot, series = snapshots.load(
                owner_id=owner.owner_id,
                instrument_id=instrument_id,
                dataset=dataset,
                as_of=requested_as_of,
            )
            series = slice_time_series(series, start=start, end=end)
            benchmark = None
            if benchmark_instrument_id is not None:
                _benchmark_snapshot, benchmark = snapshots.load(
                    owner_id=owner.owner_id,
                    instrument_id=benchmark_instrument_id,
                    dataset=dataset,
                    as_of=requested_as_of,
                )
                benchmark = slice_time_series(benchmark, start=start, end=end)
            view = build_time_series_view(series, benchmark=benchmark)
        except TimeSeriesUnavailable as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error
        except (InsufficientBenchmarkCoverage, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error
        return TimeSeriesResponse(snapshot=snapshot, view=view)

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
        if payload.decision_inputs is not None:
            job_payload["decision_inputs"] = payload.decision_inputs.model_dump(mode="json")
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
            snapshot_ids=payload.decision_inputs.snapshot_ids() if payload.decision_inputs else (),
            decision_inputs=payload.decision_inputs,
        )
        if payload.decision_inputs is not None:
            from tradingagents.platform.analysis.profiles import (
                resolve_analysis_profile,
                select_analysts,
            )
            from tradingagents.platform.analysis.snapshots import load_snapshot_context

            try:
                select_analysts(resolve_analysis_profile(instrument), run.selected_analysts)
                load_snapshot_context(ArtifactService(artifact_store, repository), run,
                                      payload.decision_inputs.snapshots_by_analyst)
                inputs = payload.decision_inputs
                if inputs.portfolio_snapshot_id is not None:
                    portfolio = repository.get_portfolio_snapshot(inputs.portfolio_snapshot_id, owner.owner_id)
                    policy = repository.get_policy(inputs.policy_id, inputs.policy_version, owner.owner_id)
                    if portfolio is None or portfolio.as_of != run.analysis_as_of or policy is None:
                        raise ValueError("risk inputs unavailable")
            except (ValueError, ArtifactIntegrityError) as error:
                raise HTTPException(status_code=422, detail="ineligible snapshot analysis inputs") from error
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
            metrics.open_sse()
            try:
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
            finally:
                metrics.close_sse()

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

    @app.get(f"{API_PREFIX}/decisions/{{decision_id}}/state", response_model=DecisionStateResponse, tags=["decisions"])
    def get_decision_state(decision_id: UUID, owner: OwnerDependency, session: SessionDependency):
        repository = PlatformRepository(session)
        candidate = repository.get_decision(decision_id, owner.owner_id)
        if candidate is None:
            raise HTTPException(status_code=404, detail="decision not found")
        events = repository.list_decision_events(decision_id, owner.owner_id)
        return DecisionStateResponse(candidate=candidate, events=events,
                                     current_status=DecisionLifecycle().apply(candidate, events))

    @app.post(f"{API_PREFIX}/decisions/{{decision_id}}/transitions", response_model=DecisionStateResponse, tags=["decisions"])
    def transition_decision(
        decision_id: UUID, body: DecisionTransitionRequest,
        owner: CsrfOwnerDependency, session: SessionDependency,
    ):
        repository = PlatformRepository(session, artifact_store=artifact_store)
        candidate = repository.get_decision(decision_id, owner.owner_id)
        if candidate is None:
            raise HTTPException(status_code=404, detail="decision not found")
        history = repository.list_decision_events(decision_id, owner.owner_id)
        target = {
            "approve": DecisionStatus.APPROVED, "reject": DecisionStatus.REJECTED,
            "review": DecisionStatus.REVIEW, "expire": DecisionStatus.EXPIRED,
        }[body.action]
        previous = next((item for item in history if item.event_id == body.event_id), None)
        try:
            event = DecisionLifecycleEvent(
                event_id=body.event_id, decision_id=decision_id, owner_id=owner.owner_id,
                actor_id=owner.owner_id, actor_type=DecisionActorType.OWNER,
                from_status=body.expected_status, to_status=target, reason=body.reason,
                occurred_at=previous.occurred_at if previous else _now(settings),
                policy_id=body.policy_id, policy_version=body.policy_version,
            )
            repository.add_decision_event(event)
        except ValueError as error:
            raise HTTPException(status_code=409, detail="decision transition rejected") from error
        events = repository.list_decision_events(decision_id, owner.owner_id)
        return DecisionStateResponse(candidate=candidate, events=events,
                                     current_status=DecisionLifecycle().apply(candidate, events))

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
