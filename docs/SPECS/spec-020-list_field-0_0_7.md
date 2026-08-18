# Spec: `DjangoListField` (non-Relay list)

Target release: `0.0.7`.
Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-020-0.0.7`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`DjangoType`][glossary-djangotype], [`Meta.fields`][glossary-metafields], [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook], [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`Relation handling`][glossary-relation-handling], [`Meta.primary`][glossary-metaprimary], [`Relay Node integration`][glossary-relay-node-integration], [`DjangoListField`][glossary-djangolistfield]), [`KANBAN.md`][kanban] card `DONE-020-0.0.7`, predecessor spec [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (Decision 9 - async `get_queryset` shape) and [`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018] (multiple `DjangoType`s per model).

Deliberation - the six revisions of review feedback, the alternatives each Decision rejected, the risks-and-open-questions record, and every claim this spec once made and may no longer make - lives in [`spec-020-list_field-0_0_7-rationale.md`][spec-020-rationale]. This file states only the contract that holds at `HEAD`.

**The card shipped as `016`.** The build commits are `7e8632f6` and `06c8df92` (2026-05-20 / 2026-05-21); the 2026-07-30 board renumber moved the card to `020` and renamed the spec. `CHANGELOG.md`'s tracking label and the in-tree scaffold references still carry the pre-renumber number - see the rationale companion's provenance section before chasing `git log` for "spec-020".

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoListField`][glossary-djangolistfield] — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 5](#slice-checklist).
- [`DjangoType`][glossary-djangotype] — the type class the field binds to; the field's queryset is derived from `Meta.model` (see [Decision 2](#decision-2--default-resolver-shape)).
- [`Meta.model`][glossary-metamodel] — the source of `model._default_manager` (see [Decision 2](#decision-2--default-resolver-shape)).
- [`Meta.fields`][glossary-metafields] — independent of this card; `DjangoListField` does not introspect a type's selected fields.
- [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] — applied to the default queryset before return (see [Decision 3](#decision-3--get_queryset-and-async-symmetry)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — root-gated planning already shipped; the field must return a `QuerySet` so the existing `info.path.prev is None` gate fires (see [Decision 4](#decision-4--optimizer-cooperation)).
- [`Relation handling`][glossary-relation-handling] — many-side relations currently produce `list[T]` via generated resolvers; this card adds the symmetric **root**-list primitive but does NOT change relation-side many-list shapes (see [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields)).
- [`Meta.primary`][glossary-metaprimary] — multiple `DjangoType`s per model; `DjangoListField(SecondaryType)` is the explicit-target shape that side-steps the registry lookup ambiguity (see [Decision 6](#decision-6--metaprimary-interaction)).
- [`Relay Node integration`][glossary-relay-node-integration] — non-Relay list shape is the entire point of this card; the Relay sibling lives under [`DjangoConnectionField`][glossary-djangoconnectionfield] in `DONE-030-0.0.9` (see [Decision 8](#decision-8--out-of-scope-boundary-with-djangoconnectionfield)).
- [`ConfigurationError`][glossary-configurationerror] — raised by the field's constructor when the argument is not a registered `DjangoType` subclass (see [Decision 5](#decision-5--validation--error-shapes)).

Project conventions to follow:

- [`AGENTS.md`][agents] — schema testing via `schema.execute_sync`; live `/graphql/` HTTP coverage in `examples/fakeshop/test_query/`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 5](#slice-checklist) grants that permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; release-bump checklist.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 5.
- [`docs/TREE.md`][tree] — package layout; tests mirror source one-to-one; flat single-file Layer-3 modules at the package root pair with `tests/test_<module>.py`.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 0: Pre-implementation verification (no code lands; throw-away spike)
  - [ ] **Confirm `info: Info` import path** — run `python -c "from strawberry.types import Info; print(Info.__module__)"` against the installed Strawberry; confirm the import raises no `ImportError`. There is deliberately no assertion on the module path itself; record `Info.__module__` in the slice's build report so a future maintainer can see which module path the installed Strawberry exposed. If the import fails, fall back to `import strawberry; Info = strawberry.Info` and pin that shape in Decision 1. Without this verification, Slice 1's resolver signatures may compile but fail schema construction.
  - [ ] Write a throw-away stub in a sandbox using an annotated module-level resolver — a bare-lambda `lambda root, info: ...` resolver raises `MissingArgumentsAnnotationsError` at `strawberry.field(resolver=...)` call time on the installed Strawberry, BEFORE `@strawberry.type`'s class-body walk runs, so the lambda cannot be used to verify the class-body-discovery contract; the annotated `def` shape below is the only viable form and matches the `(root: Any, info: Info)` signature pinned for Slice 1:
    ```python
    from typing import Any
    from strawberry.types import Info
    import strawberry

    def _stub_resolver(root: Any, info: Info):
        return target_type.__django_strawberry_definition__.model._default_manager.all()

    def DjangoListFieldStub(target_type):
        return strawberry.field(resolver=_stub_resolver)
    ```
  - [ ] Assign it to a Query attribute under `@strawberry.type`: `all_branches: list[BranchType] = DjangoListFieldStub(BranchType)`.
  - [ ] Build a Strawberry schema and confirm the field is picked up with annotation-derived GraphQL type `[BranchType!]!` — the verification mechanism is an introspection query, not `print(schema)` or SDL substring assertions, which are fragile across Strawberry minor versions. Concretely: `result = schema.execute_sync('{ __type(name: \"Query\") { fields { name type { kind ofType { kind ofType { kind name } } } } } }')`; locate `fields[name == "allBranches"]`; assert the outer `type.kind == "NON_NULL"`, the wrapped `ofType.kind == "LIST"`, the inner `ofType.ofType.kind == "NON_NULL"`, and the leaf `ofType.ofType.ofType.name == "BranchType"`. Run a real `schema.execute_sync('{ allBranches { id name } }')` query afterward and confirm rows return.
  - [ ] Build a second stub that uses an explicitly annotated resolver — `def resolver(root: Any, info: Info)` with `from strawberry.types import Info` — and confirm Strawberry's schema construction accepts it without raising `MissingArgumentsAnnotationsError`; this is the import verification's other half.
  - [ ] Repeat with `list[BranchType] | None` annotation; confirm the rendered type is `[BranchType!]` (nullable outer).
  - [ ] If all shapes work end-to-end: proceed to Slice 1 with the factory-function design intact.
  - [ ] If either shape does NOT work: the fallback shape (directly construct a `StrawberryField` with explicit `python_name` / `type_annotation`) is promoted to Decision 1; Slice 1 is reauthored before any production code lands.
  - [ ] No tests committed in this slice; the spike is local exploration. The Slice 1 implementation begins only after this Slice's checkboxes are ticked.
- [ ] Slice 1: Module + factory function
  - [ ] New flat module `django_strawberry_framework/list_field.py` (placement decision: see [Decision 1](#decision-1--module-location-mechanism--public-export)) housing the `DjangoListField` symbol.
  - [ ] Implement `DjangoListField` as a **factory function**. The factory returns `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)`. Consumer usage is `all_branches: list[BranchType] = DjangoListField(BranchType)` — Strawberry reads the consumer's class-attribute annotation for the outer GraphQL list shape (`list[BranchType]` → `[BranchType!]!`, `list[BranchType] | None` → `[BranchType!]`), so the factory does NOT need to override the annotation.
  - [ ] Suppress `ruff` rule **N802** on the `def DjangoListField(...)` line with `# noqa: N802  # PascalCase for graphene-django parity — consumer usage is `DjangoListField(BranchType)``. The repo's `pyproject.toml` enables `N` (pep8-naming) in `[tool.ruff.lint]` and N802 flags PascalCase function names; the PascalCase shape is intentional graphene-django parity. Per-line `noqa` is preferred over a per-file ignore because `list_field.py` only has one PascalCase definition and a wider exception would hide future violations.
  - [ ] Capture `target_type` via closure (the resolver signature is the Strawberry-native `(root: Any, info: Info)`, NOT `(type_cls, info)` or `(root, info, **kwargs)`; `target_type` is looked up from the enclosing scope, not from a first positional argument). Imports: `from typing import Any` and `from strawberry.types import Info` at the top of `list_field.py`. Drop `**kwargs` from every resolver signature in this card; Strawberry treats every parameter as a GraphQL argument by default, and this card does not add any.
  - [ ] Default resolver body — sync path:
    1. `qs = initial_queryset(target_type)` — the shared `model._default_manager.all()` seed at `django_strawberry_framework/utils/querysets.py::initial_queryset`.
    2. `qs = apply_type_visibility_sync(target_type, qs, info)` — the shared sealed-boundary visibility helper; an async `get_queryset` met on the sync path is rejected with `SyncMisuseError` per [Decision 3](#decision-3--get_queryset-and-async-symmetry).
    3. `return bounded_rows(qs, info, max_rows, trusted=trusted_max_rows)` — the row bound is applied LAST, after the visibility hook has composed onto the unsliced source.
  - [ ] Default resolver body — async path:
    1. `qs = initial_queryset(target_type)`.
    2. `qs = await apply_type_visibility_async(target_type, qs, info)`.
    3. `return await bounded_rows_async(qs, info, max_rows, trusted=trusted_max_rows)`.
  - [ ] Async detection uses the same `in_async_context` hook the Relay defaults use — pin the import as `from strawberry.utils.inspect import in_async_context` (already imported at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"`).
  - [ ] Optional `resolver=` constructor argument that overrides the default body. When supplied, wrap the consumer resolver so a `Manager`/`QuerySet` return value is fed through `target_type.get_queryset(qs, info)` (graphene-django parity). The wrapper itself does the `Manager → QuerySet` coercion BEFORE applying `get_queryset` (the optimizer's downstream `Manager` coercion is a safety net, not a substitute). **Three arms, chosen at construction time**: an async generator function (`django_strawberry_framework/utils/typing.py::is_async_generator_callable`), any other async callable (`django_strawberry_framework/utils/typing.py::is_async_callable` — the wrapper-aware superset of `inspect.iscoroutinefunction`, which also sees an `async def __call__` instance, a `functools.partial`, and a raw `staticmethod` descriptor), or a plain sync callable. The async-callable arm builds an `async def` wrapper that `await`s the consumer's coroutine BEFORE the isinstance check, so an async resolver returning a `QuerySet` still gets `get_queryset` applied. The sync arm additionally detects an async-only iterable return at call time and rejects it with `SyncMisuseError` when execution is synchronous. Python `list` returns from any arm pass through unchanged. There is no runtime-coroutine fallback and none is needed: a sync resolver that returns a coroutine, a custom awaitable, or a `Future` is rejected loudly (see [Edge cases and constraints](#edge-cases-and-constraints)). Optimizer cooperation still applies because the extension is root-gated against `info.path.prev is None` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`); a consumer resolver returning a `QuerySet` is planned exactly like the default.
  - [ ] Optional `description=` / `deprecation_reason=` / `directives=` pass-through into the inner `strawberry.field(...)` call so the symbol is feature-comparable to `strawberry.field(...)` at the metadata level, plus the `max_rows=` / `trusted_max_rows=` row-bound arguments validated per [Decision 5](#decision-5--validation--error-shapes).
  - [ ] Re-export from `django_strawberry_framework/__init__.py` in alphabetical order ([Decision 1](#decision-1--module-location-mechanism--public-export)); add `"DjangoListField"` to `__all__`.
  - [ ] Update `tests/base/test_init.py`'s pinned `__all__` assertion.
  - [ ] Remove the scaffold TODOs at this site — covers `django_strawberry_framework/list_field.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`. Ruff's `ERA001` catches commented-out code but not `# TODO:` markers, so explicit cleanup is the only protection against the scaffold TODOs landing in main.
- [ ] Slice 2: Validation
  - [ ] Constructor validates that the argument is a class AND is `issubclass(arg, DjangoType)` AND carries its **own** registered definition (`definition.origin is arg`, never `hasattr`) — per [Decision 5](#decision-5--validation--error-shapes). Errors raise `ConfigurationError` with the same `<Symbol> <constraint>; got <repr>.` shape pattern (`django_strawberry_framework/types/base.py::_format_unknown_fields_error` style) reused for consistency.
  - [ ] `resolver=`, when supplied, is callable; otherwise `ConfigurationError`.
  - [ ] Tests for validation cluster live in `tests/test_list_field.py`.
- [ ] Slice 3: Optimizer + `get_queryset` cooperation tests
  - [ ] Package-internal tests under `tests/test_list_field.py` covering: default-resolver shape, `cls.get_queryset` invocation, sync coroutine rejection, async path awaits sync + async `get_queryset`, **sync consumer `resolver=` return value receives `get_queryset` when it is a `Manager`/`QuerySet`**, Python-`list` sync consumer returns pass through unchanged, **async consumer `resolver=` returning a `Manager`/`QuerySet` receives `get_queryset`**, Python-`list` async consumer returns pass through unchanged, nullable-outer-via-consumer-annotation produces `[T!]`, non-nullable-outer default produces `[T!]!`, `DjangoListField` at root position is optimized, [FK-id elision][glossary-fk-id-elision] survives, `Meta.primary` interaction (explicit primary, explicit secondary). The default-resolver `get_queryset` filter and the nullable-outer rendering are pinned at the live `/graphql/` tier instead of package-internally — see [Test plan](#test-plan).
  - [ ] Remove the scaffold TODOs at this site — covers the TODO stubs in `tests/test_list_field.py` as they get replaced with real test bodies.
- [ ] Slice 4: Live HTTP coverage
  - [ ] **Add new** root fields to `examples/fakeshop/apps/library/schema.py` — `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` for the default-resolver path, `all_library_branches_via_list_field_nullable: list[BranchType] | None` for the nullable-outer rendering, and `all_library_branches_via_list_field_manager_resolver` for a consumer resolver returning a `Manager` (do NOT replace the existing `all_library_branches` because its `order_by("id")` is depended on by `test_library_relation_override_shapes_http_response_data`). Every pre-existing `@strawberry.field` resolver stays unchanged.
  - [ ] Add a new HTTP test in `examples/fakeshop/test_query/test_library_api.py` (or extend an existing test in the same file) asserting: (a) the new field returns the expected branches via `/graphql/`, (b) the optimizer planned `prefetch_related` / `select_related` correctly for a nested selection (via `assertNumQueries` / the existing SQL-sniffer pattern). The `cls.get_queryset` cooperation coverage lives in the package-internal `tests/test_list_field.py` tests (adding a real `BranchType.get_queryset` filter would mutate every `BranchType` path in the library schema and is out of scope here).
  - [ ] Remove the scaffold TODOs at this site — covers `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/test_query/test_library_api.py`.
- [ ] Slice 5: Promotion + docs + version
  - [ ] Flip [`DjangoListField`][glossary-djangolistfield] from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`][glossary]; update the public exports list at the top and the index table.
  - [ ] Update [`README.md`][readme], [`docs/README.md`][docs-readme], [`GOAL.md`][goal], and [`TODAY.md`][today] where `DjangoListField` is currently called out as unshipped or "wait for":
    - `README.md` — the `## Status` section's "Earlier alpha surfaces" list (which runs newest-first and is the file's own idiom for a shipped cut) carries a `0.0.7` entry leading with `DjangoListField`, in that list's existing one-line-per-version voice; `KANBAN.md #"## Done"` holds the authoritative content for the cut.
    - `docs/README.md` — the "Shipped today (`0.0.6`)" → "Shipped today (`0.0.7`)" bullet list under "Today and coming next".
    - `GOAL.md` — Migration shape sections mention `DjangoListField` indirectly through `graphene-django` migration; ensure the migration story is now reachable.
    - `TODAY.md` — `DjangoListField` is absent from the wait-for list and named among the capabilities the `library` app demonstrates. The file's capability list is compact by design, so no individual root field is named there.
  - [ ] `docs/TREE.md` — add `list_field.py` to the current on-disk layout AND to the target layout (a flat single-file Layer-3 module per the TREE convention); add `tests/test_list_field.py` to the current test-tree section. **Remove the `DjangoListField` mention from the existing `connection.py # [alpha] DjangoConnectionField + DjangoListField` line** so the target layout doesn't advertise two homes for the symbol.
  - [ ] `KANBAN.md` — move `DONE-020-0.0.7` to Done with `DONE-NNN-0.0.7` (next available number; the column-move pass renumbers as usual). The past-tense Done body MUST reflect the add-only posture: "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" rather than the original card text's "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" — an intentional departure from the original card text.
  - [ ] `CHANGELOG.md` — `[0.0.7]` Added entry: `DjangoListField` (non-Relay `list[T]` field for **root Query fields** with default `model._default_manager.all()` resolver, `cls.get_queryset` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns, optimizer cooperation through root-gating).
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card): see [Decision 10](#decision-10--joint-007-cut). This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion — those move when the last of the five `0.0.7` WIP cards ships.
  - [ ] Final gates:
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run pytest` passes with 100% package coverage (`fail_under = 100`).
    - [ ] One new public export (`DjangoListField`) — the only addition to `__all__` in this slice.

## Problem statement

`DjangoType` users cannot declare a model-backed `list[T]` root field through the package; every root resolver returning a `list[T]` of a `DjangoType` today is hand-rolled. The `library` example schema makes this concrete — `examples/fakeshop/apps/library/schema.py::Query` declares **eight** `@strawberry.field` resolvers, every one of which has the same shape:

```python
@strawberry.field
def all_library_branches(self) -> list[BranchType]:
    return models.Branch.objects.order_by("id")
```

The shape is identical across the seven non-`prefetched` resolvers (`all_library_branches`, `all_library_shelves`, `all_library_books`, `all_library_genres`, `all_library_patrons`, `all_library_membership_cards`, `all_library_loans`) — only the model and target type change. The eighth (`all_library_prefetched_books`) is a separate concern that exercises the queryset-diffing path and intentionally stays as a `@strawberry.field`.

Consequences without a `DjangoListField`:

- Every Django app that wants a model collection through GraphQL writes a one-line root resolver. The library example proves the boilerplate is mechanical and identical.
- `graphene-django` migrants lose a primitive they already know (`/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoListField` — `class DjangoListField(Field)` is the default list shape for graphene-django).
- The `cls.get_queryset(...)` visibility hook is silently bypassed unless the consumer remembers to thread it through every hand-rolled resolver — the [`Visibility filtering via get_queryset`][today-visibility-filtering-via-get_queryset] section in `TODAY.md` lays out the exact boilerplate consumers have to write today, and the package has no symbol that does it automatically.
- `TODAY.md`'s "fakeshop should wait for" list (`TODAY.md #"## What the fakeshop example should wait for"`) includes `DjangoConnectionField` but not `DjangoListField`; that omission is symptomatic — the package does not currently distinguish the simple-list case from the Relay-connection case.

`0.0.6` shipped every architectural seam this slice needs: `DjangoTypeDefinition.model` for the queryset source, `cls.get_queryset(...)` for the visibility hook, `DjangoOptimizerExtension`'s root-gated `info.path.prev is None` planning hook (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`), and the sync + async visibility-hook application in [`spec-015-relay_interfaces-0_0_5.md`][spec-015]. `0.0.7` populates and applies that seam.

The target is not a full connection/query-field release. The target is to make `list[T]` **root** fields possible in the package's `class Meta` style, while preserving the existing optimizer behavior, the `get_queryset` cooperation contract, and the `Meta.primary` registry semantics. Nested non-root usage of `DjangoListField` is functional (the field still produces a list resolver) but is NOT root-optimized in `0.0.7` per [Decision 4](#decision-4--optimizer-cooperation).

## Current state

- `django_strawberry_framework/__init__.py #"__all__"` re-exports [`BigInt`][glossary-bigint-scalar], `DjangoOptimizerExtension`, `DjangoType`, [`OptimizerHint`][glossary-optimizerhint], `__version__`, `auto`, [`finalize_django_types`][glossary-finalize-django-types] — and only those seven. That is the pre-card baseline this spec was authored against.
- The `library` example schema at `examples/fakeshop/apps/library/schema.py::Query` carries eight hand-rolled root list resolvers, seven of which share the identical "queryset over model.objects ordered by id" shape (see the [Problem statement](#problem-statement) for the exact code).
- The `products` example schema at `examples/fakeshop/apps/products/schema.py::Query` has the same shape: four `@strawberry.field` resolvers returning `Model.objects.all()` directly. The post-`TODO-ALPHA-022` future shape in the comments (`examples/fakeshop/apps/products/schema.py::Query #"Future shape"`) jumps straight from `@strawberry.field` resolvers to `relay.ListConnection[…] = DjangoConnectionField(…)`; the simpler `DjangoListField` shape is not the documented future target for products, whose design goal is Relay-shaped throughout. `DjangoListField`'s example home is the `library` app (see [Decision 9](#decision-9--example-app-migration-posture)).
- The sync + async `cls.get_queryset(...)` application is single-sited in `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` and `::apply_type_visibility_async`, the helpers that run the hook in sync and async contexts respectively. The sync helper rejects an async hook met from a sync resolver with `SyncMisuseError`, a `ConfigurationError` subclass (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync #"reject_async_in_sync_context"`). These are the helpers the `DjangoListField` default resolver re-uses — no new sync/async plumbing is invented in this slice.
- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve` defines the root-gated `resolve` hook keying on `info.path.prev is None`. A field that returns a `Django QuerySet` at the root is planned automatically; a field that returns a Python `list` is not. The `DjangoListField` default resolver MUST return a `QuerySet`, not a Python list, for the optimizer to engage.
- `django_strawberry_framework/registry.py` carries the `Meta.primary`-aware lookup (`primary_for(model)`, `types_for(model)`). `DjangoListField` takes an explicit `DjangoType` argument, NOT a model — this means the registry's primary/secondary ambiguity is irrelevant to the construction path (the consumer named the target type explicitly).
- `django_strawberry_framework/scalars.py` ships `BigInt` as a flat single-file Layer-3 module. The target on-disk layout in `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"` lists `fieldset.py`, `permissions.py`, `connection.py` as parallel single-file Layer-3 modules under the package root. `list_field.py` slots in next to those.
- `tests/test_registry.py`, `tests/test_scalars.py` (if present) — and per the convention in `docs/TREE.md #"tests/test_<module>.py (flat, at the root)"` ("`tests/test_<module>.py` (flat, at the root) — single-file Layer-3 module tests") — the test home for `DjangoListField` is `tests/test_list_field.py`, parallel to the source module.

## Goals

1. Ship `DjangoListField(TargetType)` as a single new public export from `django_strawberry_framework` — a factory function that returns `strawberry.field(resolver=..., ...)`. The default resolver calls `model._default_manager.all()` and applies `cls.get_queryset(...)`; sync + async paths; consumer-`resolver=` override is supported, and the override's `Manager`/`QuerySet` return value also receives `target_type.get_queryset(...)` (graphene-django parity).
2. Preserve `DjangoOptimizerExtension`'s root-gated planning for `DjangoListField`-served querysets at **root** Query positions. Nested non-root use of `DjangoListField` works as a resolver but is NOT root-optimized in `0.0.7`; see [Decision 4](#decision-4--optimizer-cooperation).
3. Preserve the `cls.get_queryset(...)` cooperation contract from [`spec-015-relay_interfaces-0_0_5.md`][spec-015] and [`docs/GLOSSARY.md#get_queryset-visibility-hook`][glossary-get-queryset-visibility-hook]: both the sync and the async paths invoke `cls.get_queryset(qs, info)` before returning, and an async `get_queryset` met on the sync path is rejected with `SyncMisuseError` — the [`ConfigurationError`][glossary-configurationerror] subclass raised by `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` (via `django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`), the same rejection every read surface receives.
4. Stay tight: no `DjangoConnectionField`, no filter / order / aggregate / search arguments on the field, no auto-upgrade of reverse-FK / M2M relation fields, no node-aware optimizer feature work beyond preserving root-gated planning.
5. **Add** a new `all_library_branches_via_list_field` root field to the `library` example (do NOT replace `all_library_branches`, which has `order_by("id")` dependencies in existing HTTP tests) so the package ships a live HTTP-tested example of the default `DjangoListField` resolver without mutating any existing field.

## Non-goals

- `DjangoConnectionField` and the Relay-shaped pagination surface. Tracked under `DONE-030-0.0.9` in [`KANBAN.md`][kanban].
- Filter / order / search / aggregate input arguments on `DjangoListField`. Those are the Layer-3 read-side primitives tracked in `DONE-027-0.0.8` (filters), `DONE-028-0.0.8` (orders), `TODO-BETA-047-0.1.2` (search), `TODO-BETA-049-0.1.3` (aggregates). Once those subsystems ship, `DjangoListField` will pick up the corresponding input arguments under their own specs — this card is the minimum primitive that exists ahead of those.
- Cascade permissions and field-level permissions. Tracked under `DONE-034-0.0.10`. `DjangoListField` needs no cascade-specific code: [`apply_cascade_permissions`][glossary-apply-cascade-permissions] is called from a type's own `cls.get_queryset(...)`, and the field applies that hook, so a cascading target narrows the list with no participation from this field (`tests/test_list_field.py::test_list_field_default_resolver_applies_cascade`).
- Auto-upgrading reverse-FK / M2M many-side relation fields to `DjangoListField`. Relation many-side fields are already shipped as `list[T]` via generated resolvers (see [`Relation handling`][glossary-relation-handling]); `DjangoListField` is the **root** primitive, not a relation-side replacement. See [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields).
- [Multi-database][glossary-multi-database-cooperation] / sharding-aware queryset routing. Tracked under `DONE-023-0.0.7` (the multi-db cooperation contract). `DjangoListField` uses `model._default_manager.all()` which Django routes through the configured database router automatically; nothing in this card precludes the cooperation contract that lands alongside.
- Pagination and ordering defaults. Out of scope by design — `DjangoListField` takes no pagination arguments and adds no order tiebreaker; the Relay-connection field is the right home for both. Row **limits** are neither out of scope nor optional: every `DjangoListField` is row-bounded, see [Row bound](#row-bound).
- A flat-list helper class shape that wraps every `DjangoType` declaration (e.g., `class MyTypeListField(DjangoListField): pass`). Not needed; `DjangoListField(MyType)` at the call site is sufficient.

## Borrowing posture

The two reference packages at the paths given in `docs/TREE.md` ship a similar primitive. The slice should borrow patterns, not implementations.

### From `graphene-django` — borrow the user-facing shape

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoListField` (referenced from `docs/TREE.md #"## graphene_django"`).

- **`DjangoListField` symbol name.** Same name, same role.
- **Default-resolver shape — model-derived manager → type-level visibility hook.** `graphene_django/fields.py::DjangoListField` (the `get_manager` / `list_resolver` methods) derives the manager from `_type._meta.model._default_manager`, calls `_type.get_queryset(queryset, info)`, returns the queryset. We borrow this contract verbatim. One adaptation: our `DjangoType.get_queryset` is a `classmethod`, not a `staticmethod` ([`docs/GLOSSARY.md#get_queryset-visibility-hook`][glossary-get-queryset-visibility-hook]).
- **Item-level non-null; outer-level via consumer annotation.** `graphene_django/fields.py::DjangoListField.__init__ #"List(NonNull(_type))"` wraps the type as `List(NonNull(_type))`. We borrow the item-non-null part (Django ORM never returns `None` rows from a queryset); the outer nullability is driven by the **consumer's class-attribute annotation** rather than a constructor kwarg (`list[BranchType]` → `[BranchType!]!`, `list[BranchType] | None` → `[BranchType!]`).
- **`maybe_queryset` coercion of `Manager`-shaped returns + `get_queryset` application on consumer-resolver returns.** `graphene_django/fields.py::DjangoListField.list_resolver` calls `maybe_queryset(...)` so a consumer resolver returning `Model.objects` (the Django shorthand) is coerced via `.all()`, AND then applies `_type.get_queryset(queryset, info)` to any `QuerySet` returned. We borrow BOTH halves of this — the **field wrapper itself** performs the `Manager → QuerySet` coercion (`result.all()`) BEFORE applying `target_type.get_queryset(...)` so the visibility hook receives a `QuerySet`, not a `Manager`. The `DjangoOptimizerExtension._optimize` step's own `Manager` coercion at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"if isinstance(result, models.Manager):"` is a downstream safety net for non-`DjangoListField` root resolvers that happen to return `Model.objects`; the two coercions co-exist (one for visibility-hook correctness inside the field, one for optimizer cooperation at the extension boundary). The `get_queryset` application on consumer-resolver returns is explicit in the field wrapper, and applies whether the consumer supplied a sync or an `async def` resolver. Consumers who genuinely want to bypass `get_queryset` return a Python `list` (already-evaluated) from their resolver; the field detects this and passes the list through unchanged.

### Explicitly do not borrow

- Graphene-django's `wrap_resolve` machinery (`graphene_django/fields.py::DjangoListField.wrap_resolve`). Strawberry's resolver assignment is direct (`strawberry.field(resolver=...)`), and graphene-django's `partial(self.list_resolver, …)` wrapping is the graphene-side equivalent. We use Strawberry's native shape.
- Graphene-django's `_type.of_type.of_type` unwrap dance (`graphene_django/fields.py::DjangoListField.wrap_resolve #"_type.of_type.of_type"`) — the type wrapping is different in Strawberry; we annotate `list[T]` directly.
- `strawberry-graphql-django` does NOT ship a direct `DjangoListField` analogue — its closest primitive is `strawberry_django.field()` returning a `list[T]` of a strawberry-django type. That mechanism is decorator-based and contradicts the `class Meta`-driven posture in [`README.md`][readme] and [`GOAL.md`][goal]. No borrow there.

## User-facing API

The shipped consumer surface in `0.0.7` adds exactly one new public export (`DjangoListField`) to `django_strawberry_framework`. No other public names change.

### Default usage — root list field

```python path=null start=null
import strawberry
from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from apps.library import models


class BranchType(DjangoType):
    class Meta:
        model = models.Branch
        fields = ("id", "name", "city", "shelves")


@strawberry.type
class Query:
    all_library_branches: list[BranchType] = DjangoListField(BranchType)


finalize_django_types()

schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
```

Expected GraphQL behavior:

- `Query.allLibraryBranches: [BranchType!]!` (item-non-null + list-non-null by default).
- The resolver returns `Branch._default_manager.all()`, threaded through `BranchType.get_queryset(qs, info)` and then row-bounded (see [Row bound](#row-bound)).
- **No order guarantee.** The default resolver appends no tiebreaker, so response order is database-dependent unless the model declares `Meta.ordering` or the query passes `orderBy` (see [Decision 8](#decision-8--out-of-scope-boundary-with-djangoconnectionfield)).
- `DjangoOptimizerExtension` plans `select_related` / `prefetch_related` / [`only()`][glossary-only-projection] for nested selections.
- Async resolvers awaiting `BranchType.get_queryset` work without consumer wiring.

### Custom resolver override

```python path=null start=null
from typing import Any

from strawberry.types import Info


def _branches_with_recent_loans(root: Any, info: Info) -> models.QuerySet:
    return models.Branch.objects.filter(shelves__books__loans__isnull=False).distinct()


@strawberry.type
class Query:
    branches_with_recent_loans: list[BranchType] = DjangoListField(
        BranchType,
        resolver=_branches_with_recent_loans,
    )
```

When `resolver=` is supplied, the consumer's body runs instead of the default `model._default_manager.all()` call. The field then applies `BranchType.get_queryset(qs, info)` to the return value when it is a `Manager` or `QuerySet` (graphene-django parity per `graphene_django/fields.py::DjangoListField.list_resolver`). Consumers who genuinely want to bypass `get_queryset` return a Python `list` (already-evaluated) from their resolver — a non-queryset iterable passes through unchanged.

**Async consumer resolvers**: an async resolver returning a `Manager`/`QuerySet` is awaited before the `isinstance` check, so `get_queryset` is applied to the awaited value — async-vs-sync is not a contract surface. The factory decides the wrapper shape at construction time with `django_strawberry_framework/utils/typing.py::is_async_callable`, which sees an `async def`, an instance whose `__call__` is `async def`, a raw `staticmethod` descriptor, and any nesting of `functools.partial` / `staticmethod` layers around those. That predicate is the authority for which spellings count; the field factory does not keep its own list. An **async generator** resolver, and a sync resolver returning an async-only iterable, are both supported too and are both bounded; an async-only iterable met from synchronous execution raises `SyncMisuseError` rather than yielding nothing (see [Decision 2](#decision-2--default-resolver-shape)).

```python path=null start=null
# Async-resolver example. Django's ORM is sync-by-default, so the typical
# shape wraps the queryset construction in ``sync_to_async``. The returned QuerySet
# still receives ``BranchType.get_queryset(...)`` exactly like the sync example above.
from asgiref.sync import sync_to_async


async def _branches_with_recent_loans_async(root: Any, info: Info) -> models.QuerySet:
    return await sync_to_async(
        lambda: models.Branch.objects.filter(
            shelves__books__loans__isnull=False,
        ).distinct()
    )()


@strawberry.type
class Query:
    branches_with_recent_loans_async: list[BranchType] = DjangoListField(
        BranchType,
        resolver=_branches_with_recent_loans_async,
    )
```

Resolver signature is the Strawberry-native `(root: Any, info: Info)` shape (`info` MUST be annotated `strawberry.types.Info` or Strawberry's schema construction raises `MissingArgumentsAnnotationsError`; `**kwargs` is NOT a harmless catch-all because Strawberry treats every parameter as a GraphQL argument). Filter / order arguments arrive in future Layer-3 cards under their own specs.

Optimizer cooperation still applies because the optimizer extension is root-gated and runs on whatever queryset the field returns.

### Nullable outer list

The outer-list nullability is controlled by the **consumer's class-attribute annotation** (`DjangoListField` does NOT take a `nullable_list=` constructor argument). Strawberry reads the annotation directly to render the GraphQL type:

```python path=null start=null
all_branches: list[BranchType] = DjangoListField(BranchType)                  # [BranchType!]!  (non-null outer)
all_branches_or_none: list[BranchType] | None = DjangoListField(BranchType)   # [BranchType!]   (nullable outer)
```

Item-level non-null is the same in both shapes — Django ORM never returns `None` rows from a queryset.

### Row bound

Every `DjangoListField` is row-bounded, and the field's surface for that bound is two constructor arguments: `max_rows=` narrows the bound for this field, and `trusted_max_rows=True` is the only spelling that lets the field be wider than the request's policy. There is no unbounded spelling — `max_rows=None` means the policy governs. How the bound and the policy compose — that `max_list_rows` applies whether or not the field says anything, and which of the two wins — is the standing statement in [`docs/GLOSSARY.md#djangolistfield`][glossary-djangolistfield], the consumer-facing authority; the constructor guard that enforces the argument itself is [Decision 5](#decision-5--validation--error-shapes).

```python path=null start=null
all_library_branches: list[BranchType] = DjangoListField(
    BranchType,
    max_rows=50,            # narrows to the tighter of 50 and the request policy
    trusted_max_rows=False, # the default; True is the explicit widening opt-in
)
```

### Field-level GraphQL metadata

```python path=null start=null
all_library_branches: list[BranchType] = DjangoListField(
    BranchType,
    description="Every branch in the library system, ordered by Django default.",
    deprecation_reason=None,
    directives=(),
)
```

These pass through to the underlying Strawberry field unchanged.

## Architectural decisions

### Decision 1 — Module location, mechanism, & public export

**Mechanism.** `DjangoListField` is a **factory function**, not a class. It returns a `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)` with the resolver wrapped per [Decision 2](#decision-2--default-resolver-shape). The consumer's class-attribute annotation (`all_branches: list[BranchType]`) is what Strawberry reads to derive the field's GraphQL type; the factory does not own or override that annotation.

**Module location.** `DjangoListField` lives in **`django_strawberry_framework/list_field.py`** (new flat single-file Layer-3 module at the package root), NOT in a hypothetical `connection.py` that does not yet exist.

**`list_field.py` is the home of the shared field-target validation contract.** The four constructor guards live here as `django_strawberry_framework/list_field.py::_validate_djangotype_target`, and the Relay-Node-shaped superset as `::_validate_relay_djangotype_target`. `DjangoConnectionField` (`django_strawberry_framework/connection.py #"from .list_field import _validate_relay_djangotype_target"`) and the root node fields (`django_strawberry_framework/relay.py::_validate_node_target`) both import the Relay variant, so the target-validation contract is single-sited in this module rather than duplicated per factory. Each caller passes its own `field=` name, so every `ConfigurationError` names the factory that raised it. A reader changing a guard changes it here, once.

Public-export surface:

- `django_strawberry_framework/__init__.py` adds `from .list_field import DjangoListField` (alphabetical position between `BigInt` and `DjangoOptimizerExtension`).
- `__all__` gains `"DjangoListField"`. The public-surface promise in `README.md` says today's names remain stable through `0.1.0`; this card adds, never removes.
- `tests/base/test_init.py`'s pinned `__all__` assertion is updated in the same commit so the surface check stays accurate.

The rejected placement alternatives (bundling into `connection.py`, inlining into `__init__.py`, a `fields/` subpackage), the reasons `list_field.py` won, and the two mechanisms the first draft sketched that did not survive contact with the installed Strawberry are in [the rationale companion][spec-020-rationale].

### Decision 2 — Default resolver shape

The factory function captures `target_type` via closure and builds a wrapped resolver whose signature matches Strawberry's contract (Strawberry calls a field resolver with `(root, info)` where `info` MUST be annotated `strawberry.types.Info`; `**kwargs` is NOT a harmless catch-all because Strawberry treats every parameter as a GraphQL argument). Sketch:

```python path=null start=null
# django_strawberry_framework/list_field.py
from collections.abc import AsyncIterable, Callable, Iterable, Sequence
from typing import Any

import strawberry
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .resource_policy import bounded_rows, bounded_rows_async, validate_collection_bound
from .utils.querysets import (
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
    post_process_queryset_result_async,
    post_process_queryset_result_sync,
)
from .utils.typing import is_async_callable, is_async_generator_callable


# Module-scope consumer-resolver post-processing helpers (pinned at module scope,
# NOT inside the factory body, so they're referentially transparent and
# unit-testable independently of `DjangoListField(...)`. `target_type` and `info`
# are explicit parameters. The `Manager` -> `QuerySet` coercion + visibility-hook
# contract is single-sited in `utils/querysets.py`; these stay as the named
# consumer-wrapper entry points the `_wrap` resolvers call. The default-resolver
# path bypasses them because `qs` is already known to be a QuerySet from
# `initial_queryset(...)` -- no normalization is needed there. The `_consumer`
# suffix in the names makes the per-consumer-resolver scope explicit.)


def _post_process_consumer_sync(target_type: type, result: Any, info: Info) -> Any:
    return post_process_queryset_result_sync(target_type, result, info)


async def _post_process_consumer_async(target_type: type, result: Any, info: Info) -> Any:
    return await post_process_queryset_result_async(target_type, result, info)


def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity.
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
    max_rows: int | None = None,
    trusted_max_rows: bool = False,
) -> Any:
    if max_rows is not None:
        validate_collection_bound(max_rows, field="DjangoListField max_rows")
    # The four shared target guards, per Decision 5.
    _validate_djangotype_target(target_type, resolver, field="DjangoListField")

    if resolver is None:
        def _default(root: Any, info: Info) -> Any:
            qs = initial_queryset(target_type)
            if in_async_context():
                # The async branch DOES need its own coroutine wrapper: the row
                # bound has to be applied to the AWAITED value, after the
                # visibility hook has composed onto the unsliced source.
                return _bounded_async(
                    apply_type_visibility_async(target_type, qs, info),
                    info, max_rows, trusted=trusted_max_rows,
                )
            return bounded_rows(
                apply_type_visibility_sync(target_type, qs, info),
                info, max_rows, trusted=trusted_max_rows,
            )
        wrapped = _default
    else:
        user_resolver = resolver

        async def _resolve_async_iterable(source: Any, info: Info) -> Any:
            return await bounded_rows_async(
                await _post_process_consumer_async(target_type, source, info),
                info, max_rows, trusted=trusted_max_rows,
            )

        if is_async_generator_callable(user_resolver):
            # An async generator function is CALLED synchronously and yields
            # asynchronously, so this wrapper stays a plain `def`.
            def _wrap(root: Any, info: Info) -> Any:
                source = user_resolver(root, info)
                _require_async_iterable_context()
                return _resolve_async_iterable(source, info)
        elif is_async_callable(user_resolver):
            async def _wrap(root: Any, info: Info) -> Any:
                # `await` the consumer coroutine BEFORE handing the result to
                # `_post_process_consumer_async`, otherwise the
                # isinstance-QuerySet branch sees the coroutine, not the value.
                return await bounded_rows_async(
                    await _post_process_consumer_async(
                        target_type, await user_resolver(root, info), info,
                    ),
                    info, max_rows, trusted=trusted_max_rows,
                )
        else:
            def _wrap(root: Any, info: Info) -> Any:
                source = user_resolver(root, info)
                if isinstance(source, AsyncIterable) and not isinstance(source, Iterable):
                    _require_async_iterable_context()
                    return _resolve_async_iterable(source, info)
                return bounded_rows(
                    _post_process_consumer_sync(target_type, source, info),
                    info, max_rows, trusted=trusted_max_rows,
                )
        wrapped = _wrap

    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
```

Where `apply_type_visibility_sync` / `apply_type_visibility_async`, `initial_queryset` and `post_process_queryset_result_sync` / `_async` are imported from `django_strawberry_framework/utils/querysets.py` (see [Decision 3](#decision-3--get_queryset-and-async-symmetry)); `bounded_rows` / `bounded_rows_async` / `validate_collection_bound` from `django_strawberry_framework/resource_policy.py`; and `_bounded_async`, `_require_async_iterable_context` and `_validate_djangotype_target` are module-local to `list_field.py`.

**Three consumer-resolver arms, not two.** A consumer `resolver=` is (a) an async generator function, (b) any other async callable — `async def`, an instance whose `__call__` is `async def`, a raw `staticmethod` descriptor, or any nesting of `functools.partial` / `staticmethod` around those, as `django_strawberry_framework/utils/typing.py::is_async_callable` defines it (`django_strawberry_framework/utils/typing.py::_callable_inspection_target` peels both wrapper kinds in a loop, so the nesting depth is not a contract surface) — or (c) a plain sync callable. Arms (a) and (b) are committed to at construction time; arm (c) additionally detects an async-only iterable at call time, because a sync callable may return one. An async-only iterable met from synchronous GraphQL execution is rejected with `SyncMisuseError` rather than silently yielding nothing: `django_strawberry_framework/list_field.py::_require_async_iterable_context` raises unless `in_async_context()`. `tests/test_list_field.py::test_djangolistfield_async_generator_resolver_is_bounded`, `::test_djangolistfield_sync_resolver_returning_async_iterable_is_bounded`, `::test_djangolistfield_partial_async_generator_resolver_is_bounded`, `::test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse`, `::test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded` and `::test_djangolistfield_async_consumer_resolver_async_iterable_can_exhaust_before_bound` pin the arm.

**The row bound is applied last, never before the visibility hook.** A sliced queryset cannot be refiltered or reordered, and both the visibility hook and the consumer post-processing compose onto the source — so slicing first would turn the bound into a crash on every type that declares a hook. The ordering is a correctness constraint, not a preference, which is why the async default branch carries its own `_bounded_async` coroutine wrapper: the bound must land on the awaited value.

**Async-detection asymmetry — intentional, not a harmonization candidate**. Two different detection mechanisms appear above:

- The **default** resolver uses **runtime** `in_async_context()` inside a plain `def _default(...)` body that lazily returns either a value or a coroutine. Strawberry handles `AwaitableOrValue` from sync resolvers, so the same factory output dispatches correctly under both `schema.execute_sync(...)` and `await schema.execute(...)`. This is the same pattern the optimizer extension uses at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`.
- The **consumer-resolver wrapper** uses **construction-time** `is_async_callable(user_resolver)` (and `is_async_generator_callable` first) to commit to either an `async def _wrap` or a plain `def _wrap`. The wrapper has to be statically sync OR async at factory time because Strawberry inspects the resolver's signature once at schema construction and commits to async-vs-sync handling globally — an `async def` wrapper lets Strawberry await it directly without going through `AwaitableOrValue`. The predicate is deliberately **not** `inspect.iscoroutinefunction`, which returns `False` for a `functools.partial` around an `async def`, for a callable object with an `async def __call__`, and for a raw `staticmethod` descriptor wrapping an `async def`.

Harmonizing the two would either force the default into static commitment (loses sync-callability) or force the consumer wrapper into lazy upgrade (adds an extra coroutine layer per call). Both mechanisms are correct for their respective dispatch sites; a future maintainer noticing the asymmetry should leave it alone.

Item-level non-null is unconditional — Django ORM never returns `None` rows from a queryset (matches `graphene_django/fields.py::DjangoListField.__init__ #"Django would never return a Set of None"`'s comment).

Outer-level nullability is driven by the **consumer's class-attribute annotation**: `list[T]` → `[T!]!`; `list[T] | None` → `[T!]`. The factory does NOT take a `nullable_list=` constructor argument because Strawberry already reads the class-attribute annotation; a separate kwarg would either fight or silently override it.

The rejected alternatives - a Python-`list` default return, skipping `cls.get_queryset` on consumer-resolver returns, a `nullable_list=` constructor argument, a first-positional `(type_cls, info)` signature, a catch-all `**kwargs`, and `null=True` item types - are in [the rationale companion][spec-020-rationale], each with the reason it lost.

### Decision 3 — `get_queryset` and async symmetry

The sync + async `cls.get_queryset(...)` cooperation is delegated to the shared sealed-boundary helpers in `django_strawberry_framework/utils/querysets.py`, the single site every recomposing read surface uses — e.g. the Relay node defaults, the connection root, this field, and the cascade:

- `apply_type_visibility_sync(cls, qs, info)` at `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` — applies the hook in a sync context; rejects an async hook with `SyncMisuseError`, a `ConfigurationError` subclass that also inherits `RuntimeError`, after closing the unawaited coroutine so no "coroutine was never awaited" warning escapes. Each surface passes its own recourse wording.
- `apply_type_visibility_async(cls, qs, info)` at `django_strawberry_framework/utils/querysets.py::apply_type_visibility_async` — applies the hook in an async context; awaits awaitables; passes sync returns through.

Async detection re-uses the same `in_async_context` symbol the Relay defaults use — the canonical import is `from strawberry.utils.inspect import in_async_context` (already imported at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"`). The `list_field.py` module imports it from the same site; no fork.

**The hook's return crosses a sealed boundary.** The contract is not "call the hook and use what comes back". Both helpers SEAL the source and the hook's result into a fresh framework-owned plain `QuerySet` rebuilt from validated query state — shape, concrete and actual-base table, sealability, model-row-ness, routed alias — and fail closed on any return they cannot prove: a `Manager` whose `.all()` degrades to a non-queryset, a silently re-routed database, a `.values()` projection on a read surface, an instance-shadowed `all`, or a sliced result a later recomposition would have to reorder. A hostile or careless `get_queryset` override therefore cannot widen the rows this field serves, and an unprovable return raises rather than passing through. Pinned by `tests/test_list_field.py::test_djangolistfield_hostile_hook_subclass_serves_only_visible_rows_sync` / `_async`, `::test_djangolistfield_instance_shadowed_all_hook_is_sealed`, `::test_djangolistfield_resolver_manager_degrading_to_list_fails_closed_sync` / `_async`, and `::test_djangolistfield_resolver_manager_alias_drift_fails_closed_sync`.

Neither helper is public surface, and the cross-module import is a single line. The helpers live in `utils/querysets.py` rather than in either consuming module precisely because more than one field factory needs them: a helper shared by the list field, the connection field and the Relay node defaults belongs at a neutral site, so a change to the coroutine-in-sync rejection contract touches one body.

The relocation option weighed and deferred here, and the two rejected alternatives (inline copies of the helpers; a `list_field.py`-local async-detection mechanism), are in [the rationale companion][spec-020-rationale].

### Decision 4 — Optimizer cooperation

`DjangoListField` does NOT touch the optimizer source code. The cooperation contract is:

- The default resolver returns a `QuerySet` (not a Python `list`).
- The root-gated `DjangoOptimizerExtension.resolve` hook (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`) fires on `info.path.prev is None`; the field site IS a root (top-level `Query` field), so the hook fires.
- `_optimize` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`) normalizes its input through the shared `django_strawberry_framework/utils/querysets.py::normalize_query_source` (`Manager` → `QuerySet`, non-queryset iterables short-circuit); the field returns a `QuerySet`, so the normalization is a no-op.
- The selection-tree walker (`django_strawberry_framework/optimizer/walker.py`) reads the target `DjangoType` from `_resolve_model_from_return_type(info)` — defined at `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type`, called inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"resolved = _resolve_model_from_return_type(info)"`, and returning an `_OriginAndModel` pair (the resolved Strawberry origin plus its model) or `None`. The return-type machinery already handles `list[T]` annotations.
- Plan caching, FK-id elision, `only()` projection, [queryset diffing][glossary-queryset-diffing], strictness mode — all shipped, all apply unchanged.

**Scope narrowing — root only in `0.0.7`.** The optimizer extension is explicitly root-gated on `info.path.prev is None`. A `DjangoListField` used at a **nested non-root** position on a Strawberry type — for example, a child `@strawberry.type` carrying `more_items: list[ItemType] = DjangoListField(ItemType)` — produces a functional list resolver (the default body still runs and `get_queryset` is still applied), but the optimizer's `resolve` hook does NOT fire because `info.path.prev` is not `None`. The `0.0.7` shipped contract is therefore **root list fields only**; nested non-root use works but is not root-optimized. The connection card (`DONE-030-0.0.9`) and any follow-up spec may revisit nested optimization explicitly. Pinned by `test_djangolistfield_at_root_position_is_optimized` in `tests/test_list_field.py` (a sibling negative test for the nested-non-root case is NOT required in `0.0.7` because the contract is "we don't promise optimization there", not "we promise non-optimization there").

The slice MUST add an optimizer-side test (in `tests/test_list_field.py`) that confirms the planned `select_related` / `prefetch_related` for a nested selection on a `DjangoListField`-served collection at the **root** position. The Slice 4 live HTTP test in `examples/fakeshop/test_query/test_library_api.py` covers the same selection shape end-to-end. Both tests are required, because they pin different contracts: the package-internal test pins the **return-shape contract** (the default resolver returns a `QuerySet`, not a Python `list` - the regression that breaks N+1 cooperation silently), while the HTTP test pins the **end-to-end contract** (URL routing + view + schema execution + JSON serialization survive the round trip). Either fail mode can fly past the other test: a refactor that accidentally calls `qs.all()` and returns a list still passes the HTTP test because the rows come back, and a Django middleware change can break the HTTP path without affecting in-process schema execution.

The rejected alternatives (bypassing the root gate, extending the hook to plan nested `DjangoListField` sites, an `info.context` marker) are in [the rationale companion][spec-020-rationale].

### Decision 5 — Validation & error shapes

The `DjangoListField(arg, *, resolver=None, description=None, deprecation_reason=None, directives=(), max_rows=None, trusted_max_rows=False)` constructor validates:

- `arg` is a class (`inspect.isclass(arg)`); otherwise `ConfigurationError("DjangoListField requires a DjangoType class; got <repr>.")`.
- `arg` is `issubclass(arg, DjangoType)`; otherwise `ConfigurationError("DjangoListField requires a DjangoType subclass; got <name>.")`.
- `arg` carries its **own** registered definition — `definition = getattr(arg, "__django_strawberry_definition__", None)` is not `None` **and** `definition.origin is arg`; otherwise `ConfigurationError("DjangoListField target <name> is not a registered DjangoType. This usually means <name>'s `Meta` is missing a `model` declaration, or it inherits a definition from a parent without declaring its own `Meta`.")`. The attribute is assigned at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"` only when the `DjangoType` subclass carries a `Meta` with a `model` — but it is **inherited via MRO**, so `hasattr(...)` is NOT a sufficient discriminator: it would accept a subclass that omits its own `Meta` and bind the field to a target whose definition, `Meta.primary` state and model all belong to the parent. The own-class-origin identity check is the invariant (`tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta`).
- `resolver`, when supplied, is callable; otherwise `ConfigurationError("DjangoListField resolver must be callable.")`.

The four target checks above are ordered among themselves, and that order is load-bearing — each one assumes the previous passed. They are shared, not local to this factory: see [Decision 1](#decision-1--module-location-mechanism--public-export).

The row-bound guard runs **first**, ahead of all four target checks: a `max_rows` that is not a positive integer is rejected by `django_strawberry_framework/resource_policy.py::validate_collection_bound` before the target is inspected, so a field constructed with both a bad target and a bad `max_rows` reports the `max_rows` error (`tests/test_list_field.py::test_djangolistfield_rejects_a_non_positive_max_rows_at_construction`). What the bound then means is [Row bound](#row-bound); `::test_djangolistfield_max_rows_narrows_the_request_policy` pins the narrowing.

Error site count: two error sites in the `DjangoListField` constructor — the shared target-validation guards and the row-bound guard. All errors raise [`ConfigurationError`][glossary-configurationerror] or a subclass of it.

The error messages follow the same `<Symbol> <constraint>; got <repr>.` shape pattern that `django_strawberry_framework/types/base.py::_format_unknown_fields_error` uses for consistency with the rest of the package's validation surface.

Validation fires in the constructor rather than at type-decoration or `finalize_django_types()` time: the rules are local to the constructor, no cross-class state is needed, and the error surfaces at the line that wrote `DjangoListField(...)`. This is symmetric with `OptimizerHint`-related `Meta` validation, which fires at type creation.

The deferred-validation and model-class-argument alternatives, and why each lost, are in [the rationale companion][spec-020-rationale].

### Decision 6 — `Meta.primary` interaction

`DjangoListField(TargetType)` takes a concrete `DjangoType` subclass as its argument — never a model class. This means:

- For a model with one `DjangoType`, no `Meta.primary` declaration, current behavior — `DjangoListField(TargetType)` is unambiguous and works.
- For a model with multiple `DjangoType`s where one carries `Meta.primary = True` — `DjangoListField(PrimaryType)` and `DjangoListField(SecondaryType)` both work; each is bound to the explicit target's queryset, `get_queryset` hook, and (if any) optimizer hints. No registry lookup happens.
- For a model with multiple `DjangoType`s where the primary ambiguity hasn't been resolved (no `Meta.primary` declared on any) — `finalize_django_types()` raises `ConfigurationError` already ([`spec-018-meta_primary-0_0_6.md`][spec-018] Decision); `DjangoListField` is downstream and inherits the same loud failure mode.

`DjangoListField(PrimaryType)` and `DjangoListField(SecondaryType)` produce two distinct optimizer [plan cache][glossary-plan-cache] entries, because plan-cache keys include the resolver's origin Strawberry type - pointing two fields at two types on one model carries no cache-poisoning risk. The explicit-target shape is the same one the existing relation-resolver paths use for multi-type-per-model targets ([`docs/GLOSSARY.md#metaprimary`][glossary-metaprimary]).

Tests in `tests/test_list_field.py` must cover:

- `test_djangolistfield_with_meta_primary_true_returns_primary_queryset` — declare two `DjangoType`s on the same model, one with `Meta.primary = True`; `DjangoListField(PrimaryType)` returns rows queried via the primary's `get_queryset`.
- `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset` — declare two types, point the field at the secondary; the secondary's `get_queryset` is applied, not the primary's.

The rejected alternatives (accepting a model class and looking up the primary, defaulting to the primary on an ambiguous model, a `DjangoListField.for_model(Model)` classmethod) are in [the rationale companion][spec-020-rationale].

### Decision 7 — Scope boundary vs relation list fields

`DjangoListField` is the **root** primitive — it adds a new list-shape field to a `Query` class (or any `@strawberry.type` class). It is NOT the relation-side many-list field; that path is already shipped via generated relation resolvers (see [`docs/GLOSSARY.md#relation-handling`][glossary-relation-handling]):

> reverse `ForeignKey` → `list[target_type]`. The optimizer plans `prefetch_related`. Many-side resolvers return Python lists, not Django managers.

This card does NOT:

- Replace the generated relation resolvers with `DjangoListField`-based plumbing.
- Change the shape of many-side relation fields (still `list[T]`, still returned as Python lists from generated resolvers).
- Auto-upgrade reverse-FK / M2M fields to use `DjangoListField`.

A future spec MAY consider unifying the two — likely when the connection field lands and the relation-side many-list field grows up to a connection auto-upgrade. That decision belongs to the connection spec (`DONE-030-0.0.9`), not this one.

Why the root primitive and the generated relation-side many-list resolvers stay separate is in [the rationale companion][spec-020-rationale].

### Decision 8 — Out-of-scope boundary with `DjangoConnectionField`

`DjangoListField` and `DjangoConnectionField` ([`DONE-030-0.0.9`][kanban]) are sibling primitives. Both bind to a `DjangoType`; both apply `cls.get_queryset(...)`; both cooperate with the optimizer.

Boundary line:

- `DjangoListField` returns `list[T!]!` (or `list[T!]`); no pagination, no edges, no `pageInfo`, no Relay arguments — **and no order guarantee**. The default resolver appends no tiebreaker, so row order is whatever the database returns unless the query supplies an `orderBy` argument or the model declares `Meta.ordering`.
- `DjangoConnectionField` returns a [`DjangoConnection`][glossary-djangoconnection] (`Connection[T]`) with `edges` / `node` / `pageInfo` / `totalCount` and Relay pagination arguments (`first` / `after` / `last` / `before`), **and a pk tiebreaker appended to guarantee a deterministic total order** — its positional cursors require one.
- The ordering asymmetry between the two primitives is deliberate, not an oversight: a flat list has no cursors that an unstable order could invalidate, so paying for a tiebreaker on every list query would buy nothing. A consumer who needs deterministic list order declares `Meta.ordering` on the model or passes `orderBy`.
- Filter / order / search / aggregate input arguments are added to BOTH primitives by the relevant Layer-3 spec when those subsystems ship; the input-shape contract is the same across both.

A consumer migrating from `DjangoListField` to `DjangoConnectionField` later:

```diff
- all_branches: list[BranchType] = DjangoListField(BranchType)
+ all_branches: DjangoConnection[BranchType] = DjangoConnectionField(BranchType)
```

Same `DjangoType` argument; same `get_queryset` cooperation; same optimizer integration; richer return shape.

The rejected alternatives (a single `DjangoField` symbol with a `connection=True/False` argument; inheriting `DjangoConnectionField` from `DjangoListField`) are in [the rationale companion][spec-020-rationale].

### Decision 9 — Example-app migration posture

This card **adds** new root fields to `examples/fakeshop/apps/library/schema.py`'s `Query` class and replaces none: `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` for the default-resolver path, `all_library_branches_via_list_field_nullable: list[BranchType] | None` for the nullable-outer rendering, and `all_library_branches_via_list_field_manager_resolver` for a consumer resolver returning a `Manager`. No existing `all_library_*` resolver is touched (`all_library_branches`'s `order_by("id")` is depended on by `test_library_relation_override_shapes_http_response_data` in `examples/fakeshop/test_query/test_library_api.py`, which seeds two branches and asserts a deterministic order. `Branch` has no model-level `Meta.ordering`, so the default-manager queryset is unordered).

Two constraints on the surrounding resolvers:

- The pre-existing `all_library_*` resolvers each carry `order_by("id")` for deterministic test ordering; this card does NOT migrate any of them.
- The `all_library_prefetched_books` resolver uses `Book.objects.select_related("shelf").prefetch_related("genres").order_by("id")` - a consumer-shaped queryset. That resolver MUST stay a hand-rolled `@strawberry.field` so it keeps exercising the optimizer's [queryset diffing][glossary-queryset-diffing] path.

The `library` example schema's prose comment near the top of `schema.py` should be updated in the same slice to mention that `all_library_branches_via_list_field` exercises the new `DjangoListField` primitive while the sibling `all_library_*` resolvers continue to exercise the consumer-resolver / queryset-diffing paths.

The five replacement postures that were considered and rejected - including the original card text's "replacing one of the hand-rolled `all_library_*` resolvers" wording, which this spec departs from deliberately - are in [the rationale companion][spec-020-rationale].

### Decision 10 — Joint `0.0.7` cut

`0.0.7` ships a bundle of WIP cards: `DONE-020-0.0.7` (this card), `DONE-021-0.0.7` (`apps.py`), `DONE-022-0.0.7` (schema-export management command), `DONE-023-0.0.7` (multi-db cooperation contract), `DONE-024-0.0.7` (Django Trac #37064 hardening), `DONE-025-0.0.7` (warning-free scalar registration) and `DONE-026-0.0.7` (scalar conversion end-to-end coverage). The version bump in `pyproject.toml #"version ="` and `django_strawberry_framework/__init__.py #"__version__ ="` and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

There is no separate release-cut card in `KANBAN.md`; the policy names the owner rather than a card: whichever feature card ships last owns the bump.

The rejected alternatives (each card bumping independently; blocking all five cards on one integration commit) are in [the rationale companion][spec-020-rationale].

## Implementation plan

The slice ships as **six slices** aligned with the [Slice checklist](#slice-checklist), of which Slice 0 is a verification spike that does NOT produce a commit (Slice 0 is a throw-away local check that the factory-function shape integrates with `@strawberry.type`; the stub is discarded after confirmation). Slices 1-5 each map to one commit. The per-commit breakdown exists for review legibility; squashing Slices 1-5 into a single PR is acceptable.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 0 — Pre-implementation verification | (sandbox; no repo files touched) | 0 (throw-away spike; the stub is discarded after the shape is confirmed) | `0 / 0` |
| 1 — Module + factory function | `django_strawberry_framework/list_field.py` (new), `django_strawberry_framework/__init__.py`, `tests/base/test_init.py` | 0 (validation tests land in Slice 2 / 3) | `+150 / -2` |
| 2 — Validation | `django_strawberry_framework/list_field.py`, `tests/test_list_field.py` (new) | the validation-guard tests | `+80 / -0` |
| 3 — Optimizer + `get_queryset` cooperation tests | `tests/test_list_field.py` | behavior tests, one-to-one with the named methods in [Test plan](#test-plan): default resolver applies sync `get_queryset`, default resolver awaits async `get_queryset`, default resolver works under both `schema.execute_sync` and `await schema.execute`, sync coroutine rejection, sync consumer-resolver `QuerySet` return receives `get_queryset`, sync consumer-resolver Python-`list` return passes through, async consumer-resolver `QuerySet` return receives `get_queryset`, async consumer-resolver Python-`list` return passes through, nullable-outer via consumer annotation renders `[T!]`, non-nullable-outer default renders `[T!]!`, `DjangoListField` at root position is optimized, FK-id elision survives, `Meta.primary` explicit primary returns primary queryset, `Meta.primary` secondary target uses secondary `get_queryset` | `+280 / -0` |
| 4 — Live HTTP coverage | `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py` | 1 new HTTP test for the **added** `all_library_branches_via_list_field` field (no existing resolver is replaced) | `+25 / -0` |
| 5 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md` | 0 | `+65 / -12` |

Total expected delta: ~530 lines across the six slices (Slice 0 contributes no repo-resident lines).

The six slices must be authored in order. Slice 0 is a gating check — Slice 1 begins only after the factory-function shape is verified end-to-end. Slice 4 depends on Slice 1 (the symbol must exist) and Slice 3 (the contracts must be pinned by tests before consuming the symbol from the example app).

## Edge cases and constraints

- **`Meta.primary` ambiguity not resolved at the registry**. `DjangoListField(TargetType)` accepts an explicit `DjangoType` so the registry's primary/secondary state is irrelevant at the field site. If `finalize_django_types()` later raises a `Meta.primary` ambiguity error for the target's model, that error is the one consumers see — not a `DjangoListField`-specific one.
- **Custom managers via `Meta.default_manager_name`**. Django's `_default_manager` honors the model's `default_manager_name` if set; `DjangoListField` inherits this for free. No special-casing.
- **`null=True` on the row's primary key**. Django does not allow nullable single-column primary keys on normal models; if a future Django version adds support, the `DjangoListField` resolver path passes through unchanged because the field doesn't introspect the pk.
- **Model proxies**. Django proxy models share the underlying table; `_default_manager.all()` returns proxy instances. `DjangoListField` works the same way it does for the base model; the consumer just passes the proxy-backed `DjangoType`.
- **Abstract `DjangoType` bases without a `Meta`**. The validation in [Decision 5](#decision-5--validation--error-shapes) catches this via the "registered DjangoType" check — abstract bases don't have `__django_strawberry_definition__` and raise `ConfigurationError` at construction.
- **Multi-database routing**. `model._default_manager.all()` is routed by Django's database router automatically. The multi-db cooperation contract pinned by `DONE-023-0.0.7` already covers the relation-traversal case; root-list fields inherit the same routing behavior because the queryset is the same `Manager.all()` call relations use.
- **[Strictness mode][glossary-strictness-mode] and N+1 detection**. The optimizer's strictness mode operates at the relation-walk level, not the root-resolver level. `DjangoListField`-served root querysets pass through the strictness contract unchanged.
- **`schema.execute_sync` testing**. The field works under both `schema.execute_sync` (synchronous) and `await schema.execute` (asynchronous) call shapes; the in-async-context detection handles both. Pinned by `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`.
- **`functools.partial`-wrapped and callable-object async consumer resolvers work.** `inspect.iscoroutinefunction(functools.partial(some_async_fn, ...))` returns `False`, and so does `inspect.iscoroutinefunction(instance)` for an instance whose `__call__` is `async def` — which is exactly why neither is the predicate the factory uses. Construction-time detection routes through `django_strawberry_framework/utils/typing.py::is_async_callable`, the wrapper-aware superset of `inspect.iscoroutinefunction`, so every spelling that predicate covers builds the async wrapper and its `Manager`/`QuerySet` return receives `get_queryset` — the two above, a raw `staticmethod async def` descriptor (`tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`), and any nesting of the two wrapper kinds. No consumer rewrapping is needed:

  ```python path=null start=null
  # WORKS -- is_async_callable sees through the partial, so DjangoListField
  # builds an async _wrap and BranchType.get_queryset(...) is applied to the
  # awaited return value.
  field = DjangoListField(
      BranchType,
      resolver=functools.partial(my_async_resolver, some_arg=1),
  )

  # WORKS -- an async generator function, and a plain callable object whose
  # __call__ is `async def`, are both detected the same way.
  field = DjangoListField(BranchType, resolver=my_async_generator_resolver)
  ```

  The factory carries no runtime-coroutine fallback, and needs none: a resolver detected as sync that nonetheless returns a coroutine, a custom awaitable, or a `Future` is rejected loudly rather than passed through with the hook skipped (`tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_coroutine_rejects_loudly`, `::test_djangolistfield_sync_resolver_returning_custom_awaitable_rejects_loudly`, `::test_djangolistfield_sync_resolver_returning_future_cancels_it`). An async-only iterable returned from a sync-detected resolver is routed to the async-iterable arm instead ([Decision 2](#decision-2--default-resolver-shape)).

## Test plan

Tests live in two trees, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement is mandatory.

### `tests/test_list_field.py` (new)

Package tests; system-under-test is `django_strawberry_framework`. The file is the flat single-file Layer-3 module's mirror per `docs/TREE.md #"tests/test_<module>.py (flat, at the root)"`. The list below names the contract pins this card owes; the shipped file also carries the async-iterable, row-bound and sealed-boundary pins that [Decision 2](#decision-2--default-resolver-shape), [Decision 3](#decision-3--get_queryset-and-async-symmetry) and [Decision 5](#decision-5--validation--error-shapes) name, so it is not an inventory of the file.

Validation tests (Slice 2):

- `test_djangolistfield_rejects_non_class_argument` — passing a string, int, instance, etc., raises `ConfigurationError`.
- `test_djangolistfield_rejects_non_djangotype_class` — passing a plain class that doesn't subclass `DjangoType` raises `ConfigurationError`.
- `test_djangolistfield_rejects_djangotype_without_definition` — passing an abstract `DjangoType` base without a `Meta` raises `ConfigurationError`.
- `test_djangolistfield_rejects_non_callable_resolver` — `resolver="not callable"` raises `ConfigurationError`.

Behavior tests (Slice 3):

- `test_branches_via_list_field_default_resolver_applies_get_queryset_live`, in `examples/fakeshop/test_query/test_library_api.py` rather than here — declare a `DjangoType` with `get_queryset` filtering on `is_private=False`; assert the field's default resolver serves only visible rows. The default-resolver path is reachable from a real `/graphql/` query, so the live tier owns it per `AGENTS.md` #"Test through real usage"; the live docstring names the retired package test.
- `test_djangolistfield_async_get_queryset_is_awaited` — declare a `DjangoType` with an `async def get_queryset(...)`; assert the field's default resolver awaits the coroutine in an async context and returns the filtered queryset.
- `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution` — declare a `DjangoType` with a **sync** `get_queryset(...)`; execute the field via `schema.execute_sync(...)` AND via `await schema.execute(...)`; assert both return the filtered queryset. Pins the runtime `in_async_context()` branch in the default resolver (the case where `in_async_context()` is True but `get_queryset` is sync). Without this test, the dual-execution shape promised in the Edge cases section is unverified.
- `test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset` — declare a `DjangoType` with an `async def get_queryset(...)`; assert the sync resolver raises `SyncMisuseError` (a `ConfigurationError` subclass) matching the `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync #"reject_async_in_sync_context"` contract.
- `test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied` — supply a **sync** `resolver=` returning `Model.objects.filter(...)`; assert the resolved field's queryset has been threaded through `target_type.get_queryset(qs, info)` (verifiable by giving the target a `get_queryset` that filters out a known row, then asserting that row is absent from the field's output).
- `test_djangolistfield_consumer_resolver_python_list_return_passes_through` — supply a **sync** `resolver=` returning a Python `list[T]`; assert `target_type.get_queryset(...)` is NOT applied (verifiable by including a row that `get_queryset` would have filtered out and asserting it survives).
- `test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied` — supply an `async def resolver(...)` returning `Model.objects.filter(...)`; execute through Strawberry's async schema execution; assert the queryset has been threaded through `target_type.get_queryset(qs, info)` exactly the same way as the sync test. Pins that the wrapper awaits the consumer coroutine BEFORE the isinstance check.
- `test_djangolistfield_async_consumer_resolver_python_list_return_passes_through` — supply an `async def resolver(...)` returning a Python `list[T]`; assert `target_type.get_queryset(...)` is NOT applied. Pins that the await-then-isinstance ordering is symmetric across return shapes.
- `test_djangolistfield_at_root_position_is_optimized` — declare a `DjangoType` with relations; query through a root `DjangoListField` with a nested selection. Assert **exactly** `N` queries via `assertNumQueries(N)` (exact count, not `<= N`; a permissive bound would let a refactor that quietly changes the per-query count slide past unnoticed). `N` is one base SELECT plus one extra SELECT per `prefetch_related` relation in the nested selection (e.g., for `{ allBranches { id name shelves { id } } }` against `Branch` with `shelves` as a reverse-FK, `N = 2` — one Branch SELECT, one Shelf prefetch SELECT). The test docstring documents the derivation so a future maintainer who changes the selection shape can recompute `N` deterministically.
- `test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves`, in `examples/fakeshop/test_query/test_library_api.py` rather than here — a Query field declared `list[BranchType] | None = DjangoListField(BranchType)`; assert the rendered GraphQL type is `[BranchType!]` (nullable outer, non-null items) and that it resolves over the wire. Its non-nullable companion below stays package-internal, so the pair splits across the two tiers; `tests/test_list_field.py` carries a `NOTE:` block above the companion explaining why.
- `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation` — declare a Query field as `field: list[BranchType] = DjangoListField(BranchType)`; assert the rendered GraphQL type is `[BranchType!]!` (non-null outer, non-null items).
- `test_djangolistfield_fk_id_elision_survives` — query `{ allBranches { shelves { id } } }` (or equivalent); assert no JOIN was issued for the `id`-only relation selection (FK-id elision still fires).
- `test_djangolistfield_with_meta_primary_true_returns_primary_queryset` — see [Decision 6](#decision-6--metaprimary-interaction).
- `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset` — see [Decision 6](#decision-6--metaprimary-interaction).

### `examples/fakeshop/test_query/test_library_api.py` (extend)

System-under-test is the live `/graphql/` HTTP endpoint. Coverage MUST be earned here per the `docs/TREE.md #"**Coverage priority.**"` rule ("Any package coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against fakeshop MUST be earned in `examples/fakeshop/test_query/`").

Add `test_library_branches_via_djangolistfield_optimized_nested_selection` (or extend an existing test) that:

- issues `{ allLibraryBranchesViaListField { id name shelves { id code } } }` against `/graphql/`;
- asserts the response includes every branch row (order-agnostic — sort by `id` in the assertion if needed since the new field has no `order_by`);
- asserts the optimizer planned `prefetch_related("shelves")` for the nested selection (via the existing `assertNumQueries` / SQL-sniffer pattern in `test_library_api.py`).

`cls.get_queryset` cooperation is **not** asserted by this HTTP test. The library example's real `BranchType` has no custom `get_queryset` today, and adding one would mutate every `BranchType` path in the schema (including nested `book → shelf → branch` selections and existing branch tests). Package-internal `tests/test_list_field.py` has the dedicated coverage with isolated fixtures.

The HTTP test file's reload pattern from [`docs/TREE.md #"HTTP tests that import the project schema"`][tree] must be preserved: clear the global registry, reload app schema modules, then reload the project schema and URLconf. The new test follows this pattern unchanged.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Flip [`DjangoListField`][glossary-djangolistfield] from `planned for 0.0.7` to `shipped (0.0.7)`.
  - Update the entry body to describe the shipped contract: factory function (not class), `list[T]` annotation on the class attribute drives outer nullability, default `model._default_manager.all()` resolver, `cls.get_queryset(...)` applied in sync + async contexts AND to consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity), root-only optimizer cooperation.
  - Update the [Public exports][glossary-public-exports] list near the top to include `DjangoListField`.
  - Update the Index table's status column.

- [`README.md`][readme]
  - Update the "Shipped today" / status bullet list to mention `DjangoListField`.

- [`docs/README.md`][docs-readme]
  - Add `DjangoListField` to the "Shipped today (`0.0.7`)" bullet list.
  - Optional: add a small example in the Quick start section showing the `DjangoListField` shape next to the existing `@strawberry.field` example.

- [`docs/TREE.md`][tree]
  - Add `list_field.py` to the "current on-disk layout" section.
  - Add `list_field.py` to the "target package layout" section as its own flat single-file Layer-3 module bullet.
  - **Remove `DjangoListField` from the existing `connection.py # [alpha] DjangoConnectionField + DjangoListField` line** so the target layout doesn't advertise two homes for the symbol.
  - Add `tests/test_list_field.py` to the current test-tree section.

- [`GOAL.md`][goal]
  - Update the "Coming from `graphene-django`" migration subsection at `GOAL.md #"### Coming from \`graphene-django\`"` — add a one-line bullet under the existing diff block noting that `DjangoListField` replaces graphene-django's symbol of the same name with no shape change at the migration site (the Success criteria mention at `GOAL.md #"Expose model collections with \`DjangoConnectionField\` or \`DjangoListField\`"` is already accurate as a forward-pointer and needs no edit).

- [`TODAY.md`][today]
  - Drop `DjangoListField` from the wait-for list if listed there.
  - Update the `library` summary line to mention that the **new** `all_library_branches_via_list_field` root field exercises `DjangoListField`'s default resolver path (no existing resolver was replaced).

- [`KANBAN.md`][kanban]
  - Move `DONE-020-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id; rewrite the body in past tense using the add-only language: the Done body says "added `all_library_branches_via_list_field`", not "replaced one of the `all_library_*` resolvers".

- [`CHANGELOG.md`][changelog]
  - **Append** to the existing `[0.0.7]` `### Added` subsection (create the subsection only if absent; do NOT create a second `[0.0.7]` heading — the repo's `CHANGELOG.md` already has a `[0.0.7]` section from prior commits this patch, and every `0.0.7` card under the joint cut appends to the same shared section): `DjangoListField` — non-Relay `list[T]` field for **root Query fields**, with default `model._default_manager.all()` resolver, `cls.get_queryset(...)` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity), optimizer cooperation via root-gating, outer nullability driven by the consumer's class-attribute annotation, and standard field-level metadata pass-through (`description`, `deprecation_reason`, `directives`).
  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 10](#decision-10--joint-007-cut), NOT this slice.

## Out of scope (explicitly tracked elsewhere)

- `DjangoConnectionField` and Relay-shaped pagination: `DONE-030-0.0.9` in [`KANBAN.md`][kanban].
- [`DjangoNodeField`][glossary-djangonodefield] (root-level Relay node lookup): `DONE-030-0.0.9` (same card as connection field per current KANBAN scoping).
- Filter / order / search / aggregate input arguments on the field: `DONE-027-0.0.8` / `DONE-028-0.0.8` / `TODO-BETA-047-0.1.2` / `TODO-BETA-049-0.1.3`.
- Cascade permissions and field-level permissions: `DONE-034-0.0.10`.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]: `DONE-033-0.0.9` (note: same-named entry under the connection card).
- Multi-database / sharding-aware queryset routing: cooperation contract `DONE-023-0.0.7`; first-class sharding-aware planning post-`1.0.0` in [`BACKLOG.md`][backlog].
- Auto-upgrade of reverse-FK / M2M relation fields to `DjangoListField`-based plumbing: deferred indefinitely; see [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields).
- Pagination on `DjangoListField`: not on the roadmap; pagination is the connection field's responsibility. Row **limits** are the opposite of out of scope — every `DjangoListField` is row-bounded (see [Row bound](#row-bound)).

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/list_field.py` exists and defines `DjangoListField` as a factory function per [Decision 1](#decision-1--module-location-mechanism--public-export) and [Decision 2](#decision-2--default-resolver-shape) — returns the value of `strawberry.field(resolver=..., description=..., ...)`; closure-captures `target_type`; the resolver signature is the Strawberry-native `(root: Any, info: Info)` shape (`Any` from `typing`, `Info` from `strawberry.types`; `**kwargs` is NOT used because Strawberry treats every parameter as a GraphQL argument). Sync callables, async callables (every shape `django_strawberry_framework/utils/typing.py::is_async_callable` covers: `async def`, an `async def __call__` instance, a raw `staticmethod` descriptor, and nestings of `functools.partial` / `staticmethod` over those) and async generator functions are all supported as consumer resolvers, the wrapper shape chosen at construction time by `is_async_generator_callable` then `is_async_callable`; there is no runtime-coroutine fallback, and a sync-detected resolver returning a coroutine / awaitable / `Future` is rejected loudly instead.
2. `django_strawberry_framework/__init__.py` re-exports `DjangoListField` and includes it in `__all__` in alphabetical position.
3. `tests/base/test_init.py`'s `__all__` assertion includes `"DjangoListField"`.
4. `tests/test_list_field.py` exists and contains the tests listed in the [Test plan](#test-plan), excepting the two the Test plan pins at the live `/graphql/` tier instead.
5. `examples/fakeshop/apps/library/schema.py` **adds** the new root fields named in [Decision 9](#decision-9--example-app-migration-posture) to the `Query` class; every pre-existing `all_library_*` resolver is unchanged.
6. `examples/fakeshop/test_query/test_library_api.py` adds a test that asserts the new `DjangoListField`-served field's `/graphql/` response and optimizer plan via the existing `assertNumQueries` / SQL-sniffer pattern. The HTTP test does NOT assert `get_queryset` application — that coverage lives in package-internal `tests/test_list_field.py` with isolated fixtures.
7. Constructor-time validation rejects a non-class, a non-`DjangoType`, a subclass carrying no registered definition of its **own** (an inherited one does not count), and a non-callable `resolver=`, with `ConfigurationError`s matching the message contract in [Decision 5](#decision-5--validation--error-shapes); a non-positive `max_rows=` is rejected at the same site.
8. The default resolver returns a `QuerySet` (not a Python `list`) so the existing root-gated `DjangoOptimizerExtension` plan applies unchanged at the root. The queryset is row-bounded per [Row bound](#row-bound), and the bound is applied by slicing after the visibility hook and any consumer post-processing, so a `QuerySet` carries it into SQL as a `LIMIT`.
9. The sync path rejects an async `cls.get_queryset` with `SyncMisuseError`, the `ConfigurationError` subclass that `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` raises for every read surface.
10. The async path awaits the `get_queryset` coroutine and applies the optimizer through the same root-gated hook.
11. A consumer-supplied `resolver=` runs in place of the default body. When the consumer return value is a `Manager` or `QuerySet`, `target_type.get_queryset(qs, info)` is applied (graphene-django parity); a Python-`list` return passes through unchanged; an async-only iterable (an async generator, or an `AsyncIterable` from a sync-detected resolver) is bounded under async execution and rejected with `SyncMisuseError` under sync execution. Every path is pinned by tests.
12. Outer-list nullability is driven by the consumer's class-attribute annotation: `list[T]` → `[T!]!`, `list[T] | None` → `[T!]`. Both renderings are pinned by schema-introspection tests.
13. The contract is **root list fields only** in `0.0.7`. Nested non-root usage is functional but not root-optimized. The CHANGELOG and GLOSSARY entries reflect this scope.
14. `Meta.primary` interaction is covered: a model with multiple `DjangoType`s, one declared primary, is queryable through `DjangoListField(PrimaryType)` AND `DjangoListField(SecondaryType)` independently per [Decision 6](#decision-6--metaprimary-interaction).
15. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
16. `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the [Doc updates](#doc-updates) section. The `docs/TREE.md` target-layout `connection.py` line has `DjangoListField` removed from its bullet.
17. `KANBAN.md` moves `DONE-020-0.0.7` to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope in **add-only language**: the body says "added `all_library_branches_via_list_field`", not "replaced one of the `all_library_*` resolvers".
18. The version bump is NOT in this card per [Decision 10](#decision-10--joint-007-cut); **the last `0.0.7` card to ship** owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion. There is no separate release-cut card; the policy names the owner, not a card.
19. Exactly one new public export (`DjangoListField`) is added; no other public names change.
20. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest` passes with 100% package coverage.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[today]: ../../TODAY.md
[today-visibility-filtering-via-get_queryset]: ../../TODAY.md#visibility-filtering-via-get_queryset

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary-apply-cascade-permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-get-queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-015]: spec-015-relay_interfaces-0_0_5.md
[spec-018]: spec-018-meta_primary-0_0_6.md
[spec-020-rationale]: appx/spec-020-list_field-0_0_7-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
