from datetime import datetime, timezone

from tradingagents._compat import UTC


def test_utc_alias_preserves_timezone_identity_and_serialization():
    assert UTC is timezone.utc
    assert datetime(2026, 9, 25, tzinfo=UTC).isoformat() == "2026-09-25T00:00:00+00:00"
