# Review: `docs/spec-021-filters-0_0_8.md`

## High

### H1 - Layer 5 uses `strawberry.lazy(...)` as an object-path lookup, but Strawberry resolves module globals only

`docs/spec-021-filters-0_0_8.md#decision-3--six-layer-lazy-resolution-pipeline` proposes forms like `strawberry.lazy("django_strawberry_framework.filters.inputs._registry.{TargetFilterSet}InputType")`. That cannot work with the installed Strawberry API. `strawberry.lazy(module_path)` takes a module path; `strawberry.types.lazy_type.LazyType.resolve_type` imports that module and returns `module.__dict__[type_name]`. It does not traverse a dict, and it does not import `module.TypeName` as an object path.

Fix: make generated filter input classes real module globals in `django_strawberry_framework.filters.inputs` and reference them with `Annotated["TargetFilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]`. The input registry can still exist, but it must mirror actual globals if `strawberry.lazy` is the cycle-breaking mechanism. Update Decision 3, Decision 9, Risks, DoD item 6, and the `tests/filters/test_inputs.py` expectations around this exact shape.

### H2 - The spec does not define how a Strawberry `filter:` argument reaches live root fields

The spec says finalizer phase 2.5 calls `FilterArgumentsFactory(filterset_cls).arguments`, and Slice 4 says `all_library_books(filter: ...)` works over live HTTP. That is still a Graphene-shaped concept unless the spec pins how Strawberry sees a resolver argument annotation before schema construction. Current fakeshop root fields are normal `@strawberry.field` resolvers, and Strawberry collects arguments from Python signatures/annotations; finalizing `DjangoType`s does not mutate `apps.library.schema.Query` fields after `@strawberry.type` has collected them.

Fix: add a Strawberry-native argument surface before claiming live HTTP filtering. Good options:

- expose `FilterSet.input_type()` / `filter_input_type(FilterSet)` so resolvers can write `filter: BranchFilter.input_type() | None = None` or an equivalent stable annotation alias;
- extend `DjangoListField` with `filterset_class=` and have the field factory own the argument injection; or
- define an explicit generated-input alias pattern using `Annotated["BranchFilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` and require finalizer to materialize the class before `strawberry.Schema(...)`.

Whichever path you choose, Slice 4 needs concrete resolver code shape. Without it, the implementation can build input classes forever and still expose no GraphQL `filter:` argument.

### H3 - Decision 5's `django-filter` posture contradicts the upstream implementation, current dependency graph, and project promises

`docs/spec-021-filters-0_0_8.md#decision-5--django-filter-soft-dependency-posture` says the package drops `django-filter` and does not subclass `django_filters.BaseFilterSet`. But the cookbook code being "ported verbatim" depends on `django-filter` at the load-bearing layer: `django_graphene_filters/filterset.py::AdvancedFilterSet` subclasses `filterset.BaseFilterSet`, reads `declared_filters`, `base_filters`, `.filters`, `.form`, `.qs`, `get_filters()`, form validation, `Filter.method`, and lookup parsing from `django-filter`. The repo also already has a hard dependency in `pyproject.toml #"django-filter>=25.2"`, and `GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"` promises direct DRF/`django-filter` migration.

Fix: either embrace `django-filter` as a hard dependency and make the package `FilterSet` subclass `django_filters.BaseFilterSet` (recommended, because it matches the current dependency and avoids reimplementing form/filter semantics), or explicitly scope the full replacement: remove the dependency from `pyproject.toml`, update `GOAL.md`/`README.md`, and add detailed implementation/test requirements for replacing `BaseFilterSet`, `Filter`, `MultipleChoiceFilter`, `FilterMethod`, form cleaning, lookup generation, and `.qs` behavior. The current middle position is not implementable as written.

### H4 - FK/PK to `GlobalIDFilter` is over-broad and breaks non-Relay types

The spec repeatedly says `FILTER_DEFAULTS` maps FK/PK to `GlobalIDFilter`, and the live test plan filters `Book.shelf` by a `<gid>`. In the current fakeshop schema, `ShelfType` is not a Relay node; non-Relay model IDs are scalar `int` via `django_strawberry_framework/types/converters.py::SCALAR_MAP`. A blanket FK/PK `GlobalIDFilter` would make filters require Relay GlobalIDs even when the exposed GraphQL type uses an integer ID, and the planned shelf test would not match the actual public schema.

Fix: make ID filter selection conditional on the target `DjangoType`'s Relay shape. Relay-node targets should accept `relay.GlobalID`/GlobalID strings and decode to PKs; non-Relay targets should accept the converted PK scalar. Update `FILTER_DEFAULTS`, the forward-FK live test, and the Relay-aware test coverage accordingly. If the intended test is GlobalID-specific, use `GenreType` or make `ShelfType` explicitly Relay-shaped.

### H5 - The generated input registry has no lifecycle contract, so finalizer retries and fakeshop reloads can collide

Decision 6 says the new finalizer work is idempotent, and Decision 9 says duplicate input names raise. The spec never defines how those two facts coexist. Existing tests reload fakeshop schemas by calling `django_strawberry_framework.registry.TypeRegistry.clear` only; a separate `filters.inputs` registry would survive that clear unless explicitly wired. A failed `finalize_django_types()` before `registry.mark_finalized()` could also leave partially registered filter input types behind, then collide on retry.

