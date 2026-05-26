# Review: `django_strawberry_framework/list_field.py`

Status: verified

## DRY analysis

- **Reuse `types/relay._initial_queryset(target_type)` at `list_field.py:132`.** The default-resolver body builds `target_type.__django_strawberry_definition__.model._default_manager.all()` inline; `types/relay.py:283-290` already centralizes that exact chain as `_initial_queryset(cls) -> _model_for(cls)._default_manager.all()`, and the four Relay node-default sites (`types/relay.py:361, 382, 421, 446`) all consume the helper. The inline chain duplicates the per-package "default queryset for a DjangoType" idiom in the only other place that needs it; it also re-asserts the `__django_strawberry_definition__` attribute path that `_model_for` already encapsulates. Act now — import `_initial_queryset` alongside the existing `_apply_get_queryset_{sync,async}` imports and call `qs = _initial_queryset(target_type)`. The helper is already private (`_`-prefixed) in the same module the file already cross-imports from, so no public-API surface change. Test pinning is already in place (every default-resolver test in `tests/test_list_field.py` traverses this site).

- **Promote the `target_type._django_strawberry_definition__.model._default_manager` lookup chain to a shared "default queryset" helper accessible from outside `types/relay.py` only when a third caller lands.** Defer until either `DjangoConnectionField` or a non-Relay equivalent (KANBAN card `TODO-ALPHA-023-0.0.9`) adds a third call site, OR the cross-module use of `_apply_get_queryset_{sync,async}` plus `_initial_queryset` grows to a fourth callsite outside `types/relay.py`; at that point a `types/_queryset.py` or `types/_visibility.py` module collecting these three helpers under a non-`_`-prefixed name removes the "private helper imported across packages" smell.

## High:

None.

## Medium:

### `_default` re-asserts the default-queryset chain instead of reusing `_initial_queryset`

The default-resolver body at `list_field.py:131-139` reaches into `target_type.__django_strawberry_definition__.model._default_manager.all()` directly:

```django_strawberry_framework/list_field.py:131-139
        def _default(root: Any, info: Info) -> Any:
            qs = target_type.__django_strawberry_definition__.model._default_manager.all()
            if in_async_context():
                # rev6 H1: return the coroutine from ``_apply_get_queryset_async``
                # directly; Strawberry's AwaitableOrValue dispatch awaits it.
                # An inner ``async def`` wrapper would add a redundant coroutine
                # layer with no semantic gain.
                return _apply_get_queryset_async(target_type, qs, info)
            return _apply_get_queryset_sync(target_type, qs, info)
```

`types/relay.py:283-290` already exposes `_initial_queryset(cls)` for exactly this purpose, and `_apply_get_queryset_{sync,async}` are already imported from that module at `list_field.py:20`. Two reasons this matters:

1. The four-attribute chain encodes the package's "default queryset for a registered DjangoType" invariant in two places. If the registered-model lookup ever needs to evolve (e.g., honor a `Meta.default_manager_name`, route through a `default_queryset()` hook, support proxy models), the change must land in two files for the Relay path and the list-field path to stay in lockstep. Today they share one helper; tomorrow they would silently drift.
2. The existing helper already documents the contract ("Centralizes the `cls.__django_strawberry_definition__.model` lookup so both the sync and async assembly paths share one source of truth"). Adding a third in-package use case that bypasses it weakens that contract by example.

Recommended change: add `_initial_queryset` to the existing `from .types.relay import ...` line and replace the inline chain:

```python
from .types.relay import (
    _apply_get_queryset_async,
    _apply_get_queryset_sync,
    _initial_queryset,
)
...
        def _default(root: Any, info: Info) -> Any:
            qs = _initial_queryset(target_type)
            if in_async_context():
                return _apply_get_queryset_async(target_type, qs, info)
            return _apply_get_queryset_sync(target_type, qs, info)
```

The existing test suite covers this site through every default-resolver test (`tests/test_list_field.py::test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset` and the dual-execution / async-`get_queryset` tests), so no new test is required — the behavior is observable through the `get_queryset` exclusion assertions.

