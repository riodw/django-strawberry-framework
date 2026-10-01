# Rationale: spec-027 — Filtering subsystem (justifications and rejected alternatives)

Deliberative companion to [`spec-027-filters-0_0_8.md`][spec-027]. The spec is the contract; this file carries why each of its twelve Decisions is shaped the way it is and which alternatives it rejected. Every Decision heading below reproduces the spec's heading text, so the spec's `[rationale-dN]` links land here.

## Decision 1 — Spec filename and canonical naming

Spec text: [Decision 1][spec-027-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] and observed by the spec cohort around this one ([`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018], [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019], [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020], [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021], [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022], [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023], [`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][spec-025]) bakes the card's NNN and target patch into the filename.
- The card body's `docs/spec-filters.md` predates that convention.
- References use whichever path the file actually has: the in-flight `docs/` path while the card was active, the archived `docs/SPECS/` path after [Step 8 of NEXT.md][next-step-8] moved it.

### Alternatives considered (and rejected)

- **Honor the card body verbatim with `docs/spec-filters.md`.** Rejected: breaks the structured-filename convention and would land an unnumbered spec next to a numbered cohort.
- **Longer topic slug `filtering_subsystem`.** Rejected: `filters` already names the architectural intent and matches the [`django_strawberry_framework/filters/`][filters] subpackage name.

## Decision 2 — Subpackage layout and public export surface

Spec text: [Decision 2][spec-027-d2].

### Justification

