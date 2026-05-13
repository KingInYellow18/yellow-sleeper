from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .shared import BlockingRule, PolicyFlag, SourceNote


class PolicyStatus(str, Enum):
    OK = "OK"
    BLOCKED = "BLOCKED"


class ResolutionStatus(str, Enum):
    OK = "OK"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class DataStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class ResponseEnvelope(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    policy_status: PolicyStatus
    resolution_status: ResolutionStatus
    data_status: DataStatus
    blocking_rules: list[BlockingRule] = Field(default_factory=list)
    policy_flags: list[PolicyFlag] = Field(default_factory=list, max_length=25)
    source_notes: list[SourceNote] = Field(default_factory=list, max_length=25)
    config_sources: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_blocking_consistency(self) -> ResponseEnvelope:
        if self.policy_status == PolicyStatus.BLOCKED and not self.blocking_rules:
            raise ValueError("policy_status=BLOCKED requires non-empty blocking_rules")
        if self.policy_status == PolicyStatus.OK and self.blocking_rules:
            raise ValueError("policy_status=OK requires empty blocking_rules")
        return self

    @model_validator(mode="after")
    def _validate_stale_explanation(self) -> ResponseEnvelope:
        for note in self.source_notes:
            if note.stale and not note.explanation:
                raise ValueError(
                    f"source_note for field={note.field} is stale; explanation is required"
                )
            if note.cache_status == "stale" and not note.stale:
                raise ValueError(
                    f"source_note for field={note.field}: cache_status=stale must set stale=True"
                )
        return self


class TransportError(BaseModel):
    ok: Literal[False] = False
    error_type: Literal["validation_error", "transport_error", "internal_error"]
    message: str = Field(..., max_length=500)
    retry_hint: str | None = Field(None, max_length=500)
