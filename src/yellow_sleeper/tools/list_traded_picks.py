from __future__ import annotations

from ..analyze.pipelines import list_traded_picks_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_list_traded_picks(seasons: list[int] | None = None) -> dict:
    """Return enriched Sleeper traded-pick records."""
    runtime = await get_runtime()
    snapshot, _ = await runtime.snapshot()
    output = list_traded_picks_output(snapshot=snapshot, my_roster_id=0, seasons=seasons)
    return output.model_dump(mode="json")
