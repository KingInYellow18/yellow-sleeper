# Feature: Review Follow-up Round 2 — Residual P1-P2 Items

## Problem Statement

The multi-agent persona review of PR #2
(`agent/feat/review-followup-type-invariants`) surfaced **5 residual P1-P2
findings** that were intentionally not auto-applied because each requires
design judgment or a multi-file refactor better suited to a separate PR:

1. **`source_disagreement` called with a single-element list** (maintainability
   P1, manual) — `ValueMath.source_disagreement` is always `None` because the
   call site iterates per-asset and passes `[value_source]` (length 1).
   Disagreement is intrinsically a cross-source concept; the current call
   shape can never produce one. Dead logic.
2. **`PerAssetValue` cross-field invariants** (type-design 3× P1) —
   - `asset=None` with `value!=None` is a representable invalid state
   - `sources[*].value` and `.value` coherence is unenforced
   - The new typed sub-model formalizes structure but not relationships
3. **Test fixture duplication** (maintainability P1, code-simplicity +
   polyglot + pr-test-analyzer P2-P3 — 4 reviewers) — Three of the new
   `test_pipelines_*.py` files each declare an identical local `snapshot`
   fixture that mirrors `conftest.sleeper_snapshot`; `players` is
   triplicated; `values` is duplicated; `_fresh_statuses`/`_all_fresh` are
   duplicated across two files.
4. **`extra='forbid'` consistency** (5 reviewers: maintainability,
   adversarial, code-simplicity, type-design, architecture, all P2-P3) —
   Only `PerAssetValue` has `extra='forbid'`. Sibling sub-models exposed via
   the same MCP schema (`ValueMath`, `PositionDepthChange`,
   `PickInventorySummary`, `AgeStats`, `RosterContext`,
   `ValueSourceBreakdown`) do not. Asymmetric hardening posture.
5. **`_adjust_pick_count` negative-floor** (adversarial P2) —
   `PickInventorySummary.post[key]` can go to `-1` if a player sends a pick
   they don't own (no clamp at 0). Now that `PickInventorySummary` has the
   `_validate_delta` invariant from PR #2 review fixes, surfacing a negative
   `post` value is silently representable but semantically nonsensical.

<!-- deepen-plan: codebase -->
> **Codebase:** Important correction to this plan's earlier framing — the
> claimed conflict between `_adjust_pick_count` clamping and
> `PickInventorySummary._validate_delta` does NOT exist. The delta dict is
> built at construction time from the FINAL `pre`/`post` dicts
> (`pipelines.py:1028`: `{key: post.get(key,0) - pre.get(key,0) for key in keys}`),
> NOT from accumulated raw increments. Clamping `post[key] = max(0, ...)`
> still produces a delta consistent with the (clamped) post − pre, so the
> validator passes. The semantic question remains — "send a pick you don't
> own" silently maps to "no change" — but the implementation conflict is
> spurious. See the validator at `trade.py:61-71`.
<!-- /deepen-plan -->

## Linear Issues

(None — this work originates from PR #2 review aggregation, not an external
issue tracker.)

## Current State

After PR #2 merged or pending merge, the codebase has:

- `src/yellow_sleeper/models/trade.py:12` — `PerAssetValue` with
  `ConfigDict(extra="forbid")` (the only model with this config)
- `src/yellow_sleeper/models/trade.py:55` — `PickInventorySummary` with
  `_validate_delta` invariant added in PR #2 round-2
- `src/yellow_sleeper/analyze/pipelines.py:900-901` —
  `source_disagreement([value_source])` per-asset call (always length 1)
- `src/yellow_sleeper/analyze/pipelines.py:1018-1023` —
  `_adjust_pick_count(post, resolved_id, inventory, ±1)` with no floor
- `src/yellow_sleeper/analyze/pipelines.py:1039` — `_adjust_pick_count` impl
- `tests/conftest.py:16-23` — existing `sleeper_snapshot` fixture (target
  for consolidation)
- `tests/unit/test_pipelines_{analyze_trade,whats_on_the_clock,league_power_map}.py`
  — 3× duplicated `snapshot` fixture, 3× duplicated `players` fixture,
  2× duplicated `values` fixture
- `tests/unit/test_pipelines_{health_check,refresh_cache}.py` —
  2× duplicated `_all_fresh()`/`_fresh_statuses()` helper

## Proposed Solution

Five small, mostly independent changes grouped into three phases:

1. **Phase 1: Pure cleanup** (fixture consolidation, dead code removal) —
   zero behavioral risk.