- The surface (seventeen `__all__` names plus the input adapters, the namespace and the factory) is too large for a flat module; the upstream cookbook spreads it across a dozen files under `django_graphene_filters/`, and the package collapses that to five by combining the filter-class primitives into `base.py`.
- The mirror partner is `tests/filters/`: the `__init__.py` shell, four source mirrors (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`), `test_finalizer.py`, and a `fixtures/` sub-package.
- Subpackage-scoped re-export is the shape every set family uses — `OrderSet` at `django_strawberry_framework/orders/__init__.py`, and the planned `AggregateSet` the same way — so the Layer-3 subpackages line up without each one widening the top-level `__all__`.

### Alternatives considered (and rejected)

- **Flat `django_strawberry_framework/filters.py` single-file module.** Rejected: the surface is too large and review legibility suffers.
- **Top-level public re-export (`from django_strawberry_framework import FilterSet`).** Rejected: the surface is opt-in for consumers who filter; widening the top-level `__all__` for every consumer (including optimizer-only ones) creates churn and a longer Index in `docs/GLOSSARY.md`.
- **Splitting `base.py` into per-primitive files (`array_filter.py`, `range_filter.py`, etc.) mirroring `graphene-django`'s layout.** Rejected: the primitives are short; the per-file layout is a `graphene-django` artifact, not a design choice the package needs to mirror.

## Decision 3 — Six-layer lazy-resolution pipeline

Spec text: [Decision 3][spec-027-d3].

### Justification

- The cookbook's architecture is proven (the working reference per [`START.md`][start]); reinventing it would burn schedule for no architectural gain.
- Layers 1–4 are library-agnostic Python on top of the shared `django_filters.filterset.BaseFilterSet` (per [Decision 5](#decision-5--django-filter-as-the-foundation)), so the port is mechanical, not creative.
- Layer 5's adaptation follows the actual Strawberry API (`Annotated["Name", strawberry.lazy("module")]` over module globals). A lazy reference on an object path (`module.path.ClassName`) or on a dict registry (`module._registry.Name`) cannot work, because Strawberry neither traverses object paths nor looks into dicts.
- Narrowing `Meta.fields = "__all__"` keeps the [Non-goals][spec-027-non-goals] "no implicit `FilterSet` generation from `Meta.fields`" rule self-consistent — `"__all__"` would otherwise need to invent target filtersets for every relation, which IS auto-generation.

### Alternatives considered (and rejected)

- **Design a new lazy-resolution mechanism from scratch.** Rejected: zero benefit over the cookbook's proven architecture; doubles the review surface.
- **Ship Layer 6 (dynamic-factory plumbing).** Rejected: no surface generates a `FilterSet`. [`DjangoConnectionField`][glossary-djangoconnectionfield] reads the target type's `Meta.filterset_class` like every other filtered surface, so a memoized dynamic-`FilterSet` cache would have no production reader.
- **Use `typing.ForwardRef` instead of `strawberry.lazy(...)`.** Rejected: Strawberry's documented forward-reference idiom IS `strawberry.lazy(...)`; reaching past it to `typing.ForwardRef` would build on private behavior.
- **Store input classes in a private dict registry and look them up at `LazyType.resolve_type` time via a Strawberry monkey-patch.** Rejected: monkey-patching Strawberry's internals is a maintenance hazard; the documented module-globals path is the cleaner shape.
- **`Meta.fields = "__all__"` auto-generates a default `<Target>Filter` for every relation it touches.** Rejected: this is the "implicit `FilterSet` generation" path the [Non-goals][spec-027-non-goals] section excludes; relations come through explicit `RelatedFilter` declarations.

## Decision 4 — Upstream-primitives parity floor

Spec text: [Decision 4][spec-027-d4].

### Justification

- Parity with `graphene-django` (the package's positioning claim) requires an equivalent for each parity-floor primitive; a missing one is the kind of gap that bites consumers immediately.
- Each primitive is short; porting all of them plus `FILTER_DEFAULTS` costs far less than explaining why the package is missing one.
- The FK/PK mapping is conditional on the target's Relay shape because the package's `DjangoType` is non-Relay by default: an unconditional GlobalID mapping would force GlobalID strings onto relations whose GraphQL type exposes an integer ID.
- `FILTER_DEFAULTS` lives on `FilterSet` rather than in the factory because `BaseFilterSet.filter_for_field()` / `filter_for_lookup()` consult `cls.FILTER_DEFAULTS` when they build the runtime filter instances; a factory-only conditional would let the GraphQL input and the runtime filter disagree.
- Multi-owner reuse is checked strictly because only the first binding is stored: GlobalID validation depends on the concrete GraphQL type name, and branch visibility depends on the bound owner's `get_queryset`, so a compatible-looking second owner could otherwise validate IDs or scope rows against the wrong type.

### Alternatives considered (and rejected)

- **Ship only `GlobalIDFilter`; defer the `TypedFilter` subclasses.** Rejected: half-shipping the parity floor invites the same churn as not shipping it; consumers hit the gap immediately.
- **Ship the parity floor under different symbol names (e.g., `DSTArrayFilter`).** Rejected: the upstream naming is the consumer's mental model; renaming for no architectural gain creates friction.

## Decision 5 — `django-filter` as the foundation

Spec text: [Decision 5][spec-027-d5].

### Justification

Three facts make the hard dependency the right shape:

1. [`pyproject.toml #"django-filter>=25.2"`][pyproject] already pins `django-filter` as a runtime dependency.
2. [`GOAL.md #"migrates with a one-line parent-class swap"`][goal-migration-shape] promises that an existing `django_filters.FilterSet` migrates with a one-line parent-class swap, which requires the package's `FilterSet` to be a `BaseFilterSet`.
3. The cookbook's `django_graphene_filters/filterset.py::AdvancedFilterSet` IS a `django_filters.filterset.BaseFilterSet` subclass; Layers 1–4 port verbatim only on top of that base.

- Removing the dependency would mean rewriting the [`GOAL.md`][goal] promise, the [`README.md`][readme] migration narrative, and every consumer-facing claim that a `django_filters.FilterSet` migrates by a parent swap — a fan-out nothing in [Goals][spec-027-goals] requires.
- Keeping it costs one line of inheritance plus the cookbook's import path.
- `django-filter>=25.2` installs cleanly on every supported Python / Django combination; because the dependency is hard, no `ImportWarning` branch exists.

### Alternatives considered (and rejected)

- **Drop `django-filter`; re-implement the `BaseFilterSet` machinery in the package.** Rejected: re-implementing `BaseFilterSet`, `Filter`, `MultipleChoiceFilter`, `FilterMethod`, form cleaning, lookup generation, and `.qs` is a large net-new code surface for zero functional gain.
- **Soft-dep on `django-filter` (`ImportError` branch on first `FilterSet` declaration).** Rejected: the dependency is already hard; a soft dependency adds a branch to test and a warning surface consumers who don't filter would still pay.
- **Accept either a package `FilterSet` or a `django_filters.FilterSet` at `Meta.filterset_class`.** Rejected: two consumer-facing surfaces for one wiring create ambiguity about which `check_*_permission` shape applies and which lazy-resolution mechanism runs. The single package `FilterSet` (a `BaseFilterSet` by inheritance) is the boundary class; consumers convert by parent-class swap.

## Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering

Spec text: [Decision 6][spec-027-d6].

### Justification

- Phase 2.5 is already the synchronization seam for Relay-Node injection; running the filter binding there keeps the finalizer's phase ordering coherent.
- Materializing classes as module globals (not dict entries in a separate registry) matches Strawberry's `LazyType.resolve_type`, which cannot reach a dict-keyed registry through `strawberry.lazy(...)`.
- Lazy `RelatedFilter` targets follow the record-now-resolve-at-finalization pattern the package uses for model relations, and an unresolved one fails loud with the same `Cannot finalize Django types: ...` [`ConfigurationError`][glossary-configurationerror] prefix the model-relation finalizer produces.
- Re-running is safe: `finalize_django_types()` is a no-op once `registry.is_finalized()`, and materialization is idempotent for the same `(name, input_class)` pair while a different class claiming a name raises per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- Partial-finalize lifecycle: if phase 2.5 raises mid-pass (e.g., an unresolved `RelatedFilter`), the registry is never marked finalized, the ledger keeps its partial state, and the next `finalize_django_types()` resumes. `registry.clear()` resets the ledger and leaves the materialized globals parked for replacement on the next finalize, so the fakeshop reload fixture (used by [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]) resets the filter subsystem in the same step.
- Binding is separated from expansion because expansion of one filterset can reach another's `filter_for_field`; binding every owner first makes the result independent of registry iteration order.

### Alternatives considered (and rejected)

- **Run filter binding in phase 2 alongside `_attach_relation_resolvers`.** Rejected: Relay-aware filters depend on the Relay-Node setup, which phase 2 runs before.
- **Run filter binding in a new phase 2.75.** Rejected: invents an extra phase number for one capability; the existing 2.5 is the right grain.
- **Run filter binding at `DjangoType.__init_subclass__` instead of at finalization.** Rejected: `RelatedFilter("CelestialBodyFilter")` cannot be resolved at class-creation time because the target filterset's module may not be imported yet — the same definition-order-independence constraint the package solves for model relations.
- **Inject a `filter:` argument into existing root resolvers' Strawberry field metadata after finalize.** Rejected: Strawberry collects field arguments at `@strawberry.type` decoration time; injection-after-collection would require monkey-patching Strawberry internals or invalidating already-decorated `Query` types. The shipped shape annotates the resolver with the [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper) helper at module-load time, so Strawberry collects the lazy reference naturally.

## Decision 7 — `Meta.filterset_class` promotion gate

Spec text: [Decision 7][spec-027-d7].

### Justification

- The cross-subsystem invariant in [`docs/GLOSSARY.md`][glossary] ("Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end") applies to every Layer-3 sidecar.
- Half-promoting (accepting the key but no-oping on it) is the worst of both: consumers cannot tell whether their filter declaration does anything.
- The promotion is one entry moving between the two frozensets in [`django_strawberry_framework/types/base.py`][base]; `_validate_meta` rejects deferred keys and any key in neither set.

### Alternatives considered (and rejected)

- **Promote `Meta.filterset_class` before the binding is wired.** Rejected: silently accepting a key whose effect doesn't exist is a maintenance hazard.
- **Keep the key deferred until `DjangoConnectionField` ships.** Rejected: the connection field is a second consumer; root-list resolvers call `FilterSet.apply_sync(...)` / `apply_async(...)` themselves (per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)), and the live HTTP coverage exercises that path.

