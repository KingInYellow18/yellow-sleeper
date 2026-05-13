from __future__ import annotations

from typing import Any

from yellow_sleeper.analyze.pipelines import league_power_map_output
from yellow_sleeper.models import DataStatus, FlagType


def test_happy_path_without_pick_value(
    sleeper_snapshot: dict[str, Any],
    players: dict[str, Any],
    values: list[dict[str, Any]],
) -> None:
    result = league_power_map_output(
        snapshot=sleeper_snapshot, players=players, values=values
    )

    assert result.data_status in {DataStatus.COMPLETE, DataStatus.PARTIAL}
    assert len(result.teams) == len(sleeper_snapshot["rosters"])
    assert all(team.pick_total is None for team in result.teams)
    assert all(team.roster_total >= 0 for team in result.teams)


def test_include_pick_value_populates_pick_rollup(
    sleeper_snapshot: dict[str, Any],
    players: dict[str, Any],
    values: list[dict[str, Any]],
) -> None:
    result = league_power_map_output(
        snapshot=sleeper_snapshot,
        players=players,
        values=values,
        include_pick_value=True,
    )

    assert any(team.pick_total is not None for team in result.teams)


def test_stale_values_cache_propagates_partial_and_flag(
    sleeper_snapshot: dict[str, Any],
    players: dict[str, Any],
    values: list[dict[str, Any]],
) -> None:
    result = league_power_map_output(
        snapshot=sleeper_snapshot,
        players=players,
        values=values,
        values_cache_status="stale",
        values_cache_error="FantasyCalc 503",
    )

    assert result.data_status == DataStatus.PARTIAL
    stale_flags = [f for f in result.policy_flags if f.type == FlagType.STALE_DATA]
    assert len(stale_flags) == 1
    assert stale_flags[0].asset == "fantasycalc_values"
