from __future__ import annotations

import sys


def main() -> int:
    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print("yellow-sleeper: local stdio MCP server")
        print("usage: yellow-sleeper")
        return 0

    from .server import mcp

    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
