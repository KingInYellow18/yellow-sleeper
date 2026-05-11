from __future__ import annotations

import pytest
import respx

from yellow_sleeper.clients import FantasyCalcClient, build_shared_client, index_records
from tests.conftest import load_fixture


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
