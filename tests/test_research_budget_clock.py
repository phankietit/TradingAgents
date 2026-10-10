"""Local budget accounting is not transport/provider total-deadline proof."""

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tradingagents.platform.analysis.observer import ResearchBudgetExceeded, ResearchObserver


def test_remaining_allowance_uses_original_monotonic_start_without_reset():
    clock = [100.0]
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *_: None,
                                clock=lambda: clock[0], max_seconds=60)
    assert observer.remaining_seconds() == 60
    clock[0] = 159.5
    assert observer.remaining_seconds() == 0.5
    clock[0] = 160
    with pytest.raises(ResearchBudgetExceeded):
        observer.remaining_seconds()
    with pytest.raises(ResearchBudgetExceeded):
        observer.on_chat_model_start({}, [])
    assert observer.started_calls == 0


def test_cancellation_precedes_deadline_and_never_reserves_a_call():
    cancelled = [False]

    def check():
        if cancelled[0]:
            raise RuntimeError("cancelled")

    observer = ResearchObserver(check_cancelled=check, emit=lambda *_: None, max_seconds=0)
    cancelled[0] = True
    with pytest.raises(RuntimeError, match="cancelled"):
        observer.on_chat_model_start({}, [])
    assert observer.started_calls == 0


def test_parallel_model_starts_cannot_exceed_the_shared_logical_call_cap():
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *_: None,
                                clock=lambda: 0, max_calls=7)

    def start(_):
        try:
            observer.on_chat_model_start({}, [])
            return True
        except ResearchBudgetExceeded:
            return False

    with ThreadPoolExecutor(max_workers=16) as pool:
        accepted = list(pool.map(start, range(100)))
    assert sum(accepted) == observer.started_calls == 7


def test_returned_usage_after_deadline_is_kept_without_claiming_provider_attempts():
    clock = [0]
    events = []
    observer = ResearchObserver(check_cancelled=lambda: None,
        emit=lambda *args: events.append(args), clock=lambda: clock[0], max_seconds=1)
    observer.on_chat_model_start({}, [])
    clock[0] = 2
    response = SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(
        usage_metadata={"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}))]])
    observer.on_llm_end(response, run_id=uuid4())
    usage = observer.receipt()["usage"]
    assert usage["total_tokens"] == 5
    assert usage["started_model_calls"] == usage["model_calls"] == 1
    assert usage["model_call_scope"] == "logical_langchain_invocations"
    assert usage["provider_request_attempts"] is None and usage["cost"] is None
    assert events[0][0] == "model.usage"
    with pytest.raises(ResearchBudgetExceeded):
        observer.on_chat_model_start({}, [])
