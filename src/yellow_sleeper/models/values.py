from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .envelope import ResponseEnvelope
from .shared import Candidate


class ValueSourceBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["fantasycalc", "xlsx", "config_pick_table"]
    value: float | None = None
    timestamp: datetime
    enabled: bool


class SourceDisagreement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_delta_pct: float
    sources: list[ValueSourceBreakdown] = Field(..., max_length=10)


class GetPlayerValueInput(BaseModel):
    player: str = Field(..., max_length=100)
    valuation_source: Literal["fantasycalc", "xlsx", "auto"] = "auto"


class GetPlayerValueOutput(ResponseEnvelope):
    sleeper_id: str | None = Field(None, max_length=20)
    name: str | None = Field(None, max_length=100)
    value: float | None = None
    value_sources: list[ValueSourceBreakdown] = Field(default_factory=list)
    source_disagreement: SourceDisagreement | None = None
    missing_values: list[str] = Field(default_factory=list, max_length=5)
    candidates: list[Candidate] = Field(default_factory=list, max_length=5)
