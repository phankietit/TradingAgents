"""Full-history/PIT/native-unit macro fixtures; no live API/model evidence."""

import json
import subprocess
import sys
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.summary_fixtures import summary_response
from tests.test_platform_fred import NOW, collect, documents
from tests.test_price_preparation import AAPL
from tests.test_report_compiler import draft
from tradingagents.agents.utils.financial_validation import create_financial_validation
from tradingagents.agents.utils.report_compiler import compile_report
from tradingagents.agents.utils.report_localization import localize_report
from tradingagents.contracts import DataQualityStatus
from tradingagents.graph.snapshot_analysis import snapshot_analyst_nodes
from tradingagents.platform.analysis.engine import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.macro_facts import SnapshotMacroFacts
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    validate_canonical_report,
)
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot, SnapshotAnalysisContext
from tradingagents.platform.jobs.analysis import publication_warning
from tradingagents.platform.market_data.macro import _manifest


def macro_source(*, count=101, missing=True, units="Percent"):
    raw = documents()
    raw["series"]["seriess"][0]["units"] = units
    raw["series/observations"]["observations"] = [
        {"date": (NOW.date() - timedelta(days=count - index)).isoformat(),
            "value": "." if missing and index == 4 else str(index / 10),
            "realtime_start": "2026-10-02", "realtime_end": "2026-10-02"}
        for index in range(count)]
    raw["series/observations"]["count"] = count
    collection = collect(raw)
    manifest = _manifest(collection, uuid4())
    return {"snapshot_id": str(manifest.snapshot_id), "provenance": manifest.model_dump(mode="json"),
        "data": collection.model_dump(mode="json")}


def macro_context(source):
    return SnapshotAnalysisContext(as_of=NOW, by_analyst={"news": (
        AnalysisSnapshot(manifest=source["provenance"], payload=json.dumps(source["data"],
            ensure_ascii=False, sort_keys=True, separators=(",", ":"))),)}, source_max_age_seconds={"news": 86400})


def macro_draft(source, fact_id=None):
    raw, _ = draft()
    facts = SnapshotMacroFacts(source)
    raw["investment_thesis"] = [{"claim": "{{QA}}. The observation does not establish causality.",
        "snapshot_ids": [source["snapshot_id"]]}]
    for name in ("risks", "invalidation_conditions"):
        for claim in raw[name]:
            claim["snapshot_ids"] = [source["snapshot_id"]]
    raw["quantity_bindings"][0].update(snapshot_id=source["snapshot_id"],
        fact_id=fact_id or next(iter(facts.fact_catalog())))
    return raw, {source["snapshot_id"]: facts}


def test_full_history_page_missing_rows_and_latest_only_projection_are_not_truncation():
    source = macro_source()
    facts = SnapshotMacroFacts(source)
    assert len(facts.fact_catalog()) == 1
    first, last = facts.page(limit=50), facts.page(offset=100)
    assert first["next_offset"] == 50 and last["next_offset"] is None
    assert first["observations"][4]["value"] is None
    assert facts.resolve_fact(first["observations"][4]["fact_id"]) is None
    assert facts.resolve_fact(first["observations"][0]["fact_id"]) == 0  # Real zero is not missing.
    assert last["observations"][0]["value"] == 10
    assert facts.summary()["total_observations"] == 101
    assert "release" in facts.summary()["limitations"]
    assert macro_context(source).reports(AAPL.instrument_id, ("news",))


@pytest.mark.parametrize("field,value", [("series_id", "OTHER"), ("units", "Index"),
    ("vintage_date", "2026-10-01"),
    ("retrieved_at", (NOW + timedelta(seconds=1)).isoformat())])
