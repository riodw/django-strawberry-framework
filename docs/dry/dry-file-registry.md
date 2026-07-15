# DRY review: `django_strawberry_framework/registry.py`

Status: verified

## System trace

`registry.py` owns three lifecycles behind one process-global singleton (`registry`):

- **Type/model bookkeeping.** `TypeRegistry._types` (model -> list of registered `DjangoType`
  subclasses, registration order), `_primaries` (model -> the declared relation-resolution
  target), `_models` (the reverse, one-to-one `type_cls -> model` map), and `_definitions`
  (`type_cls -> DjangoTypeDefinition`). `register` / `register_with_definition` are the sole
  writers; `unregister` is the sole eraser; `get` / `model_for_type` / `iter_types` /
  `primary_for` / `types_for` / `models_with_multiple_types` / `iter_definitions` /
  `definition_for_graphql_name` are the read surface consumed by `types/base.py`
  (`DjangoType.__init_subclass__`), the optimizer (`optimizer/extension.py`,
  `optimizer/walker.py`), the schema audit, and `types/relay.py`'s GlobalID decode.
- **Pending relations.** `_pending`, mutated by `add_pending_relation` / `discard_pending` /
  `iter_pending_relations`, resolved by `types/finalizer.py::resolved_relation_annotation`.
- **Subsystem-lifecycle registration.** The module-level `_subsystem_clears` dict plus
  `register_subsystem_clear` / `iter_subsystem_clears`, and the per-type `_type_teardowns` /
  `register_type_teardown` / `_run_type_teardowns` on `TypeRegistry` itself. This is the single
  owner every other package co-clear plugs into: `forms/inputs.py`, `forms/sets.py`,
  `mutations/inputs.py`, `mutations/sets.py`, `filters/inputs.py`, `filters/__init__.py`,
  `orders/inputs.py`, `orders/__init__.py`, `rest_framework/inputs.py`,
  `rest_framework/serializer_converter.py`, `auth/mutations.py`, `auth/queries.py`,
  `relay.py`, and `connection.py` each call `register_subsystem_clear(their_own_clear_fn,
  owner="...")` at import time. `types/finalizer.py` calls `iter_subsystem_clears(before_bind=True)`
  once per finalize pass; `TypeRegistry.clear()` calls `iter_subsystem_clears()` (no filter) for
  the full test-teardown lifecycle. This registry-of-callbacks shape (owner-resolved function
  objects, not string/import-path lookups) is itself the confirmed prior consolidation replacing
  what `_clear_if_importable`'s stale docstring still described (see Verification) - each
  subsystem states its own reset once, `registry.py` never special-cases a subsystem by name.

Connected callers read for this review: `types/finalizer.py` (the `before_bind` co-clear loop
and phase-1/2/2.5/3 finalize sequencing that calls `register`/`register_definition`/
`add_pending_relation`/`discard_pending`/`mark_finalized`), `types/base.py`
(`DjangoType.__init_subclass__` -> `register_with_definition`), `filters/factories.py` and
`orders/factories.py` (class-level caches named to match what `registry.clear()`/tests address
directly, no clear hook of their own - accepted lifecycle per their own review-cycle notes),
`connection.py` (`_connection_type_cache`, `clear_connection_type_cache`, and the
`register_subsystem_clear` call at its own bottom), `apps.py` (no registry coupling - `ready()`
only wires Django app config, unrelated to this lifecycle), and `tests/test_registry.py` /
`tests/optimizer/test_extension.py` / `examples/fakeshop/test_query/conftest.py` (the only
production-adjacent direct pokes of `_types`/`_models`, all in test fixtures simulating a
corner state, not a parallel production representation).

## Verification

- `rg` for `register_subsystem_clear\(` across the package: 14 owner call sites, each a thin
  module-local `clear_X()` wrapping that module's own dict/cache `.clear()` (or, for
  `forms/inputs.py` / `mutations/inputs.py` / `rest_framework/inputs.py`, delegating to the
  already-consolidated `utils/inputs.py::clear_generated_input_namespace`). Read each call site;
  none duplicates `registry.py`'s registration/dispatch mechanism itself - they are the
  *consumers* of the one mechanism `registry.py` owns. Rejected as duplication: the shared
  *shape* (owner registers a zero-arg callable) is the intended single-sited abstraction, not a
  smell.