## Decision 8 — Relation-permission cascade + `get_queryset` cooperation

Spec text: [Decision 8][spec-027-d8].

### Justification

- Visibility-before-filter is the security-correct ordering: filtering inside a queryset not yet scoped to the request's user would let a filter "see through" the visibility gate (compute `WHERE name LIKE '%admin%'` against rows the user shouldn't see). Step 3's nested visibility scoping extends this property to the related-filter join.
- Threading `info` through `apply_*` and into the nested `RelatedFilter` application is what lets the target's visibility hook scope the join's right-hand side. The optimizer's `Prefetch` downgrade covers OUTPUT visibility, but the parent-row restriction is already baked into the WHERE clause by then.
- The cookbook's `_apply_related_queryset_constraints` is the precedent for the related-filter `queryset=` constraint; the package ports its parent-scoping shape, narrowed to active branches.
- The explicit `form.is_valid()` call closes a real failure mode in `BaseFilterSet.qs` — without the explicit raise, a malformed filter input silently degrades instead of surfacing a `GraphQLError`.
- Optimizer cooperation is already documented in [Queryset diffing][glossary-queryset-diffing] — a `.filter(...)` call on the consumer queryset doesn't change the cooperation contract, because the optimizer reconciles against whatever queryset shape the resolver returns.

