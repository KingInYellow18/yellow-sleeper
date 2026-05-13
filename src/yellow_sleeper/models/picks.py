from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .envelope import ResponseEnvelope

# Season year bounds — mirror Pick.season constraint. Used by every model that
# accepts or emits a season year so out-of-range input fails at the contract
# boundary instead of producing nonsensical pipeline output.
SeasonYear = Annotated[int, Field(ge=2020, le=2099)]

_PICK_TOKEN_PATTERN = r"^pick_\d{4}_r\d+_orig\d+$"


class ListTradedPicksInput(BaseModel):
    seasons: list[SeasonYear] | None = Field(None, max_length=3)


class TradedPick(BaseModel):
    pick_token: str = Field(..., max_length=30, pattern=_PICK_TOKEN_PATTERN)
    display_name: str = Field(..., max_length=100)
    season: SeasonYear
    round: int = Field(..., ge=1, le=10)
    original_owner_roster_id: int
    previous_owner_roster_id: int | None = None
    current_owner_roster_id: int
    original_owner_name: str = Field(..., max_length=100)
    current_owner_name: str = Field(..., max_length=100)


class ListTradedPicksOutput(ResponseEnvelope):
    picks: list[TradedPick] = Field(..., max_length=25)


class ListMyPicksInput(BaseModel):
    seasons: list[SeasonYear] | None = Field(None, max_length=3)
    include_traded_away: bool = False


class Pick(BaseModel):
    pick_token: str = Field(..., max_length=30, pattern=_PICK_TOKEN_PATTERN)
    display_name: str = Field(..., max_length=100)
    season: SeasonYear
    round: int = Field(..., ge=1, le=10)
    original_owner_roster_id: int
    original_owner_name: str = Field(..., max_length=100)
    current_owner_roster_id: int
    origin: Literal["native", "traded_in", "traded_away"]


class ListMyPicksOutput(ResponseEnvelope):
    owned_picks: list[Pick] = Field(default_factory=list, max_length=25)
    traded_away_picks: list[Pick] = Field(default_factory=list, max_length=25)
    unresolved: list[str] = Field(default_factory=list, max_length=10)
