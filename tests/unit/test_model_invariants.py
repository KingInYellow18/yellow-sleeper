from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from yellow_sleeper.models import (
    ListMyPicksInput,
    ListTradedPicksInput,
    PerAssetValue,
    PickContext,
    PickInventorySummary,
    PositionDepthChange,
    TradedPick,
    ValueSourceBreakdown,
    WhatsOnTheClockOutput,
)


def _value_source(value: float | None, *, enabled: bool = True) -> ValueSourceBreakdown:
    return ValueSourceBreakdown(
        source="fantasycalc",
        value=value,
        timestamp=datetime.now(UTC),
        enabled=enabled,
    )


def test_position_depth_change_rejects_inconsistent_delta() -> None:
    """pre=3, post=4, delta=1 is valid; delta=5 must raise."""
    PositionDepthChange(position="RB", pre=3, post=4, delta=1)
    with pytest.raises(ValidationError, match="inconsistent"):
        PositionDepthChange(position="RB", pre=3, post=4, delta=5)


def test_position_depth_change_accepts_negative_delta() -> None:
    PositionDepthChange(position="QB", pre=3, post=1, delta=-2)


def test_pick_inventory_summary_rejects_inconsistent_delta() -> None:
    """Sibling invariant to PositionDepthChange — keys with mismatched delta must raise."""
    PickInventorySummary(
        pre={"2026_R1": 1, "2026_R2": 2},
        post={"2026_R1": 0, "2026_R2": 2},
        delta={"2026_R1": -1, "2026_R2": 0},
    )
    with pytest.raises(ValidationError, match="inconsistent"):
        PickInventorySummary(
            pre={"2026_R1": 1},
            post={"2026_R1": 0},
            delta={"2026_R1": 5},
        )


def test_pick_inventory_summary_handles_asymmetric_keys() -> None:
    """Keys present in only post are treated as pre=0; only-pre keys treated as post=0."""
    PickInventorySummary(
        pre={"2026_R1": 1},
        post={"2026_R1": 1, "2027_R3": 1},
        delta={"2026_R1": 0, "2027_R3": 1},
    )
    with pytest.raises(ValidationError, match="inconsistent"):
        PickInventorySummary(
            pre={"2026_R1": 1},
            post={"2026_R1": 1, "2027_R3": 1},
            delta={"2026_R1": 0, "2027_R3": 0},
        )


def _pick_context() -> PickContext:
    return PickContext(
        round=1, slot=1, on_the_clock_owner="owner", on_the_clock_team="team"
    )


def test_whats_on_the_clock_drafting_requires_pick_context() -> None:
    with pytest.raises(ValidationError, match="pick_context"):
        WhatsOnTheClockOutput(
            data_status="COMPLETE",
            policy_status="OK",
            resolution_status="OK",
            generated_at="2026-01-01T00:00:00Z",
            draft_status="drafting",
            pick_context=None,
        )


def test_whats_on_the_clock_non_drafting_forbids_pick_context() -> None:
    with pytest.raises(ValidationError, match="pick_context"):
        WhatsOnTheClockOutput(
            data_status="COMPLETE",
            policy_status="OK",
            resolution_status="OK",
            generated_at="2026-01-01T00:00:00Z",
            draft_status="complete",
            pick_context=_pick_context(),
        )
    with pytest.raises(ValidationError, match="pick_context"):
        WhatsOnTheClockOutput(
            data_status="COMPLETE",
            policy_status="OK",
            resolution_status="OK",
            generated_at="2026-01-01T00:00:00Z",
            draft_status="not_started",
            pick_context=_pick_context(),
        )


def test_whats_on_the_clock_drafting_accepts_pick_context() -> None:
    WhatsOnTheClockOutput(
        data_status="COMPLETE",
        policy_status="OK",
        resolution_status="OK",
        generated_at="2026-01-01T00:00:00Z",
        draft_status="drafting",
        pick_context=_pick_context(),
    )


def test_season_year_bounds_reject_out_of_range() -> None:
    with pytest.raises(ValidationError):
        ListTradedPicksInput(seasons=[2019])
    with pytest.raises(ValidationError):
        ListTradedPicksInput(seasons=[2100])
    with pytest.raises(ValidationError):
        ListMyPicksInput(seasons=[1999])
    ListTradedPicksInput(seasons=[2026, 2099])
    ListMyPicksInput(seasons=[2020])


def test_traded_pick_rejects_malformed_pick_token() -> None:
    with pytest.raises(ValidationError):
        TradedPick(
            pick_token="malformed",
            display_name="2026 R1",
            season=2026,
            round=1,
            original_owner_roster_id=1,
            current_owner_roster_id=2,
            original_owner_name="Owner A",
            current_owner_name="Owner B",
        )
    TradedPick(
        pick_token="pick_2026_r1_orig1",
        display_name="2026 R1",
        season=2026,
        round=1,
        original_owner_roster_id=1,
        current_owner_roster_id=2,
        original_owner_name="Owner A",
        current_owner_name="Owner B",
    )


def test_per_asset_value_rejects_value_without_asset() -> None:
    with pytest.raises(ValidationError, match="asset"):
        PerAssetValue(asset=None, side="send", value=42.0)
    PerAssetValue(asset=None, side="send", value=None)
    PerAssetValue(asset="player_1234", side="send", value=42.0)


def test_per_asset_value_rejects_disagreement_with_sole_enabled_source() -> None:
    PerAssetValue(
        asset="player_1234",
        side="send",
        value=42.0,
        sources=[_value_source(42.0)],
    )
    with pytest.raises(ValidationError, match="disagrees"):
        PerAssetValue(
            asset="player_1234",
            side="send",
            value=42.0,
            sources=[_value_source(99.0)],
        )


def test_per_asset_value_skips_multi_source_coherence_check() -> None:
    # When 2+ sources are enabled-with-value, the single-source invariant
    # does not fire (scope intentionally narrow per plan 2.2).
    PerAssetValue(
        asset="player_1234",
        side="send",
        value=42.0,
        sources=[_value_source(40.0), _value_source(44.0)],
    )


def test_per_asset_value_rejects_none_value_with_sole_enabled_source() -> None:
    # value=None is inconsistent when exactly one enabled source carries a value.
    with pytest.raises(ValidationError, match="disagrees|sole enabled"):
        PerAssetValue(asset="x", side="send", value=None, sources=[_value_source(99.0)])


def test_per_asset_value_ignores_disabled_sources() -> None:
    # A disabled source's value is not in the disagreement check.
    PerAssetValue(
        asset="player_1234",
        side="send",
        value=42.0,
        sources=[_value_source(42.0), _value_source(99.0, enabled=False)],
    )
