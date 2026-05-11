from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from rapidfuzz import fuzz

from ..models import AssetResolution, Candidate

PLAYER_RESOLVE_THRESHOLD = 88
PLAYER_CLARIFY_THRESHOLD = 70


def resolve_player(
    query: str,
    players: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> AssetResolution:
    records = _player_records(players)
    by_id = {record["sleeper_id"]: record for record in records if record.get("sleeper_id")}
    if query in by_id:
        record = by_id[query]
        return AssetResolution(
            input=query,
            asset_type="player",
            resolved_id=record["sleeper_id"],
            match_confidence=100,
        )

    scored = sorted(
        ((_score(query, record["name"]), record) for record in records),
        key=lambda item: item[0],
        reverse=True,
    )
    if not scored:
        return _unresolved(query)

    top_score, top_record = scored[0]
    candidates = [
        _candidate(record, score)
        for score, record in scored[:5]
        if score >= PLAYER_CLARIFY_THRESHOLD
    ]

    if top_score >= PLAYER_RESOLVE_THRESHOLD:
        return AssetResolution(
            input=query,
            asset_type="player",
            resolved_id=top_record["sleeper_id"],
            match_confidence=top_score,
        )
    if top_score >= PLAYER_CLARIFY_THRESHOLD:
        return AssetResolution(
            input=query,
            asset_type="player",
            resolved_id=None,
            match_confidence=top_score,
            candidates=candidates,
            manual_review=True,
        )
    return _unresolved(query)


def _score(query: str, candidate: str) -> int:
    return int(round(fuzz.WRatio(query, candidate)))


def _candidate(record: dict[str, Any], score: int) -> Candidate:
    return Candidate(
        sleeper_id=record.get("sleeper_id"),
        name=record["name"],
        position=record.get("position"),
        team=record.get("team"),
        match_confidence=score,
    )


def _unresolved(query: str) -> AssetResolution:
    return AssetResolution(
        input=query,
        asset_type="player",
        resolved_id=None,
        match_confidence=0,
        candidates=[],
        manual_review=True,
    )


def _player_records(
    players: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    raw_records: Iterable[Mapping[str, Any]]
    if isinstance(players, Mapping):
        raw_records = (
            {**record, "player_id": player_id}
            for player_id, record in players.items()
            if isinstance(record, Mapping)
        )
    else:
        raw_records = players

    records: list[dict[str, Any]] = []
    for raw in raw_records:
        sleeper_id = str(raw.get("player_id") or raw.get("sleeper_id") or raw.get("id") or "")
        name = (
            raw.get("full_name")
            or raw.get("search_full_name")
            or " ".join(part for part in [raw.get("first_name"), raw.get("last_name")] if part)
        )
        position = raw.get("position") or _first_position(raw.get("fantasy_positions"))
        if sleeper_id and name and position in {"QB", "RB", "WR", "TE"}:
            records.append(
                {
                    "sleeper_id": sleeper_id,
                    "name": str(name),
                    "position": str(position),
                    "team": raw.get("team"),
                    "age": raw.get("age"),
                }
            )
    return records


def _first_position(positions: Any) -> str | None:
    if isinstance(positions, list) and positions:
        return str(positions[0])
    return None
