"""Single-owner password and opaque-session authentication evidence."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from tradingagents.platform.auth import (
    BootstrapClosed,
    InvalidCredentials,
    OwnerAuth,
)
from tradingagents.platform.persistence import Database, downgrade_database, upgrade_database
from tradingagents.platform.persistence.models import OwnerRow, OwnerSessionRow

NOW = datetime(2026, 9, 23, 11, 0, tzinfo=UTC)
PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "another strong owner password"


def _database(tmp_path) -> Database:
    url = f"sqlite:///{tmp_path / 'auth.db'}"
    upgrade_database(url)
    return Database(url)


def _bootstrap(database: Database):
    with database.session() as session:
        return OwnerAuth(session).bootstrap_owner(
            " Owner@Example.COM ", PASSWORD, owner_id=uuid4(), now=NOW
        )


@pytest.mark.unit
def test_bootstrap_creates_one_normalized_owner_without_plaintext_password(tmp_path):
    database = _database(tmp_path)
    principal = _bootstrap(database)
    assert principal.email == "owner@example.com"

    with database.session() as session:
        row = session.get(OwnerRow, principal.owner_id)
        assert row.password_hash.startswith("scrypt$")
        assert PASSWORD not in row.password_hash
        assert row.singleton_key == "primary-owner"
        with pytest.raises(BootstrapClosed):
            OwnerAuth(session).bootstrap_owner("second@example.com", PASSWORD, now=NOW)
    database.dispose()


@pytest.mark.unit
def test_password_policy_and_invalid_email_fail_before_account_creation(tmp_path):
    database = _database(tmp_path)
    with pytest.raises(ValueError, match="email"), database.session() as session:
        OwnerAuth(session).bootstrap_owner("not-an-email", PASSWORD, now=NOW)
    with pytest.raises(ValueError, match="password"), database.session() as session:
        OwnerAuth(session).bootstrap_owner("owner@example.com", "too-short", now=NOW)

    with database.session() as session:
        assert session.scalar(select(OwnerRow)) is None
    database.dispose()


@pytest.mark.unit
def test_login_returns_redacted_token_once_and_database_stores_only_hash(tmp_path):
    database = _database(tmp_path)
    principal = _bootstrap(database)
    with database.session() as session:
        issued = OwnerAuth(session).login("OWNER@example.com", PASSWORD, now=NOW)

    assert issued.principal == principal
    assert issued.token.startswith("ta_session_")
    assert issued.token not in repr(issued)
    assert "<redacted>" in repr(issued)
    with database.session() as session:
        stored = session.scalar(select(OwnerSessionRow))
        assert stored.token_hash != issued.token
        assert issued.token not in stored.token_hash
        assert len(stored.token_hash) == 64
    database.dispose()


@pytest.mark.unit
def test_wrong_and_unknown_credentials_share_generic_failure(tmp_path):
    database = _database(tmp_path)
    _bootstrap(database)
    failures = []
    for email, password in (
        ("owner@example.com", "wrong password value"),
        ("missing@example.com", "wrong password value"),
        ("invalid", "wrong password value"),
    ):
        with pytest.raises(InvalidCredentials) as captured, database.session() as session:
            OwnerAuth(session).login(email, password, now=NOW)
        failures.append(str(captured.value))
    assert failures == ["invalid credentials"] * 3
    database.dispose()


@pytest.mark.unit
def test_session_authentication_is_expiring_and_revocable(tmp_path):
    database = _database(tmp_path)
    principal = _bootstrap(database)
    with database.session() as session:
        issued = OwnerAuth(session, session_ttl=timedelta(hours=1)).login(
            principal.email, PASSWORD, now=NOW
        )

    with database.session() as session:
        authenticated = OwnerAuth(session).authenticate_session(
            issued.token, now=NOW + timedelta(minutes=59)
        )
    assert authenticated == principal

    with pytest.raises(InvalidCredentials), database.session() as session:
        OwnerAuth(session).authenticate_session(issued.token, now=NOW + timedelta(hours=1))

    with database.session() as session:
        assert OwnerAuth(session).revoke_session(issued.token, now=NOW + timedelta(minutes=30))
    with pytest.raises(InvalidCredentials), database.session() as session:
        OwnerAuth(session).authenticate_session(issued.token, now=NOW + timedelta(minutes=31))
    database.dispose()


@pytest.mark.unit
def test_password_change_revokes_sessions_and_rotates_verifier(tmp_path):
    database = _database(tmp_path)
    principal = _bootstrap(database)
    with database.session() as session:
        issued = OwnerAuth(session).login(principal.email, PASSWORD, now=NOW)
    with database.session() as session:
        OwnerAuth(session).change_password(
            principal.owner_id,
            PASSWORD,
            NEW_PASSWORD,
            now=NOW + timedelta(minutes=1),
        )

    with pytest.raises(InvalidCredentials), database.session() as session:
        OwnerAuth(session).authenticate_session(issued.token, now=NOW + timedelta(minutes=2))
    with pytest.raises(InvalidCredentials), database.session() as session:
        OwnerAuth(session).login(principal.email, PASSWORD, now=NOW + timedelta(minutes=2))
    with database.session() as session:
        replacement = OwnerAuth(session).login(
            principal.email, NEW_PASSWORD, now=NOW + timedelta(minutes=2)
        )
    assert replacement.principal == principal
    database.dispose()


@pytest.mark.unit
def test_disabling_owner_revokes_sessions_and_blocks_new_login(tmp_path):
    database = _database(tmp_path)
    principal = _bootstrap(database)
    with database.session() as session:
        issued = OwnerAuth(session).login(principal.email, PASSWORD, now=NOW)
    with database.session() as session:
        OwnerAuth(session).disable_owner(principal.owner_id, now=NOW + timedelta(minutes=1))

    with pytest.raises(InvalidCredentials), database.session() as session:
        OwnerAuth(session).authenticate_session(issued.token, now=NOW + timedelta(minutes=2))
    with pytest.raises(InvalidCredentials), database.session() as session:
        OwnerAuth(session).login(principal.email, PASSWORD, now=NOW + timedelta(minutes=2))
    database.dispose()


@pytest.mark.integration
def test_postgresql_concurrent_bootstrap_creates_exactly_one_owner():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")

    database = Database(url)
    try:
        upgrade_database(url)

        def bootstrap(index: int):
            try:
                with database.session() as session:
                    return OwnerAuth(session).bootstrap_owner(
                        f"owner{index}@example.com", f"concurrent owner password {index}", now=NOW
                    )
            except BootstrapClosed:
                return None

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(bootstrap, range(2)))
        assert len([result for result in results if result is not None]) == 1
        with database.session() as session:
            assert session.scalar(select(OwnerRow.singleton_key)) == "primary-owner"
            assert len(session.scalars(select(OwnerRow)).all()) == 1
    finally:
        downgrade_database(url)
        database.dispose()
