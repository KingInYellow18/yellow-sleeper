from __future__ import annotations

from yellow_sleeper.analyze.pipelines import health_check_output
from yellow_sleeper.models import DataStatus, FlagType


def _all_fresh() -> dict[str, str]:
    return {
        "sleeper_players_nfl": "fresh",
        "fantasycalc_values": "fresh",
        "league_snapshot": "fresh",
        "draft_state": "fresh",
    }


def test_one_stale_key_returns_partial_with_stale_flag() -> None:
    cache_status = {**_all_fresh(), "fantasycalc_values": "stale"}

    result = health_check_output(
        cache_status=cache_status,
        league_id="lg1",
        user="brad",
        config_sources=[".yellow-sleeper.yaml"],
    )

    assert result.data_status == DataStatus.PARTIAL
    stale_flags = [f for f in result.policy_flags if f.type == FlagType.STALE_DATA]
    assert len(stale_flags) == 1
    assert stale_flags[0].asset == "fantasycalc_values"


def test_all_stale_keys_return_unavailable() -> None:
    cache_status = dict.fromkeys(_all_fresh(), "stale")

    result = health_check_output(
        cache_status=cache_status,
        league_id="lg1",
        user="brad",
        config_sources=[".yellow-sleeper.yaml"],
    )

    assert result.data_status == DataStatus.UNAVAILABLE
    stale_flags = [f for f in result.policy_flags if f.type == FlagType.STALE_DATA]
    assert len(stale_flags) == 4
