from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from ..models import LiveProbeResult
from ..store import Cache

logger = logging.getLogger("yellow_sleeper.clients.fantasycalc")

QUERY_PARAMS = {
    "isDynasty": "true",
    "numQbs": "2",
    "numTeams": "14",
    "ppr": "1",
}


class FCPlayer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    sleeperId: str | None = None
    position: str


class FCRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    player: FCPlayer
    value: float
    overallRank: int
    redraftValue: float | None = None
    trend30Day: float | None = None


class FantasyCalcClient:
    BASE_URL = "https://api.fantasycalc.com"

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def get_current_values(self) -> list[FCRecord]:
        response = await self._http.get(f"{self.BASE_URL}/values/current", params=QUERY_PARAMS)
        response.raise_for_status()
        raw = response.json()
        records: list[FCRecord] = []
        skipped = 0
        for record in raw:
            try:
                records.append(FCRecord.model_validate(record))
            except ValidationError as exc:
                skipped += 1
                logger.warning(
                    "fantasycalc: skipping malformed record: %s",
                    str(exc)[:200],
                )
        if skipped:
            logger.warning(
                "fantasycalc: skipped %d/%d malformed records",
                skipped,
                len(raw),
            )
        return records

    async def get_current_values_cached(self, cache: Cache, *, force: bool = False):
        async def fetch() -> list[dict]:
            return [record.model_dump(mode="json") for record in await self.get_current_values()]

        return await cache.read_or_fetch("fantasycalc_values", fetch, force=force)

    async def probe(self) -> LiveProbeResult:
        start = time.monotonic()
        try:
            response = await self._http.get(
                f"{self.BASE_URL}/values/current",
                params={**QUERY_PARAMS, "limit": "1"},
            )
            response.raise_for_status()
            records = response.json()
            if not records:
                raise ValueError("empty response")
            FCRecord.model_validate(records[0])
            elapsed = int((time.monotonic() - start) * 1000)
            return LiveProbeResult(
                source="fantasycalc",
                reachable=True,
                latency_ms=elapsed,
                probed_at=datetime.now(UTC),
            )
        except Exception as exc:
            return LiveProbeResult(
                source="fantasycalc",
                reachable=False,
                error=str(exc)[:500],
                probed_at=datetime.now(UTC),
            )


def index_records(records: list[FCRecord]) -> dict[str, dict[str, FCRecord]]:
    return {
        "by_sleeper_id": {
            record.player.sleeperId: record for record in records if record.player.sleeperId
        },
        "by_name_lower": {record.player.name.lower(): record for record in records},
    }