## Low:

### Test-docstring line citations drift from current source

Several test docstrings cite `list_field.py` source-line ranges that no longer match the production file's line numbering — they were written against an earlier draft of the file and were not re-pinned when the file's layout settled into its current shape. The drift is not a logic defect (the tests themselves still exercise the right behavior), but the citations mislead a reviewer who follows a test docstring back to source.

Examples:

- `tests/test_list_field.py:198-201` cites "the sync branch at `list_field.py:101`" — the actual sync-default-resolver branch is at `list_field.py:139` (`return _apply_get_queryset_sync(target_type, qs, info)`).
- `tests/test_list_field.py:232-238` cites "the async branch at `list_field.py:94-100`" — the actual async-default-resolver site is at `list_field.py:133-138`.
- `tests/test_list_field.py:284-290` cites "`list_field.py:95`" for the in-async-context branch — the actual `if in_async_context():` is at `list_field.py:133`.
- `tests/test_list_field.py:382-385`, `tests/test_list_field.py:472-481`, `tests/test_list_field.py:660-666` cite "`list_field.py:120-125`" / "`list_field.py:108-117`" for the consumer-resolver wrapper — the actual wrapper sites are at `list_field.py:142-165`.
- `tests/test_list_field.py:520-523` cites "`list_field.py:40-41`" for the async manager coercion — accurate.
- `examples/fakeshop/test_query/test_library_api.py:567-575` cites "`list_field.py:33`" — accurate.

Recommended change: this is a test-side comment-pass concern, not a production-code logic finding. Worker 2 should re-anchor these citations during the comment/docstring pass for this artifact (or, if cheaper, leave the in-test citations alone and let the next 0.0.7 cycle that edits each test re-cite). The drift is a maintenance smell, not a correctness smell.

### `directives: tuple = ()` lacks the element-type generic

The `directives` parameter at `list_field.py:84` is annotated as `tuple = ()` — a bare `tuple` with no element type. Strawberry's `strawberry.field` (which receives the value at `list_field.py:171`) accepts the canonical `Sequence[object] | None` shape, and other call sites in the package that forward `directives` (e.g., the relation-field shapes in `types/relations.py`) tend to use `Sequence[object] = ()` or `tuple[object, ...] = ()`. Bare `tuple` weakens type-checker enforcement on the call site (anything iterable that happens to be a tuple slips through).

