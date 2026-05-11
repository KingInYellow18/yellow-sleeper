from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from yellow_sleeper.models import (
    AnalyzeTradeOutput,
    AssetResolution,
    BlockingRule,
    DataStatus,
    FindRosterOutput,
    PolicyStatus,
    ResolutionStatus,
    ResponseEnvelope,
    RosterMatch,
    SourceNote,
    ValueMath,
)


def test_blocked_envelope_requires_blocking_rules() -> None:
    with pytest.raises(ValidationError, match="requires non-empty blocking_rules"):
        ResponseEnvelope(
            policy_status=PolicyStatus.BLOCKED,
            resolution_status=ResolutionStatus.OK,
            data_status=DataStatus.UNAVAILABLE,
        )


def test_ok_envelope_rejects_blocking_rules() -> None:
    with pytest.raises(ValidationError, match="requires empty blocking_rules"):
        ResponseEnvelope(
            policy_status=PolicyStatus.OK,
            resolution_status=ResolutionStatus.OK,
            data_status=DataStatus.COMPLETE,
            blocking_rules=[
                BlockingRule(
                    rule="hard_untouchable",
                    asset="Drake London",
                    matched_against="Drake London",
                    match_confidence=100,
                    rule_source="tool_argument",
                )
            ],
        )


def test_stale_source_note_requires_explanation_and_stale_flag() -> None:
    with pytest.raises(ValidationError, match="cache_status=stale must set stale=True"):
        ResponseEnvelope(
            policy_status=PolicyStatus.OK,
            resolution_status=ResolutionStatus.OK,
            data_status=DataStatus.PARTIAL,
            source_notes=[
                SourceNote(
                    field="value_math",
                    source="fantasycalc",
                    timestamp=datetime.now(UTC),
                    cache_status="stale",
                    stale=False,
                )
            ],
        )

    with pytest.raises(ValidationError, match="explanation is required"):
        ResponseEnvelope(
            policy_status=PolicyStatus.OK,
            resolution_status=ResolutionStatus.OK,
            data_status=DataStatus.PARTIAL,
            source_notes=[
                SourceNote(
                    field="value_math",
                    source="fantasycalc",
                    timestamp=datetime.now(UTC),
                    cache_status="stale",
                    stale=True,
                )
            ],
        )


def test_blocked_trade_shape_rejects_value_math_and_roster_context() -> None:
    with pytest.raises(ValidationError, match="must not return value_math"):
        AnalyzeTradeOutput(
            policy_status=PolicyStatus.BLOCKED,
            resolution_status=ResolutionStatus.OK,
            data_status=DataStatus.UNAVAILABLE,
            blocking_rules=[
                BlockingRule(
                    rule="hard_untouchable",
                    asset="Drake London",
                    matched_against="Drake London",
                    match_confidence=100,
                    rule_source=".yellow-sleeper.yaml",
                )
            ],
            asset_resolution=[
                AssetResolution(
                    input="Drake London",
                    asset_type="player",
                    resolved_id="9745",
                    match_confidence=100,
                )
            ],
            value_math=ValueMath(send_total=8200),
        )


def test_find_roster_narrow_margin_validator() -> None:
    with pytest.raises(ValidationError, match="narrow-margin rule"):
        FindRosterOutput(
            policy_status=PolicyStatus.OK,
            resolution_status=ResolutionStatus.OK,
            data_status=DataStatus.COMPLETE,
            matched=RosterMatch(
                roster_id=4,
                owner_name="Mike Smith",
                username="mikes",
                match_confidence=92,
                matched_field="display_name",
            ),
            alternatives=[
                RosterMatch(
                    roster_id=11,
                    owner_name="Mike Johnson",
                    username="bigmike",
                    match_confidence=89,
                    matched_field="display_name",
                )
            ],
        )
