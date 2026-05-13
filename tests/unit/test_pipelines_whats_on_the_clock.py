from __future__ import annotations

from typing import Any

from tests.conftest import load_fixture
from yellow_sleeper.analyze.pipelines import whats_on_the_clock_output
from yellow_sleeper.models import DataStatus


def test_complete_draft_returns_no_pick_context(
    sleeper_snapshot: dict[str, Any], players: dict[str, Any]
) -> None:
    draft = dict(load_fixture("sleeper/draft.json"))
    draft["status"] = "complete"
    draft_state = {"draft": draft, "picks": load_fixture("sleeper/draft_picks.json")}

    result = whats_on_the_clock_output(
        draft_state=draft_state, snapshot=sleeper_snapshot, players=players
    )

    assert result.draft_status == "complete"
    assert result.pick_context is None
    assert result.data_status == DataStatus.COMPLETE


def test_drafting_status_returns_populated_pick_context(
    sleeper_snapshot: dict[str, Any], players: dict[str, Any]
) -> None:
    draft_state = {
        "draft": load_fixture("sleeper/draft.json"),
        "picks": load_fixture("sleeper/draft_picks.json"),
    }

    result = whats_on_the_clock_output(
        draft_state=draft_state, snapshot=sleeper_snapshot, players=players
    )

    assert result.draft_status == "drafting"
    assert result.pick_context is not None
    assert result.pick_context.round >= 1
    assert result.pick_context.slot >= 1
    assert result.pick_context.on_the_clock_owner
    assert result.pick_context.on_the_clock_team


def test_pool_all_returns_partial_with_unimplemented_source_note(
    sleeper_snapshot: dict[str, Any], players: dict[str, Any]
) -> None:
    draft = dict(load_fixture("sleeper/draft.json"))
    draft["status"] = "complete"
    draft_state = {"draft": draft, "picks": load_fixture("sleeper/draft_picks.json")}

    result = whats_on_the_clock_output(
        draft_state=draft_state, snapshot=sleeper_snapshot, players=players, pool="all"
    )

    assert result.data_status == DataStatus.PARTIAL
    explanations = [
        note.explanation for note in result.source_notes if note.explanation
    ]
    assert any("pool='all'" in exp for exp in explanations)
