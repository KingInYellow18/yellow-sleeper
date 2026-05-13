# Yellow Sleeper MCP MVP Plan

Source documents: `PRD.md` v0.4.4, `TOOL_CONTRACTS.md` v1.0, `TECHNICAL_SPEC.md` v1.0. Re-read all three at each milestone before acting.

## Milestone 0: Project Memory And Spec Map

Spec sections: `goal.md` durable memory requirements; `PRD.md` MVP Definition of Done; `TOOL_CONTRACTS.md` §§1-4; `TECHNICAL_SPEC.md` §§1, 10-11.

Acceptance criteria:
- `PLAN.md`, `STATUS.md`, and `DECISIONS.md` exist at the repo root.
- The implementation milestones are independently testable and each lists validation commands.
- Spec drift or ambiguity is recorded in `DECISIONS.md`.

Validation commands:
- `test -f PLAN.md && test -f STATUS.md && test -f DECISIONS.md`

Stop-and-fix rule: if any project-memory file is missing or stale after a milestone, update it before moving on.

## Milestone 1: Packaging, Models, Config, Logging, Cache

Spec sections: `TOOL_CONTRACTS.md` §§1-3, 5; `TECHNICAL_SPEC.md` §§1-2, 7, 9, 11; `PRD.md` Status Fields and Additional Implementor Notes.

Acceptance criteria:
- Python package under `src/yellow_sleeper/` with `pyproject.toml` and command entry point.
- Every shared and tool-specific Pydantic model from `TOOL_CONTRACTS.md` §§1-2 exists under `models/` with specified field names, enums, limits, and validators.
- Cross-cutting validators for blocking consistency, stale explanation, blocked trade shape, and find-roster narrow margin are implemented and tested.
- Config loader follows precedence `tool_argument > .yellow-sleeper.yaml > env > defaults` for policy and env/YAML/defaults for static settings.
- Cache layer uses atomic writes, gzip for Sleeper players, per-key asyncio locks, TTL status helpers, and stale fallback.
- JSON file logging writes only to `.cache/logs/server.log` and redacts `league_id`, `username`, and `user_id`.

Validation commands:
- `ruff check src/ tests/`
- `python -m pytest tests/unit/ -x -q`

Stop-and-fix rule: no later milestone starts while model/config/cache/logging unit tests fail.

## Milestone 2: Clients, Fixtures, Resolution, Pick Inventory

Spec sections: `PRD.md` Data Source of Truth and Pick Inventory Algorithm; `TOOL_CONTRACTS.md` §§2.3-2.6, 4; `TECHNICAL_SPEC.md` §§3-5, 8, 10.

Acceptance criteria:
- Sleeper and FantasyCalc clients use one shared `httpx.AsyncClient`, explicit timeouts, retry semantics, response adapters, and cache keys from the spec.
- Hand-crafted Sleeper and FantasyCalc fixtures cover a 14-team league, Brad's roster, traded picks, a draft, draft picks, players, and values.
- Player, roster, and pick resolution enforce the fuzzy thresholds and narrow-margin rule.
- Pick inventory uses native grid plus traded overlay and never projects slots.

Validation commands:
- `ruff check src/ tests/`
- `python -m pytest tests/unit/ -x -q`
- `python -m pytest tests/integration/ -x -q`

Stop-and-fix rule: client/resolution regressions must be fixed before building tool pipelines.

## Milestone 3: Tool Pipelines And MCP Registration

Spec sections: `TOOL_CONTRACTS.md` §2 all tools; `TECHNICAL_SPEC.md` §§1, 6; `PRD.md` Guardrail Policy and LLM Consumption Contract.

Acceptance criteria:
- All eleven `dynasty_*` tools are implemented and registered on a single FastMCP instance.
- Every response includes `schema_version`, `policy_status`, `resolution_status`, `data_status`, `source_notes`, `policy_flags`, `blocking_rules`, and `config_sources`.
- `dynasty_analyze_trade` follows the ordered pipeline and enforces hard untouchable blocks, asset-resolution-required semantics, and no write actions.
- Tools return facts, flags, and source notes only; no verdicts, recommendations, `context_scores`, or `roster_mode`.

Validation commands:
- `ruff check src/ tests/`
- `python -m pytest tests/unit/ -x -q`
- `python -m pytest tests/integration/ -x -q`
- `python -m pytest tests/smoke/ -x -q`

Stop-and-fix rule: no distribution verification starts while any smoke scenario fails.

## Milestone 4: Full Verification, Install, Handoff

Spec sections: `goal.md` Verifiable end state; `TECHNICAL_SPEC.md` §11; all source documents for final audit.

Acceptance criteria:
- `uv tool install .` succeeds from this checkout.
- `yellow-sleeper --help` exits 0.
- `ruff check src/ tests/` passes.
- `python -m pytest tests/ -v` passes.
- `tests/smoke/test_smoke_questions.py` contains six smoke scenarios and all pass.
- `STATUS.md` final entry reads `MVP complete — all smoke tests passing, ready for human review`.
- `HANDOFF.md` exists with inventory, verification commands, known gaps, deferred items, TODOs, and spec drift pointers.

Validation commands:
- `uv tool install --force .`
- `yellow-sleeper --help`
- `ruff check src/ tests/`
- `python -m pytest tests/ -v`

Stop-and-fix rule: every failed final gate must be repaired and re-run before marking the MVP complete.
