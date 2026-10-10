"""Explicit synthetic local web QA server; never opens an existing owner database.

Run: python -m scripts.web_fixture --synthetic-local-only
Login: fixture@example.com / synthetic-local-web-password
Use --fixture-worker for the real durable worker with synthetic graph output.
No vendor/model is called in either mode. Not an investment dataset.
"""

import argparse
import hashlib
import json
import math
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event, Thread
from uuid import uuid4

import uvicorn

from tradingagents._compat import UTC
from tradingagents.contracts import (
    DecisionCandidate,
    JobKind,
    LedgerTransaction,
    PolicyContract,
    PriceInterval,
    RunManifest,
    SnapshotManifest,
    StockScreenerPolicy,
    StockScreeningInput,
)
from tradingagents.platform.analysis import AnalysisEngine
from tradingagents.platform.api import ApiSettings, create_app as create_platform_app
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.jobs import JobWorker
from tradingagents.platform.jobs.analysis import AnalysisJobHandler
from tradingagents.platform.market_data import TimeSeriesSnapshotService, normalize_time_series
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.portfolio.service import PortfolioLedgerService
from tradingagents.platform.screening import DeterministicStockScreener


class SyntheticSnapshotGraph:
    """Offline QA substitute only; deliberately has no live propagate method."""

    def __init__(self, *, snapshot_reports, **kwargs):
        self.sources = sorted({row["snapshot_id"] for report in snapshot_reports.values()
                               for row in json.loads(report)})
        if not self.sources:
            raise ValueError("synthetic graph requires bound snapshots")

    def propagate_snapshots(self, *args, **kwargs):
        claims = (
            "SYNTHETIC LOCAL QA — generated fixture thesis, not investment research.",
            "Synthetic inputs do not establish live market conditions.",
            "Do not use this fixture to make an investment decision.",
        )
        narrative = {
            "rating": "Hold", "executive_summary": "SYNTHETIC GRAPH OUTPUT — NO MODEL CALL",
            "report_contract_version": "2.0", "summary_evidence": {
                "claim": "SYNTHETIC GRAPH OUTPUT — NO MODEL CALL", "snapshot_ids": self.sources},
            "investment_thesis": claims[0], "confidence": .5,
            "risks": [claims[1]], "invalidation_conditions": [claims[2]],
            "evidence_claims": [{"claim": claim, "snapshot_ids": self.sources} for claim in claims],
        }
        return {"final_trade_decision": narrative["executive_summary"],
                "structured_decision": narrative}, "Hold"


class InvalidSyntheticGraph(SyntheticSnapshotGraph):
    """Exercise the real invalid-output-to-REVIEW path without a model call."""

    def propagate_snapshots(self, *args, **kwargs):
        return {"final_trade_decision": "SYNTHETIC INVALID OUTPUT — NO MODEL CALL",
                "structured_decision": {"rating": "not-a-valid-rating"}}, "Review"