### Alternatives considered (and rejected)

- **Apply filters first, then `get_queryset`.** Rejected: security-incorrect ordering per the reasoning above.
- **Skip step 3 (nested visibility scoping)** and rely on the optimizer's `Prefetch` downgrade for related-row visibility. Rejected: the downgrade covers OUTPUT planning, not parent-row JOIN filtering — the queryset already exists in WHERE-clause form by the time the optimizer walks the selection tree.
- **Skip the active-branch refinement** (step 7) and apply every declared `RelatedFilter(queryset=...)` constraint unconditionally. Rejected: the unconditional behavior would exclude parent rows without a constrained child even for `filter: {}` or `filter: { name: { ... } }` — row loss the consumer never asked for.
- **Skip step 6 (`form.is_valid()`)** and let `BaseFilterSet.qs` consult `self.errors` as the cookbook does. Rejected: the cookbook's behavior silently degrades to "filter what we can clean, drop what we can't" — the wrong shape for a GraphQL surface that must return a structured error.
- **Let a nested clause escape the `RelatedFilter(queryset=...)` constraint.** Rejected: the constraint is the declared filter-scope boundary; a nested clause that could ignore it would make the declaration meaningless.

## Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle

Spec text: [Decision 9][spec-027-d9].

### Justification

- The `TypeRegistry` is the model-to-`DjangoType` mapping that powers [`Meta.primary`][glossary-metaprimary] / `registry.get(model)` / `registry.types_for(model)`; mixing string-keyed input-class entries into the same dict would weaken its type contract.
- The input-class names are stable and class-derived (`f"{FilterSet.__name__}InputType"`); two connection fields targeting the same model resolve to the same `FilterInputType` (Apollo cache friendly) without registry collision.
- Each set family owns its own namespace — [`OrderSet`][glossary-orderset] at `orders.inputs`, the planned [`AggregateSet`][glossary-aggregateset] likewise — so responsibilities stay scoped and each matches Strawberry's `LazyType.resolve_type` semantics; collapsing them into the `TypeRegistry` would put heterogeneous namespaces in one place.
- `Meta.primary`'s ambiguity rules (`primary_for(model)`, `types_for(model)`) are model-keyed; the input-class namespace is name-keyed; no read-time predicate from one needs to walk the other.
- The lifecycle clauses make a test that builds a `FilterSet`, finalizes, asserts, calls `registry.clear()`, and rebuilds with a different filterset shape behave correctly: the ledger reset forces re-materialization, and each parked global is replaced in place by the rebuilt class.

