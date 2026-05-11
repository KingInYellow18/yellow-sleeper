from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz

from ..models import AssetResolution, Candidate, Pick

ROUND_LEXICON = {
    "1": 1,
    "1st": 1,
    "first": 1,
    "i": 1,
    "2": 2,
    "2nd": 2,
    "second": 2,
    "ii": 2,
    "3": 3,
    "3rd": 3,
    "third": 3,
    "iii": 3,
    "4": 4,
    "4th": 4,
    "fourth": 4,
    "iv": 4,
    "5": 5,
    "5th": 5,
    "fifth": 5,
    "v": 5,
}
RELATIVE_SEASON = {"next year": 1, "next year's": 1, "this year": 0, "this year's": 0}


@dataclass(frozen=True)
class ParsedPickDescription:
    raw: str
    season: int | None
    round: int | None
    original_owner_query: str | None = None
    is_mine: bool = False
    failure_reason: str | None = None

    @property
    def parsed(self) -> bool:
        return self.season is not None and self.round is not None and self.failure_reason is None


def parse_pick_description(
    value: str,
    *,
    current_season: int,
    draft_active: bool = False,
) -> ParsedPickDescription:
    text = " ".join(value.strip().split())
    lowered = text.lower()
    via_match = re.search(r"\(\s*via\s+([^)]+?)\s*\)", text, flags=re.IGNORECASE)
    via = via_match.group(1).strip() if via_match else None
    if via_match:
        text = (text[: via_match.start()] + text[via_match.end() :]).strip()
        lowered = text.lower()

    owner_possessive = None
    if not lowered.startswith(("next year", "this year")):
        owner_match = re.match(r"^(?P<owner>[\w .-]+?)'s\s+(?P<rest>.+)$", text)
        if owner_match:
            owner_possessive = owner_match.group("owner").strip()
            text = owner_match.group("rest").strip()
            lowered = text.lower()

    is_mine = False
    if lowered.startswith("my "):
        is_mine = True
        text = text[3:].strip()
        lowered = text.lower()

    season = _extract_season(lowered, current_season, draft_active)
    round_number = _extract_round(lowered)
    owner_query = via or owner_possessive

    if season is None:
        return ParsedPickDescription(
            raw=value,
            season=None,
            round=round_number,
            original_owner_query=owner_query,
            is_mine=is_mine,
            failure_reason="missing season and no active draft",
        )
    if round_number is None:
        return ParsedPickDescription(
            raw=value,
            season=season,
            round=None,
            original_owner_query=owner_query,
            is_mine=is_mine,
            failure_reason="missing or unsupported round",
        )
    return ParsedPickDescription(
        raw=value,
        season=season,
        round=round_number,
        original_owner_query=owner_query,
        is_mine=is_mine,
    )


def resolve_pick_description(
    value: str,
    *,
    owned_picks: list[Pick],
    league_picks: list[Pick] | None = None,
    current_season: int,
    side: str = "send",
    draft_active: bool = False,
) -> AssetResolution:
    parsed = parse_pick_description(value, current_season=current_season, draft_active=draft_active)
    if not parsed.parsed:
        return _unresolved(value)

    pool = owned_picks if side == "send" else league_picks or owned_picks
    matches = [
        pick
        for pick in pool
        if pick.season == parsed.season
        and pick.round == parsed.round
        and _owner_matches(parsed.original_owner_query, pick)
    ]

    if len(matches) == 1:
        return AssetResolution(
            input=value,
            asset_type="pick",
            resolved_id=matches[0].pick_token,
            match_confidence=100,
        )
    if len(matches) > 1:
        return AssetResolution(
            input=value,
            asset_type="pick",
            resolved_id=None,
            match_confidence=50,
            candidates=[_pick_candidate(pick, 50) for pick in matches[:5]],
            manual_review=True,
        )
    return _unresolved(value)


def pick_token(season: int, round_number: int, original_owner_roster_id: int) -> str:
    return f"pick_{season}_r{round_number}_orig{original_owner_roster_id}"


def round_label(round_number: int) -> str:
    suffix = "th"
    if round_number == 1:
        suffix = "st"
    elif round_number == 2:
        suffix = "nd"
    elif round_number == 3:
        suffix = "rd"
    return f"{round_number}{suffix}"


def _extract_season(lowered: str, current_season: int, draft_active: bool) -> int | None:
    season_match = re.search(r"\b(20\d{2})\b", lowered)
    if season_match:
        return int(season_match.group(1))
    for phrase, offset in RELATIVE_SEASON.items():
        if phrase in lowered:
            return current_season + offset
    return current_season if draft_active else None


def _extract_round(lowered: str) -> int | None:
    slot_match = re.search(r"\b([1-5])\.\d+\b", lowered)
    if slot_match:
        return int(slot_match.group(1))
    round_match = re.search(r"\br(?:ound\s*)?([1-5])\b", lowered)
    if round_match:
        return int(round_match.group(1))
    explicit_match = re.search(r"\bround\s*([1-5])\b", lowered)
    if explicit_match:
        return int(explicit_match.group(1))
    for token, round_number in ROUND_LEXICON.items():
        if re.search(rf"\b{re.escape(token)}(?:-rounder|-round)?\b", lowered):
            return round_number
    return None


def _owner_matches(owner_query: str | None, pick: Pick) -> bool:
    if owner_query is None:
        return True
    return fuzz.WRatio(owner_query, pick.original_owner_name) >= 88


def _pick_candidate(pick: Pick, score: int) -> Candidate:
    return Candidate(
        pick_token=pick.pick_token,
        name=pick.display_name,
        match_confidence=score,
    )


def _unresolved(value: str) -> AssetResolution:
    return AssetResolution(
        input=value,
        asset_type="pick",
        resolved_id=None,
        match_confidence=0,
        candidates=[],
        manual_review=True,
    )
