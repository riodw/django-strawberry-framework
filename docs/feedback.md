# Review feedback for `docs/spec-021-filters-0_0_8.md`

## High

### H1. `FILTER_DEFAULTS` is pinned on the schema factory path, not the runtime filter-generation path

`docs/spec-021-filters-0_0_8.md#decision-4--upstream-primitives-parity-floor` says the Relay-vs-scalar FK/PK decision runs inside `FilterArgumentsFactory._ensure_built`. That only controls the Strawberry input shape. The actual `django-filter` filter instances are created earlier by `FilterSet.get_filters()` via `django_filters.filterset.BaseFilterSet.filter_for_field()` / `filter_for_lookup()`, which reads `cls.FILTER_DEFAULTS`.

If implementation follows the spec literally, the GraphQL input can expose `relay.GlobalID` for `BookFilter.genres` while the runtime filter instance is still whatever vanilla `django-filter` generated. That is the worst class of bug: the schema accepts one wire shape and the queryset translator expects another.

Root fix: make the conditional default-selection a `FilterSet` concern, not only a `FilterArgumentsFactory` concern. Put the adapted defaults on the package `FilterSet` class or a mixin it inherits, and override `filter_for_field()` / `filter_for_lookup()` where conditional target inspection is needed. Then make `FilterArgumentsFactory` derive its input field shape from `filterset_cls.get_filters()` / the actual filter instances, not from a parallel map. Add tests that assert both the generated input type and the generated filter class agree for non-Relay `ShelfType` and Relay `GenreType`.

### H2. The runtime application API is still inconsistent and conflicts with `django-filter`'s instance method contract

The user-facing example calls `GalaxyFilter.apply(filter, queryset, info)`, Slice 4 says root resolvers call `filters.BranchFilter.filter_queryset(...)`, and Decision 8 describes `FilterSet.filter_queryset(input, queryset, info)`. But upstream `django_filters.filterset.BaseFilterSet.filter_queryset` is an instance method with signature `filter_queryset(self, queryset)` and consumes `self.form.cleaned_data` after validation.

Overloading that method into a class-level Strawberry-input entry point will either break `django-filter`'s `.qs` flow or force an awkward signature split. The spec also does not pin the bridge from Strawberry input dataclasses (`and_`, `or_`, nested input objects) into the dict/form data shape `django-filter` validates.

Root fix: define one public classmethod, for example `FilterSet.apply(input_value, queryset, info)`, as the resolver-facing API. That method should normalize the Strawberry input object into filter data, extract `request` from `info.context`, instantiate `cls(data=data, queryset=queryset, request=request)`, run validation/permission checks, and return `filterset.qs`. Keep `filter_queryset(self, queryset)` as the `django-filter` instance override for tree-form logic. Update all examples, Decision 8, DoD item 13, and the test plan to use the same symbol.

### H3. `django_filters.BaseFilterSet` does not exist at the top-level import path

The spec repeatedly says `FilterSet` subclasses `django_filters.BaseFilterSet`. In the pinned local `django-filter` version, `django_filters.BaseFilterSet` is not exported; the class is `django_filters.filterset.BaseFilterSet`. The cookbook reference imports it through `from django_filters import filterset` and subclasses `filterset.BaseFilterSet`.

If an implementer writes `class FilterSet(django_filters.BaseFilterSet, ...)` from this spec, the module fails at import time.

Root fix: make the import path exact everywhere. Prefer the cookbook shape: `from django_filters import filterset`, `class FilterSet(..., filterset.BaseFilterSet, metaclass=FilterSetMetaclass)`, and `class FilterSetMetaclass(filterset.FilterSetMetaclass)`. If you intentionally choose public `django_filters.FilterSet` instead, spell out why the extra public base is better than the cookbook's direct `BaseFilterSet` base.

### H4. The related-queryset boundary HTTP test asserts output filtering that the proposed implementation does not provide

`docs/spec-021-filters-0_0_8.md#examplesfakeshoptest_querytest_library_apipy-extend` says the boundary test should assert shelves outside `topic="permanent collection"` never appear. But the cookbook `_apply_related_queryset_constraints` shape filters the parent queryset using `shelves__in=<constraint_qs>`; it does not filter the nested relation resolver output.

That matters in the current fakeshop schema: `examples/fakeshop/apps/library/schema.py::BranchType.shelves` is a consumer-authored resolver returning `list(self.shelves.order_by("-code"))`. A branch with one permanent shelf and one non-permanent shelf can pass the parent `Branch` filter and still return both shelves in the response.

