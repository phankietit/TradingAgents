"""Allowlisted graph progress and provider-reported token accounting.

Never persist prompts, chain inputs, credentials, model reasoning or raw errors.
"""

from threading import Lock
from time import monotonic

from langchain_core.callbacks import BaseCallbackHandler

STAGES = frozenset({"Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst",
                   "Bull Researcher", "Bear Researcher", "Research Manager", "Trader",
                   "Aggressive Analyst", "Conservative Analyst", "Neutral Analyst", "Portfolio Manager", "Report presentation"})


class ResearchBudgetExceeded(RuntimeError):
    """Stop rather than silently truncate the flow or repeatedly spend on it."""


class ResearchObserver(BaseCallbackHandler):
    raise_error = True
    run_inline = True

    def __init__(self, *, check_cancelled, emit, clock=monotonic, max_seconds=1800, max_calls=128):
        self.check_cancelled = check_cancelled
        self.emit = emit
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
        self.check_cancelled()
        if self.clock() - self.started >= self.max_seconds:
            raise ResearchBudgetExceeded("research wall-time budget exhausted")

    def on_chain_start(self, serialized, inputs, *, run_id, name=None, **kwargs):
        if name not in STAGES:
            return
        self._check()
        self.active[run_id] = name
        self.emit("stage.started", {"stage": name})

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        name = self.active.pop(run_id, None)
        if name:
            self._check()
            self.completed.append(name)
            self.emit("stage.completed", {"stage": name})

    def on_chat_model_start(self, serialized, messages, **kwargs):
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
            "status": "reported" if self.usage["model_calls"] and self.usage["model_calls"] == self.usage["calls_with_usage"] else "incomplete",
            "cost": None, "cost_status": "not_reported_by_provider"}}
