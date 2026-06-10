# Build: Cross-slice integration pass — globalid_encoding / 0.0.9 (031)

Spec source: `docs/spec-031-globalid_encoding-0_0_9.md`
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md`
Artifact: `docs/builder/bld-integration.md`
Status: final-accepted

> **Worker 1 final-verification update (2026-06-10, round 2):** all three
> integration findings — M1 (double-walk regression), L1 (`products/schema.py`
> Slice-4 TODO), and L2 (`test_relay_interfaces.py` Slices-2-3 TODO) — are
> confirmed RESOLVED against the working tree. The repo-wide `TODO(spec-031`
> grep (scratch dirs excluded) returns ZERO matches, the cross-slice DRY verdict
> holds, the public surface is unchanged, and the focused integration suite is
> `322 passed`. Status set to `final-accepted`; see
> `## Final verification (Worker 1, integration — round 2)` at the bottom of this
> file. The build is clear for the final test-run gate (`bld-final.md`).

`Status: final-accepted` (set at round-2 final verification, bottom of this
file). The original pass found one cross-slice regression (M1, a red package
test) plus one stale source-site TODO (L1); the round-1 finalize surfaced a
second stale TODO (L2). All three were resolved across two Worker-2
consolidation passes (each followed by a Worker-3 review). Everything else — the
DRY single-source of the strategy frozensets, the one-way import direction, the
unchanged public surface, the uniform `ConfigurationError` error handling — was
clean throughout. The build is integration-clean and clear for the final
test-run gate.

All five spec slices reached `final-accepted` (build plan checklist boxes
1-5 `- [x]`). This pass walks the cross-slice surface per BUILD.md
"Cross-slice integration pass".

---

## The 5 mandatory pre-write steps (BUILD.md)

### Pre-step 1 — read every `bld-slice-*.md` in slice order

Read all five in order (1→2→3→4→5), full back-and-forth (plan / build / review /
final-verification) for each. Carry-forwards walked: every slice's
`What looks solid`, `DRY findings`, and `Notes for Worker 1`. Key findings folded
into this pass:

- **Slice 2** (`Notes for Worker 1`): observed the Slice-4 example-suite blast
  radius (default flip + Decision-13 filter break the live filter-input
  assertions) and flagged the `TYPE_NAME_STRATEGIES` DRY follow-up for Slice 3.
  Both were correctly deferred and both landed (Slice 4 re-greened the example
  suite; Slice 3 introduced `TYPE_NAME_STRATEGIES`).
- **Slice 3** (`Notes for Worker 1`): explicitly routed the
  `test_audit_runs_once_per_build` regression here, naming the root cause
  (Slice-2's second `models_with_multiple_types()` caller) and the two candidate
  fixes (bump test to `== 2` vs. consolidate the walk). Resolved below — the
  consolidation is the root-cause fix; the test bump is the surface patch and is
  rejected.
- **Slice 4** (`Spec changes made`): the line-102 `TODAY.md`-ownership spec
  reconciliation (TODAY.md edits are Slice-5-owned, Slice 4 is
  `examples/fakeshop/test_query/`-only) — already landed at Slice-4 planning, no
  integration action.
- **Slice 5** (`Notes for Worker 1` / final verification): the
  `check_spec_glossary` spec-body-link gap was a Worker-1-only spec edit, made at
  Slice-5 final verification (check now `OK: 31 terms`). No integration action.

### Pre-step 2 — static-inspection helper run for every touched Python file

Refreshed shadow output for the whole package: `uv run python
scripts/review_inspect.py --all --output-dir docs/shadow` → 45 files written
under `docs/shadow/` (build-cycle invocation passes `--output-dir docs/shadow`
per BUILD.md). This covers every reviewable file the build touched:
`types/base.py`, `types/definition.py`, `types/relay.py`, `types/finalizer.py`,
`registry.py`, `filters/base.py`, `filters/inputs.py`. No file with
review-worthy logic was skipped. (Per-slice helper runs were already recorded:
Slice 1 / 2 / 3 each ran it on the `types/` + `registry.py` files they touched;
Slice 4 correctly skipped it — `examples/fakeshop/test_query/` test files only;
Slice 5 correctly skipped it — no package `.py` source.)

### Pre-step 3 — Repeated string literals cross-slice comparison

Walked the **Repeated string literals** section of every touched file's shadow
overview. The cross-slice DRY signal that matters for this build is the GlobalID
**strategy vocabulary** (`model` / `type` / `type+model` / `callable` / `custom`).
Findings:

- `types/relay.py`: `2x type+model` — the **two frozenset definitions**
  `MODEL_LABEL_STRATEGIES = frozenset({"model", "type+model"})` and
  `TYPE_NAME_STRATEGIES = frozenset({"type", "type+model"})` (relay.py:385-386).
  These are the single-source definitions, NOT duplication — `type+model` is a
  member of both legitimate sets.
- `types/base.py`: `2x globalid_strategy` (the ALLOWED-key string + the
  validator) and the distinct `STRING_GLOBALID_STRATEGIES = frozenset({"model",
  "type", "type+model"})` (base.py:85) — the validation vocabulary, a
  deliberately different set from the model-label-emitting subset.
- `types/definition.py`, `registry.py`: `None`.
- `filters/base.py`: `2x bound_filterset` (unrelated to GlobalID).
- A repo-wide grep for any parallel literal strategy set
  (`{"model", ...}` / `("type", "type+model")` / `{"type", "type+model"}`)
  across `django_strawberry_framework/` returns **only** the three single-source
  frozenset definitions above plus docstring/comment mentions (definition.py:72/79,
  relay.py:380-381/419 comments). The one other `{"model", "fields"}` hit
  (`filters/factories.py:248`) is an unrelated `Meta`-key exclusion set, not a
  GlobalID strategy set.

**Verdict: the strategy frozensets are genuinely single-sourced** — no parallel
literal strategy set survives anywhere. See `### Integration check: repeated
literals / strategy frozensets` below for the full single-source map.

### Pre-step 4 — Imports cross-slice comparison (dependency direction)

Walked the **Imports** section of every touched file's shadow overview.

- **`types/relay.py` module-top imports** (lines 23-39): stdlib / django /
  strawberry / `..exceptions` / `.definition` (TYPE_CHECKING only). It does
  **NOT** import `filters` or `registry` at module top. The reverse-direction
  reads it needs are all **in-function**: `..registry` at relay.py:607 (inside
  `decode_global_id`), `..conf` + `.base` at relay.py:355-356 (inside
  `_resolve_globalid_strategy`). Confirmed: relay.py reaches `filters`/`registry`
  only in-function. ✓ (spec-required check)
- **`filters/base.py`** imports `MODEL_LABEL_STRATEGIES, TYPE_NAME_STRATEGIES`
  from `..types.relay` at **module top** (base.py:44). This is the documented
  safe direction (`filters → types`); since `types/relay.py` has no module-top
  reverse import, it is acyclic. Worker 3 (Slices 2/3) verified the imported
  frozensets are the **same object** across the boundary (`is`-identity, a
  re-export, not a copy). ✓
- **`registry.py`** imports `implements_relay_node` from `.types.relay`
  **in-function** (registry.py:343, inside `definition_for_graphql_name`),
  dodging the `registry ↔ relay` coupling (registry is imported very early). ✓
- **`finalizer.py`** imports the audit predicates `_accepts_model_label_decode,
  _emits_model_label, install_globalid_typename_resolver` from `.relay` at module
  top (finalizer.py:59) — `types → types`, fine; `..filters` / `..orders` are
  only in-function (finalizer.py:764-766, 871-873). ✓

**Verdict: one-way dependency direction holds** (`filters → types`,
`registry → types` in-function). No sibling imports outside the documented
boundary.

### Pre-step 5 — deferred-follow-up walk across accepted slice artifacts

Walked every accepted slice's `What looks solid` / `DRY findings` /
`Notes for Worker 1`. The only deferred follow-up that must land in THIS pass is
the routed regression (Slice 3's `Notes for Worker 1`). The
`TYPE_NAME_STRATEGIES` DRY follow-up (Slice 2 → Slice 3) already landed in Slice
3. The TODAY.md-ownership reconciliation (Slice 4) and the spec-body-link edit
(Slice 5) already landed. Genuine sibling-card / maintainer deferrals are
cataloged under `### Deferred work catalog`.

---

## Integration findings (by severity)

### Medium

#### M1 — Cross-slice regression: `models_with_multiple_types()` is walked twice per finalize (routed)

`tests/test_registry.py::test_audit_runs_once_per_build` FAILS (`assert 2 == 1`).
Confirmed by focused run (no `--cov`): `uv run pytest
tests/test_registry.py::test_audit_runs_once_per_build --no-cov` → `assert 2 == 1`
(`+ where 2 = len([None, None])`). Across the four GlobalID-touching package
suites (`test_registry.py`, `test_relay_interfaces.py`, `test_base.py`,
`test_filters/test_base.py`) this is the **sole** failure: `1 failed, 321
passed`.

**Severity:** Medium. This is precisely the BUILD.md integration check "repeated
ORM/queryset patterns that should be centralized" — a per-finalize registry walk
duplicated across two audit call sites — and it red-tests the suite, so the final
test-run gate would trip on it.

**Root cause (cross-slice).** Slice 2 added a SECOND
`registry.models_with_multiple_types()` caller per finalize:

- Phase-1 caller: `types/finalizer.py::_audit_primary_ambiguity` (finalizer.py:139,
  invoked at finalizer.py:269).
- Phase-2.5 caller (NEW in Slice 2):
  `types/finalizer.py::_audit_model_label_routing` (finalizer.py:200, invoked at
  finalizer.py:346).

`test_audit_runs_once_per_build` (test_registry.py:1210-1235) monkeypatches the
bound method `registry.models_with_multiple_types` with a `spy` that appends to a
`calls` list, runs `finalize_django_types()` twice (the second call hits the
`is_finalized()` short-circuit), and asserts `len(calls) == 1` — i.e. the
multi-type-model walk happens exactly once per build. With two audit callers per
finalize, the spy fires twice in the first finalize → `assert 2 == 1`.

**Recommended fix: root-cause consolidation, NOT the test bump.** Per AGENTS.md
("always recommend the root-cause fix over the surface patch"): compute the
multi-type-model set ONCE per finalize and share it to BOTH audits, preserving
the Phase-1 / Phase-2.5 ordering and keeping the two `raise` sites separate. This
restores the test's `== 1` "once per build" invariant AND centralizes the
duplicated registry walk (the actual DRY defect). **Do NOT bump the assertion to
`== 2`** — that is the surface patch the spec/AGENTS.md forbids; it would leave
the duplicated walk in place and re-label the symptom as expected. The precise
shape is pinned under `### Worker-2 consolidation contract` below.

**Feasibility verified** (read the two call sites + `registry.py`):

- `_audit_primary_ambiguity` (finalizer.py:120-145) iterates
  `registry.models_with_multiple_types()`, collecting `(model,
  registry.types_for(model))` where `registry.primary_for(model) is None`; raises
  `_format_ambiguity_error(offenders)`.
- `_audit_model_label_routing` (finalizer.py:177-211) iterates the SAME
  `registry.models_with_multiple_types()`, and for each model calls
  `_first_model_label_emitter(model)` (finalizer.py:214-226, which itself iterates
  `registry.types_for(model)`), then reads `registry.primary_for(model)` and the
  primary's `effective_globalid_strategy`; raises
  `_format_model_label_routing_error(offenders)`.
- `registry.models_with_multiple_types` (registry.py:253-259) returns a **lazy
  generator** `(model for model, types in self._types.items() if len(types) >=
  2)`. The two audits run in different phases (1 and 2.5) and the generator is
  one-shot, so each call site re-invokes it today — hence two spy hits. The
  consolidation must materialize the walk once (a `tuple`/`list`) and pass it to
  both audits.

This is feasible with a small, behavior-preserving refactor (pass the
materialized model list into both audit functions, or have `finalize_django_types`
compute it once and hand it down). Requires Worker 2 to touch
`types/finalizer.py` only.

### Low

#### L1 — Stale `TODO(spec-031...Slice 4)` marker left in `examples/fakeshop/apps/products/schema.py`

`examples/fakeshop/apps/products/schema.py:93-99` still carries:

```text
# TODO(spec-031-globalid_encoding-0_0_9 Slice 4): If the live HTTP
# ``type``-strategy opt-out test is clearer with a schema fixture than
# a settings override, add ``globalid_strategy = "type"`` to one
# dedicated fakeshop type in the same change that updates the expected
# GlobalID payloads.
# Pseudocode:
#   globalid_strategy = "type"  # noqa: ERA001
```

This marker anchors the **alternative** Slice-4 opt-out approach (a dedicated
schema-fixture type) that Slice 4 did **not** take — Slice 4 used the spec's
preferred shape (`override_settings(DJANGO_STRAWBERRY_FRAMEWORK=
{"RELAY_GLOBALID_STRATEGY": "type"})` + the extracted reload helper, spec Risks
P3, confirmed at `examples/fakeshop/test_query/test_products_api.py:169-170`). No
fakeshop type carries `globalid_strategy = "type"` (only this commented
pseudocode). Per AGENTS.md (#26: staged-slice TODO comments are "removed in the
same change that ships the slice") and the integration check "confirm all
`TODO(spec-031...)` markers that the build's slices were meant to resolve are
gone", this marker's work is fully resolved by the chosen Slice-4 path and should
have been removed. It is the ONLY remaining `TODO(spec-031...)` marker in package
source / example schema (verified by grep). **Severity: Low** — a stale,
non-load-bearing comment (it would also trip an `ERA001`-style "commented-out
code" smell on a future sweep). The sibling commented Layer-3 lines
(`search_fields`/`aggregate_class`/`fields_class`/`get_queryset`) in the same
`Meta` block legitimately belong to sibling cards (039/040/038/027) and are NOT
this card's concern — they stay.

Worker 2 should remove lines 93-99 (the spec-031 Slice-4 TODO block only) in the
consolidation pass while it is already touching the build.

---

## Integration checks (BUILD.md)

### Duplicated helpers across slices

One genuine duplication: the `models_with_multiple_types()` walk across the two
finalizer audits (M1). No other duplicated helper — the `_format_*_error` /
`_audit_*` pattern is the deliberate finalizer house style (each audit owns one
invariant + one message builder), and the GlobalID encode/decode helpers are each
single-sited (`encode_typename`, `install_globalid_typename_resolver`,
`decode_global_id`, `definition_for_graphql_name`).

### Inconsistent naming / error handling between slices

Clean. Every decode / encode / audit / validation failure introduced by the build
is a uniform `ConfigurationError` (the package's finalize-time / type-creation
error contract):

- type-creation: `_validate_globalid_strategy` (unknown string, wrong type,
  callable arity/sync, non-Relay gate) → `ConfigurationError` (Slice 1).
- finalization: `_resolve_globalid_strategy` setting validation, the both-declared
  override+`Meta` conflict, the non-`str`/empty callable return, the
  model-label-routing audit → `ConfigurationError` (Slice 2).
- decode: input-type gate, malformed-parse (`GlobalIDValueError ⊂ ValueError`
  caught), empty-slot, unresolvable label, absent-strategy, strategy-shape
  rejection → one uniform `ConfigurationError` (Slice 3).
- filter: wrong-model/type mismatch stays the existing `GraphQLError("GlobalID
  type mismatch: ...")` (the filter is request-time, not finalize-time — correctly
  a `GraphQLError`, not `ConfigurationError`); the node-id-only fallback for
  `callable`/`custom`/`None` is defense-in-depth, never raises (Slice 2,
  Decision 13).

The naming is consistent across slices: `MODEL_LABEL_STRATEGIES` /
`TYPE_NAME_STRATEGIES` / `STRING_GLOBALID_STRATEGIES` (the three sets),
`effective_globalid_strategy` (the recorded field) vs. `globalid_strategy` (the
raw slot) — the distinction is documented in `definition.py` and used uniformly
by encode (reads/records `effective_*`), decode (reads `effective_*`), and the
filter (reads `effective_*`).

### Repeated ORM/queryset patterns that should be centralized

The `models_with_multiple_types()` double-walk (M1) — the exact pattern this
check targets. No other repeated ORM pattern: `decode_global_id`'s
`apps.get_model(...)` is a single in-memory app-registry lookup (no query, no
N+1, per Slice-3 shadow walk), and `registry.get` / `get_definition` /
`definition_for_graphql_name` are in-memory dict reads.

### Misplaced responsibilities between modules

Clean. Encode/decode live in `types/relay.py` (the Relay foundation module, spec
Decision 11 — no new module); the strategy→payload-shape source of truth
(`MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` + predicates) lives in
`types/relay.py` (the encode home) and is consumed by the finalizer audit and the
filter via one-way imports; `definition_for_graphql_name` lives in `registry.py`
(the registry owns name→definition lookup); the raw `globalid_strategy` slot +
recorded `effective_globalid_strategy` live on `DjangoTypeDefinition`; validation
lives in `types/base.py` (alongside `_validate_connection`). No responsibility is
split across the wrong module.

### Missing or too-broad exports introduced by the build

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` is
unchanged. Confirmed per Decision 11 ("no new public exports in 0.0.9"):
`decode_global_id`, `encode_typename`, `install_globalid_typename_resolver`,
`MODEL_LABEL_STRATEGIES`, `TYPE_NAME_STRATEGIES`, `STRING_GLOBALID_STRATEGIES`,
`DEFAULT_GLOBALID_STRATEGY`, and `definition_for_graphql_name` are all internal
(none added to `__all__`). The public `testing/relay` helpers ship with sibling
card 032. No export drift.

### Repeated string literals / dict keys / tuple shapes across slices (strategy frozensets)

**The single-source strategy frozensets are genuinely the ONE source consumed by
encoder + decoder + the model-label-routing audit + the strategy-aware filter; no
parallel literal `{"model",...}` / `("type","type+model")` sets remain anywhere.**
Single-source map:

| Symbol | Defined once at | Consumed by |
|---|---|---|
| `MODEL_LABEL_STRATEGIES = frozenset({"model", "type+model"})` | `types/relay.py:385` | encoder `encode_typename` (relay.py:460); predicates `_emits_model_label` (relay.py:396) / `_accepts_model_label_decode` (relay.py:409) → finalizer audit (`_audit_model_label_routing` / `_first_model_label_emitter`); decode Step-2 (Slice 3); filter `_accepted_globalid_type_names` (filters/base.py:243) |
| `TYPE_NAME_STRATEGIES = frozenset({"type", "type+model"})` | `types/relay.py:386` | predicate `_accepts_type_name_decode` (relay.py:422) → decode Step-2 (Slice 3); filter `_accepted_globalid_type_names` (filters/base.py:245) |
| `STRING_GLOBALID_STRATEGIES = frozenset({"model", "type", "type+model"})` | `types/base.py:85` | validation vocabulary in `_validate_globalid_strategy` (Slice 1) — a deliberately distinct set (all valid strings) from the model-label-emitting subset |

The `callable` / `custom` "no framework decode" contract correctly **falls out of
predicate math** (a candidate in neither `MODEL_LABEL_STRATEGIES` nor
`TYPE_NAME_STRATEGIES` is rejected) — there is NO `{"callable", "custom"}` literal
anywhere (verified by grep; Slice-3 review confirmed). `filters/base.py` binds the
SAME frozenset objects via the module-top re-export (`is`-identity, not a copy).
This is exemplary on the build's headline DRY watch point.

### Comments tell one coherent story / TODO markers resolved

Mostly coherent. The encode/decode/audit comments across `types/relay.py`,
`types/finalizer.py`, `registry.py`, `filters/base.py`, and `definition.py` tell
one consistent story (the strategy→payload-shape single source, the recorded
`effective_globalid_strategy`, the re-entrancy guard, the phase placement). The
`STRING_GLOBALID_STRATEGIES` vs `MODEL_LABEL_STRATEGIES` vs `TYPE_NAME_STRATEGIES`
distinction is documented at each definition.

**Exception — L1:** the one remaining `TODO(spec-031...Slice 4)` marker
(`examples/fakeshop/apps/products/schema.py:93-99`) is stale and should be removed
(see L1). All OTHER spec-031 source mentions are legitimate spec-reference
comments (`spec-031 Decision N`), not TODO markers. The remaining commented
Layer-3 lines in `products/schema.py` (`search_fields` / `aggregate_class` /
`fields_class` / `get_queryset`) legitimately belong to sibling cards
(039/040/038/027), not this card.

---

## Worker-2 consolidation contract

Worker 0 dispatches Worker 2 for one consolidation pass (then Worker 3 review).
Two items, both in scope, both small. **Files Worker 2 may touch:**
`django_strawberry_framework/types/finalizer.py` (M1) and
`examples/fakeshop/apps/products/schema.py` (L1). No test edits beyond what M1's
behavior preservation requires — and `test_audit_runs_once_per_build` must NOT be
edited (its `== 1` assertion is the invariant the fix restores).

### M1 — share ONE `models_with_multiple_types()` walk across both audits

**Goal:** compute the multi-type-model set ONCE per `finalize_django_types()` call
and pass it to both `_audit_primary_ambiguity` and `_audit_model_label_routing`,
so `registry.models_with_multiple_types` is invoked exactly once per build (the
test's `== 1` invariant) while keeping the two audits' distinct logic, phase
ordering, and separate `raise` sites.

**Exact shape (recommended):**

1. In `finalize_django_types()` (finalizer.py:229-357), after the
   `if registry.is_finalized(): return` short-circuit (finalizer.py:266-267) and
   BEFORE the Phase-1 `_audit_primary_ambiguity()` call (finalizer.py:269),
   materialize the walk once:
   ```python
   multi_type_models = tuple(registry.models_with_multiple_types())
   ```
   `models_with_multiple_types()` returns a lazy generator (registry.py:259), so
   materialize to a `tuple` (it is iterated by both audits and once is enough).
   This is the SINGLE invocation per finalize.
2. Change `_audit_primary_ambiguity()` →
   `_audit_primary_ambiguity(multi_type_models)`: accept the materialized models
   as a parameter and iterate it instead of re-calling
   `registry.models_with_multiple_types()` at finalizer.py:139. Body otherwise
   UNCHANGED (still collects `(model, registry.types_for(model))` where
   `registry.primary_for(model) is None`, sorts by `model.__name__`, raises
   `_format_ambiguity_error`). Update the call site at finalizer.py:269 to pass
   `multi_type_models`. Update the docstring's "Walks
   `registry.models_with_multiple_types()`" sentence to "Walks the
   pre-materialized multi-type-model list" (the once-per-build guarantee now lives
   in `finalize_django_types`, which the docstring should note).
3. Change `_audit_model_label_routing()` →
   `_audit_model_label_routing(multi_type_models)`: accept the same parameter and
   iterate it instead of re-calling `registry.models_with_multiple_types()` at
   finalizer.py:200. Body otherwise UNCHANGED (still calls
   `_first_model_label_emitter(model)`, reads `registry.primary_for(model)` + its
   `effective_globalid_strategy`, sorts, raises
   `_format_model_label_routing_error`). Update the call site at finalizer.py:346
   to pass `multi_type_models`. `_first_model_label_emitter` (finalizer.py:214) is
   UNCHANGED — it iterates `registry.types_for(model)`, NOT
   `models_with_multiple_types()`, so it does not contribute to the spy count.

**Load-bearing invariants Worker 2 MUST preserve:**

- **Once-per-build.** After the fix, `registry.models_with_multiple_types` is
  called exactly ONCE per `finalize_django_types()` invocation (the single
  materialization in step 1). The second `finalize_django_types()` call still
  hits `is_finalized()` and never reaches the materialization, so the spy count
  stays 1 across two finalize calls — `test_audit_runs_once_per_build` (`== 1`)
  passes UNCHANGED.
- **Phase ordering.** `_audit_primary_ambiguity` still runs at Phase-1 top
  (finalizer.py:269, before pending-relation resolution — the failure-atomic
  placement, M1 of the prior audit's spec); `_audit_model_label_routing` still
  runs at Phase 2.5 (finalizer.py:346, AFTER the Relay loop records every
  `effective_globalid_strategy` and BEFORE Phase-3 `finalized = True` /
  `mark_finalized()`). Do NOT merge the two audits into one walk-with-two-checks;
  they MUST stay two separate functions with two separate `raise` sites at their
  two phases (the Phase-1 ambiguity audit guarantees a primary exists, which the
  Phase-2.5 routing audit relies on via `registry.primary_for(model)`).
- **Failure-atomicity of the materialization.** Computing `multi_type_models`
  before `_audit_primary_ambiguity` is a pure read (no class mutation), so it does
  not disturb Phase-1's failure-atomic contract.
- **Re-entrancy.** A Phase-2.5 raise (e.g. the routing audit) leaves
  `finalized = False`; a re-run re-enters `finalize_django_types`, re-checks
  `is_finalized()` (still `False`), and re-materializes `multi_type_models` once
  — so the spy count on a clean single finalize is 1; the existing re-entrancy
  test (`test_finalize_rerun_after_audit_raise_preserves_recorded_strategy`)
  asserts recordings survive, which the materialization does not affect.

**Do NOT:** edit `test_audit_runs_once_per_build` (no `== 2` bump — that is the
rejected surface patch); merge the two audits; change `models_with_multiple_types`
in `registry.py` (it is correct — the duplication is at the finalizer call sites,
not the registry method).

**Verification Worker 2/3 run (no `--cov*`):**
`uv run pytest tests/test_registry.py tests/types/test_relay_interfaces.py
tests/types/test_base.py tests/filters/test_base.py --no-cov` → must be all green
(was `1 failed, 321 passed`; target `322 passed`).

### L1 — remove the stale Slice-4 TODO block

Remove `examples/fakeshop/apps/products/schema.py:93-99` (the
`# TODO(spec-031-globalid_encoding-0_0_9 Slice 4): ...` block and its `Pseudocode:`
two lines only). Leave the surrounding `Meta` block, the
`filterset_class`/`orderset_class` lines, and the sibling commented Layer-3 lines
(`search_fields`/`aggregate_class`/`fields_class`) and the commented
`get_queryset` block untouched — those belong to sibling cards 039/040/038/027.
After removal, run `uv run ruff format examples/fakeshop/apps/products/schema.py`
+ `uv run ruff check examples/fakeshop/apps/products/schema.py` and confirm
`uv run python examples/fakeshop/manage.py check` stays clean.

---

## Deferred work catalog (integration-relevant)

Items legitimately deferred to sibling cards / maintainer follow-up
(the formal full catalog lives in `bld-final.md` per BUILD.md; this lists the
integration-relevant deferrals):

- **Callable / `custom` decode path → `WIP-ALPHA-032-0.0.9` (Full Relay story).**
  `callable` and `custom` (consumer `resolve_typename` override) effective
  strategies are **encode-only** in 0.0.9 — they have no `decode_global_id`
  branch (fall out of the predicate math; spec Decision 4/8). A consumer-owned
  paired decoder is deferred to card 032. (Source: Slice-3 artifact; spec
  Decision 8 / line 418.)
- **First consumer of `decode_global_id` / `definition_for_graphql_name` →
  `WIP-ALPHA-032-0.0.9`.** Both helpers are internal forward-looking surfaces with
  no shipped 0.0.9 caller; root `node(id:)` / `nodes(ids:)` in card 032 is their
  first consumer (spec Decision 8 / 11; intentional — the latent breaking-default
  flip is undecodable until 032 ships, per the CHANGELOG `[Unreleased]` note).
- **Connection-aware optimizer planning → `WIP-ALPHA-033-0.0.9`.** Orthogonal to
  this card (the GlobalID payload does not change connection-walker work);
  `DjangoConnectionField`'s `edges { node { id } }` picks up the model-label
  payload through the same `resolve_typename` seam with no `connection.py` change.
- **`type+model` is a strategy bridge, NOT a rename-history alias map → BACKLOG
  item 39.** `type+model` decodes an old type-anchored ID only while its GraphQL
  type name still resolves; a full rename-history alias map is post-1.0.0
  (documented in CHANGELOG `[Unreleased]` + TODAY.md, Slice 5).
- **Joint `0.0.9` version cut (NOT this card) → maintainer.** `pyproject.toml`,
  `__version__`, `tests/base/test_init.py::test_version`, `uv.lock` stay at
  `0.0.8`; no `## [0.0.9]` CHANGELOG heading promotion. The version bump is owned
  by the joint cut across cards 029/030/031/032/033 (spec Decision 12). On-disk
  version is correctly still `0.0.8`.

No spec-031 in-card work is deferred — the five slices delivered the full spec
contract end-to-end; only the M1 consolidation + L1 cleanup remain before the
final gate, and both are this-build integration work, not deferrals.

---

## Spec changes made (Worker 1 only)

None. No spec gap, conflict, or inaccuracy surfaced during the integration pass.
Per-spawn spec status-line re-verification (spec lines 1-9): the `Status: planned
— not started` line + the unticked `## Slice checklist` are the intentional
contract record (spec line 5: "The Slice checklist below stays unticked as the
contract record (build progress is tracked in the build plan, not here)") — not a
build tracker; no header edit required. No predecessor reference broke. (The
Slice-4 line-102 TODAY.md-ownership edit and the Slice-5 spec-body-link edit were
already made and recorded in their own slice artifacts.)

---

## Outcome

`Status: revision-needed`. Worker 0 must dispatch a Worker 2 consolidation pass
(M1 + L1 per `### Worker-2 consolidation contract`) followed by a Worker 3 review,
then re-run this integration pass to confirm clean before the final test-run gate.
The build is otherwise integration-clean: strategy frozensets single-sourced,
imports one-way, public surface unchanged, error handling uniform.

---

## Build report (Worker 2)

Consolidation pass implementing the two integration findings (M1 + L1) per the
`### Worker-2 consolidation contract` above. No spec-slice verbatim checklist
exists on this integration artifact, so there are no `- [ ]` boxes to tick.

### Files touched

- `django_strawberry_framework/types/finalizer.py` (M1) — root-cause
  consolidation of the duplicated `registry.models_with_multiple_types()` walk:
  - In `finalize_django_types()`, after the `if registry.is_finalized(): return`
    short-circuit and BEFORE the Phase-1 `_audit_primary_ambiguity()` call,
    materialize the walk once:
    `multi_type_models = tuple(registry.models_with_multiple_types())`. Added a
    comment explaining the once-per-finalize materialization and its
    failure-atomicity (pure read, does not disturb Phase 1).
  - `_audit_primary_ambiguity()` → `_audit_primary_ambiguity(multi_type_models)`:
    accepts the materialized tuple and iterates it instead of re-calling
    `registry.models_with_multiple_types()`. Body otherwise unchanged (still
    collects `(model, registry.types_for(model))` where
    `registry.primary_for(model) is None`, sorts by `model.__name__`, raises
    `_format_ambiguity_error`). Docstring updated: now walks "the pre-materialized
    multi-type-model list" and notes the once-per-build guarantee lives in
    `finalize_django_types`.
  - `_audit_model_label_routing()` →
    `_audit_model_label_routing(multi_type_models)`: accepts the same tuple and
    iterates it. Body otherwise unchanged (still calls
    `_first_model_label_emitter(model)`, reads `registry.primary_for(model)` + its
    `effective_globalid_strategy`, sorts, raises
    `_format_model_label_routing_error`). Docstring updated to note it shares the
    same materialized list.
  - Phase-2.5 call site updated to pass `multi_type_models`.
  - `_first_model_label_emitter` is UNCHANGED (it iterates
    `registry.types_for(model)`, not the spy'd method).
- `examples/fakeshop/apps/products/schema.py` (L1) — removed the stale
  `# TODO(spec-031-globalid_encoding-0_0_9 Slice 4): ...` block plus its
  `# Pseudocode:` two lines from `ItemType.Meta` (7 lines deleted, 0 inserted).
  The sibling commented Layer-3 lines (`search_fields` / `aggregate_class` /
  `fields_class` for cards 039/040/038) and the commented `get_queryset` block
  (card 027) are untouched.

### Tests added or updated

None. M1's contract is behavior-preserving and explicitly forbids editing
`test_audit_runs_once_per_build` (its `== 1` assertion is the invariant the fix
restores). The fix is proven green by the existing suite. L1 is a comment-only
removal with no test surface.

### Validation run

- `uv run ruff format .` — pass (235 files left unchanged; the `COM812`
  formatter-conflict line is the repo's pre-existing config warning, not an error
  introduced by this pass).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` after both ruff invocations — classification:
  - **Slice-intended (stay in the diff):**
    `django_strawberry_framework/types/finalizer.py`,
    `examples/fakeshop/apps/products/schema.py` — this pass's M1 + L1 edits.
  - **Expected cumulative Slice 1-5 accepted diff + Worker 1 spec edits (NOT this
    pass, NOT churn — do not revert):** `CHANGELOG.md`, `KANBAN.html`, `KANBAN.md`,
    `README.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`,
    `docs/spec-031-globalid_encoding-0_0_9.md`,
    `docs/spec-031-globalid_encoding-0_0_9-terms.csv`,
    `examples/fakeshop/db.sqlite3`, the four other touched package modules
    (`filters/base.py`, `filters/inputs.py`, `registry.py`, `types/base.py`,
    `types/definition.py`, `types/relay.py`), the three live test files
    (`test_kanban_api.py`, `test_library_api.py`, `test_products_api.py`), and the
    four package test files (`tests/filters/test_base.py`, `tests/test_registry.py`,
    `tests/types/test_base.py`, `tests/types/test_relay_interfaces.py`).
  - **Concurrent activity (leave untouched per AGENTS.md #33):**
    `docs/dry/dry-0_0_9.md` (concurrent DRY cycle).
  - **Untracked build artifacts (the build cycle's own `bld-*` / `build-*` files):**
    the seven `docs/builder/*.md` build files.
  - **Unrelated tool churn introduced by this pass: none.** Ruff reformatted
    nothing; the two slice-intended files carry only the intended M1/L1 edits.
    Nothing to `git checkout --`.

### Focused test run (no `--cov*`)

`uv run pytest tests/test_registry.py tests/types/test_relay_interfaces.py
tests/types/test_base.py tests/filters/test_base.py --no-cov` →
**`322 passed`** (was `1 failed, 321 passed` before the fix; target `322 passed`
met). `tests/test_registry.py::test_audit_runs_once_per_build` confirmed green
individually (`1 passed`) — its `len(calls) == 1` assertion passes UNCHANGED, no
`== 2` bump. The once-per-build invariant is preserved.

### Implementation notes

- **Materialized as a `tuple`, not a `list`.** The contract's recommended shape
  is `tuple(...)`; the collection is read-only and iterated by both audits, so a
  tuple communicates the immutable, single-materialization intent. Iterating it
  twice (once per audit) is the whole point — one generator drain, two consumers.
- **Two audits stay two functions with two raise sites at their two phases.** Did
  NOT merge them into one walk-with-two-checks: Phase-1 `_audit_primary_ambiguity`
  (top, pre-pending-relation-resolution, failure-atomic) still guarantees a
  primary exists, which Phase-2.5 `_audit_model_label_routing` relies on via
  `registry.primary_for(model)`. Only the shared input changed, not the phase
  structure or the separate `ConfigurationError` raises.
- **`registry.py` untouched.** The `models_with_multiple_types()` generator is
  correct; the duplication was at the two finalizer call sites, so the fix lives
  entirely in `finalizer.py`.
- **L1 was a pure comment removal**, so no `noqa: ERA001` concern remains (the
  removed pseudocode line carried the only such suppression in that block).

### Notes for Worker 3

- M1 is behavior-preserving by construction: same iteration, same offender
  collection, same sort, same two raises, same two phases — only the source of
  the iterated model collection moved from two in-function generator calls to one
  materialized tuple passed as a parameter. The regression test
  `test_audit_runs_once_per_build` (`== 1`, unedited) is the gate.
- Re-entrancy is intact: a Phase-2.5 raise leaves `finalized = False`; a re-run
  re-enters `finalize_django_types`, re-checks `is_finalized()` (still `False`),
  and re-materializes `multi_type_models` once — so a clean single finalize still
  drains the generator exactly once.
- No shadow file was used for this pass (the change is a small, local
  parameter-threading refactor against the already-read `finalizer.py`).
- L1 removed only the spec-031 Slice-4 TODO block; sibling commented Layer-3
  lines for cards 039/040/038/027 are intentionally retained.

### Notes for Worker 1 (spec reconciliation)

None. No spec gap, conflict, or unstated assumption surfaced — the consolidation
matched the integration contract exactly and the spec needs no edit. M1 is a
root-cause DRY fix that preserves every documented invariant (once-per-build,
phase ordering, failure-atomicity, re-entrancy); L1 is the AGENTS.md #26
stale-staged-slice-TODO removal that should have shipped with Slice 4.

---

## Review (Worker 3, integration consolidation)

Reviewed Worker 2's consolidation diff (M1 + L1) against the `### Worker-2
consolidation contract` and the spec's two-audit / Phase-1+Phase-2.5 invariants
(Decisions 8/10). Diff scope: ONLY `django_strawberry_framework/types/finalizer.py`
(M1) and `examples/fakeshop/apps/products/schema.py` (L1). The cumulative Slice 1-5
diff + Worker 1's spec edits + the concurrent `docs/dry/dry-0_0_9.md` /
"archive 030" activity are out of scope and were not weighed (cumulative-diff trap
handled via the contract's described shape, not raw `git diff -- finalizer.py`,
which also carries Slice-2's accepted audit logic).

Static-inspection helper: RAN on `finalizer.py` per BUILD.md (the consolidation
touches a `types/` file). `uv run python scripts/review_inspect.py
django_strawberry_framework/types/finalizer.py --output-dir docs/shadow` →
overview written. `products/schema.py` is example config and the change is a pure
comment removal (no logic) — helper SKIPPED there (recorded reason: comment-only
deletion, no reviewable logic surface).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

**The original M1 double-walk is RESOLVED — the duplicated registry walk is now a
single walk.** Verified by grep: `registry.models_with_multiple_types()` appears
at exactly ONE executable call site in `finalizer.py` —
`multi_type_models = tuple(registry.models_with_multiple_types())`
(finalizer.py:283), sitting after the `if registry.is_finalized(): return`
short-circuit (finalizer.py:273-274) and before the Phase-1
`_audit_primary_ambiguity(multi_type_models)` call (finalizer.py:285). The four
other `models_with_multiple_types` hits in the file (finalizer.py:125, 138, 198,
278) are all docstring/comment mentions, not call sites. The control-flow hotspot
walk confirms the new `multi_type_models` materialization sits correctly between
the guard and Phase-1, and the Phase-2.5 routing audit
(`_audit_model_label_routing(multi_type_models)`, finalizer.py:363) reuses the
SAME tuple after the Relay loop and before Phase-3. No new duplication introduced.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is EMPTY. `__all__` and the
re-export list are unchanged. The consolidation is purely internal
(`finalizer.py` parameter threading + example-config comment removal). No public
export drift; consistent with Decision 11 ("no new public exports in 0.0.9").

### CHANGELOG sanity

Not applicable; consolidation did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; consolidation did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Root-cause fix, not surface patch.** The walk is materialized ONCE per
  finalize as a `tuple` and passed to BOTH audits — the highest-quality fix per
  AGENTS.md. The rejected `== 2` test bump was NOT taken.
- **Single call site (grep-verified).** `models_with_multiple_types()` invoked
  exactly once (finalizer.py:283). The registry generator
  (`registry.py::models_with_multiple_types`, a lazy
  `(model for model, types in ... if len(types) >= 2)`) is unchanged.
- **Tuple, not a bare generator.** `tuple(registry.models_with_multiple_types())`
  materializes the one-shot generator into a re-iterable sequence. This is the
  load-bearing correctness point: a generator passed to two audits would be
  exhausted by the first, silently skipping the routing audit. The tuple is
  iterated by both audits — proven correct below.
- **Two audits / two raises / two phases preserved.** `_audit_primary_ambiguity`
  (Phase-1 top, pre-pending-relation-resolution, failure-atomic — raises
  `_format_ambiguity_error`) and `_audit_model_label_routing` (Phase-2.5, after
  the Relay loop records every `effective_globalid_strategy`, before Phase-3 —
  raises `_format_model_label_routing_error`) remain two SEPARATE functions with
  two SEPARATE `ConfigurationError` raises at their two distinct phases. They were
  NOT merged. `_first_model_label_emitter` (finalizer.py:221) is untouched and
  iterates `registry.types_for(model)`, NOT `models_with_multiple_types()`, so it
  does not contribute to the spy count. Phase ordering matters: Phase-1 guarantees
  a primary exists, which Phase-2.5 relies on via `registry.primary_for(model)`.
- **Error handling / messages unchanged.** Same `ConfigurationError` raises, same
  message builders (`_format_ambiguity_error`, `_format_model_label_routing_error`).
  The fix is structural (input source moved from two in-function generator calls to
  one materialized tuple parameter), not behavioral.
- **`test_audit_runs_once_per_build` UNCHANGED.** The test's `assert len(calls)
  == 1` (test_registry.py:1235) is intact — verified the test was not bumped to
  `== 2`. The test's `tests/test_registry.py` diff-vs-HEAD reflects the cumulative
  accepted-slice changes (it predates Slice 1 at HEAD), NOT a consolidation edit;
  Worker 2's build report and the contract both classify it as accepted-slice
  diff, and the load-bearing assertion shape (`== 1`) and registry generator are
  exactly the accepted-slice forms the contract pinned. The spy wraps
  `registry.models_with_multiple_types`; with the single materialization it fires
  once across two finalize calls (second hits `is_finalized()`). Green
  individually and in the focused run.
- **L1 scoped exactly.** `products/schema.py` diff is `0 7` (numstat: 0 insertions,
  7 deletions) — only the spec-031 Slice-4 TODO block + its `Pseudocode:` lines
  removed from `ItemType.Meta`. Sibling commented Layer-3 lines
  (`search_fields`→039, `aggregate_class`→040, `fields_class`→038) and the
  commented `get_queryset` block (027) remain. No `globalid_strategy` assignment
  exists anywhere in `examples/fakeshop/` (grep). No `TODO(spec-031...)` markers
  remain anywhere in package source / example schema (grep).

### Temp test verification

No temp tests created (the empty scratch dir was removed). The
generator-exhaustion risk the contract flagged — the single highest-risk failure
mode — is already pinned by the PERMANENT suite and is green:

- `tests/types/test_relay_interfaces.py::test_model_label_routing_audit_rejects_type_primary_with_model_secondary`
  builds a REAL multi-type model and asserts the Phase-2.5 routing audit RAISES.
  This can only pass if the materialized tuple still contains that model when the
  SECOND audit iterates it — i.e. it directly disproves the
  "generator-drained-by-first-audit" regression. Its siblings
  (`_passes_all_type_plus_model`, `_passes_model_primary_with_type_secondary`,
  `_single_type_model_passes`) and the re-entrancy test
  (`test_finalize_rerun_after_audit_raise_preserves_recorded_strategy`) all pass.
- `tests/test_registry.py::test_audit_runs_once_per_build` (`== 1`) pins the
  once-per-build invariant.

Disposition: no temp test needed — the permanent suite already exercises both the
once-per-build invariant and the two-audits-share-one-iterable-tuple correctness
property the consolidation depends on.

### Notes for Worker 1 (spec reconciliation)

None. The consolidation matched the integration contract exactly; no spec gap,
conflict, or unstated assumption surfaced. The two-audit / two-phase / two-raise
structure and the once-per-build invariant (Decisions 8/10) are all preserved. The
spec needs no edit.

### Confirm green (focused suite, no `--cov`)

`uv run pytest tests/test_registry.py tests/types/test_relay_interfaces.py
tests/types/test_base.py tests/filters/test_base.py --no-cov` → **`322 passed`**
(was `1 failed, 321 passed` pre-consolidation; target met).
`test_audit_runs_once_per_build` green within the run. M1 regression resolved.

### Review outcome

`review-accepted`. The consolidation correctly resolves M1 (root-cause shared
single walk — one tuple-materialized call site, passed to both audits) and L1
(stale Slice-4 TODO block removed, siblings retained) with no new defect. Every
load-bearing invariant is preserved: single call site, tuple (not generator),
two audits / two raises / two phases, `_first_model_label_emitter` untouched,
`registry.py` and `test_audit_runs_once_per_build` (`== 1`) unchanged by the pass,
public surface empty, error handling structural-only. Zero High/Medium/Low
findings. The artifact top-level `Status:` is set to `review-accepted`.

---

## Final verification (Worker 1, integration)

Fresh Worker-1 finalize pass after the consolidation loop (2026-06-10). I
confirmed M1 and the original L1 against the working tree, re-ran the cross-slice
DRY scan conclusion, and ran the focused integration suite. **One new finding
(L2) blocks `final-accepted`** — a second stale `TODO(spec-031...)` marker the
original M1/L1 catalog did not surface. Outcome: `revision-needed`.

### M1 — RESOLVED (root-cause consolidation, verified)

`registry.models_with_multiple_types()` is materialized ONCE per finalize and
shared to both audits, exactly per the contract:

- **Single call site (grep-verified).** `multi_type_models =
  tuple(registry.models_with_multiple_types())` at `finalizer.py` #"multi_type_models = tuple"
  is the SOLE executable call site (`grep -n models_with_multiple_types
  finalizer.py` → one `tuple(...)` invocation; the four other hits are
  docstring/comment mentions). It sits after the `if registry.is_finalized():
  return` short-circuit and BEFORE the Phase-1 `_audit_primary_ambiguity(...)`
  call — a pure read that does not disturb Phase-1 failure-atomicity.
- **Materialized as a `tuple`**, so the one-shot lazy generator is drained once
  and re-iterated by both audits (a bare generator would be exhausted by the
  first audit, silently skipping the routing audit).
- **Two separate functions / two raises / two phases preserved.**
  `_audit_primary_ambiguity(multi_type_models)` (Phase 1 top, raises
  `_format_ambiguity_error`) and `_audit_model_label_routing(multi_type_models)`
  (Phase 2.5, after every `effective_globalid_strategy` is recorded and before
  Phase 3, raises `_format_model_label_routing_error`) each accept the
  materialized tuple as a parameter; they were NOT merged into one
  walk-with-two-checks. `_first_model_label_emitter` is UNCHANGED and iterates
  `registry.types_for(model)` (not the spied method), so it does not contribute
  to the spy count.
- **`test_audit_runs_once_per_build` unedited (`== 1`).** Confirmed
  `assert len(calls) == 1` at `tests/test_registry.py` #"assert len(calls) == 1";
  no `== 2` surface bump. Green in the focused run.
- **`registry.py` untouched** — the duplication was at the finalizer call sites,
  and the fix lives entirely in `finalizer.py`.

### L1 (original) — RESOLVED

The stale Slice-4 TODO block at `examples/fakeshop/apps/products/schema.py` is
GONE: `grep -n "spec-031\|globalid" examples/fakeshop/apps/products/schema.py`
returns nothing, and `grep -rn globalid_strategy examples/` returns nothing (no
fakeshop type carries `globalid_strategy = "type"` — the chosen Slice-4 opt-out
was `override_settings`, not a dedicated schema-fixture type). Sibling commented
Layer-3 lines (cards 039/040/038/027) correctly remain.

### L2 — NEW finding (blocks `final-accepted`): stale `TODO(spec-031...Slices 2-3)` in `tests/types/test_relay_interfaces.py`

A repo-wide `grep -rn "TODO(spec-031"` (excluding `docs/builder/`, `docs/shadow/`,
`docs/dry/` scratch) returns exactly ONE remaining marker:

```text
tests/types/test_relay_interfaces.py:57:# TODO(spec-031-globalid_encoding-0_0_9 Slices 2-3): Extend this module with
```

The block (`test_relay_interfaces.py:57-71`) is a `# Pseudocode:`-anchored
staged-slice TODO whose pseudocode enumerates the GlobalID strategy / encode /
decode / routing-audit / re-entrancy tests. **Every scenario it lists has fully
landed** — the module now carries 30 GlobalID tests below it
(`test_globalid_model_strategy_emits_model_label`,
`test_globalid_type_strategy_emits_graphql_type_name`,
`test_globalid_type_plus_model_emits_model_label`,
`test_globalid_callable_strategy_emits_custom`,
`test_consumer_resolve_typename_override_preserved_and_recorded_custom`,
`test_resolve_typename_override_plus_meta_strategy_raises`,
`test_model_label_routing_audit_*` ×4,
`test_finalize_rerun_after_audit_raise_preserves_recorded_strategy`,
`test_decode_*` ×17, `test_encode_decode_round_trip_decodable_strategies`, …),
all green in the focused run. Slices 2 and 3 both reached `final-accepted`.

Per AGENTS.md #26 a staged-slice TODO comment is "removed in the same change that
ships the slice"; this marker should have been deleted when Slices 2-3 shipped.
It is THIS card's TODO (it names "Slices 2-3" of spec-031), NOT a sibling card
032/033 deferral, so it fails this finalize pass's explicit L1-class criterion
("no remaining `TODO(spec-031...)` markers in package/example source that belong
to this card"). The original integration pass cataloged only the
`products/schema.py` Slice-4 TODO (L1) and did not surface this test-module
marker; the consolidation pass therefore never touched it.

**Severity: Low** — a stale, non-load-bearing comment (it would also trip an
`ERA001`-style "commented-out pseudocode" smell on a future sweep). But it is an
unmet contract item, so it blocks `final-accepted` until removed.

**Worker-2 consolidation contract addendum (L2).** Worker 0 re-dispatches one
Worker 2 consolidation pass (then Worker 3 review). **File Worker 2 may touch:**
`tests/types/test_relay_interfaces.py` only. Remove the
`# TODO(spec-031-globalid_encoding-0_0_9 Slices 2-3): ...` block plus its
`# Pseudocode:` lines and the trailing standalone `#` separator
(`test_relay_interfaces.py:57-71`, the comment block sitting between the `_meta`
helper at line 51-54 and the `# Slice 1 — validation + storage` section header).
Remove ONLY that spec-031 staged-slice TODO comment block; do NOT edit any test
function, the surrounding section-divider comments, or any assertion. This is a
pure comment-only deletion with no test-behavior surface. After removal run
`uv run ruff format tests/types/test_relay_interfaces.py` +
`uv run ruff check tests/types/test_relay_interfaces.py`, then re-run the focused
suite below and confirm it stays `322 passed`. Do NOT remove or alter the 30
GlobalID tests the block describes — they are the shipped work; only the stale
forward-looking comment goes.

### DRY verdict (cross-slice DRY scan conclusion) — STILL HOLDS

- **Strategy frozensets single-sourced.** `MODEL_LABEL_STRATEGIES =
  frozenset({"model", "type+model"})` and `TYPE_NAME_STRATEGIES =
  frozenset({"type", "type+model"})` are defined once at `types/relay.py:385-386`
  (grep-confirmed). `STRING_GLOBALID_STRATEGIES = frozenset({"model", "type",
  "type+model"})` at `types/base.py:85` is the deliberately distinct validation
  vocabulary. No parallel literal strategy set survives anywhere — the only other
  `{"model","type+model"}` / `{"type","type+model"}` hits are docstring/comment
  mentions (relay.py:380/384/419, definition.py:80). No `{"callable","custom"}`
  literal exists (the encode-only contract falls out of predicate math; only
  docstring mentions at relay.py:384, definition.py:80).
- **Consumed by encoder / decoder / audit / filter.** `filters/base.py:44`
  imports `MODEL_LABEL_STRATEGIES, TYPE_NAME_STRATEGIES` from `..types.relay` at
  module top (the SAME frozenset objects, a re-export not a copy) and reads them
  at base.py:243/245; the finalizer audit consumes them via the `_emits_model_label`
  / `_accepts_model_label_decode` predicates; decode Step-2 and the encoder read
  the same source.
- **Imports one-way.** `filters → types` (module top), `registry → types` /
  `relay → registry` (in-function). `types/relay.py` has NO module-top
  `filters` / `registry` import (grep over lines 1-45 confirms). Acyclic.
- **`__all__` unchanged.** `git diff --stat -- django_strawberry_framework/__init__.py`
  is EMPTY — no public-export drift (Decision 11, "no new public exports in
  0.0.9").

### Focused-test result (integration scope, `--no-cov` REQUIRED)

`uv run pytest tests/test_registry.py tests/types/test_relay_interfaces.py
tests/types/test_base.py tests/filters/test_base.py --no-cov` → **`322 passed`**
(matches the target, including `test_audit_runs_once_per_build` green). No
coverage flags passed. The L2 finding is a comment-only stale TODO — it does not
red-test the suite, but it is an unmet AGENTS.md #26 contract item, so the suite
being green does not by itself license `final-accepted`.

### Deferrals to sibling cards

Unchanged from the integration pass's `### Deferred work catalog` (all legitimate
sibling-card / maintainer deferrals): callable/`custom` decode path → card 032;
first consumer of `decode_global_id` / `definition_for_graphql_name` → card 032;
connection-aware optimizer planning → card 033; `type+model` rename-history alias
map → BACKLOG item 39; joint `0.0.9` version cut → maintainer. No spec-031 in-card
functional work is deferred — L2 is this-build cleanup, not a deferral.

### Spec changes made (Worker 1 only)

None. No spec gap, conflict, or inaccuracy surfaced. Per-spawn spec status-line
re-verification (spec lines 1-9): the `Status: planned — not started` line + the
unticked `## Slice checklist` are the intentional contract record (spec line 5:
"The Slice checklist below stays unticked as the contract record (build progress
is tracked in the build plan, not here)") — not a build tracker; no header edit
required. No predecessor reference broke. L2 is a source-comment removal (Worker
2 scope), NOT a spec edit.

### Outcome

`Status: revision-needed`. M1 (root-cause shared single walk) and the original L1
(products/schema.py Slice-4 TODO removed) are confirmed resolved, the cross-slice
DRY verdict still holds, and the focused suite is `322 passed`. But finalize
surfaced **L2** — a stale `TODO(spec-031...Slices 2-3)` block in
`tests/types/test_relay_interfaces.py:57-71` that belongs to this card, whose work
has fully landed, and which AGENTS.md #26 requires be removed with the shipping
slice. Worker 0 re-dispatches one Worker 2 consolidation pass (L2 per the addendum
above, `tests/types/test_relay_interfaces.py` only) + Worker 3 review, then re-runs
this integration finalize to confirm clean before the final test-run gate.

---

## Build report (Worker 2, consolidation pass 2)

Second consolidation pass implementing the single finalize-pass finding **L2** per
the `### Worker-2 consolidation contract addendum (L2)` in
`## Final verification (Worker 1, integration)` above. No spec-slice verbatim
checklist exists on this integration artifact, so there are no `- [ ]` boxes to
tick.

### Files touched

- `tests/types/test_relay_interfaces.py` (L2) — removed the stale
  `# TODO(spec-031-globalid_encoding-0_0_9 Slices 2-3): ...` comment block plus its
  `# Pseudocode:` enumeration lines and the trailing standalone `#` separator
  (was `test_relay_interfaces.py:57-71`, the block sitting between the `_meta`
  helper at lines 51-54 and the `# Slice 1 — validation + storage` section header).
  15 comment lines deleted. Preserved the two-blank-line PEP-8 separator between
  the `_meta` helper and the section-divider comment. No test function, fixture,
  import, assertion, or surrounding section-divider comment was touched — this is a
  pure comment-block deletion. Per AGENTS.md #26 the marker should have been deleted
  when Slices 2-3 shipped: every GlobalID strategy / encode / decode /
  routing-audit / re-entrancy scenario the pseudocode enumerated has already landed
  in this same module via the now-`final-accepted` Slices 2 and 3.

### Tests added or updated

None. L2 is a comment-only removal with no test-behavior surface. The 30+ GlobalID
tests the block described are the shipped Slice 2-3 work and were left untouched.

### Validation run

- `uv run ruff format .` — pass (235 files left unchanged; the `COM812`
  formatter-conflict line is the repo's pre-existing config warning, not an error
  introduced by this pass).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` after both ruff invocations — classification:
  - **Slice-intended (stays in the diff):** `tests/types/test_relay_interfaces.py`
    — this pass's L2 comment-block deletion (and the cumulative Slice 2-3 GlobalID
    tests already accepted in the same file).
  - **Expected cumulative Slice 1-5 accepted diff + the prior consolidation fix
    (`types/finalizer.py` + `examples/fakeshop/apps/products/schema.py`) + Worker 1
    spec edits (NOT this pass, NOT churn — do not revert):** `CHANGELOG.md`,
    `KANBAN.html`, `KANBAN.md`, `README.md`, `TODAY.md`, `docs/GLOSSARY.md`,
    `docs/README.md`, `docs/TREE.md`, `docs/spec-031-globalid_encoding-0_0_9.md`,
    `docs/spec-031-globalid_encoding-0_0_9-terms.csv`,
    `examples/fakeshop/db.sqlite3`, the touched package modules
    (`filters/base.py`, `filters/inputs.py`, `registry.py`, `types/base.py`,
    `types/definition.py`, `types/finalizer.py`, `types/relay.py`),
    `examples/fakeshop/apps/products/schema.py`, the three live test files
    (`test_kanban_api.py`, `test_library_api.py`, `test_products_api.py`), and the
    three other package test files (`tests/filters/test_base.py`,
    `tests/test_registry.py`, `tests/types/test_base.py`).
  - **Concurrent activity (leave untouched per AGENTS.md #33):**
    `docs/dry/dry-0_0_9.md` (concurrent DRY cycle).
  - **Untracked build artifacts (the build cycle's own `bld-*` / `build-*` files):**
    the seven `docs/builder/*.md` build files.
  - **Unrelated tool churn introduced by this pass: none.** Ruff reformatted
    nothing; only `tests/types/test_relay_interfaces.py` carries this pass's edit.
    Nothing to `git checkout --`.
- **`TODO(spec-031` grep confirmation.** Repo-wide
  `grep -rn "TODO(spec-031" .` excluding scratch dirs `docs/builder/`,
  `docs/shadow/`, `docs/review/`, `docs/dry/` returns **zero** matches after the
  edit (exit 1, no lines). No card-031-owned `TODO(spec-031` marker remains in
  package or test source. (The original integration L1 already removed the
  `products/schema.py` Slice-4 marker; this pass removed the last one.)

### Focused test run (no `--cov*`)

`uv run pytest tests/types/test_relay_interfaces.py --no-cov` → **`106 passed`**.
A comment-block deletion does not change test behavior, so the pass count is
unchanged from before the edit. Explicit `--no-cov` passed (required because
`pytest.ini` auto-applies `--cov`); no `--cov*` flag passed; full repo suite NOT
run per the contract.

### Implementation notes

- **Whitespace shape after deletion.** The TODO block was preceded by two blank
  lines (after the `_meta` helper) and followed by two blank lines (before the
  `# ---` section divider). Removing the block collapses both gaps into a single
  PEP-8 top-level two-blank-line separator between the helper and the section
  comment — the canonical shape `ruff format` keeps, confirmed by the
  `235 files left unchanged` format run (no reflow of this file).

### Notes for Worker 3

- Pure comment-only deletion in a test module: no logic, no assertions, no
  fixtures, no imports changed. The 30+ shipped GlobalID tests the stale block
  described remain intact and green (`106 passed`).
- No shadow file used — a comment-block removal needs no static-inspection
  refresh.
- The repo-wide `TODO(spec-031` grep (scratch dirs excluded) is now empty; any
  future marker would belong to sibling cards 032/033, none currently present in
  source.

### Notes for Worker 1 (spec reconciliation)

None. No spec gap, conflict, or unstated assumption surfaced. L2 is the AGENTS.md
#26 stale-staged-slice-TODO removal that should have shipped with Slices 2-3; it
is a source-comment deletion in Worker-2 scope, not a spec edit. The spec needs no
change.

---

## Review (Worker 3, integration consolidation pass 2)

Reviewed Worker 2's second consolidation diff (**L2** only) against the
`### Worker-2 consolidation contract addendum (L2)` in
`## Final verification (Worker 1, integration)` and AGENTS.md #26 (staged-slice
TODO removal). Diff scope: ONLY `tests/types/test_relay_interfaces.py`, and within
that file ONLY the stale `TODO(spec-031...Slices 2-3)` comment-block deletion. The
file ALSO carries the already-accepted Slice-2/Slice-3 test additions (the
`decode_global_id, encode_typename` import add + the ~593 lines of GlobalID tests
at the file tail) — those are the cumulative accepted-slice diff (the file predates
Slice 1 at HEAD), NOT this pass's contribution, and were not weighed. The prior
consolidation fix (`types/finalizer.py` M1 + `products/schema.py` L1), Worker 1's
spec edits, and the concurrent `docs/dry/` / "archive 030" activity are likewise
out of scope.

Static-inspection helper: SKIPPED, recorded reason — L2 is a pure comment-only
deletion in a test module (no logic, no new `.py` file, no `optimizer/`/`types/`
source touched, zero lines of new logic). BUILD.md "When to run the helper" does
not trigger for a comment-block removal; nothing to inspect.

### Verification performed

- **Pure comment-block deletion (confirmed by reading the diff hunk).**
  `git diff -- tests/types/test_relay_interfaces.py | grep '^-'` shows every
  deleted line is a `#` comment: the `TODO(spec-031-globalid_encoding-0_0_9 Slices
  2-3)` marker, its `# Pseudocode:` enumeration, and the trailing standalone `#`
  separator (plus the two blank lines the block carried, collapsing to the single
  PEP-8 top-level two-blank separator between the `_meta` helper and the
  `# Slice 1 — validation + storage` section divider). `numstat` is `592 17` — the
  17 deletions are exactly the TODO block; the 592 insertions are the
  already-accepted Slice-2/3 tests (out of scope). NO test function, fixture,
  import, assertion, or section-divider comment was changed by this pass.
- **Zero remaining card-031 TODO markers (grep-confirmed).**
  `grep -rn "TODO(spec-031" .` excluding `docs/builder/ docs/shadow/ docs/review/
  docs/dry/` returns EXIT 1, zero matches. No card-031-owned staged TODO remains
  (the `products/schema.py` Slice-4 marker was removed in consolidation pass 1; this
  pass removed the last one).
- **No collateral source / public-surface change.**
  `git diff -- django_strawberry_framework/__init__.py` is EMPTY (public surface
  unchanged). `git diff --name-only -- django_strawberry_framework/` lists only the
  seven prior-accepted/consolidation package files (`filters/base.py`,
  `filters/inputs.py`, `registry.py`, `types/base.py`, `types/definition.py`,
  `types/finalizer.py`, `types/relay.py`) — NO NEW package change from this pass
  (L2 touched the test file only).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None. A comment-block deletion introduces no logic and no duplication. The deleted
TODO had no behavior surface; the GlobalID tests it forward-referenced already
exist in the same module (the shipped Slice-2/3 work), so removing the marker does
not orphan anything.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is EMPTY. `__all__` and the
re-export list are unchanged. L2 touches only `tests/types/test_relay_interfaces.py`
(a comment deletion); no public export drift. Consistent with Decision 11 ("no new
public exports in 0.0.9").

### CHANGELOG sanity

Not applicable; consolidation pass 2 did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; consolidation pass 2 did not modify docs/release/KANBAN/archive
surfaces (the only file touched is a package test).

### What looks solid

- **Pure comment removal, correctly scoped.** Only the stale
  `TODO(spec-031...Slices 2-3)` block + `# Pseudocode:` enumeration + trailing `#`
  separator were deleted (15 comment lines). Every deleted line is a `#` comment;
  no test logic moved.
- **Whitespace shape clean.** The collapse to a single two-blank-line separator
  matches `ruff format` (Worker 2's `235 files left unchanged` format run confirms
  no reflow). No stray blank-line churn.
- **AGENTS.md #26 satisfied.** The marker named "Slices 2-3" of spec-031 — both
  `final-accepted` — and every scenario its pseudocode enumerated (strategy /
  encode / decode / routing-audit / re-entrancy) has landed in this same module.
  Removing it is the contract-completing cleanup, not a behavior change.
- **No card-031 TODO debt remains.** Grep (scratch dirs excluded) is empty; the
  build's staged-slice TODO markers are fully discharged.

### Temp test verification

None created. A comment-block deletion has no behavior surface to probe, and the
106 shipped tests in the module already cover the GlobalID behavior the stale block
forward-referenced. The focused suite (below) is the gate.

### Notes for Worker 1 (spec reconciliation)

None. L2 is a source-comment (test-module) deletion in Worker-2 scope, not a spec
edit. No spec gap, conflict, or unstated assumption surfaced. The spec needs no
change.

### Confirm green (focused suite, no `--cov`)

`uv run pytest tests/types/test_relay_interfaces.py --no-cov` → **`106 passed`**
(unchanged — a comment deletion has no behavior surface). Explicit `--no-cov`
passed (required because `pytest.ini` auto-applies `--cov`); no `--cov*` flag used;
full repo suite NOT run per the contract.

### Review outcome

`review-accepted`. The pass is a correct, pure comment-block deletion that resolves
L2 with zero behavior change: only the stale `TODO(spec-031...Slices 2-3)` marker
(TODO + Pseudocode enumeration + trailing `#` separator) was removed; no test
function, fixture, import, assertion, or section-divider was touched. Zero
remaining card-031 `TODO(spec-031...)` markers (grep, scratch dirs excluded).
Public surface empty, no new package source change. Focused suite `106 passed`,
unchanged. Zero High/Medium/Low findings. The artifact top-level `Status:` is set
to `review-accepted`.

---

## Final verification (Worker 1, integration — round 2)

Fresh Worker-1 finalize pass after the SECOND consolidation loop (the L2 fix:
Worker 2 build + Worker 3 review, both `review-accepted` above). I re-verified
all three findings (M1 + L1 + L2) against the working tree, re-ran the
no-remaining-TODO grep myself, re-confirmed the cross-slice DRY verdict and the
public surface, and re-ran the focused integration suite. **All findings are
resolved; no new blocker surfaced.** Outcome: `final-accepted`.

Per AGENTS.md (rigorous, not perfectionist) and my own round-1 lesson (a clean
Worker-3 review does not license a rubber-stamp), I independently re-ran every
task-criterion check below rather than relying on the consolidation review.

### M1 — RESOLVED (root-cause consolidation, re-verified)

`registry.models_with_multiple_types()` is materialized ONCE per finalize and
shared to both audits:

- **Single executable call site (grep-verified).**
  `multi_type_models = tuple(registry.models_with_multiple_types())` at
  `finalizer.py` #"multi_type_models = tuple" is the SOLE call site
  (`grep -n models_with_multiple_types finalizer.py` → one `tuple(...)`
  invocation at the materialization line; the four other hits are
  docstring/comment mentions). It sits after the `if registry.is_finalized():
  return` short-circuit and BEFORE the Phase-1 `_audit_primary_ambiguity(...)`
  call — a pure read that does not disturb Phase-1 failure-atomicity.
- **Materialized as a `tuple`** so the one-shot lazy generator is drained once
  and re-iterated by both audits (a bare generator would be exhausted by the
  first audit, silently skipping the routing audit).
- **Two separate functions / two raises / two phases preserved.** Both
  `_audit_primary_ambiguity(multi_type_models: tuple[type[models.Model], ...])`
  (Phase 1 top, raises `_format_ambiguity_error`) and
  `_audit_model_label_routing(multi_type_models: tuple[type[models.Model], ...])`
  (Phase 2.5, after every `effective_globalid_strategy` is recorded and before
  Phase 3, raises `_format_model_label_routing_error`) accept the materialized
  tuple as a parameter; they were NOT merged. `_first_model_label_emitter` is
  UNCHANGED and iterates `registry.types_for(model)` (not the spied method), so
  it does not contribute to the spy count.
- **`test_audit_runs_once_per_build` unedited (`== 1`).** Confirmed
  `assert len(calls) == 1` at `tests/test_registry.py` #"assert len(calls) == 1";
  no `== 2` surface bump. Green individually (`1 passed`) and in the focused run.
- **`registry.py` untouched** — the duplication was at the finalizer call sites,
  and the fix lives entirely in `finalizer.py`.

### L1 — RESOLVED (re-verified)

The stale Slice-4 TODO block in `examples/fakeshop/apps/products/schema.py` is
GONE: `grep -n "spec-031\|globalid" examples/fakeshop/apps/products/schema.py`
returns nothing, and `grep -rn globalid_strategy examples/` returns nothing (no
fakeshop type carries `globalid_strategy = "type"` — the chosen Slice-4 opt-out
was `override_settings`, not a dedicated schema-fixture type). Sibling commented
Layer-3 lines (cards 039/040/038/027) correctly remain.

### L2 — RESOLVED (re-verified)

The stale `TODO(spec-031...Slices 2-3)` block in
`tests/types/test_relay_interfaces.py` (was lines 57-71) is GONE:
`grep -n "TODO(spec-031\|Pseudocode" tests/types/test_relay_interfaces.py`
returns nothing. The pure comment-block deletion (Worker-2 consolidation pass 2)
left every shipped GlobalID test in the module intact — the focused run collects
and passes them all. Per AGENTS.md #26 the marker should have shipped removed
with Slices 2-3; it now is.

### No-remaining-TODO grep — ZERO card-031 matches (re-run myself)

`grep -rn "TODO(spec-031" .` excluding scratch dirs `docs/builder/`,
`docs/shadow/`, `docs/review/`, `docs/dry/` returns **EXIT 1, zero matches**. No
card-031-owned staged TODO remains anywhere in package or test source. A
contrast grep for `TODO(spec-032` / `TODO(spec-033` in `*.py` returns none — no
sibling-card TODOs are currently staged in source either (any that appear later
would be sibling-card scope, not spec-031). Confirmed.

### DRY verdict — STILL HOLDS

- **Strategy frozensets single-sourced.** `MODEL_LABEL_STRATEGIES =
  frozenset({"model", "type+model"})` and `TYPE_NAME_STRATEGIES =
  frozenset({"type", "type+model"})` are defined exactly once, at
  `types/relay.py:385-386` (grep over `django_strawberry_framework/` returns ONLY
  those two definitions — no parallel definition anywhere).
  `STRING_GLOBALID_STRATEGIES = frozenset({"model", "type", "type+model"})` at
  `types/base.py:85` remains the deliberately distinct validation vocabulary. No
  `{"callable","custom"}` literal exists (the encode-only contract falls out of
  predicate math).
- **Consumed by encoder / decoder / audit / filter.** `filters/base.py:44`
  imports `MODEL_LABEL_STRATEGIES, TYPE_NAME_STRATEGIES` from `..types.relay` at
  module top (the SAME frozenset objects, a re-export not a copy) and reads them
  at base.py:243/245; the finalizer audit consumes them via the predicates;
  decode Step-2 and the encoder read the same source.
- **Imports one-way.** `filters → types` (module top). `types/relay.py` reaches
  `registry` only IN-FUNCTION (the `from ..registry import registry` is inside
  `decode_global_id` at relay.py:607, with the cycle-dodge comment at 602-604);
  no module-top `filters` / `registry` reverse import. Acyclic.
- **`__all__` unchanged.** `git diff -- django_strawberry_framework/__init__.py`
  is EMPTY — no public-export drift (Decision 11, "no new public exports in
  0.0.9").

### Focused-test result (integration scope, `--no-cov` REQUIRED)

`uv run pytest tests/test_registry.py tests/types/test_relay_interfaces.py
tests/types/test_base.py tests/filters/test_base.py --no-cov` → **`322 passed`**
(matches the prior target, including `test_audit_runs_once_per_build` green;
re-confirmed `test_audit_runs_once_per_build` green individually, `1 passed`).
Explicit `--no-cov` passed; no `--cov*` flag used; the full repo suite was NOT
run (that is the final test-run gate's job, `bld-final.md`).

### Deferrals to sibling cards (unchanged)

All legitimate sibling-card / maintainer deferrals from the
`### Deferred work catalog` above stand, none owned by this card:

- Callable / `custom` decode path → `WIP-ALPHA-032-0.0.9` (Full Relay story).
- First consumer of `decode_global_id` / `definition_for_graphql_name` →
  `WIP-ALPHA-032-0.0.9` (root `node(id:)` / `nodes(ids:)`).
- Connection-aware optimizer planning → `WIP-ALPHA-033-0.0.9`.
- `type+model` rename-history alias map → BACKLOG item 39 (post-1.0.0).
- Joint `0.0.9` version cut (pyproject / `__version__` / `test_version` /
  `uv.lock`; no `## [0.0.9]` CHANGELOG heading promotion) → maintainer, owned by
  the joint cut across cards 029/030/031/032/033 (spec Decision 12). On-disk
  version correctly still `0.0.8`.

No spec-031 in-card work is deferred — the five slices delivered the full spec
contract end-to-end, and M1/L1/L2 were this-build integration cleanup, all now
resolved.

### Spec changes made (Worker 1 only)

None. No spec gap, conflict, or inaccuracy surfaced at this round-2 finalize.
Per-spawn spec status-line re-verification (spec lines 1-9): the `Status: planned
— not started` line + the unticked `## Slice checklist` are the intentional
contract record (spec line 5: "The Slice checklist below stays unticked as the
contract record"), not a build tracker — no header edit required. No predecessor
reference broke.

### Outcome

`Status: final-accepted`. M1 (root-cause shared single walk), L1
(`products/schema.py` Slice-4 TODO removed), and L2
(`test_relay_interfaces.py` Slices-2-3 TODO removed) are all confirmed resolved
against the working tree; the repo-wide `TODO(spec-031` grep returns zero
card-031 matches; the cross-slice DRY verdict holds (frozensets single-sourced,
imports one-way, `__all__` unchanged); and the focused integration suite is
`322 passed`. The integration pass is clean. Worker 0 may now dispatch the final
test-run gate (`docs/builder/bld-final.md`).

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
