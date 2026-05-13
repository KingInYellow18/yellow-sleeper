# Feature: Review Follow-up — Type Invariants + Pipeline Test Coverage

## Problem Statement

The multi-agent persona review of PR #1 surfaced **6 high-confidence P1
findings** that were not auto-fixed because they require careful Pydantic
model design or new test files:

- **5 type-design P1s** — weak invariants in the Pydantic envelope models
  let the pipeline construct internally-inconsistent or untyped responses
  (e.g. `dict[str, Any]` shapes, missing cross-field validators, inputs with
  no per-element bounds).
- **1 test-coverage P1** — three pipeline functions
  (`league_power_map_output`, `refresh_cache_output`,
  `whats_on_the_clock_output`) have **zero** direct behavioral tests, plus
  ~10 branch-level gaps in pipelines that do have tests.

The reliability/correctness P1s from the same review were already fixed and
shipped in commit `c225e33`; this plan tackles only the residual P1 work.

## Current State

Models live in `src/yellow_sleeper/models/`:

- `shared.py` — `SourceNote`, `PolicyFlag`, `Candidate`, `AssetResolution`
- `envelope.py` — `ResponseEnvelope` with `model_validator` enforcing
  stale-explanation invariant (good prior art)
- `trade.py` — `ValueMath`, `PositionDepthChange`, `PickInventorySummary`,
  `PolicyOverride`, `AgeStats`
- `draft.py` — `PickContext`, `RecentPick`, `WhatsOnTheClockOutput`
- `picks.py` — `Pick`, `TradedPick`, `ListMyPicksInput`, `ListTradedPicksInput`
- `roster.py`, `bpa.py`, `health.py`, `refresh.py`, `values.py`

Tests live in `tests/{unit,integration,smoke}/`. 50 tests pass on `main`.
Smoke tests cover the tool wrappers (which call pipelines), but most pipeline
functions lack direct branch coverage.

## Proposed Solution

Two-phase implementation:

1. **Phase 1: tighten model invariants.** Add Pydantic `model_validator`s,
   replace `dict[str, Any]` with typed sub-models, add `Annotated` field
   constraints, and unify position types.
2. **Phase 2: pipeline behavioral tests.** Add direct tests for the three
   untested pipelines and fill the highest-value branch gaps in already-tested
   pipelines.

Each model invariant is small (~5-15 lines) and independent. Test additions
follow the existing fixture patterns in `tests/unit/test_*_resolver.py` and
`tests/integration/`.

<!-- deepen-plan: codebase -->
> **Codebase:** Three existing `model_validator(mode="after")` precedents to
> mirror: `envelope.py:37-43` and `envelope.py:45-56` (envelope-level
> invariants on `blocking_rules` and `stale` explanation), and
> `trade.py:65-74` (`AnalyzeTradeOutput._validate_blocked_trade_shape`). All
> three follow the same shape: validator returns `self`, raises `ValueError`
> on violation. Phase 1's new validators should follow this exact pattern for
> consistency.
<!-- /deepen-plan -->

<!-- deepen-plan: external -->
> **Research:** Pydantic v2 `model_validator(mode="after")` runs after
> field-level validation, so type-narrowed values are safe to dereference
> without `None` guards on required fields. **Most common footgun:**
> forgetting `return self` silently yields a `None` model instance — every
> new validator must end with `return self`. For machine-readable error
> classification (useful when MCP callers programmatically parse
> `ValidationError`), consider `PydanticCustomError` from `pydantic_core`
> instead of plain `ValueError`. Docs:
> <https://pydantic.dev/docs/validation/latest/concepts/validators/>
<!-- /deepen-plan -->

<!-- deepen-plan: external -->
> **Research:** Replacing `list[dict[str, Any]]` with a typed sub-model lifts
> the generated JSON schema from `{"type": "array", "items": {}}` to a full
> `$defs` entry — FastMCP surfaces this to MCP tool callers. Add
> `model_config = ConfigDict(extra="forbid")` to new sub-models exposed via
> MCP to reject silently-ignored unknown keys. FastMCP JSON schema docs:
> <https://gofastmcp.com/python-sdk/fastmcp-utilities-json_schema>
<!-- /deepen-plan -->

## Implementation Plan

### Phase 1: Model invariants

