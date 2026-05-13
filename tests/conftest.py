from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def load_fixture(relative_path: str) -> Any:
    return json.loads((FIXTURE_ROOT / relative_path).read_text(encoding="utf-8"))


@pytest.fixture
def sleeper_snapshot() -> dict[str, Any]:
    return {
        "league": load_fixture("sleeper/league.json"),
        "rosters": load_fixture("sleeper/rosters_14team.json"),
        "users": load_fixture("sleeper/users_14team.json"),
        "traded_picks": load_fixture("sleeper/traded_picks.json"),
        "drafts": load_fixture("sleeper/drafts.json"),
    }


@pytest.fixture
def players() -> dict[str, Any]:
    return load_fixture("sleeper/players_nfl.json")


@pytest.fixture
def values() -> list[dict[str, Any]]:
    return load_fixture("fantasycalc/values_current.json")


def fresh_cache_statuses() -> dict[str, str]:
    return {
        "sleeper_players_nfl": "fresh",
        "fantasycalc_values": "fresh",
        "league_snapshot": "fresh",
        "draft_state": "fresh",
    }
