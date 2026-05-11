from __future__ import annotations

from tests.conftest import load_fixture
from yellow_sleeper.resolve import resolve_player


def test_resolve_player_by_exact_name() -> None:
    players = load_fixture("sleeper/players_nfl.json")

    result = resolve_player("Drake London", players)

    assert result.resolved_id == "9745"
    assert result.match_confidence == 100
    assert result.manual_review is False


def test_resolve_player_returns_candidates_for_clarification() -> None:
    players = load_fixture("sleeper/players_nfl.json")

    result = resolve_player("Jalen", players)

    assert result.resolved_id is None
    assert result.manual_review is True
    assert result.match_confidence >= 70
    assert {candidate.name for candidate in result.candidates} >= {"Jaylen Wright"}


def test_resolve_player_fails_below_threshold() -> None:
    players = load_fixture("sleeper/players_nfl.json")

    result = resolve_player("not a player", players)

    assert result.resolved_id is None
    assert result.match_confidence == 0
    assert result.manual_review is True
