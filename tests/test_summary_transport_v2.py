"""V2 reader/checkpoint transport; not generator activation or translation QA."""

import copy
import json

import pytest

from tests.test_snapshot_checkpoint_codec import checkpoint
from tests.test_summary_provenance_v2 import _draft
from tradingagents.agents.research_schemas import (
    LocalizedResearchReport,
    SnapshotReportDraftV2,
    read_canonical_snapshot_report,
    read_snapshot_report,
)
from tradingagents.agents.utils.report_compiler import compile_report_v2
from tradingagents.agents.utils.report_localization import create_report_presentation, reader_report
from tradingagents.platform.analysis.checkpoint_codec import (
    CheckpointCodecError,
    SnapshotCheckpointCodec,
)
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts


def _report():
    raw, data = _draft()
    return compile_report_v2(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)}).model_dump(mode="json")


def test_saved_v2_reader_preserves_locales_and_exact_summary_sources():
    raw = _report()
    raw["localized_report"] = {"en": "The price is $499.00.", "vi": "Giá là $499.00."}
    before = copy.deepcopy(raw)
    parsed = read_snapshot_report(raw)
    assert parsed.model_dump(mode="json") == before
    assert raw == before
    assert raw["summary_evidence"]["snapshot_ids"][0] not in reader_report(parsed)
    with pytest.raises(ValueError):
        read_canonical_snapshot_report(raw)  # Presentation cannot become review input.


@pytest.mark.parametrize("language", ["English", "English and Vietnamese"])
def test_presentation_preserves_canonical_v2_metadata_without_regeneration(monkeypatch, language):
    from tradingagents.agents.utils import report_localization
    from tradingagents.dataflows import config

    raw = _report()
    before = copy.deepcopy(raw)
    calls = []
    monkeypatch.setattr(config, "get_config", lambda: {"output_language": language})

    def translate(llm, canonical, diagnostics, **kwargs):
        # Stub only isolates transport. Existing translation tests verify the
        # actual bounded translator; this fixture is not language-quality proof.
        calls.append(canonical.model_dump(mode="json"))
        return LocalizedResearchReport(en="The price is $499.00.", vi="Giá là $499.00.")

    monkeypatch.setattr(report_localization, "localize_report", translate)
    result = create_report_presentation(object())({"structured_decision": raw})
    rendered = result["structured_decision"]
    assert read_snapshot_report(rendered).model_dump(mode="json") == rendered
    assert {key: value for key, value in rendered.items() if key != "localized_report"} == {
        key: value for key, value in before.items() if key != "localized_report"}
    assert raw == before
    assert len(calls) == (language != "English")


@pytest.mark.parametrize("channel", ["structured_draft", "structured_decision", "rejected_structured_decision"])
def test_checkpoint_roundtrip_preserves_v2_sources_in_state_and_pending_writes(channel):
    # Native generation stores model_dump, including schema defaults. Keep the
    # exact transport assertion against that actual representation, not an
    # intentionally sparse constructor fixture.
    raw = SnapshotReportDraftV2.model_validate(_draft()[0]).model_dump(mode="json") if channel == "structured_draft" else _report()
    if channel == "structured_decision":
        raw["localized_report"] = {"en": "The price is $499.00.", "vi": "Giá là $499.00."}
    native = checkpoint()
    native.checkpoint["channel_values"][channel] = copy.deepcopy(raw)
    native.checkpoint["channel_versions"][channel] = 1
    native.pending_writes[0][2][channel] = copy.deepcopy(raw)
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    encoded = codec.encode(native)
    restored = codec.decode(encoded)
    assert restored.checkpoint["channel_values"][channel] == raw
    assert restored.pending_writes[0][2][channel] == raw
    assert native.checkpoint["channel_values"][channel] == raw
    assert codec.encode(restored) == encoded


@pytest.mark.parametrize("mutation", ["version", "missing_sources", "duplicate", "text"])
def test_checkpoint_rejects_invalid_v2_without_legacy_downgrade(mutation):
    native = checkpoint()
    raw = _report()
    native.checkpoint["channel_values"]["structured_decision"] = raw
    native.checkpoint["channel_versions"]["structured_decision"] = 1
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    envelope = json.loads(codec.encode(native))
    value = envelope["checkpoint"]["channel_values"]["structured_decision"]
    if mutation == "version":
        value["report_contract_version"] = "3.0"
    elif mutation == "missing_sources":
        value.pop("summary_evidence")
    elif mutation == "duplicate":
        value["summary_evidence"]["snapshot_ids"] *= 2
    else:
        value["summary_evidence"]["claim"] = "PRIVATE_UNRELATED_TEXT"
    with pytest.raises(CheckpointCodecError) as failure:
        codec.decode(json.dumps(envelope).encode())
    assert "PRIVATE_UNRELATED_TEXT" not in str(failure.value)
