from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import respx

from tests.conftest import load_fixture
from yellow_sleeper.clients import FantasyCalcClient, build_shared_client, index_records
from yellow_sleeper.store import Cache


@pytest.mark.asyncio
@respx.mock
async def test_fantasycalc_client_validates_and_indexes_records() -> None:
    respx.get("https://api.fantasycalc.com/values/current").respond(
        json=load_fixture("fantasycalc/values_current.json")
    )
    async with build_shared_client() as http:
        client = FantasyCalcClient(http)

        records = await client.get_current_values()

    index = index_records(records)
    assert index["by_sleeper_id"]["9745"].value == 8200
    assert index["by_name_lower"]["drake london"].player.sleeperId == "9745"


@pytest.mark.asyncio
@respx.mock
async def test_fantasycalc_malformed_response_falls_back_to_stale_cache(
    tmp_path: Path,
) -> None:
    cached = load_fixture("fantasycalc/values_current.json")
    cache = Cache(tmp_path)
    await cache.write("fantasycalc_values", cached)
    old = time.time() - (8 * 60 * 60)
    os.utime(tmp_path / "fantasycalc_values.json", (old, old))
    respx.get("https://api.fantasycalc.com/values/current").respond(
        json=[{"player": {"id": 1, "name": "Broken", "position": "WR"}}]
    )
    async with build_shared_client() as http:
        client = FantasyCalcClient(http)

        result = await client.get_current_values_cached(cache)

    assert result.status == "stale"
    assert result.data == cached
    assert result.error is not None