- Compared `unregister`'s `_types[model]`-remove-and-prune-if-empty block against
  `register_with_definition`'s rollback block byte-for-byte: identical four-line invariant
  maintenance (`types.remove(type_cls); if not types: pop(model)`) plus an identical
  `self._models.pop(type_cls, None)`, present verbatim at both sites. Verified they are NOT
  interchangeable beyond that shared fragment: `unregister` additionally runs type teardowns,
  unconditionally drops the primary slot, purges `_definitions`, and filters pending relations
  and the connection-type cache - none of which the rollback may do, because
  `register_with_definition` is a single atomic call and nothing new could have been attached to
  `type_cls` between its internal `register()` and `register_definition()` calls.
  `test_register_with_definition_rolls_back_register_on_definition_failure` pins that a
  *pre-existing* `_definitions` entry must survive the rollback - proof that naively calling
  `unregister()` from the rollback path (which unconditionally pops `_definitions`) would be a
  behavior-changing merge, not a safe consolidation. Confirmed real, narrow duplication: only the
  `_types`/`_models` invariant-maintenance fragment, not the surrounding call.
- Read `_clear_if_importable`'s docstring against its actual call graph
  (`rg '_clear_if_importable' django_strawberry_framework/registry.py`): one definition, one call
  site (`unregister`'s connection-cache eviction). The docstring claimed it was "the... shape that
  `TypeRegistry.clear` / `TypeRegistry.unregister` repeat for each subsystem co-clear (filter /
  order input namespaces + helper ledgers, the connection-class cache, the root node-field
  ledger)" - false for `clear()` (which uses `iter_subsystem_clears()` exclusively, no import at
  clear-time at all) and overbroad for `unregister()` (which touches only the connection cache,
  never the registry-wide filter/order namespaces or node-field ledger - correctly so, since a
  single-type unregister must not reset registry-wide state). This reads as leftover text from
  before the `register_subsystem_clear` mechanism existed, when `clear()` likely *did* inline
  per-subsystem best-effort imports directly. Traced this to the same root cause as the
  concurrent, already-tracked staleness in `docs/bug_hunt/bug_hunt-0_0_13.md` (the `_clear_if_loaded`
  symbol removed from `registry.py` but still imported by `tests/auth/test_mutations.py`, and the
  matching stale docstring noted in `utils/imports.py`) - a maintainer refactor of the co-clear
  mechanism that is still settling. That log explicitly defers the *cross-file* instances of this
  staleness ("left for the refactor to settle"); this docstring lives inside the assigned target
  file itself, so it is fixed here rather than deferred.
- Checked `orders/__init__.py`, `orders/inputs.py`, `orders/sets.py`, `filters/factories.py` for
  the same "Slice 3 wires `registry.clear()` to call X via a cycle-safe local-import dance, TWO
  separate steps" phrasing - still present, still describing the pre-`register_subsystem_clear`
  architecture. **Rejected for edit here**: these docstrings belong to their own files, not
  `registry.py`; the maintainer's refactor is confirmed in-flight and concurrently touching that
  same architectural seam (`docs/bug_hunt/bug_hunt-0_0_13.md`'s "left for the refactor to settle"
  entries), and sweeping them from this item risks colliding with that work. Recorded as a
  blocker for the maintainer / a later pass, not fixed.
- Compared `TypeRegistry.__init__`'s seven-field initialization against `clear()`'s seven
  `.clear()` calls: structurally parallel but not a duplication candidate - a constructor
  documents the fresh-state shape once at class definition, `clear()` documents a test-teardown
  reset contract; both lists are short, stable (no field added without touching this class
  directly), and merging them behind a shared field-list constant would only hide which fields
  exist from a reader scanning either method, for a two-line saving. Rejected.
