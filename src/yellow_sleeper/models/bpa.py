from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .envelope import ResponseEnvelope


class BestPlayerAvailableInput(BaseModel):
    draft_id: str | None = Field(None, max_length=20)
    position: Literal["QB", "RB", "WR", "TE"] | None = None
    limit: int = Field(10, ge=1, le=25)
    rookie_board_source: Literal["local", "fantasycalc", "xlsx"] = "fantasycalc"


class BPACandidate(BaseModel):
    sleeper_id: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    position: Literal["QB", "RB", "WR", "TE"]
    value: float | None = None
    rookie_status: bool
    prior_drafted: bool
    inclusion_reasons: list[str] = Field(..., max_length=5)


class BestPlayerAvailableOutput(ResponseEnvelope):
    candidates: list[BPACandidate] = Field(..., max_length=25)
    excluded_count: int = Field(..., ge=0)
    board_source: Literal["local", "fantasycalc", "xlsx"]