### Alternatives considered (and rejected)

- **A private sidecar `dict[str, type]` registry in `filters.inputs`.** Rejected: Strawberry's `LazyType.resolve_type` cannot reach into a dict; the registry must coincide with the module's global namespace.
- **Single shared `TypeRegistry` mapping both `model → DjangoType` and `name → input_class`.** Rejected: heterogeneous key types weaken the contract; sibling set families would make the same dict grow more axes; and Strawberry's lazy mechanism still requires module globals.
- **Per-`DjangoType` input-class namespace (attached to the definition).** Rejected: the per-module namespace is the natural shape and matches Strawberry's `strawberry.lazy("module-path")` lookup.
- **Per-app input-class namespace (Django-app-scoped).** Rejected: Strawberry schemas span Django apps; the namespace's scope is the Strawberry schema, not the Django app.
- **No clear contract — let test fixtures recover ad hoc.** Rejected: a partial-finalize failure plus a fakeshop schema reload would collide on an already-materialized name; the lifecycle clauses are what make rerun and reload deterministic.

## Decision 10 — Joint `0.0.8` cut

Spec text: [Decision 10][spec-027-d10].

### Justification

- Each feature card lands self-contained code, tests, and docs; the version string is a release action, not a feature-card change.
- Letting each card of a release cohort bump the version would make several bumps compete for one number.
- The release is single-sourced in `__version__`, so the maintainer's cut touches one literal.

### Alternatives considered (and rejected)

- **Each card bumps independently.** Rejected: the cards land in arbitrary order, so the version would point at whichever card happened to merge last — fragile and surprising.
- **Block all cohort cards on a single integration commit.** Rejected: cards lose independence; review surface balloons.

## Decision 11 — `filter_input_type(FilterSet)` consumer helper

Spec text: [Decision 11][spec-027-d11].

### Justification

- Without a helper, consumers would spell out `Annotated["GalaxyFilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` on every resolver — a long incantation that ties consumer code to the package's internal module path and bypasses the validation gate.
- A helper-returned `Annotated[...]` is the only consumer-facing shape that satisfies all three requirements: (a) it's a real Python annotation Strawberry collects at `@strawberry.type` time; (b) it defers resolution to schema-build time; (c) it points at a module Strawberry can import to resolve via `module.__dict__[name]`.
- Eager validation (`TypeError` at evaluation time for a non-`FilterSet`) catches misuse at the resolver-declaration site instead of letting Strawberry surface a more cryptic schema-build-time error.
- The `FilterInput[...]` spelling exists because a call is not a valid type expression: a type checker rejects `filter_input_type(MyFilter)` in an annotation but accepts the generic and enforces its `FilterSet` bound.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] reads `Meta.filterset_class` and builds its `filter:` argument with the same helper, so there is one annotation-building path.

### Alternatives considered (and rejected)

- **No helper; consumers spell out `Annotated[...]` themselves.** Rejected: ties consumer code to the package's internal module path; bypasses validation; not the package's `Meta`-driven shape.
- **Helper returns `<Name>FilterInputType` directly (a class).** Rejected: the class doesn't exist at module-load time — `finalize_django_types()` materializes it later. Returning a class at module-load time would force the helper to run the finalizer eagerly, contradicting the definition-order-independence contract.
- **Helper is a method on `FilterSet`: `GalaxyFilter.input_type()`.** Rejected: viable, but adds class-method surface to every `FilterSet` for one call site per resolver. The module-level form is the smaller import and the more discoverable doc entry.
- **No helper; only `DjangoConnectionField` exposes `filter:`.** Rejected: plain `@strawberry.field` resolvers need a working `filter:` argument independent of the connection field, and [Goals][spec-027-goals] item 5's REPL introspection presumes a consumer-facing path.

