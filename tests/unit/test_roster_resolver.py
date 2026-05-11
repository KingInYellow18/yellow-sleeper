from __future__ import annotations

from yellow_sleeper.resolve import resolve_roster


def test_resolve_roster_uses_narrow_margin_rule(sleeper_snapshot: dict) -> None:
    result = resolve_roster("mike", sleeper_snapshot["rosters"], sleeper_snapshot["users"])

    assert result.matched is None
    assert [match.owner_name for match in result.alternatives[:2]] == ["Mike Johnson", "Mike Smith"]


def test_resolve_roster_returns_single_confident_match(sleeper_snapshot: dict) -> None:
    result = resolve_roster(
        "Yellow Sleeper",
        sleeper_snapshot["rosters"],
        sleeper_snapshot["users"],
    )

    assert result.matched is not None
    assert result.matched.roster_id == 11
    assert result.alternatives == []
