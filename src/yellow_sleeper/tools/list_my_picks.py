from __future__ import annotations

from ..analyze import find_roster_id_for_username
from ..analyze.pipelines import list_my_picks_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_list_my_picks(
    seasons: list[int] | None = None,
    include_traded_away: bool = False,
) -> dict:
    """Return Brad's native, traded-in, and optionally traded-away picks."""
    runtime = await get_runtime()
    snapshot, _ = await runtime.snapshot()
    my_roster_id = (
        find_roster_id_for_username(snapshot, runtime.config.static.sleeper_username) or 0
    )
    output = list_my_picks_output(
        snapshot=snapshot,
        my_roster_id=my_roster_id,
        seasons=seasons,
        include_traded_away=include_traded_away,
    )
    return output.model_dump(mode="json")