class BilingualSyntheticGraph(SyntheticSnapshotGraph):
    """Exercise saved bilingual reading through the real compiler/publication gates.

    This substitutes graph/model output for browser QA only. It is not evidence
    of LangGraph role parity, provider availability or financial translation.
    """

    def __init__(self, *, snapshot_reports, **kwargs):
        super().__init__(snapshot_reports=snapshot_reports, **kwargs)
        from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts

        self.facts = {source["snapshot_id"]: SnapshotMarketFacts(source)
                      for source in json.loads(snapshot_reports.get("market", "[]"))
                      if source["provenance"]["dataset"] == "ohlcv.daily"}
        if not self.facts:
            raise ValueError("bilingual fixture requires immutable daily prices")

    def propagate_snapshots(self, *args, **kwargs):
        from tradingagents.agents.research_schemas import LocalizedResearchReport
        from tradingagents.agents.utils.report_compiler import compile_report_v2
        from tradingagents.agents.utils.report_localization import reader_report
        from tradingagents.platform.analysis.research_validation import validate_canonical_report

        snapshot_id = next(iter(self.facts))
        thesis = ("SYNTHETIC LOCAL QA — the saved fixture close is ${{QA}}. "
                  "The opposing case is that generated price movements cannot establish a live trend. "
                  "Coverage is limited to synthetic price and volume.")
        risk = "Synthetic prices do not establish company fundamentals, news or market sentiment."
        invalidation = "Discard this fixture conclusion when reviewing any real investment."
        raw = {"rating": "Hold", "confidence": .5,
               "executive_summary": "SYNTHETIC LOCAL QA — saved bilingual reading test; no model or vendor call.",
               "investment_thesis": [{"claim": thesis, "snapshot_ids": [snapshot_id]}],
               "risks": [{"claim": risk, "snapshot_ids": [snapshot_id]}],
               "invalidation_conditions": [{"claim": invalidation, "snapshot_ids": [snapshot_id]}],
               "time_horizon": "Browser verification only.",
               "quantity_bindings": [{"key": "QA", "snapshot_id": snapshot_id,
                                      "fact_id": "latest.close", "decimal_places": 2}]}
        raw["report_contract_version"] = "2.0"
        raw["summary_evidence"] = {"claim": raw["executive_summary"], "snapshot_ids": [snapshot_id]}
        report = compile_report_v2(raw, self.facts)
        validate_canonical_report(report, self.facts, set(self.sources))
        amount = f"{report.observed_numbers[0].value:.2f}"
        localized = LocalizedResearchReport(en=reader_report(report), vi=(
            "## Tóm tắt\n\nDỮ LIỆU KIỂM THỬ SYNTHETIC LOCAL QA — kiểm tra cách đọc báo cáo song ngữ đã lưu; không gọi model hay nguồn dữ liệu.\n\n"
            "## Luận điểm đầu tư\n\n"
            f"DỮ LIỆU KIỂM THỬ SYNTHETIC LOCAL QA — giá đóng cửa giả lập đã lưu là ${amount}. "
            "Luận điểm đối lập: biến động giá được tạo giả lập không xác lập xu hướng thị trường thực tế. "
            "Phạm vi chỉ gồm giá và khối lượng giả lập.\n\n"
            "## Rủi ro\n\n- Giá giả lập không phản ánh phân tích cơ bản doanh nghiệp, tin tức hay tâm lý thị trường.\n\n"
            "## Điều kiện mất hiệu lực\n\n- Loại bỏ kết luận giả lập này khi xem xét bất kỳ khoản đầu tư thực tế nào.\n\n"
            "## Khung thời gian nghiên cứu\n\nChỉ dùng để kiểm tra trình duyệt."
        ))
        decision = report.model_dump(mode="json") | {"localized_report": localized.model_dump()}
        return {"structured_draft": raw, "structured_decision": decision,
                "final_trade_decision": localized.en,
                "market_report": "SYNTHETIC LOCAL QA — immutable generated daily prices; no live market research.",
                "investment_debate_state": {"history": "SYNTHETIC LOCAL QA — opposing case retained in the saved thesis."},
                "risk_debate_state": {"history": "SYNTHETIC LOCAL QA — real financial use is invalid."}}, "Hold"


class FailedSyntheticGraph(SyntheticSnapshotGraph):
    """Exercise durable retry/exhaustion without contacting a provider."""

    def propagate_snapshots(self, *args, **kwargs):
        raise RuntimeError("SYNTHETIC LOCAL QA failure — no provider was contacted")


def create_app(settings):
    """Synthetic browser fixtures must never acquire live market data."""
    from tradingagents.dataflows.platform_fred import MacroPreparationError
    from tradingagents.dataflows.platform_news import NewsPreparationError
    from tradingagents.dataflows.platform_prices import PricePreparationError
    from tradingagents.dataflows.platform_sec import SecPreparationError

    app = create_platform_app(settings)

    def unavailable(_instrument):
        raise PricePreparationError("unavailable")

    def unavailable_news(_instrument):
        raise NewsPreparationError("unavailable")

    def unavailable_sec(_instrument):
        raise SecPreparationError("unavailable")

    def unavailable_macro(_instrument, _series_id, **_kwargs):
        raise MacroPreparationError("unavailable")

    app.state.fetch_daily_prices = unavailable
    app.state.collect_yahoo_news = unavailable_news
    app.state.collect_sec_facts = unavailable_sec
    app.state.collect_fred_series = unavailable_macro
    from tradingagents.dataflows.platform_social import SocialPreparationError
    def unavailable_social(*_args, **_kwargs):
        raise SocialPreparationError("unavailable")
    app.state.collect_social = unavailable_social
    return app


