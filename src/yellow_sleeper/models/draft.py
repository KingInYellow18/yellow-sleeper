from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

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
    round: int = Field(..., ge=1)
    slot: int = Field(..., ge=1)
    sleeper_id: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    position: str = Field(..., max_length=10)
    drafted_by_owner: str = Field(..., max_length=100)


class WhatsOnTheClockOutput(ResponseEnvelope):
    draft_status: Literal["drafting", "not_started", "complete"]
    pick_context: PickContext | None = None
    recent_picks: list[RecentPick] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def _validate_pick_context_presence(self) -> WhatsOnTheClockOutput:
        if self.draft_status == "drafting" and self.pick_context is None:
            raise ValueError("draft_status=drafting requires pick_context to be set")
        if self.draft_status != "drafting" and self.pick_context is not None:
            raise ValueError(
                f"pick_context must be None when draft_status={self.draft_status!r}"
            )
        return self
