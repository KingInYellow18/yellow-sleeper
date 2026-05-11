from __future__ import annotations

from ..analyze.pipelines import whats_on_the_clock_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_whats_on_the_clock(draft_id: str | None = None) -> dict:
    """Return current draft state, pick context, and recent picks.

    Currently always returns the rookies-only view. The contract's `pool`
    selector is intentionally omitted until the `all` view is implemented.
    """
    runtime = await get_runtime()
    snapshot, _ = await runtime.snapshot()
    draft_state, _ = await runtime.draft_state(draft_id)
    players, _ = await runtime.players()
    output = whats_on_the_clock_output(
        draft_state=draft_state,
        snapshot=snapshot,
        players=players,
    )
    return output.model_dump(mode="json")
