from __future__ import annotations

import httpx
import pytest
import respx

from tests.conftest import load_fixture
from yellow_sleeper.clients import SleeperClient, build_shared_client, draft_state_ttl


@pytest.mark.asyncio
@respx.mock
async def test_sleeper_client_fetches_league_snapshot() -> None:
    league_id = "1234567890"
    respx.get(f"https://api.sleeper.app/v1/league/{league_id}").respond(
        json=load_fixture("sleeper/league.json")
    )
    respx.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").respond(
        json=load_fixture("sleeper/rosters_14team.json")
    )
    respx.get(f"https://api.sleeper.app/v1/league/{league_id}/users").respond(
        json=load_fixture("sleeper/users_14team.json")
    )
    respx.get(f"https://api.sleeper.app/v1/league/{league_id}/traded_picks").respond(
        json=load_fixture("sleeper/traded_picks.json")
    )
    respx.get(f"https://api.sleeper.app/v1/league/{league_id}/drafts").respond(
        json=load_fixture("sleeper/drafts.json")
    )
    async with build_shared_client() as http:
        client = SleeperClient(http)

        result = await client.get_league_snapshot(league_id)

    assert result.data["league"]["league_id"] == league_id
    assert len(result.data["rosters"]) == 14
    assert len(result.data["users"]) == 14


@pytest.mark.asyncio
@respx.mock
async def test_sleeper_client_does_not_retry_4xx() -> None:
    route = respx.get("https://api.sleeper.app/v1/league/bad").respond(404, json={"error": "no"})
    async with build_shared_client() as http:
        client = SleeperClient(http)
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_league("bad")

    assert route.call_count == 1


def test_draft_state_ttl() -> None:
    assert draft_state_ttl({"status": "drafting"}) == 30
    assert draft_state_ttl({"status": "complete"}) == 3600