2. **Phase 2: Invariant additions** (`PerAssetValue` cross-field validators,
   `_adjust_pick_count` floor + matching invariant on
   `PickInventorySummary`) — requires design choice on each invariant's
   strictness.
3. **Phase 3: Consistency sweep** (`extra='forbid'` across siblings) — easy
   if we keep it simple, requires audit if we want a shared base class.

Each item ships independently. If any item turns out to require breaking
contract changes, it can be deferred without blocking the others.

<!-- deepen-plan: codebase -->
> **Codebase:** Bonus low-cost cleanup discovered during validation —
> `_user_by_owner(snapshot)` is rebuilt on every iteration inside
> `_recent_pick` (`pipelines.py:1088-1103`, called from
> `whats_on_the_clock_output:493`). Up to 10 redundant dict builds per
> call. Hoisting it once into `whats_on_the_clock_output` and threading
> the dict as a parameter to `_recent_pick` is a Phase 1-suitable
> performance improvement (was flagged by the performance reviewer in
> PR #2 review as pre-existing P3 but it's nearly free to fix here).
<!-- /deepen-plan -->

## Implementation Plan

### Phase 1: Cleanup (zero-risk)

- [ ] 1.1: Consolidate `snapshot` fixture — delete local declarations in
      `test_pipelines_analyze_trade.py:13`,
      `test_pipelines_whats_on_the_clock.py:12`,
      `test_pipelines_league_power_map.py:12`; rename their test
      parameters from `snapshot` to `sleeper_snapshot` to use the existing
      `conftest.sleeper_snapshot`. Verify all referencing tests still pass.
- [ ] 1.2: Move `players` fixture from `test_pipelines_*.py` (3 files) to
      `tests/conftest.py` with scope `function` (or `session` if
      `load_fixture` is pure). Drop local declarations.

<!-- deepen-plan: external -->
> **Research:** Use `scope="session"` for these fixtures. pytest's
> official guidance is that pure-data fixtures (immutable JSON loaded
> from disk) should be session-scoped to avoid meaningless per-test I/O.
> Only fall back to `function` scope if tests mutate the dict — in which
> case return `copy.deepcopy(session_loaded_data)` from a function-scoped
> wrapper around a session-scoped loader. See
> https://docs.pytest.org/en/stable/reference/fixtures.html ("Fixture
> scopes").
<!-- /deepen-plan -->
- [ ] 1.3: Move `values` fixture from
      `test_pipelines_{analyze_trade,league_power_map}.py` to
      `tests/conftest.py`. Drop local declarations.
- [ ] 1.4: Consolidate `_all_fresh()` / `_fresh_statuses()` helpers — pick
      one name (suggest `fresh_cache_statuses`), promote to
      `tests/conftest.py` as a fixture or to `tests/unit/_helpers.py` as a
      module constant. Update both
      `test_pipelines_{health_check,refresh_cache}.py` to import it.
- [ ] 1.5: Remove dead `source_disagreement` per-asset call —
      `pipelines.py:900-902` and the surrounding `disagreements: list`
      collection at line 880. The `disagreement` is always `None` because
      `source_disagreement` requires ≥2 sources to detect disagreement.
      Either:
      (a) **Remove entirely** and set `ValueMath.source_disagreement=None`
      with a TODO comment explaining the future cross-source design is
      out of scope, OR
      (b) **Move call to cross-asset scope** — call
      `source_disagreement(all_value_sources_from_per_asset)` once after
      the loop to detect disagreement across the whole trade.
      Choose (a) — simpler and matches current intent. (b) changes
      semantic meaning of the field; defer to a future PR if real
      disagreement detection is wanted.
- [ ] 1.6: Phase 1 gate — `uv run ruff check src/ tests/` and
      `uv run pytest tests/` clean.

### Phase 2: Invariants (requires design choices)

- [ ] 2.1: `PerAssetValue.asset|value` consistency invariant — add
      `model_validator(mode='after')` requiring `asset is not None when
      value is not None`. Semantic: a value without an asset is a category
      error. Verify no pipeline call site constructs a valueless
      `PerAssetValue` first then mutates `value` later (they don't —
      construction is single-shot at `pipelines.py:885-892`).

<!-- deepen-plan: external -->
> **Research:** `model_validator(mode='after')` is the correct choice per
> Pydantic v2 docs. It runs after all fields are coerced to their declared
> types, so `self.asset` and `self.value` are guaranteed to be their final
> values (including resolved `None` defaults). Alternatives are wrong fits:
> `field_validator` + `info.data` works only when the dependency field is
> declared *before* the validated field (fragile to reordering);
> `model_validator(mode='before')` runs on raw input (loses type safety);
> `computed_field` is for serialized derived values, not enforcement. See
> https://docs.pydantic.dev/latest/concepts/validators/ "Model Validators".
<!-- /deepen-plan -->
- [ ] 2.2: `PerAssetValue.value|sources` coherence invariant — add the same
      validator: when `sources` has exactly one enabled source with non-null
      `value`, `PerAssetValue.value` must equal that source's value (within
      `abs(diff) < 0.01` float tolerance). Document the rule in a model
      docstring. Per the current pipeline shape this is always true; the
      validator codifies the contract.
