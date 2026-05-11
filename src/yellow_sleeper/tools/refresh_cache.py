from __future__ import annotations

from ..analyze.pipelines import refresh_cache_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_refresh_cache(force: bool = False) -> dict:
    """Refresh Sleeper and FantasyCalc caches and return before/after status."""
    runtime = await get_runtime()
    prior, post, refreshed, failures = await runtime.refresh_all(force=force)
    output = refresh_cache_output(
        prior_status=prior,
        post_status=post,
        refreshed=refreshed,
        failures=failures,
    )
    return output.model_dump(mode="json")
