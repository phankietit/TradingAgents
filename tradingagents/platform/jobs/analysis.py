"""Durable research handler; unattested legacy graph data cannot authorize readiness."""

import json
from uuid import uuid5

from tradingagents._compat import UTC
from tradingagents.contracts import ArtifactKind, RunEventType
from tradingagents.platform.analysis import (
    AnalysisEngine,
    AnalysisRequest,
)
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.analysis.profiles import resolve_analysis_profile
from tradingagents.platform.analysis.snapshots import load_snapshot_context
from tradingagents.platform.analysis.stage_records import ResearchStageService
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.persistence import PlatformRepository

from .decision_pipeline import build_run_decision, load_run_portfolio


def publication_warning(snapshot_context):
    """Deterministic disclosure retained even if a model omits its limitation."""
    if snapshot_context is None:
        return ""
    warnings = []
    delayed = {source.manifest.source_end for sources in snapshot_context.by_analyst.values()
               for source in sources if source.manifest.metadata.get("freshness") == "delayed"}
    if delayed:
        cutoffs = ", ".join(sorted(value.isoformat() for value in delayed if value is not None))
        warnings.append(
            f"DATA LIMITATION / GIỚI HẠN DỮ LIỆU: Source publication delayed; completed candles through "
            f"{cutoffs}. Not a current-market assessment. No missing candle filled. / "
            f"Nguồn cập nhật trễ; nến hoàn tất đến {cutoffs}. Không phản ánh thị trường hiện tại; "
            "không tự bù nến thiếu."
        )
    if any(source.manifest.dataset == "news"
           and source.manifest.metadata.get("coverage") == "recent_feed_not_exhaustive"
           for sources in snapshot_context.by_analyst.values() for source in sources):
        warnings.append(
            "NEWS COVERAGE / PHẠM VI TIN TỨC: Recent vendor headlines are not an exhaustive "
            "record of market or economic events. Missing coverage is unavailable, not neutral; "
            "do not infer the absence of catalysts. / Tin gần đây từ nguồn không bao quát mọi "
            "sự kiện thị trường hay kinh tế. Thiếu nguồn là chưa có dữ liệu, không phải trung lập; "
            "không suy luận rằng không có chất xúc tác."
        )
    if any(source.manifest.dataset == "fundamentals"
           and source.manifest.vendor == "sec_edgar"
           for sources in snapshot_context.by_analyst.values() for source in sources):
        warnings.append(
            "FILING COVERAGE / PHẠM VI BÁO CÁO: SEC facts cover reported US GAAP tags "
            "and their filing dates, not a complete company profile or live valuation. "
            "The saved response is current-vintage evidence and cannot be backdated. / "
            "Số liệu SEC chỉ gồm các chỉ tiêu US GAAP được công bố và ngày nộp báo cáo, "
            "không phải toàn bộ hồ sơ doanh nghiệp hay định giá trực tiếp. Bản đã lưu "
            "là dữ liệu ghi nhận hiện tại, không được gán ngược cho thời điểm quá khứ."
        )
    return "\n\n".join(warnings) + ("\n\n" if warnings else "")