## Decision 12 — Live HTTP coverage strategy

Spec text: [Decision 12][spec-027-d12].

### Justification

- The live HTTP path exercises ORM cooperation, optimizer cooperation, and Relay GlobalID round-trips — three properties an in-process `schema.execute_sync(...)` test would miss without significant setup.
- The package-internal `tests/filters/` tree catches the edge cases (re-entry guard, error shapes, cache behavior) that a real query cannot reach without authoring filter classes that explicitly fail.

### Alternatives considered (and rejected)

- **Skip live HTTP coverage; cover everything via `tests/filters/`.** Rejected per [`AGENTS.md`][agents]'s live-HTTP-priority rule — any line a real GraphQL query against fakeshop reaches is covered over HTTP.
- **Cover everything via live HTTP; skip package-internal tests.** Rejected: re-entry, cache-behavior and error-surface paths are not reachable through normal consumer queries.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[goal-migration-shape]: ../../../GOAL.md#migration-shape
[goal]: ../../../GOAL.md
[pyproject]: ../../../pyproject.toml
[readme]: ../../../README.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-aggregateset]: ../../GLOSSARY.md#aggregateset
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-djangoconnectionfield]: ../../GLOSSARY.md#djangoconnectionfield
[glossary-metaprimary]: ../../GLOSSARY.md#metaprimary
[glossary-orderset]: ../../GLOSSARY.md#orderset
[glossary-queryset-diffing]: ../../GLOSSARY.md#queryset-diffing
[glossary]: ../../GLOSSARY.md

<!-- docs/SPECS/ -->
[next-step-8]: ../NEXT.md#step-8--archive-prior-specs-and-update-cross-references
[next]: ../NEXT.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-022]: ../spec-022-export_schema-0_0_7.md
[spec-023]: ../spec-023-multi_db-0_0_7.md
[spec-025]: ../spec-025-scalar_map_helper-0_0_7.md
[spec-027-d10]: ../spec-027-filters-0_0_8.md#decision-10--joint-008-cut
[spec-027-d11]: ../spec-027-filters-0_0_8.md#decision-11--filter_input_typefilterset-consumer-helper
[spec-027-d12]: ../spec-027-filters-0_0_8.md#decision-12--live-http-coverage-strategy
[spec-027-d1]: ../spec-027-filters-0_0_8.md#decision-1--spec-filename-and-canonical-naming
[spec-027-d2]: ../spec-027-filters-0_0_8.md#decision-2--subpackage-layout-and-public-export-surface
[spec-027-d3]: ../spec-027-filters-0_0_8.md#decision-3--six-layer-lazy-resolution-pipeline
[spec-027-d4]: ../spec-027-filters-0_0_8.md#decision-4--upstream-primitives-parity-floor
[spec-027-d5]: ../spec-027-filters-0_0_8.md#decision-5--django-filter-as-the-foundation
[spec-027-d6]: ../spec-027-filters-0_0_8.md#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering
[spec-027-d7]: ../spec-027-filters-0_0_8.md#decision-7--metafilterset_class-promotion-gate
[spec-027-d8]: ../spec-027-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation
[spec-027-d9]: ../spec-027-filters-0_0_8.md#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle
[spec-027-goals]: ../spec-027-filters-0_0_8.md#goals
[spec-027-non-goals]: ../spec-027-filters-0_0_8.md#non-goals
[spec-027]: ../spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../../django_strawberry_framework/types/base.py
[filters]: ../../../django_strawberry_framework/filters/

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-test-library]: ../../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
