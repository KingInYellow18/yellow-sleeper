from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CacheKey = Literal["sleeper_players_nfl", "fantasycalc_values", "league_snapshot", "draft_state"]


@dataclass(frozen=True)
class CacheSpec:
    key: CacheKey
    ttl_seconds: int
    gzipped: bool = False


CACHE_SPECS: dict[CacheKey, CacheSpec] = {
    "sleeper_players_nfl": CacheSpec("sleeper_players_nfl", 24 * 60 * 60, gzipped=True),
    "fantasycalc_values": CacheSpec("fantasycalc_values", 6 * 60 * 60),
    "league_snapshot": CacheSpec("league_snapshot", 5 * 60),
    "draft_state": CacheSpec("draft_state", 60 * 60),
}


def cache_path(base_dir: Path, key: CacheKey, *, gzipped: bool | None = None) -> Path:
    spec = CACHE_SPECS[key]
    use_gzip = spec.gzipped if gzipped is None else gzipped
    suffix = ".json.gz" if use_gzip else ".json"
    return base_dir / f"{key}{suffix}"