- Confirmed `_clear_if_importable`'s only caller is `unregister`'s connection-cache eviction (`rg`
  count: one definition, one call). No second site to converge with it exists today; its
  docstring is corrected to state that precisely instead of claiming a shared-mechanism status it
  does not have.

## Opportunities

**1. Repeated `_types`/`_models` invariant-maintenance fragment**

- **Repeated responsibility:** "detach `type_cls` from `_types[model]` (pruning the model key if
  the list becomes empty) and from the one-to-one `_models` map" - the exact inverse of what
  `register` appends when it adds a new registration.
- **Sites:** `TypeRegistry.unregister` and `TypeRegistry.register_with_definition`'s
  exception-path rollback.
- **Evidence:** identical four-plus-one-line body at both sites; both exist to undo the same two
  `register`-side mutations and must change in lockstep with `register`'s forward shape (e.g. if
  `_types` ever became a `set` instead of a `list`, both sites would need the same edit).
- **Owner:** `TypeRegistry` itself (the class already owns both `_types` and `_models`).
- **Consolidation:** extracted `TypeRegistry._detach_type_from_model(model, type_cls)`, called
  from both sites; each site keeps its own distinct handling of `_primaries`, `_definitions`,
  pending relations, and type teardowns unmerged, since those differ by design (see Verification).
- **Proof:** behavior-preserving refactor - byte-identical mutation sequence, same branch
  coverage (`if not types` empty-prune branch is hit by the single-type rollback case
  and the single-type `unregister` case; the non-empty no-prune branch is hit by
  `test_unregister_keeps_siblings_intact_in_multi_type_case` and
  `test_register_with_definition_rollback_restores_pre_existing_primary`). No new test added -
  the existing `tests/test_registry.py` suite (`test_register_with_definition_rolls_back_...`,
  `test_register_with_definition_rollback_clears_primary`,
  `test_register_with_definition_rollback_restores_pre_existing_primary`,
  `test_unregister_removes_from_types_models_primaries_definitions`,
  `test_unregister_keeps_siblings_intact_in_multi_type_case`) already exercises every branch of
  the extracted method through both callers; a redundant test would only pin implementation
  structure, not new behavior.
- **Risks / non-goals:** did not fold `unregister` and the rollback into one method - their
  handling of `_primaries` (unconditional purge vs. conditional restore-or-pop),
  `_type_teardowns`, `_definitions`, pending relations, and the connection-cache eviction is
  intentionally distinct and must stay so.

**2. `_clear_if_importable` docstring overclaimed a shared-mechanism status it does not have**

- **Repeated responsibility (as claimed, disproven):** the docstring asserted this helper was the
  common co-clear shape for both `clear()` and `unregister()` across filter/order namespaces, the
  connection cache, and the node-field ledger.
- **Sites:** the helper's own docstring vs. its actual single call site (`unregister`'s
  connection-cache eviction) and `clear()`'s actual mechanism (`iter_subsystem_clears()`).
- **Evidence:** `rg` count of one definition / one call; `clear()`'s body contains no import at
  all, only the registered-callback loop.
- **Owner:** the helper's own docstring, in this file.
- **Consolidation:** rewrote the docstring to name its actual single caller and to point readers
  at `register_subsystem_clear` / `iter_subsystem_clears` as the mechanism `clear()` actually
  uses, so a future contributor adding a co-clear does not reach for the wrong (and
  now-single-purpose) helper.
- **Proof:** documentation-only change; no behavior to test. Ruff format/check clean.
- **Risks / non-goals:** left the cross-file instances of the same staleness
  (`orders/__init__.py`, `orders/inputs.py`, `orders/sets.py`, `filters/factories.py`, and the
  `_clear_if_loaded` symbol referenced by `utils/imports.py`'s docstring and imported by
  `tests/auth/test_mutations.py`) untouched - confirmed concurrent, in-flight maintainer work per
  `docs/bug_hunt/bug_hunt-0_0_13.md`, out of scope for this item, and reported as a blocker below.

## Judgment

