# Spec: Filtering subsystem (`FilterSet`, `RelatedFilter`, `Meta.filterset_class`)

Target release: `0.0.8` (per [`KANBAN.md`][kanban] card `WIP-ALPHA-021-0.0.8`). The version bump from `0.0.7 → 0.0.8` is owned by the joint `0.0.8` cut, NOT this card — see [Decision 10](#decision-10--joint-008-cut).
Status: planned — no production code on disk yet; the only existing seam is the [`Meta.filterset_class`][glossary-metafilterset_class] entry in `DEFERRED_META_KEYS` at [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base], which this card promotes out of `DEFERRED_META_KEYS` into `ALLOWED_META_KEYS` once the subsystem applies the configured class end-to-end.
Owner: package maintainer.
Predecessors: [`docs/SPECS/spec-011-relay_interfaces-0_0_5.md`][spec-011] (Relay-Node wiring at finalizer phase 2.5 — the synchronization point this card reuses); [`docs/SPECS/spec-014-meta_primary-0_0_6.md`][spec-014] (the `Meta.primary` design and the [`TypeRegistry`][glossary-djangotype] keying convention this card respects when answering [Decision 9](#decision-9--input-type-namespace-vs-typeregistry)); [`docs/SPECS/spec-016-list_field-0_0_7.md`][spec-016] (Decision 10's "joint cut" precedent this card mirrors); [`docs/GLOSSARY.md`][glossary] entries [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], [`Meta.filterset_class`][glossary-metafilterset_class] (all currently `planned for 0.0.8`); [`KANBAN.md`][kanban] card body's "Recommended architectural direction" block (the six-layer lazy-resolution pipeline summary), preserved as [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) without re-litigation.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pins the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)), the subpackage layout ([Decision 2](#decision-2--subpackage-layout-and-public-export-surface)), the six-layer lazy-resolution pipeline imported verbatim from `django-graphene-filters` with Strawberry-adapted Layer 5 ([Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)), the upstream-primitives parity floor ([Decision 4](#decision-4--upstream-primitives-parity-floor)), the `django-filter` soft-dependency posture ([Decision 5](#decision-5--django-filter-soft-dependency-posture)), the finalizer-phase-2.5 wiring seam ([Decision 6](#decision-6--finalizer-phase-25-binding-seam)), the `Meta.filterset_class` promotion gate ([Decision 7](#decision-7--metafilterset_class-promotion-gate)), the relation-permission cascade composition with [`get_queryset`][glossary-get_queryset-visibility-hook] ([Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)), the input-type namespace question against the [`Meta.primary`][glossary-metaprimary] design ([Decision 9](#decision-9--input-type-namespace-vs-typeregistry)), the joint-`0.0.8`-cut posture ([Decision 10](#decision-10--joint-008-cut)), and the live-HTTP coverage strategy ([Decision 11](#decision-11--live-http-coverage-strategy)). Out of scope: ordering ([`OrderSet`][glossary-orderset]) — covered by sibling [`WIP-ALPHA-022-0.0.8`][kanban]; aggregation ([`AggregateSet`][glossary-aggregateset]) — `0.1.3`; [`DjangoConnectionField`][glossary-djangoconnectionfield] — `0.0.9`; permission cascade ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`; [Meta.search_fields][glossary-metasearch_fields] — `0.1.2`. Dependencies on these surfaces are forward-only: this card composes when they arrive without retrofit.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`FilterSet`][glossary-filterset] — the declarative filter class this card ships (`planned for 0.0.8`). Borrows the six-layer lazy-resolution architecture verbatim from `django-graphene-filters` per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline); Graphene's `graphene.InputObjectType` becomes `strawberry.input` and Graphene's `lambda:` forward references become `strawberry.lazy(...)`.
- [`RelatedFilter`][glossary-relatedfilter] — cross-relation filter traversal (`planned for 0.0.8`). Accepts a target `FilterSet` class, an absolute import path string, or an unqualified name for circular references; lazy-resolved at finalizer time.
- [`Meta.filterset_class`][glossary-metafilterset_class] — the consumer-facing key (`planned for 0.0.8`) that points a [`DjangoType`][glossary-djangotype] at its `FilterSet`. Promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` per [Decision 7](#decision-7--metafilterset_class-promotion-gate).
- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type this card extends with a filter sidecar. The `Meta`-driven shape is what makes `Meta.filterset_class = ItemFilter` legible to a Django audience.
- [`finalize_django_types`][glossary-finalize_django_types] — the synchronization point where the filter subsystem's lazy-resolution pipeline runs (phase 2.5, the same seam [`Meta.interfaces = (relay.Node,)`][glossary-metainterfaces] uses).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the optimizer this card composes with. Filter clauses applied to a queryset must not break the optimizer's [Queryset diffing][glossary-queryset-diffing] cooperation; covered by [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation) and a live HTTP test.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — pre-filter visibility scoping. Composes with filter `check_*_permission` gates ([Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)).
- [`OrderSet`][glossary-orderset] — sibling [`WIP-ALPHA-022-0.0.8`][kanban] subsystem. Mentioned only as the second consumer of the same lazy-resolution architecture this card ships; out of scope here.
- [`AggregateSet`][glossary-aggregateset] / [`get_child_queryset`][glossary-get_child_queryset] / [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — future Layer-3 sidecars referenced as the forward composition surface; not implemented here.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — `0.0.9`; the consumer-facing surface that threads `filter:` arguments through. The factory machinery this card ships is the input it will consume, so the `0.0.8` deliverable is the back-end half of the `0.0.9` connection field's filter surface.
- [`Meta.primary`][glossary-metaprimary] — the multi-`DjangoType`-per-model design from `0.0.6` whose `TypeRegistry` keying convention this card respects per [Decision 9](#decision-9--input-type-namespace-vs-typeregistry).
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation and finalization time for unknown filter target classes, invalid lookup names, circular references that exhaust the resolution guard, etc. — see [Edge cases](#edge-cases-and-constraints).
- [`Meta.search_fields`][glossary-metasearch_fields] — the search-input surface ([planned for `0.1.2`][glossary-metasearch_fields]); the `LOOKUP_PREFIXES` map (`^` / `=` / `@` / `$`) ported verbatim from `django-graphene-filters` lives in the filter subsystem because `construct_search` belongs in the filter pipeline.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule at [`AGENTS.md`][agents] #"package tests live under" (package tests under `tests/filters/` with `__init__.py` shells; example-project non-HTTP tests under `examples/fakeshop/tests/`; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority rule at [`AGENTS.md`][agents] #"any coverage line achievable via a real GraphQL query"; the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; the settings-keys rule at [`AGENTS.md`][agents] #"Add settings keys only when the feature that needs them lands"; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — [Slice 5](#slice-checklist) grants the explicit permission for this card.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical per [Decision 11](#decision-11--live-http-coverage-strategy).
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 5; the card body's `docs/spec-filters.md` reference predates the structured `spec-<NNN>-<topic>-<0_0_X>.md` convention and gets rewritten in the same Slice-5 sweep per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
- [`docs/TREE.md`][tree] — tests mirror source one-to-one. The subsystem lives at [`django_strawberry_framework/filters/`][filters] per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface); the mirror partner is `tests/filters/` (new tree). The [target package layout][tree] section in `docs/TREE.md` already names the directory; this card flips it from `[alpha]` to on-disk.
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers).

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Six slices total.

- [ ] Slice 1: Foundation — module layout + `Filter` primitives + `FilterSet` metaclass
  - [ ] Create [`django_strawberry_framework/filters/`][filters] subpackage with `__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface). Module-level docstrings on each file pin the responsibility (`base.py` = `Filter` / `RelatedFilter` / primitives; `sets.py` = `FilterSet` + metaclass; `factories.py` = `FilterArgumentsFactory` + `get_filterset_class` + `_dynamic_filterset_cache`; `inputs.py` = generated input-type registry + input-data adapters).
  - [ ] `base.py` ships the five verified upstream primitives per [Decision 4](#decision-4--upstream-primitives-parity-floor): `Filter` (base), `TypedFilter`, `ArrayFilter` + `ArrayFilterMethod`, `RangeFilter` + `RangeField` + `validate_range`, `ListFilter` + `ListFilterMethod`, `GlobalIDFilter` + `GlobalIDMultipleChoiceFilter`. Each is a port of the matching `graphene_django/filter/filters/*.py` primitive (sourced from `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/filters/`); the port is library-agnostic where possible and Strawberry-adapted only at the input-type-construction boundary.
  - [ ] `base.py` also ships `RelatedFilter` (the `BaseRelatedFilter` port from `django_graphene_filters/filters.py::BaseRelatedFilter`) and `LazyRelatedClassMixin` (port from `django_graphene_filters/mixins.py::LazyRelatedClassMixin`) — Layers 1 + 2 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline).
  - [ ] `sets.py` ships `FilterSetMetaclass` (port from `django_graphene_filters/filterset.py::FilterSetMetaclass`) and `FilterSet` (port from `django_graphene_filters/filterset.py::AdvancedFilterSet`, with `get_filters` doing Layer-4 cycle-safe expansion) — Layers 3 + 4 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline). `FilterSet` accepts `Meta.model`, `Meta.fields` (dict form `{"name": ["exact", "icontains"]}` or `"__all__"`), and per-field `check_<field>_permission` hooks.
  - [ ] `inputs.py` ships the generated-input-type registry per [Decision 9](#decision-9--input-type-namespace-vs-typeregistry) — a per-package `dict[str, type]` keyed by stable class-derived names (e.g., `"GalaxyFilterInputType"`); it is NOT the same surface as `django_strawberry_framework.registry.registry` (the model-to-`DjangoType` registry). The two registries do not collide because their key types are disjoint (Django model class vs string input-type name).
- [ ] Slice 2: Factories — `FilterArgumentsFactory` BFS + dynamic-filterset cache
  - [ ] `factories.py` ships `FilterArgumentsFactory` (port from `django_graphene_filters/filter_arguments_factory.py::FilterArgumentsFactory`) — Layer 5 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline). BFS walk that builds every reachable `strawberry.input` type; `_build_class_type` emits `@strawberry.input`-decorated classes via `strawberry_django_framework.filters.inputs.build_input_class(name, field_specs)` (the Strawberry-adapted analogue of Graphene's `type(name, (graphene.InputObjectType,), fields)`).
  - [ ] `factories.py` ships `get_filterset_class` (port from `django_graphene_filters/filterset_factories.py::get_filterset_class`, NOT the same-named `graphene_django/filter/utils.py::get_filterset_class` — the spec pins this distinction in [Decision 4](#decision-4--upstream-primitives-parity-floor)) plus `_dynamic_filterset_cache` (Layer 6) keyed by `(model, fields, extra_meta)`. The cache prevents duplicate-`__name__` collisions when two connection fields target the same model without declaring an explicit `filterset_class`.
  - [ ] `factories.py` ships `FILTER_DEFAULTS` (the FK/PK → `GlobalIDFilter` mapping; the Strawberry-adapted analogue of `graphene_django/filter/filterset.py::GrapheneFilterSetMixin.FILTER_DEFAULTS`). Required for Relay-aware filtering against `relay.Node`-shaped types shipped in `DONE-011-0.0.5`.
  - [ ] `inputs.py` ships the input-data adapter functions: `_build_logic_fields` (`and` / `or` / `not` self-references via `strawberry.lazy(...)`), `_build_input_fields` (target-filterset references via `strawberry.lazy(...)`), and `construct_search` (the `LOOKUP_PREFIXES` map — `^` → `istartswith`, `=` → `iexact`, `@` → `search`, `$` → `iregex` — ported verbatim).
- [ ] Slice 3: Wiring — `Meta.filterset_class` promotion + finalizer phase 2.5 binding
  - [ ] [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] grows a `filterset_class: type | None = None` field. The slot is populated by `DjangoType.__init_subclass__` from `Meta.filterset_class` once the key is promoted out of `DEFERRED_META_KEYS`.
  - [ ] [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] drops `"filterset_class"`. [`ALLOWED_META_KEYS`][base] grows `"filterset_class"`. The `_validate_meta` function validates the supplied class is a `FilterSet` subclass and raises [`ConfigurationError`][glossary-configurationerror] otherwise.
  - [ ] [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] grows a per-type filter-binding pass in phase 2.5 (immediately after `apply_interfaces` / `install_relay_node_resolvers` and before phase 3's `strawberry.type` decoration). For each `DjangoType` whose `definition.filterset_class is not None`: validate, call `filterset_cls.get_filters()` to trigger Layer-4 expansion, call `FilterArgumentsFactory(filterset_cls).arguments` to trigger Layer-5 BFS, and register the resulting input types in the per-package input-type registry. The two new operations are idempotent; calling `finalize_django_types()` twice is still a no-op via the existing `registry.is_finalized()` guard.
- [ ] Slice 4: Live HTTP coverage in fakeshop
  - [ ] [`examples/fakeshop/apps/library/`][fakeshop-library] grows `filters.py` containing `BranchFilter`, `BookFilter`, `LoanFilter`, `PatronFilter` (selected because the library app already exercises forward / reverse / M2M relations live per [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]; the filter classes mirror that relation shape with `RelatedFilter("BookFilter")` / `RelatedFilter("BranchFilter")` references that exercise both same-module and cross-module lazy resolution).
  - [ ] [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] grows `Meta.filterset_class = filters.BranchFilter` (etc.) on the corresponding `DjangoType` classes. Sibling library root-list resolvers (`all_library_branches`, `all_library_books`, etc.) accept a `filter:` argument that threads through `BranchFilter.filter_queryset(...)` (or equivalent) before returning the queryset — the same shape `DjangoConnectionField` will reuse in `0.0.9`.
  - [ ] [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows 6–8 new live `/graphql/` HTTP tests: scalar-field filter (`name: { iContains: "..." }`), choice-enum filter (`circulationStatus: { exact: AVAILABLE }`), forward-FK filter (`shelf: { id: { exact: "<gid>" } }`), reverse-FK filter (`shelves: { code: { iContains: "..." } }`), M2M filter (`genres: { name: { exact: "..." } }`), logical-and / logical-or filter combinations, optimizer cooperation (filtered queryset still receives `select_related` / `prefetch_related` for nested selections — pinned by `assertNumQueries(N)`).
- [ ] Slice 5: Docs + KANBAN + CHANGELOG
  - [ ] [`docs/GLOSSARY.md`][glossary]: flip [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] from `planned for 0.0.8` to `shipped (0.0.8)`. Update the [Index][glossary-index] table's status column for each. Update the [Public exports][glossary-public-exports] list to add `FilterSet` and `RelatedFilter` after `DjangoType` (matching the `__all__` sort).
  - [ ] [`docs/README.md`][docs-readme]: add `FilterSet` / `Meta.filterset_class` / `RelatedFilter` to the "Coming in `0.1.0`" → graduate to "Shipped today (`0.0.8`)" once the version bump lands in the joint cut.
  - [ ] [`docs/TREE.md`][tree]: flip the `filters/` subpackage entry from `[alpha]` to on-disk (move from the "target package layout" section to the "current on-disk layout" section). List the five new files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); list the mirrored `tests/filters/` tree.
  - [ ] [`README.md`][readme]: add `FilterSet` / `RelatedFilter` to the shipped-symbol bullet list (under the `0.0.8` boundary), matching the joint-cut promotion timing.
  - [ ] [`GOAL.md`][goal]: the astronomy showcase already references `filters.py` and `Meta.filterset_class` in its `1.0.0` shape. No edit needed — the showcase was always forward-looking and now describes what shipped.
  - [ ] [`TODAY.md`][today]: extend the "Shipped capabilities" enumeration with `FilterSet` / `Meta.filterset_class` / `RelatedFilter`; extend the fakeshop section to mention the new live `BranchFilter` / `BookFilter` / `LoanFilter` / `PatronFilter` declarations and the filter-input live HTTP tests under [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library].
  - [ ] [`KANBAN.md`][kanban]: move `WIP-ALPHA-021-0.0.8` to the Done column with the next available `DONE-NNN-0.0.8` id (renumber per the column-move pass). Past-tense Done body pinned in [Doc updates](#doc-updates). Rewrite the card body's `Definition of done` bullet 1 (`docs/spec-filters.md` → `docs/SPECS/spec-021-filters-0_0_8.md` after the Step-8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)).
  - [ ] [`CHANGELOG.md`][changelog]: append `### Added` bullets to `[Unreleased]` for `FilterSet`, `RelatedFilter`, `Meta.filterset_class`, the per-package input-type registry, the `FILTER_DEFAULTS` map, and the cross-relation lazy-resolution surface. Append a `### Changed` bullet noting that `Meta.filterset_class` is no longer in `DEFERRED_META_KEYS`. Per the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed", this Slice-5 bullet is the explicit permission for this card.
  - [ ] Version bump: NOT in this card per [Decision 10](#decision-10--joint-008-cut). `[Unreleased]` entries accumulate against an unbumped `__version__ = "0.0.7"` until the last card in the `0.0.8` cohort owns the bump to `0.0.8`.
- [ ] Slice 6: Sibling-card composition smoke tests (held until after [`WIP-ALPHA-022-0.0.8`][kanban] ships)
  - [ ] One in-process test under [`tests/filters/test_composition.py`][test-filters-composition] (new) that constructs a `DjangoType` with BOTH `Meta.filterset_class` AND `Meta.orderset_class` set, calls `finalize_django_types()`, and asserts both factories' input types are reachable from the schema. The test is held until [`WIP-ALPHA-022-0.0.8`][kanban] (ordering) ships its `OrderSet` / `Meta.orderset_class` so this card's spec body can name the composition contract without writing the sibling-card test prematurely. If [`WIP-ALPHA-022-0.0.8`][kanban] ships first, the test lands as a slice-back-edit to this card's PR; if this card ships first, the composition test lands in the ordering card's PR and this card's Slice 6 is closed as "carried by sibling".

## Problem statement

`django-strawberry-framework`'s `0.0.7` surface ships a model-backed Strawberry type ([`DjangoType`][glossary-djangotype]), the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], the non-Relay [`DjangoListField`][glossary-djangolistfield], and the [Schema export management command][glossary-schema-export-management-command] — but consumers cannot filter the returned querysets through the GraphQL surface today. The package's `0.0.7` audience (Django teams migrating from `graphene-django` or `strawberry-graphql-django`) reaches for `Meta.filterset_class = ItemFilter` the moment they wire up a real schema, and the package's response is a [`ConfigurationError`][glossary-configurationerror] from [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] ("`Meta keys not supported yet: ['filterset_class']`").

Filtering is the first ⚛️&🍓 parity-required Layer-3 capability for two reasons:

1. **Audience expectation.** Both upstreams (`graphene-django` via `DjangoFilterConnectionField`+`filterset_class`, and `strawberry-graphql-django` via `@strawberry_django.filter_type(Model)`) ship a filter surface in their core API. A Django GraphQL package without filters is not a credible alternative to either; the gap shows up in the first ten minutes of schema authoring.
2. **Foundation for other Layer-3 work.** Sibling [`OrderSet`][glossary-orderset] ([`WIP-ALPHA-022-0.0.8`][kanban]) reuses the same lazy-resolution architecture; [`AggregateSet`][glossary-aggregateset] reuses it again at `0.1.3`; [Meta.search_fields][glossary-metasearch_fields] reuses the `LOOKUP_PREFIXES` map; the eventual [`DjangoConnectionField`][glossary-djangoconnectionfield] (`0.0.9`) consumes the `FilterArgumentsFactory` output as the connection's `filter:` argument source. Shipping filters first establishes the lazy-resolution pattern the next four cards reuse without redesign.

`django-graphene-filters` (the working reference per [`START.md`][start] "Working reference") has already solved the hard part — a cycle-safe six-layer lazy-resolution pipeline that handles circular `RelatedFilter` references across modules. Five of six layers are library-agnostic Python and port verbatim; only Layer 5 (the cycle-safe forward reference in the GraphQL schema build) needs Strawberry adaptation. The card body's "Recommended architectural direction" block pre-pins this answer; the spec preserves it as [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) without re-litigation, and the rest of the work is mechanical: port the five reusable layers, adapt Layer 5 to `strawberry.lazy(...)`, wire the binding into the finalizer's phase 2.5, and promote `Meta.filterset_class` once the end-to-end path is live.

## Current state

- [`django_strawberry_framework/filters/`][filters]: does not exist. [`docs/TREE.md`][tree]'s "target package layout" section already names the directory and the four planned files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); this card flips the entry from `[alpha]` to on-disk.
- [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base]: contains `"filterset_class"` (plus four sibling Layer-3 keys: `"orderset_class"`, `"aggregate_class"`, `"fields_class"`, `"search_fields"`). The validator at `_validate_meta` raises [`ConfigurationError`][glossary-configurationerror] when any of these is declared.
- [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition]: does not carry a `filterset_class` slot. Forward-reserved slots for the four sibling Layer-3 keys are also absent (the dataclass is intentionally minimal — slots land with the feature).
- [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer]: runs three phases (1, 2, 2.5, 3); phase 2.5 currently handles only `apply_interfaces` and `install_relay_node_resolvers`. The phase is the seam this card grows a fourth step into per [Decision 6](#decision-6--finalizer-phase-25-binding-seam).
- [`docs/GLOSSARY.md`][glossary]: [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] all carry `planned for 0.0.8` status today.
- [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]: exercises forward / reverse FK, forward / reverse OneToOne, forward / reverse M2M, choice-enum generation, `Meta.interfaces = (relay.Node,)` on `GenreType`, `Meta.optimizer_hints` on `LoanType`, and consumer-shaped querysets that cooperate with the optimizer. No filter declarations today; the schema is the natural host for the live HTTP filter coverage per [Decision 11](#decision-11--live-http-coverage-strategy).
- [`docs/SPECS/spec-016-list_field-0_0_7.md`][spec-016]: the most-recently-shipped spec; the canonical voice / depth / section-layout reference for this spec.
- Upstream cookbook (working reference per [`START.md`][start]): `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/` — the six-layer pipeline this card ports verbatim through Layers 1–4 and 6, and Strawberry-adapts at Layer 5.
- Upstream `graphene-django`: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/` — the parity-floor primitives this card mirrors (per [Decision 4](#decision-4--upstream-primitives-parity-floor)). Note: `graphene_django/filter/utils.py::get_filterset_class` and the cookbook's `filterset_factories.py::get_filterset_class` are different functions with the same name; this card mirrors the cookbook's shape per [Decision 4](#decision-4--upstream-primitives-parity-floor).
- Upstream `strawberry-graphql-django`: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py` — the single-file decorator-driven implementation. The runtime pipeline (`process_filters`) is conceptually parallel to this card's `FilterSet.filter_queryset(...)`; the declaration surface (`@strawberry_django.filter_type(Model, lookups=True)` vs `class ItemFilter(FilterSet): class Meta: model = Item`) differs per the package's DRF-shaped positioning.

## Goals

1. Ship `FilterSet` + `RelatedFilter` + per-field `check_*_permission` gates + cross-relation traversal with cycle-safe lazy resolution, mirroring the `django-graphene-filters` six-layer pipeline minus Layer 5's GraphQL-engine substitution.
2. Promote [`Meta.filterset_class`][glossary-metafilterset_class] out of `DEFERRED_META_KEYS` only when the filter subsystem applies the configured class end-to-end — same gate as [`Meta.interfaces`][glossary-metainterfaces] in `DONE-011-0.0.5`.
3. Establish the registration / factory / lazy-resolution pattern the four sibling Layer-3 subsystems ([`OrderSet`][glossary-orderset], [`AggregateSet`][glossary-aggregateset], [`FieldSet`][glossary-fieldset], [Meta.search_fields][glossary-metasearch_fields]) reuse without redesign.
4. Stay composable with [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Queryset diffing][glossary-queryset-diffing] / [Plan cache][glossary-plan-cache] / [FK-id elision][glossary-fk-id-elision] / [Strictness mode][glossary-strictness-mode] — a filter clause is just another `.filter(...)` call on the consumer queryset; the optimizer cooperates.
5. Expose enough introspection (`FilterSet.get_filters()`, `FilterArgumentsFactory(cls).arguments`) for a maintainer to ask "what filter surface does this type support?" from the REPL in one call.
6. Earn package coverage through live fakeshop HTTP flows per [Decision 11](#decision-11--live-http-coverage-strategy); the package coverage gate (`fail_under = 100`) is reached because the live HTTP tests exercise the package end-to-end.

## Non-goals

- **Ordering / aggregation / fieldsets / permissions cascade.** Each ships in its own card. Composition with this card is forward-only; no Layer-3 sibling is implemented here.
- **`DjangoConnectionField` integration.** The `0.0.9` connection field consumes the factory machinery this card ships; the connection-field surface itself is out of scope.
- **`django-filter` plug-in compatibility.** `django-graphene-filters` `GrapheneFilterSetMixin` subclasses `django_filters.BaseFilterSet`; this card's `FilterSet` does NOT inherit from `django_filters.BaseFilterSet` because the cookbook's `AdvancedFilterSet` already has a self-contained `get_filters()` / lazy-resolution machinery and the soft-dep adds review surface for no benefit. See [Decision 5](#decision-5--django-filter-soft-dependency-posture).
- **A `Meta.filterset_class = MyDjangoFilter` shape that accepts a plain `django_filters.FilterSet`.** Rejected: the consumer-facing `FilterSet` is the package's own class so the lookup-validation / lazy-related-class / permission-gate surface is uniform; consumers who want their existing `django_filters.FilterSet` to compose can wrap it in a one-line `class MyAdapter(FilterSet): ...` subclass.
- **Replacing the optimizer's queryset-diffing contract.** Filters land as `.filter(...)` calls before the optimizer walks the selection tree; the existing cooperation contract is untouched.
- **Auto-generation of `FilterSet` from `Meta.fields` without declaring an explicit class.** Deferred; the dynamic-factory machinery (Layer 6) exists for the connection-field path where the connection field can pre-declare `model=Item, fields="__all__"` without a sibling `FilterSet` class. Direct consumer-facing implicit generation lands when [`DjangoConnectionField`][glossary-djangoconnectionfield] ships in `0.0.9`.
- **The version bump.** Owned by the last `0.0.8` card to ship per [Decision 10](#decision-10--joint-008-cut).

## Borrowing posture

Filtering is the most heavily-borrowed surface in the package. The architectural answer is pre-pinned by the [`KANBAN.md`][kanban] card body's "Recommended architectural direction" block; this spec preserves it without re-litigation.

### From `django-graphene-filters` — borrow heavily (the cookbook is the working reference)

Local source path: `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/`. Per [`START.md`][start] ("Working reference") this cookbook is the package's canonical Layer-3 reference; the goal is to recreate "what the package enables for the schema author," not to port Graphene internals. Five of the six lazy-resolution layers are library-agnostic Python and port verbatim:

- `filters.py::BaseRelatedFilter` → `django_strawberry_framework.filters.base::RelatedFilter` (Layer 1).
- `mixins.py::LazyRelatedClassMixin` → `django_strawberry_framework.filters.base::LazyRelatedClassMixin` (Layer 2).
- `filterset.py::FilterSetMetaclass` → `django_strawberry_framework.filters.sets::FilterSetMetaclass` (Layer 3).
- `filterset.py::AdvancedFilterSet.get_filters` → `django_strawberry_framework.filters.sets::FilterSet.get_filters` (Layer 4, with the same `__dict__["_expanded_filters"]` cache and `__dict__["_is_expanding_filters"]` recursion guard).
- `filterset.py::AdvancedFilterSet._apply_related_queryset_constraints` → port verbatim — the explicit `queryset=` boundary that nested filters cannot escape.
- `filterset.py::AdvancedFilterSet.check_permissions` → port verbatim — recursion through `RelatedFilter`s into child filtersets' `check_*_permission` methods.
- `filter_arguments_factory.py::FilterArgumentsFactory.filterset_to_trees` / `try_add_sequence` / `sequence_to_tree` → port verbatim — per-lookup tree-building algorithm.
- `filterset_factories.py::_dynamic_filterset_cache` → port verbatim — Layer 6, the memoized `(model, fields, extra_meta)` cache.
- `LOOKUP_PREFIXES` map for `construct_search` (`^` → `istartswith`, `=` → `iexact`, `@` → `search`, `$` → `iregex`) → port verbatim.
- Recursion-protected `_get_fields` (with `visited: set[type]`) → port verbatim.

### From `graphene-django` — borrow the user-facing primitives only

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/`. The cookbook builds on `graphene-django`'s filter primitives; the package needs the same parity floor per [Decision 4](#decision-4--upstream-primitives-parity-floor):

- `filters/array_filter.py::ArrayFilter`, `ArrayFilterMethod`.
- `filters/range_filter.py::RangeFilter`, `RangeField`, `validate_range`.
- `filters/list_filter.py::ListFilter`, `ListFilterMethod`.
- `filters/typed_filter.py::TypedFilter` (base class for the four above).
- `filters/global_id_filter.py::GlobalIDFilter`, `GlobalIDMultipleChoiceFilter` (required for Relay-aware filtering against `relay.Node`-shaped types).
- `filter/filterset.py::GrapheneFilterSetMixin.FILTER_DEFAULTS` (FK/PK → `GlobalIDFilter`) — the source of this card's `FILTER_DEFAULTS` mapping under [Decision 4](#decision-4--upstream-primitives-parity-floor).

### From `strawberry-graphql-django` — borrow the runtime-pipeline pattern (not the surface)

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py`. The upstream's single-file decorator-driven implementation is conceptually parallel at the runtime layer (`process_filters` compiles input values into queryset arguments) but the declaration surface diverges per the package's DRF-shaped positioning. Borrow the runtime contract loosely; don't borrow the decorator-on-input-type surface:

- `filters.py::FilterLookup` — the generic typed lookup descriptor (`exact`, `i_exact`, `contains`, ...) is conceptually similar to this card's lookup-pair generation but the Strawberry adaptation lands differently because the cookbook's BFS factory drives the lookup expansion.
- `filters.py::process_filters` — the runtime side of the filter pipeline. This card's `FilterSet.filter_queryset(input, queryset, info)` is the equivalent symbol; the runtime contract is "compile input value into queryset args" in both cases.
- `filters.py::FILTERS_ARG` (`= "filters"`) — module-level constant for the GraphQL argument name. This card's equivalent is `FILTER_ARG = "filter"` (singular per the cookbook's convention; the upstream's plural form is a documented difference).
- `filters.py::filter_type` decorator — NOT borrowed (the package's `Meta`-driven surface forbids decorator-on-input-type per [`START.md`][start] "Style they care about").
- `filters.py #"def __getattr__"` legacy `filter` alias with `DeprecationWarning` — NOT borrowed; the package's first-ship surface does not need a legacy alias.

### Explicitly do not borrow

- **Graphene's `lambda: target_input_type` cycle-safe forward references.** Replaced by `strawberry.lazy("django_strawberry_framework.filters.inputs._registry.{TargetFilterSet}InputType")` at Layer 5 (per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)). The two are conceptual twins — both defer the type reference until schema walk — but the Strawberry idiom is `strawberry.lazy(...)` / `Annotated[..., strawberry.lazy(...)]`, not raw lambdas.
- **`graphene-django`'s `setup_filterset` wrapper-avoidance.** Strawberry's eager annotation resolution does not have the "Graphene{X}Filter" wrapping problem that motivated this in the reference; the wrapper is dropped.
- **`graphene-django`'s `replace_csv_filters`.** Strawberry's typed input handles `list[T]` natively without comma-separated-string workarounds; the function is dropped.
- **`@strawberry_django.filter_type(Model, lookups=True)` decorator surface.** The package's `Meta`-driven shape per [`START.md`][start] "Meta classes everywhere on consumer surfaces" forbids decorator-on-input-type for consumer-facing classes.
- **A `django_filters.FilterSet` subclass path.** Per [Decision 5](#decision-5--django-filter-soft-dependency-posture), the package's `FilterSet` is self-contained; consumers who want their existing `django_filters.FilterSet` to compose write a one-line adapter subclass.

## User-facing API

The shipped consumer surface adds three new symbols re-exported from `django_strawberry_framework.filters` — `FilterSet`, `RelatedFilter`, and (internally registered) the per-package input-type registry. The [`Meta.filterset_class`][glossary-metafilterset_class] hook is the consumer-facing wiring on the existing [`DjangoType`][glossary-djangotype] surface.

### Default usage — declaring a `FilterSet`

```python
from django_strawberry_framework.filters import FilterSet, RelatedFilter

from . import models


class GalaxyFilter(FilterSet):
    # Reverse FK — referenced lazily by string so Galaxy and CelestialBody
    # filtersets can live in the same file without an import cycle.
    celestial_bodies = RelatedFilter("CelestialBodyFilter", field_name="celestial_bodies")

    class Meta:
        model = models.Galaxy
        fields = {
            "name": "__all__",
            "description": ["exact", "icontains"],
        }


class CelestialBodyFilter(FilterSet):
    # Explicit queryset acts as a security/scope boundary: nested filters can
    # narrow it but cannot escape "public galaxies only".
    galaxy = RelatedFilter(
        GalaxyFilter,
        field_name="galaxy",
        queryset=models.Galaxy.objects.filter(is_private=False),
    )

    class Meta:
        model = models.CelestialBody
        fields = {
            "name": ["exact", "icontains"],
            "body_type": ["exact", "in"],
            "galaxy__name": ["exact"],
        }
```

### Wiring into a `DjangoType`

```python
from django_strawberry_framework import DjangoType

from . import filters, models


class GalaxyType(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = "__all__"
        filterset_class = filters.GalaxyFilter
```

`Meta.filterset_class` is the only wiring required at the `DjangoType` site. The finalizer-phase-2.5 binding (per [Decision 6](#decision-6--finalizer-phase-25-binding-seam)) takes care of input-type generation, lazy-related-filter resolution, and registry registration.

### Per-field permission gates

```python
from graphql import GraphQLError


class GalaxyFilter(FilterSet):
    class Meta:
        model = models.Galaxy
        fields = {"name": "__all__", "description": ["exact", "icontains"]}

    def check_name_permission(self, request):
        """Only staff users may filter by Galaxy.name."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Galaxy name.")
```

The framework calls `check_<field>_permission(request)` before applying the corresponding filter; a `GraphQLError` raised inside the gate surfaces as an `errors` entry on the response.

### Logical-and / logical-or / logical-not

The factory auto-generates the three logical-operator fields on every `<TypeName>FilterInputType`. Consumer-facing GraphQL shape:

```graphql
{
  allGalaxies(filter: {
    and: [
      { name: { iContains: "andromeda" } }
      { not: { isPrivate: { exact: true } } }
    ]
  }) {
    id
    name
  }
}
```

The self-referential nature of the input type (`and: list[<TypeName>FilterInputType]`) is handled by Layer 5's Strawberry-adapted forward reference per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline).

### Error shapes

- `Meta.filterset_class = <non-FilterSet-class>` → [`ConfigurationError`][glossary-configurationerror]("`Meta.filterset_class` must be a `FilterSet` subclass; got `<class>`") at type creation.
- `RelatedFilter("UnknownFilter")` where `"UnknownFilter"` cannot be resolved by Layer 2's module-fallback → [`ConfigurationError`][glossary-configurationerror]("Cannot finalize ... no registered FilterSet named `'UnknownFilter'`") at finalization.
- Cycle-safe expansion exhausts the recursion guard (Layer 4's `_is_expanding_filters` re-entry detection) → [`ConfigurationError`][glossary-configurationerror]("Cycle detected in `FilterSet` related-filter graph; offending class: `<class>`") at finalization.
- `Meta.fields = {"unknown_field": ["exact"]}` where `"unknown_field"` is not a model field → [`ConfigurationError`][glossary-configurationerror]("`<FilterSet>.Meta.fields` references unknown model field: `'unknown_field'`") at type creation.
- `Meta.fields = {"name": ["unsupported_lookup"]}` where the lookup is not registered for the field type → [`ConfigurationError`][glossary-configurationerror]("Lookup `'unsupported_lookup'` not supported for field `'name'` on model `<Model>`") at type creation.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-021-filters-0_0_8.md`** (this document), NOT `docs/spec-filters.md` as the [`KANBAN.md`][kanban] card body's `Definition of done` bullet 1 names it.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 and observed by every recent spec ([`docs/SPECS/spec-014-meta_primary-0_0_6.md`][spec-014], [`docs/SPECS/spec-015-consumer_overrides_scalar-0_0_6.md`][spec-015], [`docs/SPECS/spec-016-list_field-0_0_7.md`][spec-016], [`docs/SPECS/spec-017-apps-0_0_7.md`][spec-017], [`docs/SPECS/spec-018-export_schema-0_0_7.md`][spec-018], [`docs/SPECS/spec-019-multi_db-0_0_7.md`][spec-019], [`docs/SPECS/spec-020-scalar_map_helper-0_0_7.md`][spec-020]) bakes the card's NNN and target patch into the filename.
- The card body's `docs/spec-filters.md` predates that convention.
- The Slice-5 [`KANBAN.md`][kanban] rewrite updates the card body's stale reference to the canonical name, so the cross-reference resolves after archival per [Step 8 of NEXT.md][next-step-8].
- Active-vs-archived path lifecycle (mirroring [`docs/SPECS/spec-020-scalar_map_helper-0_0_7.md`][spec-020] Decision 1): references use whichever path the file actually has when the reference is written. While this spec is at `docs/spec-021-filters-0_0_8.md`, references use that path; after a future archive pass moves it under `docs/SPECS/`, references use the archived path.

Alternatives considered (and rejected):

- **Honor the card body verbatim with `docs/spec-filters.md`.** Rejected: breaks the structured-filename convention and would land an unnumbered spec next to a numbered cohort.
- **Longer topic slug `filtering_subsystem`.** Rejected: `filters` already names the architectural intent and matches the [`django_strawberry_framework/filters/`][filters] subpackage name.

### Decision 2 — Subpackage layout and public export surface

The filter subsystem ships as a subpackage at **[`django_strawberry_framework/filters/`][filters]** (NOT a flat single-file module). Five files:

- `__init__.py` — re-exports `FilterSet`, `RelatedFilter`, and (for advanced uses) `Filter`, `TypedFilter`, `ArrayFilter`, `RangeFilter`, `ListFilter`, `GlobalIDFilter`.
- `base.py` — `Filter`, `TypedFilter`, `ArrayFilter`, `RangeFilter`, `RangeField`, `validate_range`, `ListFilter`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, `RelatedFilter`, `LazyRelatedClassMixin`.
- `sets.py` — `FilterSetMetaclass`, `FilterSet` (with `Meta.model`, `Meta.fields`, `get_filters`, `filter_queryset`, `check_permissions`, `_apply_related_queryset_constraints`).
- `factories.py` — `FilterArgumentsFactory`, `get_filterset_class`, `_dynamic_filterset_cache`, `FILTER_DEFAULTS`.
- `inputs.py` — per-package input-type registry, `build_input_class`, `_build_logic_fields`, `_build_input_fields`, `construct_search`, `LOOKUP_PREFIXES`.

Public re-export from `django_strawberry_framework` is opted-in by the subpackage's `__init__.py`, NOT by the top-level package: consumers `from django_strawberry_framework.filters import FilterSet, RelatedFilter` (matching the import shape in [`GOAL.md`][goal]'s astronomy showcase). The top-level package's `__all__` is unchanged in `0.0.8` — adding `FilterSet` / `RelatedFilter` to the top-level surface widens it for every consumer including those who never use filters; the subpackage import path is the right grain.

Justification:

- The subsystem's surface is large enough (~10 public primitives + 6 internal symbols) that a flat module would be awkward to read; the upstream cookbook ships ~12 files under `django_graphene_filters/`, the package collapses to five by combining filter-class primitives into `base.py`.
- The target package layout in [`docs/TREE.md`][tree] already names the directory; this card flips it from `[alpha]` to on-disk without renaming.
- The mirror partner is `tests/filters/` (new tree) — five files mirroring source one-to-one (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`, plus `__init__.py` shell).
- Subpackage-scoped re-export (instead of top-level package re-export) matches how `OrderSet` will land at `django_strawberry_framework/orders/__init__.py` and how `AggregateSet` will land at `django_strawberry_framework/aggregates/__init__.py`. The five sibling Layer-3 subpackages line up cleanly without each one bloating the top-level `__all__`.

Alternatives considered (and rejected):

- **Flat `django_strawberry_framework/filters.py` single-file module.** Rejected: the surface is too large; review legibility suffers; the upstream cookbook's `~12-file` layout indicates the right grain.
- **Top-level public re-export (`from django_strawberry_framework import FilterSet`).** Rejected: the surface is opt-in for consumers who actually use filters; widening the top-level `__all__` for every consumer (including the optimizer-only ones) creates churn and a longer Index in `docs/GLOSSARY.md`.
- **Splitting `base.py` into per-primitive files (`array_filter.py`, `range_filter.py`, etc.) mirroring `graphene-django`'s layout.** Rejected: the primitives are short (~50 lines each); five-file layout in the upstream is a `graphene-django` artifact, not a design choice the package needs to mirror.

### Decision 3 — Six-layer lazy-resolution pipeline

The pre-pinned architectural answer (from the [`KANBAN.md`][kanban] card body's "Recommended architectural direction" block) is borrowed verbatim and preserved here without re-litigation. Five of six layers port from `django-graphene-filters` library-agnostic; only Layer 5 is Strawberry-adapted.

**Layer 1 — Lazy class references in `RelatedFilter`** — port verbatim from `django_graphene_filters/filters.py::BaseRelatedFilter`. `RelatedFilter` accepts target as class, absolute import path string (`"myapp.filters.ManagerFilter"`), or unqualified name (`"ManagerFilter"`). `_filterset` stores it unresolved; the `.filterset` property triggers resolution.

**Layer 2 — Module-fallback resolution** — port verbatim from `django_graphene_filters/mixins.py::LazyRelatedClassMixin.resolve_lazy_class`. Two-step resolution: try as absolute path via `django.utils.module_loading.import_string`; on `ImportError`, retry with `bound_class.__module__` prefix. Handles circular-import scenarios in the same module.

**Layer 3 — Metaclass discovery, deferred expansion** — port pattern from `django_graphene_filters/filterset.py::FilterSetMetaclass`. Metaclass collects `BaseRelatedFilter` declarations into `cls.related_filters`, calls `f.bind_filterset(new_class)` so the module-fallback resolver knows the owning module, and **does not** expand. Expansion is deferred to `get_filters()`.

**Layer 4 — Cycle-safe expansion + cache** — port verbatim from `django_graphene_filters/filterset.py::AdvancedFilterSet.get_filters`. `cls.__dict__["_expanded_filters"]` cache plus `cls.__dict__["_is_expanding_filters"]` recursion guard. Two-condition cache write: `"related_filters" in cls.__dict__` AND no string `_filterset` remaining on any related filter. Breaks `A → B → A` cycles cleanly.

**Layer 5 — BFS schema build with deferred references (Strawberry-adapted)** — port the BFS algorithm in `django_graphene_filters/filter_arguments_factory.py::FilterArgumentsFactory._ensure_built` verbatim; only the cycle-safe forward reference changes. Graphene's `graphene.InputField(lambda tn=target_name: input_object_types[tn])` becomes one of two Strawberry idioms (Layer-5 implementation decides which at write time, but both are documented twins of the Graphene lambda):

1. `strawberry.lazy("django_strawberry_framework.filters.inputs._registry.{TargetFilterSet}InputType")` — direct lazy reference resolved at schema-walk time.
2. `Annotated[<base>, strawberry.lazy(...)]` annotation — used when the input class needs the lazy reference as an annotation on a generated field.

The `lambda:` and `strawberry.lazy()` are exact conceptual twins; both defer the type reference until schema walk.

**Layer 6 — Memoized dynamic FilterSet generation** — port verbatim from `django_graphene_filters/filterset_factories.py::_dynamic_filterset_cache`. Cache keyed by `(model, fields, extra_meta)` for connection fields declared without an explicit `filterset_class`; prevents duplicate-`__name__` collisions when two connection fields target the same model. (This card lands the cache plumbing; the connection-field consumer is `0.0.9`.)

Justification:

- The cookbook's six-layer architecture is proven (the working reference per [`START.md`][start]); reinventing it would burn schedule for no architectural gain.
- Five of six layers are library-agnostic Python — the port is mechanical, not creative.
- Layer 5's Strawberry-adapted forward reference is the only point where engineering judgment enters; the two candidate idioms (`strawberry.lazy("...path...")` and `Annotated[..., strawberry.lazy(...)]`) are both documented Strawberry shapes that defer the type reference until schema walk; either is correct.
- The card body's "Recommended architectural direction" block pre-pins this answer; the spec preserves it rather than re-litigating.

Alternatives considered (and rejected):

- **Design a new lazy-resolution mechanism from scratch.** Rejected: zero benefit over the cookbook's proven architecture; doubles the review surface.
- **Skip Layer 6 (no dynamic-factory plumbing).** Rejected: when [`DjangoConnectionField`][glossary-djangoconnectionfield] lands in `0.0.9`, it would need the cache regardless; lifting it here is cheaper than retrofitting later.
- **Use `typing.ForwardRef` instead of `strawberry.lazy(...)`.** Rejected: Strawberry's documented forward-reference idiom IS `strawberry.lazy(...)`; reaching past Strawberry's API to `typing.ForwardRef` would build on private behavior.

### Decision 4 — Upstream-primitives parity floor

The package ships parity equivalents for every verified upstream filter primitive named in the [`KANBAN.md`][kanban] card body:

- `ArrayFilter(TypedFilter)`, `ArrayFilterMethod(FilterMethod)` (from `graphene_django/filter/filters/array_filter.py`).
- `RangeFilter(TypedFilter)`, `RangeField(Field)`, `validate_range` (from `graphene_django/filter/filters/range_filter.py`).
- `ListFilter(TypedFilter)`, `ListFilterMethod(FilterMethod)` (from `graphene_django/filter/filters/list_filter.py`).
- `TypedFilter(Filter)` (from `graphene_django/filter/filters/typed_filter.py`) — base class for the four above.
- `GlobalIDFilter(Filter)`, `GlobalIDMultipleChoiceFilter(MultipleChoiceFilter)` (from `graphene_django/filter/filters/global_id_filter.py`).

The `FILTER_DEFAULTS` map (FK/PK → `GlobalIDFilter`) ships at [`django_strawberry_framework.filters.factories::FILTER_DEFAULTS`][filters] per the Strawberry-adapted variant of `graphene_django/filter/filterset.py::GrapheneFilterSetMixin.FILTER_DEFAULTS`. Required for Relay-aware filtering against `relay.Node`-shaped types shipped in `DONE-011-0.0.5`.

**Name-collision note:** `graphene_django/filter/utils.py::get_filterset_class` and `django_graphene_filters/filterset_factories.py::get_filterset_class` are different functions with the same name. The card body's "Verified upstream factory machinery" section flags this; this card mirrors the cookbook's shape (the `BaseFilterSet`-aware get-or-create helper), NOT graphene-django's shape (the explicit-vs-dynamic dispatcher). Reason: the cookbook's `get_filterset_class` is the entry point the BFS factory uses; graphene-django's is a different shape pinned to connection-field declaration. We need the cookbook's, the connection field needs neither in `0.0.8`.

Justification:

- ⚛️ parity (the package's positioning claim) requires shipping equivalents for each parity-floor primitive; absence in the first ship is the kind of gap that bites consumers immediately.
- Each primitive is short (~30–80 lines); the cost of porting all five plus `FILTER_DEFAULTS` is much smaller than the cost of explaining why the package is missing one.

Alternatives considered (and rejected):

- **Ship only `GlobalIDFilter` in `0.0.8`; defer the four `TypedFilter` subclasses.** Rejected: half-shipping the parity floor invites the same churn as not shipping at all; consumers hit the gap immediately.
- **Ship the parity floor under different symbol names (e.g., `DSTArrayFilter`).** Rejected: the upstream naming is the consumer's mental model; renaming for no architectural gain creates friction.

### Decision 5 — `django-filter` soft-dependency posture

The package's `FilterSet` does NOT subclass `django_filters.BaseFilterSet`. The soft-dep on `django-filter` is dropped; the cookbook's `AdvancedFilterSet` is self-contained at the `get_filters()` / lazy-resolution layer, and inheriting from `django_filters.BaseFilterSet` would add review surface, an `ImportWarning` branch, and a soft-dep optional install for no consumer benefit.

Justification:

- The cookbook's `AdvancedFilterSet` already implements its own `get_filters()` cycle-safe expansion; it inherits from `django_filters.BaseFilterSet` to reuse `django-filter`'s `Meta.fields` parsing and per-field lookup-method machinery — both of which this card can re-port library-agnostically without the soft-dep.
- `graphene_django/filter/__init__.py` issues an `ImportWarning` when `DJANGO_FILTER_INSTALLED` is false; the same shape in this package would surface a warning every import time for consumers who declared `Meta.filterset_class` without `django-filter` installed. Skipping the soft-dep removes the warning surface entirely.
- The "use my existing `django_filters.FilterSet`" use case is served by a one-line adapter subclass; the package's `FilterSet` is the boundary class, not a wholesale replacement.

Alternatives considered (and rejected):

- **Inherit from `django_filters.BaseFilterSet` and soft-dep on `django-filter`.** Rejected: adds review surface and a warning branch for the consumer who doesn't have `django-filter` installed; the cookbook's `Meta.fields` parsing ports cleanly without the inheritance.
- **Accept either a package-`FilterSet` or a `django_filters.FilterSet` at `Meta.filterset_class`.** Rejected: two consumer-facing surfaces for the same wiring create ambiguity about which check_*_permission shape applies; the package's `FilterSet` is one boundary class.
- **Soft-dep on `django-filter` for runtime `process_filters` cooperation but not for class inheritance.** Rejected: `process_filters` doesn't need `django-filter` to function — the queryset translation is `queryset.filter(<lookup_key>=<value>)` regardless.

### Decision 6 — Finalizer phase-2.5 binding seam

The filter subsystem's lazy-resolution pipeline runs inside [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer]'s phase 2.5, immediately after the existing `apply_interfaces` / `install_relay_node_resolvers` loop and before phase 3's `strawberry.type` decoration. For each `DjangoType` with `definition.filterset_class is not None`:

1. Validate `filterset_class` is a `FilterSet` subclass (raise [`ConfigurationError`][glossary-configurationerror] otherwise).
2. Call `filterset_cls.get_filters()` to trigger Layer-4 expansion (resolves lazy refs, expands related filters with cycle guards).
3. Call `FilterArgumentsFactory(filterset_cls).arguments` to trigger Layer-5 BFS (builds every reachable `strawberry.input` type).
4. Register the resulting input types in the per-package input-type registry (per [Decision 9](#decision-9--input-type-namespace-vs-typeregistry)).

By phase 3, when `strawberry.type(cls, ...)` runs on the `DjangoType`, every referenced filter input type already exists.

Justification:

- Phase 2.5 is already the synchronization seam for `DONE-011-0.0.5`'s Relay-Node injection; threading the filter binding through the same loop keeps the finalizer's phase ordering coherent.
- Running before phase 3's `strawberry.type` decoration means the `DjangoType` sees the registered input types at decoration time — no second-pass needed.
- The pending-relation registry's record-now-resolve-at-finalization pattern (used for model relations) reuses cleanly for lazy related-filter class references; the `LazyRelatedClassMixin` equivalent reuses the same fail-loud error format ("Cannot finalize ... no registered ...") that the model-relation finalizer already produces.
- Calling `finalize_django_types()` twice is still a no-op via the existing `registry.is_finalized()` guard; the new filter-binding pass is idempotent because the per-type `if definition.finalized: continue` short-circuit at the head of phase 3's loop already skips already-decorated types on a rerun.

Alternatives considered (and rejected):

- **Run filter binding in phase 2 alongside `_attach_relation_resolvers`.** Rejected: filter binding depends on Relay-Node setup (because Relay-aware filters require the `GlobalIDFilter` mapping established in `0.0.5`); phase 2 runs before Relay setup, so binding would land in the wrong order.
- **Run filter binding in a new phase 2.75.** Rejected: invents an extra phase number for one capability; the existing 2.5 is the right grain.
- **Run filter binding at `DjangoType.__init_subclass__` instead of at finalization.** Rejected: `RelatedFilter("CelestialBodyFilter")` cannot be resolved at class-creation time because the target filterset's module may not have been imported yet — same definition-order-independence constraint that `DONE-009-0.0.4` solved for model relations.

### Decision 7 — `Meta.filterset_class` promotion gate

`Meta.filterset_class` is promoted out of [`DEFERRED_META_KEYS`][base] only when:

1. The filter subsystem's class hierarchy is on disk (Slices 1 + 2).
2. The finalizer-phase-2.5 binding pass is wired (Slice 3).
3. The promotion to `ALLOWED_META_KEYS` is applied at the same commit as the validator-acceptance test (Slice 3).

Same gate as [`Meta.interfaces`][glossary-metainterfaces] in `DONE-011-0.0.5` — a deferred `Meta` key is accepted only when the subsystem applies it end-to-end. A consumer who declares `Meta.filterset_class = ItemFilter` against a `0.0.8`-installed package gets a working filter surface; against `0.0.7` they get the existing [`ConfigurationError`][glossary-configurationerror] from [`DEFERRED_META_KEYS`][base].

Justification:

- Cross-subsystem invariant pinned in [`docs/GLOSSARY.md`][glossary] ("Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end. This rule resolves entirely at `1.0.0`."); applies to every Layer-3 sidecar.
- Half-promoting (accepting the key but no-oping on it) is the worst-of-both: consumers cannot tell whether their filter declaration is doing anything; debug surface is hidden.
- The promotion is a one-line change at [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] (`"filterset_class"` moves to `ALLOWED_META_KEYS`); the validator at `_validate_meta` already gates on `ALLOWED_META_KEYS | DEFERRED_META_KEYS`.

Alternatives considered (and rejected):

- **Promote `Meta.filterset_class` early in Slice 1 before binding is wired.** Rejected: silently accepting a key whose effect doesn't exist is a maintenance hazard.
- **Keep the key in `DEFERRED_META_KEYS` until `DjangoConnectionField` ships in `0.0.9`.** Rejected: the connection field is the second consumer; root-list resolvers can apply `FilterSet.filter_queryset(...)` themselves in the meantime, and the live HTTP coverage in Slice 4 exercises that path.

### Decision 8 — Relation-permission cascade + `get_queryset` cooperation

A `FilterSet`'s `check_<field>_permission(request)` gate composes with the target type's [`get_queryset`][glossary-get_queryset-visibility-hook] hook and with `RelatedFilter`'s `_apply_related_queryset_constraints` (the explicit `queryset=` parameter on a related filter that nested filters cannot bypass). The composition order is:

1. `DjangoType.get_queryset(queryset, info)` runs first on the consumer-shaped root queryset — visibility scoping happens before any filter clauses.
2. `FilterSet.check_permissions(input, request)` runs — denial gates raise `GraphQLError` before any filter clause touches the queryset.
3. `FilterSet.filter_queryset(input, queryset, info)` applies the validated filter clauses, calling `.filter(...)` / `.exclude(...)` on the already-visibility-scoped queryset.
4. For each `RelatedFilter` in `input`, the related queryset is bounded by the `queryset=` parameter (if declared) BEFORE the child filterset's clauses apply.
5. The optimizer ([`DjangoOptimizerExtension`][glossary-djangooptimizerextension]) walks the selection tree on the post-filter queryset; [Queryset diffing][glossary-queryset-diffing] cooperates with any consumer `select_related` / `prefetch_related` work already present.

Forward composition contract: when [`apply_cascade_permissions`][glossary-apply_cascade_permissions] ships in `0.0.10`, it slots into step 1 (the `get_queryset` hook); when [Per-field permission hooks][glossary-per-field-permission-hooks] ship, they slot into the field-resolver layer that runs AFTER step 5 (queryset traversal completes before field resolvers fire). The five layers compose without retrofit.

Justification:

- Visibility-before-filter is the security-correct ordering: filtering inside a queryset that hasn't been scoped to the request's user would let a nested filter "see through" the visibility gate (compute `WHERE name LIKE '%admin%'` against rows the user shouldn't see).
- The cookbook's `_apply_related_queryset_constraints` is the precedent for the related-filter `queryset=` boundary; this card ports it verbatim.
- The optimizer cooperation is already documented in [Queryset diffing][glossary-queryset-diffing] — a `.filter(...)` call on the consumer queryset doesn't change the cooperation contract because the optimizer reconciles against whatever queryset shape the resolver returns.

Alternatives considered (and rejected):

- **Apply filters first, then `get_queryset`.** Rejected: security-incorrect ordering per the reasoning above.
- **Skip step 4 (let nested filters override the `queryset=` boundary).** Rejected: defeats the cookbook's documented security feature; the boundary's whole point is to be inviolable.

### Decision 9 — Input-type namespace vs `TypeRegistry`

The card body's "Decide whether the input-type factory's namespace shares the `TypeRegistry` or has its own" question is answered: **the input-type namespace is its own per-package registry, separate from the `TypeRegistry`** at [`django_strawberry_framework.registry.registry`][registry] (the model-to-`DjangoType` registry from [`Meta.primary`][glossary-metaprimary]).

Implementation: a per-package `dict[str, type]` at [`django_strawberry_framework.filters.inputs::_input_type_registry`][filters] (module-level), keyed by stable class-derived names (e.g., `"GalaxyFilterInputType"`). The two registries do not collide because their key types are disjoint (Django model class vs string input-type name).

Justification:

- The `TypeRegistry` is the model-to-`DjangoType` mapping that powers [`Meta.primary`][glossary-metaprimary] / `registry.get(model)` / `registry.types_for(model)`; mixing string-keyed input-type entries into the same dict would weaken the type contract.
- The input-type names are stable and class-derived (e.g., `f"{FilterSet.__name__}InputType"`); two connection fields targeting the same model resolve to the same `FilterInputType` (Apollo cache friendly) without registry collision.
- Sibling Layer-3 subsystems (`OrderSet` for `[`WIP-ALPHA-022-0.0.8`][kanban], `AggregateSet` for `0.1.3`) need their own per-subsystem input-type registries; collapsing them into the `TypeRegistry` would put four heterogeneous namespaces in one place. Per-subsystem keeps responsibilities scoped.
- `Meta.primary`'s ambiguity rules (`primary_for(model)`, `types_for(model)`) are model-keyed; the input-type registry is name-keyed; no read-time predicate from one registry needs to walk the other.

Alternatives considered (and rejected):

- **Single shared `TypeRegistry` mapping both `model → DjangoType` and `name → input_type_class`.** Rejected: heterogeneous key types weaken the contract; sibling Layer-3 subsystems would force the same dict to grow more axes.
- **Per-`DjangoType` input-type registry (attached as `definition.filter_input_types`).** Rejected: connection fields with `_dynamic_filterset_cache`-generated filtersets don't have a stable `DjangoType` to attach to; the per-package registry is the natural shape.
- **Per-app input-type registry (Django-app-scoped).** Rejected: Strawberry schemas span Django apps; the registry's scope is the Strawberry schema, not the Django app.

### Decision 10 — Joint `0.0.8` cut

`0.0.8` ships three WIP cards as a bundle: `WIP-ALPHA-021-0.0.8` (this card — filtering), `WIP-ALPHA-022-0.0.8` (ordering), and `WIP-ALPHA-023-0.0.8` (`DjangoType` consumer-DX cleanup pass). The version bump in `pyproject.toml #"version ="`, `django_strawberry_framework/__init__.py #"__version__ ="`, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

Justification:

- Each individual card lands self-contained code, tests, and docs.
- The version bump is the joint cut-over signal; doing it on each card would cause three overlapping bumps competing for `0.0.8`.
- The CHANGELOG `[Unreleased]` Added / Changed entries accumulate across the three cards' Slice 5s; the last card to ship promotes `[Unreleased]` to `[0.0.8]` and bumps `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s pinned version assertion in one atomic commit.
- Precedent: [`docs/SPECS/spec-016-list_field-0_0_7.md`][spec-016] Decision 10 pinned the same posture for the `0.0.7` five-card cohort, and [`docs/SPECS/spec-020-scalar_map_helper-0_0_7.md`][spec-020] Decision 8 pinned the same posture post-cut.

The Definition of done item that previously said "version bump in `pyproject.toml`" for this card is REMOVED from this slice and deferred to the last `0.0.8` card to ship.

Alternatives considered (and rejected):

- **Each card bumps independently.** Rejected: the three cards' commits would land in arbitrary order, and the version bump would point at whichever card happened to merge last — fragile and surprising.
- **Block all three cards on a single integration commit.** Rejected: cards lose independence; review surface balloons.

### Decision 11 — Live HTTP coverage strategy

Package coverage is earned through fakeshop live `/graphql/` HTTP flows where practical per the [`docs/TREE.md`][tree] coverage-priority rule ("Any package coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against fakeshop MUST be earned in `examples/fakeshop/test_query/`").

Live HTTP tests (Slice 4) land in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] and cover: scalar-field filter clauses, choice-enum filter clauses, forward-FK filter clauses, reverse-FK filter clauses, M2M filter clauses, logical-and / logical-or / logical-not combinations, optimizer cooperation (`assertNumQueries(N)` against a filtered queryset with nested selection), and the `_apply_related_queryset_constraints` security boundary.

Package-internal tests (`tests/filters/`) land in five mirror files (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`, plus `__init__.py` shell). Each file covers what the live HTTP path cannot easily reach: cycle-safe expansion via `_is_expanding_filters` recursion guard, `_dynamic_filterset_cache` hit/miss behavior, `LazyRelatedClassMixin.resolve_lazy_class` two-step resolution failure paths, `FILTER_DEFAULTS` FK/PK → `GlobalIDFilter` mapping, `LOOKUP_PREFIXES` map for `construct_search`, [`ConfigurationError`][glossary-configurationerror] surface for invalid `Meta.fields`, etc.

Justification:

- The live HTTP path exercises the most ORM cooperation, optimizer cooperation, and Relay GlobalID round-trip behavior — three properties that an in-process `schema.execute_sync(...)` test would miss without significant setup.
- The package-internal `tests/filters/` tree catches the edge cases (cycle detection, error shapes, cache behavior) that the live HTTP path cannot reach without authoring filter classes that explicitly fail.
- The combination matches the precedent set by [`docs/SPECS/spec-016-list_field-0_0_7.md`][spec-016] Decision 9 (live HTTP coverage via sibling root field; package-internal tests for validation surface).

Alternatives considered (and rejected):

- **Skip live HTTP coverage; cover everything via `tests/filters/`.** Rejected per the [`docs/TREE.md`][tree] coverage-priority rule — live HTTP is the canonical coverage path for anything achievable via a real GraphQL query.
- **Cover everything via live HTTP; skip package-internal tests.** Rejected: cycle-detection / cache-behavior / error-surface paths are not reachable through normal consumer GraphQL queries; the package-internal tests are the right grain.

## Implementation plan

The card ships as **six slices** aligned with the [Slice checklist](#slice-checklist). Slices 1–5 each map to one commit; Slice 6 is held until the sibling [`WIP-ALPHA-022-0.0.8`][kanban] (ordering) ships. The per-commit breakdown exists for review legibility; squashing Slices 1–5 into a single PR is acceptable given the cohesive scope.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Foundation (`base.py` + `sets.py` skeleton) | [`django_strawberry_framework/filters/__init__.py`][filters], [`django_strawberry_framework/filters/base.py`][filters], [`django_strawberry_framework/filters/sets.py`][filters], [`django_strawberry_framework/filters/inputs.py`][filters] (skeletons), [`tests/filters/__init__.py`][test-filters] (new), [`tests/filters/test_base.py`][test-filters] (new), [`tests/filters/test_sets.py`][test-filters] (new) | ~25 (filter-primitive shapes, `RelatedFilter` accepts class/string/unqualified, `FilterSet` rejects unknown `Meta.fields` etc.) | `+850 / -0` |
| 2 — Factories (`factories.py` BFS + dynamic cache + inputs adapters) | [`django_strawberry_framework/filters/factories.py`][filters] (new), [`django_strawberry_framework/filters/inputs.py`][filters] (extend), [`tests/filters/test_factories.py`][test-filters] (new), [`tests/filters/test_inputs.py`][test-filters] (new) | ~20 (`FilterArgumentsFactory` BFS, `_dynamic_filterset_cache` hit/miss, `FILTER_DEFAULTS` map, `LOOKUP_PREFIXES` map, logical-and/or/not field generation) | `+650 / -0` |
| 3 — Wiring (`Meta.filterset_class` promotion + finalizer phase-2.5 binding) | [`django_strawberry_framework/types/base.py`][base] (`DEFERRED_META_KEYS` → `ALLOWED_META_KEYS` move + validation), [`django_strawberry_framework/types/definition.py`][definition] (add `filterset_class` slot), [`django_strawberry_framework/types/finalizer.py`][finalizer] (phase 2.5 grows the filter-binding pass), [`tests/types/test_base.py`][test-types] (validator extension), [`tests/types/test_definition_order.py`][test-types] (extend), `tests/filters/test_finalizer.py` (new) | ~12 (validator accepts/rejects, phase-2.5 binding runs, idempotent rerun, lazy-related-filter resolution at finalize) | `+220 / -5` |
| 4 — Live HTTP coverage in fakeshop | [`examples/fakeshop/apps/library/filters.py`][fakeshop-library] (new), [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (extend with `Meta.filterset_class` + `filter:` argument plumbing on root resolvers), [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (extend) | 6–8 (scalar / choice-enum / forward-FK / reverse-FK / M2M / logical / optimizer cooperation / related-queryset boundary) | `+200 / -10` |
| 5 — Docs + KANBAN + CHANGELOG | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`README.md`][readme], [`TODAY.md`][today], [`KANBAN.md`][kanban], [`CHANGELOG.md`][changelog] | 0 | `+80 / -25` |
| 6 — Composition smoke test with sibling ordering card | [`tests/filters/test_composition.py`][test-filters-composition] (new, held until [`WIP-ALPHA-022-0.0.8`][kanban] ships) | 1 (composition with `OrderSet`) | `+30 / -0` |

Total expected delta (Slices 1–5): ~2000 lines across five slices.

The five slices must be authored in order. Slice 2 depends on Slice 1 (the factories consume the `FilterSet` metaclass and the `RelatedFilter` primitive); Slice 3 depends on Slice 2 (the finalizer-phase-2.5 binding calls `FilterArgumentsFactory(...)`); Slice 4 depends on Slice 3 (the fakeshop live HTTP coverage threads through the promoted `Meta.filterset_class`); Slice 5 depends on Slice 4 (the docs reference the live HTTP coverage as the canonical "what this looks like" example).

## Edge cases and constraints

- **Same-module `RelatedFilter` references** (e.g., `GalaxyFilter` and `CelestialBodyFilter` declared in the same `filters.py` with `RelatedFilter("CelestialBodyFilter")` and `RelatedFilter(GalaxyFilter)` respectively). The Layer-2 module-fallback resolution handles this; the absolute-path lookup fails (the module isn't fully loaded yet) and the `bound_class.__module__` retry succeeds.
- **Cross-module `RelatedFilter` references via absolute path** (e.g., `RelatedFilter("apps.products.filters.CategoryFilter")`). The Layer-2 absolute-path lookup succeeds; the `bound_class.__module__` retry is never reached.
- **Circular `RelatedFilter` cycles** (`A → B → A`). The Layer-4 `_is_expanding_filters` recursion guard breaks the cycle; the cache writes only when no string `_filterset` remains on any related filter (the two-condition guard). A genuine cycle exhausts the guard and raises [`ConfigurationError`][glossary-configurationerror] with the offending class named.
- **`Meta.fields = "__all__"`** (the shorthand). Expands to every model field reachable per Django's `Meta.get_fields()`; relation fields become `RelatedFilter` references with default lookups, scalar fields become per-lookup filters.
- **`Meta.fields = {"galaxy__name": ["exact"]}`** (the double-underscore lookup-path shorthand). Renders as a flat input field with the same lookup behavior as the cookbook's nested-input — the package preserves the cookbook's choice not to expand the path into nested input types at the GraphQL level.
- **`Meta.filterset_class = AdminGalaxyFilter` on a secondary `Meta.primary = False` `DjangoType`**. Per [`Meta.primary`][glossary-metaprimary], the secondary type is registered and reverse-discoverable; the filter binding runs on the secondary type's definition exactly the same way it runs on the primary's. The input-type namespace per [Decision 9](#decision-9--input-type-namespace-vs-typeregistry) is name-keyed so two `DjangoType`s on the same model with different `filterset_class`es generate two distinct input types.
- **`Meta.filterset_class` on a `DjangoType` that also declares `Meta.interfaces = (relay.Node,)`**. The filter binding runs at phase 2.5 after the Relay-Node injection; the `GlobalIDFilter` mapping in `FILTER_DEFAULTS` covers the Relay-aware filtering case.
- **Filter on a field that is NOT in the `DjangoType`'s `Meta.fields`** (e.g., the type exposes `name` but the filterset declares `description` as filterable). The filter clause still applies to the queryset; the consumer can filter on columns they cannot select. This matches the cookbook's behavior and is intentional.
- **Filter that raises a Django ORM error at queryset-translation time** (e.g., a JSON-field filter against a SQLite backend that doesn't support the lookup). The Django `FieldError` / `NotImplementedError` propagates as a `GraphQLError`; the framework does not pre-validate the SQL backend's supported lookups.
- **Recursion-protected `_get_fields`**. When a `FilterSet`'s `Meta.fields` references a relation that loops back to itself (e.g., `RelatedFilter("Self")` for a self-referential model), the `visited: set[type]` guard breaks the loop; the expanded fields stop at one level of self-reference.
- **`construct_search` lookup-prefix handling**. `^foo` becomes `<field>__istartswith=foo`, `=foo` becomes `<field>__iexact=foo`, `@foo` becomes `<field>__search=foo` (PostgreSQL full-text only), `$foo` becomes `<field>__iregex=foo`. The map ports verbatim from `django_graphene_filters`; consumers writing the `^`/`=`/`@`/`$` prefixes get the same behavior they did in the cookbook.
- **`Meta.fields` with no lookups** (e.g., `{"name": []}`). Rejected at type creation with [`ConfigurationError`][glossary-configurationerror]; an empty lookup list is meaningless.
- **Filter input position empty** (`filter: {}`). The factory returns the unfiltered queryset; no `.filter(...)` call is made. The optimizer's [Queryset diffing][glossary-queryset-diffing] cooperation is unaffected.
- **Async resolver returning a filtered queryset**. Strawberry's async path awaits the resolver; the queryset's filter clauses apply normally. The optimizer's async-path support (shipped in `0.0.2`) cooperates without retrofit.
- **`Meta.fields` referencing a model property (not a field)**. Rejected at type creation with [`ConfigurationError`][glossary-configurationerror]; only model fields are filterable. Filtering on a property requires a custom `Filter` declaration with an explicit `method=` (the cookbook's `FilterMethod` shape, ported per [Decision 4](#decision-4--upstream-primitives-parity-floor)).
- **Filter against a queryset that's already been `.values(...)`-projected**. Filters apply; the projection persists. The framework does not pre-validate; the consumer is responsible for the projection vs filter cooperation.
- **Two consumer schemas with two `<TypeName>FilterInputType`s of the same string name**. Rejected by the per-package input-type registry's name uniqueness check; the second registration raises [`ConfigurationError`][glossary-configurationerror] with the offending name. This catches consumers who accidentally declare two `FilterSet`s with the same `__name__` across different modules.

## Test plan

Tests live in two trees, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement is mandatory.

### `tests/filters/` (new tree)

Package tests; system-under-test is `django_strawberry_framework` itself. Five files mirror the source layout one-to-one per the [`docs/TREE.md`][tree] mirror rule:

- [`tests/filters/__init__.py`][test-filters] — empty `__init__.py` shell so pytest collects under `tests.filters.<module>` matching the existing `tests/types/__init__.py` / `tests/optimizer/__init__.py` convention.
- [`tests/filters/test_base.py`][test-filters] — covers `Filter` / `TypedFilter` / `ArrayFilter` / `RangeFilter` / `ListFilter` / `GlobalIDFilter` / `RelatedFilter` / `LazyRelatedClassMixin`. Tests: primitives reject invalid `method=`; `RangeField.validate_range` accepts valid pairs; `RelatedFilter` accepts class / absolute path / unqualified name forms; `LazyRelatedClassMixin.resolve_lazy_class` tries absolute then bound-module-prefixed; failed resolution raises [`ConfigurationError`][glossary-configurationerror] with the offending name.
- [`tests/filters/test_sets.py`][test-filters] — covers `FilterSetMetaclass` + `FilterSet`. Tests: metaclass collects `RelatedFilter` declarations into `cls.related_filters`; metaclass calls `bind_filterset`; `get_filters()` triggers Layer-4 expansion; expansion cache writes only when no string `_filterset` remains; `_is_expanding_filters` breaks cycles; `_apply_related_queryset_constraints` is honored by nested filters; `check_permissions` recurses through `RelatedFilter`s; unknown `Meta.fields` raises [`ConfigurationError`][glossary-configurationerror]; unknown lookups raise [`ConfigurationError`][glossary-configurationerror].
- [`tests/filters/test_factories.py`][test-filters] — covers `FilterArgumentsFactory` + `get_filterset_class` + `_dynamic_filterset_cache` + `FILTER_DEFAULTS`. Tests: BFS visits every reachable filterset; cycle-safe forward reference resolves via `strawberry.lazy(...)`; cache hits keyed by `(model, fields, extra_meta)`; cache misses build a new filterset; `FILTER_DEFAULTS` maps FK / PK to `GlobalIDFilter` correctly; per-package input-type registry registers under stable class-derived names; two connection fields on the same model share an input type.
- [`tests/filters/test_inputs.py`][test-filters] — covers `_build_logic_fields` + `_build_input_fields` + `construct_search` + `LOOKUP_PREFIXES`. Tests: `and` / `or` / `not` fields use `strawberry.lazy(...)` self-reference; input-field forward references resolve at schema walk; `construct_search` translates `^foo` / `=foo` / `@foo` / `$foo` prefixes correctly; `LOOKUP_PREFIXES` is exactly the cookbook's map.

`tests/filters/test_finalizer.py` (new, lands in Slice 3) — covers the phase-2.5 binding pass. Tests: `Meta.filterset_class` promotion accepts a `FilterSet` and rejects a non-`FilterSet`; the binding pass runs once per `DjangoType`; `finalize_django_types()` is idempotent; lazy-related-filter targets unresolved at finalize raise [`ConfigurationError`][glossary-configurationerror].

### `tests/types/test_base.py` (extend)

Add a test pinning the `Meta.filterset_class` promotion from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`: `test_meta_filterset_class_is_promoted_to_allowed_meta_keys` asserts `"filterset_class" not in DEFERRED_META_KEYS` AND `"filterset_class" in ALLOWED_META_KEYS`. Pins the "deferred key promoted only when subsystem ships" contract per [Decision 7](#decision-7--metafilterset_class-promotion-gate).

### `tests/types/test_definition_order.py` (extend)

Add `test_filterset_class_resolves_across_module_boundary` — two `DjangoType`s in two `tests.types.fixtures.*` modules, each with a `Meta.filterset_class` pointing at a sibling `FilterSet`. Asserts `finalize_django_types()` resolves both bindings without `ImportError`.

### `examples/fakeshop/test_query/test_library_api.py` (extend)

System-under-test is the live `/graphql/` HTTP endpoint. Coverage MUST be earned here per the [`docs/TREE.md`][tree] coverage-priority rule. 6–8 new live HTTP tests:

- `test_library_branches_filter_by_name_icontains` — `{ allLibraryBranches(filter: { name: { iContains: "main" } }) { id name } }`; assert response includes only the matching branches.
- `test_library_books_filter_by_choice_enum` — `{ allLibraryBooks(filter: { circulationStatus: { exact: AVAILABLE } }) { id title } }`; assert response includes only available books.
- `test_library_books_filter_by_forward_fk_id` — `{ allLibraryBooks(filter: { shelf: { id: { exact: "<gid>" } } }) { id title } }`; assert response includes only books on the named shelf.
- `test_library_branches_filter_by_reverse_fk_lookup` — `{ allLibraryBranches(filter: { shelves: { code: { iContains: "A" } } }) { id } }`; assert response includes only branches with matching shelves.
- `test_library_books_filter_by_m2m` — `{ allLibraryBooks(filter: { genres: { name: { exact: "SciFi" } } }) { id title } }`; assert response includes only books in the named genre.
- `test_library_books_filter_combines_and_or_not` — `{ allLibraryBooks(filter: { and: [{ title: { iContains: "Foundation" } }, { not: { circulationStatus: { exact: CHECKED_OUT } } }] }) { id } }`; assert response respects all three operators.
- `test_library_books_filter_preserves_optimizer_cooperation` — `{ allLibraryBooks(filter: { ... }) { id title shelf { id code } genres { id name } } }` under `assertNumQueries(N)`; assert the optimizer's `select_related("shelf")` and `prefetch_related("genres")` survive the filter clause.
- `test_library_branches_filter_respects_related_queryset_boundary` — declares a `BranchFilter` with `RelatedFilter("ShelfFilter", queryset=Shelf.objects.filter(is_archived=False))`; queries `{ allLibraryBranches(filter: { shelves: { code: { iContains: "A" } } }) { ... } }`; asserts archived shelves never appear regardless of the nested filter clause.

The HTTP test file's reload pattern from [`docs/TREE.md`][tree] is preserved: clear the global registry, reload app schema modules, then reload the project schema and URLconf.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Flip [`FilterSet`][glossary-filterset] from `planned for 0.0.8` to `shipped (0.0.8)`. Update entry body to describe the shipped contract: declarative `Meta.model` / `Meta.fields` (dict or `"__all__"`); `RelatedFilter` for cross-relation traversal; `check_*_permission` denial gates; explicit-`queryset=` security boundary; logical-and / logical-or / logical-not on the input shape; generated input types with stable class-derived names; cycle-safe lazy resolution via the six-layer pipeline (port per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)).
  - Flip [`RelatedFilter`][glossary-relatedfilter] from `planned for 0.0.8` to `shipped (0.0.8)`. Update body to describe target acceptance (class / absolute path / unqualified name), the Layer-2 module-fallback resolution, and the `queryset=` security boundary.
  - Flip [`Meta.filterset_class`][glossary-metafilterset_class] from `planned for 0.0.8` to `shipped (0.0.8)`. Update body to describe the consumer-facing wiring and the promotion-from-`DEFERRED_META_KEYS` gate.
  - Update the [Index][glossary-index] table's status column for the three entries.
  - Update the [Public exports][glossary-public-exports] list — add `FilterSet` and `RelatedFilter` after `DjangoType` (matching subpackage-import shape; the top-level `__all__` is unchanged per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface)).

- [`docs/README.md`][docs-readme]
  - Move `FilterSet` / `Meta.filterset_class` / `RelatedFilter` from "Coming in `0.1.0`" to "Shipped today (`0.0.8`)" once the joint cut bumps the version.
  - Optional: add a small Quick start example showing the `Meta.filterset_class = MyFilter` shape next to the existing `DjangoType` declaration.

- [`docs/TREE.md`][tree]
  - Flip the `filters/` subpackage entry from `[alpha]` to on-disk. Move from the "target package layout" section to the "current on-disk layout" section.
  - List the five new files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); list the mirrored `tests/filters/` tree (`__init__.py`, `test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`, `test_finalizer.py`).
  - Update the "Test layout going forward" section's `tests/filters/` enumeration to match the on-disk reality.

- [`README.md`][readme]
  - Add `FilterSet` / `RelatedFilter` / `Meta.filterset_class` to the shipped-symbol bullet list (under the `0.0.8` boundary).

- [`GOAL.md`][goal]
  - No edit needed. The astronomy showcase already references `Meta.filterset_class = filters.GalaxyFilter` and the per-app `filters.py` shape; with this card the showcase now describes what shipped instead of what's planned.

- [`TODAY.md`][today]
  - Extend the "Shipped capabilities" enumeration with `FilterSet` / `Meta.filterset_class` / `RelatedFilter`.
  - Extend the fakeshop section to describe the new `BranchFilter` / `BookFilter` / `LoanFilter` / `PatronFilter` declarations under [`examples/fakeshop/apps/library/filters.py`][fakeshop-library] and the live HTTP filter coverage under [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library].

- [`KANBAN.md`][kanban] (Slice 5)
  - Move `WIP-ALPHA-021-0.0.8` to the Done column with the next available `DONE-NNN-0.0.8` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). Past-tense Done body:

    > "Shipped the filtering subsystem. [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] (promoted out of `DEFERRED_META_KEYS`) land at [`django_strawberry_framework/filters/`][filters] across five files (`base.py`, `sets.py`, `factories.py`, `inputs.py`, `__init__.py`) and `tests/filters/` mirrors the layout. Six-layer lazy-resolution pipeline borrowed from `django-graphene-filters`: Layers 1–4 and 6 port library-agnostic verbatim, Layer 5's cycle-safe forward reference adapts from Graphene's `lambda:` to `strawberry.lazy(...)`. Parity-floor primitives (`ArrayFilter`, `RangeFilter`, `ListFilter`, `TypedFilter`, `GlobalIDFilter`) ship under `base.py`; `FILTER_DEFAULTS` maps FK/PK to `GlobalIDFilter` for Relay-aware filtering against `relay.Node` types. `Meta.filterset_class` promotion runs through finalizer phase 2.5 (same seam as `Meta.interfaces`). Per-package input-type registry is separate from the model-to-`DjangoType` registry (`Meta.primary` design preserved). [`examples/fakeshop/apps/library/`][fakeshop-library] grows `filters.py` with `BranchFilter` / `BookFilter` / `LoanFilter` / `PatronFilter` wired through `Meta.filterset_class`; [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows 6–8 live HTTP tests covering scalar / choice-enum / FK / reverse-FK / M2M / logical-and-or-not / optimizer cooperation / related-queryset boundary. Spec: `docs/spec-021-filters-0_0_8.md`. The version bump from `0.0.7 → 0.0.8` is owned by the joint `0.0.8` cut (last `0.0.8` card to ship), NOT this card per Decision 10."
  - Update the card body's `Definition of done` bullet 1 (`docs/spec-filters.md` → `docs/SPECS/spec-021-filters-0_0_8.md` after the Step-8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)).
  - Update the `### In progress` summary paragraph (anchored at [`KANBAN.md`][kanban] #"### In progress") to remove `WIP-ALPHA-021-0.0.8` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`][changelog] (Slice 5)
  - **Append** to the `[Unreleased]` `### Added` subsection (creating the subsection if absent):

    > "Filtering subsystem. [`FilterSet`][glossary-filterset] (declarative `Meta.model` / `Meta.fields` / `check_*_permission` gates / explicit-`queryset=` security boundary), [`RelatedFilter`][glossary-relatedfilter] (cross-relation traversal accepting class / absolute path / unqualified name), and [`Meta.filterset_class`][glossary-metafilterset_class] (promoted out of `DEFERRED_META_KEYS`). Parity-floor primitives: `ArrayFilter`, `RangeFilter`, `ListFilter`, `TypedFilter`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`. Cycle-safe six-layer lazy-resolution pipeline borrowed from `django-graphene-filters` with Graphene's `lambda:` forward references replaced by `strawberry.lazy(...)`. Per-package input-type registry keyed by stable class-derived names. Subpackage at [`django_strawberry_framework/filters/`][filters] (five files); mirror tests at `tests/filters/`. Live HTTP filter coverage in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (6–8 tests across scalar / choice-enum / FK / reverse-FK / M2M / logical / optimizer-cooperation / related-queryset-boundary axes)."
  - **Append** to the `[Unreleased]` `### Changed` subsection:

    > "[`Meta.filterset_class`][glossary-metafilterset_class] is no longer in `DEFERRED_META_KEYS`; declaring `Meta.filterset_class = MyFilter` now wires through to finalizer phase 2.5 and surfaces a working filter input on the GraphQL type. Consumers who declared the key against `0.0.7` saw a [`ConfigurationError`][glossary-configurationerror]; against `0.0.8` it produces a filter surface."
  - Per the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed", this Slice-5 bullet is the explicit permission for this card.
  - The version bump is NOT in this card per [Decision 10](#decision-10--joint-008-cut); the last `0.0.8` card to ship promotes `[Unreleased]` to `[0.0.8]` and bumps `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion atomically.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **Layer 5's Strawberry-adapted forward reference: `strawberry.lazy("dotted.path.TargetInputType")` vs `Annotated[<base>, strawberry.lazy(...)]`.** Preferred answer: use `strawberry.lazy("dotted.path.TargetInputType")` for the input-type self-reference (`and: list[<TypeName>FilterInputType]`) because that's the documented Strawberry shape for "input type that references itself or another input type built later"; use `Annotated[..., strawberry.lazy(...)]` for input-field annotations that need to carry additional Strawberry metadata. Fallback: if implementation reveals one idiom doesn't work for a specific Layer-5 shape (e.g., Strawberry's input-decorator forbids `Annotated[...]` in some position), the implementer picks the idiom that works and pins the decision in a follow-up sub-decision; this is not a re-litigation of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline), only the choice between two Strawberry-idiomatic forms.
- **Input-type namespace under per-`Meta.primary` secondary `DjangoType`s.** Preferred answer per [Decision 9](#decision-9--input-type-namespace-vs-typeregistry): the input-type registry is name-keyed, so two `DjangoType`s on the same model with two different `filterset_class`es generate two distinct input types (`PrimaryGalaxyFilterInputType` and `AdminGalaxyFilterInputType`). Fallback: if a real consumer scenario surfaces where two filtersets on the same model should share an input type (e.g., shared queries against two roles), a follow-up card adds an optional `Meta.filter_input_alias` key that lets the consumer alias the generated input-type name; deferred until demand surfaces.
- **`Meta.filterset_class = MyDjangoFilter` accepting a `django_filters.FilterSet` (not a package `FilterSet`).** Preferred answer per [Decision 5](#decision-5--django-filter-soft-dependency-posture): the validator rejects with [`ConfigurationError`][glossary-configurationerror]; the consumer wraps their `django_filters.FilterSet` in a one-line adapter subclass. Fallback: if the adapter pattern is too verbose for real consumer adoption, a follow-up card ships a `from django_strawberry_framework.filters.adapters import DjangoFilterAdapter` helper that wraps a `django_filters.FilterSet` automatically.
- **Filter applied to a relation that has a custom `get_queryset`.** Preferred answer per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation): the optimizer's existing `Prefetch` downgrade ([Queryset diffing][glossary-queryset-diffing]) preserves the target type's `get_queryset` visibility filter; the filter clause applies to the visibility-scoped queryset. Fallback: if a specific filter shape (e.g., `filter on relation that has both get_queryset AND a RelatedFilter queryset=`) breaks the optimizer cooperation, a follow-up card refactors the binding to thread through the optimizer's `Prefetch` wrapper.
- **Logical-and / logical-or input shape — flat vs nested.** Preferred answer: the cookbook's flat shape (`filter: { and: [...] }`) ports verbatim; nested per-field structures (`filter: { name__icontains: "...", and: [...] }`) are accepted at the top level only; nesting `and` / `or` / `not` inside per-field input is rejected. Fallback: if real consumer feedback wants nested operators, a follow-up card lifts the restriction.
- **`Meta.fields = "__all__"` performance**. Preferred answer: the BFS factory walks every model field; for models with many fields this is O(field_count × lookup_count) at finalize time but the result is cached. Caching at finalize means the per-request cost is unaffected. Fallback: if real-world consumer schemas with very-wide models surface measurable finalize-time impact, a follow-up card adds a `Meta.lookup_subset` shorthand or a per-app field-set policy.
- **`Meta.search_fields` planned for `0.1.2`** but `LOOKUP_PREFIXES` ships in this card. Preferred answer: the `LOOKUP_PREFIXES` map + `construct_search` helper land in `filters/inputs.py` so the future `Meta.search_fields` card consumes them without retrofit; no consumer surface for search lookups exists today. Fallback: if `Meta.search_fields` ships earlier or the cookbook's `search_fields` shape diverges from `LOOKUP_PREFIXES`, that card adjusts; this card's surface is unaffected.
- **Glossary entry parity.** `LazyRelatedClassMixin`, `FilterArgumentsFactory`, `_dynamic_filterset_cache`, `FILTER_DEFAULTS`, and `LOOKUP_PREFIXES` are internal symbols not currently in [`docs/GLOSSARY.md`][glossary]. Preferred answer: keep them internal — the consumer surface is `FilterSet` / `RelatedFilter` / `Meta.filterset_class`; the internal symbols are documented via this spec's body and via module docstrings, not the glossary. Fallback: if a future card surfaces one (e.g., a public `LOOKUP_PREFIXES` re-export for consumers writing custom search resolvers), the glossary entry lands with that card.

## Out of scope (explicitly tracked elsewhere)

- **Ordering** ([`OrderSet`][glossary-orderset], [`Meta.orderset_class`][glossary-metaorderset_class], [`RelatedOrder`][glossary-relatedorder]) — [`WIP-ALPHA-022-0.0.8`][kanban]. Sibling card; reuses this card's lazy-resolution architecture verbatim with `OrderSet` / `RelatedOrder` substituted for `FilterSet` / `RelatedFilter`. Slice 6 of this card holds the composition smoke test until the ordering card ships.
- **Aggregation** ([`AggregateSet`][glossary-aggregateset], [`RelatedAggregate`][glossary-relatedaggregate], [`Meta.aggregate_class`][glossary-metaaggregate_class], [`get_child_queryset`][glossary-get_child_queryset]) — `0.1.3`. Future Layer-3 sidecar; reuses Layers 1–4 of this card's lazy-resolution pipeline; runs at the aggregate-input layer not the filter-input layer.
- **Field selection** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`. Future Layer-3 sidecar; orthogonal to filter machinery (field selection gates result-shape, filters gate result-content).
- **Search fields** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`. Future Layer-3 sidecar; consumes this card's `LOOKUP_PREFIXES` + `construct_search` without modification.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions], [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.0.10`. Future Layer-3 sidecar; composes with this card's `check_*_permission` gates per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation) without retrofit.
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — `0.0.9`. Consumes the `FilterArgumentsFactory` output as the connection's `filter:` argument source. This card's per-package input-type registry is the registration point.
- **`DjangoNodeField`** ([`DjangoNodeField`][glossary-djangonodefield]) — `0.0.9`. Root-level single-node lookup; orthogonal to filtering.
- **`DjangoConnection`** ([`DjangoConnection`][glossary-djangoconnection]) — `0.0.9`. Generic return-type alias; orthogonal to filtering.
- **Connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]) — `0.0.9`. The optimizer learns `edges { node { ... } }` selections; unrelated to filter-input machinery despite both being `0.0.9` follow-ons.
- **`DjangoType` consumer-DX cleanup pass** ([`WIP-ALPHA-023-0.0.8`][kanban]) — joint-`0.0.8` sibling; Strawberry `extensions=[instance]` migration, `manage.py inspect_django_type` diagnostic, `Meta.nullable_overrides`. Independent of filtering.
- **Modifying [`DEFERRED_META_KEYS`][base] entries other than `"filterset_class"`.** Out of scope — this card promotes only `"filterset_class"`; the four siblings (`"orderset_class"`, `"aggregate_class"`, `"fields_class"`, `"search_fields"`) ship under their own cards.

## Definition of done

The card is complete when all of the following are true:

1. [`docs/spec-021-filters-0_0_8.md`][spec-021] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-021-filters-0_0_8-terms.csv`][spec-021-terms] anchoring every project-specific term used in the spec body to the matching [`docs/GLOSSARY.md`][glossary] heading (per [`docs/SPECS/NEXT.md`][next] Step 7).
2. [`django_strawberry_framework/filters/`][filters] ships as a subpackage with `__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface). The subpackage's `__init__.py` re-exports `FilterSet`, `RelatedFilter` (plus internal primitives for advanced uses); the top-level package's `__all__` is unchanged.
3. `base.py` ships the parity-floor primitives per [Decision 4](#decision-4--upstream-primitives-parity-floor): `Filter`, `TypedFilter`, `ArrayFilter`, `ArrayFilterMethod`, `RangeFilter`, `RangeField`, `validate_range`, `ListFilter`, `ListFilterMethod`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, plus `RelatedFilter` and `LazyRelatedClassMixin`.
4. `sets.py` ships `FilterSetMetaclass` and `FilterSet` (with `Meta.model`, `Meta.fields`, `get_filters`, `filter_queryset`, `check_permissions`, `_apply_related_queryset_constraints`) per Layers 3 + 4 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline).
5. `factories.py` ships `FilterArgumentsFactory` (Layer 5 BFS), `get_filterset_class`, `_dynamic_filterset_cache` (Layer 6), and `FILTER_DEFAULTS`.
6. `inputs.py` ships the per-package input-type registry per [Decision 9](#decision-9--input-type-namespace-vs-typeregistry), plus `build_input_class`, `_build_logic_fields`, `_build_input_fields`, `construct_search`, `LOOKUP_PREFIXES`.
7. [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] grows a `filterset_class: type | None = None` slot, populated by `DjangoType.__init_subclass__` from `Meta.filterset_class`.
8. [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] no longer contains `"filterset_class"`; [`ALLOWED_META_KEYS`][base] contains `"filterset_class"`; `_validate_meta` validates `Meta.filterset_class` is a `FilterSet` subclass and raises [`ConfigurationError`][glossary-configurationerror] otherwise.
9. [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] grows the phase-2.5 filter-binding pass per [Decision 6](#decision-6--finalizer-phase-25-binding-seam): for each `DjangoType` with `definition.filterset_class is not None`, validate, call `filterset_cls.get_filters()` (Layer 4), call `FilterArgumentsFactory(filterset_cls).arguments` (Layer 5), and register the resulting input types.
10. `tests/filters/` (new tree) carries five mirror files (`__init__.py`, `test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`) plus `test_finalizer.py` per the [Test plan](#test-plan); each file covers what its mirror source file ships.
11. [`tests/types/test_base.py`][test-types] and [`tests/types/test_definition_order.py`][test-types] grow validator and definition-order tests for `Meta.filterset_class` per the [Test plan](#test-plan).
12. [`examples/fakeshop/apps/library/`][fakeshop-library] ships `filters.py` (new) carrying `BranchFilter`, `BookFilter`, `LoanFilter`, `PatronFilter` with `RelatedFilter` declarations exercising same-module and cross-module lazy resolution.
13. [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] grows `Meta.filterset_class = filters.BranchFilter` (etc.) on the corresponding `DjangoType` classes; root resolvers accept a `filter:` argument that threads through `FilterSet.filter_queryset(...)`.
14. [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows 6–8 live `/graphql/` HTTP tests per the [Test plan](#test-plan) (scalar / choice-enum / forward-FK / reverse-FK / M2M / logical / optimizer-cooperation / related-queryset-boundary).
15. [`docs/GLOSSARY.md`][glossary] flips [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] from `planned for 0.0.8` to `shipped (0.0.8)`; updates entry bodies; updates the [Index][glossary-index] table; updates the [Public exports][glossary-public-exports] list.
16. [`docs/spec-021-filters-0_0_8-terms.csv`][spec-021-terms] anchors every project-specific term in the spec body to its [`docs/GLOSSARY.md`][glossary] heading; running [`uv run python scripts/check_spec_glossary.py --spec docs/spec-021-filters-0_0_8.md`][check-spec-glossary] reports `OK: <N> terms`.
17. [`docs/TREE.md`][tree] flips the `filters/` subpackage entry from `[alpha]` to on-disk; the mirror `tests/filters/` tree is enumerated; "Test layout going forward" reflects the new tree.
18. [`docs/README.md`][docs-readme] moves filter symbols from "Coming in `0.1.0`" to "Shipped today" once the joint cut bumps the version.
19. [`README.md`][readme] adds filter symbols to the shipped-symbol bullet list.
20. [`TODAY.md`][today] extends the shipped-capabilities and fakeshop sections.
21. [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.8` (moved from `WIP-ALPHA-021-0.0.8` in Slice 5) with the past-tense body in [Doc updates](#doc-updates); the `Definition of done` bullet 1 points at the structured spec filename.
22. [`CHANGELOG.md`][changelog] `[Unreleased]` carries the new `### Added` and `### Changed` bullets pinned in [Doc updates](#doc-updates); the CHANGELOG-edit permission for this card comes from this DoD item per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed".
23. The version bump is NOT in this card per [Decision 10](#decision-10--joint-008-cut); the last `0.0.8` card to ship owns the bump to `0.0.8`.
24. Top-level `__all__` is NOT widened (subpackage import path is the right grain per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface)).
25. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — verified by CI's `fail_under = 100` gate, not by the worker locally (per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits").
26. Worker-local validation: `uv run ruff format .` passes and `uv run ruff check --fix .` passes. The worker does NOT run pytest as part of completing this card; pytest is invoked only by CI or by an explicit maintainer ask.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnection]: GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-get_child_queryset]: GLOSSARY.md#get_child_queryset
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-index]: GLOSSARY.md#index
[glossary-metaaggregate_class]: GLOSSARY.md#metaaggregate_class
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-public-exports]: GLOSSARY.md#public-exports
[glossary-queryset-diffing]: GLOSSARY.md#queryset-diffing
[glossary-relatedaggregate]: GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: GLOSSARY.md#relatedfilter
[glossary-relatedorder]: GLOSSARY.md#relatedorder
[glossary-schema-export-management-command]: GLOSSARY.md#schema-export-management-command
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[next-step-8]: SPECS/NEXT.md#step-8--archive-prior-specs-and-update-cross-references
[spec-011]: SPECS/spec-011-relay_interfaces-0_0_5.md
[spec-014]: SPECS/spec-014-meta_primary-0_0_6.md
[spec-015]: SPECS/spec-015-consumer_overrides_scalar-0_0_6.md
[spec-016]: SPECS/spec-016-list_field-0_0_7.md
[spec-017]: SPECS/spec-017-apps-0_0_7.md
[spec-018]: SPECS/spec-018-export_schema-0_0_7.md
[spec-019]: SPECS/spec-019-multi_db-0_0_7.md
[spec-020]: SPECS/spec-020-scalar_map_helper-0_0_7.md
[spec-021]: spec-021-filters-0_0_8.md
[spec-021-terms]: spec-021-filters-0_0_8-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../django_strawberry_framework/types/base.py
[definition]: ../django_strawberry_framework/types/definition.py
[filters]: ../django_strawberry_framework/filters/
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[registry]: ../django_strawberry_framework/registry.py

<!-- tests/ -->
[test-filters]: ../tests/filters/
[test-filters-composition]: ../tests/filters/test_composition.py
[test-types]: ../tests/types/

<!-- examples/ -->
[fakeshop-library]: ../examples/fakeshop/apps/library/
[fakeshop-library-schema]: ../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
