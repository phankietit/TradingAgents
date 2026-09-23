"""Versioned deterministic policy definitions and evaluation results."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, Field

from .base import NonEmptyText, StrictContract, VersionedContract
from .instruments import AssetClass


class PolicyResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


class PolicyContract(VersionedContract):
    policy_id: UUID
    owner_id: UUID
    name: NonEmptyText
    policy_version: NonEmptyText
    asset_class: AssetClass
    effective_at: AwareDatetime
    parameters: dict[str, Any] = Field(default_factory=dict)


class PolicyCheck(StrictContract):
    check_id: NonEmptyText
    policy_id: UUID
    policy_version: NonEmptyText
    result: PolicyResult
    blocking: bool
    reason: NonEmptyText
    observed_value: float | str | bool | None = None
    limit_value: float | str | bool | None = None
