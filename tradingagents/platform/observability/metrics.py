"""Small in-process Prometheus registry with bounded label sets."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
JOB_STATUSES = {
    "queued",
    "running",
    "retry_wait",
    "cancel_requested",
    "succeeded",
    "failed",
    "cancelled",
}


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


class MetricsRegistry:
    def __init__(self):
        self._lock = Lock()
        self._http_requests: dict[tuple[str, str, str], int] = defaultdict(int)
        self._http_duration_count: dict[tuple[str, str], int] = defaultdict(int)
        self._http_duration_sum: dict[tuple[str, str], float] = defaultdict(float)
        self._job_transitions: dict[str, int] = defaultdict(int)
        self._sse_connections = 0

    def observe_http(self, *, method: str, route: str, status_code: int, duration: float) -> None:
        normalized_method = method.upper()
        if normalized_method not in HTTP_METHODS:
            normalized_method = "OTHER"
        key = (normalized_method, route, str(status_code))
        duration_key = (normalized_method, route)
        with self._lock:
            self._http_requests[key] += 1
            self._http_duration_count[duration_key] += 1
            self._http_duration_sum[duration_key] += max(duration, 0.0)

    def observe_job(self, status: str) -> None:
        normalized_status = status if status in JOB_STATUSES else "other"
        with self._lock:
            self._job_transitions[normalized_status] += 1

    def open_sse(self) -> None:
        with self._lock:
            self._sse_connections += 1

    def close_sse(self) -> None:
        with self._lock:
            self._sse_connections = max(0, self._sse_connections - 1)

    def render(self) -> str:
        with self._lock:
            http_requests = dict(self._http_requests)
            duration_count = dict(self._http_duration_count)
            duration_sum = dict(self._http_duration_sum)
            job_transitions = dict(self._job_transitions)
            sse_connections = self._sse_connections

        lines = [
            "# HELP tradingagents_http_requests_total HTTP requests by bounded route template.",
            "# TYPE tradingagents_http_requests_total counter",
        ]
        for (method, route, status_code), value in sorted(http_requests.items()):
            lines.append(
                "tradingagents_http_requests_total"
                f'{{method="{_label(method)}",route="{_label(route)}",status="{status_code}"}} {value}'
            )
        lines.extend(
            [
                "# HELP tradingagents_http_request_duration_seconds HTTP request duration.",
                "# TYPE tradingagents_http_request_duration_seconds summary",
            ]
        )
        for (method, route), value in sorted(duration_count.items()):
            labels = f'method="{_label(method)}",route="{_label(route)}"'
            lines.append(f"tradingagents_http_request_duration_seconds_count{{{labels}}} {value}")
            lines.append(
                "tradingagents_http_request_duration_seconds_sum"
                f"{{{labels}}} {duration_sum[(method, route)]:.9f}"
            )
        lines.extend(
            [
                "# HELP tradingagents_job_transitions_total Durable job transitions by status.",
                "# TYPE tradingagents_job_transitions_total counter",
            ]
        )
        for status, value in sorted(job_transitions.items()):
            lines.append(
                f'tradingagents_job_transitions_total{{status="{_label(status)}"}} {value}'
            )
        lines.extend(
            [
                "# HELP tradingagents_sse_connections_active Active authenticated SSE connections.",
                "# TYPE tradingagents_sse_connections_active gauge",
                f"tradingagents_sse_connections_active {sse_connections}",
            ]
        )
        return "\n".join(lines) + "\n"
