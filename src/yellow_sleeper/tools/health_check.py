from __future__ import annotations

import asyncio

from ..analyze.pipelines import health_check_output
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_health_check(force_probe: bool = False) -> dict:
    """Return config, cache freshness, and source reachability details."""
    runtime = await get_runtime()
    probes = None
    if force_probe:
        probes = await asyncio.gather(runtime.sleeper.probe(), runtime.fantasycalc.probe())
    output = health_check_output(
        cache_status=runtime.cache.statuses(),
        league_id=runtime.config.static.sleeper_league_id,
        user=runtime.config.static.sleeper_username,
        config_sources=runtime.config.static_sources,
        live_probe_results=probes,
    )
    return output.model_dump(mode="json")
