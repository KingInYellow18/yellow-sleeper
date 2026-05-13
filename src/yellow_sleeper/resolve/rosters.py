from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rapidfuzz import fuzz

from ..models import RosterMatch

ROSTER_RESOLVE_THRESHOLD = 88
ROSTER_MIN_GAP = 5
ROSTER_FAIL_THRESHOLD = 70


@dataclass(frozen=True)
class RosterResolution:
    matched: RosterMatch | None
    alternatives: list[RosterMatch]

    @property
    def needs_clarification(self) -> bool:
        return self.matched is None


def resolve_roster(
    search_term: str,
    rosters: list[dict[str, Any]],
    users: list[dict[str, Any]],
) -> RosterResolution:
    user_by_id = {user.get("user_id"): user for user in users}
    scored = [
        _score_roster(search_term, roster, user_by_id.get(roster.get("owner_id"), {}))
        for roster in rosters
    ]
    scored.sort(key=lambda match: match.match_confidence, reverse=True)

    if not scored:
        return RosterResolution(matched=None, alternatives=[])

    top = scored[0]
    second = scored[1] if len(scored) > 1 else None
    enough_gap = second is None or top.match_confidence - second.match_confidence >= ROSTER_MIN_GAP
    if top.match_confidence >= ROSTER_RESOLVE_THRESHOLD and enough_gap:
        return RosterResolution(matched=top, alternatives=[])

    alternatives = [
        match for match in scored[:5] if match.match_confidence >= ROSTER_FAIL_THRESHOLD
    ]
    if not alternatives:
        alternatives = scored[:5]
    return RosterResolution(matched=None, alternatives=alternatives)


def _score_roster(
    search_term: str,
    roster: dict[str, Any],
    user: dict[str, Any],
) -> RosterMatch:
    metadata = user.get("metadata") if isinstance(user.get("metadata"), dict) else {}
    fields = {
        "team_name": str(metadata.get("team_name") or ""),
        "display_name": str(user.get("display_name") or ""),
        "username": str(user.get("username") or ""),
    }
    field, score = max(
        (
            (field_name, int(round(fuzz.WRatio(search_term, value))))
            for field_name, value in fields.items()
        ),
        key=lambda item: item[1],
    )
    return RosterMatch(
        roster_id=int(roster["roster_id"]),
        owner_name=fields["display_name"] or fields["username"] or f"Roster {roster['roster_id']}",
        username=fields["username"] or fields["display_name"] or f"roster_{roster['roster_id']}",
        match_confidence=score,
        matched_field=field,  # type: ignore[arg-type]
    )
