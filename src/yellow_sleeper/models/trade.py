from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .envelope import DataStatus, PolicyStatus, ResponseEnvelope
from .shared import AssetResolution
from .values import SourceDisagreement, ValueSourceBreakdown


class PerAssetValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset: str | None = Field(None, max_length=200)
    side: Literal["send", "receive"]
    value: float | None = None
    sources: list[ValueSourceBreakdown] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def _validate_value_requires_asset(self) -> PerAssetValue:
        if self.value is not None and self.asset is None:
            raise ValueError("asset must not be None when value is set")
        return self

    @model_validator(mode="after")
    def _validate_value_matches_single_source(self) -> PerAssetValue:
        # When exactly one enabled source carries a value, PerAssetValue.value
        # must reflect that source (within float tolerance). Pipelines today
        # always populate sources with a single ValueSourceBreakdown per asset;
        # this codifies that contract. Multi-source aggregation is intentionally
        # out of scope — when sources != 1 enabled-with-value, skip the check.
        if self.value is None:
            return self
        enabled = [
            s.value for s in self.sources if s.enabled and s.value is not None
        ]
        if len(enabled) == 1 and abs(enabled[0] - self.value) >= 0.01:
            raise ValueError(
                f"value={self.value} disagrees with sole enabled source "
                f"value={enabled[0]}"
            )
        return self


class ValueMath(BaseModel):
    send_total: float | None = None
    receive_total: float | None = None
    delta: float | None = None
    delta_pct: float | None = None
    per_asset: list[PerAssetValue] = Field(default_factory=list)
    source_disagreement: SourceDisagreement | None = None


class PositionDepthChange(BaseModel):
    position: Literal["QB", "RB", "WR", "TE"]
    pre: int = Field(..., ge=0)
    post: int = Field(..., ge=0)
    delta: int

    @model_validator(mode="after")
    def _validate_delta(self) -> PositionDepthChange:
        expected = self.post - self.pre
        if self.delta != expected:
            raise ValueError(
                f"delta={self.delta} inconsistent with post-pre={expected} "
                f"(pre={self.pre}, post={self.post})"
            )
        return self


class AgeStats(BaseModel):
    pre_avg: float
    pre_median: float
    post_avg: float
    post_median: float
    by_position: dict[str, dict[str, float]] = Field(default_factory=dict)


class PickInventorySummary(BaseModel):
    pre: dict[str, int]
    post: dict[str, int]
    delta: dict[str, int]

    @model_validator(mode="after")
    def _validate_delta(self) -> PickInventorySummary:
        for key in set(self.pre) | set(self.post) | set(self.delta):
            expected = self.post.get(key, 0) - self.pre.get(key, 0)
            actual = self.delta.get(key, 0)
            if actual != expected:
                raise ValueError(
                    f"delta[{key!r}]={actual} inconsistent with "
                    f"post-pre={expected} "
                    f"(pre={self.pre.get(key, 0)}, post={self.post.get(key, 0)})"
                )
        return self


class RosterContext(BaseModel):
    position_depth_change: list[PositionDepthChange]
    age_stats: AgeStats
    pick_inventory_summary: PickInventorySummary


class PolicyOverride(BaseModel):
    hard_untouchables: list[str] | None = Field(None, max_length=25)
    protected_players: list[str] | None = Field(None, max_length=25)
    protected_pick_patterns: list[str] | None = Field(None, max_length=25)


class AnalyzeTradeInput(BaseModel):
    my_send: list[str] = Field(..., min_length=1, max_length=10)
    my_receive: list[str] = Field(..., min_length=1, max_length=10)
    policy_override: PolicyOverride | None = None


class AnalyzeTradeOutput(ResponseEnvelope):
    asset_resolution: list[AssetResolution]
    value_math: ValueMath | None = None
    roster_context: RosterContext | None = None

    @model_validator(mode="after")
    def _validate_blocked_trade_shape(self) -> AnalyzeTradeOutput:
        if self.policy_status == PolicyStatus.BLOCKED:
            if self.value_math is not None:
                raise ValueError("BLOCKED trades must not return value_math")
            if self.roster_context is not None:
                raise ValueError("BLOCKED trades must not return roster_context")
            if self.data_status != DataStatus.UNAVAILABLE:
                raise ValueError("BLOCKED trades must have data_status=UNAVAILABLE")
        return self