Fix: pin the lifecycle. `registry.clear()` should clear the filter input registry, or the reload fixture must call a public `clear_filter_input_registry()` helper. Registration should be idempotent for the same filterset/name pair and should raise only when the same GraphQL name is owned by a different filterset. Add tests for successful rerun after a partial finalizer failure and for fakeshop schema reload after input types were generated once.

### H6 - `and` / `or` / `not` cannot be emitted as Python dataclass field names

The spec asks `_build_logic_fields` to create `and`, `or`, and `not` fields directly. Strawberry input types wrap dataclasses, and dataclasses cannot generate an `__init__` with keyword-only parameters named `and`, `or`, or `not`. A dynamic class whose `__annotations__` contains `{"and": ...}` fails at input decoration time.

Fix: use Python-safe names (`and_`, `or_`, `not_`) with explicit GraphQL names (`strawberry.field(name="and")`, etc.). Update the implementation plan and tests to assert both sides: Python attributes are safe, GraphQL schema fields are exactly `and`, `or`, and `not`.

### H7 - `Meta.fields = "__all__"` auto-related traversal conflicts with the non-goal of implicit `FilterSet` generation

The Edge cases section says `Meta.fields = "__all__"` turns relation fields into `RelatedFilter` references with default lookups. But the Non-goals section defers auto-generation of `FilterSet`s from `Meta.fields`, and `RelatedFilter` requires a target `FilterSet` class. There is no specified source for a target `ShelfFilter`/`GenreFilter` when a relation appears under `"__all__"`.

Fix: narrow `"__all__"` to scalar fields and raw FK/PK lookups unless the relation has an explicit `RelatedFilter` declaration, or explicitly move relation-target dynamic filterset generation into this card. The first option is cleaner and keeps the non-goal true.

## Medium

### M1 - The fakeshop filter plan is missing required filter classes and references a nonexistent field

Slice 4 lists only `BranchFilter`, `BookFilter`, `LoanFilter`, and `PatronFilter`, but the planned live tests require `ShelfFilter` and `GenreFilter`: `BookFilter.shelf`, `BranchFilter.shelves`, and `BookFilter.genres` all need target filtersets for nested input. The related-queryset-boundary test also uses `Shelf.objects.filter(is_archived=False)`, but `examples/fakeshop/apps/library/models.py::Shelf` has no `is_archived` field.

Fix: add `ShelfFilter` and `GenreFilter` to Slice 4/DoD/docs, and either use an existing field for the boundary (`topic`, `code`, or `branch`) or explicitly add `is_archived` with a model migration and test data. Do not leave the model change implicit.

### M2 - The cross-module lazy-resolution claim is not covered by the planned fakeshop shape

The spec says fakeshop `RelatedFilter("BookFilter")` / `RelatedFilter("BranchFilter")` exercises both same-module and cross-module lazy resolution, but a single `examples/fakeshop/apps/library/filters.py` file only exercises same-module unqualified-name resolution. The `tests/types/test_definition_order.py` addition checks `Meta.filterset_class` module boundaries, not `RelatedFilter` absolute-import resolution.

Fix: add a dedicated `RelatedFilter("apps.library.filters.ShelfFilter")` or split one filterset into a second fixture module and test that path. Keep same-module and absolute-path cases distinct in the test plan.

### M3 - Public-export documentation contradicts the top-level `__all__` decision

Decision 2 says `FilterSet` and `RelatedFilter` are subpackage exports only and the top-level package `__all__` stays unchanged. Slice 5 then tells `docs/GLOSSARY.md#public-exports` to add `FilterSet` and `RelatedFilter` after `DjangoType`, but that glossary section is explicitly "Symbols re-exported from `django_strawberry_framework`".

Fix: either top-level re-export the filter symbols, or leave `Public exports` unchanged and document them under the Filtering category / individual entries as subpackage exports from `django_strawberry_framework.filters`. Given Decision 2, the latter is the consistent fix.

### M4 - Existing direct-`django_filters.FilterSet` migration docs must be updated if the spec rejects that path

Separate from H3's implementation issue, the docs currently promise direct reuse: `GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`. The spec says the opposite and also says `GOAL.md` needs no edit.

Fix: if the spec keeps rejecting plain `django_filters.FilterSet`, Slice 5 must update `GOAL.md` and any README wording that implies direct reuse. If direct reuse is still a project goal, Decision 5 needs to reverse course.

## Low

### L1 - Several documentation anchors/links are misleading or malformed

- The Predecessors line links `TypeRegistry` to `[glossary-djangotype]`; either add a real `TypeRegistry` glossary row/entry or cite `django_strawberry_framework/registry.py::TypeRegistry`.
- Decision 9 has malformed markdown around `OrderSet` / `WIP-ALPHA-022-0.0.8` (`OrderSet` for ``[`WIP...``).
- The link-definition block places `[spec-021]` and `[spec-021-terms]` under the `docs/SPECS/` header even though the active files currently live at `docs/`.

Fix these while revising the architectural items so the spec stays checker-clean and convention-clean.

## Validation Notes

- Ran `uv run python scripts/check_spec_glossary.py --spec docs/spec-021-filters-0_0_8.md`; it reports `OK: 32 terms`.
- Inspected the installed Strawberry `strawberry.lazy` / `LazyType.resolve_type` implementation locally to verify H1.
- Inspected current `types/base.py`, `types/finalizer.py`, `registry.py`, `list_field.py`, fakeshop library schema/models/tests, `pyproject.toml`, `GOAL.md`, and the referenced upstream `django_graphene_filters` / `graphene_django.filter` filter code.
- Did not run pytest.