Recommended change: tighten to `directives: Sequence[object] = ()` (matching Strawberry's own `directives=` slot) or `directives: tuple[object, ...] = ()`. Both ruff-format clean; both communicate the intent to a reviewer.

### `wrapped` local variable is a single-use rebinding

`list_field.py:141, 165` assign `wrapped = _default` / `wrapped = _wrap`, then `list_field.py:167-172` calls `strawberry.field(resolver=wrapped, ...)`. The intermediate name carries no extra information beyond what `_default`/`_wrap` already convey. The original draft history likely showed three wrappers (sync default, sync wrapper, async wrapper) sharing one `wrapped` slot, and the consolidation to two named inner functions left the intermediate name behind.

Recommended change (cosmetic only): collapse the two assignments into a single return per branch:

```python
        return strawberry.field(
            resolver=_default,  # or _wrap
            description=description,
            ...
        )
```

OR leave the current shape — the name `wrapped` does help a reader who is scanning the bottom of the function for "what gets handed to `strawberry.field`" without re-reading the if/else. Worker 2 may defer this; the duplication cost is minimal.

### `_is_async_callable` docstring is dense for a six-line function

The docstring at `list_field.py:48-71` is 24 lines explaining a 4-line function. The explanation IS correct — both branches are load-bearing, and the rationale for not adding a `functools.partial.func` unwrap is documented — but the comment-to-code ratio invites a reader to skim past the actual logic. The relevant facts (catches `async def`, catches `functools.partial` natively since 3.8, catches `__call__`-async callable instances, does NOT catch sync functions that return awaitables) could compress into a six-line block with the test-name citation kept verbatim.

Recommended change: defer the compression until the next docstring-pass cycle touches this file. The current docstring is correct; reducing it is cosmetic. Pinned via `tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied` and `::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`.

### `_post_process_consumer_*` helpers' two-line bodies repeat across colors

`list_field.py:31-44` defines `_post_process_consumer_sync` and `_post_process_consumer_async`; both are five-line bodies with the same shape (`isinstance Manager → .all()`, `isinstance QuerySet → _apply_get_queryset_{sync,async}`, pass through). The two-color asymmetry is justified by Python's function-color rule — a sync helper cannot `await` and an async helper cannot return the awaitable to a sync caller — but the structural symmetry invites a future "shared coercion + dispatch" helper.

Recommended change: defer until a third color-symmetric pair lands in this package OR until `DjangoConnectionField` (`TODO-ALPHA-023-0.0.9`) adds a third caller of the `Manager → QuerySet → get_queryset` post-processing chain. At that point a single `_post_process_consumer(target_type, result, info, *, is_async)` helper that branches on `is_async` and uses the existing `_apply_get_queryset_async` / `_apply_get_queryset_sync` cleanly absorbs the duplication. Today the duplication is twelve lines, all of them load-bearing, and consolidating two-into-one without the third caller would just push the branching one level deeper.

## What looks solid

### DRY recap

- **Existing patterns reused.** The file imports the canonical visibility-hook helpers `_apply_get_queryset_async` and `_apply_get_queryset_sync` from `types/relay.py:199, 225` (`list_field.py:20`) — the same two helpers the Relay node defaults use (`types/relay.py:361, 382, 421, 446`). The runtime async-detection idiom uses Strawberry's `in_async_context()` import (`list_field.py:16`) the same way `types/relay.py:33` consumes it for `_resolve_node_default` / `_resolve_nodes_default`. The error-message shape `"<Symbol> <constraint>; got <repr>."` at `list_field.py:99, 103, 115, 120` mirrors `types/base.py:_format_unknown_fields_error` (cited in spec line 555). `ConfigurationError` is the single error type for all four guards, consistent with the rest of the package's validation surface.
- **New helpers considered.** A `_initial_queryset(cls)` reuse at `list_field.py:132` is flagged Medium above — not new code, just reuse of the existing helper. A consolidated `_post_process_consumer` helper that branches on `is_async` was considered and deferred-with-trigger above. A `functools.partial.func` manual unwrap branch in `_is_async_callable` was considered upstream (in the pre-merge review) and rejected as dead code on Python 3.10+ — the docstring at `list_field.py:48-71` captures the rejection rationale verbatim and the contract is pinned by `tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied`.
- **Duplication risk in the current file.** The `isinstance Manager → .all()` / `isinstance QuerySet → _apply_get_queryset_*` shape repeats across `_post_process_consumer_sync` (`list_field.py:31-36`) and `_post_process_consumer_async` (`list_field.py:39-44`); this is intentional Python function-color symmetry, captured under the deferred Low above. The "field-wrapper coerces `Manager → QuerySet` before applying `get_queryset`" invariant at `list_field.py:33, 41` is documented as the "rev4 M1" rule and tied to a live-HTTP test (`examples/fakeshop/test_query/test_library_api.py:564` for sync, `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_manager_return_gets_get_queryset_applied` for async).

### Other positives

- The own-class registration guard at `list_field.py:112-118` is the strict invariant the spec calls out (Decision 5, spec line 548; rev3 M3 anchor): `definition.origin is target_type` rather than `hasattr(target_type, "__django_strawberry_definition__")`. The inline comment (`list_field.py:105-111`) walks through the MRO-inheritance failure mode that `hasattr` would silently accept and cites the `types/base.py:251` assignment site for the strict-invariant rationale. The pinning test (`tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta`) declares a `ParentCategoryType` with `Meta` and a `ChildCategoryType` without — exercising exactly the inheritance failure mode the comment names.
- Async-detection asymmetry between the default-resolver path and the consumer-resolver path is documented at `list_field.py:121-128` and at the spec Decision 2 "Async-detection asymmetry — intentional, not a harmonization candidate". The `_default` path uses runtime `in_async_context()` because the same factory output dispatches under both `schema.execute_sync` and `await schema.execute`; the consumer-wrapper path commits per-construction via `inspect.iscoroutinefunction(user_resolver)` because Strawberry inspects resolver signatures once at schema-construction time. The dual-execution test (`tests/test_list_field.py::test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`) pins both branches of the runtime detection in a single test.
- `_apply_get_queryset_async(target_type, qs, info)` is returned directly from the sync entry point at `list_field.py:138` rather than wrapped in an inner `async def`. The comment at `list_field.py:134-137` explains the rationale (Strawberry's `AwaitableOrValue` dispatch awaits the coroutine; an inner wrapper is a redundant coroutine layer). This is correct — `_apply_get_queryset_async` is an `async def` and returns a coroutine when called, which Strawberry's middleware then awaits.
- The `await user_resolver(...) → _post_process_consumer_async` ordering at `list_field.py:151-155` is correct (rev4 H2): the consumer coroutine is awaited BEFORE the result is handed to `_post_process_consumer_async` so the `isinstance(result, models.QuerySet)` check sees the awaited value, not the coroutine itself. Pinned by `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied`.
- Outer-list nullability is correctly delegated to the consumer's class-attribute annotation (rev2 H2, spec line 14): the constructor does NOT accept a `nullable_list=` argument, and the two introspection tests (`tests/test_list_field.py::test_djangolistfield_nullable_outer_via_consumer_annotation` and `::test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`) prove the `list[T] | None` → `[T!]` and `list[T]` → `[T!]!` mappings ride entirely on Strawberry's class-body annotation walk. The test plan's previously-considered `nullable_list=` bool guard was correctly DROPPED (`tests/test_list_field.py:175-177` records the rev2 H2 drop).
- Optimizer cooperation rides the existing root-gate at `optimizer/extension.py:541-543` — no new walker code, no new marker on `info.context`, no DjangoListField-specific code path. The root-position test (`tests/test_list_field.py::test_djangolistfield_at_root_position_is_optimized`) and the FK-id-elision test (`tests/test_list_field.py::test_djangolistfield_fk_id_elision_survives`) pin that the same optimizer pipeline that already serves `strawberry.field(resolver=...)` root resolvers serves `DjangoListField` root resolvers identically. The pinned `assertNumQueries(2)` value (not `<= N`) catches a refactor that quietly changes the per-query count.
- `Meta.primary` interaction is correctly handled by accepting an explicit `DjangoType` argument rather than a model class (Decision 6, spec lines 568-590). The two pinning tests (`test_djangolistfield_with_meta_primary_true_returns_primary_queryset` and `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset`) prove that pointing the field at the primary vs the secondary picks the corresponding `get_queryset` filter — no registry lookup, no implicit `Meta.primary` reordering, no cache-poisoning risk.
- `_is_async_callable` deliberately does NOT catch the "sync function that returns an awaitable from somewhere else" shape (`list_field.py:67-70`). The contract is explicit: resolvers signal sync-vs-async through the standard coroutine-function flag, not through opaque awaitable returns. This is a reasonable boundary — the alternative (post-call `inspect.isawaitable(result)` in both wrappers) would couple the field's color choice to the resolver's return shape and turn a typed contract into a runtime branch.
- The `# noqa: N802  # PascalCase for graphene-django parity` exemption at `list_field.py:78` is the right call — the function is a factory whose consumer-facing usage (`DjangoListField(BranchType)`) reads like a class instantiation. Mirrors `graphene_django.DjangoListField` and `graphene_django.DjangoConnectionField`.

### Summary

`list_field.py` is the new-in-0.0.7 factory entry point for non-Relay `list[T]` root Query fields. The factory-function shape (vs a descriptor class) matches the "DRF first, strawberry second" stance from `START.md` and the graphene-django parity the spec calls out. The four constructor-site guards fire at the line that wrote `DjangoListField(...)` rather than at finalize time, with the third guard's `definition.origin is target_type` strict-invariant correctly catching the MRO-inheritance failure mode that `hasattr` would silently accept. Sync and async branch coverage is thorough: the default-resolver path commits sync-vs-async per-call via `in_async_context()`, the consumer-resolver path commits per-construction via `inspect.iscoroutinefunction` (including the `__call__`-async callable-instance and `functools.partial`-wrapped cases), and the `_post_process_consumer_*` helpers symmetrically apply `Manager → QuerySet` coercion before `target_type.get_queryset(...)` runs. Outer-list nullability is correctly delegated to the consumer's class-attribute annotation, and optimizer cooperation rides the existing root-gate with no new code. One Medium finding: the default-resolver body re-asserts the `target_type.__django_strawberry_definition__.model._default_manager.all()` chain inline at `list_field.py:132` instead of reusing the existing `types/relay._initial_queryset(target_type)` helper — a one-line DRY win that keeps the four-attribute lookup chain in a single source of truth. Five Lows are documentation / cosmetic / deferred-DRY only.

---

## Fix report (Worker 2)

Consolidated single-spawn pass per REVIEW.md "All-Lows-forward-looking or DRY-equivalent" clause — Medium 1 is a pure DRY delegation to a canonical helper (`_initial_queryset`) whose docstring already documents the post-delegation contract; Low 2 is `Sequence[object]` type-narrowing inside an existing pinned `directives` contract (no behaviour change, still ruff-format clean); Lows 3, 4, 5 are explicitly forward-looking per Worker 1's own quoted prose ("Worker 2 may defer this", "defer the compression until the next docstring-pass cycle touches this file", "defer until a third color-symmetric pair lands"); Low 1 (test-docstring citation drift) is the artifact's own comment-pass concern and is addressed in the Comment pass section below.

### Files touched
- `django_strawberry_framework/list_field.py:20` — added `_initial_queryset` to the `.types.relay` import alongside the existing `_apply_get_queryset_{sync,async}` imports.
- `django_strawberry_framework/list_field.py:132` — replaced `target_type.__django_strawberry_definition__.model._default_manager.all()` with `_initial_queryset(target_type)` (Medium 1).
- `django_strawberry_framework/list_field.py:10` — added `Sequence` to the `from collections.abc import` line (supporting import for Low 2).
- `django_strawberry_framework/list_field.py:84` — tightened `directives: tuple = ()` to `directives: Sequence[object] = ()` (Low 2). Matches Strawberry's own `directives=` slot shape.

### Tests added or updated
None — the existing default-resolver test surface already pins the post-delegation behaviour through every `get_queryset` exclusion assertion (per the artifact's explicit "the behavior is observable through the `get_queryset` exclusion assertions" note). The `directives` annotation change is type-system-only and does not alter the runtime contract Strawberry sees at `list_field.py:171`.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged.
- `uv run ruff check --fix .` — pass / All checks passed.
- No focused pytest run per `AGENTS.md` line 14 / `START.md` "Do not run pytest after edits".

### Notes for Worker 3
- DRY delegation verified against `types/relay.py:283-290` — `_initial_queryset(cls)` returns `_model_for(cls)._default_manager.all()` which expands to `cls.__django_strawberry_definition__.model._default_manager.all()` (the exact chain replaced inline). The helper is already imported across packages (this file already pulls `_apply_get_queryset_{sync,async}` from the same module at line 20), so no new public-API surface and no circular-import risk.
- `_initial_queryset` is named with a single leading underscore; the artifact's second DRY observation ("Promote ... to a shared 'default queryset' helper accessible from outside `types/relay.py` only when a third caller lands") notes the cross-package private-helper smell but explicitly defers the rename until a third caller appears (`DjangoConnectionField` / `TODO-ALPHA-023-0.0.9`).
- Lows 3, 4, 5 intentionally not edited — Worker 1's prose explicitly defers each. Low 1 is a comment-pass concern, addressed in the next section.
- Shadow file consulted at `docs/shadow/list_field.overview.md` — control-flow hotspots (`_default` branch, `_wrap` async/sync split, `_post_process_consumer_*`) match the line numbers Worker 1 cites; no marker regressed by the edit.

---

## Comment/docstring pass

### Files touched
- `tests/test_list_field.py:200` — re-anchored sync default-resolver citation from `list_field.py:101` to `list_field.py:139` (the actual `return _apply_get_queryset_sync(target_type, qs, info)` line).
- `tests/test_list_field.py:236` — re-anchored async default-resolver citation from `list_field.py:94-100` to `list_field.py:133-138`.
- `tests/test_list_field.py:289` — re-anchored runtime `in_async_context()` citation from `list_field.py:95` to `list_field.py:133`.
- `tests/test_list_field.py:382` — re-anchored sync consumer-resolver wrapper citation from `list_field.py:120-125` (with `line 121` inner) to `list_field.py:158-163` (with `line 159` inner).
- `tests/test_list_field.py:424` — re-anchored second sync consumer-resolver wrapper citation from `list_field.py:120-125` to `list_field.py:158-163`.
- `tests/test_list_field.py:473` — re-anchored async consumer-resolver wrapper citation from `list_field.py:108-117` (with `lines 113-117` inner) to `list_field.py:146-155` (with `lines 151-155` inner).
- `tests/test_list_field.py:662` — re-anchored async consumer-resolver wrapper citation from `list_field.py:108-117` to `list_field.py:146-155`.

The two accurate citations Worker 1 flagged (`tests/test_list_field.py:520-523` on `list_field.py:40-41` and `examples/fakeshop/test_query/test_library_api.py:567-575` on `list_field.py:33`) are unchanged because the artifact confirms they already match the current source.

### Per-finding dispositions
- Medium 1: accept-and-edit. DRY delegation to `_initial_queryset` landed in the Fix report above. Semantics preserved by construction — the helper expands to the exact chain that was inlined. The default-resolver test surface (`test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset`, the dual-execution test, the async-`get_queryset` test) traverses the post-delegation path identically.
- Low 1: accept-and-edit (this pass). Seven test docstrings re-anchored to current source lines per the mapping above; the comment-pass disposition was the cheaper option Worker 1 named (vs. leaving them for the next per-test edit cycle), so the artifact closes with no remaining drift.
- Low 2: accept-and-edit. `directives: tuple = ()` → `directives: Sequence[object] = ()` landed in the Fix report — type tightening inside an existing pinned contract, matches Strawberry's own slot shape, no runtime behaviour change.
- Low 3: defer-with-trigger. Worker 1 explicitly noted "Worker 2 may defer this; the duplication cost is minimal" and the `wrapped` intermediate name still helps a reader scan to "what gets handed to `strawberry.field`"; the cosmetic-only cleanup is left for the next cycle that touches the factory's return shape.
- Low 4: defer-with-trigger. Worker 1 explicitly noted "defer the compression until the next docstring-pass cycle touches this file. The current docstring is correct; reducing it is cosmetic." The docstring still correctly documents both load-bearing checks and the rejected `partial.func` unwrap.
- Low 5: defer-with-trigger. Worker 1 explicitly noted "defer until a third color-symmetric pair lands in this package OR until `DjangoConnectionField` (`TODO-ALPHA-023-0.0.9`) adds a third caller". The two-color symmetry stays intact; the consolidation trigger lives at the KANBAN card.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged.
- `uv run ruff check --fix .` — pass / All checks passed.

### Notes for Worker 3
- Citations re-anchored against the post-delegation source line numbers (the M1 edit was line-internal at line 132 and added no new line, so the cited line numbers Worker 3 should verify match the final tree exactly).
- The two citations Worker 1 confirmed accurate are deliberately left alone (`tests/test_list_field.py:519-541` on `list_field.py:40-41` and the example live-HTTP cite on `list_field.py:33`).

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Three lined-up citations:

1. `AGENTS.md` line 21: "Do not update CHANGELOG.md unless explicitly instructed."
2. The active plan `docs/review/review-0_0_7.md` is silent on changelog authorisation for the `rev-list_field.md` cycle.
3. Precedent chain: the four prior 0.0.7 cycles (`rev-_django_patches.md`, `rev-apps.md`, `rev-conf.md`, `rev-exceptions.md`) all closed `Not warranted`. The fix in this cycle is the same shape (DRY delegation to a canonical helper, type tightening inside an existing pinned contract, test-docstring re-anchoring) — none of which is consumer-visible. The default-resolver behaviour is unchanged (the helper expands to the exact chain it replaces), `Sequence[object]` is a stricter form of the already-accepted `tuple = ()` shape (any prior caller passing a tuple still type-checks), and test-docstring citation re-anchoring is internal documentation. Per REVIEW.md "Not warranted" examples this cycle's edits fit "refactors against canonical helpers", "docstring polish", and "type tightening inside an existing pinned contract" simultaneously.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged.
- `uv run ruff check --fix .` — pass / All checks passed.

---

## Verification (Worker 3)

### Logic verification outcome
- Medium 1 (DRY delegation to `_initial_queryset`): accepted. `git diff -- django_strawberry_framework/list_field.py` shows the four cited line changes — import addition at line 20 (`_initial_queryset` joined to the existing `.types.relay` import), inline chain replaced at line 132 with `_initial_queryset(target_type)`, `Sequence` joined to the `from collections.abc import` line at line 10, and `directives: Sequence[object] = ()` at line 84. Semantics preserved by construction — `types/relay.py:283-290` defines `_initial_queryset(cls) -> _model_for(cls)._default_manager.all()`, and `_model_for(cls)` at line 280 returns `cls.__django_strawberry_definition__.model`; the helper expansion is identical to the inlined chain. The existing default-resolver test surface pins the post-delegation behavior through every `get_queryset` exclusion assertion as the artifact notes.
- Low 1 (test-docstring citation drift): accepted as comment-pass. `git diff -- tests/test_list_field.py` shows exactly the 7 docstring-only changes Worker 2 listed (lines 200, 236, 289, 382, 424, 473, 662) re-anchoring source-line citations to the post-edit positions (`list_field.py:139`, `:133-138`, `:133`, `:158-163` x2, `:146-155` x2). No test logic changed — every diff hunk is inside a docstring block.
- Low 2 (`Sequence[object]` type tightening): accepted. Type-system-only change, matches Strawberry's own `directives=` slot shape, no runtime behavior change.
- Lows 3, 4, 5 (defer-with-trigger): accepted. Each deferral preserves Worker 1's verbatim prose ("Worker 2 may defer this; the duplication cost is minimal", "defer the compression until the next docstring-pass cycle touches this file", "defer until a third color-symmetric pair lands in this package OR until `DjangoConnectionField` (`TODO-ALPHA-023-0.0.9`) adds a third caller") at the cited artifact lines 93, 99, 105.

### DRY findings disposition
DRY observation 1 (reuse `_initial_queryset`) implemented in M1. DRY observation 2 (promote to a non-`_`-prefixed shared helper) explicitly deferred to a third-caller trigger (`DjangoConnectionField` / `TODO-ALPHA-023-0.0.9`) — Worker 2's notes echo the trigger.

### Temp test verification
None used — the artifact's claim that "the behavior is observable through the `get_queryset` exclusion assertions" via the existing default-resolver test surface is grep-discoverable at `tests/test_list_field.py::test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset` and the dual-execution / async-`get_queryset` tests Worker 1 named.

### Changelog verification
`git diff -- CHANGELOG.md` is empty, matching the artifact's `Not warranted` disposition. The disposition cites three legs: AGENTS.md line 21, plan silence in `review-0_0_7.md`, and the four prior 0.0.7 cycles' precedent — comfortably clears the two-citation bar. Internal-only framing is honest: M1 is a DRY delegation expanding to the exact chain it replaces, L2 is a stricter type form of an already-accepted shape, L1 is test-docstring citation re-anchoring. No public-API surface touched.

### Validation
- `uv run ruff format --check .` — 118 files already formatted.
- `uv run ruff check .` (no `--fix`) — All checks passed.

### Verification outcome
`cycle accepted; verified`
