from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .envelope import ResponseEnvelope

CacheState = Literal["fresh", "cached", "stale", "missing"]


class HealthCheckInput(BaseModel):
    force_probe: bool = False


class LiveProbeResult(BaseModel):
    source: Literal["sleeper", "fantasycalc"]
    reachable: bool
    latency_ms: int | None = Field(None, ge=0)
    error: str | None = Field(None, max_length=500)
    probed_at: datetime


class HealthCheckOutput(ResponseEnvelope):
    status_msgs: list[str] = Field(default_factory=list, max_length=10)
    cache_status: dict[str, CacheState]
    league_id: str = Field(..., max_length=20)
    user: str = Field(..., max_length=100)
    errors: list[str] = Field(default_factory=list, max_length=10)
    live_probe_results: list[LiveProbeResult] | None = None
