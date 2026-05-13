from __future__ import annotations

from typing import Literal

from ..analyze.pipelines import whats_on_the_clock_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_whats_on_the_clock(
    draft_id: str | None = None,
    pool: Literal["rookies_only", "all"] = "rookies_only",
) -> dict:
    """Return current draft state, pick context, and recent picks."""
    runtime = await get_runtime()
    snapshot, _ = await runtime.snapshot()
    draft_state, _ = await runtime.draft_state(draft_id)
    players, _ = await runtime.players()
    output = whats_on_the_clock_output(
        draft_state=draft_state,
        snapshot=snapshot,
        players=players,
        pool=pool,
    )
    return output.model_dump(mode="json")
