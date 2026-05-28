# Spec: Filtering subsystem (`FilterSet`, `RelatedFilter`, `Meta.filterset_class`)

Target release: `0.0.8` (per [`KANBAN.md`][kanban] card `WIP-ALPHA-021-0.0.8`). The version bump from `0.0.7 → 0.0.8` is owned by the joint `0.0.8` cut, NOT this card — see [Decision 10](#decision-10--joint-008-cut).
Status: planned — no production code on disk yet; the only existing seam is the [`Meta.filterset_class`][glossary-metafilterset_class] entry in `DEFERRED_META_KEYS` at [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base], which this card promotes out of `DEFERRED_META_KEYS` into `ALLOWED_META_KEYS` once the subsystem applies the configured class end-to-end.
Owner: package maintainer.
Predecessors: [`docs/SPECS/spec-011-relay_interfaces-0_0_5.md`][spec-011] (Relay-Node wiring at finalizer phase 2.5 — the synchronization point this card reuses); [`docs/SPECS/spec-014-meta_primary-0_0_6.md`][spec-014] (the `Meta.primary` design and the [`TypeRegistry`][registry-typeregistry] keying convention this card respects when answering [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)); [`docs/SPECS/spec-016-list_field-0_0_7.md`][spec-016] (Decision 10's "joint cut" precedent this card mirrors); [`docs/GLOSSARY.md`][glossary] entries [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], [`Meta.filterset_class`][glossary-metafilterset_class] (all currently `planned for 0.0.8`); [`KANBAN.md`][kanban] card body's "Recommended architectural direction" block (the six-layer lazy-resolution pipeline summary), preserved as [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) without re-litigation.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pinned the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)), the subpackage layout ([Decision 2](#decision-2--subpackage-layout-and-public-export-surface)), the six-layer lazy-resolution pipeline imported verbatim from `django-graphene-filters` with Strawberry-adapted Layer 5 ([Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)), the upstream-primitives parity floor ([Decision 4](#decision-4--upstream-primitives-parity-floor)), a "drop the soft-dep" `django-filter` posture ([Decision 5](#decision-5--django-filter-as-the-foundation) — REVERSED in rev2), the finalizer-phase-2.5 wiring seam ([Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)), the `Meta.filterset_class` promotion gate ([Decision 7](#decision-7--metafilterset_class-promotion-gate)), the relation-permission cascade composition with [`get_queryset`][glossary-get_queryset-visibility-hook] ([Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)), the input-type namespace question against the [`Meta.primary`][glossary-metaprimary] design ([Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)), the joint-`0.0.8`-cut posture ([Decision 10](#decision-10--joint-008-cut)), and the live-HTTP coverage strategy ([Decision 12](#decision-12--live-http-coverage-strategy)). Out of scope: ordering ([`OrderSet`][glossary-orderset]) — covered by sibling [`WIP-ALPHA-022-0.0.8`][kanban]; aggregation ([`AggregateSet`][glossary-aggregateset]) — `0.1.3`; [`DjangoConnectionField`][glossary-djangoconnectionfield] — `0.0.9`; permission cascade ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`; [Meta.search_fields][glossary-metasearch_fields] — `0.1.2`. Dependencies on these surfaces are forward-only: this card composes when they arrive without retrofit.
- **Revision 2** — review pass over rev1 captured in [`docs/feedback.md`][feedback]. Worked in two sub-passes with a coherence check between them.
  - **Pass 1 — Architectural reshape.** Reversed [Decision 5](#decision-5--django-filter-as-the-foundation) (embrace `django-filter` as a hard dep; `FilterSet` subclasses `django_filters.filterset.BaseFilterSet`) per H3 of the feedback because [`pyproject.toml #"django-filter>=25.2"`][pyproject] already pins it and [`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`][goal-migration-shape] promises direct `django_filters.FilterSet` reuse; rewrote [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)'s Layer 5 per H1 to materialize generated input classes as real module globals of [`django_strawberry_framework.filters.inputs`][filters] (Strawberry's `LazyType.resolve_type` reads `module.__dict__`, not object paths); added [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper) (`filter_input_type(FilterSet)`) per H2 to pin the consumer-facing `filter:` argument shape so root resolvers see a working argument at `strawberry.Schema(...)` time; rewrote [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering) to add the materialize-before-`Schema` ordering and [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) to pin the input-class lifecycle (idempotent `(name, filterset_class)` materialization; `registry.clear()` clears the filter input namespace too; `clear_filter_input_namespace()` public helper) per H5. Narrowed `Meta.fields = "__all__"` to scalars + raw FK/PK (no implicit relation traversal) per H7. Pinned the Python-attribute-vs-GraphQL-name shape of `and` / `or` / `not` (`and_` / `or_` / `not_` Python attrs with `strawberry.field(name="and")` etc.) per H6.
  - **Pass 2 — Localized corrections.** Made [Decision 4](#decision-4--upstream-primitives-parity-floor)'s `FILTER_DEFAULTS` FK/PK mapping conditional on the target `DjangoType`'s Relay shape per H4 (Relay-Node targets → `GlobalIDFilter`; non-Relay targets → scalar PK filter). Added `ShelfFilter` to the fakeshop filter plan and split `GenreFilter` into a separate `examples/fakeshop/apps/library/filters_genre.py` fixture module so the `BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")` declaration exercises Layer-2 absolute-import-path resolution (per M1 + M2). Replaced the rev1 `Shelf.objects.filter(is_archived=False)` related-queryset-boundary test (M1 — `is_archived` does not exist on the `Shelf` model) with `Shelf.objects.filter(topic="permanent collection")` using the existing `Shelf.topic` text field. Removed the inconsistent "Public exports list — add `FilterSet` / `RelatedFilter`" instruction from DoD item 15 + Slice 5 GLOSSARY bullet per M3 (the section enumerates top-level re-exports; per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) the filter symbols live at `django_strawberry_framework.filters`, so they're documented under the Filtering category of the Browse-by-category block instead). M4 (`GOAL.md` reuse claim) was auto-resolved by H3's Decision 5 reversal — `FilterSet` IS a `BaseFilterSet`, so the GOAL.md promise holds via parent-class swap; no edit needed. L1: fixed the `TypeRegistry` cross-reference in Predecessors (now points at [`django_strawberry_framework/registry.py`][registry-typeregistry] instead of the wrong glossary anchor) and moved `[spec-021]` / `[spec-021-terms]` link defs from the `docs/SPECS/` group to the `docs/` group; the malformed `OrderSet` / `WIP-ALPHA-022-0.0.8` markdown inside Decision 9 was auto-corrected during Pass 1's Decision 9 rewrite.
- **Revision 3** — second review pass over rev2 captured in [`docs/feedback.md`][feedback]. Worked in two sub-passes with a coherence check between them.
  - **Pass 1 — Architectural / behavioral.** Moved `FILTER_DEFAULTS` from `factories.py` to a class attribute on `FilterSet` (in `sets.py`) per H1 because `django_filters.filterset.BaseFilterSet.filter_for_field()` / `filter_for_lookup()` consult `cls.FILTER_DEFAULTS` directly at runtime filter-instance build time; a factory-only conditional would have let the GraphQL input shape disagree with the runtime filter instance. `FilterSet` overrides `filter_for_field` / `filter_for_lookup` to apply the Relay-vs-scalar branch selection there. `FilterArgumentsFactory._ensure_built` now derives input field shape from `filterset_cls.get_filters()` (the resolved filter instances), NOT from a parallel `FILTER_DEFAULTS` lookup. Defined `FilterSet.apply(input_value, queryset, info)` as the **single resolver-facing classmethod** per H2 (normalizes Strawberry input dataclass → form-data dict, extracts `request` from `info.context`, instantiates `cls(data=data, queryset=queryset, request=request)`, runs `check_permissions`, returns `.qs`); the `django-filter` instance method `filter_queryset(self, queryset)` is now explicitly reserved for the tree-form-logic override path. Replaced every `django_filters.BaseFilterSet` reference with `django_filters.filterset.BaseFilterSet` and pinned the cookbook import shape `from django_filters import filterset` + `class FilterSet(filterset.BaseFilterSet, ...)` per H3 (the top-level `django_filters.BaseFilterSet` does not exist). Narrowed [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)'s related-queryset-boundary contract per H4 to match the cookbook's `_apply_related_queryset_constraints` actual behavior — filters the PARENT queryset via `parent_qs.filter(<rel>__in=<constraint_qs>)`, not the nested relation resolver's output; updated the live HTTP test assertion to seed two branches and verify only the parent-scoping contract.
  - **Pass 2 — Medium + Low.** Pinned the live HTTP test count at exactly 9 per M3 (rev2 was inconsistent "6-8" / "8" / 9-named-bullets). Fixed `relay.GlobalID` construction per M4 (`str(relay.GlobalID(type_name="GenreType", node_id=str(genre.pk)))`, not `relay.GlobalID.from_id(...)` which is the parser for already-encoded strings). Added a Slice 5 `GOAL.md` doc-update bullet rewriting the "plugs in directly" migration-shape narrative per M1 (the spec rejects plain `django_filters.FilterSet`, so the narrative needs to describe the one-line parent-class swap; rev2's "no edit needed" was wrong). Documented the `filter_input_type` CSV-deferral pattern explicitly in the [Risks](#risks-and-open-questions) section per M2 (matches spec-020's `strawberry_config` shape: Slice 5 implementation lands both the GLOSSARY entry and the CSV row; until then the new public symbol is documented in the spec body but not in the CSV). Added `filter_input_type` to the README / docs README symbol sweeps in Slice 5 per M2's second branch. Pinned an import-cycle-safe integration between `registry.clear()` and `clear_filter_input_namespace()` per M5 (local import inside `TypeRegistry.clear()` plus a subprocess test that imports `registry` alone and verifies clear runs without `ImportError`). Converted prose "GOAL.md line 450" references to substring anchors per L1. Unified `materialize_input_class` to the two-argument `(name, cls)` signature per L2 (the destination module is always `django_strawberry_framework.filters.inputs`, no need for a parameter). Softened the `filter_input_type` timing claim per L3 ("when Strawberry evaluates the annotation during schema declaration/collection" instead of "at module-load time"; added a future-annotations fixture test). Refined the graphene-django Relay claim per L4 (the unconditional `GlobalIDFilter` is tied to the filter-connection-field defaults, not the framework as a whole — `graphene-django`'s `DjangoObjectType` itself supports non-Relay shapes).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`FilterSet`][glossary-filterset] — the declarative filter class this card ships (`planned for 0.0.8`). Subclasses `django_filters.filterset.BaseFilterSet` per [Decision 5](#decision-5--django-filter-as-the-foundation) and borrows the six-layer lazy-resolution architecture from `django-graphene-filters` per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline); Graphene's `graphene.InputObjectType` becomes `strawberry.input` and Graphene's `lambda:` forward references become `Annotated["TypeName", strawberry.lazy("django_strawberry_framework.filters.inputs")]` over module globals (per H1 of [`docs/feedback.md`][feedback]).
- [`RelatedFilter`][glossary-relatedfilter] — cross-relation filter traversal (`planned for 0.0.8`). Accepts a target `FilterSet` class, an absolute import path string, or an unqualified name for circular references; lazy-resolved at finalizer time.
- [`Meta.filterset_class`][glossary-metafilterset_class] — the consumer-facing key (`planned for 0.0.8`) that points a [`DjangoType`][glossary-djangotype] at its `FilterSet`. Promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` per [Decision 7](#decision-7--metafilterset_class-promotion-gate).
- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type this card extends with a filter sidecar. The `Meta`-driven shape is what makes `Meta.filterset_class = ItemFilter` legible to a Django audience.
- [`finalize_django_types`][glossary-finalize_django_types] — the synchronization point where the filter subsystem's lazy-resolution pipeline runs (phase 2.5, the same seam [`Meta.interfaces = (relay.Node,)`][glossary-metainterfaces] uses).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the optimizer this card composes with. Filter clauses applied to a queryset must not break the optimizer's [Queryset diffing][glossary-queryset-diffing] cooperation; covered by [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation) and a live HTTP test.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — pre-filter visibility scoping. Composes with filter `check_*_permission` gates ([Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)).
- [`OrderSet`][glossary-orderset] — sibling [`WIP-ALPHA-022-0.0.8`][kanban] subsystem. Mentioned only as the second consumer of the same lazy-resolution architecture this card ships; out of scope here.
- [`AggregateSet`][glossary-aggregateset] / [`get_child_queryset`][glossary-get_child_queryset] / [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — future Layer-3 sidecars referenced as the forward composition surface; not implemented here.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — `0.0.9`; the consumer-facing surface that threads `filter:` arguments through. The factory machinery this card ships is the input it will consume, so the `0.0.8` deliverable is the back-end half of the `0.0.9` connection field's filter surface.
- [`Meta.primary`][glossary-metaprimary] — the multi-`DjangoType`-per-model design from `0.0.6` whose `TypeRegistry` keying convention this card respects per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation and finalization time for unknown filter target classes, invalid lookup names, circular references that exhaust the resolution guard, etc. — see [Edge cases](#edge-cases-and-constraints).
- [`Meta.search_fields`][glossary-metasearch_fields] — the search-input surface ([planned for `0.1.2`][glossary-metasearch_fields]); the `LOOKUP_PREFIXES` map (`^` / `=` / `@` / `$`) ported verbatim from `django-graphene-filters` lives in the filter subsystem because `construct_search` belongs in the filter pipeline.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule at [`AGENTS.md`][agents] #"package tests live under" (package tests under `tests/filters/` with `__init__.py` shells; example-project non-HTTP tests under `examples/fakeshop/tests/`; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority rule at [`AGENTS.md`][agents] #"any coverage line achievable via a real GraphQL query"; the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; the settings-keys rule at [`AGENTS.md`][agents] #"Add settings keys only when the feature that needs them lands"; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — [Slice 5](#slice-checklist) grants the explicit permission for this card.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical per [Decision 12](#decision-12--live-http-coverage-strategy).
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 5; the card body's `docs/spec-filters.md` reference predates the structured `spec-<NNN>-<topic>-<0_0_X>.md` convention and gets rewritten in the same Slice-5 sweep per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
- [`docs/TREE.md`][tree] — tests mirror source one-to-one. The subsystem lives at [`django_strawberry_framework/filters/`][filters] per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface); the mirror partner is `tests/filters/` (new tree). The [target package layout][tree] section in `docs/TREE.md` already names the directory; this card flips it from `[alpha]` to on-disk.
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers).

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Six slices total.

- [ ] Slice 1: Foundation — module layout + `Filter` primitives + `FilterSet` metaclass
  - [ ] Create [`django_strawberry_framework/filters/`][filters] subpackage with `__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface). Module-level docstrings on each file pin the responsibility (`base.py` = `Filter` / `RelatedFilter` / primitives; `sets.py` = `FilterSet` (subclasses `django_filters.filterset.BaseFilterSet`) + metaclass; `factories.py` = `FilterArgumentsFactory` + `get_filterset_class` + `_dynamic_filterset_cache`; `inputs.py` = filter input classes materialized as module globals + input-data adapters + lifecycle ledger).
  - [ ] `base.py` ships the five verified upstream primitives per [Decision 4](#decision-4--upstream-primitives-parity-floor): `Filter` (base), `TypedFilter`, `ArrayFilter` + `ArrayFilterMethod`, `RangeFilter` + `RangeField` + `validate_range`, `ListFilter` + `ListFilterMethod`, `GlobalIDFilter` + `GlobalIDMultipleChoiceFilter`. Each is a port of the matching `graphene_django/filter/filters/*.py` primitive (sourced from `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/filters/`); the port is library-agnostic where possible and Strawberry-adapted only at the input-type-construction boundary.
  - [ ] `base.py` also ships `RelatedFilter` (the `BaseRelatedFilter` port from `django_graphene_filters/filters.py::BaseRelatedFilter`) and `LazyRelatedClassMixin` (port from `django_graphene_filters/mixins.py::LazyRelatedClassMixin`) — Layers 1 + 2 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline).
  - [ ] `sets.py` ships `FilterSetMetaclass` (port from `django_graphene_filters/filterset.py::FilterSetMetaclass`) and `FilterSet` (port from `django_graphene_filters/filterset.py::AdvancedFilterSet`, with `get_filters` doing Layer-4 cycle-safe expansion) — Layers 3 + 4 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline). `FilterSet` accepts `Meta.model`, `Meta.fields` (dict form `{"name": ["exact", "icontains"]}` or `"__all__"`), and per-field `check_<field>_permission` hooks.
  - [ ] `inputs.py` IS the input-class namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) — generated filter input classes are materialized as real module globals of `django_strawberry_framework.filters.inputs` via `materialize_input_class(name, cls)` (sets `sys.modules["django_strawberry_framework.filters.inputs"].<name> = cls`), keyed by stable class-derived names (e.g., `"GalaxyFilterInputType"`); a private `_materialized_names: dict[str, type[FilterSet]]` ledger tracks provenance for idempotent re-materialization. This module namespace is NOT the same surface as `django_strawberry_framework.registry.registry` (the model-to-`DjangoType` registry). The two namespaces do not collide because their key types are disjoint (Django model class vs string class name). The shape is module-globals-keyed (not dict-keyed) because Strawberry's [`LazyType.resolve_type`][filters] reads `module.__dict__[name]`, not a sidecar dict — per H1 of [`docs/feedback.md`][feedback].
