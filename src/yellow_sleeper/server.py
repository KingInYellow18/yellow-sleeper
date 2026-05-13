from __future__ import annotations

from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from .runtime import create_runtime, set_runtime


@asynccontextmanager
async def lifespan(server: FastMCP):
    runtime = create_runtime()
    set_runtime(runtime)
    try:
        yield {"runtime": runtime}
    finally:
        try:
            await runtime.aclose()
        finally:
            set_runtime(None)


mcp = FastMCP("yellow-sleeper", lifespan=lifespan)

from . import tools as _tools  # noqa: E402,F401