def fixture_session_seconds(value):
    seconds = int(value)
    if not 300 <= seconds <= 43200:
        raise argparse.ArgumentTypeError("fixture session duration must be 300–43200 seconds")
    return seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-local-only", action="store_true", required=True)
    parser.add_argument("--fixture-worker", action="store_true",
                        help="Run durable jobs with synthetic graph output; never calls models/vendors")
    parser.add_argument("--built-web", action="store_true",
                        help="Serve the existing web/dist build and API together on 127.0.0.1:8000")
    parser.add_argument("--all-assets", action="store_true",
                        help="Seed labelled synthetic daily charts for ETF, BTC/ETH and NQ/ES QA")
    parser.add_argument("--screening", action="store_true",
                        help="Seed a deterministic screening from labelled synthetic input facts")
    parser.add_argument("--graph-result", choices=("valid", "bilingual", "invalid", "failed"), default="valid",
                        help="Synthetic worker outcome; bilingual exercises compiled saved reading, invalid exercises REVIEW, failed exercises retries")
    parser.add_argument("--session-seconds", type=fixture_session_seconds, default=43200,
                        help="Synthetic-only session TTL for browser expiry QA (300–43200)")
    args = parser.parse_args()
    if args.graph_result != "valid" and not args.fixture_worker:
        parser.error("--graph-result requires --fixture-worker")
    cache = Path(__file__).resolve().parents[1] / ".cache"
    cache.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="web-fixture-", dir=cache))
    url = f"sqlite:///{directory / 'fixture.db'}"
    upgrade_database(url)
    now = datetime.now(UTC).replace(microsecond=0)
    database = Database(url)
    with database.session() as session:
        owner = OwnerAuth(session).bootstrap_owner("fixture@example.com", "synthetic-local-web-password", now=now)
        repository = PlatformRepository(session)
        master = InstrumentMaster(repository)
        master.bootstrap()
        instrument = next(item for item in master.list() if item.canonical_symbol == "AAPL")
        bars = []
        for index in range(60):
            close = round(180 + index * .25 + math.sin(index / 4) * 4, 2)
            bars.append({"timestamp": now - timedelta(days=60-index), "open": close - .3,
                         "high": close + 1, "low": close - 1, "close": close,
                         "volume": 1_000_000 + index * 1000})
        series = normalize_time_series(instrument=instrument, dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY, as_of=now, annualization_periods=252, bars=bars)
        artifacts = ArtifactService(LocalArtifactStore(directory / "artifacts"), repository)
        source = TimeSeriesSnapshotService(repository, artifacts).persist(
            owner_id=owner.owner_id, series=series, vendor="SYNTHETIC LOCAL QA — NOT MARKET DATA", retrieved_at=now)
        if args.screening:
            inputs = []
            for asset in master.list():
                if asset.canonical_symbol not in {"AAPL", "SPY"}:
                    continue
                facts = {"notice": "SYNTHETIC QA FACTS — NOT INVESTMENT DATA",
                    "market_cap_usd": 100_000_000_000, "average_dollar_volume_20d_usd": 100_000_000,
                    "last_price_usd": 100, "history_days": 500, "annualized_volatility": .3}
                payload = json.dumps(facts, sort_keys=True).encode()
                manifest = SnapshotManifest(snapshot_id=uuid4(), instrument_id=asset.instrument_id,
                    dataset="screening.inputs", vendor="SYNTHETIC LOCAL QA — NOT MARKET DATA",
                    as_of=now, retrieved_at=now, source_start=now, source_end=now,
                    content_hash="sha256:" + hashlib.sha256(payload).hexdigest(), quality_status="OK")
                repository.add_snapshot(manifest)
                artifacts.create(owner_id=owner.owner_id, kind="snapshot_payload", media_type="application/json",
                    content=payload, snapshot_id=manifest.snapshot_id, instrument_id=asset.instrument_id, created_at=now)
                inputs.append(StockScreeningInput(instrument=asset, observed_at=now,
                    source_snapshot_id=manifest.snapshot_id, source_content_hash=manifest.content_hash,
                    quality_status="OK", **{key: value for key, value in facts.items() if key != "notice"}))
            screener = DeterministicStockScreener(artifacts)
            screening = screener.screen(inputs=tuple(inputs),
                policy=StockScreenerPolicy(policy_id="SYNTHETIC-QA-NOT-OWNER-POLICY"), as_of=now, generated_at=now)
            screener.persist(owner_id=owner.owner_id, snapshot=screening)
        if args.all_assets:
            bases = {"SPY": 500, "QQQ": 430, "BTC-USD": 60000, "ETH-USD": 3000,
                     "NQ=F": 20000, "ES=F": 5000}
            for asset in master.list():
                if asset.canonical_symbol not in bases:
                    continue
                scale = bases[asset.canonical_symbol] / 180
                fixture_bars = [{**bar, **{key: round(bar[key] * scale, 2)
                    for key in ("open", "high", "low", "close")}} for bar in bars]
                fixture_series = normalize_time_series(instrument=asset, dataset="ohlcv.daily",
                    interval=PriceInterval.ONE_DAY, as_of=now,
                    annualization_periods=365 if asset.asset_class.value == "crypto" else 252,
                    bars=fixture_bars)
                TimeSeriesSnapshotService(repository, artifacts).persist(owner_id=owner.owner_id,
                    series=fixture_series, vendor="SYNTHETIC LOCAL QA — NOT MARKET DATA", retrieved_at=now)
        ledger_id = uuid4()
        repository.add_ledger_transaction(LedgerTransaction(transaction_id=uuid4(), ledger_id=ledger_id,
            owner_id=owner.owner_id, occurred_at=now - timedelta(days=62), transaction_type="cash_deposit",
            currency="USD", cash_amount="10000", external_reference="SYNTHETIC-QA-DEPOSIT"))
        repository.add_ledger_transaction(LedgerTransaction(transaction_id=uuid4(), ledger_id=ledger_id,
            owner_id=owner.owner_id, occurred_at=now - timedelta(days=61), transaction_type="buy",
            currency="USD", instrument_id=instrument.instrument_id, quantity="10", unit_price="180",
            external_reference="SYNTHETIC-QA-HISTORICAL-ENTRY-NOT-AN-ORDER"))
        PortfolioLedgerService(artifacts).replay(ledger_id=ledger_id, owner_id=owner.owner_id,
            base_currency="USD", price_snapshot_ids={instrument.instrument_id: source.snapshot_id},
            as_of=now, max_price_age=timedelta(days=2))
        repository.add_policy(PolicyContract(policy_id=uuid4(), owner_id=owner.owner_id,
            name="SYNTHETIC QA POLICY — NOT OWNER LIMITS", policy_version="fixture-1", asset_class="equity",
            effective_at=now, parameters={"max_position_weight": .3, "max_asset_class_weight": .7,
                "max_gross_exposure": .8, "max_turnover": .2, "max_correlation": .8, "min_cash_weight": .2,
                "correlation_periods": 20, "correlation_max_age_seconds": 172800}))
        # Deliberately REVIEW with no risk approval. This is seeded QA content,
        # not a worker/model result and cannot be approved.
        run = RunManifest(run_id=uuid4(), owner_id=owner.owner_id, instrument_id=instrument.instrument_id,
            analysis_as_of=now, status="queued", created_at=now, selected_analysts=("market",),
            llm_provider="synthetic-no-provider", quick_model="fixture", deep_model="fixture",
            config_hash="sha256:" + "0" * 64, prompt_version="fixture", snapshot_ids=(source.snapshot_id,))
        repository.save_run(run)
        repository.add_decision(DecisionCandidate(decision_id=uuid4(), run_id=run.run_id,
            owner_id=owner.owner_id, instrument_id=instrument.instrument_id, as_of=now,
            status="review", rating="Review", confidence=0,
            thesis="SYNTHETIC LOCAL QA — seeded review candidate, not model output or investment advice.",
            risks=("Synthetic fixture has no live-provider verification.",),
            invalidation_conditions=("Do not use this fixture to make an investment decision.",),
            evidence=(), data_quality="UNAVAILABLE", policy_checks=()))
    database.dispose()
    stopped = Event()
    thread = None
    worker_database = None
    if args.fixture_worker:
        worker_database = Database(url)
        handler = AnalysisJobHandler(worker_database, LocalArtifactStore(directory / "artifacts"),
            engine=AnalysisEngine(graph_factory={"valid": SyntheticSnapshotGraph,
                "bilingual": BilingualSyntheticGraph,
                "invalid": InvalidSyntheticGraph, "failed": FailedSyntheticGraph}[args.graph_result]))
        worker = JobWorker(worker_database, worker_id="synthetic-local-qa",
                           handlers={JobKind.ANALYSIS_RUN: handler})

        def process_jobs():
            while not stopped.is_set():
                worker.run_once()
                stopped.wait(.25)

        thread = Thread(target=process_jobs, name="synthetic-local-qa", daemon=True)
        thread.start()
    print(f"Synthetic-only API on 127.0.0.1:8000; fixture worker={args.fixture_worker}; no provider calls.")
    try:
        uvicorn.run(create_app(ApiSettings(database_url=url, artifact_root=directory / "artifacts",
            allowed_origin="http://127.0.0.1:8000" if args.built_web else "http://127.0.0.1:5173",
            web_root=Path(__file__).resolve().parents[1] / "web" / "dist" if args.built_web else None,
            secure_cookies=False,
            session_ttl=timedelta(seconds=args.session_seconds),
            llm_provider="synthetic-local-qa", quick_model="fixture", deep_model="fixture")),
            host="127.0.0.1", port=8000, access_log=False)
    finally:
        stopped.set()
        if thread is not None:
            thread.join()
        if worker_database is not None:
            worker_database.dispose()


if __name__ == "__main__":
    main()
