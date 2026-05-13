from __future__ import annotations

from tests.conftest import fresh_cache_statuses
from yellow_sleeper.analyze.pipelines import refresh_cache_output
from yellow_sleeper.models import DataStatus


def test_all_keys_refreshed_returns_complete() -> None:
    statuses = fresh_cache_statuses()
    result = refresh_cache_output(
        prior_status=statuses,
        post_status=fresh_cache_statuses(),
        refreshed=list(statuses.keys()),
        failures=None,
    )

    assert result.data_status == DataStatus.COMPLETE
    assert {entry.cache_key for entry in result.refreshed} == set(statuses)
    assert result.failures == []


def test_partial_failure_returns_partial_with_failure_entry() -> None:
    refreshed_keys = ["sleeper_players_nfl", "league_snapshot", "draft_state"]
    failures = {"fantasycalc_values": "httpx.ReadTimeout: deadline exceeded"}

    result = refresh_cache_output(
        prior_status=fresh_cache_statuses(),
        post_status={**fresh_cache_statuses(), "fantasycalc_values": "stale"},
        refreshed=refreshed_keys,
        failures=failures,
    )

    assert result.data_status == DataStatus.PARTIAL
    assert len(result.refreshed) == 3
    assert len(result.failures) == 1
    failure = result.failures[0]
    assert failure.cache_key == "fantasycalc_values"
    assert failure.success is False
    assert failure.error == "httpx.ReadTimeout: deadline exceeded"
