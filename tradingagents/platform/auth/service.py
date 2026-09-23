"""Single-owner password authentication with hashed opaque sessions."""

from __future__ import annotations

import base64
import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tradingagents.platform.persistence.models import OwnerRow, OwnerSessionRow

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_PREFIX = "ta_session_"
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 1024
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_LENGTH = 32
SCRYPT_MAX_MEMORY = 64 * 1024 * 1024


class OwnerStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class BootstrapClosed(RuntimeError):
    """The one-time owner bootstrap has already completed."""


class InvalidCredentials(ValueError):
    """Credentials or session state did not authenticate an active owner."""


@dataclass(frozen=True, slots=True)
class OwnerPrincipal:
    owner_id: UUID
    email: str


@dataclass(frozen=True, slots=True, repr=False)
class IssuedSession:
    token: str
    principal: OwnerPrincipal
    expires_at: datetime

    def __repr__(self) -> str:
        return (
            "IssuedSession(token=<redacted>, "
            f"principal={self.principal!r}, expires_at={self.expires_at!r})"
        )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_email(value: str) -> str:
    normalized = value.strip().casefold()
    if len(normalized) > 254 or not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("email is invalid")
    return normalized


def _validate_password(password: str) -> None:
    if (
        not isinstance(password, str)
        or not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH
    ):
        raise ValueError(
            f"password must contain {PASSWORD_MIN_LENGTH} to {PASSWORD_MAX_LENGTH} characters"
        )


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_LENGTH,
        maxmem=SCRYPT_MAX_MEMORY,
    )


def _hash_password(password: str) -> str:
    _validate_password(password)
    salt = secrets.token_bytes(16)
    digest = _derive(password, salt)
    return f"scrypt$n={SCRYPT_N},r={SCRYPT_R},p={SCRYPT_P}${_encode(salt)}${_encode(digest)}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, parameters, salt_value, digest_value = encoded.split("$", 3)
        parsed = dict(part.split("=", 1) for part in parameters.split(","))
        if algorithm != "scrypt" or parsed != {
            "n": str(SCRYPT_N),
            "r": str(SCRYPT_R),
            "p": str(SCRYPT_P),
        }:
            return False
        actual = _derive(password, _decode(salt_value))
        expected = _decode(digest_value)
        return secrets.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


_DUMMY_PASSWORD_HASH = _hash_password("invalid-credential-probe")