Root fix: either narrow the test to the real boundary contract ("branches without a matching constrained shelf are excluded; nested filter clauses cannot use shelves outside the constraint to make a branch match") or add a separate relation-output scoping feature. The latter is bigger than this card and would need to interact with consumer-authored relation resolvers and optimizer `Prefetch` planning, so the cleaner fix is to change the test assertion.

## Medium

### M1. The GOAL migration promise is still false after the parent-class-swap revision

`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"` shows `class CategoryFilter(django_filters.FilterSet)` being assigned directly to `Meta.filterset_class`. The revised spec says that promise is honored by a parent-class swap, while `_validate_meta` rejects plain `django_filters.FilterSet` subclasses.

That is not "plugs in directly"; it is a one-line migration. Either implement an adapter/acceptance path for plain `django_filters.FilterSet`, or update `GOAL.md` and the spec prose to say consumers swap the base class to `django_strawberry_framework.filters.FilterSet`.

### M2. `filter_input_type` is a new public helper but is missing from the terms CSV and some doc sweeps

The spec adds a glossary entry and public re-export for `filter_input_type`, but `docs/spec-021-filters-0_0_8-terms.csv` does not list it. The checker still passes because it only validates listed terms, so the omission hides the new public symbol from the glossary gate.

Add a CSV row for `filter_input_type` and update the expected checker count. Also include the helper in the README/docs README sweep where the spec currently says only `FilterSet` / `RelatedFilter` / `Meta.filterset_class`.

### M3. The live HTTP test count is internally inconsistent

The spec says "6-8 new live HTTP tests", the Slice 4 table says 8, and the test-plan bullet list names 9 separate tests: scalar, choice enum, non-Relay FK, Relay M2M, reverse FK, logical operators, optimizer cooperation, related-queryset boundary, and absolute-import `RelatedFilter`.

Pin the exact count. If the cross-module `GenreFilter` path is meant to be covered by the Relay M2M test, merge those bullets explicitly; otherwise say 9 tests and update Slice 4 / DoD item 14 / CHANGELOG wording.

### M4. The Relay GlobalID test construction API is backwards

The test plan says to construct a GlobalID via `relay.GlobalID.from_id(...)` for a seeded `Genre`. In Strawberry, `GlobalID.from_id(value)` parses an already-encoded global ID string. Construction is `str(relay.GlobalID(type_name="GenreType", node_id=str(genre.pk)))`.

Update the test plan so the test does not copy a parser call into the setup path.

### M5. `registry.clear()` needs an import-cycle-safe integration point

Decision 9 says `registry.clear()` calls `clear_filter_input_namespace()`, but the spec does not pin how. `django_strawberry_framework/registry.py` is a low-level module imported by most of the package; adding a top-level import from `django_strawberry_framework.filters.inputs` risks a cycle once `filters` imports exceptions, registry helpers, types, or converters.

Pin a local import inside `TypeRegistry.clear()` or an optional callback registration pattern. Also add a test that imports `django_strawberry_framework.registry` alone before importing `django_strawberry_framework.filters` and verifies `registry.clear()` still works.

## Low

### L1. Several `GOAL.md line 450` references should be converted to substring anchors

The spec still uses prose references like `GOAL.md line 450`. Standing docs should use section/substr anchors, e.g. `GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`.

### L2. `materialize_input_class` has two signatures in the prose

Decision 3 mentions `materialize_input_class(module, name, cls)`, while Decision 6 / Decision 9 / DoD item 6 use `materialize_input_class(name, cls)`. Keep the two-argument helper unless there is a real need to materialize into arbitrary modules.

### L3. The `filter_input_type` timing wording is too absolute under postponed annotations

Decision 11 says the helper evaluates at module-load time and catches misuse at the resolver-declaration site. With `from __future__ import annotations`, Python stores the annotation expression as a string and Strawberry evaluates it during type/field processing, potentially more than once. The helper still works, but the timing claim should be softened to "when Strawberry evaluates the annotation during schema declaration/collection." Add one package test using a module fixture with postponed annotations.

### L4. The Graphene-Django Relay explanation is overstated

Decision 4 says `graphene-django` is unconditional because it "always Relay-shapes". Graphene-Django supports non-Relay `DjangoObjectType`; the unconditional `GlobalIDFilter` behavior is more specifically tied to the Graphene filter connection path and its defaults. Reword so the comparison does not overclaim upstream behavior.
