from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .envelope import ResponseEnvelope
from .health import CacheState

CacheKey = Literal["sleeper_players_nfl", "fantasycalc_values", "league_snapshot", "draft_state"]


class RefreshCacheInput(BaseModel):
    force: bool = False


class CacheRefreshResult(BaseModel):
    cache_key: CacheKey
    success: bool
    error: str | None = Field(None, max_length=500)


class RefreshCacheOutput(ResponseEnvelope):
    refreshed: list[CacheRefreshResult] = Field(default_factory=list)
    failures: list[CacheRefreshResult] = Field(default_factory=list)
    prior_status: dict[str, CacheState]
    post_status: dict[str, CacheState]
