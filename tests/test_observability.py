"""Structured-log redaction and bounded-cardinality metric evidence."""

from __future__ import annotations

import json
import logging

import pytest

from tradingagents.platform.observability import JsonFormatter, MetricsRegistry, request_id_scope


@pytest.mark.unit
def test_json_logs_redact_secrets_private_data_and_url_credentials():
    record = logging.makeLogRecord(
        {
            "name": "tradingagents.platform.test",
            "levelno": logging.ERROR,
            "levelname": "ERROR",
            "msg": (
                "provider failed at postgresql://owner:database-password@db.example/test "
                "with Bearer bearer-token-value and sk-exampleapikey123456"
            ),
            "password": "plain-password",
            "authorization": "Bearer another-token",
            "portfolio_value": 12345,
            "nested": {"session_token": "ta_session_rawtoken", "safe": "visible"},
        }
    )
    with request_id_scope("request-123"):
        rendered = JsonFormatter().format(record)
    payload = json.loads(rendered)

    for forbidden in (
        "database-password",
        "bearer-token-value",
        "exampleapikey123456",
        "plain-password",
        "another-token",
        "ta_session_rawtoken",
        "12345",
    ):
        assert forbidden not in rendered
    assert payload["request_id"] == "request-123"
    assert payload["password"] == "<redacted>"
    assert payload["portfolio_value"] == "<redacted>"
    assert payload["nested"]["safe"] == "visible"


@pytest.mark.unit
def test_metrics_use_bounded_labels_and_render_prometheus_text():
    metrics = MetricsRegistry()
    metrics.observe_http(
        method="CUSTOM-UNBOUNDED",
        route="/api/v1/runs/{run_id}",
        status_code=200,
        duration=0.125,
    )
    metrics.observe_job("succeeded")
    metrics.observe_job("unbounded-custom-status")
    metrics.open_sse()
    metrics.close_sse()
    rendered = metrics.render()

    assert 'method="OTHER"' in rendered
    assert 'route="/api/v1/runs/{run_id}"' in rendered
    assert 'status="succeeded"' in rendered
    assert 'status="other"' in rendered
    assert "tradingagents_sse_connections_active 0" in rendered
