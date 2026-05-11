from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class FlagSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"


class FlagType(str, Enum):
    PROTECTED_PLAYER = "protected_player"
    PROTECTED_PICK_PATTERN = "protected_pick_pattern"
    MISSING_VALUE = "missing_value"
    SOURCE_DISAGREEMENT = "source_disagreement"
    STALE_DATA = "stale_data"
    AMBIGUOUS_RESOLUTION = "ambiguous_resolution"
    CONDITIONAL_OR_SWAP_TRADE = "conditional_or_swap_trade"


class SourceNote(BaseModel):
    field: str = Field(..., max_length=100)
    source: Literal["sleeper", "fantasycalc", "xlsx", "local_config", "computed"]
    timestamp: datetime
    cache_status: Literal["fresh", "cached", "stale"]
    stale: bool = False
    explanation: str | None = Field(None, max_length=500)


class PolicyFlag(BaseModel):
    type: FlagType
    asset: str | None = Field(None, max_length=100)
    rule_source: Literal[".yellow-sleeper.yaml", "tool_argument", "computed"]
    severity: FlagSeverity
    reason: str = Field(..., max_length=500)


class BlockingRule(BaseModel):
    rule: Literal["hard_untouchable"]
    asset: str = Field(..., max_length=100)
    matched_against: str = Field(..., max_length=100)
    match_confidence: int = Field(..., ge=0, le=100)
    rule_source: Literal[".yellow-sleeper.yaml", "tool_argument"]


class Candidate(BaseModel):
    sleeper_id: str | None = Field(None, max_length=20)
    pick_token: str | None = Field(None, max_length=30)
    name: str = Field(..., max_length=100)
    position: str | None = Field(None, max_length=10)
    team: str | None = Field(None, max_length=10)
    match_confidence: int = Field(..., ge=0, le=100)


class AssetResolution(BaseModel):
    input: str = Field(..., max_length=200)
    asset_type: Literal["player", "pick"]
    resolved_id: str | None = Field(None, max_length=30)
    match_confidence: int = Field(..., ge=0, le=100)
    candidates: list[Candidate] = Field(default_factory=list, max_length=5)
    manual_review: bool = False
