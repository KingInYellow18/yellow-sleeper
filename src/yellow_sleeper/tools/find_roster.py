from __future__ import annotations

from ..analyze.pipelines import find_roster_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_find_roster(search_term: str) -> dict:
    """Return fuzzy roster matches for a team, owner, or username."""
    runtime = await get_runtime()
    snapshot, _ = await runtime.snapshot()
    return find_roster_output(search_term, snapshot).model_dump(mode="json")
