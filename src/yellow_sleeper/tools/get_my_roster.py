from __future__ import annotations

from ..analyze.pipelines import get_my_roster_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_get_my_roster() -> dict:
    """Return Brad's roster with context, policy, and source details."""
    runtime = await get_runtime()
    policy, config_sources = runtime.config.policy()
    snapshot, _ = await runtime.snapshot()
    players, _ = await runtime.players()
    values, _ = await runtime.values()
    output = get_my_roster_output(
        snapshot=snapshot,
        players=players,
        values=values,
        sleeper_username=runtime.config.static.sleeper_username,
        policy=policy,
        config_sources=config_sources,
    )
    return output.model_dump(mode="json")
