from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .envelope import ResponseEnvelope


class WhatsOnTheClockInput(BaseModel):
    draft_id: str | None = Field(None, max_length=20)
    pool: Literal["rookies_only", "all"] = "rookies_only"


class PickContext(BaseModel):
    round: int = Field(..., ge=1)
    slot: int = Field(..., ge=1)
    on_the_clock_owner: str = Field(..., max_length=100)
    on_the_clock_team: str = Field(..., max_length=100)


class RecentPick(BaseModel):
    round: int
    slot: int
    sleeper_id: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    position: str = Field(..., max_length=10)
    drafted_by_owner: str = Field(..., max_length=100)


class WhatsOnTheClockOutput(ResponseEnvelope):
    draft_status: Literal["drafting", "not_started", "complete"]
    pick_context: PickContext | None = None
    recent_picks: list[RecentPick] = Field(default_factory=list, max_length=10)