class OwnerAuth:
    def __init__(self, session: Session, *, session_ttl: timedelta = timedelta(hours=12)):
        if not timedelta(minutes=5) <= session_ttl <= timedelta(days=30):
            raise ValueError("session_ttl must be between 5 minutes and 30 days")
        self.session = session
        self.session_ttl = session_ttl

    def bootstrap_owner(
        self,
        email: str,
        password: str,
        *,
        owner_id: UUID | None = None,
        now: datetime | None = None,
    ) -> OwnerPrincipal:
        timestamp = _utc(now or datetime.now(UTC))
        canonical_email = _normalize_email(email)
        password_hash = _hash_password(password)
        owner_count = self.session.scalar(select(func.count()).select_from(OwnerRow))
        if owner_count:
            raise BootstrapClosed("owner bootstrap is already closed")
        row = OwnerRow(
            owner_id=owner_id or uuid4(),
            singleton_key="primary-owner",
            email=canonical_email,
            password_hash=password_hash,
            status=OwnerStatus.ACTIVE.value,
            created_at=timestamp,
            updated_at=timestamp,
        )
        try:
            with self.session.begin_nested():
                self.session.add(row)
                self.session.flush()
        except IntegrityError as error:
            raise BootstrapClosed("owner bootstrap is already closed") from error
        return OwnerPrincipal(row.owner_id, row.email)

    def login(self, email: str, password: str, *, now: datetime | None = None) -> IssuedSession:
        timestamp = _utc(now or datetime.now(UTC))
        try:
            canonical_email = _normalize_email(email)
        except ValueError:
            canonical_email = "invalid@example.invalid"
        row = self.session.scalar(select(OwnerRow).where(OwnerRow.email == canonical_email))
        encoded = row.password_hash if row else _DUMMY_PASSWORD_HASH
        valid_shape = isinstance(password, str) and len(password) <= PASSWORD_MAX_LENGTH
        password_probe = password if valid_shape else "invalid-credential-probe"
        password_matches = _verify_password(password_probe, encoded)
        valid_password = valid_shape and password_matches
        if row is None or not valid_password or OwnerStatus(row.status) is not OwnerStatus.ACTIVE:
            raise InvalidCredentials("invalid credentials")

        token = SESSION_PREFIX + secrets.token_urlsafe(32)
        expires_at = timestamp + self.session_ttl
        self.session.add(
            OwnerSessionRow(
                session_id=uuid4(),
                owner_id=row.owner_id,
                token_hash=_token_hash(token),
                issued_at=timestamp,
                expires_at=expires_at,
                last_seen_at=timestamp,
                revoked_at=None,
            )
        )
        self.session.flush()
        return IssuedSession(token, OwnerPrincipal(row.owner_id, row.email), expires_at)

    def authenticate_session(self, token: str, *, now: datetime | None = None) -> OwnerPrincipal:
        timestamp = _utc(now or datetime.now(UTC))
        if not isinstance(token, str) or not token.startswith(SESSION_PREFIX) or len(token) > 128:
            raise InvalidCredentials("invalid session")
        session_row = self.session.scalar(
            select(OwnerSessionRow).where(OwnerSessionRow.token_hash == _token_hash(token))
        )
        if (
            session_row is None
            or session_row.revoked_at is not None
            or _utc(session_row.expires_at) <= timestamp
        ):
            raise InvalidCredentials("invalid session")
        owner = self.session.get(OwnerRow, session_row.owner_id)
        if owner is None or OwnerStatus(owner.status) is not OwnerStatus.ACTIVE:
            raise InvalidCredentials("invalid session")
        session_row.last_seen_at = timestamp
        self.session.flush()
        return OwnerPrincipal(owner.owner_id, owner.email)

    def revoke_session(self, token: str, *, now: datetime | None = None) -> bool:
        if not isinstance(token, str) or not token.startswith(SESSION_PREFIX) or len(token) > 128:
            return False
        row = self.session.scalar(
            select(OwnerSessionRow)
            .where(OwnerSessionRow.token_hash == _token_hash(token))
            .with_for_update()
        )
        if row is None:
            return False
        if row.revoked_at is None:
            row.revoked_at = _utc(now or datetime.now(UTC))
            self.session.flush()
        return True

    def change_password(
        self,
        owner_id: UUID,
        current_password: str,
        new_password: str,
        *,
        now: datetime | None = None,
    ) -> None:
        timestamp = _utc(now or datetime.now(UTC))
        owner = self.session.scalar(
            select(OwnerRow).where(OwnerRow.owner_id == owner_id).with_for_update()
        )
        if owner is None or not _verify_password(current_password, owner.password_hash):
            raise InvalidCredentials("invalid credentials")
        owner.password_hash = _hash_password(new_password)
        owner.updated_at = timestamp
        self._revoke_owner_sessions(owner_id, timestamp)
        self.session.flush()

    def disable_owner(self, owner_id: UUID, *, now: datetime | None = None) -> None:
        timestamp = _utc(now or datetime.now(UTC))
        owner = self.session.scalar(
            select(OwnerRow).where(OwnerRow.owner_id == owner_id).with_for_update()
        )
        if owner is None:
            raise InvalidCredentials("owner not found")
        owner.status = OwnerStatus.DISABLED.value
        owner.updated_at = timestamp
        self._revoke_owner_sessions(owner_id, timestamp)
        self.session.flush()

    def _revoke_owner_sessions(self, owner_id: UUID, timestamp: datetime) -> None:
        self.session.execute(
            update(OwnerSessionRow)
            .where(OwnerSessionRow.owner_id == owner_id, OwnerSessionRow.revoked_at.is_(None))
            .values(revoked_at=timestamp)
        )