- [ ] Slice 2: Factories — `FilterArgumentsFactory` BFS + dynamic-filterset cache
  - [ ] `factories.py` ships `FilterArgumentsFactory` (port from `django_graphene_filters/filter_arguments_factory.py::FilterArgumentsFactory`) — Layer 5 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline). BFS walk that builds every reachable `strawberry.input` type; `_build_class_type` emits `@strawberry.input`-decorated classes via `strawberry_django_framework.filters.inputs.build_input_class(name, field_specs)` (the Strawberry-adapted analogue of Graphene's `type(name, (graphene.InputObjectType,), fields)`).
  - [ ] `factories.py` ships `get_filterset_class` (port from `django_graphene_filters/filterset_factories.py::get_filterset_class`, NOT the same-named `graphene_django/filter/utils.py::get_filterset_class` — the spec pins this distinction in [Decision 4](#decision-4--upstream-primitives-parity-floor)) plus `_dynamic_filterset_cache` (Layer 6) keyed by `(model, fields, extra_meta)`. The cache prevents duplicate-`__name__` collisions when two connection fields target the same model without declaring an explicit `filterset_class`.
  - [ ] `sets.py` carries `FILTER_DEFAULTS` as a **class attribute on `FilterSet`** (NOT in `factories.py` — corrected per H1 of [`docs/feedback.md`][feedback], because `django_filters.filterset.BaseFilterSet.filter_for_field()` / `filter_for_lookup()` consult `cls.FILTER_DEFAULTS` directly during the runtime filter-instance build). The same map is the Strawberry-adapted analogue of `graphene_django/filter/filterset.py::GrapheneFilterSetMixin.FILTER_DEFAULTS`. `FilterSet` also overrides `filter_for_field()` / `filter_for_lookup()` to apply the conditional Relay-vs-scalar selection per [Decision 4](#decision-4--upstream-primitives-parity-floor): Relay-Node targets → `GlobalIDFilter`; non-Relay targets → the scalar PK filter derived from the target PK column conversion. `factories.py::FilterArgumentsFactory._ensure_built` then derives the Strawberry input field type from the **resolved filter instances on the FilterSet**, not from a parallel map — input shape stays downstream of filter shape.
  - [ ] `inputs.py` ships the input-data adapter functions: `_build_logic_fields` (`and` / `or` / `not` self-references via `strawberry.lazy(...)`), `_build_input_fields` (target-filterset references via `strawberry.lazy(...)`), and `construct_search` (the `LOOKUP_PREFIXES` map — `^` → `istartswith`, `=` → `iexact`, `@` → `search`, `$` → `iregex` — ported verbatim).
- [ ] Slice 3: Wiring — `Meta.filterset_class` promotion + finalizer phase 2.5 binding
  - [ ] [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] grows a `filterset_class: type | None = None` field. The slot is populated by `DjangoType.__init_subclass__` from `Meta.filterset_class` once the key is promoted out of `DEFERRED_META_KEYS`.
  - [ ] [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] drops `"filterset_class"`. [`ALLOWED_META_KEYS`][base] grows `"filterset_class"`. The `_validate_meta` function validates the supplied class is a `FilterSet` subclass and raises [`ConfigurationError`][glossary-configurationerror] otherwise.
  - [ ] [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] grows a per-type filter-binding pass in phase 2.5 (immediately after `apply_interfaces` / `install_relay_node_resolvers` and before phase 3's `strawberry.type` decoration). For each `DjangoType` whose `definition.filterset_class is not None`: validate, call `filterset_cls.get_filters()` to trigger Layer-4 expansion, call `FilterArgumentsFactory(filterset_cls).arguments` to trigger Layer-5 BFS, and materialize each built input class as a module global of [`django_strawberry_framework.filters.inputs`][filters] via `materialize_input_class(name, cls)`. The materialization is idempotent for `(name, filterset_class)` pairs and raises [`ConfigurationError`][glossary-configurationerror] on name collision against a different filterset (per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)). `registry.clear()` invokes `clear_filter_input_namespace()` so the model-to-`DjangoType` clear and the filter-input clear share one entry point. Calling `finalize_django_types()` twice is still a no-op via the existing `registry.is_finalized()` guard.
- [ ] Slice 4: Live HTTP coverage in fakeshop
  - [ ] [`examples/fakeshop/apps/library/`][fakeshop-library] grows `filters.py` containing `BranchFilter`, `ShelfFilter`, `BookFilter`, `LoanFilter`, `PatronFilter` (selected because the library app already exercises forward / reverse / M2M relations live per [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]; the filter classes mirror that relation shape with same-module `RelatedFilter(ShelfFilter)` references between `BranchFilter` and `ShelfFilter`). The M2M side targets `GenreType` (which IS Relay-Node-shaped per [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] — `Meta.interfaces = (relay.Node,)` ships on `GenreType`); `GenreFilter` lives in a **separate fixture module** [`examples/fakeshop/apps/library/filters_genre.py`][fakeshop-library] so this card's `BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")` declaration exercises the Layer-2 absolute-import-path lazy-resolution path (corrected per M2 of [`docs/feedback.md`][feedback]; same-module unqualified-name resolution is exercised by every other `RelatedFilter("...")` declaration in `filters.py`).
  - [ ] [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] grows `Meta.filterset_class = filters.BranchFilter` (etc.) on the corresponding `DjangoType` classes including `ShelfType` (so `BookFilter.shelf` has a target `ShelfFilter` to resolve against under [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) Layer 4). Sibling library root-list resolvers (`all_library_branches`, `all_library_books`, etc.) annotate `filter:` via `filter_input_type(filters.BranchFilter)` per [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper) and call `filters.BranchFilter.apply(filter_value, queryset, info)` (the unified resolver-facing classmethod per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation) and H2 of [`docs/feedback.md`][feedback]) before returning the queryset — the same shape `DjangoConnectionField` will reuse in `0.0.9`.
  - [ ] [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows 9 new live `/graphql/` HTTP tests (pinned per M3 of [`docs/feedback.md`][feedback], replacing rev2's inconsistent "6–8"/"8" wording): scalar-field filter (`name: { iContains: "..." }`), choice-enum filter (`circulationStatus: { exact: AVAILABLE }`), **non-Relay forward-FK filter** against `ShelfType`'s scalar `int` PK (`shelf: { id: { exact: 1 } }`), **Relay forward-M2M filter** against `GenreType`'s GlobalID (`genres: { id: { exact: "<global-id-string>" } }`), reverse-FK filter (`shelves: { code: { iContains: "..." } }`), logical-and / logical-or filter combinations, optimizer cooperation (filtered queryset still receives `select_related` / `prefetch_related` for nested selections — pinned by `assertNumQueries(N)`), related-queryset boundary using an existing `Shelf` field (`Shelf.objects.filter(topic="permanent collection")` as the `RelatedFilter` `queryset=` constraint — no model change needed; corrected per M1 of [`docs/feedback.md`][feedback], which flagged the rev1 `is_archived` field as nonexistent). The Relay-vs-scalar split confirms the [Decision 4](#decision-4--upstream-primitives-parity-floor) conditional `FILTER_DEFAULTS` mapping end-to-end.
- [ ] Slice 5: Docs + KANBAN + CHANGELOG
  - [ ] [`docs/GLOSSARY.md`][glossary]: flip [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] from `planned for 0.0.8` to `shipped (0.0.8)`. Add a new entry `## filter_input_type` documenting the consumer helper from [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper) — returns `Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` for resolver-argument annotations. Update the [Index][glossary-index] table with rows for all four entries. Document `FilterSet` / `RelatedFilter` / `filter_input_type` under the Filtering category of the [Browse by category][glossary] block; the [Public exports][glossary-public-exports] section is NOT updated here because it lists top-level `django_strawberry_framework` re-exports, and per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) the filter symbols live at `django_strawberry_framework.filters`.
  - [ ] [`docs/README.md`][docs-readme]: add `FilterSet` / `RelatedFilter` / `filter_input_type` / `Meta.filterset_class` to the "Coming in `0.1.0`" → graduate to "Shipped today (`0.0.8`)" once the version bump lands in the joint cut (per M2 of [`docs/feedback.md`][feedback]: `filter_input_type` is the consumer-facing resolver helper from [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper) and was missing from the rev2 sweep).
  - [ ] [`docs/TREE.md`][tree]: flip the `filters/` subpackage entry from `[alpha]` to on-disk (move from the "target package layout" section to the "current on-disk layout" section). List the five new files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); list the mirrored `tests/filters/` tree.
  - [ ] [`README.md`][readme]: add `FilterSet` / `RelatedFilter` / `filter_input_type` to the shipped-symbol bullet list (under the `0.0.8` boundary), matching the joint-cut promotion timing (per M2 of [`docs/feedback.md`][feedback]).
  - [ ] [`GOAL.md`][goal]: the astronomy showcase already references `filters.py` and `Meta.filterset_class`. AND rewrite the "Coming from DRF + `django-filter`" migration narrative (currently anchored at [`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`][goal-migration-shape]) — corrected per M1 of [`docs/feedback.md`][feedback]. The literal "plugs in directly" wording is misleading because the spec's validator at `_validate_meta` rejects a plain `django_filters.FilterSet` and the consumer migration is a one-line parent-class swap (`class CategoryFilter(FilterSet):` instead of `class CategoryFilter(django_filters.FilterSet):`). Replacement wording: "Your existing `django_filters.FilterSet` migrates to `Meta.filterset_class` via a one-line parent-class swap to `django_strawberry_framework.filters.FilterSet`; the package's `FilterSet` IS a `django_filters.filterset.BaseFilterSet` subclass, so every `Filter` / `FilterMethod` / form-cleaning primitive you already use carries over unchanged." Update the diff block in the same section so the `class CategoryFilter(django_filters.FilterSet):` line shows the parent-class swap rather than implying direct reuse.
  - [ ] [`TODAY.md`][today]: extend the "Shipped capabilities" enumeration with `FilterSet` / `Meta.filterset_class` / `RelatedFilter`; extend the fakeshop section to mention the new live `BranchFilter` / `BookFilter` / `LoanFilter` / `PatronFilter` declarations and the filter-input live HTTP tests under [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library].
  - [ ] [`KANBAN.md`][kanban]: move `WIP-ALPHA-021-0.0.8` to the Done column with the next available `DONE-NNN-0.0.8` id (renumber per the column-move pass). Past-tense Done body pinned in [Doc updates](#doc-updates). Rewrite the card body's `Definition of done` bullet 1 (`docs/spec-filters.md` → `docs/SPECS/spec-021-filters-0_0_8.md` after the Step-8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)).
  - [ ] [`CHANGELOG.md`][changelog]: append `### Added` bullets to `[Unreleased]` for `FilterSet`, `RelatedFilter`, `Meta.filterset_class`, the per-module input-class namespace, the `FILTER_DEFAULTS` map, and the cross-relation lazy-resolution surface. Append a `### Changed` bullet noting that `Meta.filterset_class` is no longer in `DEFERRED_META_KEYS`. Per the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed", this Slice-5 bullet is the explicit permission for this card.
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
- [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer]: runs three phases (1, 2, 2.5, 3); phase 2.5 currently handles only `apply_interfaces` and `install_relay_node_resolvers`. The phase is the seam this card grows a fourth step into per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering).
- [`docs/GLOSSARY.md`][glossary]: [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] all carry `planned for 0.0.8` status today.
- [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]: exercises forward / reverse FK, forward / reverse OneToOne, forward / reverse M2M, choice-enum generation, `Meta.interfaces = (relay.Node,)` on `GenreType`, `Meta.optimizer_hints` on `LoanType`, and consumer-shaped querysets that cooperate with the optimizer. No filter declarations today; the schema is the natural host for the live HTTP filter coverage per [Decision 12](#decision-12--live-http-coverage-strategy).
- [`docs/SPECS/spec-016-list_field-0_0_7.md`][spec-016]: the most-recently-shipped spec; the canonical voice / depth / section-layout reference for this spec.
- Upstream cookbook (working reference per [`START.md`][start]): `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/` — the six-layer pipeline this card ports verbatim through Layers 1–4 and 6, and Strawberry-adapts at Layer 5.
- Upstream `graphene-django`: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/` — the parity-floor primitives this card mirrors (per [Decision 4](#decision-4--upstream-primitives-parity-floor)). Note: `graphene_django/filter/utils.py::get_filterset_class` and the cookbook's `filterset_factories.py::get_filterset_class` are different functions with the same name; this card mirrors the cookbook's shape per [Decision 4](#decision-4--upstream-primitives-parity-floor).
- Upstream `strawberry-graphql-django`: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py` — the single-file decorator-driven implementation. The runtime pipeline (`process_filters`) is conceptually parallel to this card's `FilterSet.apply(input_value, queryset, info)` classmethod; the declaration surface (`@strawberry_django.filter_type(Model, lookups=True)` vs `class ItemFilter(FilterSet): class Meta: model = Item`) differs per the package's DRF-shaped positioning.

## Goals

1. Ship `FilterSet` + `RelatedFilter` + per-field `check_*_permission` gates + cross-relation traversal with cycle-safe lazy resolution, mirroring the `django-graphene-filters` six-layer pipeline minus Layer 5's GraphQL-engine substitution.
2. Promote [`Meta.filterset_class`][glossary-metafilterset_class] out of `DEFERRED_META_KEYS` only when the filter subsystem applies the configured class end-to-end — same gate as [`Meta.interfaces`][glossary-metainterfaces] in `DONE-011-0.0.5`.
3. Establish the registration / factory / lazy-resolution pattern the four sibling Layer-3 subsystems ([`OrderSet`][glossary-orderset], [`AggregateSet`][glossary-aggregateset], [`FieldSet`][glossary-fieldset], [Meta.search_fields][glossary-metasearch_fields]) reuse without redesign.
4. Stay composable with [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Queryset diffing][glossary-queryset-diffing] / [Plan cache][glossary-plan-cache] / [FK-id elision][glossary-fk-id-elision] / [Strictness mode][glossary-strictness-mode] — a filter clause is just another `.filter(...)` call on the consumer queryset; the optimizer cooperates.
5. Expose enough introspection (`FilterSet.get_filters()`, `FilterArgumentsFactory(cls).arguments`) for a maintainer to ask "what filter surface does this type support?" from the REPL in one call.
6. Earn package coverage through live fakeshop HTTP flows per [Decision 12](#decision-12--live-http-coverage-strategy); the package coverage gate (`fail_under = 100`) is reached because the live HTTP tests exercise the package end-to-end.

## Non-goals

- **Ordering / aggregation / fieldsets / permissions cascade.** Each ships in its own card. Composition with this card is forward-only; no Layer-3 sibling is implemented here.
- **`DjangoConnectionField` integration.** The `0.0.9` connection field consumes the factory machinery this card ships; the connection-field surface itself is out of scope.
- **A `Meta.filterset_class = MyDjangoFilter` shape that accepts an arbitrary `django_filters.FilterSet` subclass without re-parenting.** Per [Decision 5](#decision-5--django-filter-as-the-foundation), `FilterSet` IS a `django_filters.filterset.BaseFilterSet` subclass, so any consumer who has `class MyFilter(django_filters.FilterSet):` today migrates by swapping the parent class to `django_strawberry_framework.filters.FilterSet`; the migration is one line and inherits the lazy-resolution + GraphQL-input layers for free. Accepting a plain `django_filters.FilterSet` at `Meta.filterset_class` without re-parenting would mean two consumer-facing surfaces for the same wiring (one with `RelatedFilter` / `check_*_permission` recursion, one without), so the package validates that `Meta.filterset_class` is specifically a `django_strawberry_framework.filters.FilterSet` subclass — but the package's class IS a `django_filters.filterset.BaseFilterSet`, so the [`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`][goal-migration-shape] direct-reuse promise holds via parent-class swap.
- **Replacing the optimizer's queryset-diffing contract.** Filters land as `.filter(...)` calls before the optimizer walks the selection tree; the existing cooperation contract is untouched.
- **Auto-generation of `FilterSet` from `Meta.fields` without declaring an explicit class.** Deferred; the dynamic-factory machinery (Layer 6) exists for the connection-field path where the connection field can pre-declare `model=Item, fields="__all__"` without a sibling `FilterSet` class. Direct consumer-facing implicit generation lands when [`DjangoConnectionField`][glossary-djangoconnectionfield] ships in `0.0.9`.
- **The version bump.** Owned by the last `0.0.8` card to ship per [Decision 10](#decision-10--joint-008-cut).

## Borrowing posture

Filtering is the most heavily-borrowed surface in the package. The architectural answer is pre-pinned by the [`KANBAN.md`][kanban] card body's "Recommended architectural direction" block; this spec preserves it without re-litigation.

### From `django-filter` — embrace as the foundation

`django-filter` is already a hard dependency at [`pyproject.toml #"django-filter>=25.2"`][pyproject], and [`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`][goal-migration-shape] explicitly promises that "the existing `django_filters.FilterSet` plugs into `Meta.filterset_class` directly". The package's `FilterSet` subclasses `django_filters.filterset.BaseFilterSet` and inherits the load-bearing machinery — `declared_filters`, `base_filters`, `.filters`, `.form`, `.qs`, `get_filters()`, `Filter.method`, form cleaning, lookup generation. Re-implementing those layers would be a large net-new code surface for zero gain when the dependency is already in the lock file. Per [Decision 5](#decision-5--django-filter-as-the-foundation), this card embraces the dep; the [`docs/GLOSSARY.md`][glossary] entry for [`FilterSet`][glossary-filterset] documents the inheritance contract for consumers.

The cookbook's `AdvancedFilterSet` (the working reference per [`START.md`][start]) inherits from `django_filters.filterset.BaseFilterSet`; the package's `FilterSet` mirrors that exact inheritance. The added value is the cycle-safe lazy-resolution layer (Layers 1–4 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)), the Strawberry-adapted GraphQL-input layer (Layer 5), and the dynamic-factory cache (Layer 6) — none of which `django-filter` ships.

### From `django-graphene-filters` — borrow heavily (the cookbook is the working reference)

Local source path: `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/`. Per [`START.md`][start] ("Working reference") this cookbook is the package's canonical Layer-3 reference; the goal is to recreate "what the package enables for the schema author," not to port Graphene internals. Five of the six lazy-resolution layers are library-agnostic Python and port verbatim on top of the shared `django_filters.filterset.BaseFilterSet` foundation:

- `filters.py::BaseRelatedFilter` → `django_strawberry_framework.filters.base::RelatedFilter` (Layer 1).
- `mixins.py::LazyRelatedClassMixin` → `django_strawberry_framework.filters.base::LazyRelatedClassMixin` (Layer 2).
- `filterset.py::FilterSetMetaclass` → `django_strawberry_framework.filters.sets::FilterSetMetaclass` (Layer 3).
- `filterset.py::AdvancedFilterSet` → `django_strawberry_framework.filters.sets::FilterSet`, subclassing `django_filters.filterset.BaseFilterSet` exactly as the cookbook does. `FilterSet.get_filters` runs Layer-4 cycle-safe expansion with the same `__dict__["_expanded_filters"]` cache and `__dict__["_is_expanding_filters"]` recursion guard.
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
- `filter/filterset.py::GrapheneFilterSetMixin.FILTER_DEFAULTS` (FK/PK → `GlobalIDFilter`) — the source of this card's `FILTER_DEFAULTS` mapping under [Decision 4](#decision-4--upstream-primitives-parity-floor). Note: per [Decision 4](#decision-4--upstream-primitives-parity-floor) the FK/PK → `GlobalIDFilter` mapping is **conditional on the target `DjangoType`'s Relay shape**, not blanket — the upstream mapping is unconditional because `graphene-django`'s `DjangoFilterConnectionField` (the path `FILTER_DEFAULTS` is tied to) always returns a Relay connection by construction; `graphene-django`'s `DjangoObjectType` itself supports non-Relay shapes, so the unconditional `GlobalIDFilter` is specifically a property of the filter-connection-field defaults, not the framework as a whole (corrected per L4 of [`docs/feedback.md`][feedback]). The package preserves the conditional shape that matches its non-Relay-by-default `DjangoType` surface and its FilterSet-not-connection-field-yet entry point.

### From `strawberry-graphql-django` — borrow the runtime-pipeline pattern (not the surface)

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py`. The upstream's single-file decorator-driven implementation is conceptually parallel at the runtime layer (`process_filters` compiles input values into queryset arguments) but the declaration surface diverges per the package's DRF-shaped positioning. Borrow the runtime contract loosely; don't borrow the decorator-on-input-type surface:

- `filters.py::FilterLookup` — the generic typed lookup descriptor (`exact`, `i_exact`, `contains`, ...) is conceptually similar to this card's lookup-pair generation but the Strawberry adaptation lands differently because the cookbook's BFS factory drives the lookup expansion.
- `filters.py::process_filters` — the runtime side of the filter pipeline. This card's `FilterSet.apply(input_value, queryset, info)` classmethod is the equivalent consumer-facing entry point (the `django-filter` instance method `filter_queryset(self, queryset)` is reserved for the tree-form-logic override path and has a different signature); both compile a Strawberry/Graphene input into queryset args.
- `filters.py::FILTERS_ARG` (`= "filters"`) — module-level constant for the GraphQL argument name. This card's equivalent is `FILTER_ARG = "filter"` (singular per the cookbook's convention; the upstream's plural form is a documented difference).
- `filters.py::filter_type` decorator — NOT borrowed (the package's `Meta`-driven surface forbids decorator-on-input-type per [`START.md`][start] "Style they care about").
- `filters.py #"def __getattr__"` legacy `filter` alias with `DeprecationWarning` — NOT borrowed; the package's first-ship surface does not need a legacy alias.

### Explicitly do not borrow

- **Graphene's `lambda: target_input_type` cycle-safe forward references.** Replaced by `Annotated["{TargetFilterSet}InputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` at Layer 5 (per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)). Strawberry's `LazyType.resolve_type` imports the named module and reads `module.__dict__[type_name]` — it does NOT traverse object paths — so the generated input classes MUST be real module globals of `django_strawberry_framework.filters.inputs`, not dict entries on a private registry (verified by inspection of the installed Strawberry; cited in H1 of [`docs/feedback.md`][feedback]).
- **`graphene-django`'s `setup_filterset` wrapper-avoidance.** Strawberry's eager annotation resolution does not have the "Graphene{X}Filter" wrapping problem that motivated this in the reference; the wrapper is dropped.
- **`graphene-django`'s `replace_csv_filters`.** Strawberry's typed input handles `list[T]` natively without comma-separated-string workarounds; the function is dropped.
- **`@strawberry_django.filter_type(Model, lookups=True)` decorator surface.** The package's `Meta`-driven shape per [`START.md`][start] "Meta classes everywhere on consumer surfaces" forbids decorator-on-input-type for consumer-facing classes.

## User-facing API

The shipped consumer surface adds four new symbols re-exported from `django_strawberry_framework.filters` — `FilterSet`, `RelatedFilter`, `filter_input_type`, and (internally registered) the input-class module-globals registry. The [`Meta.filterset_class`][glossary-metafilterset_class] hook is the consumer-facing wiring on the existing [`DjangoType`][glossary-djangotype] surface; `filter_input_type(FilterSet)` is the resolver-annotation helper that lets a normal `@strawberry.field` resolver accept a `filter:` argument that resolves to the generated input class at schema-build time.

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

`FilterSet` subclasses `django_filters.filterset.BaseFilterSet` (per [Decision 5](#decision-5--django-filter-as-the-foundation)), so consumers familiar with `django-filter` keep every primitive they already know — `declared_filters`, `base_filters`, `Filter.method`, `form`, `qs`, lookup parsing — and add the package's `RelatedFilter` lazy-resolution layer plus the GraphQL-input layer on top.

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

`Meta.filterset_class` is the only wiring required at the `DjangoType` site. The finalizer-phase-2.5 binding (per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)) takes care of input-class materialization (as module globals of [`django_strawberry_framework.filters.inputs`][filters]), lazy-related-filter resolution, and registry registration.

### Exposing the `filter:` argument on a resolver

```python
import strawberry

from django_strawberry_framework.filters import filter_input_type

from . import filters, models


@strawberry.type
class Query:
    @strawberry.field
    def all_galaxies(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.GalaxyFilter) | None = None,
    ) -> list[GalaxyType]:
        queryset = models.Galaxy.objects.all()
        if filter is not None:
            queryset = filters.GalaxyFilter.apply(filter, queryset, info)
        return queryset
```

`filter_input_type(filters.GalaxyFilter)` returns `Annotated["GalaxyFilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]`, the canonical Strawberry forward-reference idiom. At `@strawberry.type` decoration time, Strawberry stores the annotation unresolved; at `strawberry.Schema(...)` construction time, Strawberry's `LazyType.resolve_type` imports `django_strawberry_framework.filters.inputs` and reads `GalaxyFilterInputType` from `module.__dict__` — which the finalizer's phase-2.5 binding pass has materialized as a real module global by then. The consumer never touches `Annotated[...]` directly; the helper hides it.

`GalaxyFilter.apply(input_value, queryset, info)` is the **single resolver-facing classmethod** per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation). It normalizes the Strawberry input dataclass into the form-data dict `django-filter` expects (walking nested `RelatedFilter` input objects, mapping `and_` / `or_` / `not_` Python attrs back into the logical-operator keys, flattening per-field lookup pairs), extracts `request = info.context.request` (or `info.context`, depending on the consumer's request adapter), instantiates `cls(data=data, queryset=queryset, request=request)`, runs `check_permissions(request)` (recurses through `RelatedFilter`s), and returns `filterset.qs` — the `django-filter` instance's `.qs` property after validation. The classmethod is the only symbol the resolver code touches; the inherited instance method `filter_queryset(self, queryset)` is reserved for the `django-filter` tree-form-logic override path (it has the `django-filter` signature `(self, queryset) -> QuerySet`, not the resolver signature `(input_value, queryset, info)`) and is not what consumer code calls.

When [`DjangoConnectionField`][glossary-djangoconnectionfield] ships in `0.0.9`, it accepts `filterset_class=` and owns the argument injection AND the `apply(...)` call internally; the manual `filter_input_type(...)` annotation + `Filter.apply(...)` body shown above is the explicit shape `0.0.8` consumers reach for at the resolver level and the same machinery the connection field reuses under the hood one card later.

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

The factory auto-generates the three logical-operator fields on every `<TypeName>FilterInputType`. Python attribute names use the trailing-underscore convention (`and_`, `or_`, `not_`) because `and` / `or` / `not` are Python keywords and cannot appear as dataclass field names; the GraphQL surface names are exactly `and`, `or`, `not` via `strawberry.field(name="and")` / `name="or"` / `name="not"`. Consumer-facing GraphQL shape:

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

The self-referential nature of the input type (`and_: list[<TypeName>FilterInputType] | None`) is handled by Layer 5's Strawberry-adapted forward reference per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) — `Annotated[list["<TypeName>FilterInputType"], strawberry.lazy("django_strawberry_framework.filters.inputs")] | None`.

### Error shapes

- `Meta.filterset_class = <non-FilterSet-class>` → [`ConfigurationError`][glossary-configurationerror]("`Meta.filterset_class` must be a `FilterSet` subclass; got `<class>`") at type creation.
- `RelatedFilter("UnknownFilter")` where `"UnknownFilter"` cannot be resolved by Layer 2's module-fallback → [`ConfigurationError`][glossary-configurationerror]("Cannot finalize ... no registered FilterSet named `'UnknownFilter'`") at finalization.
- Cycle-safe expansion exhausts the recursion guard (Layer 4's `_is_expanding_filters` re-entry detection) → [`ConfigurationError`][glossary-configurationerror]("Cycle detected in `FilterSet` related-filter graph; offending class: `<class>`") at finalization.
- `Meta.fields = {"unknown_field": ["exact"]}` where `"unknown_field"` is not a model field → [`ConfigurationError`][glossary-configurationerror]("`<FilterSet>.Meta.fields` references unknown model field: `'unknown_field'`") at type creation.
- `Meta.fields = {"name": ["unsupported_lookup"]}` where the lookup is not registered for the field type → [`ConfigurationError`][glossary-configurationerror]("Lookup `'unsupported_lookup'` not supported for field `'name'` on model `<Model>`") at type creation.
- `filter_input_type(<non-FilterSet>)` → `TypeError("filter_input_type() requires a FilterSet subclass; got <class>")` at call time (the helper is a function, validation runs eagerly even though the returned `Annotated[...]` shape itself is lazy).

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

- `__init__.py` — re-exports `FilterSet`, `RelatedFilter`, `filter_input_type` (the consumer helper per [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper)), and (for advanced uses) `Filter`, `TypedFilter`, `ArrayFilter`, `RangeFilter`, `ListFilter`, `GlobalIDFilter`.
- `base.py` — `Filter`, `TypedFilter`, `ArrayFilter`, `RangeFilter`, `RangeField`, `validate_range`, `ListFilter`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, `RelatedFilter`, `LazyRelatedClassMixin`.
- `sets.py` — `FilterSetMetaclass`, `FilterSet` (with `Meta.model`, `Meta.fields`, `FILTER_DEFAULTS` class attr + `filter_for_field` / `filter_for_lookup` overrides per [Decision 4](#decision-4--upstream-primitives-parity-floor), `apply(input_value, queryset, info)` classmethod per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation) + [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper) (unified resolver-facing API), `get_filters`, `filter_queryset` (the `django-filter` instance-method override for tree-form logic), `check_permissions`, `_apply_related_queryset_constraints`).
- `factories.py` — `FilterArgumentsFactory` (input shape derived from resolved filter instances per H1), `get_filterset_class`, `_dynamic_filterset_cache`. (Note: `FILTER_DEFAULTS` lives in `sets.py` on the `FilterSet` class — corrected per H1; runtime `django-filter` consults `cls.FILTER_DEFAULTS` and the factory consults the resolved filter instances, so the two cannot drift.)
- `inputs.py` — per-module input-class namespace, `build_input_class`, `_build_logic_fields`, `_build_input_fields`, `construct_search`, `LOOKUP_PREFIXES`.

Public re-export from `django_strawberry_framework` is opted-in by the subpackage's `__init__.py`, NOT by the top-level package: consumers `from django_strawberry_framework.filters import FilterSet, RelatedFilter, filter_input_type` (matching the import shape in [`GOAL.md`][goal]'s astronomy showcase). The top-level package's `__all__` is unchanged in `0.0.8` — adding the filter symbols to the top-level surface widens it for every consumer including those who never use filters; the subpackage import path is the right grain.

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

The pre-pinned architectural answer (from the [`KANBAN.md`][kanban] card body's "Recommended architectural direction" block) is borrowed verbatim and preserved here. Five of six layers port from `django-graphene-filters` library-agnostic (with `django_filters.filterset.BaseFilterSet` as the shared foundation per [Decision 5](#decision-5--django-filter-as-the-foundation)); only Layer 5 is Strawberry-adapted, and the Strawberry adaptation is more specific than rev1 suggested per the H1 correction in [`docs/feedback.md`][feedback].

**Layer 1 — Lazy class references in `RelatedFilter`** — port verbatim from `django_graphene_filters/filters.py::BaseRelatedFilter`. `RelatedFilter` accepts target as class, absolute import path string (`"myapp.filters.ManagerFilter"`), or unqualified name (`"ManagerFilter"`). `_filterset` stores it unresolved; the `.filterset` property triggers resolution.

**Layer 2 — Module-fallback resolution** — port verbatim from `django_graphene_filters/mixins.py::LazyRelatedClassMixin.resolve_lazy_class`. Two-step resolution: try as absolute path via `django.utils.module_loading.import_string`; on `ImportError`, retry with `bound_class.__module__` prefix. Handles circular-import scenarios in the same module.

**Layer 3 — Metaclass discovery, deferred expansion** — port pattern from `django_graphene_filters/filterset.py::FilterSetMetaclass`. Metaclass collects `BaseRelatedFilter` declarations into `cls.related_filters`, calls `f.bind_filterset(new_class)` so the module-fallback resolver knows the owning module, and **does not** expand. Expansion is deferred to `get_filters()`.

**Layer 4 — Cycle-safe expansion + cache** — port verbatim from `django_graphene_filters/filterset.py::AdvancedFilterSet.get_filters`. `cls.__dict__["_expanded_filters"]` cache plus `cls.__dict__["_is_expanding_filters"]` recursion guard. Two-condition cache write: `"related_filters" in cls.__dict__` AND no string `_filterset` remaining on any related filter. Breaks `A → B → A` cycles cleanly.

**Layer 5 — BFS schema build with module-global materialization (Strawberry-adapted)** — port the BFS algorithm in `django_graphene_filters/filter_arguments_factory.py::FilterArgumentsFactory._ensure_built` verbatim; the cycle-safe forward reference changes shape because Strawberry's lazy mechanism is module-path-only, NOT object-path. Specifically:

- Strawberry's [`strawberry.types.lazy_type.LazyType.resolve_type`](https://strawberry.rocks) imports the module named in `strawberry.lazy("<module-path>")` and reads `module.__dict__[type_name]`. It does NOT traverse object paths (`module.attr.subattr`) and does NOT look up entries in a dict named `_registry`. Verified by direct inspection of the installed Strawberry; cited in H1 of [`docs/feedback.md`][feedback].
- Consequence: every generated filter input class MUST be a **real module global** of [`django_strawberry_framework.filters.inputs`][filters] (i.e., set via `setattr(sys.modules["django_strawberry_framework.filters.inputs"], name, cls)` or by direct attribute assignment), not an entry in a private dict.
- The Strawberry idiom is `Annotated["{TargetFilterSet}InputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` — a string forward-reference combined with the module-path marker. At schema-build time, Strawberry imports the module, looks up the unquoted name in `module.__dict__`, and resolves the forward reference.
- `FilterArgumentsFactory._ensure_built` produces both halves: it materializes each input class as a module global (via the helper [`materialize_input_class(name, cls)`][filters] in `inputs.py` — two-argument signature; the destination module is always `django_strawberry_framework.filters.inputs` so it is not a parameter, corrected per L2 of [`docs/feedback.md`][feedback]) AND it emits the `Annotated[...]` shape in field annotations so cycle-safe references between filtersets keep working.

Graphene's `graphene.InputField(lambda tn=target_name: input_object_types[tn])` and the new Strawberry idiom (`Annotated["...", strawberry.lazy("...")]` over a module-global namespace) are conceptual twins — both defer the type reference until schema walk; only the lookup mechanism differs (dict-keyed for Graphene; `module.__dict__` keyed for Strawberry).

**Layer 6 — Memoized dynamic FilterSet generation** — port verbatim from `django_graphene_filters/filterset_factories.py::_dynamic_filterset_cache`. Cache keyed by `(model, fields, extra_meta)` for connection fields declared without an explicit `filterset_class`; prevents duplicate-`__name__` collisions when two connection fields target the same model. (This card lands the cache plumbing; the connection-field consumer is `0.0.9`.)

**`Meta.fields = "__all__"` scope** (H7 from [`docs/feedback.md`][feedback]): the shorthand expands to scalar fields plus their default lookups AND each FK / PK column under the conditional `FILTER_DEFAULTS` per [Decision 4](#decision-4--upstream-primitives-parity-floor). Relation traversal under `"__all__"` is **explicitly excluded** — a relation appears in the generated input only when the consumer declares `RelatedFilter(...)` for it. This keeps the non-goal "auto-generation of `FilterSet` from `Meta.fields` without declaring an explicit class" honest: `"__all__"` does NOT silently invent a `ShelfFilter` / `GenreFilter` target class. The narrower scope ports verbatim from `django-filter`'s default `Meta.fields = "__all__"` behavior, which already restricts to direct model fields (not relations).

Justification:

- The cookbook's six-layer architecture is proven (the working reference per [`START.md`][start]); reinventing it would burn schedule for no architectural gain.
- Five of six layers are library-agnostic Python (on top of the shared `django_filters.filterset.BaseFilterSet` per [Decision 5](#decision-5--django-filter-as-the-foundation)) — the port is mechanical, not creative.
- Layer 5's Strawberry adaptation is pinned to the actual Strawberry API (`Annotated["Name", strawberry.lazy("module")]` over module globals); rev1's draft "lazy on `module.path.ClassName`" or "lazy on `module._registry.Name`" cannot work because Strawberry does not traverse object paths or dict lookups.
- `Meta.fields = "__all__"` narrowing keeps the [Non-goals](#non-goals) "no implicit `FilterSet` generation from `Meta.fields`" rule self-consistent — `"__all__"` would otherwise need to invent target filtersets for every relation, which IS auto-generation.

Alternatives considered (and rejected):

- **Design a new lazy-resolution mechanism from scratch.** Rejected: zero benefit over the cookbook's proven architecture; doubles the review surface.
- **Skip Layer 6 (no dynamic-factory plumbing).** Rejected: when [`DjangoConnectionField`][glossary-djangoconnectionfield] lands in `0.0.9`, it would need the cache regardless; lifting it here is cheaper than retrofitting later.
- **Use `typing.ForwardRef` instead of `strawberry.lazy(...)`.** Rejected: Strawberry's documented forward-reference idiom IS `strawberry.lazy(...)`; reaching past Strawberry's API to `typing.ForwardRef` would build on private behavior.
- **Store input classes in a private dict registry and look them up at `LazyType.resolve_type` time via a Strawberry monkey-patch.** Rejected: monkey-patching Strawberry's internals for the sake of preserving rev1's `_registry`-keyed shape is a maintenance hazard; using Strawberry's documented module-globals path is the cleaner shape.
- **`Meta.fields = "__all__"` auto-generates a default `<Target>Filter` for every relation it touches.** Rejected per H7 of [`docs/feedback.md`][feedback]: this is the "implicit `FilterSet` generation" path the [Non-goals](#non-goals) section excludes; relations must come through explicit `RelatedFilter` declarations.

### Decision 4 — Upstream-primitives parity floor

The package ships parity equivalents for every verified upstream filter primitive named in the [`KANBAN.md`][kanban] card body:

- `ArrayFilter(TypedFilter)`, `ArrayFilterMethod(FilterMethod)` (from `graphene_django/filter/filters/array_filter.py`).
- `RangeFilter(TypedFilter)`, `RangeField(Field)`, `validate_range` (from `graphene_django/filter/filters/range_filter.py`).
- `ListFilter(TypedFilter)`, `ListFilterMethod(FilterMethod)` (from `graphene_django/filter/filters/list_filter.py`).
- `TypedFilter(Filter)` (from `graphene_django/filter/filters/typed_filter.py`) — base class for the four above.
- `GlobalIDFilter(Filter)`, `GlobalIDMultipleChoiceFilter(MultipleChoiceFilter)` (from `graphene_django/filter/filters/global_id_filter.py`).

The `FILTER_DEFAULTS` map is a **class attribute on the package `FilterSet`** (not a factory-side parallel map) so the `django-filter` runtime AND the Strawberry input factory agree on the chosen filter primitive. The mapping is **conditional on the target `DjangoType`'s Relay shape** — corrected per H1 + H4 in [`docs/feedback.md`][feedback]:

- FK / PK whose target `DjangoType` implements `relay.Node` (per `Meta.interfaces = (relay.Node,)`, shipped in `DONE-011-0.0.5`) → `GlobalIDFilter` (the Relay-`GlobalID`-aware primitive); the filter input accepts the Strawberry `relay.GlobalID` string shape, the factory decodes it back to the underlying PK before applying the queryset filter.
- FK / PK whose target `DjangoType` is **non-Relay** (the default — most `DjangoType`s today, e.g., `ShelfType` in the fakeshop library app) → the scalar PK filter derived from the target PK column's Django scalar conversion (per [`django_strawberry_framework/types/converters.py::SCALAR_MAP`][filters]); the filter input accepts the raw PK value (typically `int`, sometimes `uuid.UUID` or `BigInt`).

**Where the conditional runs.** Per H1 of [`docs/feedback.md`][feedback], rev2's "the lookup runs inside `FilterArgumentsFactory._ensure_built`" placement was wrong: `_ensure_built` only controls the Strawberry input shape, while `django-filter` instantiates the actual filter instances earlier via `filterset.BaseFilterSet.filter_for_field()` / `filter_for_lookup()`, which read `cls.FILTER_DEFAULTS`. A factory-only conditional would let the GraphQL input expose `relay.GlobalID` for `BookFilter.genres` while the runtime filter instance is whatever vanilla `django-filter` generated — wire-shape disagreement at the queryset translation step. The corrected shape:

- `FilterSet.FILTER_DEFAULTS` is the same dict shape `django-filter` consumes (`{django.db.models.Field: {"filter_class": ..., "extra": ...}}`).
- `FilterSet.filter_for_field(cls, field, field_name, lookup_expr)` and `FilterSet.filter_for_lookup(cls, field, lookup_type)` override the cookbook ancestors. For relation fields, they consult `registry.get(target_model)` (the model-to-`DjangoType` registry from [`Meta.primary`][glossary-metaprimary]) to find the primary target `DjangoType`, then check `implements_relay_node(target_type)` (the same predicate used by [`finalize_django_types`][finalizer]'s phase 2.5 Relay-Node injection) to pick the `GlobalIDFilter` branch vs the scalar PK branch.
- The chosen filter primitive lands in the FilterSet's `declared_filters` / `base_filters` via the standard `django-filter` machinery. `get_filters()` (Layer 4 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)) expands them with the cycle-safe guard.
- `FilterArgumentsFactory._ensure_built` derives the Strawberry input field type **from the resolved filter instances** (`type(filter_instance).input_type` — or whatever attr the per-primitive port exposes), NOT from a parallel `FILTER_DEFAULTS` lookup. The input shape is downstream of the filter shape, so the two cannot drift.

**Why this matters.** Rev1's blanket "FK/PK → `GlobalIDFilter`" mapping (mirroring `graphene-django`'s unconditional shape) would have broken non-Relay filters: a consumer filtering `Book.shelf` by ID against a non-Relay `ShelfType` would have to pass a GlobalID-encoded string even though the exposed GraphQL type uses an integer ID — a wire-shape mismatch the consumer would discover at the first query. `graphene-django`'s filter-connection-path defaults are unconditional because that path Relay-shapes by construction (its `DjangoFilterConnectionField` always returns a Relay connection); but `graphene-django`'s `DjangoObjectType` itself supports non-Relay shapes too — the unconditional `GlobalIDFilter` is specifically tied to the filter-connection path's defaults, not the framework as a whole (per L4 of [`docs/feedback.md`][feedback]). The package's default is non-Relay (`Meta.interfaces = (relay.Node,)` is opt-in), and the package's filter surface is the FilterSet itself (not a connection-field wrapper yet — that's `0.0.9`), so the conditional shape matches the actual GraphQL surface the consumer sees.

**Name-collision note:** `graphene_django/filter/utils.py::get_filterset_class` and `django_graphene_filters/filterset_factories.py::get_filterset_class` are different functions with the same name. The card body's "Verified upstream factory machinery" section flags this; this card mirrors the cookbook's shape (the `BaseFilterSet`-aware get-or-create helper), NOT graphene-django's shape (the explicit-vs-dynamic dispatcher). Reason: the cookbook's `get_filterset_class` is the entry point the BFS factory uses; graphene-django's is a different shape pinned to connection-field declaration. We need the cookbook's, the connection field needs neither in `0.0.8`.

Justification:

- ⚛️ parity (the package's positioning claim) requires shipping equivalents for each parity-floor primitive; absence in the first ship is the kind of gap that bites consumers immediately.
- Each primitive is short (~30–80 lines); the cost of porting all five plus `FILTER_DEFAULTS` is much smaller than the cost of explaining why the package is missing one.

Alternatives considered (and rejected):

- **Ship only `GlobalIDFilter` in `0.0.8`; defer the four `TypedFilter` subclasses.** Rejected: half-shipping the parity floor invites the same churn as not shipping at all; consumers hit the gap immediately.
- **Ship the parity floor under different symbol names (e.g., `DSTArrayFilter`).** Rejected: the upstream naming is the consumer's mental model; renaming for no architectural gain creates friction.

### Decision 5 — `django-filter` as the foundation

The package's `FilterSet` **subclasses `django_filters.filterset.BaseFilterSet`** and `django-filter` remains a **hard dependency** at [`pyproject.toml #"django-filter>=25.2"`][pyproject]. The cookbook's `AdvancedFilterSet` is built on `django_filters.filterset.BaseFilterSet` and reuses its load-bearing machinery (`declared_filters`, `base_filters`, `.filters`, `.form`, `.qs`, `get_filters()`, `Filter.method`, form cleaning, lookup generation); porting the cookbook verbatim without that inheritance would mean re-implementing all of those layers, which is a large net-new surface for zero gain when the dependency is already locked in [`pyproject.toml`][pyproject].

This Decision is a reversal of rev1's "drop the soft-dep" stance — corrected per H3 in [`docs/feedback.md`][feedback]. Rev1's posture contradicted three load-bearing facts:

1. [`pyproject.toml #"django-filter>=25.2"`][pyproject] already pins `django-filter` as a hard runtime dep.
2. [`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`][goal-migration-shape] explicitly promises "the existing `django_filters.FilterSet` plugs into `Meta.filterset_class` directly" — a direct migration path that requires `FilterSet` to be a `BaseFilterSet`.
3. The cookbook's `django_graphene_filters/filterset.py::AdvancedFilterSet` IS a `django_filters.filterset.BaseFilterSet` subclass at load-bearing layers; the spec's "five of six layers port verbatim" claim only holds when those layers ride on `BaseFilterSet`.

Justification:

- The dep is already on the lock file. The cost of removing it is updating [`pyproject.toml`][pyproject], the [`GOAL.md`][goal] promise, the [`README.md`][readme] migration narrative, and any consumer-facing claim that a `django_filters.FilterSet` plugs in directly — a fan-out that nothing in [Goals](#goals) requires.
- The cost of keeping it is one line of inheritance, plus the cookbook's import path. Pinned shape (H3 of [`docs/feedback.md`][feedback] flagged that `django_filters.BaseFilterSet` does NOT exist at the top-level import path — the class lives at `django_filters.filterset.BaseFilterSet`):

  ```python
  from django_filters import filterset

  class FilterSetMetaclass(filterset.FilterSetMetaclass):
      ...

  class FilterSet(filterset.BaseFilterSet, metaclass=FilterSetMetaclass):
      ...
  ```

  An implementer who reaches for `from django_filters import BaseFilterSet` or `class FilterSet(django_filters.BaseFilterSet, ...):` gets an `ImportError` at module import — the cookbook's `from django_filters import filterset` + `filterset.BaseFilterSet` shape is the documented one and the only path that actually resolves.
- Consumer migration shape stays simple: a consumer who has `class MyFilter(django_filters.FilterSet)` today writes `class MyFilter(FilterSet)` after the upgrade (changing the parent class), and inherits the package's `RelatedFilter` / lazy-resolution surface for free. The cookbook's pattern is the same.
- The `django-filter` install surface is uncomplicated: `django-filter>=25.2` ships clean on every supported Python / Django combo the package targets; no `ImportWarning` branch is required because the dep is hard, not soft.

Alternatives considered (and rejected):

- **Drop `django-filter` entirely; re-implement `BaseFilterSet` machinery in the package.** Rejected per H3: re-implementing `BaseFilterSet`, `Filter`, `MultipleChoiceFilter`, `FilterMethod`, form cleaning, lookup generation, and `.qs` is a large net-new code surface for zero functional gain; the dep is already in the lock file and the cookbook's port relies on it.
- **Soft-dep on `django-filter` (`ImportError` branch on first `FilterSet` declaration).** Rejected: the dep is already hard; a soft-dep would surface an `ImportWarning` every import time and add a branch to test against; consumers who don't filter would still pay the warning surface.
- **Accept either a package-`FilterSet` or a `django_filters.FilterSet` at `Meta.filterset_class`.** Rejected: two consumer-facing surfaces for the same wiring create ambiguity about which `check_*_permission` shape applies and which lazy-resolution mechanism runs. The single package `FilterSet` (which IS a `django_filters.filterset.BaseFilterSet` via inheritance) is the boundary class; consumers convert via parent-class swap, not via dual acceptance.

### Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering

The filter subsystem's lazy-resolution pipeline runs inside [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer]'s phase 2.5, immediately after the existing `apply_interfaces` / `install_relay_node_resolvers` loop and before phase 3's `strawberry.type` decoration. For each `DjangoType` with `definition.filterset_class is not None`:

1. Validate `filterset_class` is a `FilterSet` subclass (raise [`ConfigurationError`][glossary-configurationerror] otherwise).
2. Call `filterset_cls.get_filters()` to trigger Layer-4 expansion (resolves lazy refs, expands related filters with cycle guards).
3. Call `FilterArgumentsFactory(filterset_cls).arguments` to trigger Layer-5 BFS (builds every reachable `strawberry.input`-decorated class).
4. **Materialize each built class as a real module global** of [`django_strawberry_framework.filters.inputs`][filters] via the helper `materialize_input_class(name, cls)`. The helper sets `sys.modules["django_strawberry_framework.filters.inputs"].<name> = cls` and records `name → filterset_class` provenance in the lifecycle ledger (per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)). Materialization is what makes the `Annotated["Name", strawberry.lazy("django_strawberry_framework.filters.inputs")]` references on consumer resolver signatures resolvable at `strawberry.Schema(...)` time — Strawberry's `LazyType.resolve_type` imports the named module and reads `module.__dict__[name]`, so the class MUST exist as a module global by then per H1 in [`docs/feedback.md`][feedback].

By phase 3, when `strawberry.type(cls, ...)` runs on the `DjangoType`, every referenced filter input class is a module global of `django_strawberry_framework.filters.inputs`. By `strawberry.Schema(query=Query, ...)` time, every `filter:` argument annotation on a `@strawberry.field`-decorated root resolver (introduced via `filter_input_type(FilterSet)` per [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper)) resolves cleanly through `LazyType.resolve_type`.

Materialization MUST land before `strawberry.Schema(...)` runs — this is the ordering contract corrected per H2 in [`docs/feedback.md`][feedback]. Rev1 assumed the binding pass would inject arguments into existing `@strawberry.field` resolvers after the fact, but Strawberry collects field arguments at `@strawberry.type` decoration time (well before `finalize_django_types()` runs), so injection-after-collection is not a real path. The corrected ordering is: resolvers use `filter_input_type(FilterSet)` (a string forward reference) at module-load time → `@strawberry.type` collects the lazy annotation → `finalize_django_types()` runs and materializes the input class as a module global → `strawberry.Schema(query=Query, ...)` resolves the lazy reference via `LazyType.resolve_type` → schema build succeeds. The package-recommended call ordering in [`docs/README.md`'s Schema setup boundary][docs-readme] already pins `finalize_django_types()` before `strawberry.Schema(...)`; this card adds the materialization step under that ordering without changing the consumer-facing call sequence.

Justification:

- Phase 2.5 is already the synchronization seam for `DONE-011-0.0.5`'s Relay-Node injection; threading the filter binding through the same loop keeps the finalizer's phase ordering coherent.
- Materializing classes as module globals (not as dict entries in a separate registry) matches Strawberry's actual `LazyType.resolve_type` semantics; H1 in [`docs/feedback.md`][feedback] verified by direct inspection of the installed Strawberry that dict-keyed registries are not reachable through `strawberry.lazy(...)`.
- The pending-relation registry's record-now-resolve-at-finalization pattern (used for model relations) reuses cleanly for lazy related-filter class references; the `LazyRelatedClassMixin` equivalent reuses the same fail-loud error format ("Cannot finalize ... no registered ...") that the model-relation finalizer already produces.
- Calling `finalize_django_types()` twice is still a no-op via the existing `registry.is_finalized()` guard; the new filter-binding pass is idempotent because (a) materialization is keyed by `(name, filterset_class)` provenance — re-materializing the same `(name, filterset_class)` pair is a no-op, and (b) re-materializing the same `name` from a DIFFERENT `filterset_class` raises [`ConfigurationError`][glossary-configurationerror] per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- Partial-finalize lifecycle: if phase 2.5 raises mid-iteration (e.g., an unresolved `RelatedFilter`), `registry.mark_finalized()` is never reached, the lifecycle ledger keeps the partial state, and a subsequent `finalize_django_types()` call resumes the binding pass; the idempotency contract above ensures a clean rerun. `registry.clear()` clears the lifecycle ledger AND removes the materialized module globals (the lifecycle clause in [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) pins this), so test-fixture reload patterns (e.g., the one [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] uses) reset the filter subsystem in the same step.

Alternatives considered (and rejected):

- **Run filter binding in phase 2 alongside `_attach_relation_resolvers`.** Rejected: filter binding depends on Relay-Node setup (because Relay-aware filters require the `GlobalIDFilter` mapping established in `0.0.5`); phase 2 runs before Relay setup, so binding would land in the wrong order.
- **Run filter binding in a new phase 2.75.** Rejected: invents an extra phase number for one capability; the existing 2.5 is the right grain.
- **Run filter binding at `DjangoType.__init_subclass__` instead of at finalization.** Rejected: `RelatedFilter("CelestialBodyFilter")` cannot be resolved at class-creation time because the target filterset's module may not have been imported yet — same definition-order-independence constraint that `DONE-009-0.0.4` solved for model relations.
- **Inject `filter:` argument into existing root resolvers' Strawberry field metadata after finalize.** Rejected per H2: Strawberry collects field arguments at `@strawberry.type` decoration time; injection-after-collection would require either monkey-patching Strawberry internals or invalidating already-decorated `Query` types. The corrected shape uses `filter_input_type(FilterSet)` on the resolver signature at module-load time (per [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper)) so Strawberry collects the lazy reference naturally.

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
- **Keep the key in `DEFERRED_META_KEYS` until `DjangoConnectionField` ships in `0.0.9`.** Rejected: the connection field is the second consumer; root-list resolvers can call `FilterSet.apply(...)` themselves in the meantime, and the live HTTP coverage in Slice 4 exercises that path.

### Decision 8 — Relation-permission cascade + `get_queryset` cooperation

A `FilterSet`'s `check_<field>_permission(request)` gate composes with the target type's [`get_queryset`][glossary-get_queryset-visibility-hook] hook and with `RelatedFilter`'s `_apply_related_queryset_constraints` (the explicit `queryset=` parameter on a related filter that nested filters cannot bypass). The composition flows through the unified `FilterSet.apply(input_value, queryset, info)` classmethod per [H2 of `docs/feedback.md`][feedback]:

1. The consumer resolver calls `DjangoType.get_queryset(queryset, info)` first on the consumer-shaped root queryset — visibility scoping happens before any filter clauses.
2. The consumer resolver then calls `FilterSet.apply(input_value, queryset, info)`. Internally, `apply` normalizes the Strawberry input dataclass (walking nested `RelatedFilter` input objects, mapping `and_` / `or_` / `not_` Python attrs back to the logical-operator keys, flattening per-field lookup pairs) into the form-data dict `django-filter` expects.
3. `apply` extracts `request = info.context.request` (or `info.context` directly when the consumer's request adapter does not wrap it) and instantiates `cls(data=normalized_data, queryset=queryset, request=request)`.
4. `apply` calls `cls.check_permissions(input_value, request)` — denial gates raise `GraphQLError` before any filter clause touches the queryset. The check recurses through `RelatedFilter`s into child filtersets' `check_*_permission` methods (cookbook's `AdvancedFilterSet.check_permissions` shape).
5. `django-filter`'s form-validation pass runs over `cls.form` (the `cleaned_data` step), and for each `RelatedFilter` in the input, the related queryset is bounded by the `queryset=` parameter (if declared) BEFORE the child filterset's clauses apply (cookbook's `_apply_related_queryset_constraints` shape; **note** that this filters the PARENT queryset via `parent_qs.filter(<rel>__in=<constraint_qs>)`, NOT the nested relation resolver's output — see [H4 follow-up below](#h4-related-queryset-boundary-scope)).
6. The instance's `.qs` property runs `cls.filter_queryset(self, queryset)` (the `django-filter` instance-method override; the tree-form-logic application path) and returns the final queryset. `apply` returns `cls(..).qs` to the resolver.
7. The optimizer ([`DjangoOptimizerExtension`][glossary-djangooptimizerextension]) walks the selection tree on the post-filter queryset; [Queryset diffing][glossary-queryset-diffing] cooperates with any consumer `select_related` / `prefetch_related` work already present.

<a id="h4-related-queryset-boundary-scope"></a>**H4 follow-up — `_apply_related_queryset_constraints` scope.** The cookbook's `_apply_related_queryset_constraints` filters the parent queryset using `parent_qs.filter(<related_name>__in=<constraint_qs>)`. It does NOT filter the nested relation resolver's output. Per H4 of [`docs/feedback.md`][feedback], that means a `Branch` row with one shelf inside the constraint AND one shelf outside the constraint will pass the parent `Branch` filter and still surface BOTH shelves through `BranchType.shelves` (which is a consumer-authored resolver that runs after queryset filtering). The contract this card pins is: "branches without any matching constrained shelf are excluded from the parent result; nested filter clauses cannot use shelves outside the constraint to make a branch match." It is **not** "shelves outside the constraint never appear in the response." Output-shape scoping at the nested-relation level would require either rewriting consumer relation resolvers or extending the optimizer's `Prefetch` planner to honor a per-relation constraint — both are out of scope for `0.0.8`; tracked as a follow-up if real consumer demand surfaces.

Forward composition contract: when [`apply_cascade_permissions`][glossary-apply_cascade_permissions] ships in `0.0.10`, it slots into step 1 (the `get_queryset` hook); when [Per-field permission hooks][glossary-per-field-permission-hooks] ship, they slot into the field-resolver layer that runs AFTER step 5 (queryset traversal completes before field resolvers fire). The five layers compose without retrofit.

Justification:

- Visibility-before-filter is the security-correct ordering: filtering inside a queryset that hasn't been scoped to the request's user would let a nested filter "see through" the visibility gate (compute `WHERE name LIKE '%admin%'` against rows the user shouldn't see).
- The cookbook's `_apply_related_queryset_constraints` is the precedent for the related-filter `queryset=` boundary; this card ports it verbatim.
- The optimizer cooperation is already documented in [Queryset diffing][glossary-queryset-diffing] — a `.filter(...)` call on the consumer queryset doesn't change the cooperation contract because the optimizer reconciles against whatever queryset shape the resolver returns.

Alternatives considered (and rejected):

- **Apply filters first, then `get_queryset`.** Rejected: security-incorrect ordering per the reasoning above.
- **Skip step 4 (let nested filters override the `queryset=` boundary).** Rejected: defeats the cookbook's documented security feature; the boundary's whole point is to be inviolable.

### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle

The card body's "Decide whether the input-type factory's namespace shares the `TypeRegistry` or has its own" question is answered: **the input-class namespace is the [`django_strawberry_framework.filters.inputs`][filters] module's own global namespace**, separate from the model-to-`DjangoType` registry at [`django_strawberry_framework.registry.registry`][registry] (which powers [`Meta.primary`][glossary-metaprimary]).

Implementation: every generated filter input class is a real module global of `django_strawberry_framework.filters.inputs`, set at finalize time via `setattr(sys.modules["django_strawberry_framework.filters.inputs"], name, cls)`. The class names are stable and class-derived (e.g., `f"{FilterSet.__name__}InputType"` → `"GalaxyFilterInputType"`). The "registry" IS the module's `__dict__` — there is no separate `_input_type_registry: dict[str, type]`, because Strawberry's `LazyType.resolve_type` reads `module.__dict__` directly and cannot traverse a sidecar dict (verified per H1 of [`docs/feedback.md`][feedback]). A lifecycle ledger (a private `dict[str, type[FilterSet]]` at `django_strawberry_framework.filters.inputs._materialized_names`) tracks `class_name → filterset_class` provenance so re-materialization is idempotent and clears cleanly.

This Decision corrects rev1's `_registry` dict shape per H1 of [`docs/feedback.md`][feedback]: the registry must coincide with the module's global namespace because Strawberry's lazy mechanism is module-path-only, not object-path. The two namespaces (model-to-`DjangoType` registry and input-class module globals) remain disjoint by key type (Django model class vs string class name).

Lifecycle contract (corrected per H5 of [`docs/feedback.md`][feedback]):

- **Registration is idempotent for the same `(name, filterset_class)` pair.** Calling `materialize_input_class("GalaxyFilterInputType", cls_a)` twice with the same `cls_a` is a no-op; the second call neither raises nor reassigns the module global.
- **Registration raises [`ConfigurationError`][glossary-configurationerror] when the same name is claimed by a DIFFERENT filterset class.** `materialize_input_class("GalaxyFilterInputType", cls_a)` followed by `materialize_input_class("GalaxyFilterInputType", cls_b)` raises with both classes' qualified names in the message. This catches accidental duplicate-`__name__` collisions between two `FilterSet`s declared in different modules.
- **`registry.clear()` (the model-to-`DjangoType` registry's clear) clears the filter input lifecycle ledger and removes every materialized class from the module's global namespace.** The shared clear point lets test-fixture reload patterns reset both subsystems in one call. The clear walks `_materialized_names.items()` and `delattr(sys.modules["django_strawberry_framework.filters.inputs"], name)` for each, then resets the ledger to `{}`.
- **Import-cycle-safe integration** (M5 of [`docs/feedback.md`][feedback]). [`django_strawberry_framework/registry.py`][registry] is a low-level module imported by `types/`, `optimizer/`, and the package's `__init__.py`; a top-level `from django_strawberry_framework.filters.inputs import clear_filter_input_namespace` at the top of `registry.py` would create a cycle (`filters/inputs.py` already imports `exceptions.ConfigurationError` and may import `registry` helpers as the subsystem grows). The integration uses **a local import inside `TypeRegistry.clear()`** — the import resolves at clear-time, when the filter subsystem has either been loaded by the consumer (in which case the import is free) or never used (in which case clearing it is a no-op the local import handles gracefully):

  ```python
  # django_strawberry_framework/registry.py
  class TypeRegistry:
      def clear(self) -> None:
          self._reset_state()
          try:
              from django_strawberry_framework.filters.inputs import (
                  clear_filter_input_namespace,
              )
          except ImportError:
              # Filter subsystem not loaded; nothing to clear.
              return
          clear_filter_input_namespace()
  ```

  A package test imports `django_strawberry_framework.registry` alone (before importing `django_strawberry_framework.filters`) and verifies `registry.clear()` runs without `ImportError` — pinning the import-cycle-safe contract.
- **Partial-finalize recovery.** If `finalize_django_types()` raises mid-phase-2.5 (e.g., an unresolved `RelatedFilter`), the lifecycle ledger and the module globals retain whatever was materialized before the raise. A subsequent `finalize_django_types()` call re-runs the binding pass; the idempotent `(name, filterset_class)` check above lets already-materialized classes pass through cleanly while the failed type's binding completes on the retry.
- **Public `clear_filter_input_namespace()` helper.** Exposed from `django_strawberry_framework.filters.inputs` so tests that need to clear the filter namespace WITHOUT clearing the full `TypeRegistry` (e.g., when validating partial-finalize recovery) have a dedicated entry point. `registry.clear()` calls this helper internally.

Justification:

- The `TypeRegistry` is the model-to-`DjangoType` mapping that powers [`Meta.primary`][glossary-metaprimary] / `registry.get(model)` / `registry.types_for(model)`; mixing string-keyed input-class entries into the same dict would weaken the type contract.
- The input-class names are stable and class-derived (e.g., `f"{FilterSet.__name__}InputType"`); two connection fields targeting the same model resolve to the same `FilterInputType` (Apollo cache friendly) without registry collision.
- Sibling Layer-3 subsystems ([`OrderSet`][glossary-orderset] for [`WIP-ALPHA-022-0.0.8`][kanban], [`AggregateSet`][glossary-aggregateset] for `0.1.3`) need their own per-subsystem input-class namespaces; collapsing them into the `TypeRegistry` would put four heterogeneous namespaces in one place. Per-subsystem (each in its own module's globals) keeps responsibilities scoped and matches Strawberry's actual `LazyType.resolve_type` semantics.
- `Meta.primary`'s ambiguity rules (`primary_for(model)`, `types_for(model)`) are model-keyed; the input-class namespace is name-keyed; no read-time predicate from one needs to walk the other.
- The lifecycle clauses above mean a `tests/filters/` test that constructs a `FilterSet`, calls `finalize_django_types()`, asserts behavior, calls `registry.clear()`, and rebuilds with a different filterset shape works correctly; the materialized globals from the first build don't leak into the second.

Alternatives considered (and rejected):

- **Sidecar `_input_type_registry: dict[str, type]` in `filters.inputs`.** Rejected per H1 of [`docs/feedback.md`][feedback]: Strawberry's `LazyType.resolve_type` cannot reach into a dict; the registry must coincide with the module's global namespace.
- **Single shared `TypeRegistry` mapping both `model → DjangoType` and `name → input_class`.** Rejected: heterogeneous key types weaken the contract; sibling Layer-3 subsystems would force the same dict to grow more axes; and Strawberry's lazy mechanism still requires module globals regardless.
- **Per-`DjangoType` input-class namespace (attached as `definition.filter_input_types`).** Rejected: connection fields with `_dynamic_filterset_cache`-generated filtersets don't have a stable `DjangoType` to attach to; the per-module namespace is the natural shape and matches Strawberry's `strawberry.lazy("module-path")` lookup.
- **Per-app input-class namespace (Django-app-scoped).** Rejected: Strawberry schemas span Django apps; the namespace's scope is the Strawberry schema, not the Django app.
- **No clear contract — let test fixtures recover ad hoc.** Rejected per H5 of [`docs/feedback.md`][feedback]: a partial-finalize failure plus a fakeshop schema reload would collide on the existing materialized name; the lifecycle clauses above are what make rerun and reload deterministic.

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

### Decision 11 — `filter_input_type(FilterSet)` consumer helper

Added per H2 of [`docs/feedback.md`][feedback]. The package ships a small public helper at [`django_strawberry_framework.filters.filter_input_type`][filters]:

```python
from typing import Annotated, TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from django_strawberry_framework.filters import FilterSet


def filter_input_type(filterset_class: type["FilterSet"]) -> object:
    """Return the Annotated[...] forward-reference for the filterset's GraphQL input class.

    The returned annotation is the canonical Strawberry forward-reference
    idiom: ``Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]``.
    Consumer resolvers use it as the type annotation for a ``filter:`` argument; Strawberry
    collects the annotation at @strawberry.type decoration time, defers resolution, and
    resolves it via LazyType.resolve_type at schema-build time — by which point
    finalize_django_types() has materialized the input class as a module global of
    django_strawberry_framework.filters.inputs (per Decision 6).
    """
    # Validation runs eagerly even though the returned annotation is lazy.
    from django_strawberry_framework.filters.sets import FilterSet
    if not (isinstance(filterset_class, type) and issubclass(filterset_class, FilterSet)):
        raise TypeError(
            "filter_input_type() requires a FilterSet subclass; got "
            f"{filterset_class!r}"
        )
    name = f"{filterset_class.__name__}InputType"
    return Annotated[name, strawberry.lazy("django_strawberry_framework.filters.inputs")]
```

Consumers use it as a normal Python type annotation in a resolver signature:

```python
@strawberry.field
def all_galaxies(
    self,
    info: strawberry.Info,
    filter: filter_input_type(GalaxyFilter) | None = None,
) -> list[GalaxyType]:
    ...
```

`filter_input_type(GalaxyFilter)` evaluates **when Strawberry evaluates the annotation during schema declaration / collection** (the function body runs, validation succeeds, and the `Annotated[...]` shape is returned). The exact evaluation moment depends on the consumer's import style — with normal annotations the call evaluates at module-load time; with `from __future__ import annotations` Python stores the expression as a string and Strawberry evaluates it lazily during type/field processing, potentially more than once (per L3 of [`docs/feedback.md`][feedback]). Either way, the `"GalaxyFilterInputType"` string forward-reference inside the `Annotated[...]` stays unresolved until `strawberry.Schema(...)` time — which is when `finalize_django_types()` has already materialized the class as a module global per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering).

Justification:

- Without a helper, consumers would have to spell out `Annotated["GalaxyFilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` directly on every resolver — a long incantation that ties consumer code to the package's internal module path and bypasses the validation gate.
- A helper-returned `Annotated[...]` is the only consumer-facing shape that satisfies all three requirements: (a) it's a real Python annotation Strawberry collects at `@strawberry.type` time; (b) it defers resolution to schema-build time; (c) it points at a module Strawberry can import to resolve via `module.__dict__[name]`.
- The eager validation (`TypeError` at call time for a non-`FilterSet`) catches misuse at the resolver-declaration site instead of letting Strawberry surface a more cryptic schema-build-time error.
- The helper is mechanical: ~15 lines, no state, returns a value. Adding it costs nothing; not shipping it forces every consumer to spell out the underlying shape and learn the module path. The forward-compatibility shape for [`DjangoConnectionField`][glossary-djangoconnectionfield] in `0.0.9` (which accepts `filterset_class=` and owns the wiring internally) uses the same `filter_input_type(FilterSet)` helper under the hood.

Alternatives considered (and rejected):

- **No helper; consumers spell out `Annotated[...]` themselves.** Rejected: ties consumer code to the package's internal module path; bypasses validation; not the package's `Meta`-driven shape.
- **Helper returns `<Name>FilterInputType` directly (a class).** Rejected: the class doesn't exist yet at module-load time — it's materialized later by `finalize_django_types()`. Returning a class at module-load time would force the helper to eagerly run the finalizer, which contradicts the definition-order-independence contract.
- **Helper is a method on `FilterSet`: `GalaxyFilter.input_type()`.** Rejected: viable shape, but adds class-method surface to every `FilterSet` for the sake of one call site per resolver. The module-level function form is the smaller import and the more discoverable doc entry.
- **Defer the helper to `0.0.9` (`DjangoConnectionField` accepts `filterset_class=` directly).** Rejected: `0.0.8` consumers cannot wait for `0.0.9` to expose a working `filter:` argument; this card's [Goals](#goals) item 5 ("expose introspection for what filter surface a type supports") requires a consumer-facing path right now, not next patch.

### Decision 12 — Live HTTP coverage strategy

Package coverage is earned through fakeshop live `/graphql/` HTTP flows where practical per the [`docs/TREE.md`][tree] coverage-priority rule ("Any package coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against fakeshop MUST be earned in `examples/fakeshop/test_query/`").

Live HTTP tests (Slice 4) land in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] and cover: scalar-field filter clauses, choice-enum filter clauses, forward-FK filter clauses, reverse-FK filter clauses, M2M filter clauses, logical-and / logical-or / logical-not combinations, optimizer cooperation (`assertNumQueries(N)` against a filtered queryset with nested selection), and the `_apply_related_queryset_constraints` security boundary.

Package-internal tests (`tests/filters/`) land in five mirror files (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`, plus `__init__.py` shell). Each file covers what the live HTTP path cannot easily reach: cycle-safe expansion via `_is_expanding_filters` recursion guard, `_dynamic_filterset_cache` hit/miss behavior, `LazyRelatedClassMixin.resolve_lazy_class` two-step resolution failure paths, `FILTER_DEFAULTS` Relay-vs-scalar branch selection (Relay-Node targets → `GlobalIDFilter`; non-Relay targets → scalar PK filter — per [Decision 4](#decision-4--upstream-primitives-parity-floor)), `LOOKUP_PREFIXES` map for `construct_search`, [`ConfigurationError`][glossary-configurationerror] surface for invalid `Meta.fields`, etc.

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
| 1 — Foundation (`base.py` + `sets.py` skeleton, including `FILTER_DEFAULTS` + `filter_for_field`/`filter_for_lookup` overrides + `FilterSet.apply` classmethod) | [`django_strawberry_framework/filters/__init__.py`][filters], [`django_strawberry_framework/filters/base.py`][filters], [`django_strawberry_framework/filters/sets.py`][filters], [`django_strawberry_framework/filters/inputs.py`][filters] (skeletons), [`tests/filters/__init__.py`][test-filters] (new), [`tests/filters/test_base.py`][test-filters] (new), [`tests/filters/test_sets.py`][test-filters] (new) | ~30 (filter-primitive shapes, `RelatedFilter` accepts class/string/unqualified, `FilterSet` rejects unknown `Meta.fields`, `FilterSet.FILTER_DEFAULTS` Relay-vs-scalar branch selection at filter-instance time, `FilterSet.apply` classmethod normalizes Strawberry input into form-data and returns `.qs`) | `+950 / -0` |
| 2 — Factories (`factories.py` BFS + dynamic cache + inputs adapters; input shape derived from filter instances) | [`django_strawberry_framework/filters/factories.py`][filters] (new), [`django_strawberry_framework/filters/inputs.py`][filters] (extend), [`tests/filters/test_factories.py`][test-filters] (new), [`tests/filters/test_inputs.py`][test-filters] (new) | ~20 (`FilterArgumentsFactory` BFS walks `filterset_cls.get_filters()`, `_dynamic_filterset_cache` hit/miss, `LOOKUP_PREFIXES` map, logical-and/or/not field generation, factory and FilterSet runtime agree on filter primitive for Relay AND non-Relay targets) | `+650 / -0` |
| 3 — Wiring (`Meta.filterset_class` promotion + finalizer phase-2.5 binding + lifecycle helpers) | [`django_strawberry_framework/types/base.py`][base] (`DEFERRED_META_KEYS` → `ALLOWED_META_KEYS` move + validation), [`django_strawberry_framework/types/definition.py`][definition] (add `filterset_class` slot), [`django_strawberry_framework/types/finalizer.py`][finalizer] (phase 2.5 grows the filter-binding pass), [`django_strawberry_framework/filters/inputs.py`][filters] (add `materialize_input_class` + `clear_filter_input_namespace` + `_materialized_names` ledger), [`django_strawberry_framework/registry.py`][registry] (`clear()` invokes `clear_filter_input_namespace()`), [`tests/types/test_base.py`][test-types] (validator extension), [`tests/types/test_definition_order.py`][test-types] (extend), `tests/filters/test_finalizer.py` (new) | ~20 (validator accepts/rejects, phase-2.5 binding runs, idempotent rerun, partial-finalize recovery, `registry.clear()` co-clear, lazy-related-filter resolution at finalize) | `+320 / -5` |
| 4 — Live HTTP coverage in fakeshop | [`examples/fakeshop/apps/library/filters.py`][fakeshop-library] (new, carrying `BranchFilter` / `ShelfFilter` / `BookFilter` / `LoanFilter` / `PatronFilter`), [`examples/fakeshop/apps/library/filters_genre.py`][fakeshop-library] (new, carrying `GenreFilter` — cross-module fixture for the Layer-2 absolute-import-path test), [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (extend with `Meta.filterset_class` + `filter_input_type(...)` annotations on root resolvers), [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (extend) | 9 (scalar / choice-enum / non-Relay-FK scalar PK / Relay-M2M GlobalID / reverse-FK / logical / optimizer cooperation / related-queryset parent-scope boundary via `Shelf.topic` / cross-module absolute-path `RelatedFilter`) | `+260 / -10` |
| 5 — Docs + KANBAN + CHANGELOG | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`README.md`][readme], [`TODAY.md`][today], [`KANBAN.md`][kanban], [`CHANGELOG.md`][changelog] | 0 | `+80 / -25` |
| 6 — Composition smoke test with sibling ordering card | [`tests/filters/test_composition.py`][test-filters-composition] (new, held until [`WIP-ALPHA-022-0.0.8`][kanban] ships) | 1 (composition with `OrderSet`) | `+30 / -0` |

Total expected delta (Slices 1–5): ~2000 lines across five slices.

The five slices must be authored in order. Slice 2 depends on Slice 1 (the factories consume the `FilterSet` metaclass and the `RelatedFilter` primitive); Slice 3 depends on Slice 2 (the finalizer-phase-2.5 binding calls `FilterArgumentsFactory(...)`); Slice 4 depends on Slice 3 (the fakeshop live HTTP coverage threads through the promoted `Meta.filterset_class`); Slice 5 depends on Slice 4 (the docs reference the live HTTP coverage as the canonical "what this looks like" example).

## Edge cases and constraints

- **Same-module `RelatedFilter` references** (e.g., `GalaxyFilter` and `CelestialBodyFilter` declared in the same `filters.py` with `RelatedFilter("CelestialBodyFilter")` and `RelatedFilter(GalaxyFilter)` respectively). The Layer-2 module-fallback resolution handles this; the absolute-path lookup fails (the module isn't fully loaded yet) and the `bound_class.__module__` retry succeeds.
- **Cross-module `RelatedFilter` references via absolute path** (e.g., `RelatedFilter("apps.products.filters.CategoryFilter")`). The Layer-2 absolute-path lookup succeeds; the `bound_class.__module__` retry is never reached.
- **Circular `RelatedFilter` cycles** (`A → B → A`). The Layer-4 `_is_expanding_filters` recursion guard breaks the cycle; the cache writes only when no string `_filterset` remains on any related filter (the two-condition guard). A genuine cycle exhausts the guard and raises [`ConfigurationError`][glossary-configurationerror] with the offending class named.
- **`Meta.fields = "__all__"`** (the shorthand). Expands to every **scalar** model field plus each FK / PK column under the conditional `FILTER_DEFAULTS` per [Decision 4](#decision-4--upstream-primitives-parity-floor) — **NOT** relations. Relations only become filterable when the consumer declares an explicit `RelatedFilter(...)`. The narrower scope (corrected per H7 of [`docs/feedback.md`][feedback]) keeps the [Non-goals](#non-goals) "no implicit `FilterSet` generation from `Meta.fields`" rule self-consistent — `"__all__"` would otherwise need to invent target filtersets for every relation, which IS auto-generation. Matches `django-filter`'s own `Meta.fields = "__all__"` default behavior.
- **`Meta.fields = {"galaxy__name": ["exact"]}`** (the double-underscore lookup-path shorthand). Renders as a flat input field with the same lookup behavior as the cookbook's nested-input — the package preserves the cookbook's choice not to expand the path into nested input types at the GraphQL level.
- **`Meta.filterset_class = AdminGalaxyFilter` on a secondary `Meta.primary = False` `DjangoType`**. Per [`Meta.primary`][glossary-metaprimary], the secondary type is registered and reverse-discoverable; the filter binding runs on the secondary type's definition exactly the same way it runs on the primary's. The input-type namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) is name-keyed so two `DjangoType`s on the same model with different `filterset_class`es generate two distinct input types.
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
- **Two consumer schemas with two `<TypeName>FilterInputType`s of the same string name**. Rejected by the per-module input-class namespace's name uniqueness check (per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) lifecycle clause): same `(name, filterset_class)` pair is idempotent; same name from a different filterset raises [`ConfigurationError`][glossary-configurationerror] with both filtersets' qualified names. Catches consumers who accidentally declare two `FilterSet`s with the same `__name__` across different modules.
- **Python keywords `and` / `or` / `not` in dataclass field positions**. Strawberry input types are dataclass-backed; dataclasses cannot generate an `__init__` with keyword-only parameters named `and`, `or`, or `not`. Per H6 of [`docs/feedback.md`][feedback], the package uses Python-safe attribute names (`and_`, `or_`, `not_`) and pins the GraphQL surface names via `strawberry.field(name="and")` / `name="or"` / `name="not"`. Consumer GraphQL queries see `and:` / `or:` / `not:`; Python tests / library code see `result.and_` / `result.or_` / `result.not_`.
- **Partial-finalize recovery for the input-class namespace.** If `finalize_django_types()` raises mid-phase-2.5 (e.g., on an unresolved `RelatedFilter`), already-materialized classes stay in the `django_strawberry_framework.filters.inputs` module's `__dict__` and the lifecycle ledger keeps their provenance. A subsequent `finalize_django_types()` call resumes; idempotent `(name, filterset_class)` keys let the already-materialized classes pass through cleanly. `registry.clear()` resets the filter-input namespace too (per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) lifecycle clause), so test-fixture reload patterns work.
- **Fakeshop schema-reload pattern with already-materialized filter inputs.** The reload pattern (`registry.clear()` → reload app schema modules → reload project schema and URLconf) clears both the model-to-`DjangoType` registry AND the filter-input namespace in the same `registry.clear()` call; reload then re-runs `finalize_django_types()` and re-materializes the input classes fresh. No stale globals leak between test runs.
- **`filter_input_type(filterset_class)` validation**. The helper validates eagerly (`TypeError` at call time for a non-`FilterSet`) even though the returned `Annotated[...]` annotation is lazy. This catches misuse at the resolver-declaration site instead of letting Strawberry surface a more cryptic schema-build-time error.

## Test plan

Tests live in two trees, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement is mandatory.

### `tests/filters/` (new tree)

Package tests; system-under-test is `django_strawberry_framework` itself. Five files mirror the source layout one-to-one per the [`docs/TREE.md`][tree] mirror rule:

- [`tests/filters/__init__.py`][test-filters] — empty `__init__.py` shell so pytest collects under `tests.filters.<module>` matching the existing `tests/types/__init__.py` / `tests/optimizer/__init__.py` convention.
- [`tests/filters/test_base.py`][test-filters] — covers `Filter` / `TypedFilter` / `ArrayFilter` / `RangeFilter` / `ListFilter` / `GlobalIDFilter` / `RelatedFilter` / `LazyRelatedClassMixin`. Tests: primitives reject invalid `method=`; `RangeField.validate_range` accepts valid pairs; `RelatedFilter` accepts class / absolute path / unqualified name forms; `LazyRelatedClassMixin.resolve_lazy_class` tries absolute then bound-module-prefixed; failed resolution raises [`ConfigurationError`][glossary-configurationerror] with the offending name.
- [`tests/filters/test_sets.py`][test-filters] — covers `FilterSetMetaclass` + `FilterSet`. Tests: metaclass collects `RelatedFilter` declarations into `cls.related_filters`; metaclass calls `bind_filterset`; `get_filters()` triggers Layer-4 expansion; expansion cache writes only when no string `_filterset` remains; `_is_expanding_filters` breaks cycles; `_apply_related_queryset_constraints` is honored by nested filters (parent-queryset filter via `parent_qs.filter(<rel>__in=<constraint_qs>)`; nested resolver output is NOT scoped — per H4 of [`docs/feedback.md`][feedback]); `check_permissions` recurses through `RelatedFilter`s; unknown `Meta.fields` raises [`ConfigurationError`][glossary-configurationerror]; unknown lookups raise [`ConfigurationError`][glossary-configurationerror]; **`FilterSet.FILTER_DEFAULTS` Relay-vs-scalar branch selection at filter-instance time** — `FilterSet.filter_for_field` / `filter_for_lookup` overrides produce `GlobalIDFilter` instances when the FK / PK target `DjangoType` implements `relay.Node` AND the scalar PK filter when it does not (per [Decision 4](#decision-4--upstream-primitives-parity-floor); corrected per H1 of [`docs/feedback.md`][feedback] so the runtime filter instance matches the factory-derived input shape); **`FilterSet.apply(input_value, queryset, info)` classmethod** — normalizes a Strawberry input dataclass into `django-filter`'s form-data dict, extracts `request` from `info.context`, instantiates the filterset, runs `check_permissions`, returns `.qs` (per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation) / H2 of [`docs/feedback.md`][feedback]); tests cover `apply` success, `apply` with logical-and/or/not nested input normalization, `apply` propagating a `GraphQLError` raised by `check_permissions`, and `apply` rejecting an input whose normalized shape fails `django-filter` form validation.
- [`tests/filters/test_factories.py`][test-filters] — covers `FilterArgumentsFactory` + `get_filterset_class` + `_dynamic_filterset_cache`. Tests: BFS visits every reachable filterset via `filterset_cls.get_filters()`; cycle-safe forward reference resolves via the `Annotated["Name", strawberry.lazy("module")]` shape per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) Layer 5; cache hits keyed by `(model, fields, extra_meta)`; cache misses build a new filterset; per-module input-class namespace registers under stable class-derived names; two connection fields on the same model share an input type; **input-shape parity with filter-instance shape** — the Strawberry input type derived for `BookFilter.shelf` accepts a scalar `int` shape (because the resolved filter instance is the scalar PK filter, not `GlobalIDFilter`), and the input type derived for `BookFilter.genres` accepts a `GlobalID` string shape (because the resolved filter instance is `GlobalIDFilter`); pins that the factory derives shape from filter instances and never drifts from runtime per H1 of [`docs/feedback.md`][feedback].
- [`tests/filters/test_inputs.py`][test-filters] — covers `_build_logic_fields` + `_build_input_fields` + `construct_search` + `LOOKUP_PREFIXES` + `materialize_input_class` + `filter_input_type`. Tests: Python attribute names are `and_` / `or_` / `not_` (Python keywords are not legal dataclass field names) while GraphQL surface names are exactly `and` / `or` / `not` via `strawberry.field(name="and")` etc. (H6); logical-and / -or / -not fields use the `Annotated["TypeName", strawberry.lazy("django_strawberry_framework.filters.inputs")]` shape over module globals (H1); `materialize_input_class("Name", cls)` sets `module.Name = cls` and writes the lifecycle ledger; re-materialization of the same `(name, filterset_class)` is idempotent; re-materialization of the same name from a different `FilterSet` raises [`ConfigurationError`][glossary-configurationerror]; `clear_filter_input_namespace()` removes every materialized global and resets the ledger; `filter_input_type(non_filterset)` raises `TypeError`; `filter_input_type(MyFilter)` returns the documented `Annotated[...]` shape; **`test_filter_input_type_under_future_annotations`** — module-fixture test that imports a sibling module declaring `from __future__ import annotations` and a resolver `def f(self, filter: filter_input_type(MyFilter) | None = None) -> list[MyType]: ...`; constructs a schema; asserts the resolver's `filter` argument resolves through `LazyType.resolve_type` without `NameError`. Pins the L3 timing-claim contract from [`docs/feedback.md`][feedback] (helper must work whether the annotation evaluates eagerly or lazily); `construct_search` translates `^foo` / `=foo` / `@foo` / `$foo` prefixes correctly; `LOOKUP_PREFIXES` is exactly the cookbook's map.

`tests/filters/test_finalizer.py` (new, lands in Slice 3) — covers the phase-2.5 binding pass. Tests: `Meta.filterset_class` promotion accepts a `FilterSet` and rejects a non-`FilterSet`; the binding pass runs once per `DjangoType`; `finalize_django_types()` is idempotent (re-running it does not re-materialize globals from scratch — the `(name, filterset_class)` idempotency contract holds); a phase-2.5 raise (e.g., from an unresolved `RelatedFilter`) leaves already-materialized globals in place AND the lifecycle ledger consistent, so a follow-up `finalize_django_types()` call resumes cleanly (H5 partial-finalize recovery); `registry.clear()` invokes `clear_filter_input_namespace()` so both registries reset together; lazy-related-filter targets unresolved at finalize raise [`ConfigurationError`][glossary-configurationerror]; **`test_registry_clear_works_without_filters_imported`** — subprocess test that runs `python -c "import django_strawberry_framework.registry; django_strawberry_framework.registry.registry.clear()"` (importing `registry` alone, NOT `filters`); asserts the subprocess exits cleanly (no `ImportError` from the local import inside `TypeRegistry.clear`). Pins the import-cycle-safe integration contract per M5 of [`docs/feedback.md`][feedback].

### `tests/types/test_base.py` (extend)

Add a test pinning the `Meta.filterset_class` promotion from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`: `test_meta_filterset_class_is_promoted_to_allowed_meta_keys` asserts `"filterset_class" not in DEFERRED_META_KEYS` AND `"filterset_class" in ALLOWED_META_KEYS`. Pins the "deferred key promoted only when subsystem ships" contract per [Decision 7](#decision-7--metafilterset_class-promotion-gate).

### `tests/types/test_definition_order.py` (extend)

Add `test_filterset_class_resolves_across_module_boundary` — two `DjangoType`s in two `tests.types.fixtures.*` modules, each with a `Meta.filterset_class` pointing at a sibling `FilterSet`. Asserts `finalize_django_types()` resolves both bindings without `ImportError`.

### `examples/fakeshop/test_query/test_library_api.py` (extend)

System-under-test is the live `/graphql/` HTTP endpoint. Coverage MUST be earned here per the [`docs/TREE.md`][tree] coverage-priority rule. 9 new live HTTP tests:

- `test_library_branches_filter_by_name_icontains` — `{ allLibraryBranches(filter: { name: { iContains: "main" } }) { id name } }`; assert response includes only the matching branches.
- `test_library_books_filter_by_choice_enum` — `{ allLibraryBooks(filter: { circulationStatus: { exact: AVAILABLE } }) { id title } }`; assert response includes only available books.
- `test_library_books_filter_by_non_relay_fk_scalar_id` — `{ allLibraryBooks(filter: { shelf: { id: { exact: 1 } } }) { id title } }`; pin that `BookFilter.shelf` accepts a **scalar `int`** PK because `ShelfType` is non-Relay (the [Decision 4](#decision-4--upstream-primitives-parity-floor) conditional `FILTER_DEFAULTS` branch picks the scalar PK filter, not `GlobalIDFilter`). Asserts the response includes only books on shelf id=1.
- `test_library_books_filter_by_relay_m2m_global_id` — `{ allLibraryBooks(filter: { genres: { id: { exact: "<GenreType GlobalID string>" } } }) { id title } }`; pin that `BookFilter.genres` accepts a **Relay `GlobalID` string** because `GenreType` is Relay-Node-shaped (the [Decision 4](#decision-4--upstream-primitives-parity-floor) conditional `FILTER_DEFAULTS` branch picks `GlobalIDFilter`). The test constructs the GlobalID via `str(relay.GlobalID(type_name="GenreType", node_id=str(genre.pk)))` against a seeded `Genre.objects.first()` — NOT `relay.GlobalID.from_id(...)`, which is the parser for already-encoded strings (corrected per M4 of [`docs/feedback.md`][feedback]). Asserts the response includes only books in that genre. Pinpoints the Relay-vs-scalar split end-to-end.
- `test_library_branches_filter_by_reverse_fk_lookup` — `{ allLibraryBranches(filter: { shelves: { code: { iContains: "A" } } }) { id } }`; assert response includes only branches with matching shelves.
- `test_library_books_filter_combines_and_or_not` — `{ allLibraryBooks(filter: { and: [{ title: { iContains: "Foundation" } }, { not: { circulationStatus: { exact: CHECKED_OUT } } }] }) { id } }`; assert response respects all three operators (and the `and_` / `not_` Python attrs serialize as `and` / `not` on the GraphQL side per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) / [Edge cases](#edge-cases-and-constraints)).
- `test_library_books_filter_preserves_optimizer_cooperation` — `{ allLibraryBooks(filter: { ... }) { id title shelf { id code } genres { id name } } }` under `assertNumQueries(N)`; assert the optimizer's `select_related("shelf")` and `prefetch_related("genres")` survive the filter clause.
- `test_library_branches_filter_respects_related_queryset_boundary_on_parent` — declares a `BranchFilter` with `RelatedFilter(ShelfFilter, queryset=Shelf.objects.filter(topic="permanent collection"))` (uses the existing `Shelf.topic` text field — corrected per M1 of the earlier feedback, which flagged the rev1 `is_archived` field as nonexistent on the `Shelf` model). Seeds two `Branch` rows: `branch_A` with one shelf inside the constraint AND one shelf outside, `branch_B` with all shelves outside the constraint. Queries `{ allLibraryBranches(filter: { shelves: { code: { iContains: "A" } } }) { id shelves { id code topic } } }`. Asserts: (a) `branch_B` is **excluded** from the response (no constrained shelf matches the nested filter — the cookbook's `_apply_related_queryset_constraints` shape filters the PARENT queryset via `parent_qs.filter(shelves__in=<constraint_qs>)`); (b) `branch_A` is **included** because at least one constrained shelf matches; (c) when expanded, `branch_A.shelves` may still surface BOTH the in-constraint AND the out-of-constraint shelves through `BranchType.shelves`'s consumer-authored resolver (the constraint scopes the parent filter, NOT the nested relation-resolver output — pinned per H4 of [`docs/feedback.md`][feedback] and [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)'s H4 follow-up clause). Pins the real boundary contract, not the rev2-misstated output-scoping claim.
- `test_book_genres_uses_absolute_import_path_related_filter` — pin Layer-2 absolute-import lazy resolution end-to-end. `GenreFilter` lives in [`examples/fakeshop/apps/library/filters_genre.py`][fakeshop-library] (a separate module per Slice 4); `BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")` resolves at finalize via `import_string`; `{ allLibraryBooks(filter: { genres: { name: { exact: "SciFi" } } }) { id title } }` returns the matching books. Corrected per M2 of [`docs/feedback.md`][feedback] — the rev1 plan only exercised same-module unqualified-name resolution; this test pins the cross-module absolute-path branch.

The HTTP test file's reload pattern from [`docs/TREE.md`][tree] is preserved: clear the global registry, reload app schema modules, then reload the project schema and URLconf.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Flip [`FilterSet`][glossary-filterset] from `planned for 0.0.8` to `shipped (0.0.8)`. Update entry body to describe the shipped contract: declarative `Meta.model` / `Meta.fields` (dict or `"__all__"`); `RelatedFilter` for cross-relation traversal; `check_*_permission` denial gates; explicit-`queryset=` security boundary; logical-and / logical-or / logical-not on the input shape; generated input types with stable class-derived names; cycle-safe lazy resolution via the six-layer pipeline (port per [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline)).
  - Flip [`RelatedFilter`][glossary-relatedfilter] from `planned for 0.0.8` to `shipped (0.0.8)`. Update body to describe target acceptance (class / absolute path / unqualified name), the Layer-2 module-fallback resolution, and the `queryset=` security boundary.
  - Flip [`Meta.filterset_class`][glossary-metafilterset_class] from `planned for 0.0.8` to `shipped (0.0.8)`. Update body to describe the consumer-facing wiring and the promotion-from-`DEFERRED_META_KEYS` gate.
  - Update the [Index][glossary-index] table's status column for the three entries.
  - Add a new entry `## filter_input_type` documenting the consumer helper from [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper). Body: factory returning `Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` for resolver-argument annotations; eager validation; consumer usage `filter: filter_input_type(BranchFilter) | None = None`.
  - List `FilterSet`, `RelatedFilter`, `filter_input_type` under the Filtering category of the [Browse by category][glossary] block. The [Public exports][glossary-public-exports] section is NOT updated here — that section enumerates top-level `django_strawberry_framework` re-exports, and per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) the filter symbols live at `django_strawberry_framework.filters`. The Filtering-category listing is the right grain.

- [`docs/README.md`][docs-readme]
  - Move `FilterSet` / `Meta.filterset_class` / `RelatedFilter` from "Coming in `0.1.0`" to "Shipped today (`0.0.8`)" once the joint cut bumps the version.
  - Optional: add a small Quick start example showing the `Meta.filterset_class = MyFilter` shape next to the existing `DjangoType` declaration.

- [`docs/TREE.md`][tree]
  - Flip the `filters/` subpackage entry from `[alpha]` to on-disk. Move from the "target package layout" section to the "current on-disk layout" section.
  - List the five new files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); list the mirrored `tests/filters/` tree (`__init__.py`, `test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`, `test_finalizer.py`).
  - Update the "Test layout going forward" section's `tests/filters/` enumeration to match the on-disk reality.

- [`README.md`][readme]
  - Add `FilterSet` / `RelatedFilter` / `filter_input_type` / `Meta.filterset_class` to the shipped-symbol bullet list (under the `0.0.8` boundary). Per M2 of [`docs/feedback.md`][feedback], `filter_input_type` belongs in the README sweep because it IS a consumer-facing public symbol from [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper).

- [`GOAL.md`][goal]
  - The astronomy showcase already references `Meta.filterset_class = filters.GalaxyFilter` and the per-app `filters.py` shape — no edit needed there.
  - Rewrite the "Coming from DRF + `django-filter`" migration narrative anchored at [`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`][goal-migration-shape] so it no longer implies direct reuse without re-parenting (corrected per M1 of [`docs/feedback.md`][feedback]; the validator at `_validate_meta` rejects a plain `django_filters.FilterSet`, and the consumer migration is a one-line parent-class swap to `django_strawberry_framework.filters.FilterSet`, which IS a `django_filters.filterset.BaseFilterSet` subclass so every `Filter` / `FilterMethod` / form-cleaning primitive carries over unchanged). Update the diff block in the same section so the example shows the parent-class swap.

- [`TODAY.md`][today]
  - Extend the "Shipped capabilities" enumeration with `FilterSet` / `Meta.filterset_class` / `RelatedFilter`.
  - Extend the fakeshop section to describe the new `BranchFilter` / `BookFilter` / `LoanFilter` / `PatronFilter` declarations under [`examples/fakeshop/apps/library/filters.py`][fakeshop-library] and the live HTTP filter coverage under [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library].

- [`KANBAN.md`][kanban] (Slice 5)
  - Move `WIP-ALPHA-021-0.0.8` to the Done column with the next available `DONE-NNN-0.0.8` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). Past-tense Done body:

    > "Shipped the filtering subsystem. [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] (promoted out of `DEFERRED_META_KEYS`) land at [`django_strawberry_framework/filters/`][filters] across five files (`base.py`, `sets.py`, `factories.py`, `inputs.py`, `__init__.py`) and `tests/filters/` mirrors the layout. Six-layer lazy-resolution pipeline borrowed from `django-graphene-filters`: Layers 1–4 and 6 port library-agnostic verbatim on top of the shared `BaseFilterSet` foundation, Layer 5's cycle-safe forward reference adapts from Graphene's `lambda:` to `Annotated["TypeName", strawberry.lazy("django_strawberry_framework.filters.inputs")]` over module globals (per H1 of `docs/feedback.md`). Parity-floor primitives (`ArrayFilter`, `RangeFilter`, `ListFilter`, `TypedFilter`, `GlobalIDFilter`) ship under `base.py`; `FILTER_DEFAULTS` is a class attribute on `FilterSet` (NOT in `factories.py`); `FilterSet.filter_for_field` / `filter_for_lookup` overrides pick `GlobalIDFilter` when the FK/PK target `DjangoType` implements `relay.Node` and the scalar PK filter when it does not (per `registry.get(target_model)` + `implements_relay_node(...)`). `FilterArgumentsFactory` derives Strawberry input field shape from the resolved filter instances on `filterset_cls.get_filters()`, NOT from a parallel map — runtime filter instance and input shape cannot drift. `Meta.filterset_class` promotion runs through finalizer phase 2.5 (same seam as `Meta.interfaces`); the phase materializes each generated input class as a module global of `django_strawberry_framework.filters.inputs` before `strawberry.Schema(...)` runs. The new `filter_input_type(BranchFilter)` helper produces the resolver-annotation shape. `registry.clear()` co-clears the filter input namespace via `clear_filter_input_namespace()`. Per-package input-class namespace is separate from the model-to-`DjangoType` registry (`Meta.primary` design preserved). [`examples/fakeshop/apps/library/`][fakeshop-library] grows `filters.py` (carrying `BranchFilter` / `ShelfFilter` / `BookFilter` / `LoanFilter` / `PatronFilter`) and `filters_genre.py` (carrying `GenreFilter` — the cross-module fixture for the Layer-2 absolute-import-path test) wired through `Meta.filterset_class`; root resolvers accept `filter:` via `filter_input_type(<Name>Filter)` annotations; [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows 9 live HTTP tests covering scalar / choice-enum / non-Relay-FK scalar PK / Relay-M2M GlobalID / reverse-FK / logical / optimizer cooperation / related-queryset parent-scope boundary via `Shelf.topic` / cross-module absolute-path `RelatedFilter`. Spec: `docs/spec-021-filters-0_0_8.md`. The version bump from `0.0.7 → 0.0.8` is owned by the joint `0.0.8` cut (last `0.0.8` card to ship), NOT this card per Decision 10."
  - Update the card body's `Definition of done` bullet 1 (`docs/spec-filters.md` → `docs/SPECS/spec-021-filters-0_0_8.md` after the Step-8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)).
  - Update the `### In progress` summary paragraph (anchored at [`KANBAN.md`][kanban] #"### In progress") to remove `WIP-ALPHA-021-0.0.8` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`][changelog] (Slice 5)
  - **Append** to the `[Unreleased]` `### Added` subsection (creating the subsection if absent):

    > "Filtering subsystem. [`FilterSet`][glossary-filterset] (declarative `Meta.model` / `Meta.fields` / `check_*_permission` gates / explicit-`queryset=` security boundary), [`RelatedFilter`][glossary-relatedfilter] (cross-relation traversal accepting class / absolute path / unqualified name), and [`Meta.filterset_class`][glossary-metafilterset_class] (promoted out of `DEFERRED_META_KEYS`). Parity-floor primitives: `ArrayFilter`, `RangeFilter`, `ListFilter`, `TypedFilter`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`. Cycle-safe six-layer lazy-resolution pipeline borrowed from `django-graphene-filters` (with `django_filters.filterset.BaseFilterSet` as the shared foundation per [Decision 5](#decision-5--django-filter-as-the-foundation)); Graphene's `lambda:` forward references become `Annotated["TypeName", strawberry.lazy("django_strawberry_framework.filters.inputs")]` over module globals (per H1 of `docs/feedback.md`). Per-package input-class namespace materialized as real module globals of `django_strawberry_framework.filters.inputs`, keyed by stable class-derived names; `clear_filter_input_namespace()` co-clears with `registry.clear()`. Consumer resolver-annotation helper `filter_input_type(FilterSet)` returns the documented `Annotated[...]` shape so root resolvers see a working `filter:` argument at `strawberry.Schema(...)` time. Subpackage at [`django_strawberry_framework/filters/`][filters] (five files); mirror tests at `tests/filters/`. Live HTTP filter coverage in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (6–8 tests across scalar / choice-enum / FK / reverse-FK / M2M / logical / optimizer-cooperation / related-queryset-boundary axes)."
  - **Append** to the `[Unreleased]` `### Changed` subsection:

    > "[`Meta.filterset_class`][glossary-metafilterset_class] is no longer in `DEFERRED_META_KEYS`; declaring `Meta.filterset_class = MyFilter` now wires through to finalizer phase 2.5 and surfaces a working filter input on the GraphQL type. Consumers who declared the key against `0.0.7` saw a [`ConfigurationError`][glossary-configurationerror]; against `0.0.8` it produces a filter surface."
  - Per the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed", this Slice-5 bullet is the explicit permission for this card.
  - The version bump is NOT in this card per [Decision 10](#decision-10--joint-008-cut); the last `0.0.8` card to ship promotes `[Unreleased]` to `[0.0.8]` and bumps `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion atomically.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **Layer 5's forward-reference shape against Strawberry releases.** The corrected idiom is `Annotated["{Name}FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` resolved via `LazyType.resolve_type` reading `module.__dict__` (per H1 of [`docs/feedback.md`][feedback] and [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline) Layer 5). Preferred answer: pin Strawberry to a version that supports this idiom (the package's existing `strawberry-graphql>=0.262.0` pin in [`pyproject.toml`][pyproject] already covers it); `tests/filters/test_inputs.py` constructs a minimal schema with a lazy `Annotated[...]` forward reference and asserts resolution succeeds, catching any future Strawberry regression at CI time. Fallback: if Strawberry deprecates the module-globals path in a future release (no signal that this is coming), the package re-evaluates; today's shape is the documented Strawberry idiom.
- **`Annotated["NotYetMaterialized", strawberry.lazy(...)]` resolution timing.** The materialize-before-`Schema` ordering ([Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)) depends on consumers calling `finalize_django_types()` BEFORE `strawberry.Schema(...)` — the canonical setup order pinned in [`docs/README.md`'s Schema setup boundary][docs-readme]. Preferred answer: consumers who follow the documented order get materialization in time; consumers who construct `strawberry.Schema(...)` before `finalize_django_types()` get a `LazyType.resolve_type` failure naming the missing class, which surfaces the ordering bug at schema-build time. Fallback: if real consumer reports surface "I called Schema first" confusion, a follow-up card adds an explicit check at `FilterSet.__init_subclass__` time that materializes a stub-class placeholder so `Schema(...)` resolves a clear "this class is being finalized" error instead of an opaque `KeyError`.
- **`filter_input_type(FilterSet)` against future `DjangoConnectionField`.** [`DjangoConnectionField`][glossary-djangoconnectionfield] (`0.0.9`) will accept `filterset_class=` directly and own the argument injection — but `0.0.8` consumers using `DjangoListField` or plain `@strawberry.field` resolvers reach for `filter_input_type(...)` first. Preferred answer: the `0.0.9` connection field uses `filter_input_type(FilterSet)` internally under the hood (no duplicate machinery); the `0.0.8` consumer-facing helper is the same shape `0.0.9` builds on. Fallback: if the connection field's argument-injection path turns out to need a different annotation shape (e.g., a wrapped `FilterSetWrapper[T]` generic for connection-field internals), the helper grows a `filter_input_type(FilterSet, *, connection_wrap=True)` parameter; the bare helper signature stays compatible.
- **Input-type namespace under per-`Meta.primary` secondary `DjangoType`s.** Preferred answer per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle): the input-class namespace is name-keyed, so two `DjangoType`s on the same model with two different `filterset_class`es generate two distinct input types (`PrimaryGalaxyFilterInputType` and `AdminGalaxyFilterInputType`). Fallback: if a real consumer scenario surfaces where two filtersets on the same model should share an input type (e.g., shared queries against two roles), a follow-up card adds an optional `Meta.filter_input_alias` key that lets the consumer alias the generated input-type name; deferred until demand surfaces.
- **`Meta.filterset_class = MyDjangoFilter` accepting a `django_filters.FilterSet` subclass without re-parenting.** Preferred answer per [Decision 5](#decision-5--django-filter-as-the-foundation): the package's `FilterSet` IS a `django_filters.filterset.BaseFilterSet` subclass, so consumers migrate via parent-class swap (`class MyFilter(FilterSet):` instead of `class MyFilter(django_filters.FilterSet):`); the validator at `_validate_meta` rejects a plain `django_filters.FilterSet` that isn't a `django_strawberry_framework.filters.FilterSet` because the lazy-resolution + GraphQL-input layers don't run otherwise. [`GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`][goal-migration-shape] (the wording itself) is honored as "plugs in via one-line parent swap, inheriting every `django-filter` primitive". Fallback: if real consumer adoption pressure surfaces for accepting `django_filters.FilterSet` directly (without re-parenting), a follow-up card ships an opt-in `DjangoFilterAdapter` helper that wraps a `django_filters.FilterSet` in a thin `FilterSet`-shaped subclass.
- **Filter applied to a relation that has a custom `get_queryset`.** Preferred answer per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation): the optimizer's existing `Prefetch` downgrade ([Queryset diffing][glossary-queryset-diffing]) preserves the target type's `get_queryset` visibility filter; the filter clause applies to the visibility-scoped queryset. Fallback: if a specific filter shape (e.g., `filter on relation that has both get_queryset AND a RelatedFilter queryset=`) breaks the optimizer cooperation, a follow-up card refactors the binding to thread through the optimizer's `Prefetch` wrapper.
- **Logical-and / logical-or input shape — flat vs nested.** Preferred answer: the cookbook's flat shape (`filter: { and: [...] }`) ports verbatim; nested per-field structures (`filter: { name__icontains: "...", and: [...] }`) are accepted at the top level only; nesting `and` / `or` / `not` inside per-field input is rejected. Fallback: if real consumer feedback wants nested operators, a follow-up card lifts the restriction.
- **`Meta.fields = "__all__"` performance**. Preferred answer: the BFS factory walks every model field; for models with many fields this is O(field_count × lookup_count) at finalize time but the result is cached. Caching at finalize means the per-request cost is unaffected. Fallback: if real-world consumer schemas with very-wide models surface measurable finalize-time impact, a follow-up card adds a `Meta.lookup_subset` shorthand or a per-app field-set policy.
- **`Meta.search_fields` planned for `0.1.2`** but `LOOKUP_PREFIXES` ships in this card. Preferred answer: the `LOOKUP_PREFIXES` map + `construct_search` helper land in `filters/inputs.py` so the future `Meta.search_fields` card consumes them without retrofit; no consumer surface for search lookups exists today. Fallback: if `Meta.search_fields` ships earlier or the cookbook's `search_fields` shape diverges from `LOOKUP_PREFIXES`, that card adjusts; this card's surface is unaffected.
- **Glossary entry parity.** `LazyRelatedClassMixin`, `FilterArgumentsFactory`, `_dynamic_filterset_cache`, `FILTER_DEFAULTS`, and `LOOKUP_PREFIXES` are internal symbols not currently in [`docs/GLOSSARY.md`][glossary]. Preferred answer: keep them internal — the consumer surface is `FilterSet` / `RelatedFilter` / `filter_input_type` / `Meta.filterset_class`; the internal symbols are documented via this spec's body and via module docstrings, not the glossary. Fallback: if a future card surfaces one (e.g., a public `LOOKUP_PREFIXES` re-export for consumers writing custom search resolvers), the glossary entry lands with that card.
- **`filter_input_type` CSV row deferral** (M2 of [`docs/feedback.md`][feedback]). [`docs/spec-021-filters-0_0_8-terms.csv`][spec-021-terms] currently lists 32 terms and does NOT include `filter_input_type`, because the corresponding `## filter_input_type` heading does not yet exist in [`docs/GLOSSARY.md`][glossary] — the entry lands during Slice 5 implementation alongside the CSV row (mirroring spec-020's `strawberry_config` pattern). The reviewer correctly noted this hides the new public symbol from the glossary gate during the authoring cycle. Preferred answer: the spec body documents the GLOSSARY entry as a Slice 5 deliverable (Slice 5 GLOSSARY bullet + DoD item 15 + DoD item 16); the CSV row is added in the same Slice 5 commit; the checker exits 0 against the 33-term CSV after Slice 5 lands. Fallback: if a future maintainer prefers the over-zealous discipline (CSV row in spec-author cycle, accepting checker failure until Slice 5), add the row at `filter_input_type,filter_input_type,The consumer helper this card introduces; GLOSSARY entry created in Slice 5.` and document the failure mode in this entry.

## Out of scope (explicitly tracked elsewhere)

- **Ordering** ([`OrderSet`][glossary-orderset], [`Meta.orderset_class`][glossary-metaorderset_class], [`RelatedOrder`][glossary-relatedorder]) — [`WIP-ALPHA-022-0.0.8`][kanban]. Sibling card; reuses this card's lazy-resolution architecture verbatim with `OrderSet` / `RelatedOrder` substituted for `FilterSet` / `RelatedFilter`. Slice 6 of this card holds the composition smoke test until the ordering card ships.
- **Aggregation** ([`AggregateSet`][glossary-aggregateset], [`RelatedAggregate`][glossary-relatedaggregate], [`Meta.aggregate_class`][glossary-metaaggregate_class], [`get_child_queryset`][glossary-get_child_queryset]) — `0.1.3`. Future Layer-3 sidecar; reuses Layers 1–4 of this card's lazy-resolution pipeline; runs at the aggregate-input layer not the filter-input layer.
- **Field selection** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`. Future Layer-3 sidecar; orthogonal to filter machinery (field selection gates result-shape, filters gate result-content).
- **Search fields** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`. Future Layer-3 sidecar; consumes this card's `LOOKUP_PREFIXES` + `construct_search` without modification.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions], [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.0.10`. Future Layer-3 sidecar; composes with this card's `check_*_permission` gates per [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation) without retrofit.
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — `0.0.9`. Consumes the `FilterArgumentsFactory` output as the connection's `filter:` argument source. This card's per-module input-class namespace is the registration point.
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
4. `sets.py` ships `FilterSetMetaclass` and `FilterSet` per Layers 3 + 4 of [Decision 3](#decision-3--six-layer-lazy-resolution-pipeline). `FilterSet` subclasses `django_filters.filterset.BaseFilterSet` per [Decision 5](#decision-5--django-filter-as-the-foundation) and carries: (a) `FILTER_DEFAULTS` class attribute (Relay-vs-scalar mapping per [Decision 4](#decision-4--upstream-primitives-parity-floor)) + `filter_for_field` / `filter_for_lookup` overrides that apply the conditional, so runtime filter instances and Strawberry input shape stay aligned (per H1 of [`docs/feedback.md`][feedback]); (b) `apply(input_value, queryset, info)` classmethod — the **unified resolver-facing API** that normalizes a Strawberry input dataclass into `django-filter`'s form-data dict, extracts `request` from `info.context`, instantiates `cls(data=data, queryset=queryset, request=request)`, runs `check_permissions(...)`, and returns `filterset.qs` (per H2 of [`docs/feedback.md`][feedback]); (c) `filter_queryset(self, queryset)` — the `django-filter` instance-method override for tree-form logic, distinct from `apply`; (d) `Meta.model`, `Meta.fields`, `get_filters`, `check_permissions`, `_apply_related_queryset_constraints` on top of the upstream's `declared_filters` / `base_filters` / `.filters` / `.form` / `.qs` / `Filter.method` machinery.
5. `factories.py` ships `FilterArgumentsFactory` (Layer 5 BFS, deriving input field types from the resolved filter instances on `filterset_cls.get_filters()`, NOT from a parallel `FILTER_DEFAULTS` lookup — per H1 of [`docs/feedback.md`][feedback]), with module-globals materialization via `materialize_input_class`. Ships `get_filterset_class`, `_dynamic_filterset_cache` (Layer 6).
6. `inputs.py` IS the input-class namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle): filter input classes are materialized as real module globals of `django_strawberry_framework.filters.inputs` via `materialize_input_class(name, cls)` (idempotent for `(name, filterset_class)` pairs; raises [`ConfigurationError`][glossary-configurationerror] on name collision against a different filterset). The module ships `materialize_input_class`, `clear_filter_input_namespace`, `_materialized_names` (private ledger), plus `_build_logic_fields`, `_build_input_fields`, `construct_search`, `LOOKUP_PREFIXES`.
6a. `filters/__init__.py` re-exports `filter_input_type` per [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper): consumers call `filter_input_type(BranchFilter)` on a resolver signature and get back `Annotated["BranchFilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]`. The helper validates eagerly (`TypeError` for non-`FilterSet` arguments).
7. [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] grows a `filterset_class: type | None = None` slot, populated by `DjangoType.__init_subclass__` from `Meta.filterset_class`.
8. [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] no longer contains `"filterset_class"`; [`ALLOWED_META_KEYS`][base] contains `"filterset_class"`; `_validate_meta` validates `Meta.filterset_class` is a `FilterSet` subclass and raises [`ConfigurationError`][glossary-configurationerror] otherwise.
9. [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] grows the phase-2.5 filter-binding pass per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering): for each `DjangoType` with `definition.filterset_class is not None`, validate, call `filterset_cls.get_filters()` (Layer 4), call `FilterArgumentsFactory(filterset_cls).arguments` (Layer 5), and call `materialize_input_class(name, cls)` for every generated input class so each becomes a module global of `django_strawberry_framework.filters.inputs`. `registry.clear()` invokes `clear_filter_input_namespace()` so the model-to-`DjangoType` clear and the filter-input clear share one entry point per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
10. `tests/filters/` (new tree) carries five mirror files (`__init__.py`, `test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`) plus `test_finalizer.py` per the [Test plan](#test-plan); each file covers what its mirror source file ships.
11. [`tests/types/test_base.py`][test-types] and [`tests/types/test_definition_order.py`][test-types] grow validator and definition-order tests for `Meta.filterset_class` per the [Test plan](#test-plan).
12. [`examples/fakeshop/apps/library/`][fakeshop-library] ships `filters.py` (new) carrying `BranchFilter`, `ShelfFilter`, `BookFilter`, `LoanFilter`, `PatronFilter` (same-module `RelatedFilter("ShelfFilter")` / `RelatedFilter("BookFilter")` references) AND `filters_genre.py` (new) carrying `GenreFilter` (the cross-module fixture so `BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")` exercises the Layer-2 absolute-import-path branch).
13. [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] grows `Meta.filterset_class = filters.BranchFilter` (and the matching key on `ShelfType` / `BookType` / `LoanType` / `PatronType` / `GenreType`) on the corresponding `DjangoType` classes; root resolvers annotate `filter:` via `filter_input_type(filters.<Name>Filter)` per [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper) and call the resolved filterset's `apply(filter_value, queryset, info)` classmethod (per H2 of [`docs/feedback.md`][feedback] / [Decision 8](#decision-8--relation-permission-cascade--get_queryset-cooperation)) before returning the queryset.
14. [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows **exactly 9** live `/graphql/` HTTP tests per the [Test plan](#test-plan) (scalar / choice-enum / non-Relay-FK-scalar / Relay-M2M-GlobalID / reverse-FK / logical / optimizer-cooperation / related-queryset parent-scope boundary via `Shelf.topic` / cross-module-absolute-path-`RelatedFilter`); count pinned per M3 of [`docs/feedback.md`][feedback]. The Relay-vs-scalar split pins [Decision 4](#decision-4--upstream-primitives-parity-floor)'s conditional `FILTER_DEFAULTS` end-to-end.
15. [`docs/GLOSSARY.md`][glossary] flips [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], and [`Meta.filterset_class`][glossary-metafilterset_class] from `planned for 0.0.8` to `shipped (0.0.8)`; adds a new `## filter_input_type` entry per [Decision 11](#decision-11--filter_input_typefilterset-consumer-helper); updates entry bodies; updates the [Index][glossary-index] table for all four entries; lists `FilterSet` / `RelatedFilter` / `filter_input_type` under the Filtering category of the [Browse by category][glossary] block. The [Public exports][glossary-public-exports] section is NOT updated — it enumerates top-level `django_strawberry_framework` re-exports, and per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) the filter symbols live at `django_strawberry_framework.filters` (corrected per M3 of [`docs/feedback.md`][feedback]).
16. [`docs/spec-021-filters-0_0_8-terms.csv`][spec-021-terms] anchors every project-specific term in the spec body to its [`docs/GLOSSARY.md`][glossary] heading; running [`uv run python scripts/check_spec_glossary.py --spec docs/spec-021-filters-0_0_8.md`][check-spec-glossary] reports `OK: <N> terms`.
17. [`docs/TREE.md`][tree] flips the `filters/` subpackage entry from `[alpha]` to on-disk; the mirror `tests/filters/` tree is enumerated; "Test layout going forward" reflects the new tree.
18. [`docs/README.md`][docs-readme] moves filter symbols from "Coming in `0.1.0`" to "Shipped today" once the joint cut bumps the version.
19. [`README.md`][readme] adds `FilterSet` / `RelatedFilter` / `filter_input_type` / `Meta.filterset_class` to the shipped-symbol bullet list (per M2 of [`docs/feedback.md`][feedback]).
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
[goal-migration-shape]: ../GOAL.md#migration-shape
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
[spec-021]: spec-021-filters-0_0_8.md
[spec-021-terms]: spec-021-filters-0_0_8-terms.csv
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

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../django_strawberry_framework/types/base.py
[definition]: ../django_strawberry_framework/types/definition.py
[filters]: ../django_strawberry_framework/filters/
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[registry]: ../django_strawberry_framework/registry.py
[registry-typeregistry]: ../django_strawberry_framework/registry.py

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