- [ ] **1.1** Add `_validate_pick_context_presence` `model_validator` to
  `WhatsOnTheClockOutput` (draft.py:31) enforcing
  `pick_context is None iff draft_status != "drafting"`. Verify the existing
  `whats_on_the_clock_output` pipeline construction satisfies this for both
  the `drafting` and `complete` paths (including the new `pool="all"` path
  that returns `data_status=PARTIAL` but `draft_status` unchanged).

- [ ] **1.2** Replace `ValueMath.per_asset: list[dict[str, Any]]` with a typed
  `PerAssetValue` sub-model. The known shape from `pipelines.py` is:
  `asset: str | None`, `side: Literal["send", "receive"]`,
  `value: float | None`, `sources: list[ValueSourceBreakdown]`. Update the
  pipeline construction site to emit `PerAssetValue` instances. Verify
  `models/__init__.py` re-exports the new type.

<!-- deepen-plan: codebase -->
> **Codebase:** The field is at `trade.py:17`, not line 12 (line 12 is the
> `class ValueMath(BaseModel):` line). Construction site is
> `pipelines.py:884-891` (plan said 884-889). The pipeline already writes
> `sources` as `list[ValueSourceBreakdown]` Python objects (not raw dicts) —
> `PerAssetValue.sources` should type as `list[ValueSourceBreakdown]`
> directly. No circular dependency: `trade.py:9` already has
> `from .values import SourceDisagreement`, so importing `ValueSourceBreakdown`
> from the same module is safe.
<!-- /deepen-plan -->

- [ ] **1.3** Add `_validate_delta` `model_validator` to `PositionDepthChange`
  (trade.py:21) enforcing `delta == post - pre`. The pipeline already
  computes the delta correctly; this turns a silent invariant into an
  explicit constructor-time check.

- [ ] **1.4** Constrain `seasons` field-element bounds on both
  `ListTradedPicksInput` (picks.py:11) and `ListMyPicksInput` (picks.py:31)
  via `Annotated[int, Field(ge=2020, le=2099)]` (matching the constraint
  already present on `Pick.season`). Define `SeasonYear` once at module
  scope and reuse.

- [ ] **1.5** Tighten `TradedPick` (picks.py:14) to match `Pick`'s
  constraints: `pick_token` regex pattern `^pick_\d{4}_r\d+_orig\d+$`,
  `season: int = Field(..., ge=2020, le=2099)`, `round: int = Field(..., ge=1, le=10)`.
  Extract a `_PickBase` parent if both classes get bulky.

- [ ] **1.6** Run `uv run ruff check` and `uv run pytest -x`. Each Pydantic
  change risks breaking an existing fixture; if any test fails, fix the
  fixture to satisfy the new invariant rather than weakening the invariant.

### Phase 2: Pipeline test coverage

- [ ] **2.1** Add `tests/unit/test_pipelines_whats_on_the_clock.py` with three
  test cases: (a) `status=complete` returns `pick_context=None`, (b)
  `status=drafting` returns populated `PickContext` with round/slot/owner,
  (c) `pool="all"` returns `data_status=PARTIAL` and source-note explanation.
  Each test calls `whats_on_the_clock_output` directly with synthetic dicts.

<!-- deepen-plan: codebase -->
> **Codebase:** No existing `tests/unit/test_pipelines_*.py` files — all
> Phase 2 files are net-new. The calling-pattern precedent is
> `tests/unit/test_stale_value_status.py`: import the pipeline function
> directly from `yellow_sleeper.analyze.pipelines`, call with in-memory dicts,
> assert on returned model fields. Phase 2 should follow this shape.
<!-- /deepen-plan -->

<!-- deepen-plan: external -->
> **Research:** Prefer `@pytest.mark.parametrize` over class-based suites for
> these pure-function pipeline tests — each case stays visible, test IDs are
> auto-generated (`test_foo[case0]`), no setup/teardown overhead. For error-
> path assertions in tests/unit/test_envelope_*.py-style coverage of the new
> invariants, assert on `exc_info.value.errors()[0]['type']` (stable slug
> like `"value_error"`) rather than the human message string — Pydantic
> message text can change across patch versions. Docs:
> <https://docs.pytest.org/en/stable/how-to/parametrize.html>
<!-- /deepen-plan -->