class AnalysisJobHandler:
    """Run the existing graph outside DB transactions, persist one immutable result.

    Legacy tools do not yet attest every read to a run-bound snapshot. Retain
    useful research but withhold approval-ready decisions until that evidence
    exists. A free-text fallback is never parsed into a structured decision.
    """

    def __init__(self, database, artifact_store, *, engine=None, prompt_version="1"):
        self.database = database
        self.artifact_store = artifact_store
        self.engine = engine or AnalysisEngine()
        self.prompt_version = prompt_version

    def __call__(self, job, context):
        context.raise_if_cancelled()
        context.heartbeat()
        report_id = uuid5(job.run_id, "analysis-report-v1")
        decision_id = uuid5(job.run_id, "decision-v1")
        with self.database.session() as session:
            repository = PlatformRepository(session, artifact_store=self.artifact_store)
            run = repository.get_run(job.run_id, job.owner_id)
            if run is None or run.prompt_version != self.prompt_version:
                raise ValueError("run or supported prompt version unavailable")
            expected_payload = {
                "instrument_id": str(run.instrument_id),
                "analysis_as_of": run.analysis_as_of.astimezone(UTC).isoformat(),
                "selected_analysts": list(run.selected_analysts),
                "config_hash": run.config_hash,
            }
            if run.decision_inputs is not None:
                expected_payload["decision_inputs"] = run.decision_inputs.model_dump(mode="json")
            if run.report_language is not None:
                expected_payload["report_language"] = run.report_language
            if job.payload != expected_payload:
                raise ValueError("analysis job does not match its immutable run")
            artifacts = ArtifactService(self.artifact_store, repository)
            existing = artifacts.read(report_id, job.owner_id)
            candidate = repository.get_decision(decision_id, job.owner_id)
            if existing is not None and candidate is not None:
                if existing[0].run_id != run.run_id or candidate.run_id != run.run_id:
                    raise ValueError("analysis output context mismatch")
                evidence_id = json.loads(existing[1]).get("evidence_artifact_id")
                if evidence_id:
                    from uuid import UUID

                    if artifacts.read(UUID(evidence_id), job.owner_id) is None:
                        raise ValueError("analysis evidence output missing")
                    return (report_id, UUID(evidence_id))
                return (report_id,)
            if existing is not None or candidate is not None:
                raise ValueError("incomplete analysis output transaction")
            instrument = repository.get_instrument(run.instrument_id)
            if instrument is None:
                raise ValueError("run instrument unavailable")
            snapshot_context = load_snapshot_context(artifacts, run, run.decision_inputs.snapshots_by_analyst) if run.decision_inputs else None
            portfolio = load_run_portfolio(repository, run)
        def emit(event_type, payload):
            from datetime import datetime

            # The same fenced session used for publication rejects cancelled
            # or expired workers. No model call is made under this transaction.
            with context.publication_session() as event_session:
                RunEventStore(event_session).append(owner_id=run.owner_id, run_id=run.run_id,
                    event_type=RunEventType(event_type), occurred_at=datetime.now(UTC),
                    payload={**payload, "attempt": job.attempt})

        stage_sequence = 0

        def save_stage(stage, outputs):
            nonlocal stage_sequence
            from datetime import datetime

            stage_sequence += 1
            with context.publication_session() as stage_session:
                stage_repository = PlatformRepository(stage_session, artifact_store=self.artifact_store)
                service = ResearchStageService(ArtifactService(self.artifact_store, stage_repository))
                manifest = service.persist(run, stage=stage, outputs=outputs,
                    attempt=job.attempt, sequence=stage_sequence,
                    snapshot_attestation="PASS" if snapshot_context is not None else "UNVERIFIED")
                if manifest is not None:
                    RunEventStore(stage_session).append(owner_id=run.owner_id, run_id=run.run_id,
                        event_type=RunEventType.ARTIFACT_CREATED, occurred_at=datetime.now(UTC),
                        payload={"artifact_id": str(manifest.artifact_id),
                                 "kind": manifest.kind.value, "stage": stage,
                                 "attempt": job.attempt, "research_quality": "unvalidated"})
                    return manifest.artifact_id
            return None

        observer = ResearchObserver(check_cancelled=context.raise_if_cancelled, emit=emit,
                                    save_stage=save_stage)
        result = self.engine.analyze(AnalysisRequest(
            instrument=instrument, analysis_date=run.analysis_as_of.date(),
            selected_analysts=run.selected_analysts,
            snapshot_context=snapshot_context,
            portfolio=portfolio,
            execution_observer=observer,
            config_overrides={"llm_provider": run.llm_provider,
                              "quick_think_llm": run.quick_model,
                              "deep_think_llm": run.deep_model,
                              **({"output_language": {"en": "English", "vi": "Vietnamese", "en-vi": "English and Vietnamese"}[run.report_language]}
                                 if run.report_language is not None else {})},
        ))
        context.raise_if_cancelled()
        context.heartbeat()  # Reject a lost/expired lease before publishing.
        raw = result.decision_payload.model_dump(mode="json") if result.decision_payload else {}
        market_sources = [SnapshotMarketFacts(source)
            for source in json.loads(snapshot_context.reports(run.instrument_id, run.selected_analysts).get("market", "[]"))
            if source["provenance"]["dataset"] == "ohlcv.daily"] if snapshot_context else []
        # Deliberately exclude raw graph messages, which may contain provider
        # objects or unrelated prompt context. Preserve the research artifact.
        report = {
            "run_id": str(run.run_id), "decision_id": str(decision_id),
            "profile": result.profile_name, "reference_only": result.reference_only,
            "selected_analysts": result.selected_analysts,
            "narrative": publication_warning(snapshot_context)
                + result.final_state.get("final_trade_decision", result.narrative_signal),
            "structured_narrative": raw or None,
            "snapshot_attestation": "PASS" if snapshot_context is not None else "UNVERIFIED",
            "report_language": run.report_language,
            "publication_warning": publication_warning(snapshot_context),
            "structured_diagnostics": result.final_state.get("structured_diagnostics", []),
            "execution": observer.receipt(),
            "source_quality": "verified" if snapshot_context is not None else "unverified",
            "research_quality": "structured" if raw else "unvalidated",
            "validation_issues": list(result.validation_issues),
            "quantitative_references": [item.model_dump(mode="json") for item in result.quantitative_references],
            "localized_report": (result.final_state.get("structured_decision") or {}).get("localized_report"),
            "rejected_structured_decision": result.final_state.get("rejected_structured_decision"),
            "structured_draft": result.final_state.get("structured_draft"),
            "canonical_research": result.final_state.get("structured_decision"),
            "coverage": {"selected": list(run.selected_analysts),
                         "expected": list(resolve_analysis_profile(instrument).allowed_analysts),
                         "missing": [role for role in resolve_analysis_profile(instrument).allowed_analysts if role not in run.selected_analysts],
                         "all_profile_roles_present": set(run.selected_analysts) == set(resolve_analysis_profile(instrument).allowed_analysts)},
            "market_facts": [source.summary() for source in market_sources],
            "market_history": [source.chart() for source in market_sources],
            "research_sections": {key: result.final_state[key] for key in (
                "market_report", "sentiment_report", "news_report", "fundamentals_report",
                "investment_plan", "trader_investment_plan")
                if isinstance(result.final_state.get(key), str)},
            "debate_sections": {key: result.final_state.get(key, {}).get("history", "")
                for key in ("investment_debate_state", "risk_debate_state")},
        }
        with context.publication_session() as session:
            repository = PlatformRepository(session, artifact_store=self.artifact_store)
            artifacts = ArtifactService(self.artifact_store, repository)
            candidate, evidence = build_run_decision(artifacts, run, result)
            report["evidence_artifact_id"] = str(evidence.artifact_id) if evidence else None
            artifacts.create(
                artifact_id=report_id, owner_id=run.owner_id, run_id=run.run_id,
                instrument_id=run.instrument_id, kind=ArtifactKind.ANALYSIS_REPORT,
                media_type="application/json", created_at=run.created_at,
                content=json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(),
            )
            repository.add_decision(candidate)
        return (report_id, evidence.artifact_id) if evidence else (report_id,)
