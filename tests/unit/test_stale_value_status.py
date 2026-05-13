from __future__ import annotations

from tests.conftest import load_fixture
from yellow_sleeper.analyze.pipelines import get_player_value_output
from yellow_sleeper.models import DataStatus, FlagType


def test_get_player_value_surfaces_stale_fantasycalc_values() -> None:
    result = get_player_value_output(
        player="Drake London",
        players=load_fixture("sleeper/players_nfl.json"),
        values=load_fixture("fantasycalc/values_current.json"),
        values_cache_status="stale",
        values_cache_error="FantasyCalc validation failed",
    )

    assert result.data_status == DataStatus.PARTIAL
    assert result.policy_flags[0].type == FlagType.STALE_DATA
    assert result.source_notes[0].cache_status == "stale"
    assert result.source_notes[0].stale is True
    assert result.source_notes[0].explanation == "FantasyCalc validation failed"