- [ ] 2.3: `_adjust_pick_count` negative floor — change `pipelines.py:1049`
      from `counts[key] = counts.get(key, 0) + delta` to
      `counts[key] = max(0, counts.get(key, 0) + delta)`. Add a comment
      explaining that "send a pick you don't own" maps to "no change"
      because the inventory delta is already wrong upstream and we don't
      want to surface negative pick counts to MCP callers.

<!-- deepen-plan: codebase -->
> **Codebase:** The "breaks `_validate_delta`" concern in the original
> plan was incorrect (see Problem Statement annotation). Delta is computed
> from final `pre`/`post` at `pipelines.py:1028`, not from accumulated
> raw increments — clamping `post` then deriving `delta = post − pre`
> still satisfies the validator. This item is safe to ship without the
> deferral. Add a comment at the clamp site documenting the silent-swallow
> semantic for callers who passed an unowned pick.
<!-- /deepen-plan -->
- [ ] 2.4: Add tests in `tests/unit/test_model_invariants.py` for 2.1 and
      2.2.
- [ ] 2.5: Phase 2 gate — `uv run pytest tests/` clean.

### Phase 3: Consistency (low-risk if scoped)

- [ ] 3.1: Decide between two options for `extra='forbid'`:
      (a) **Apply to all output sub-models** —
      `ValueSourceBreakdown`, `PositionDepthChange`,
      `PickInventorySummary`, `AgeStats`, `RosterContext`. Each gets one
      line: `model_config = ConfigDict(extra="forbid")`.
      (b) **Remove from `PerAssetValue`** — restore symmetric "accept extras
      silently" posture across all sub-models.
      Prefer (a) — defense-in-depth wins; the cost is one line per model
      and a verification that no test constructs these models with stray
      keys.

<!-- deepen-plan: codebase -->
> **Codebase:** All six target models (`ValueMath`, `PositionDepthChange`,
> `PickInventorySummary`, `AgeStats`, `RosterContext`,
> `ValueSourceBreakdown`) are constructed only inside `pipelines.py` via
> explicit keyword arguments — no `**kwargs` from external sources, no
> dict-unpacking. Grep of `tests/` found no direct constructions of these
> models. Applying `extra='forbid'` is mechanically safe.
<!-- /deepen-plan -->

<!-- deepen-plan: external -->
> **Research:** Per Pydantic v2 docs, `extra='forbid'` only fires at
> construction (`Model(**dict)`). It does NOT block direct attribute
> assignment (`m.foo = x` succeeds silently in v2) and is skipped by
> `model_construct()` (the validation-bypassing factory). So option (a)
> protects against the dict-construction path used by `pipelines.py` but
> not against mutation. On the shared-base-class question, Pydantic docs
> recommend **explicit per-model `model_config`** over inheritance — the
> implicit-strictness-via-inheritance pattern can surprise child authors
> who partially override `model_config`. Recommend keeping option (a) with
> 6 explicit `model_config = ConfigDict(extra='forbid')` lines rather than
> introducing a `StrictModel` base. See
> https://docs.pydantic.dev/latest/concepts/config/.
<!-- /deepen-plan -->
- [ ] 3.2: Run pytest and verify no test breaks. If any test passes extra
      keys to one of these models, either update the test or revert the
      change on that model.
- [ ] 3.3: Phase 3 gate — full suite + ruff clean.

### Phase 4: Ship

- [ ] 4.1: Commit and submit stacked PR. Recommend three commits matching
      the three phases for reviewability.

## Technical Details

### Files to Modify

- `src/yellow_sleeper/analyze/pipelines.py` — 1.5 (remove dead call), 2.3
  (clamp), import cleanup
- `src/yellow_sleeper/models/trade.py` — 2.1, 2.2, 3.1
- `src/yellow_sleeper/models/values.py` — 3.1 (`ValueSourceBreakdown`)
- `tests/conftest.py` — 1.1 (already has `sleeper_snapshot`), 1.2
  (`players`), 1.3 (`values`), 1.4 (`fresh_cache_statuses`)
