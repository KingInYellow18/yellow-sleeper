from __future__ import annotations

from ..analyze.pipelines import get_player_value_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_get_player_value(player: str) -> dict:
    """Return a player's value with source and resolution details.

    Values come from the FantasyCalc feed. The contract's `valuation_source`
    selector is intentionally omitted until an alternate (xlsx) source ships.
    """
    runtime = await get_runtime()
    players, _ = await runtime.players()
    values, _ = await runtime.values()
    output = get_player_value_output(player=player, players=players, values=values)
    return output.model_dump(mode="json")