def test_recomputed_payload_hash_cannot_hide_collection_manifest_mismatch(field, value):
    source = macro_source()
    source["data"][field] = value
    # Mimics internally consistent blob hashing, not an authentic canonical manifest.
    import hashlib
    encoded = json.dumps(source["data"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    source["provenance"]["content_hash"] = "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
    with pytest.raises(ValueError):
        macro_context(source).reports(AAPL.instrument_id, ("news",))


def test_changed_title_cannot_match_original_immutable_payload_hash():
    source = macro_source()
    source["data"]["title"] = "Synthetic replacement"
    with pytest.raises(ValueError):
        macro_context(source).reports(AAPL.instrument_id, ("news",))


@pytest.mark.parametrize("field,value", [("canonical_symbol", "OTHER"), ("asset_class", "crypto"),
    ("venue", "OTHER"), ("quote_currency", "EUR"), ("timezone", "UTC")])
def test_self_consistent_in_memory_source_cannot_replace_request_instrument_metadata(field, value):
    source = macro_source()
    collection = collect().model_copy(update={field: value})
    source.update(data=collection.model_dump(mode="json"),
        provenance=_manifest(collection, uuid4()).model_dump(mode="json"))
    source["snapshot_id"] = source["provenance"]["snapshot_id"]

    def forbidden(**kwargs):
        pytest.fail("Invalid canonical identity reached graph/client construction")

    with pytest.raises(ValueError, match="instrument identity"):
        AnalysisEngine(graph_factory=forbidden).analyze(AnalysisRequest(instrument=AAPL,
            analysis_date=NOW.date(), selected_analysts=("news",), snapshot_context=macro_context(source)))


@pytest.mark.parametrize("field,value", [("dataset", "news"), ("vendor", "fixture"),
    ("quality_status", DataQualityStatus.STALE.value), ("metadata", {}),
    ("source_end", (NOW - timedelta(seconds=1)).isoformat())])
def test_provenance_cannot_be_relabelled_to_eligible_macro(field, value):
    source = macro_source()
    source["provenance"][field] = value
    with pytest.raises(ValueError):
        SnapshotMacroFacts(source)


@pytest.mark.parametrize("args", [{"offset": True}, {"offset": -1}, {"offset": 101},
    {"limit": True}, {"limit": 0}, {"limit": 251}])
def test_invalid_page_queries_refuse(args):
    with pytest.raises(ValueError):
        SnapshotMacroFacts(macro_source()).page(**args)


@pytest.mark.parametrize("args", [{"operation": "ratio"}, {"operation": []},
    {"left_period": "2026-99-02"}, {"left_period": "2026-10-03"},
    {"right_period": "2020-01-01"}, {"right_period": True}])
def test_invalid_calculation_arguments_refuse(args):
    query = {"operation": "difference", "left_period": "2026-10-02", "right_period": "2026-10-01"}
    query.update(args)
    with pytest.raises(ValueError):
        SnapshotMacroFacts(macro_source()).calculation(**query)


def test_negative_denominator_and_nonfinite_derived_value_stay_unavailable():
    source = macro_source(count=2, missing=False)
    source["data"]["observations"][0]["value"] = -1e308
    source["data"]["observations"][1]["value"] = 1e308
    from tradingagents.dataflows.platform_fred import MacroCollection
    collection = MacroCollection.model_validate(source["data"])
    source["provenance"] = _manifest(collection, source["snapshot_id"]).model_dump(mode="json")
    facts = SnapshotMacroFacts(source)
    for operation in ("pct_change", "difference"):
        result = facts.calculation(operation=operation, left_period="2026-10-02", right_period="2026-10-01")
        assert result["value"] is None and result["status"] == "unavailable"
        assert facts.resolve_fact(result["fact_id"]) is None


def test_unrepresentable_macro_quantity_is_a_publication_failure_not_an_unhandled_decimal_error():
    source = macro_source(count=2, missing=False)
    source["data"]["observations"][-1]["value"] = 1e308
    from tradingagents.dataflows.platform_fred import MacroCollection
    collection = MacroCollection.model_validate(source["data"])
    source["provenance"] = _manifest(collection, source["snapshot_id"]).model_dump(mode="json")
    raw, facts = macro_draft(source)
    with pytest.raises(PublicationValidationError) as error:
        compile_report(raw, facts)
    assert error.value.issues == ("numeric_claim_not_supported",)


@pytest.mark.parametrize("role", ["market", "social", "fundamentals"])
def test_macro_cannot_substitute_for_other_analyst_roles(role):
    context = macro_context(macro_source())
    invalid = context.model_copy(update={"by_analyst": {role: context.by_analyst["news"]},
        "source_max_age_seconds": {role: 86400}})
    with pytest.raises(ValueError):
        invalid.reports(AAPL.instrument_id, (role,))


@pytest.mark.parametrize("operation,expected,unit", [
    ("difference", .1, "percentage points"), ("pct_change", (10 / 9.9 - 1) * 100, "percent")])
def test_exact_arithmetic_denominator_and_units_replay(operation, expected, unit):
    facts = SnapshotMacroFacts(macro_source())
    result = facts.calculation(operation=operation, left_period="2026-10-02", right_period="2026-10-01")
    assert result["value"] == pytest.approx(expected) and result["output_unit"] == unit
    assert facts.resolve_fact(result["fact_id"]) == result["value"]
    assert result["reference_period"] == "2026-10-01"


@pytest.mark.parametrize("index", [0, 4])  # Zero and explicitly missing.
def test_missing_or_zero_reference_is_not_a_valid_percent_change(index):
    facts = SnapshotMacroFacts(macro_source())
    point = facts.page()["observations"][index]
    assert point["value"] == (0 if index == 0 else None)
    right = point["observation_label"]
    result = facts.calculation(operation="pct_change",
        left_period="2026-10-02", right_period=right)
    assert result["value"] is None and result["status"] == "unavailable"


@pytest.mark.parametrize("mutation", ["series", "unit", "vintage", "period", "literal", "extra_operand"])
def test_fact_ids_are_series_unit_vintage_and_exact_period_bound(mutation):
    facts = SnapshotMacroFacts(macro_source())
    original = next(iter(facts.fact_catalog()))
    wrong = {"series": original.replace("DGS10", "CPIAUCSL"),
        "unit": original.replace(facts._unit, "0" * 16),
        "vintage": original.replace("vintage.2026-10-02", "vintage.2026-10-01"),
        "period": original.replace("value.2026-10-02", "value.2026-10-03"),
        "literal": original.replace("value.2026-10-02", "value.100"),
        "extra_operand": original.replace("value.2026-10-02", "value.2026-10-02.2026-10-01")}[mutation]
    assert facts.resolve_fact(wrong) is None


@pytest.mark.parametrize("operation", ["value", "difference", "pct_change"])
@pytest.mark.parametrize("units", ["Percent", "Index 1982-1984=100", "Billions of Dollars"])
def test_owned_macro_statements_compile_preserve_native_units_and_bilingual_quantities(operation, units):
    source = macro_source(units=units)
    facts = SnapshotMacroFacts(source)
    fid = (next(iter(facts.fact_catalog())) if operation == "value" else
        facts.calculation(operation=operation, left_period="2026-10-02", right_period="2026-10-01")["fact_id"])
    raw, sources = macro_draft(source, fid)
    compiled = compile_report(raw, sources)
    validate_canonical_report(compiled, sources, set(sources))
    statement = facts.statement(fid, format(compiled.observed_numbers[0].value, ".2f"))
    assert statement in compiled.investment_thesis
    from tradingagents.agents.research_schemas import LocalizedResearchReport
    LocalizedResearchReport(en=statement, vi=facts.statement(fid,
        format(compiled.observed_numbers[0].value, ".2f"), vi=True))
    assert "vintage" in statement and "2026-10-02" in statement


@pytest.mark.parametrize("text", ["Inflation was {{QA}}%.", "GDP was USD {{QA}} billion.",
    "Not {{QA}}.", "{{QA}} per share."])
def test_models_cannot_attach_invented_macro_metric_scale_unit_or_negation(text):
    source = macro_source()
    raw, facts = macro_draft(source)
    raw["investment_thesis"][0]["claim"] = text
    with pytest.raises(PublicationValidationError) as error:
        compile_report(raw, facts)
    assert error.value.issues == ("macro_statement_requires_standalone_anchor",)


def test_canonical_macro_number_without_owned_semantics_cannot_bypass_compiler():
    source = macro_source()
    raw, facts = macro_draft(source)
    compiled = compile_report(raw, facts)
    modified = compiled.model_copy(update={"investment_thesis": "Unverified inflation 10.00%."})
    with pytest.raises(PublicationValidationError, match="publication"):
        validate_canonical_report(modified, facts, set(facts))


def test_macro_financial_review_and_protected_translation_use_the_same_sources():
    source = macro_source()
    raw, facts = macro_draft(source)
    review_calls = []

    class Reviewer:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda prompt: review_calls.append(prompt) or schema.model_validate(summary_response(raw, [source["snapshot_id"]])))

    reviewed = create_financial_validation(Reviewer(), {"news": json.dumps([source])})({"structured_draft": raw})
    assert reviewed["structured_decision"] is not None and len(review_calls) == 1
    compiled = compile_report(raw, facts)

    class Translator:
        def with_structured_output(self, schema):
            def invoke(prompt):
                rows = json.loads(prompt.split("<translation_blocks>\n")[1].split("\n</translation_blocks>")[0])
                return schema(blocks=[{"block_id": row["block_id"], "vi": row["en"]} for row in rows])
            return SimpleNamespace(invoke=invoke)

    result = localize_report(Translator(), compiled, [], fact_sources=facts)
    assert "Chuỗi FRED" in result.vi and 'đơn vị gốc "Percent"' in result.vi
    with pytest.raises(PublicationValidationError) as error:
        localize_report(Translator(), compiled, [])
    assert error.value.issues == ("macro_statement_source_unavailable",)


def test_macro_tool_paging_calculation_and_no_live_fallback():
    source = macro_source()
    seen = []

    class Model:
        def bind_tools(self, tools):
            self.tools = {tool.name for tool in tools}
            return self
        def invoke(self, prompt):
            seen.append(prompt)
            if len(seen) == 1:
                assert self.tools == {"get_snapshot_macro", "get_snapshot_macro_calculation"}
                assert "total_observations" in prompt[1].content and "observations" not in json.loads(prompt[1].content)[0]["data"]
                return AIMessage(content="", tool_calls=[
                    {"id": "p", "name": "get_snapshot_macro", "args": {"snapshot_id": source["snapshot_id"], "offset": 100}},
                    {"id": "c", "name": "get_snapshot_macro_calculation", "args": {"snapshot_id": source["snapshot_id"],
                        "operation": "difference", "left_period": "2026-10-02", "right_period": "2026-10-01"}}])
            assert json.loads(prompt[-2].content)["observations"][0]["value"] == 10
            assert json.loads(prompt[-1].content)["output_unit"] == "percentage points"
            return AIMessage(content="Synthetic macro review; headline coverage unavailable.")

    result = snapshot_analyst_nodes(Model(), {"news": json.dumps([source])})["news"](
        {"trade_date": NOW.date().isoformat(), "instrument_context": "AAPL"})
    assert "headline" in result["news_report"]
    warnings = publication_warning(macro_context(source))
    assert "MACRO COVERAGE" in warnings and "HEADLINE COVERAGE" in warnings


@pytest.mark.parametrize("module", ["tradingagents.platform.analysis.macro_facts",
    "tradingagents.platform.market_data.macro", "tradingagents.agents.utils.report_localization"])
def test_each_new_import_entrypoint_works_in_an_independent_interpreter(tmp_path, module):
    result = subprocess.run([sys.executable, "-c", f"import {module}"], cwd=tmp_path,
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, "Isolated import failed; no raw environment/output echoed"


@pytest.mark.parametrize("mode", ["negated", "unit_changed", "moved"])
def test_translation_cannot_change_or_qualify_a_macro_owned_statement(mode):
    source = macro_source()
    raw, facts = macro_draft(source)
    compiled = compile_report(raw, facts)
    diagnostics, attempts = [], []

    def bad_blocks(prompt):
        rows = json.loads(prompt.split("<translation_blocks>\n")[1].split("\n</translation_blocks>")[0])
        result = [{"block_id": row["block_id"], "vi": row["en"]} for row in rows]
        for row in result:
            if "⟦Q" in row["vi"]:
                row["vi"] = {"negated": "Không đúng: " + row["vi"],
                    "unit_changed": row["vi"].replace("⟧.", "⟧ triệu USD."),
                    "moved": "Nếu " + row["vi"]}[mode]
        return result

    class Model:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda prompt: attempts.append("structured")
                or schema(blocks=bad_blocks(prompt)))
        def invoke(self, prompt):
            attempts.append("repair")
            return AIMessage(content=json.dumps({"blocks": bad_blocks(prompt)}))

    assert localize_report(Model(), compiled, diagnostics, fact_sources=facts) is None
    assert attempts == ["structured", "repair"]
    assert all("translation_statement_requires_standalone_anchor" in row["checks"] for row in diagnostics)