- `tests/unit/test_pipelines_analyze_trade.py` — 1.1, 1.2, 1.3
- `tests/unit/test_pipelines_whats_on_the_clock.py` — 1.1, 1.2
- `tests/unit/test_pipelines_league_power_map.py` — 1.1, 1.2, 1.3
- `tests/unit/test_pipelines_health_check.py` — 1.4
- `tests/unit/test_pipelines_refresh_cache.py` — 1.4
- `tests/unit/test_model_invariants.py` — 2.4 (extend with new cases)

### Files to Create

- `tests/unit/_helpers.py` — only if 1.4 chooses module-constant route
  rather than conftest fixture. Recommend conftest route to avoid a new
  file.

### Dependencies

None. All work uses existing Pydantic v2 + pytest.

## Testing Strategy

- Each phase has its own pytest gate.
- Phase 1 changes must keep all 72 existing tests passing without
  modification beyond the parameter-name renames (`snapshot` →
  `sleeper_snapshot`).
- Phase 2 adds 2-3 new tests in `test_model_invariants.py` exercising the
  new validators (positive + negative cases).
- Phase 3 is verified by running the suite — if a test constructs a model
  with extra keys, that test breaks and either gets fixed or the model
  reverts.

## Acceptance Criteria

1. `ValueMath.source_disagreement` is no longer set by a guaranteed-empty
   computation (1.5).
2. `PerAssetValue` rejects `asset=None, value=non-None` and
   `value != sources[0].value` (when single enabled source) at construction
   time (2.1, 2.2).
3. No test file declares a `snapshot`, `players`, or `values` fixture
   locally; all use conftest-level fixtures (1.1, 1.2, 1.3).
4. Only one helper for "all cache keys are fresh" exists across the test
   suite (1.4).
5. `ConfigDict(extra="forbid")` is either present on every output sub-model
   or absent from all (3.1).
6. Pytest 72/72 → 75±/75± passing (phase 2 adds 2-3 tests); ruff clean.

## Edge Cases & Notes

- **2.3 reconciliation.** ~~The `_adjust_pick_count` negative-floor item
  conflicts with `_validate_delta`.~~ Superseded — codebase research
  confirmed no conflict exists (see Problem Statement annotation on item
  5). The remaining semantic question is whether "send a pick you don't
  own" should silently no-op (current behavior + clamp) or raise upstream.
  Within this PR's scope, silent no-op is acceptable; document the
  behavior near the clamp.
- **2.2 design choice.** The `value == sources[0].value when single enabled
  source` invariant is currently true by construction. If a future code
  path averages multiple enabled sources, this invariant must change. Add
  the validator now, but keep its scope narrow (only fire when there's
  exactly one enabled source) so future expansion is non-breaking.
- **3.1 false sense of strictness.** `extra='forbid'` only protects against
  dict-style construction (`Model(**raw_dict)`); direct attribute
  assignment (`m.foo = "extra"`) is allowed regardless. Pipelines use the
  former exclusively. Document this limitation if not already noted.

## References

- PR #2: `agent/feat/review-followup-type-invariants` review summary
  (multi-agent sweep, 12 reviewers, 4-5 reviewer consensus on each item)
- `plans/review-followup-type-invariants-and-pipeline-tests.md` — parent
  plan from PR #2; this plan addresses what was deliberately left out
- `tests/conftest.py:16-23` — existing `sleeper_snapshot` fixture
- `src/yellow_sleeper/models/trade.py:12-15` — `PerAssetValue` definition
  (the model whose invariants are being tightened)
- `src/yellow_sleeper/analyze/pipelines.py:880-915` — `_trade_value_math`
  including the dead `source_disagreement` per-asset call
- `src/yellow_sleeper/analyze/pipelines.py:1011-1049` —
  `_pick_inventory_summary` and `_adjust_pick_count` (the
  negative-floor site)

<!-- deepen-plan: external -->
> **Research — external documentation:**
> - Pydantic v2 Validators: https://docs.pydantic.dev/latest/concepts/validators/
>   — `model_validator` modes, validator ordering, cross-field patterns
> - Pydantic v2 Config: https://docs.pydantic.dev/latest/concepts/config/
>   — `ConfigDict(extra='forbid')` semantics, model_config inheritance
> - pytest Fixtures Reference:
>   https://docs.pytest.org/en/stable/reference/fixtures.html — conftest.py
>   discovery hierarchy, fixture scope tradeoffs
<!-- /deepen-plan -->
