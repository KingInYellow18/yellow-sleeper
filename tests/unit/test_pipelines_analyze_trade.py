from __future__ import annotations

from typing import Any

from yellow_sleeper.analyze.pipelines import analyze_trade_pipeline
from yellow_sleeper.config import DynamicPolicy
from yellow_sleeper.models import DataStatus, FlagType, PolicyStatus, ResolutionStatus


def test_unresolved_asset_returns_needs_clarification(
    sleeper_snapshot: dict[str, Any],
    players: dict[str, Any],
    values: list[dict[str, Any]],
) -> None:
    # Player name absent from the fixture forces `_unresolved` (match_confidence=0,
    # manual_review=True, resolved_id=None), which `_resolution_status` flags as
    # NEEDS_CLARIFICATION and the pipeline returns PARTIAL with no value_math.
    result = analyze_trade_pipeline(
        my_send=["Definitely Not A Real Player"],
        my_receive=["Bijan Robinson"],
        policy=DynamicPolicy(),
        snapshot=sleeper_snapshot,
        players=players,
        values=values,
        sleeper_username="brad",
    )

    assert result.policy_status == PolicyStatus.OK
    assert result.resolution_status == ResolutionStatus.NEEDS_CLARIFICATION
    assert result.data_status == DataStatus.PARTIAL
    assert result.value_math is None
    assert result.roster_context is None
    assert any(f.type == FlagType.AMBIGUOUS_RESOLUTION for f in result.policy_flags)


def test_all_assets_missing_values_returns_unavailable(
    sleeper_snapshot: dict[str, Any],
    players: dict[str, Any],
) -> None:
    # Use real player names so resolution succeeds, but empty values feed so
    # every asset reports value=None — exercising _trade_data_status UNAVAILABLE.
    result = analyze_trade_pipeline(
        my_send=["Drake London"],
        my_receive=["Bijan Robinson"],
        policy=DynamicPolicy(),
        snapshot=sleeper_snapshot,
        players=players,
        values=[],
        sleeper_username="brad",
    )

    assert result.policy_status == PolicyStatus.OK
    assert result.resolution_status == ResolutionStatus.OK
    assert result.data_status == DataStatus.UNAVAILABLE
    assert result.value_math is not None
    assert result.value_math.delta_pct is None


def test_stale_values_cache_emits_stale_flag_and_partial(
    sleeper_snapshot: dict[str, Any],
    players: dict[str, Any],
    values: list[dict[str, Any]],
) -> None:
    result = analyze_trade_pipeline(
        my_send=["Drake London"],
        my_receive=["Bijan Robinson"],
        policy=DynamicPolicy(),
        snapshot=sleeper_snapshot,
        players=players,
        values=values,
        sleeper_username="brad",
        values_cache_status="stale",
        values_cache_error="FantasyCalc 503",
    )

    assert result.data_status == DataStatus.PARTIAL
    stale_flags = [f for f in result.policy_flags if f.type == FlagType.STALE_DATA]
    assert len(stale_flags) == 1
    assert stale_flags[0].asset == "fantasycalc_values"