- [ ] **2.2** Add `tests/unit/test_pipelines_refresh_cache.py` with two test
  cases: (a) all keys refreshed → `data_status=COMPLETE`, (b) one key in
  `failures` → `data_status=PARTIAL` with failure entry carrying
  `success=False` and the error text.

- [ ] **2.3** Add `tests/unit/test_pipelines_league_power_map.py` with three
  test cases: (a) `include_pick_value=False` happy path, (b)
  `include_pick_value=True` asserts pick rollup populated, (c)
  `values_cache_status="stale"` propagates `data_status=PARTIAL` and a
  `STALE_DATA` policy flag.

- [ ] **2.4** Extend `tests/unit/test_pipelines_analyze_trade.py` (or create
  if absent) with: (a) `NEEDS_CLARIFICATION` branch (ambiguous asset name),
  (b) `data_status=UNAVAILABLE` when all assets miss values,
  (c) `delta_pct=None` guard when `send_total == 0`,
  (d) protected-pick-pattern flag emission.

- [ ] **2.5** Extend `tests/unit/test_pipelines_health_check.py` (or create
  if absent) with: (a) one stale key → `PARTIAL`, (b) all stale →
  `UNAVAILABLE`.

- [ ] **2.6** Run full test suite. Target: zero regressions; new tests
  pass; coverage on `analyze/pipelines.py` increases by a measurable
  margin (run `uv run pytest --cov=src/yellow_sleeper/analyze/pipelines`
  before and after).

### Phase 3: Submit

- [ ] **3.1** `gt create -m "feat: tighten model invariants + add pipeline tests"`.
- [ ] **3.2** `gt submit --no-interactive` → new PR stacked on top of PR #1.

## Technical Details

### Files to modify

- `src/yellow_sleeper/models/draft.py` — `WhatsOnTheClockOutput` validator (Task 1.1)
- `src/yellow_sleeper/models/trade.py` — `ValueMath`, `PositionDepthChange` (Tasks 1.2, 1.3)
- `src/yellow_sleeper/models/picks.py` — `seasons` bounds, `TradedPick` constraints (Tasks 1.4, 1.5)
- `src/yellow_sleeper/models/__init__.py` — re-export `PerAssetValue` if introduced (Task 1.2)
- `src/yellow_sleeper/analyze/pipelines.py` — update `_trade_value_math` to emit `PerAssetValue` (Task 1.2)

### Files to create

- `tests/unit/test_pipelines_whats_on_the_clock.py` (Task 2.1)
- `tests/unit/test_pipelines_refresh_cache.py` (Task 2.2)
- `tests/unit/test_pipelines_league_power_map.py` (Task 2.3)
- `tests/unit/test_pipelines_analyze_trade.py` if absent (Task 2.4)
- `tests/unit/test_pipelines_health_check.py` if absent (Task 2.5)

### Files NOT modified

- `src/yellow_sleeper/clients/`, `runtime.py`, `store/`, `tools/` — out of scope
- `tests/integration/`, `tests/smoke/` — pipeline tests are unit-level

## Acceptance Criteria

1. `WhatsOnTheClockOutput(draft_status="complete", pick_context=PickContext(...))`
   raises `ValidationError`.
2. `WhatsOnTheClockOutput(draft_status="drafting", pick_context=None)` raises
   `ValidationError`.
3. `ValueMath.per_asset[i]` is a typed `PerAssetValue` instance, not a `dict`.
4. `PositionDepthChange(pre=3, post=1, delta=5)` raises `ValidationError`.
5. `ListTradedPicksInput(seasons=[1800])` and `ListMyPicksInput(seasons=[3000])`
   raise `ValidationError`.
6. `TradedPick(pick_token="bad", season=2099, round=1)` raises `ValidationError`
   on the pattern; `season=1800` or `round=99` also raise.
7. `pytest tests/unit/test_pipelines_*.py` exercises `whats_on_the_clock_output`,
   `league_power_map_output`, and `refresh_cache_output` with at least 3 cases
   each (happy / partial / unavailable variants).
8. Full test suite passes; ruff check clean; no regressions in existing 50 tests.

## Edge Cases

- **Existing test fixtures may violate the new invariants.** Inspect
  `tests/conftest.py` fixtures for `WhatsOnTheClockOutput`,
  `PositionDepthChange`, `TradedPick`, and the trade pipeline. Update them
  to satisfy the new constraints rather than skipping validation.

