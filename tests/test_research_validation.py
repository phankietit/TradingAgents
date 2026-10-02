from types import SimpleNamespace
from uuid import uuid4

import pytest

from tradingagents.agents.research_schemas import LocalizedResearchReport, ObservedNumber
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.analysis.research_validation import (
    scope_issues,
    unsupported_financial_numbers,
    validate_numeric_claims,
)


def test_numeric_claims_require_snapshot_fact_identity_exact_units_and_honest_rounding():
    source = uuid4()
    catalog = {str(source): {"return.365_calendar_days.pct": -22.938588048}}
    valid = ObservedNumber(snapshot_id=source, fact_id="return.365_calendar_days.pct", value=-22.94, decimal_places=2)
    assert validate_numeric_claims([valid], catalog) == []
    for update in ({"value": -23.4}, {"snapshot_id": uuid4()}, {"fact_id": "invented"}, {"value": -.2294}, {"value": -22.94, "decimal_places": 0}):
        assert validate_numeric_claims([valid.model_copy(update=update)], catalog)
    assert not unsupported_financial_numbers("Return −22.94%", [valid])
    assert unsupported_financial_numbers("Return -23.40%", [valid])


def test_translation_must_preserve_numbers_and_currency_convention():
    LocalizedResearchReport(en="AAPL return -10.25%, price $100.50", vi="AAPL lợi suất -10.25%, giá $100.50")
    with pytest.raises(ValueError, match="numeric tokens"):
        LocalizedResearchReport(en="Return -10.25%", vi="Lợi suất -10.52%")


@pytest.mark.parametrize("text", ["Trim 10–20% of your position", "Buy a put spread", "Giảm tỷ trọng 20%"])
def test_known_scope_overreach_requires_review(text):
    assert scope_issues(text)


def test_provider_usage_is_reported_without_prompts_or_fabricated_cost():
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *_: None)
    run_id = uuid4()
    observer.on_chat_model_start({}, [], run_id=run_id)
    response = SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(
        usage_metadata={"input_tokens": 123, "output_tokens": 45, "total_tokens": 168}))]])
    observer.on_llm_end(response, run_id=run_id)
    observer.on_llm_end(response, run_id=run_id)
    usage = observer.receipt()["usage"]
    assert usage["total_tokens"] == 168 and usage["model_calls"] == 1
    assert usage["status"] == "reported" and usage["cost"] is None


def test_usage_events_survive_failed_attempt_without_provider_error_content():
    events = []
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda kind, payload: events.append((kind, payload)))
    run_id = uuid4()
    observer.on_llm_error(ValueError("sk-sensitive-provider-message"), run_id=run_id)
    observer.on_llm_error(ValueError("duplicate"), run_id=run_id)
    assert len(events) == 1 and events[0][0] == "model.usage"
    assert events[0][1]["usage"]["failed_calls"] == 1
    assert events[0][1]["usage"]["status"] == "incomplete"
    assert "sk-sensitive" not in str(events)
