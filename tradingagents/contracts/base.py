"""Strict, versioned primitives shared by platform domain contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"

ContentHash = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
NonEmptyText = Annotated[str, Field(min_length=1)]
Weight = Annotated[float, Field(ge=0.0, le=1.0)]


class StrictContract(BaseModel):
    """Immutable contract that rejects unknown fields."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class VersionedContract(StrictContract):
    """Root contract with an explicit wire-format version."""

    schema_version: Literal["1.0"] = SCHEMA_VERSION
