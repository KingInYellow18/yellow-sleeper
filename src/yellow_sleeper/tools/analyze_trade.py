from __future__ import annotations

from ..analyze.pipelines import analyze_trade_pipeline
from ..models import PolicyOverride
from ..runtime import get_runtime
from ..server import mcp


@mcp.tool()
async def dynasty_analyze_trade(
    my_send: list[str],
    my_receive: list[str],
    policy_override: dict | None = None,
) -> dict:
    """Return trade resolution, guardrail, value, roster, policy, and source details."""
    runtime = await get_runtime()
    override = PolicyOverride.model_validate(policy_override) if policy_override else None
    policy, config_sources = runtime.config.policy(override)
    snapshot, _ = await runtime.snapshot()
    players, _ = await runtime.players()
    values, _ = await runtime.values()
    output = analyze_trade_pipeline(
        my_send=my_send,
        my_receive=my_receive,
        policy=policy,
        snapshot=snapshot,
        players=players,
        values=values,
        sleeper_username=runtime.config.static.sleeper_username,
        config_sources=config_sources,
    )
    return output.model_dump(mode="json")