<!-- deepen-plan: codebase -->
> **Codebase:** Sweep of existing tests confirms **no fixture currently
> constructs `WhatsOnTheClockOutput`, `PositionDepthChange`, or `TradedPick`
> with values that would fail the new invariants**. `test_envelope_validators.py:107`
> constructs `ValueMath(send_total=8200)` with default `per_asset=[]` (empty
> list) — survives the type change to `list[PerAssetValue]` since empty lists
> are valid. Edge-case risk is low; conftest sweep is precautionary, not
> repair-driven.
<!-- /deepen-plan -->

<!-- deepen-plan: external -->
> **Research:** yellow-sleeper is a personal MCP server with no external
> consumers, so the recommended migration strategy is **break-and-fix**
> rather than additive-only validators. If a Pydantic `ValidationError`
> surfaces during `pytest`, the `loc` path in the traceback identifies the
> exact field to repair — fix the fixture, do not soften the validator.
> Soften only when the validator is genuinely too strict (which the prior
> review didn't surface). Source:
> <https://roman.pt/posts/pydantic-as-backward-compatibility-layer/>
<!-- /deepen-plan -->
- **`pool="all"` path** — recent fix sets `data_status=PARTIAL` but leaves
  `draft_status` unchanged. The new validator must not reject this case.
  Confirm by checking the existing pipeline branch: if status was
  `complete`, `pick_context` stays `None`, which is consistent.
- **`PerAssetValue.sources` typing** — `ValueSourceBreakdown` is already
  defined in `models/values.py`. Verify it imports cleanly into `trade.py`
  without creating a circular dependency (`trade.py` already imports
  `SourceDisagreement` from `.values`, so adding `ValueSourceBreakdown` to
  that same import line is safe).
- **Smoke tests** that construct envelope responses via tool calls should
  continue passing because pipelines already produce valid shapes — the
  invariants formalize what's already true at the construction site.

## References

- PR #1: https://app.graphite.com/github/pr/KingInYellows/yellow-sleeper/1
- Commit `c225e33` — applied reliability + correctness P1 fixes (this plan
  is the follow-up for the type-design + test-coverage P1s)
- `src/yellow_sleeper/models/envelope.py:37-43` and `envelope.py:45-56` —
  prior art for `model_validator(mode="after")` (the two existing envelope-
  level invariants on `blocking_rules` and stale-explanation)
- `src/yellow_sleeper/models/trade.py:65-74` — third `model_validator` prior
  art (`AnalyzeTradeOutput._validate_blocked_trade_shape`)
- `src/yellow_sleeper/models/picks.py:35-43` — existing `Pick` model with the
  pattern + range constraints `TradedPick` should mirror
- `src/yellow_sleeper/analyze/pipelines.py:884-891` — `_trade_value_math`
  per-asset construction site to update for `PerAssetValue` (note: `sources`
  is already a list of `ValueSourceBreakdown` Python objects, not raw dicts)
- `src/yellow_sleeper/models/values.py:12` — `ValueSourceBreakdown` definition
  (importable into `trade.py` without circular dependency)
- `tests/unit/test_stale_value_status.py` — calling-pattern precedent for
  Phase 2 pipeline tests (direct pipeline import + in-memory dict input)
- Persona review aggregation (this session): type-design reviewer + test
  reviewer findings

<!-- deepen-plan: external -->
> **Research:** External docs consulted during enrichment:
> - Pydantic v2 validators: <https://pydantic.dev/docs/validation/latest/concepts/validators/>
> - Pydantic v2 errors / `PydanticCustomError`: <https://pydantic.com.cn/en/errors/errors/>
> - Multi-error collection patterns: <https://github.com/pydantic/pydantic/discussions/7470>
> - Backward-compat layer guidance: <https://roman.pt/posts/pydantic-as-backward-compatibility-layer/>
> - FastMCP JSON schema utilities: <https://gofastmcp.com/python-sdk/fastmcp-utilities-json_schema>
> - pytest parametrize: <https://docs.pytest.org/en/stable/how-to/parametrize.html>
> - Discriminated-union test patterns with `TypeAdapter`: <https://blog.dataengineerthings.org/pydantic-for-experts-discriminated-unions-in-pydantic-v2-2d9ca965b22f>
> - freezegun + Pydantic v2 schema-gen incompatibility: <https://github.com/spulec/freezegun/issues/551>
<!-- /deepen-plan -->