`registry.py`'s headline lifecycle mechanism - one owner-registered-callback dispatch table
(`register_subsystem_clear` / `iter_subsystem_clears`) replacing what would otherwise be N
hand-rolled cycle-safe imports scattered across every consumer subsystem - is already the correct
consolidation and is not duplicated anywhere else in the package; every subsystem calls in as a
consumer, not a competing implementation. The one real internal duplication (`unregister` /
`register_with_definition` rollback sharing an invariant-maintenance fragment) is now
single-sited behind `_detach_type_from_model`. A docstring inside this file that misdescribed the
co-clear architecture is corrected. Everything else investigated (the `filters`/`orders` factory
cache lifecycle, the `__init__`/`clear` field-list parallel, the cross-file "Slice 3 wires
`registry.clear()`..." staleness) is either not a genuine duplication or is confirmed-concurrent
work correctly left to the maintainer's in-flight refactor.

## Implementation (Worker 1)

- **Owner chosen:** `TypeRegistry._detach_type_from_model` (new private method), replacing the
  duplicated fragment in `unregister` and `register_with_definition`.
- **Migrated sites:** `TypeRegistry.unregister`, `TypeRegistry.register_with_definition`
  (both in `django_strawberry_framework/registry.py`). No other file called the duplicated
  fragment directly (confirmed via the `rg` sweep in Verification), so no cross-file migration
  was needed.
- **Docs/docstrings touched:** `_clear_if_importable`'s docstring (same file) corrected to match
  its actual single caller and to point at the real `clear()` mechanism.
- **Behavior kept separate:** `_primaries` handling (unconditional purge in `unregister` vs.
  conditional restore-or-pop in the rollback), `_type_teardowns`, `_definitions`, pending-relation
  filtering, and connection-cache eviction all remain at their original call sites, unmerged.
- **Validation:** `uv run ruff format django_strawberry_framework/registry.py` (unchanged) and
  `uv run ruff check --fix django_strawberry_framework/registry.py` (all checks passed);
  `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/registry.py`
  (clean). No `pytest` run per the DRY workflow's file-item scope; existing
  `tests/test_registry.py` coverage already exercises every branch of the extracted method
  through both callers (see Opportunity 1 Proof), so no new test was added.
- **Rejected candidates and evidence:** see Verification - the `filters`/`orders`/`rest_framework`
  co-clear consumers (not a duplicate of the dispatch mechanism they consume), the
  `__init__`/`clear()` field-list parallel (different lifecycle phases, not error-prone), and the
  cross-file "Slice 3 wires `registry.clear()`..." docstring staleness (confirmed concurrent
  maintainer refactor, deferred).
- **Changelog:** not touched; no maintainer authorization requested or given for this item.

## Blockers / concurrent work observed

Reconciled after Worker 2's independent re-check against current HEAD (see below): the
test-level blockers first recorded here are now RESOLVED; only the out-of-file docstring
staleness remains, and none of it was ever in this item's scope.

- RESOLVED (verified gone in current HEAD): the maintainer's in-flight refactor of this
  co-clear mechanism (the same `register_subsystem_clear` design reviewed above) had left
  `tests/auth/test_mutations.py` failing at collection (`ImportError: cannot import name
  '_clear_if_loaded' from ...registry`) and a stale assertion in `tests/auth/test_queries.py`
  (`(module_path, "clear_current_user_alias_namespace") in iter_subsystem_clears()`, structurally
  impossible now that `iter_subsystem_clears()` returns bare callables), both tracked in
  `docs/bug_hunt/bug_hunt-0_0_13.md`. The maintainer has since reconciled both: neither
  `_clear_if_loaded` in that test nor the stale assertion survives in the tree.
- RESOLVED (verified gone in current HEAD):
  `tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_target`
  (flagged as a stale test superseded by the `before_bind` reset ordering) no longer exists in
  that file.
- `utils/imports.py`'s module docstring still lists `registry.py::_clear_if_loaded` as one of the
  three historical call sites it consolidated - that symbol no longer exists in `registry.py`.
  Confirmed the same concurrent-refactor root cause; left untouched (not this file's ownership,
  and the bug-hunt log already tracks it as deferred).
- `orders/__init__.py`, `orders/inputs.py`, `orders/sets.py`, and `filters/factories.py` retain
  docstring language describing the pre-`register_subsystem_clear` "cycle-safe local-import dance"
  architecture for their own co-clear wiring. Confirmed stale relative to the current
  `registry.py` mechanism; left untouched as out-of-file scope and concurrent with the
  maintainer's refactor.

## Independent verification (Worker 2)

Re-traced ownership from scratch rather than reviewing only the diff: read the complete current
`registry.py` (597 lines), the item-scoped diff (`git diff b51ce31a... -- registry.py`, three
hunks: the `_detach_type_from_model` extraction with call-site migration at both `unregister` and
`register_with_definition`'s rollback, and the `_clear_if_importable` docstring rewrite), and every
caller/consumer path named in the artifact's System trace.

- **Diff matches the artifact exactly.** The three hunks are precisely what the Opportunities and
  Implementation sections claim: no unrelated lines moved, no unrelated docstring elsewhere in the
  file touched.
- **Challenged "only the detach invariant is truly shared."** Independently re-read `unregister`
  (lines 271-323) against `register_with_definition`'s rollback (lines 414-444) side by side.
  Confirmed by inspection and not just by the artifact's say-so: after the extracted
  `_detach_type_from_model` call, `unregister` additionally (a) already ran `_run_type_teardowns`
  *before* detaching (rollback never runs teardowns, correctly - nothing could have attached a
  teardown to `type_cls` in the atomic window between `register()` and `register_definition()`),
  (b) unconditionally pops `_primaries[model]` when `type_cls` was primary, while the rollback
  restores `pre_primary` (which may re-set a *different* class as primary) or pops only when there
  was none - genuinely different logic, not a formatting variant, (c) pops `_definitions`
  unconditionally, while the rollback must NOT touch `_definitions` at all (the pre-poisoned entry
  it fails on is exactly what `test_register_with_definition_rolls_back_register_on_definition_failure`
  pins as surviving), and (d) filters `_pending` and evicts the connection-type cache, neither of
  which the rollback does since nothing could have been added to either within the atomic call.
  **Confirmed calling `unregister()` from the rollback would be wrong**: it would wrongly run
  teardowns never registered inside this atomic call (harmless no-op today only because
  `_run_type_teardowns` guards on a missing key, but conceptually the wrong lifecycle phase), and
  it would unconditionally purge `_definitions[type_cls]` - directly contradicting the pinned
  survive-the-rollback contract for a pre-existing definition. The four-line fragment is the only
  part that is genuinely one rule; everything around it is independently confirmed to disagree by
  design.
- **Found and evaluated a subtle non-behavior-preserving nuance the artifact did not call out.**
  The pre-consolidation `unregister` popped `_models` (bare `.pop(type_cls)`, no default) *before*
  mutating `_types`, so a hypothetical `_types`/`_models` lock-step violation in the
  "in `_models`, missing from `_types[model]`'s list" direction would have raised `KeyError`
  from `_models.pop` with `_types` still untouched; `_detach_type_from_model` reverses the order
  (mutates `_types` first, then `self._models.pop(type_cls, None)` with a default) so that same
  corruption direction would now raise `ValueError` from `list.remove` instead - a message change,
  same failure timing (before either dict is left inconsistent), so this direction is unaffected.
  The other corruption direction ("in `_types[model]`'s list, missing from `_models`") DOES change:
  originally `_models.pop(type_cls)` (no default) raised loudly before any mutation; now
  `_types` is mutated first (succeeds, since this direction has the type present in the list) and
  `_models.pop(type_cls, None)` then silently no-ops. Verified this corruption direction is
  unreachable through any current call path: `register()` always writes `_types` and `_models`
  together with no exception window between them (the only place that could partially apply the
  pair), and every direct private-map poke in the tree
  (`tests/optimizer/test_extension.py:82-89`'s `registry._models.pop(...)` teardown fixture,
  `examples/fakeshop/test_query/conftest.py:41-47`'s read-only snapshot comparison) either mutates
  both maps together or only reads them, never leaves `_models` short of `_types`. Not a
  regression in any observable behavior today; recorded here as a residual defense-in-depth
  difference rather than left silent, since the artifact's Proof section did not mention it. Not
  severe enough to send back for revision - no reachable test or production path exercises it, and
  fixing it would require the extracted method to special-case an ordering nobody's call site
  needs.
- **Confirmed docstring correction accuracy independently.** `rg '_clear_if_importable'
  django_strawberry_framework/registry.py` still returns exactly one `def` and one call (inside
  `unregister`); `clear()`'s body (lines 568-594) contains no import statement at all, only the
  `iter_subsystem_clears()` replay loop plus the `_type_teardowns` LIFO drain - the corrected
  docstring's claim that `clear()` does not go through this helper is accurate, not merely
  plausible.
- **Confirmed rejected candidates by direct inspection, not by trusting the artifact's prose.**
  `rg 'register_subsystem_clear\('` across the package returns 14 call sites (`auth/mutations.py`,
  `auth/queries.py`, `connection.py`, `filters/__init__.py`, `filters/inputs.py`,
  `forms/inputs.py`, `forms/sets.py` (2x), `mutations/inputs.py`, `mutations/sets.py`,
  `orders/__init__.py`, `orders/inputs.py`, `relay.py`, `rest_framework/inputs.py` (2x),
  `rest_framework/serializer_converter.py`) - matches the artifact's count and each is a thin
  module-owned callback, not a competing dispatch mechanism. `rg 'cycle-safe local-import dance|
  Slice 3 wires' django_strawberry_framework` confirms `orders/inputs.py:17` still carries the
  stale pre-`register_subsystem_clear` phrasing - correctly left alone as another file's docstring,
  not this item's scope. `utils/imports.py`'s module docstring (lines 1-15) still lists
  `registry.py::_clear_if_loaded` as a historical call site; confirmed that symbol does not exist
  anywhere in current `registry.py` (only in stale docs/comments) - correctly this file (well,
  `utils/imports.py`) is not the assigned target, so leaving it alone here is right.
- **Concurrent blockers re-checked against current HEAD, not just re-quoted from the bug-hunt log.**
  All three items the artifact lists under "Blockers / concurrent work observed" are now RESOLVED
  in the current tree, ahead of what the cited `docs/bug_hunt/bug_hunt-0_0_13.md` snapshot showed:
  `uv run pytest tests/auth/test_mutations.py -q` passes 35/35 with no collection error (`rg
  '_clear_if_loaded' tests/auth/test_mutations.py` finds nothing - the stale import is gone);
  `uv run pytest tests/auth/test_queries.py -q` passes 10/10 (`docs/bug_hunt/bug_hunt-0_0_13.md`
  line 12 itself already marks this one "RESOLVED - maintainer reconciled"); and
  `tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_target` no
  longer exists in that file (`rg` finds zero matches) - the maintainer deleted or renamed it per
  the bug-hunt log's own suggested disposition. None of this required any change to `registry.py`;
  it is reported so the maintainer/Worker 0 knows this artifact's Blockers section describes a
  tree state that has since moved on and should not be treated as still-open.
- **Focused regression check.** `uv run pytest tests/test_registry.py -q`: 80 passed, 0 failed;
  `django_strawberry_framework/registry.py` shows 183/183 statements covered (100%) in that run,
  confirming the Opportunity 1 Proof claim that no new test was needed - the existing suite already
  exercises every branch of `_detach_type_from_model` through both callers. Independently reran
  `uv run ruff format --check`, `uv run ruff check`, and
  `uv run python scripts/check_trailing_commas.py --check` against `registry.py`: all clean.

No revision requested. The consolidation is narrowly scoped to the one genuinely shared fragment,
the surrounding divergent logic is verified (not assumed) to differ for good reason, the docstring
correction is verifiable against the current call graph rather than aspirational, and the one
subtle ordering nuance found is confirmed unreachable rather than silently accepted.

Status: verified
