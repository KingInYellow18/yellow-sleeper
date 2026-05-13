from __future__ import annotations

import pytest

from yellow_sleeper.analyze import build_pick_inventory
from yellow_sleeper.resolve import parse_pick_description, resolve_pick_description


@pytest.mark.parametrize(
    ("input_str", "expected_season", "expected_round", "owner"),
    [
        ("2027 1st", 2027, 1, None),
        ("my 2027 1st", 2027, 1, None),
        ("2027 1st (via Mike)", 2027, 1, "Mike"),
        ("Mike's 2027 1st", 2027, 1, "Mike"),
        ("next year's 2nd", 2027, 2, None),
        ("2027 first", 2027, 1, None),
        ("2027 1.03", 2027, 1, None),
        ("R1 2027", 2027, 1, None),
        ("2028 second-rounder", 2028, 2, None),
    ],
)
def test_pick_parser_extracts_supported_descriptions(
    input_str: str,
    expected_season: int,
    expected_round: int,
    owner: str | None,
) -> None:
    result = parse_pick_description(input_str, current_season=2026)

    assert result.parsed
    assert result.season == expected_season
    assert result.round == expected_round
    assert result.original_owner_query == owner


def test_pick_parser_requires_season_when_draft_inactive() -> None:
    result = parse_pick_description("1st", current_season=2026, draft_active=False)

    assert not result.parsed
    assert result.failure_reason == "missing season and no active draft"


def test_resolve_pick_detects_ambiguous_owned_pick(sleeper_snapshot: dict) -> None:
    inventory = build_pick_inventory(sleeper_snapshot, my_roster_id=11)

    result = resolve_pick_description(
        "my 2027 1st",
        owned_picks=inventory.owned_picks,
        current_season=2026,
    )

    assert result.asset_type == "pick"
    assert result.match_confidence == 50
    assert result.manual_review is True
    assert {candidate.pick_token for candidate in result.candidates} == {
        "pick_2027_r1_orig3",
        "pick_2027_r1_orig11",
    }


def test_resolve_pick_resolves_explicit_original_owner(sleeper_snapshot: dict) -> None:
    inventory = build_pick_inventory(sleeper_snapshot, my_roster_id=11)

    result = resolve_pick_description(
        "Mike Johnson's 2027 1st",
        owned_picks=inventory.owned_picks,
        current_season=2026,
    )

    assert result.resolved_id == "pick_2027_r1_orig3"
    assert result.match_confidence == 100
