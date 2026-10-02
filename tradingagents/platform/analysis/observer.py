"""Allowlisted graph progress and provider-reported token accounting.

Never persist prompts, chain inputs, credentials, model reasoning or raw errors.
"""

from threading import Lock
from time import monotonic

from langchain_core.callbacks import BaseCallbackHandler

STAGES = frozenset({"Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst",
                   "Bull Researcher", "Bear Researcher", "Research Manager", "Trader",
                   "Aggressive Analyst", "Conservative Analyst", "Neutral Analyst", "Portfolio Manager",
                   "Financial validation", "Report presentation"})


class ResearchBudgetExceeded(RuntimeError):
    """Stop rather than silently truncate the flow or repeatedly spend on it."""


class ResearchExecutionFailed(RuntimeError):
    """An entered analysis attempt must not be blindly rerun by the queue.

    A provider may have charged without returning usage. This is not a claim
    that cost was incurred, only that automatic full-run replay is unsafe.
    """


class ResearchObserver(BaseCallbackHandler):
    raise_error = True
    run_inline = True

    def __init__(self, *, check_cancelled, emit, clock=monotonic, max_seconds=1800, max_calls=128,
                 save_stage=None):
        self.check_cancelled = check_cancelled
        self.emit = emit
        # Separate private artifact publication; outputs never enter events/logs.
        self.save_stage = save_stage
        self.active = {}
        self.completed = []
        self.seen_model_runs = set()
        self.usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                      "model_calls": 0, "calls_with_usage": 0, "failed_calls": 0}
        self.lock = Lock()
        self.clock = clock
        self.started = clock()
        self.max_seconds = max_seconds
        self.max_calls = max_calls
        self.started_calls = 0

    def _check(self):
        self.remaining_seconds()

    def remaining_seconds(self):
        """Return the run's remaining allowance, never a per-read SDK timeout.

        Future request supervision must use this same monotonic clock. Merely
        passing this number to a transport's idle timeout is not a total deadline.
        Cancellation/lease loss takes precedence over the budget classification.
        """
        self.check_cancelled()
        remaining = self.max_seconds - (self.clock() - self.started)
        if remaining <= 0:
            raise ResearchBudgetExceeded("research wall-time budget exhausted")
        return remaining

    def on_chain_start(self, serialized, inputs, *, run_id, name=None, **kwargs):
        if name not in STAGES:
            return
        self._check()
        self.active[run_id] = name
        self.emit("stage.started", {"stage": name})

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        name = self.active.pop(run_id, None)
        if name:
            self.check_cancelled()
            artifact_id = self.save_stage(name, outputs) if self.save_stage is not None else None
            # Retain returned research before a boundary deadline stops the
            # graph. It remains unvalidated, not a completed run or decision.
            self._check()
            self.completed.append(name)
            self.emit("stage.completed", {"stage": name,
                **({"research_artifact_id": str(artifact_id)} if artifact_id is not None else {})})

    def on_chat_model_start(self, serialized, messages, **kwargs):
        # Check-and-reserve is atomic even if graph nodes invoke concurrently.
        # This counts logical LangChain starts, not hidden provider SDK retries.
        with self.lock:
            self._check()
            if self.started_calls >= self.max_calls:
                raise ResearchBudgetExceeded("research model-call budget exhausted")
            self.started_calls += 1

    def on_llm_end(self, response, *, run_id, **kwargs):
        with self.lock:
            if run_id in self.seen_model_runs:
                return
            self.seen_model_runs.add(run_id)
            self.usage["model_calls"] += 1
            message = response.generations[0][0].message if response.generations and response.generations[0] else None
            usage = getattr(message, "usage_metadata", None)
            if usage and all(isinstance(usage.get(key), int) and not isinstance(usage[key], bool)
                             and usage[key] >= 0 for key in ("input_tokens", "output_tokens", "total_tokens")):
                for key in ("input_tokens", "output_tokens", "total_tokens"):
                    self.usage[key] += usage[key]
                self.usage["calls_with_usage"] += 1
            receipt = self.receipt()["usage"]
        # Save the cumulative per-attempt receipt after every model completion,
        # not just successful publication. Failed attempts still consumed quota.
        self.emit("model.usage", {"usage": receipt})

    def on_llm_error(self, error, *, run_id, **kwargs):
        with self.lock:
            if run_id in self.seen_model_runs:
                return
            self.seen_model_runs.add(run_id)
            self.usage["model_calls"] += 1
            self.usage["failed_calls"] += 1
            receipt = self.receipt()["usage"]
        # Providers may charge failed calls without returning usage. No zero-cost claim.
        self.emit("model.usage", {"usage": receipt})

    def receipt(self):
        return {"completed_stages": list(self.completed),
                "execution_limits": {"wall_seconds": self.max_seconds, "model_calls": self.max_calls}, "usage": {
            **self.usage,
            "started_model_calls": self.started_calls,
            "model_call_scope": "logical_langchain_invocations",
            "provider_request_attempts": None,
            "status": "reported" if self.usage["model_calls"] and self.usage["model_calls"] == self.usage["calls_with_usage"] else "incomplete",
            "cost": None, "cost_status": "not_reported_by_provider"}}
