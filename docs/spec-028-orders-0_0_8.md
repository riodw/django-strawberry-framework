# Spec: Ordering subsystem (`OrderSet`, `RelatedOrder`, `Meta.orderset_class`)

Target release: `0.0.8` (per [`KANBAN.md`][kanban] card `WIP-ALPHA-028-0.0.8`). The Filtering subsystem already shipped as `DONE-027-0.0.8` under `[Unreleased]` without bumping `__version__`, so this card is the last `0.0.8` card to ship — per [Decision 10](#decision-10--joint-008-cut) and the L5 contingency precedent from [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] Decision 10, **this card owns the joint-cut version bump from `0.0.7 → 0.0.8`**.
Status: planned — Slice 1 not yet started. The [`django_strawberry_framework/orders/`][orders] subpackage does not exist on disk today; [`docs/TREE.md`][tree]'s "target package layout" section names the directory under `[alpha]` and this card flips it to on-disk.
Owner: package maintainer.
Predecessors: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (the shipped Filtering subsystem — five of six lazy-resolution layers, the finalizer phase-2.5 binding seam, the per-module input-class namespace, the consumer-helper pattern, the active-input-only `check_permissions` discipline, the sync/async `apply_*` split, and the joint-cut Decision-10 posture all port directly); [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] (Decision 10's "joint cut" precedent + the L5 contingency this card invokes); [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (Relay-Node wiring at finalizer phase 2.5 — the synchronization point this card reuses); [`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018] (the `Meta.primary` design + the [`TypeRegistry`][registry-typeregistry] keying convention this card respects when answering [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)); [`docs/GLOSSARY.md`][glossary] entries [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], [`Meta.orderset_class`][glossary-metaorderset_class] (all currently `planned for 0.0.8`); [`KANBAN.md`][kanban] card body's `Verified in upstream` and `Other` blocks (the six-layer architecture summary + the Layer 6 fresh-design question), preserved as Decisions without re-litigation.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pinned the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)), the subpackage layout ([Decision 2](#decision-2--subpackage-layout-and-public-export-surface)), the six-layer lazy-resolution pipeline borrowed from `django-graphene-filters` with the same Strawberry-adapted Layer 5 the filter card pinned in [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3 ([Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6)), the upstream-primitives parity floor ([Decision 4](#decision-4--upstream-primitives-parity-floor)), the `Ordering` enum shape and the `orderBy: [<T>OrderInput!]` argument shape ([Decision 5](#decision-5--ordering-enum-and-argument-shape)), the finalizer-phase-2.5 wiring seam ([Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)), the `Meta.orderset_class` promotion gate ([Decision 7](#decision-7--metaorderset_class-promotion-gate)), the cooperation contract with the filter subsystem and the `get_queryset` visibility hook ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer)), the input-class-namespace lifecycle ([Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)), the joint-`0.0.8`-cut posture WITH the L5 contingency triggered (this card owns the bump) ([Decision 10](#decision-10--joint-008-cut)), the `order_input_type(OrderSet)` consumer helper ([Decision 11](#decision-11--order_input_typeorderset-consumer-helper)), the deferred Layer 6 + DISTINCT ON design questions ([Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009)), and the live-HTTP coverage strategy ([Decision 13](#decision-13--live-http-coverage-strategy)). Out of scope: aggregation ([`AggregateSet`][glossary-aggregateset]) — `0.1.3`; [`DjangoConnectionField`][glossary-djangoconnectionfield] — `0.0.9`; permission cascade ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`; [Meta.search_fields][glossary-metasearch_fields] — `0.1.2`. Dependencies on these surfaces are forward-only: this card composes when they arrive without retrofit.
- **Revision 2** — review pass over rev1 captured in [`docs/feedback.md`][feedback]. Every Blocking / High / Medium / Nit / Out-of-scope finding applied in a single pass; foundational findings (B1-B3) drove the largest reshapes.
  - **B1 — subpass order corrected to match shipped filter code.** [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering) reshaped from `bind → expand → materialize → orphan-validate` (the spec-027 rev8 *prescription*) to the actual shipped order `bind → expand → orphan-validate → materialize` (the actual shipped *implementation* at [`finalizer.py:478-600`][finalizer]). Orphan-validate before materialize is load-bearing — leaves no stale ledger entries when an orphan check raises, so a re-run after the consumer fixes the orphan starts clean. Slice 1 checklist, DoD item 10, and the test plan all updated.
  - **B2 + B3 — `registry.clear()` pseudocode rewritten against actual code.** [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) code block: replaced the phantom `_types_by_model` / `_primary_types` field names with the actual `_types` / `_primaries` / `_models` / `_enums` / `_definitions` / `_pending` / `_finalized` fields (verbatim from [`registry.py:43-50`][registry]); fixed the `except ImportError: return` in the last block to `except ImportError: pass` + `else:` (M-core-4 footgun fix from the shipped filter side preserved). All four try/except blocks now use the same uniform shape.
  - **H1 — `OrderSet.apply(...)` dispatcher dropped (YAGNI).** Decision 2, Decision 8, Implementation plan table, and DoD item 4 all updated. The filter side's `apply(...)` exists for sync-misuse `RuntimeError` rewrap that the order side never triggers (no async-only `get_queryset` re-derivation per step 4 of the apply pipeline). Consumers call `apply_sync` / `apply_async` directly.
  - **H2 — optimizer projection claim retracted.** Verified per `grep` that no logic in [`optimizer/walker.py`][optimizer-walker] or [`optimizer/plans.py`][optimizer-plans] inspects `queryset.query.order_by`. The user-visible behavior is correct because Django's ORM extends column fetches as needed — but that is Django's cooperation, not the package's. Order-aware projection augmentation is **out of scope for `0.0.8`** and explicitly not promised; the `test_library_books_order_preserves_optimizer_cooperation` narrative updated to reflect what the test actually pins.
  - **H3 — `__all__` cookbook parity verified.** Read `~/projects/django-graphene-filters/django_graphene_filters/orderset.py:271`; confirmed `AdvancedOrderSet.get_fields` carries the `if meta_fields == "__all__":` branch that walks `get_concrete_field_names(model)`. The reviewer's claim of divergence was incorrect; the spec preserves the parity claim with the verifying line citation now inline in [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6).
  - **H4 — position-side-channel leak acknowledged.** [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4 expanded to name the leak explicitly: ordering by a hidden related column changes the *position* of visible parent rows based on data the user cannot read, so a determined consumer can infer the relative ordering of hidden rows by diff'ing two queries. The leak is intentionally accepted for `0.0.8` (low bandwidth, no value disclosure — only causal explanation of visible ordering); the closing-this design is deferred to the `0.0.9` cohort. The `OrderSet` and `RelatedOrder` GLOSSARY entries (Slice 5) call this out so consumers reaching for permission gates know the risk.
  - **M1 — pipeline step count corrected.** "The 7-step pipeline" → "The 8-step pipeline" (the steps were numbered 1-8 in the body).
  - **M2 + M5 + M6 + M7 — Slice 4 live HTTP coverage expanded from 10 to 13 tests.** Added: `test_library_books_order_by_flat_shorthand_path` (M2; pins `Meta.fields = ["shelf__code"]` → `shelfCode:` flat surface); reverse-FK multiplicity test redesigned to *assert* the multiplication (M5; the prior workaround of seeding one shelf was brittle); `test_order_check_permission_denies_for_active_field` AND `test_order_check_permission_quiet_for_inactive_field` (M6; split from a single combined test so regressions surface as named failures); `test_order_empty_list_passes_through` AND `test_order_null_direction_skips_field` (M7; pins the no-op contracts).
  - **M3 — `INPUTS_MODULE_PATH` constant + `_input_type_name_for` helper.** Decision 2 sets.py / inputs.py contents updated to hoist both symbols from the filter side's [`filters/inputs.py:53,183`][filters-inputs] verbatim — `INPUTS_MODULE_PATH` for the module-path string + `_input_type_name_for(orderset_class)` for the `<Name>InputType` formula.
  - **M4 — `Ordering.resolve()` example corrected.** Added the missing `from django.db.models.expressions import OrderBy` import; added a one-line comment explaining `None` is Django's sentinel for "no NULLS clause" (NOT `False`).
  - **M8 — `test_order_accepts_field_not_in_djangotype_meta_fields` added.** Pins the documented "consumer can order on columns they cannot select" behavior in `tests/orders/test_sets.py`.
  - **M9 — `_helper_referenced_ordersets` location pinned to `orders/__init__.py`.** Decision 2 was previously ambiguous (listed it under `inputs.py`); now correctly pinned to the package `__init__.py` (matching the filter side's location at `filters/__init__.py:48`). The two `registry.clear()` blocks per Decision 9 stay separate.
  - **M10 — duplicated KANBAN / CHANGELOG past-tense paragraph deduplicated.** The CHANGELOG bullet now references the KANBAN body as the single source of truth and carries only a one-line headline summary.
  - **N1 — link slugs renamed to match new spec filenames.** Every `[spec-NNN]` slug updated to the post-renumbering filename (`[spec-021]` → `[spec-027]`, `[spec-016]` → `[spec-020]`, etc.); the new spec slug is `[spec-028]`. The link defs at the bottom carry the canonical paths.
  - **N2 — `Verified in upstream` block inlined.** Decision 4 now carries the verbatim list of strawberry-django ordering symbols from the KANBAN card body, so the spec is self-contained.
  - **N3 — `_validate_orderset_class` import-cycle note added.** DoD item 9 now spells out the local in-function `from ..orders.sets import OrderSet` import requirement (mirroring the filter side's `_validate_filterset_class` at `types/base.py:88`).
  - **N4 — `tests/orders/` file count harmonized.** Decision 2 and Decision 13 both now say "7 files total" (1 shell + 4 mirror + `test_finalizer.py` + `test_composition.py`); DoD item 11 was already correct.
  - **N5 — `<DATE>` placeholder.** `YYYY-MM-DD` → `<DATE>` across Slice 5 / Decision 10 / DoD item 24 so the placeholder reads as "fill this in" instead of risking literal ship into the changelog.
  - **N6 — L5 contingency made deterministic.** Decision 10 and DoD item 24 now name a concrete `grep -E 'WIP-ALPHA-[0-9]+-0\.0\.8' KANBAN.md` command for the Slice-5 author to run at merge time.
  - **N7 — `apply_async` blocking-hook caveat added.** Decision 8's sync/async-split subsection now mirrors the filter side's caveat verbatim: `apply_async` does NOT wrap `check_*_permission` hooks in `sync_to_async`, so a consumer hook that issues a blocking ORM call would block the event loop.
  - **N8 — proxy / MTI semantics documented.** Decision 3 now spells out the `"__all__"` behavior for proxy models, multi-table inheritance, and abstract models.
  - **N9 — `noqa: A002` convention note.** User-facing API resolver example now carries `# noqa: A002` on the `filter:` parameter, and the surrounding prose notes that `order_by` does not need the suppression (but `input:` would, for future cards).
  - **O1 + O2 — forward-compatibility previews added to Decision 12.** Notes the two open `Meta.distinct` shape choices (tuple-of-names vs class-reference) and confirms this card's design is forward-compatible to both the explicit-`orderset_class` and dynamic-factory Layer 6 paths.
  - Filename rebased from `spec-024-orders-0_0_8.md` to `spec-028-orders-0_0_8.md` and the archived filter spec to `docs/SPECS/spec-027-filters-0_0_8.md` per the maintainer's spec-renumbering pass between rev1 and rev2.
- **Revision 3** — sweep-residual pass over rev2 captured in [`docs/feedback.md`][feedback]. Rev2 closed all 27 rev1 findings cleanly; rev3 closes the four sweep-residuals (R1-R4: count-update misses) and the three new observations (N-new-1 through N-new-3: phrasing tweaks) the rev2 review surfaced. None of these affect architecture or implementation plan; the spec is now internally consistent on every cited count.
  - **R1 — "seven-step pipeline" residual.** Decision 8 Justification list (line 635) read "The seven-step pipeline reflects this simplification" even though Decision 8 body (line 609) was already corrected to "8-step" in rev2's M1 fix. Updated to "The eight-step pipeline reflects this simplification."
  - **R2 — section header count.** Test plan's `examples/fakeshop/test_query/test_library_api.py` subsection header at line 985 read "**Exactly 10 new live HTTP tests**" while the body listed 13 and every other count cite (DoD item 15, KANBAN past-tense body, CHANGELOG bullet) said 13. Updated to "**Exactly 13 new live HTTP tests**".
  - **R3 — Implementation plan table.** Slice 4 row at line 922 had `New tests = 10` with the rev1 capability list of 10 items. Updated to `13` with the inline list extended to name the three new capabilities (flat-shorthand path / split-pair active-input-only permission / empty-list + null-direction no-ops). Line delta `+260 / -5` → `+330 / -5` to account for the three new test bodies.
  - **R4 — Decision 13 capability list.** The conceptual summary at line 898 still enumerated the rev1 10 capabilities. Extended to 13 with the three rev1-feedback additions (flat-shorthand, split-pair permission, two-no-op-cases) so Decision 13 and Slice 4 carry the same shape.
  - **N-new-1 — H4 deferral decoupled from connection-aware optimizer planning.** Decision 8 step 4's "deferred — likely to land alongside the same `0.0.9` cohort that ships connection-aware optimizer planning" rephrased per the reviewer's recommendation. The leak-closing design and connection-aware optimizer planning are orthogonal; pinning them to the same cohort risked future readers thinking the deferral was already scheduled. Now reads "deferred — likely to a sibling `0.0.9` ordering-permissions card; the connection-field cohort is the natural integration point but the leak-closing work is independent of connection-field design."
  - **N-new-2 — `_helper_referenced_ordersets` placement rationale refined.** Decision 2's `__init__.py` bullet justified the ledger's location by the import-dependency-avoidance argument, but `orders/__init__.py` already imports `INPUTS_MODULE_PATH` and `_input_type_name_for` from `inputs.py` (per the bullet immediately above), so the import dependency exists either way. Rewrote the rationale as a locality argument: the ledger is co-located with its only writer (`order_input_type`), matching the filter side's arrangement at `filters/__init__.py:48`. Same outcome, honest rationale.
  - **N-new-3 — `DEFERRED_META_KEYS` staleness caveat.** Decision 12's O1 forward-compat preview asserted "neither [`Meta.distinct` nor `Meta.distinct_class`] is in `DEFERRED_META_KEYS` today" as a stable-state claim. Updated to name the current `DEFERRED_META_KEYS` contents explicitly (`orderset_class`, `aggregate_class`, `fields_class`, `search_fields` per `base.py:48-55`) AND add a staleness caveat noting that the `0.0.9` design may add either key to `DEFERRED_META_KEYS` before its corresponding subsystem ships, per the deferred-key promotion-gate convention.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`OrderSet`][glossary-orderset] — the declarative ordering class this card ships (`planned for 0.0.8`). Reuses the six-layer lazy-resolution architecture from the shipped [`FilterSet`][glossary-filterset] subsystem with `OrderSet` substituted for `FilterSet` and `RelatedOrder` substituted for `RelatedFilter`.
- [`RelatedOrder`][glossary-relatedorder] — cross-relation ordering traversal (`planned for 0.0.8`). Accepts a target `OrderSet` class, an absolute import path string, or an unqualified name for circular references; lazy-resolved at finalizer time.
- [`Meta.orderset_class`][glossary-metaorderset_class] — the consumer-facing key (`planned for 0.0.8`) that points a [`DjangoType`][glossary-djangotype] at its `OrderSet`. Promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` per [Decision 7](#decision-7--metaorderset_class-promotion-gate).
- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type this card extends with an ordering sidecar. The `Meta`-driven shape is what makes `Meta.orderset_class = ItemOrder` legible to a Django audience.
- [`finalize_django_types`][glossary-finalize_django_types] — the synchronization point where the ordering subsystem's lazy-resolution pipeline runs (phase 2.5, the same seam [`Meta.interfaces = (relay.Node,)`][glossary-metainterfaces] and the shipped [`Meta.filterset_class`][glossary-metafilterset_class] use).
- [`FilterSet`][glossary-filterset] / [`RelatedFilter`][glossary-relatedfilter] / [`filter_input_type`][glossary-filter_input_type] / [`Meta.filterset_class`][glossary-metafilterset_class] — the sibling subsystem shipped in `DONE-027-0.0.8` whose architecture this card mirrors. Five of the six lazy-resolution layers carry over verbatim with the class substitution; Layer 6 (the dynamic-factory cache for connection fields without an explicit `*_class`) is the one genuinely fresh design question, resolved by [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the optimizer this card composes with. An `.order_by(...)` clause applied to a queryset must not break the optimizer's [Queryset diffing][glossary-queryset-diffing] cooperation; covered by [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) and a live HTTP test.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — pre-order visibility scoping. Composes with `RelatedOrder` traversal and with the filter subsystem's `check_*_permission` gates ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer)).
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — `0.0.9`; the consumer-facing surface that threads `orderBy:` arguments through. The factory machinery this card ships is the input it will consume, so the `0.0.8` deliverable is the back-end half of the `0.0.9` connection field's order surface.
- [`Meta.primary`][glossary-metaprimary] — the multi-`DjangoType`-per-model design from `0.0.6` whose [`TypeRegistry`][registry-typeregistry] keying convention this card respects per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation and finalization time for unknown ordering target classes, invalid field names, circular references that exhaust the resolution guard — see [Edge cases](#edge-cases-and-constraints).
- [`AggregateSet`][glossary-aggregateset] / [`get_child_queryset`][glossary-get_child_queryset] / [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — future Layer-3 sidecars referenced as the forward composition surface; not implemented here.
- [`FieldSet`][glossary-fieldset] / [`Meta.fields_class`][glossary-metafields_class] — `0.1.1` Layer-3 sidecar; orthogonal to ordering (field selection vs ordering).

Foundational invariants and cross-cutting surfaces a new dev will hit while reading this spec — all defined in [`docs/GLOSSARY.md`][glossary]:

- [Relation handling][glossary-relation-handling] — the package's existing FK / OneToOne / M2M / reverse-relation traversal that `RelatedOrder` plugs into.
- [Relay Node integration][glossary-relay-node-integration] — the 0.0.5 surface (`Meta.interfaces = (relay.Node,)`); ordering does NOT consult Relay shape (an `ORDER BY id` against a Relay-Node-shaped target uses the Django PK column, not the GraphQL `GlobalID`), so unlike the filter side's Decision 4 conditional, the ordering side has no Relay-vs-scalar branch.
- [Definition-order independence][glossary-definition-order-independence] — the `DONE-010-0.0.4` invariant the lazy-resolution pipeline preserves so cross-module `RelatedOrder("...")` references work regardless of import order.
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the deferred-Meta-key promotion rule lives here; [Decision 7](#decision-7--metaorderset_class-promotion-gate)'s promotion gate is one instance of the broader invariant applied to every Layer-3 sidecar.
- [Choice enum generation][glossary-choice-enum-generation] — choice-backed columns produce a Strawberry enum on the type side; the ordering side does not need to consult the enum (an `ORDER BY status` orders by the stored DB value).
- [Scalar field conversion][glossary-scalar-field-conversion] — the `SCALAR_MAP` the order field discovery consults to confirm a column is a real model field.
- [OptimizerHint][glossary-optimizerhint] — the hint primitive `Meta.optimizer_hints` declarations carry; ordering clauses compose with hints at queryset-translation time without retrofit.
- [only() projection][glossary-only-projection] — the optimizer's projection contract; an `order_by(...)` on a column already included by `.only(...)` cooperates without modification. **The optimizer itself does NOT inspect `queryset.query.order_by` to extend `plan.only_fields`** — verified per H2 of [`docs/feedback.md`][feedback] rev1 (no logic in [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker] or [`plans.py`][optimizer-plans] reads `queryset.query.order_by`). The user-visible behavior is correct because Django's ORM itself fetches columns needed to execute the `ORDER BY` clause regardless of the consumer's `.only(...)` hint — but the cooperation is Django's, not the package's. Order-aware projection augmentation is out of scope for `0.0.8` and not promised by this card.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule at [`AGENTS.md`][agents] #"package tests live under" (package tests under `tests/orders/` with `__init__.py` shells; example-project non-HTTP tests under `examples/fakeshop/tests/`; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority rule at [`AGENTS.md`][agents] #"any coverage line achievable via a real GraphQL query"; the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; the settings-keys rule at [`AGENTS.md`][agents] #"Add settings keys only when the feature that needs them lands"; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — [Slice 5](#slice-checklist) grants the explicit permission for this card.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical per [Decision 13](#decision-13--live-http-coverage-strategy).
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 5; the card body's `docs/spec-orders.md` reference predates the structured `spec-<NNN>-<topic>-<0_0_X>.md` convention and gets rewritten in the same Slice-5 sweep per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
- [`docs/TREE.md`][tree] — tests mirror source one-to-one. The subsystem lives at [`django_strawberry_framework/orders/`][orders] per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface); the mirror partner is `tests/orders/` (new tree). The "target package layout" section in `docs/TREE.md` already names the directory; this card flips it from `[alpha]` to on-disk.
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers).

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Six slices total.

- [ ] Slice 1: Foundation — module layout + `Order` / `RelatedOrder` primitives + `OrderSet` metaclass
  - [ ] Create [`django_strawberry_framework/orders/`][orders] subpackage with `__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface). Module-level docstrings on each file pin the responsibility (`base.py` = `Order` / `RelatedOrder` primitives + `LazyRelatedClassMixin`; `sets.py` = `OrderSet` + metaclass + `apply_sync` / `apply_async`; `factories.py` = `OrderArgumentsFactory`; `inputs.py` = order input classes materialized as module globals + `Ordering` enum + input-data adapters + lifecycle ledger).
  - [ ] `base.py` ships `RelatedOrder` (the `BaseRelatedOrder` port from [`django_graphene_filters/orders.py::BaseRelatedOrder`][upstream-cookbook-orders]) and reuses the shipped [`django_strawberry_framework/filters/base.py::LazyRelatedClassMixin`][filters-base] via a sibling import. The mixin is NOT duplicated — it is the same Layer-2 module-fallback resolution that the filter subsystem ships, shared across both subsystems.
  - [ ] `sets.py` ships `OrderSetMetaclass` (port from [`django_graphene_filters/orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset]) and `OrderSet` (port from [`django_graphene_filters/orderset.py::AdvancedOrderSet`][upstream-cookbook-orderset] — Layer 3 + Layer 4 of [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6)). `OrderSet` accepts [`Meta.model`][glossary-metamodel] and `Meta.fields` (list form `["name", "created_date"]` or `"__all__"` shorthand for every concrete model field excluding relations per [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6)), and per-field `check_<field>_permission` hooks. Adds the `_owner_definition: DjangoTypeDefinition | None` slot bound at finalizer phase 2.5 (mirrors the filter subsystem's H4 binding from [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 9). The resolver-facing API is the classmethod pair `apply_sync(input_value, queryset, info) -> QuerySet` / `apply_async(input_value, queryset, info) -> Awaitable[QuerySet]` per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer); each carries `info` end-to-end so per-field `check_<field>_permission` gates and active-input-only scope run consistently.
  - [ ] `inputs.py` IS the input-class namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) — generated order input classes are materialized as real module globals of `django_strawberry_framework.orders.inputs` via `materialize_input_class(name, cls)` (sets `sys.modules["django_strawberry_framework.orders.inputs"].<name> = cls`), keyed by stable class-derived names (e.g., `"BranchOrderInputType"`); a private `_materialized_names: dict[str, type[OrderSet]]` ledger tracks provenance for idempotent re-materialization. This module namespace is **disjoint** from the sibling `django_strawberry_framework.filters.inputs` namespace shipped in `DONE-027-0.0.8` — each Layer-3 subsystem owns its own per-module input-class namespace so `OrderSet` and `FilterSet` input classes never collide on the lookup path Strawberry's [`LazyType.resolve_type`][strawberry-lazy] uses.
  - [ ] `inputs.py` also ships the `Ordering` enum (`ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST` per [Decision 5](#decision-5--ordering-enum-and-argument-shape)) as a `@strawberry.enum` so leaf fields on every `OrderSet`-derived input type land with this enum as their field type.
- [ ] Slice 2: Factories — `OrderArgumentsFactory` BFS + inputs adapters
  - [ ] `factories.py` ships `OrderArgumentsFactory` (port from [`django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory`][upstream-cookbook-order-arguments-factory]) — Layer 5 of [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6). BFS walk that builds every reachable `strawberry.input` type; `_build_class_type` emits `@strawberry.input`-decorated classes via `django_strawberry_framework.orders.inputs.build_input_class(name, field_specs)` (the Strawberry-adapted analogue of Graphene's `type(name, (graphene.InputObjectType,), fields)`). Leaf fields use the `Ordering` enum from `inputs.py`; `RelatedOrder` fields emit `Annotated["<TargetOrderSet>InputType", strawberry.lazy("django_strawberry_framework.orders.inputs")] | None` references (the same Layer-5 cycle-safe forward-reference shape the filter subsystem ships per [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3).
  - [ ] `inputs.py` ships the input-data adapter functions: `_build_input_fields` (target-orderset references via `strawberry.lazy(...)` over module globals; leaf fields typed `Ordering | None`), `convert_order_field_to_input_annotation(model_field, owner_definition)` (the named scalar-field-to-Strawberry-input converter — for ordering, the converter always emits `Ordering | None` because the only legal input value for a leaf field is a direction, NOT the field's value), `normalize_input_value(order_set_class, raw_value)` (the runtime symmetric — walks the nested `RelatedOrder` input tree and produces a flat list of `(field_path, Ordering)` tuples that the apply pipeline turns into Django `order_by(...)` arguments).
- [ ] Slice 3: Wiring — `Meta.orderset_class` promotion + finalizer phase 2.5 binding
  - [ ] [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] grows an `orderset_class: type | None = None` field. The slot is populated by `DjangoType.__init_subclass__` from `Meta.orderset_class` once the key is promoted out of `DEFERRED_META_KEYS`.
  - [ ] [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] drops `"orderset_class"`. [`ALLOWED_META_KEYS`][base] grows `"orderset_class"`. The `_validate_meta` function validates the supplied class is an `OrderSet` subclass and raises [`ConfigurationError`][glossary-configurationerror] otherwise (mirrors the shipped `_validate_filterset_class` helper at [`django_strawberry_framework/types/base.py::_validate_filterset_class`][base]).
  - [ ] [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] grows a per-type order-binding pass in phase 2.5 (immediately after the existing `_bind_filtersets()` umbrella helper and before phase 3's `strawberry.type` decoration). The pass runs four ordered subpasses mirroring the **shipped** filter binding's discipline (verified at [`django_strawberry_framework/types/finalizer.py::_bind_filtersets`][finalizer]): (1) bind every `OrderSet`'s `_owner_definition` first, no `get_fields()` calls; (2) call `get_fields()` for every wired orderset only after every owner is bound — `ImportError` from unresolved `RelatedOrder("...")` rewraps as [`ConfigurationError`][glossary-configurationerror] with `__cause__` preserved (mirrors the filter side's `ImportError` rewrap); (3) **orphan-validate** `_helper_referenced_ordersets` against the set of wired ordersets — runs BEFORE materialization so an orphan failure leaves no partial state in `_materialized_names` or `OrderArgumentsFactory.input_object_types` (verbatim shape from the shipped filter side, where the same inversion is justified by avoiding stale-ledger entries on a re-run after the consumer fixes the orphan); (4) **materialize** input classes via `OrderArgumentsFactory(orderset_cls).arguments` plus a `materialize_input_class(name, cls)` call for every built class. `registry.clear()` invokes `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` so the model-to-`DjangoType` clear, the order-input clear, and the orphan-tracking clear share one entry point per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- [ ] Slice 4: Live HTTP coverage in fakeshop
  - [ ] [`examples/fakeshop/apps/library/`][fakeshop-library] grows `orders.py` containing `BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder` (mirrors the filter side's [`examples/fakeshop/apps/library/filters.py`][fakeshop-library] split — same set of `DjangoType` owners so the live HTTP test plan exercises filter / order composition end-to-end). The M2M side targets `GenreType`; `GenreOrder` lives in a **separate fixture module** [`examples/fakeshop/apps/library/orders_genre.py`][fakeshop-library] so this card's `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` declaration exercises the Layer-2 absolute-import-path lazy-resolution path (mirrors the filter side's [`examples/fakeshop/apps/library/filters_genre.py`][fakeshop-library] fixture). Same-module unqualified-name resolution is exercised by every other `RelatedOrder("...")` declaration in `orders.py`.
  - [ ] [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] grows `Meta.orderset_class = orders.BranchOrder` (etc.) on the corresponding `DjangoType` classes. Sibling library root-list resolvers (`all_library_branches`, `all_library_books`, etc.) annotate `orderBy:` via `order_input_type(orders.BranchOrder)` per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper). Each resolver **calls the owning type's `get_queryset(queryset, info)` BEFORE `OrderSet.apply_sync(...)` / `apply_async(...)`** (same security-correct ordering the filter side pins: visibility before order — although ordering does not see through visibility the way filtering can, the rule is one-directional discipline that keeps every resolver call site uniform). Resolvers that previously took only `filter:` grow a sibling `orderBy:` argument; chaining is `queryset = <Type>.get_queryset(...)` → `queryset = <Type>Filter.apply_sync(filter, queryset, info)` → `queryset = <Type>Order.apply_sync(order_by, queryset, info)` (filter narrows the rows, order arranges them).
  - [ ] [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows **exactly 13 new live `/graphql/` HTTP tests** covering: scalar-field ascending order (`name: ASC`); scalar-field descending order with NULLS positioning (`description: DESC_NULLS_LAST`); forward-FK relation order (`shelf: { code: ASC }`); reverse-FK relation order with **denormalized JOIN+ORDER multiplicity pinned explicitly** per M5 of [`docs/feedback.md`][feedback] rev1 (a `Branch` with N shelves appears N times in the response, each instance ordered by its individual shelf's code — that is the SQL contract, and the test seeds a multi-shelf Branch to verify the multiplication rather than dodging it); M2M relation order through the absolute-import-path `RelatedOrder` resolution (`genres: { name: ASC }`); flat-shorthand path order via `Meta.fields = ["shelf__code"]` rendering as `shelfCode: ASC` per M2 of [`docs/feedback.md`][feedback] rev1 (pins the path-based GraphQL field name that the runtime normalizer must reconstruct); composition with the shipped filter subsystem (`{ allLibraryBooks(filter: { ... }, orderBy: [...]) { ... } }` — pins filter and order compose cleanly without one clobbering the other); composition with the optimizer (`assertNumQueries(N)` against an ordered + filtered queryset with nested selection — pins that `.order_by(...)` does not break the optimizer's `select_related` / `prefetch_related` plan); root `get_queryset` honoring (ordering operates on the visibility-scoped queryset, not on the unscoped manager); split-pair active-input-only `check_<field>_permission` discipline per M6 of [`docs/feedback.md`][feedback] rev1 — `test_order_check_permission_denies_for_active_field` AND `test_order_check_permission_quiet_for_inactive_field`; multi-field priority ordering (`orderBy: [{ shelf: { code: ASC } }, { title: DESC }]` — pins that the list-shaped `orderBy:` argument processes elements in order so earlier list entries dominate later ones); empty-list / null-direction no-op edge cases per M7 of [`docs/feedback.md`][feedback] rev1 — `test_order_empty_list_passes_through` (`orderBy: []` returns the unordered queryset) AND `test_order_null_direction_skips_field` (`orderBy: [{ name: null }]` is treated as if the field were omitted).
- [ ] Slice 5: Docs + KANBAN + CHANGELOG + version bump (this card owns the joint cut)
  - [ ] [`docs/GLOSSARY.md`][glossary]: flip [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], and [`Meta.orderset_class`][glossary-metaorderset_class] from `planned for 0.0.8` to `shipped (0.0.8)`. Add a new entry `## order_input_type` documenting the consumer helper from [Decision 11](#decision-11--order_input_typeorderset-consumer-helper) — returns `Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` for resolver-argument annotations. Add a new entry `## Ordering` documenting the public direction enum from [Decision 5](#decision-5--ordering-enum-and-argument-shape) (`ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST`). Update the [Index][glossary-index] table with rows for all five entries (three flips + two new). Document `OrderSet` / `RelatedOrder` / `order_input_type` under the Ordering category of the [Browse by category][glossary] block.
  - [ ] [`docs/README.md`][docs-readme]: add `OrderSet` / `RelatedOrder` / `order_input_type` / `Meta.orderset_class` to the shipped-symbol bullet list under the `0.0.8` boundary (the version bump lands in this same Slice 5 commit per [Decision 10](#decision-10--joint-008-cut)).
  - [ ] [`docs/TREE.md`][tree]: flip the `orders/` subpackage entry from `[alpha]` to on-disk (move from the "target package layout" section to the "current on-disk layout" section). List the five new files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); list the mirrored `tests/orders/` tree.
  - [ ] [`README.md`][readme]: add `OrderSet` / `RelatedOrder` / `order_input_type` to the shipped-symbol bullet list (under the `0.0.8` boundary, alongside the filter symbols promoted in `DONE-027-0.0.8`'s Slice 5).
  - [ ] [`GOAL.md`][goal]: the astronomy showcase already references `Meta.orderset_class` and the per-app `orders.py` shape — no edit needed there beyond confirming the references resolve.
  - [ ] [`TODAY.md`][today]: extend the "Shipped capabilities" enumeration with `OrderSet` / `Meta.orderset_class` / `RelatedOrder`; extend the fakeshop section to mention the new live `BranchOrder` / `BookOrder` / `LoanOrder` / `PatronOrder` declarations and the order live HTTP tests under [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library].
  - [ ] [`KANBAN.md`][kanban]: move `WIP-ALPHA-028-0.0.8` to the Done column with the next available `DONE-NNN-0.0.8` id. Past-tense Done body pinned in [Doc updates](#doc-updates). Rewrite the card body's `Definition of done` bullet 1 (`docs/spec-orders.md` → `docs/spec-028-orders-0_0_8.md`).
  - [ ] [`CHANGELOG.md`][changelog]: append `### Added` bullets to `[Unreleased]` for `OrderSet`, `RelatedOrder`, `Meta.orderset_class`, `Ordering` enum, `order_input_type`. Append a `### Changed` bullet noting that `Meta.orderset_class` is no longer in `DEFERRED_META_KEYS`. Promote `[Unreleased]` to `[0.0.8] - <DATE>` (the `<DATE>` placeholder per N5 of [`docs/feedback.md`][feedback] rev1 is intentionally non-literal — the Slice 5 author substitutes the actual merge date at commit time; the `<DATE>` shape reads more clearly as "fill this in" than the conventional `YYYY-MM-DD` literal which can ship verbatim into the released changelog by accident) — this card is the joint-cut card per [Decision 10](#decision-10--joint-008-cut), so the promotion lands here alongside `[Unreleased]` entries previously accumulated by `DONE-027-0.0.8` (Filtering subsystem).
  - [ ] **Version bump quintet** (per [Decision 10](#decision-10--joint-008-cut) L5 contingency, triggered because this card is the last `0.0.8` card to ship): (a) `pyproject.toml`'s `version = "0.0.7"` → `version = "0.0.8"`; (b) [`django_strawberry_framework/__init__.py`'s `__version__ = "0.0.7"`][package-init] → `__version__ = "0.0.8"`; (c) [`tests/base/test_init.py`'s pinned version assertion][test-base-init] `"0.0.7"` → `"0.0.8"`; (d) the `[Unreleased]` → `[0.0.8] - <DATE>` promotion in `CHANGELOG.md` above; (e) a single commit message naming this card as the joint-cut owner.
- [ ] Slice 6: Cross-card composition smoke test with the shipped Filtering subsystem
  - [ ] One package-internal test under [`tests/orders/test_composition.py`][test-orders-composition] (new) that constructs a `DjangoType` with BOTH `Meta.filterset_class` AND `Meta.orderset_class` set, calls `finalize_django_types()`, and asserts both factories' input types are reachable from the schema AND a resolver that consumes both arguments produces a queryset whose SQL carries `WHERE <filter>` AND `ORDER BY <order>` clauses in the expected order. The Filtering subsystem already shipped, so the test does NOT need to wait for a sibling card; it lands in this card's PR as Slice 6 directly. (The Slice-6 conditional clause from the Filtering spec's [Slice checklist](#slice-checklist) — "carried by sibling" — is satisfied here by this card carrying the composition test instead.)

## Problem statement

`django-strawberry-framework`'s `0.0.7` surface ships a model-backed Strawberry type ([`DjangoType`][glossary-djangotype]), the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], the non-Relay [`DjangoListField`][glossary-djangolistfield], and the [Schema export management command][glossary-schema-export-management-command]; `0.0.8` adds the Filtering subsystem ([`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter], [`Meta.filterset_class`][glossary-metafilterset_class]). What remains for the `0.0.8` cut is the corresponding ordering surface — consumers cannot order the returned querysets through the GraphQL surface today. The `0.0.7` / Filtering audience (Django teams migrating from `graphene-django` or `strawberry-graphql-django`) reaches for `Meta.orderset_class = ItemOrder` immediately after wiring `Meta.filterset_class`, and the package's response is a [`ConfigurationError`][glossary-configurationerror] from [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] ("`Meta keys not supported yet: ['orderset_class']`").

Ordering pairs with filtering as the second ⚛️&🍓 parity-required Layer-3 capability for three reasons:

1. **Audience expectation.** `strawberry-graphql-django` ships `@strawberry_django.order_type(Model)` as a peer to `@strawberry_django.filter_type(...)`; `graphene-django` ships ordering via `django_filters.OrderingFilter` declared on the `FilterSet` (covered by `DONE-027-0.0.8`'s `django_filters.filterset.BaseFilterSet` foundation, but the GraphQL surface still needs an explicit `orderBy:` argument the consumer can write against). Both upstreams expect a working ordering surface in the same release cohort as the filter surface, not a release later.
2. **Foundation reuse, no new design.** Five of the six lazy-resolution layers from `DONE-027-0.0.8` carry over verbatim with `OrderSet` substituted for `FilterSet` and `RelatedOrder` substituted for `RelatedFilter`. The architectural answer is already pinned; the only genuinely fresh question is Layer 6's dynamic-factory cache, which has no cookbook counterpart — [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009) resolves it by deferring to `0.0.9` alongside the connection field that would consume the dynamic factory.
3. **Connection-field cohort completion.** Sibling [`AggregateSet`][glossary-aggregateset] (`0.1.3`) reuses the lazy-resolution architecture again; [`Meta.search_fields`][glossary-metasearch_fields] (`0.1.2`) reuses the `LOOKUP_PREFIXES` map from the filter subsystem; the eventual [`DjangoConnectionField`][glossary-djangoconnectionfield] (`0.0.9`) consumes the `OrderArgumentsFactory` output as the connection's `orderBy:` argument source. Shipping ordering alongside filtering closes the `0.0.8` cut and unblocks every `0.0.9` follow-on (the connection field, the full Relay story, connection-aware optimizer planning) so they reach for the same lazy-resolution shape this card pins.

`django-graphene-filters` (the working reference per [`START.md`][start] "Working reference") has already solved the hard part: the cookbook ships `AdvancedOrderSet`, `RelatedOrder`, `OrderArgumentsFactory`, `OrderDirection`, and `get_flat_orders` as a complete ordering surface. Layers 1-4 of the lazy-resolution pipeline port verbatim; Layer 5 reuses the same Strawberry adaptation the filter subsystem just shipped (`Annotated["TypeName", strawberry.lazy("module-path")]` over module globals). The cookbook's `OrderDirection` is replaced by strawberry-django's six-member `Ordering` enum per [Decision 5](#decision-5--ordering-enum-and-argument-shape) because the package's downstream consumers expect `NULLS_FIRST` / `NULLS_LAST` positioning more than they expect `DISTINCT ON` partitioning (the cookbook's `ASC_DISTINCT` / `DESC_DISTINCT` direction modifiers are deferred to `0.0.9` per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009)). The card body's `Verified in upstream` block pre-pins the strawberry-django shape; the rest of the work is mechanical: port the five reusable layers, adapt Layer 5 to `strawberry.lazy(...)`, wire the binding into the finalizer's phase 2.5, promote `Meta.orderset_class` once the end-to-end path is live, and stamp the joint-cut version bump.

## Current state

- [`django_strawberry_framework/orders/`][orders]: **does not exist on disk yet** — no skeleton modules, no TODO anchors. [`docs/TREE.md`][tree]'s "target package layout" section already names the directory and the five planned files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); this card flips the entry from `[alpha]` to on-disk by authoring every file from scratch (no pre-existing TODO substrate to extend, unlike the Filtering subsystem which had skeleton anchors before Slice-1 implementation per L1 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev8).
- [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base]: contains `"orderset_class"` (alongside three sibling Layer-3 keys: `"aggregate_class"`, `"fields_class"`, `"search_fields"`). The validator at `_validate_meta` raises [`ConfigurationError`][glossary-configurationerror] when any of these is declared.
- [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition]: carries the shipped `filterset_class: type | None = None` slot from `DONE-027-0.0.8` but no `orderset_class` slot yet. The dataclass is intentionally minimal — slots land with the feature.
- [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer]: runs three phases (1, 2, 2.5, 3); phase 2.5 currently handles `apply_interfaces` (Relay-Node wiring from `DONE-015-0.0.5`), `install_relay_node_resolvers`, and `_bind_filtersets()` (the four-subpass filter binding from `DONE-027-0.0.8`). The phase is the seam this card grows a fourth step into per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering): `_bind_ordersets()` mirroring the filter binding's four-subpass discipline.
- [`docs/GLOSSARY.md`][glossary]: [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], and [`Meta.orderset_class`][glossary-metaorderset_class] all carry `planned for 0.0.8` status today.
- [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]: exercises forward / reverse FK, forward / reverse OneToOne, forward / reverse M2M, choice-enum generation, `Meta.interfaces = (relay.Node,)` on `GenreType`, [`Meta.optimizer_hints`][glossary-metaoptimizer-hints] on `LoanType`, consumer-shaped querysets cooperating with the optimizer, and (post-`DONE-027-0.0.8`) `Meta.filterset_class` declarations on six library `DjangoType` classes. No order declarations today; the schema is the natural host for the live HTTP order coverage per [Decision 13](#decision-13--live-http-coverage-strategy).
- [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027]: the most-recently-shipped spec; the canonical voice / depth / section-layout reference for this spec AND the architectural template five of the six layers port from.
- [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020]: the Decision-10 joint-cut precedent (`0.0.7` five-card cohort) this card invokes via the L5 contingency since the Filtering subsystem already shipped without bumping.
- Upstream cookbook (working reference per [`START.md`][start]): [`~/projects/django-graphene-filters/django_graphene_filters/`][upstream-cookbook] — the five-layer pipeline this card ports verbatim through Layers 1–4 and Strawberry-adapts at Layer 5. Specifically: [`orders.py::BaseRelatedOrder`][upstream-cookbook-orders] / [`orders.py::RelatedOrder`][upstream-cookbook-orders] (Layer 1); [`mixins.py::LazyRelatedClassMixin`][upstream-cookbook-mixins] (Layer 2 — reused from the filter subsystem's shared port at [`django_strawberry_framework/filters/base.py::LazyRelatedClassMixin`][filters-base]); [`orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset] (Layer 3); [`orderset.py::AdvancedOrderSet`][upstream-cookbook-orderset] with `get_fields` / `get_flat_orders` (Layer 4); [`order_arguments_factory.py::OrderArgumentsFactory`][upstream-cookbook-order-arguments-factory] (Layer 5).
- Upstream `strawberry-graphql-django`: [`~/projects/strawberry-django-main/strawberry_django/ordering.py`][upstream-strawberry-ordering] — the single-file decorator-driven implementation. Provides the [`Ordering` enum][upstream-strawberry-ordering] (`ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST`), the [`OrderSequence`][upstream-strawberry-ordering] tie-breaker descriptor, the [`process_order`][upstream-strawberry-ordering] / [`process_ordering`][upstream-strawberry-ordering] / [`apply_ordering`][upstream-strawberry-ordering] runtime pipeline, and the [`ORDER_ARG = "order"`][upstream-strawberry-ordering] / [`ORDERING_ARG = "ordering"`][upstream-strawberry-ordering] module-level constants. The package borrows the `Ordering` enum shape verbatim per [Decision 5](#decision-5--ordering-enum-and-argument-shape) but otherwise follows the cookbook's `AdvancedOrderSet` runtime shape (the cookbook's `apply` semantics are simpler and align with the package's `Meta`-driven posture).
- Upstream `graphene-django`: [`~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField`][upstream-graphene-filter-fields] #"order_by" — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the `FilterSet`. **`graphene-django` has no separate ordering primitive**; ⚛️ parity is met by the filter subsystem (`DONE-027-0.0.8`) rather than this card. The package's `OrderSet` is the 🍓-side counterpart that ⚛️ consumers do not have a direct equivalent for — but the consumer-facing shape (Meta-class declaration, `RelatedOrder` traversal, per-field permission gates) is what makes the package's ordering surface DRF-shaped rather than Strawberry-shaped, so the absence of a Graphene primitive does not change the package's design.

## Goals

1. Ship `OrderSet` + `RelatedOrder` + per-field `check_*_permission` gates + cross-relation traversal with cycle-safe lazy resolution, mirroring the shipped `DONE-027-0.0.8` Filtering subsystem's architecture with the class substitution.
2. Promote [`Meta.orderset_class`][glossary-metaorderset_class] out of `DEFERRED_META_KEYS` only when the ordering subsystem applies the configured class end-to-end — same gate as [`Meta.interfaces`][glossary-metainterfaces] in `DONE-015-0.0.5` and [`Meta.filterset_class`][glossary-metafilterset_class] in `DONE-027-0.0.8`.
3. Compose cleanly with the shipped Filtering subsystem at the resolver layer (filter narrows the rows, order arranges them) and with the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] without retrofit — an `.order_by(...)` clause is just another queryset method call before the optimizer walks the selection tree.
4. Reuse the shipped per-module input-class namespace lifecycle pattern from [`django_strawberry_framework.filters.inputs`][filters-inputs] verbatim (separate `django_strawberry_framework.orders.inputs` module globals; `materialize_input_class` / `clear_order_input_namespace` / `_materialized_names` ledger; `registry.clear()` co-clears both namespaces).
5. Expose enough introspection (`OrderSet.get_fields()`, `OrderArgumentsFactory(cls).arguments`) for a maintainer to ask "what ordering surface does this type support?" from the REPL in one call — same shape the Filtering subsystem ships.
6. Earn package coverage through live fakeshop HTTP flows per [Decision 13](#decision-13--live-http-coverage-strategy); the package coverage gate (`fail_under = 100`) is reached because the live HTTP tests exercise the package end-to-end.
7. **Stamp the joint-cut version bump** per [Decision 10](#decision-10--joint-008-cut)'s L5 contingency — since this card is the last `0.0.8` card to ship, Slice 5 owns the `0.0.7 → 0.0.8` bump quintet (`pyproject.toml`, `__version__`, `tests/base/test_init.py`, `[Unreleased] → [0.0.8]` in `CHANGELOG.md`, and the docs/README sweep that follows from the bump).

## Non-goals

- **Aggregation / fieldsets / permissions cascade.** Each ships in its own card. Composition with this card is forward-only; no Layer-3 sibling is implemented here.
- **`DjangoConnectionField` integration.** The `0.0.9` connection field consumes the factory machinery this card ships; the connection-field surface itself is out of scope.
- **`DjangoListField` orderBy-argument integration.** [`DjangoListField`][glossary-djangolistfield] (shipped `0.0.7`) currently wraps resolvers with a two-argument `(root, info)` callable that does NOT preserve or expose arbitrary resolver arguments. Adding an `orderBy:` argument to `DjangoListField` requires the same argument-injection design the filter side already deferred (per M3 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev8 feedback). `0.0.8` consumers reach for `order_input_type(...)` through **plain `@strawberry.field` resolvers ONLY**; the `DjangoListField` integration is **deferred to `0.0.9`** alongside `DjangoConnectionField`'s filter / order integration.
- **`DISTINCT ON` partitioning** (the cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` modifiers and [`AdvancedOrderSet.apply_distinct`][upstream-cookbook-orderset] Window-function fallback). Deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009) — the package ships the six-member `Ordering` enum (`ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST`) per [Decision 5](#decision-5--ordering-enum-and-argument-shape), and DISTINCT ON ships as a separate sub-feature in `0.0.9` (likely as a sibling `Meta.distinct` key + a `distinct_on:` argument).
- **Layer 6 (memoized dynamic `OrderSet` generation).** The cookbook ships no `orderset_factories.py` and no `_dynamic_orderset_cache` — only the filter side has the dynamic-factory mechanism. Deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009); when [`DjangoConnectionField`][glossary-djangoconnectionfield] lands in `0.0.9`, the connection-field card decides whether to design a Layer 6 fresh or require an explicit `orderset_class` declaration on every connection field. The `0.0.8` shape requires the explicit declaration; the dynamic-factory mechanism would be invented for a consumer surface that hasn't shipped yet.
- **`OrderSequence` tie-breaker descriptor** (per [`~/projects/strawberry-django-main/strawberry_django/ordering.py::OrderSequence`][upstream-strawberry-ordering]). The list-shaped `orderBy:` argument's element order IS the tie-breaker mechanism (earlier list entries dominate later ones); shipping a separate `OrderSequence` descriptor is redundant when the GraphQL surface already gives the consumer positional control.
- **Replacing the optimizer's queryset-diffing contract.** Orders land as `.order_by(...)` calls before the optimizer walks the selection tree; the existing cooperation contract is untouched.
- **Auto-generation of `OrderSet` from `Meta.fields` without declaring an explicit class.** Deferred; the dynamic-factory machinery (Layer 6) exists for the connection-field path where the connection field can pre-declare `model=Item, fields="__all__"` without a sibling `OrderSet` class. Direct consumer-facing implicit generation lands when [`DjangoConnectionField`][glossary-djangoconnectionfield] ships in `0.0.9`.

## Borrowing posture

Ordering is the second Layer-3 subsystem to ship. The architectural answer is pre-pinned by the shipped Filtering subsystem ([`DONE-027-0.0.8`][kanban] / [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027]); this spec preserves it via class substitution without re-litigation.

### From `django-graphene-filters` — borrow heavily (the cookbook is the working reference)

Local source path: [`~/projects/django-graphene-filters/django_graphene_filters/`][upstream-cookbook]. Per [`START.md`][start] ("Working reference") this cookbook is the package's canonical Layer-3 reference; the goal is to recreate "what the package enables for the schema author," not to port Graphene internals. Five of the six lazy-resolution layers are library-agnostic Python and port verbatim:

- [`orders.py::BaseRelatedOrder`][upstream-cookbook-orders] → `django_strawberry_framework.orders.base::RelatedOrder` (Layer 1; mirrors the filter side's `BaseRelatedFilter` → `RelatedFilter` port from `DONE-027-0.0.8`).
- [`mixins.py::LazyRelatedClassMixin`][upstream-cookbook-mixins] → **shared** with the filter subsystem (Layer 2 — the package's `LazyRelatedClassMixin` lives at [`django_strawberry_framework/filters/base.py::LazyRelatedClassMixin`][filters-base] and is reused by both subsystems via sibling import; per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) the mixin is NOT duplicated in `orders/base.py`).
- [`orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset] → `django_strawberry_framework.orders.sets::OrderSetMetaclass` (Layer 3; leaner than the filter side's `FilterSetMetaclass` because the cookbook's metaclass has no operator-bag / lookup-set discovery — the discover-and-bind pattern is identical otherwise).
- [`orderset.py::AdvancedOrderSet`][upstream-cookbook-orderset] → `django_strawberry_framework.orders.sets::OrderSet`, with `get_fields` doing Layer-4 cycle-safe expansion (port verbatim; the cookbook's expansion already uses the `__dict__["_expanded_fields"]` / `__dict__["_is_expanding_fields"]` guard pattern — same as the filter side's `_expanded_filters` / `_is_expanding_filters`, with the field naming swapped).
- [`orderset.py::AdvancedOrderSet.check_permissions`][upstream-cookbook-orderset] → port verbatim with **active-input-only scope** per the shipped filter subsystem's `check_permissions` shape — the per-field `check_<field>_permission(request)` gate runs only when the consumer's input names the field, NOT for every declared field. The cookbook recurses into child ordersets through `related_orders`; the package preserves that recursion under the same active-input-only narrowing the filter side ships.
- [`orderset.py::AdvancedOrderSet.get_flat_orders`][upstream-cookbook-orderset] → port verbatim — recursive parse of nested `OrderSet` input into flat ORM paths (e.g., `["name", "shelf__code", "-genres__name"]`). The cookbook's algorithm handles same-model fields, `RelatedOrder` traversal, and direction prefixes (`-` for `DESC`) in one pass; the package's port additionally maps the six-member `Ordering` enum's `NULLS_FIRST` / `NULLS_LAST` members into the `F(field).asc(nulls_first=...)` / `F(field).desc(nulls_last=...)` form rather than the bare string prefix (`-name`), so the queryset gets `OrderBy` expressions with NULLS positioning honored.
- [`order_arguments_factory.py::OrderArgumentsFactory`][upstream-cookbook-order-arguments-factory] → port verbatim — BFS walk that builds every reachable `strawberry.input` type (Layer 5; same shape as the filter side's `FilterArgumentsFactory`).

What the cookbook ships that this card does NOT borrow:

- [`order_arguments_factory.py::OrderDirection`][upstream-cookbook-order-arguments-factory] (the four-member `ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT` graphene enum) — replaced by the six-member `Ordering` enum from `strawberry-django` per [Decision 5](#decision-5--ordering-enum-and-argument-shape). The DISTINCT ON capability the cookbook's `_DISTINCT` members enable is deferred to `0.0.9` per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).
- [`orderset.py::AdvancedOrderSet.apply_distinct`][upstream-cookbook-orderset] / [`_apply_distinct_postgres`][upstream-cookbook-orderset] / [`_apply_distinct_emulated`][upstream-cookbook-orderset] (the cookbook's Window-function fallback for DISTINCT ON emulation on non-PostgreSQL backends). Deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).

### From `strawberry-graphql-django` — borrow the `Ordering` enum shape (and the runtime-pipeline pattern)

Local source path: [`~/projects/strawberry-django-main/strawberry_django/ordering.py`][upstream-strawberry-ordering]. The upstream's single-file decorator-driven implementation is conceptually parallel at the runtime layer ([`process_order`][upstream-strawberry-ordering] compiles input values into queryset arguments) but the declaration surface diverges per the package's DRF-shaped positioning. Borrow the [`Ordering`][upstream-strawberry-ordering] enum verbatim and the runtime contract loosely; don't borrow the decorator-on-order-type surface:

- [`ordering.py::Ordering`][upstream-strawberry-ordering] — the public direction enum: `ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST`. Borrowed verbatim per [Decision 5](#decision-5--ordering-enum-and-argument-shape) because the `NULLS_FIRST` / `NULLS_LAST` positioning is more broadly useful than the cookbook's `DISTINCT` modifiers.
- [`ordering.py::OrderSequence`][upstream-strawberry-ordering] — the per-field sequence descriptor for tie-breaking when multiple fields participate. **NOT borrowed** — the list-shaped `orderBy: [<T>OrderInput!]` argument's element order IS the tie-breaker mechanism (per [Decision 5](#decision-5--ordering-enum-and-argument-shape)).
- [`ordering.py::process_order`][upstream-strawberry-ordering] / [`apply_ordering`][upstream-strawberry-ordering] — the runtime side of the ordering pipeline. The package's `OrderSet.apply_sync(input_value, queryset, info)` / `apply_async(...)` classmethod pair is the equivalent consumer-facing entry point; both compile a Strawberry/Graphene input into queryset `order_by(...)` args.
- [`ordering.py::ORDER_ARG`][upstream-strawberry-ordering] (`= "order"`) and [`ordering.py::ORDERING_ARG`][upstream-strawberry-ordering] (`= "ordering"`) — module-level constants for the singular one-of and list GraphQL argument names. **NOT borrowed as a pair** — the package ships a single list-shaped `orderBy: [<T>OrderInput!]` argument per [Decision 5](#decision-5--ordering-enum-and-argument-shape); the singular `order:` variant is redundant when a list with one element produces the same SQL. Constant name in the package: `ORDER_BY_ARG = "orderBy"` (the GraphQL surface name; Strawberry's auto-camel-case translates from the Python attr `order_by` automatically).
- [`ordering.py::StrawberryDjangoFieldOrdering`][upstream-strawberry-ordering] — the field-base subclass that injects the order arguments on a Django-backed field. **NOT borrowed** — the package's `Meta`-driven shape forbids subclassing Strawberry field classes for consumer-facing declarations; the equivalent is `order_input_type(OrderSet)` per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper) on a plain `@strawberry.field` resolver.
- [`ordering.py::order_type`][upstream-strawberry-ordering] (`@strawberry_django.order_type(Model)`) — current consumer-facing decorator. **NOT borrowed** (the package's `Meta`-driven shape per [`START.md`][start] "Style they care about" forbids decorator-on-order-type for consumer-facing classes).
- [`ordering.py::order`][upstream-strawberry-ordering] — legacy decorator alias marked `@deprecated("strawberry_django.order is deprecated in favor of strawberry_django.order_type.")`; **NOT borrowed** (the package's first-ship surface does not need a legacy alias; the deprecation note in the upstream confirms the alias is dead code, not a parity target).

### From `graphene-django` — no separate ordering primitive to borrow

`graphene-django` has no `OrderSet` equivalent — ordering is handled by `django_filters.OrderingFilter` declared on the `FilterSet` (which `DONE-027-0.0.8` already covers via the `django_filters.filterset.BaseFilterSet` parent class). ⚛️ parity is met by the filter subsystem rather than this card; the card body's `Verified in upstream` block notes this explicitly. The package's `OrderSet` IS new surface for ⚛️ consumers, who gain a more powerful ordering shape (`RelatedOrder` traversal + per-field permission gates + NULLS positioning + composable with the package's DRF-shaped filter declaration) than they had with the bare `django_filters.OrderingFilter`. The cookbook's [`AdvancedOrderSet`][upstream-cookbook-orderset] is the closest precedent — and the cookbook is itself ⚛️-shaped (graphene-backed); the package's port carries that DRF-shaped lineage forward onto the Strawberry engine.

### Explicitly do not borrow

- **Graphene's `lambda: target_input_type` cycle-safe forward references** (from [`order_arguments_factory.py::OrderArgumentsFactory._build_class_type`][upstream-cookbook-order-arguments-factory] line 127's `lambda tn=target_name: self.input_object_types[tn]` form). Replaced by `Annotated["{TargetOrderSet}InputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` at Layer 5 (same Strawberry-adapted shape the filter subsystem ships per [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3).
- **`@strawberry_django.order_type(Model, ordering=Ordering)` decorator surface.** The package's `Meta`-driven shape per [`START.md`][start] "Meta classes everywhere on consumer surfaces" forbids decorator-on-input-type for consumer-facing classes.
- **The cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT`.** Direction modifiers conflating ordering with DISTINCT ON partitioning are confusing in a six-member enum that already needs NULLS positioning; deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009) to a separate `Meta.distinct` key + `distinct_on:` argument design in `0.0.9`.

## User-facing API

The shipped consumer surface adds five new symbols re-exported from `django_strawberry_framework.orders` — `OrderSet`, `RelatedOrder`, `Ordering` (the six-member direction enum), `order_input_type` (the resolver-annotation helper), and (internally registered) the input-class module-globals registry. The [`Meta.orderset_class`][glossary-metaorderset_class] hook is the consumer-facing wiring on the existing [`DjangoType`][glossary-djangotype] surface; `order_input_type(OrderSet)` is the resolver-annotation helper that lets a normal `@strawberry.field` resolver accept an `orderBy:` argument that resolves to the generated input class at schema-build time.

**Resolver-facing API split (mirrors `DONE-027-0.0.8`'s sync/async split).** Consumers call `OrderSet.apply_sync(...)` from sync resolvers and `OrderSet.apply_async(...)` from async resolvers per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer). The cookbook's `AdvancedOrderSet.__init__`-driven application (Django form-data style) is the runtime substrate; the classmethod API is the GraphQL-resolver-facing wrapper.

### Default usage — declaring an `OrderSet`

```python
from django_strawberry_framework.orders import OrderSet, RelatedOrder

from . import models


class GalaxyOrder(OrderSet):
    # Reverse FK — referenced lazily by string so Galaxy and CelestialBody
    # ordersets can live in the same file without an import cycle.
    celestial_bodies = RelatedOrder("CelestialBodyOrder", field_name="celestial_bodies")

    class Meta:
        model = models.Galaxy
        fields = "__all__"

    def check_name_permission(self, request):
        """Only staff users may order by Galaxy.name."""
        from graphql import GraphQLError
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to order by Galaxy name.")


class CelestialBodyOrder(OrderSet):
    galaxy = RelatedOrder(GalaxyOrder, field_name="galaxy")

    class Meta:
        model = models.CelestialBody
        # Explicitly list only "name" and "body_type" — "description" is intentionally
        # excluded so consumers can't `ORDER BY description` (large TEXT column).
        fields = ["name", "body_type"]
```

`OrderSet` does NOT subclass any third-party class (the filter subsystem subclasses `django_filters.filterset.BaseFilterSet` because `django-filter` is already a hard dependency and provides load-bearing form-cleaning machinery; the cookbook's `AdvancedOrderSet` is a plain `type`-derived class with no `django-filter` inheritance, and the package's `OrderSet` follows that shape). Consumers familiar with `django-filter`'s `OrderingFilter` will recognize the Meta-class declaration; consumers familiar with `strawberry-graphql-django`'s `@order_type(Model)` will recognize the `Ordering` enum on the GraphQL surface.

### Wiring into a `DjangoType`

```python
from django_strawberry_framework import DjangoType

from . import models, orders


class GalaxyType(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = "__all__"
        orderset_class = orders.GalaxyOrder
```

`Meta.orderset_class` is the only wiring required at the `DjangoType` site. The finalizer-phase-2.5 binding (per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)) takes care of input-class materialization (as module globals of [`django_strawberry_framework.orders.inputs`][orders-inputs]), lazy-related-order resolution, and registry registration.

### Exposing the `orderBy:` argument on a resolver

```python
import strawberry

from django_strawberry_framework.orders import order_input_type

from . import models, orders


@strawberry.type
class Query:
    @strawberry.field
    def all_galaxies(
        self,
        info: strawberry.Info,
        order_by: order_input_type(orders.GalaxyOrder) | None = None,
    ) -> list["GalaxyType"]:
        queryset = GalaxyType.get_queryset(models.Galaxy.objects.all(), info)
        if order_by is not None:
            queryset = orders.GalaxyOrder.apply_sync(order_by, queryset, info)
        return queryset
```

The Strawberry auto-camel-case converts the Python `order_by` parameter into the GraphQL `orderBy:` argument; consumers writing GraphQL queries see `{ allGalaxies(orderBy: [{ name: ASC }, { celestialBodies: { bodyType: DESC } }]) { id } }`. The resolver pattern is **`get_queryset` → optional `Filter.apply_sync` → optional `Order.apply_sync`** — the same shape `DjangoConnectionField` will compose internally in `0.0.9`.

**Note on `noqa: A002` (per N9 of [`docs/feedback.md`][feedback] rev1).** The Python parameter name `order_by` does NOT shadow a Python builtin, so it does not need the `# noqa: A002` discipline the shipped filter side applies on `filter:` arguments (the filter side's `filter` parameter DOES shadow Python's `filter` builtin, hence the suppression at [`examples/fakeshop/apps/library/schema.py:185`][fakeshop-library-schema]). The package's resolver-pattern guidance for **future** keyword arguments may need the same discipline: `aggregate:` does not shadow a builtin; `order:` does not shadow a builtin; `search:` does not shadow a builtin; `input:` (if a future card adds an `input` resolver argument) DOES shadow Python's `input` builtin and would need `# noqa: A002` to silence the lint rule. Documented here so a future card author doesn't have to rediscover the convention.

### Composing with the shipped Filtering subsystem

```python
@strawberry.field
def all_library_books(
    self,
    info: strawberry.Info,
    filter: filter_input_type(filters.BookFilter) | None = None,  # noqa: A002  (filter shadows builtin)
    order_by: order_input_type(orders.BookOrder) | None = None,
) -> list["BookType"]:
    queryset = BookType.get_queryset(models.Book.objects.all(), info)
    if filter is not None:
        queryset = filters.BookFilter.apply_sync(filter, queryset, info)
    if order_by is not None:
        queryset = orders.BookOrder.apply_sync(order_by, queryset, info)
    return queryset
```

The ordering applies AFTER the filter (filter narrows the rows, order arranges them). Either argument is optional; both can be present; neither is required.

### Per-field permission gates

```python
class GalaxyOrder(OrderSet):
    class Meta:
        model = models.Galaxy
        fields = "__all__"

    def check_name_permission(self, request):
        """Only staff users may order by Galaxy.name. Fires only when the
        consumer's input names the `name` field (active-input-only scope,
        same discipline the filter subsystem ships per
        docs/spec-027-filters-0_0_8.md Decision 8 M2 of rev5)."""
        from graphql import GraphQLError
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError(
                "You must be a staff user to order by Galaxy name.",
                extensions={"code": "ORDER_PERMISSION_DENIED"},
            )
```

The denial gate raises `GraphQLError`; the consumer sees a structured response error with the named `extensions.code`. The gate does NOT fire when the consumer's `orderBy:` input omits the `name` field (active-input-only — the rationale matches the filter side's: permissions gate USE of the order field, not its declaration).

### Multi-field priority ordering

```graphql
{
  allLibraryBooks(orderBy: [
    { shelf: { code: ASC } },
    { title: DESC_NULLS_LAST }
  ]) {
    id title shelf { code }
  }
}
```

The list-shaped argument's element order IS the tie-breaker mechanism — earlier list entries dominate later ones. The example produces SQL `ORDER BY library_shelf.code ASC, library_book.title DESC NULLS LAST` (with the `NULLS_LAST` positioning honored via Django's `F('title').desc(nulls_last=True)` expression form).

### Error shapes

- Invalid `Meta.fields` member (a field name that doesn't exist on the model): [`ConfigurationError`][glossary-configurationerror] at type-creation time naming the offending field and the model.
- Unresolved `RelatedOrder("...")` target at finalize: [`ConfigurationError`][glossary-configurationerror] naming both resolution attempts (the absolute-path attempt AND the bound-module-prefixed retry) per the shared `LazyRelatedClassMixin.resolve_lazy_class` shape from `DONE-027-0.0.8`.
- `Meta.orderset_class = NotAnOrderSet`: [`ConfigurationError`][glossary-configurationerror] at type-creation time naming both the offending value and the expected `OrderSet` subclass shape.
- `check_<field>_permission(request)` denial inside an active branch: `GraphQLError("...", extensions={"code": "ORDER_PERMISSION_DENIED"})` propagating to the GraphQL response.
- Orphan `OrderSet` referenced via `order_input_type(StandaloneOrder)` but never wired via `Meta.orderset_class`: [`ConfigurationError`][glossary-configurationerror] at finalize time naming the orphan (mirrors the filter side's H5 orphan validation from `DONE-027-0.0.8`).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-028-orders-0_0_8.md`** (this document), NOT `docs/spec-orders.md` as the [`KANBAN.md`][kanban] card body's `Definition of done` bullet 1 names it.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 and observed by every recent spec ([`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018], [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019], [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020], [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021], [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022], [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023], [`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][spec-025], [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027]) bakes the card's NNN and target patch into the filename.
- The card body's `docs/spec-orders.md` predates that convention.
- The topic slug is `orders` (matching the [`django_strawberry_framework/orders/`][orders] subpackage name, the cookbook's `orders.py` filename, and the filter side's `filters` precedent).
- The Slice-5 [`KANBAN.md`][kanban] rewrite updates the card body's stale reference to the canonical name, so the cross-reference resolves after archival per [Step 8 of NEXT.md][next-step-8].

Alternatives considered (and rejected):

- **Honor the card body verbatim with `docs/spec-orders.md`.** Rejected: breaks the structured-filename convention and would land an unnumbered spec next to a numbered cohort.
- **Longer topic slug `ordering_subsystem`** (matching the card title "Ordering subsystem"). Rejected: `orders` already names the architectural intent, matches the subpackage name, and matches the filter side's `filters` precedent — symmetry across the two sibling Layer-3 subsystems makes future Aggregation-card naming (`aggregates`) self-consistent.

### Decision 2 — Subpackage layout and public export surface

The order subsystem ships as a subpackage at **[`django_strawberry_framework/orders/`][orders]** (NOT a flat single-file module). Five files mirror the shipped Filtering subsystem layout:

- `__init__.py` — re-exports `OrderSet`, `RelatedOrder`, `Ordering`, `order_input_type` (the consumer helper per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper)), and (for advanced uses) the internal symbols `OrderSetMetaclass`, `OrderArgumentsFactory`.
- `base.py` — `RelatedOrder` (the cookbook's `BaseRelatedOrder` port). The shared [`LazyRelatedClassMixin`][filters-base] from the shipped filter subsystem is reused via sibling import (`from django_strawberry_framework.filters.base import LazyRelatedClassMixin`); the mixin is NOT duplicated.
- `sets.py` — `OrderSetMetaclass`, `OrderSet` (with `Meta.model`, `Meta.fields`, `_owner_definition: DjangoTypeDefinition | None` slot bound at finalizer phase 2.5 per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle); the resolver-facing classmethod **pair** `apply_sync(input_value, queryset, info) -> QuerySet` / `apply_async(input_value, queryset, info) -> Awaitable[QuerySet]` per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer); `get_fields`, `get_flat_orders` (the cookbook's recursive parse), `check_permissions` (active-input-only scope per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer))). **No `apply(...)` dispatcher is shipped** — per H1 of [`docs/feedback.md`][feedback] rev1, the filter side's `apply(...)` exists to detect and rewrap a sync-misuse `RuntimeError` raised when a `RelatedFilter` target declares an `async def get_queryset`; the order side has no equivalent code path (per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4, ordering never re-derives child visibility querysets) so a symmetric `apply` dispatcher would never fire. Consumers call `OrderSet.apply_sync(...)` from sync resolvers and `await OrderSet.apply_async(...)` from async resolvers — the dispatch is trivially explicit. Dead-weight abstraction with no observable behavior is not shipped (YAGNI).
- `factories.py` — `OrderArgumentsFactory` (Layer 5 BFS, deriving input field types from the resolved fields on `orderset_cls.get_fields()`).
- `inputs.py` — the `Ordering` enum (the six-member direction enum per [Decision 5](#decision-5--ordering-enum-and-argument-shape)); per-module input-class namespace; module-level constant `INPUTS_MODULE_PATH: str = "django_strawberry_framework.orders.inputs"` per M3 of [`docs/feedback.md`][feedback] rev1 (hoisted at the top of the file and used in every `strawberry.lazy(INPUTS_MODULE_PATH)` call site AND in `sys.modules[INPUTS_MODULE_PATH]` inside `materialize_input_class` — mirrors the filter side's [`INPUTS_MODULE_PATH`][filters-inputs] at `filters/inputs.py:53`); module-level helper `_input_type_name_for(orderset_class) -> str` returning `f"{orderset_class.__name__}InputType"` (mirrors the filter side's [`_input_type_name_for`][filters-inputs] at `filters/inputs.py:183` — used by `materialize_input_class`, `order_input_type`, `OrderArgumentsFactory`, and `_build_input_fields` so the `<Name>InputType` formula lives in one place rather than inline at every call site); `build_input_class`, `_build_input_fields`, `convert_order_field_to_input_annotation(model_field, owner_definition)` (the named scalar-field-to-Strawberry-input converter that always emits `Ordering | None` for leaf fields), `normalize_input_value(order_set_class, raw_value)` (the runtime symmetric — walks nested `RelatedOrder` input into a flat list of `(field_path, Ordering)` tuples), `materialize_input_class`, `clear_order_input_namespace`, `_materialized_names`.
- `__init__.py` — re-exports `OrderSet`, `RelatedOrder`, `Ordering`, `order_input_type` per the public-export section above; also hosts the **orphan-tracking ledger** `_helper_referenced_ordersets: set[type[OrderSet]]` per M9 of [`docs/feedback.md`][feedback] rev1 (parallel to the filter side's [`_helper_referenced_filtersets`][filters-base] at `filters/__init__.py:48`). **Placement rationale (refined per N-new-2 of [`docs/feedback.md`][feedback] rev2):** the ledger is **co-located with its only writer** — `order_input_type` is defined in `__init__.py` and writes to the set every time a consumer references it, so the ledger lives next to the function that mutates it. (`__init__.py` already imports `INPUTS_MODULE_PATH` and `_input_type_name_for` from `inputs.py` per the previous bullet, so the import dependency between the two modules exists regardless; co-location is a locality argument, NOT an import-dependency argument.) Matches the filter side's arrangement at `filters/__init__.py:48` exactly. `registry.clear()` clears `_helper_referenced_ordersets` and `inputs._materialized_names` as **two separate blocks** (one block per module) per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle); the two ledgers track unrelated lifecycle state (helper-set tracks consumer resolver-annotation references; materialized-names tracks finalizer-side Strawberry class registrations) and merging them into one block would couple two unrelated symbols.

Public re-export from `django_strawberry_framework` is opted-in by the subpackage's `__init__.py`, NOT by the top-level package: consumers `from django_strawberry_framework.orders import OrderSet, RelatedOrder, Ordering, order_input_type` (matching the import shape in [`GOAL.md`][goal]'s astronomy showcase). The top-level package's `__all__` is unchanged in `0.0.8` — adding the order symbols to the top-level surface widens it for every consumer including those who never use ordering; the subpackage import path is the right grain (mirrors the filter side's Decision 2 from [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027]).

Justification:

- The subsystem's surface is large enough (~6 public symbols + 5 internal symbols) that a flat module would be awkward to read; matches the filter side's five-file layout exactly so future maintainers see one shape across both subsystems.
- The target package layout in [`docs/TREE.md`][tree] already names the directory; this card flips it from `[alpha]` to on-disk without renaming.
- The mirror partner is `tests/orders/` (new tree) — **7 files total** per N4 of [`docs/feedback.md`][feedback] rev1: 1 `__init__.py` shell + 4 mirror test files (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`) + 1 phase-2.5-binding-pass test (`test_finalizer.py`) + 1 cross-card composition test (`test_composition.py`, Slice 6). Slice 1-3 land the shell + 4 mirror + `test_finalizer.py` (6 files); Slice 6 adds `test_composition.py` (7th).
- Subpackage-scoped re-export matches how `AggregateSet` will land at `django_strawberry_framework/aggregates/__init__.py` in `0.1.3`. The five sibling Layer-3 subpackages line up cleanly without each one bloating the top-level `__all__`.
- The shared `LazyRelatedClassMixin` lives in [`django_strawberry_framework/filters/base.py`][filters-base] (where it shipped in `DONE-027-0.0.8`); duplicating it under `orders/base.py` would silently bifurcate the resolution behavior if a future maintainer fixes one copy and forgets the other. Sibling import keeps both subsystems honest to one resolution algorithm.

Alternatives considered (and rejected):

- **Flat `django_strawberry_framework/orders.py` single-file module.** Rejected: the surface is too large; review legibility suffers; symmetry with the filter side's five-file layout breaks.
- **Top-level public re-export (`from django_strawberry_framework import OrderSet`).** Rejected: the surface is opt-in for consumers who actually use ordering; widening the top-level `__all__` for every consumer (including the optimizer-only ones) creates churn and a longer Index in `docs/GLOSSARY.md`.
- **Move `LazyRelatedClassMixin` to a new `django_strawberry_framework/utils/lazy_class.py` shared module.** Rejected for the `0.0.8` cut: the move is mechanical churn that touches the shipped filter subsystem's imports for zero behavioral benefit. The mixin's home stays at `filters/base.py` (where it shipped); `orders/base.py` reaches for it via sibling import. If the `AggregateSet` card (`0.1.3`) wants a neutral home, that card can perform the move atomically with both filter and order subsystems' imports updated.

### Decision 3 — Five-layer port plus a deferred Layer 6

The pre-pinned architectural answer (from the [`KANBAN.md`][kanban] card body's `Other` block) is borrowed verbatim and preserved here. Five of the six lazy-resolution layers port from `django-graphene-filters` library-agnostic; the Strawberry adaptation at Layer 5 reuses the shape the filter subsystem just shipped. Layer 6 (dynamic `OrderSet` generation) has no cookbook counterpart and is deferred to `0.0.9` per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).

**Layer 1 — Lazy class references in `RelatedOrder`** — port verbatim from [`django_graphene_filters/orders.py::BaseRelatedOrder`][upstream-cookbook-orders]. `RelatedOrder` accepts target as class, absolute import path string (`"apps.library.orders_genre.GenreOrder"`), or unqualified name (`"GenreOrder"`). `_orderset` stores it unresolved; the `.orderset` property triggers resolution.

**Layer 2 — Module-fallback resolution** — REUSED from the shipped [`django_strawberry_framework/filters/base.py::LazyRelatedClassMixin`][filters-base]. The mixin is shared between the filter and order subsystems (sibling import, no duplication per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface)). Two-step resolution: try as absolute path via `django.utils.module_loading.import_string`; on `ImportError`, retry with `bound_class.__module__` prefix. Handles circular-import scenarios in the same module.

**Layer 3 — Metaclass discovery, deferred expansion** — port pattern from [`django_graphene_filters/orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset]. Metaclass collects `BaseRelatedOrder` declarations into `cls.related_orders` (note the singular-to-plural shift from the filter side's `cls.related_filters`), calls `f.bind_orderset(new_class)` so the module-fallback resolver knows the owning module, and **does not** expand. Expansion is deferred to `get_fields()`.

**Layer 4 — Cycle-safe expansion + cache** — port verbatim from [`django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields`][upstream-cookbook-orderset]. `cls.__dict__["_expanded_fields"]` cache plus `cls.__dict__["_is_expanding_fields"]` recursion guard. Two-condition cache write: `"related_orders" in cls.__dict__` AND no string `_orderset` remaining on any related order. Breaks `A → B → A` cycles cleanly.

**Layer 5 — BFS schema build with module-global materialization (Strawberry-adapted)** — port the BFS algorithm in [`django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory._ensure_built`][upstream-cookbook-order-arguments-factory] verbatim; the cycle-safe forward reference uses the same Strawberry adaptation the filter subsystem ships per [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3. Specifically:

- Every generated order input class is a **real module global** of [`django_strawberry_framework.orders.inputs`][orders-inputs] (set via `setattr(sys.modules["django_strawberry_framework.orders.inputs"], name, cls)`).
- The Strawberry idiom is `Annotated["{TargetOrderSet}InputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` for `RelatedOrder` fields. Leaf scalar fields use the public `Ordering` enum directly (no forward reference; the enum is a module-load-time symbol).
- The `Annotated[...]` MUST directly wrap the forward-reference string for `RelatedOrder` references (no list wrapper because each `RelatedOrder` field is single-valued — there's no `and_` / `or_` operator-bag for ordering, unlike the filter side).
- `OrderArgumentsFactory._ensure_built` produces both halves: it materializes each input class as a module global (via the helper `materialize_input_class(name, cls)` in `inputs.py` — same two-argument signature the filter side ships) AND it emits the `Annotated[...]` shape in field annotations so cycle-safe references between ordersets keep working.

**Layer 6 — Memoized dynamic `OrderSet` generation** — **DEFERRED TO `0.0.9`** per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009). The cookbook ships no `orderset_factories.py` and no `_dynamic_orderset_cache` — only the filter side has the dynamic-factory mechanism. The `0.0.8` shape requires an explicit `Meta.orderset_class = MyOrder` declaration on every consumer; the `0.0.9` `DjangoConnectionField` card decides whether to design Layer 6 fresh (mirroring the filter side's `filterset_factories.py::_dynamic_filterset_cache`) or require the explicit declaration on every connection field.

**`Meta.fields = "__all__"` scope** — expands to every **concrete** model field (every column the cookbook's [`get_concrete_field_names`][upstream-cookbook-mixins] returns; relations are NOT included). Relation traversal under `"__all__"` requires an explicit `RelatedOrder(...)` declaration. **This is genuine cookbook parity** — verified per H3 of [`docs/feedback.md`][feedback] rev1 against `~/projects/django-graphene-filters/django_graphene_filters/orderset.py:271`, where `AdvancedOrderSet.get_fields` carries the `if meta_fields == "__all__":` branch that walks `get_concrete_field_names(model)`. The package's port honors the cookbook's shape exactly; this is not a package-original feature back-ported from the filter side's convention. Relation exclusion under `"__all__"` matches the cookbook's behavior AND the filter side's [Non-goals](#non-goals) "no implicit FilterSet generation from Meta.fields" rule applied to the order side.

**Proxy / multi-table-inheritance semantics (per N8 of [`docs/feedback.md`][feedback] rev1).** The cookbook's `get_concrete_field_names` walks Django's `model._meta.fields` (which on a proxy model returns the proxied parent's fields, and on a multi-table-inherited child returns the union of parent + child concrete fields). The package's port inherits this behavior unchanged:

- **Proxy models** (where `model._meta.proxy is True`): `"__all__"` returns the proxied parent's concrete field names. The proxy's own `Meta.fields` declaration takes precedence (proxies are intended as thin behavior wrappers; the GraphQL surface follows the parent's column set).
- **Multi-table inheritance (MTI)** child models: `"__all__"` returns the union of the parent's concrete fields AND the child's concrete fields (Django's `_meta.fields` walks the parent chain by default). Consumers wanting only the child's columns declare `Meta.fields = (...)` explicitly.
- **Abstract base models**: irrelevant — abstract models cannot be the target of a `DjangoType` (the `DjangoType.Meta.model` validator at `_validate_meta` time rejects abstract models, same as the filter side).

Justification:

- The cookbook's five-layer architecture is proven (the working reference per [`START.md`][start]); reinventing it would burn schedule for no architectural gain.
- The Strawberry adaptation at Layer 5 reuses the shipped filter subsystem's shape exactly — the lazy-resolution + module-globals materialization contract is one shape, not two.
- Deferring Layer 6 to `0.0.9` is correct because there is no `0.0.8` consumer surface (no `DjangoConnectionField` yet, no `DjangoListField` argument injection per [Non-goals](#non-goals)) that needs an implicit `OrderSet`. Designing it now would invent machinery for a hypothetical caller.

Alternatives considered (and rejected):

- **Design Layer 6 fresh in `0.0.8` mirroring the filter side's `_dynamic_filterset_cache`.** Rejected: no `0.0.8` consumer surface needs it. The `0.0.9` connection field is the consumer; the cache lands with that card.
- **Duplicate `LazyRelatedClassMixin` into `orders/base.py`.** Rejected per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) — silently bifurcating the resolution behavior is a maintenance hazard.
- **Borrow the cookbook's `OrderDirection` enum** (four-member: `ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT`) instead of strawberry-django's six-member `Ordering` enum. Rejected per [Decision 5](#decision-5--ordering-enum-and-argument-shape) — DISTINCT ON deserves its own design space (a separate `Meta.distinct` key + `distinct_on:` argument in `0.0.9`), and NULLS positioning is more broadly useful as a leaf-field direction.

### Decision 4 — Upstream-primitives parity floor

The cookbook ships **`AdvancedOrderSet`**, **`RelatedOrder`**, **`OrderArgumentsFactory`**, and **`OrderDirection`** as the public surface. strawberry-graphql-django ships **`Ordering`**, **`OrderSequence`**, **`order_type`**, and the **`process_order`** runtime pipeline.

**The full strawberry-django ordering surface, as quoted from the [`KANBAN.md`][kanban] card body's `Verified in upstream` block** (inlined verbatim per N2 of [`docs/feedback.md`][feedback] rev1 so this Decision is self-contained and a reader does not have to dig into KANBAN to see what was "verified"):

- `ordering.py::Ordering` — public `Ordering` enum: `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`.
- `ordering.py::OrderSequence` — per-field sequence descriptor used to order ties when multiple fields participate.
- `ordering.py::process_order` / `::process_ordering` / `::process_ordering_default` / `::apply_ordering` — the runtime pipeline that compiles an order-input value into queryset `order_by()` arguments and applies them.
- `ordering.py::StrawberryDjangoFieldOrdering` — field-base subclass that injects the `order: <T>OrderInput` and `ordering: list[<T>OrderInput]` arguments on a Django-backed field.
- `ordering.py::order_type` — current consumer-facing `@strawberry_django.order_type(Model)` decorator (public API).
- `ordering.py::order` — legacy decorator alias marked `@deprecated("strawberry_django.order is deprecated in favor of strawberry_django.order_type.")`; do not claim parity with this symbol.
- `ordering.py::ORDER_ARG` (`= "order"`) and `ordering.py::ORDERING_ARG` (`= "ordering"`) — module-level constants for the singular one-of and list GraphQL argument names.
- `~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by"` — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; ⚛️ parity is met by the filter subsystem (`DONE-027-0.0.8`) rather than this card.

The package's parity floor for `0.0.8`:

- `OrderSet` (the cookbook's `AdvancedOrderSet`) — class-based declaration with `Meta.model`, `Meta.fields`, per-field `check_<field>_permission` gates, classmethod resolver-facing `apply_sync` / `apply_async` API.
- `RelatedOrder` (the cookbook's port + the [Layer-2 lazy resolution][filters-base] shared with the filter subsystem) — cross-relation traversal.
- `OrderArgumentsFactory` (the cookbook's BFS factory + the Strawberry-adapted Layer 5 from [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3) — produces the `orderBy: [<T>OrderInput!]` argument.
- `Ordering` (the strawberry-django six-member enum) — direction modifiers per [Decision 5](#decision-5--ordering-enum-and-argument-shape).
- `order_input_type(OrderSet)` (the consumer helper, parallel to the shipped `filter_input_type(FilterSet)`) — resolver-annotation helper per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper).

NOT in the parity floor (deferred):

- `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` (the cookbook's DISTINCT ON modifiers) — deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).
- `AdvancedOrderSet.apply_distinct` / `_apply_distinct_postgres` / `_apply_distinct_emulated` (the cookbook's Window-function emulation) — deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).
- `OrderSequence` tie-breaker descriptor (the strawberry-django per-field sequence) — NOT borrowed per [Decision 5](#decision-5--ordering-enum-and-argument-shape) (the list-shaped argument provides the tie-breaker mechanism positionally).
- `StrawberryDjangoFieldOrdering` (the strawberry-django field-base subclass) — NOT borrowed (the `Meta`-driven shape forbids subclassing Strawberry field classes).
- `order_type` / `order` decorators — NOT borrowed (the `Meta`-driven shape forbids decorator-on-input-type).
- `_dynamic_orderset_cache` (Layer 6) — deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).

Justification:

- The parity floor matches what both upstreams ship as `0.0.8`-equivalent surfaces; downgrading below it would leave the package unable to express a query the upstreams accept.
- Deferring DISTINCT ON, dynamic factory, and decorator surfaces narrows the `0.0.8` cut without compromising the parity argument — each deferred item ships in a follow-on card with its own scope.

Alternatives considered (and rejected):

- **Ship `OrderSequence` for explicit tie-breaker control.** Rejected per [Decision 5](#decision-5--ordering-enum-and-argument-shape) — redundant with positional list-element ordering.
- **Ship DISTINCT ON in `0.0.8` via the cookbook's `apply_distinct` port.** Rejected per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009) — the design deserves its own decision space (`Meta.distinct` key + a `distinct_on:` argument).
- **Ship Layer 6 dynamic-factory in `0.0.8`.** Rejected — no `0.0.8` consumer surface needs it.

### Decision 5 — `Ordering` enum and argument shape

The public direction enum is `Ordering` — borrowed verbatim from [`~/projects/strawberry-django-main/strawberry_django/ordering.py::Ordering`][upstream-strawberry-ordering]:

```python
# django_strawberry_framework/orders/inputs.py
import enum
import strawberry


@strawberry.enum
class Ordering(enum.Enum):
    ASC = "ASC"
    DESC = "DESC"
    ASC_NULLS_FIRST = "ASC_NULLS_FIRST"
    ASC_NULLS_LAST = "ASC_NULLS_LAST"
    DESC_NULLS_FIRST = "DESC_NULLS_FIRST"
    DESC_NULLS_LAST = "DESC_NULLS_LAST"

    def resolve(self, value: str) -> "OrderBy":
        """Compile this direction + a Django ORM field path into an OrderBy expression.

        Mirrors strawberry-django's resolve() behavior: NULLS positioning is
        passed via Django's F(value).asc(nulls_first=...) / F(value).desc(nulls_last=...)
        rather than a bare string prefix, so the produced SQL carries the
        NULLS positioning unambiguously.
        """
        # Per M4 of docs/feedback.md rev1: both imports must be local-to-
        # function or top-of-file. F lives in django.db.models; OrderBy lives
        # in django.db.models.expressions. The return-annotation OrderBy
        # string-forward-reference resolves at type-check time against the
        # latter; the runtime body never instantiates OrderBy directly
        # (F(...).asc/desc(...) returns one), so a top-of-module import for
        # the annotation is optional. Showing both for copy-paste safety.
        from django.db.models import F
        from django.db.models.expressions import OrderBy  # noqa: F401  # used by the type annotation
        # Django sentinel semantics (M4 of docs/feedback.md rev1):
        # nulls_first=True opts INTO "NULLS FIRST" positioning; nulls_first=None
        # leaves the backend's default in place (no NULLS clause emitted).
        # The ternary below intentionally produces True-or-None so an ASC /
        # DESC member without a NULLS qualifier (e.g., `Ordering.ASC`) maps
        # to `F(value).asc(nulls_first=None, nulls_last=None)` — i.e., NO
        # NULLS clause at all, not `NULLS FIRST False`.
        nulls_first = True if "NULLS_FIRST" in self.name else None
        nulls_last = True if "NULLS_LAST" in self.name else None
        if "ASC" in self.name:
            return F(value).asc(nulls_first=nulls_first, nulls_last=nulls_last)
        return F(value).desc(nulls_first=nulls_first, nulls_last=nulls_last)
```

The GraphQL argument shape is **`orderBy: [<TypeName>OrderInputType!]`** (list of non-null order-input objects). Consumers write `orderBy: [{ name: ASC }, { shelf: { code: DESC_NULLS_LAST } }]`. The list's element order IS the tie-breaker mechanism — `get_flat_orders` processes elements in order, so earlier list entries dominate later ones.

GraphQL surface examples:

```graphql
{ allLibraryBranches(orderBy: [{ name: ASC }]) { id } }                          # single-field, ascending
{ allLibraryBooks(orderBy: [{ title: DESC_NULLS_LAST }]) { id } }                # NULLS positioning
{ allLibraryBooks(orderBy: [{ shelf: { code: ASC } }, { title: DESC }]) { id } } # tie-breaker via list order
{ allLibraryBooks(orderBy: [{ genres: { name: ASC } }]) { id } }                 # M2M relation order
```

Justification:

- The six-member `Ordering` enum is the most useful surface for the package's `0.0.8` audience: `NULLS_FIRST` / `NULLS_LAST` positioning is broadly applicable across every backend Django supports, while the cookbook's `DISTINCT` modifiers are PostgreSQL-specific (the cookbook's [`_apply_distinct_emulated`][upstream-cookbook-orderset] Window-function fallback works on other backends but the `DISTINCT ON` mental model is PostgreSQL-native).
- The list-shaped argument (NOT a sibling singular `order:` argument like strawberry-django ships) is sufficient — a list with one element produces the same SQL as a singular variant, so two arguments would be redundant. The package's `0.0.8` audience expects one argument shape per capability.
- The Python attribute name on the resolver is `order_by` (Strawberry's auto-camel-case translates to `orderBy:` on the GraphQL surface); the module-level constant in `factories.py` is `ORDER_BY_ARG = "orderBy"` (the GraphQL surface name).
- `Ordering.resolve(field_path)` returns an `OrderBy` expression (via `F(...).asc/desc(nulls_first=...)`) rather than a bare string with `-` prefix because the bare-string form cannot express NULLS positioning. The `get_flat_orders` port from the cookbook is adapted to collect `OrderBy` expressions instead of bare strings; `queryset.order_by(*expressions)` accepts both forms, so the change is transparent to the queryset.

Alternatives considered (and rejected):

- **Ship the cookbook's four-member `OrderDirection`** (`ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT`). Rejected per [Decision 4](#decision-4--upstream-primitives-parity-floor) — DISTINCT ON deserves its own design space, and NULLS positioning is more broadly useful.
- **Ship both a singular `order:` argument AND a list `ordering:` argument** (matching strawberry-django's two-constant module). Rejected — redundant; a list with one element is the same SQL.
- **Ship `OrderSequence` for explicit tie-breaker control** (per strawberry-django's per-field sequence descriptor). Rejected — the list's element order IS the tie-breaker; positional control is more discoverable than a separate descriptor field.
- **Use bare-string Django ORM expressions (`["-name", "shelf__code"]`)** instead of `OrderBy` expressions from `F(...).asc/desc(nulls_first=...)`. Rejected — bare strings cannot express NULLS positioning; the `OrderBy` expression form is required.

### Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering

The finalizer-phase-2.5 binding for `Meta.orderset_class` runs immediately after the shipped `_bind_filtersets()` umbrella helper and before phase 3's `strawberry.type` decoration. The implementation is `_bind_ordersets()` — a four-subpass helper mirroring the **shipped** `_bind_filtersets()` implementation at [`django_strawberry_framework/types/finalizer.py::_bind_filtersets`][finalizer] (NOT spec-027 rev8 as written — per B1 of `docs/feedback.md` rev1, the spec-027 H1 prescription and the shipped code diverged on subpass 3-vs-4 ordering, and the shipped code is the authoritative shape):

1. **Bind owners.** For each `DjangoType` whose `definition.orderset_class is not None`, set `orderset_class._owner_definition = definition` and run own-PK + related-target validation. Two-owner re-use is allowed only when every owner-sensitive target resolves to the same `DjangoTypeDefinition` (mirrors the filter side's strict reuse check from H2 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev8 — but the order side's "owner-sensitive target" set is smaller because ordering does NOT consult Relay shape, so the only owner-sensitive question is "does this related-order target's `_owner_definition` resolve to the same `DjangoType`?").
2. **Expand orderset fields.** Call `orderset_cls.get_fields()` for every wired orderset only after every owner is bound. Layer-4 expansion now reads correct `_owner_definition` for every reachable `RelatedOrder` target. An `ImportError` raised by `LazyRelatedClassMixin.resolve_lazy_class` (a string-form `RelatedOrder("Name")` that cannot be resolved) is rewrapped as [`ConfigurationError`][glossary-configurationerror] with `__cause__` preserving the underlying `ImportError`; any other exception from `get_fields()` rewraps as [`ConfigurationError`][glossary-configurationerror] with `repr(exc)` keeping the original class + args in the consumer-visible message (mirrors the filter side's `_bind_filtersets` lines 540-571 verbatim — uniform finalize-time error shape per H-core-1 of the filter side's pre-merge review).
3. **Orphan validation.** Compare `_helper_referenced_ordersets` (the set of `OrderSet`s passed to `order_input_type`) against the set of `Meta.orderset_class`-wired ordersets and raise [`ConfigurationError`][glossary-configurationerror] for every orphan, with the same fix-suggestion message shape the filter side ships. **Runs BEFORE materialization** so an orphan failure leaves no partial state in `_materialized_names` / `OrderArgumentsFactory.input_object_types`; without this ordering, a re-run of `finalize_django_types()` after the consumer fixes the orphan would see stale ledger entries from the prior failed attempt. The shipped filter side at [`finalizer.py:572-587`][finalizer] documents this rationale explicitly; this card mirrors the shipped order, not the spec-027 rev8 H1 prescription which inverted subpasses 3 and 4.
4. **Materialize input classes.** Call `OrderArgumentsFactory(orderset_cls).arguments` to trigger the Layer-5 BFS, then iterate `factory.input_object_types.items()` and call `materialize_input_class(name, cls)` for every built class so each becomes a module global of [`django_strawberry_framework.orders.inputs`][orders-inputs]. The materialization runs BEFORE `strawberry.Schema(...)` is constructed (the consumer-side ordering is pinned in [`docs/README.md`'s Schema setup boundary][docs-readme]). A second factory instance for a sibling root sees the cached build via the factory's class-level dict — same shape the filter side ships at [`finalizer.py:589-598`][finalizer].

`registry.clear()` invokes `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` so the model-to-`DjangoType` clear, the order-input clear, the orphan-tracking clear, AND the already-shipped filter-input clear all share one entry point. Calling `finalize_django_types()` twice is still a no-op via the existing `registry.is_finalized()` guard.

Justification:

- Same phase, same seam, same four-subpass discipline as the **shipped** filter side — symmetry across the two sibling Layer-3 subsystems makes the finalizer's intent legible. A future maintainer reading `finalize_django_types` sees `_bind_filtersets()` then `_bind_ordersets()` and understands the pattern; a future Aggregation card adds `_bind_aggregates()` at the same seam.
- The four-subpass ordering closes the same `_owner_definition` race the filter side closed in rev8: if `BookOrder.shelf = RelatedOrder("ShelfOrder")` and `BookType` is iterated before `ShelfType` in the binding loop, the naive single-subpass call to `BookOrder.get_fields()` would expand `ShelfOrder` before its `_owner_definition` is set. The four-subpass ordering binds every owner first, then expands.
- **The orphan-before-materialize ordering is load-bearing**, not arbitrary. Materializing first then orphan-validating would leave half-materialized input classes in the inputs-module namespace AND half-populated entries in `OrderArgumentsFactory.input_object_types` whenever the orphan check raises; the next `finalize_django_types()` call (after the consumer fixes the orphan) would then see stale ledger entries and either skip re-materialization for entries that should rebuild OR raise a name-collision error for the legitimate retry. Inverting the order keeps both ledgers empty until every gate has passed.
- The `registry.clear()` co-clear keeps the test-fixture reload pattern from [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`][fakeshop-test-library-reload] working unchanged.

Alternatives considered (and rejected):

- **Single-subpass binding** (iterate `DjangoType`s once, calling `bind_owner` + `get_fields` + `materialize` in one loop body). Rejected per the rev8 H1 lesson — the `_owner_definition` race is real and the four-subpass discipline closes it.
- **Bind ordersets at type-creation time (in `DjangoType.__init_subclass__`)** instead of at finalize. Rejected — relation targets may not be registered yet at type-creation time (definition-order independence); finalize is the only point where every type is known.
- **Materialize BEFORE orphan-validate** (the order spec-027 rev8 H1 *prescribed* but the shipped code rejected). Rejected — leaves stale `_materialized_names` ledger entries and stale `OrderArgumentsFactory.input_object_types` entries on every orphan-validation failure, causing the next finalize attempt to mis-fire after the consumer fixes the orphan. The shipped filter side's choice (orphan-validate first) is the right shape; this card preserves it.
- **Skip the orphan-validation step.** Rejected — without it, an orphan `order_input_type(StandaloneOrder)` reference would surface as a cryptic `LazyType.resolve_type` `KeyError` at `strawberry.Schema(...)` time, well after the resolver-declaration site. Failing loud at finalize names the bug at the right location.

### Decision 7 — `Meta.orderset_class` promotion gate

`Meta.orderset_class` is promoted out of [`DEFERRED_META_KEYS`][base] only when:

1. The order subsystem's class hierarchy is on disk (Slices 1 + 2).
2. The finalizer-phase-2.5 binding pass is wired (Slice 3).
3. The promotion to `ALLOWED_META_KEYS` is applied at the same commit as the validator-acceptance test (Slice 3).

Same gate as [`Meta.interfaces`][glossary-metainterfaces] in `DONE-015-0.0.5` and [`Meta.filterset_class`][glossary-metafilterset_class] in `DONE-027-0.0.8` — a deferred `Meta` key is accepted only when the subsystem applies it end-to-end. A consumer who declares `Meta.orderset_class = ItemOrder` against a `0.0.8`-installed package gets a working ordering surface; against `0.0.7` they get the existing [`ConfigurationError`][glossary-configurationerror] from [`DEFERRED_META_KEYS`][base].

Justification:

- Cross-subsystem invariant pinned in [`docs/GLOSSARY.md`][glossary] ([Cross-subsystem invariants][glossary-cross-subsystem-invariants] — "Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end. This rule resolves entirely at `1.0.0`."); applies to every Layer-3 sidecar.
- Half-promoting (accepting the key but no-oping on it) is the worst-of-both: consumers cannot tell whether their order declaration is doing anything; debug surface is hidden.
- The promotion is a one-line change at [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] (`"orderset_class"` moves to `ALLOWED_META_KEYS`); the validator at `_validate_meta` already gates on `ALLOWED_META_KEYS | DEFERRED_META_KEYS`.

Alternatives considered (and rejected):

- **Promote `Meta.orderset_class` early in Slice 1 before binding is wired.** Rejected: silently accepting a key whose effect doesn't exist is a maintenance hazard.
- **Keep the key in `DEFERRED_META_KEYS` until `DjangoConnectionField` ships in `0.0.9`.** Rejected: the connection field is the second consumer; root-list resolvers can call `OrderSet.apply_sync(...)` themselves in the meantime, and the live HTTP coverage in Slice 4 exercises that path.

### Decision 8 — Cooperation with filtering, `get_queryset`, and the optimizer

The ordering subsystem composes with three shipped surfaces without modification: the Filtering subsystem (`DONE-027-0.0.8`), the `get_queryset` visibility hook (`DONE-001-0.0.1`), and the `DjangoOptimizerExtension` (`DONE-002-0.0.2` through `DONE-004-0.0.3`). The composition flows through the resolver-facing classmethods `OrderSet.apply_sync(input_value, queryset, info)` and `OrderSet.apply_async(input_value, queryset, info)`. Resolvers pick the variant matching their own sync/async shape (mirrors the filter side's H2 split from [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev5).

**`GraphQLError` import path** — every `GraphQLError` raised in this Decision and in [Decision 11](#decision-11--order_input_typeorderset-consumer-helper) is `from graphql import GraphQLError` (the class Strawberry's response builder honors for the `extensions` payload). NOT `strawberry.exceptions.StrawberryGraphQLError` (a private subclass).

**Apply pipeline (mirrors the filter side's pipeline, simplified — no operator-bag, no form validation, no related-queryset filter-scope constraint).** The 8-step pipeline:

1. **The consumer resolver calls `<OwnerType>.get_queryset(queryset, info)` first** on the consumer-shaped root queryset — visibility scoping happens BEFORE any order clause runs. Unlike the filter side where this ordering is security-critical (a filter clause can see through visibility to hidden rows), the order side's `<get_queryset>` → `apply_*` ordering is one-directional discipline: ordering applied AFTER visibility scoping operates on the row set the user is allowed to see, which is the consumer's expectation. (An `ORDER BY name` against a visibility-filtered queryset orders only the visible rows; against the unscoped manager it orders the universe and the consumer sees the wrong row at the head of the list.)
2. **The consumer resolver optionally calls `<TypeName>Filter.apply_sync(filter, queryset, info)`** (or `apply_async`) to narrow the row set per the shipped filter subsystem's contract. This step is optional — a resolver that does not declare a `filter:` argument skips it.
3. **The consumer resolver then calls `OrderSet.apply_sync(input_value, queryset, info)`** (or `await OrderSet.apply_async(input_value, queryset, info)`). Internally, the apply pipeline normalizes the Strawberry input dataclass (walking nested `RelatedOrder` input objects via the cookbook's `get_flat_orders` algorithm; producing a flat list of `(field_path, Ordering)` tuples).
4. **`<OwnerType>.get_queryset` is NOT re-applied for the parent type** — step 1 already ran it on the consumer-shaped queryset. The filter side's H1 (nested `RelatedFilter` branches re-derive child visibility querysets to prevent see-through-to-hidden-rows on the JOIN's right-hand side) has **no direct parallel** for the order side's *projected* output: an `ORDER BY shelves.code` against a queryset whose `Shelf.get_queryset` would hide some shelves does NOT expose hidden-shelf data in the response payload — the projected output is the parent `Branch` rows and the order clause influences row position, not row content. **However, a low-bandwidth position-side-channel leak exists and is intentionally accepted for `0.0.8`** (per H4 of [`docs/feedback.md`][feedback] rev1): ordering Branch rows by a hidden `Shelf.code` column changes the *position* of visible Branch rows in the result list based on data the user is not allowed to read. A determined consumer can infer the relative ordering of hidden shelves by sending two queries (one with `orderBy: [{ shelves: { code: ASC } }]`, one without) and diffing the Branch row positions. The leak bandwidth is low (one bit of ordinal information per visible Branch pair per query), the consumer already sees the visible-Branch ordering, and the only thing they recover is the *causal explanation* (which hidden column drove the visible ordering) — not the hidden column's values directly. **Closing this side channel** would require re-deriving every nested `RelatedOrder` branch's child visibility queryset and rewriting the parent JOIN's `ORDER BY` to operate only on the visibility-scoped subset, which is a non-trivial design change (the parent JOIN's `ORDER BY` would have to fall back to `NULL` for rows whose related-side is hidden, requiring per-relation `Case`/`When` expressions or a subquery-driven rewrite). That work is **deferred** — likely to a sibling `0.0.9` ordering-permissions card (or to a follow-up that lifts the position-side-channel question into its own design). Per N-new-1 of [`docs/feedback.md`][feedback] rev2: the connection-field cohort is the natural integration point because Relay connections are where `RelatedOrder` traversal becomes consumer-visible at scale, but the leak-closing work is **independent of connection-field design** — pinning the two together would risk a future reader assuming the deferral is already scheduled when in fact the work has not been carved into a card yet. The package's `OrderSet` [`check_*_permission`][glossary-per-field-permission-hooks] gates ARE the consumer's defense for `0.0.8`: any `RelatedOrder` field that should not influence visible-row position must declare a permission gate (e.g., `check_shelves_permission(request)`) that raises [`GraphQLError`][glossary-configurationerror] for unauthorized users. The GLOSSARY entry for [`OrderSet`][glossary-orderset] and the [`RelatedOrder`][glossary-relatedorder] entry both call this out (Slice 5 doc-update bullet), so consumers reaching for permission gates to harden their schema see the position-side-channel risk before they ship.
5. **The apply pipeline extracts the Django request.** Canonical shape is `info.context.request` matching the Strawberry-Django convention; the dispatcher detects the wrapper-less alternative via `isinstance(info.context, HttpRequest)` and treats it as the request directly. Same shape the filter side ships per M8 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev5.
6. **The apply pipeline calls `cls.check_permissions(input_value, request)`** — denial gates raise `from graphql import GraphQLError; GraphQLError(...)` before any `order_by(...)` clause touches the queryset. Per the active-input-only discipline shipped in `DONE-027-0.0.8`, the per-field `check_<field>_permission(request)` gate runs **only for fields present in the normalized input**, NOT for every declared field. The check recurses through `RelatedOrder`s into child ordersets' `check_*_permission` methods, but only for active branches.
7. **The instance applies `queryset.order_by(*expressions)`** where `expressions` is the flat list of `OrderBy` expressions produced by `Ordering.resolve(field_path)` for each `(field_path, direction)` tuple (per [Decision 5](#decision-5--ordering-enum-and-argument-shape)). The apply pipeline returns the ordered queryset to the resolver.
8. **The optimizer ([`DjangoOptimizerExtension`][glossary-djangooptimizerextension]) walks the selection tree on the ordered queryset**; [Queryset diffing][glossary-queryset-diffing] cooperates with any consumer `select_related` / `prefetch_related` work already present. The optimizer's own `.only(...)` projection (shipped in `DONE-002-0.0.2`) is **selection-tree-derived only** — it does not inspect `queryset.query.order_by` to extend `plan.only_fields` (verified per H2 of [`docs/feedback.md`][feedback] rev1). Django's ORM itself fetches the columns required to execute the `ORDER BY` clause regardless of the `.only(...)` hint, so the user-visible behavior is correct without the package doing anything — but this is Django's cooperation, not the package's. Order-aware projection augmentation is **out of scope for `0.0.8`**; if a future card adds it (likely under Connection-aware optimizer planning in `0.0.9`), the projection-extension logic ships there with a focused test.

**Sync / async API split.** Same shape as the filter side per H2 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev5:

- `OrderSet.apply_sync(input_value, queryset, info) -> QuerySet` — the sync-resolver entry point.
- `OrderSet.apply_async(input_value, queryset, info) -> Awaitable[QuerySet]` — the async-resolver entry point.
- **No `OrderSet.apply(...)` dispatcher.** Per H1 of [`docs/feedback.md`][feedback] rev1, the filter side's `apply(...)` exists to detect and rewrap a sync-misuse `RuntimeError` raised when a `RelatedFilter` target declares an `async def get_queryset`; the order side has no equivalent code path (step 4 above is explicit that ordering never re-derives child visibility querysets) so a symmetric `apply` dispatcher would never fire. Consumers call `OrderSet.apply_sync(...)` from sync resolvers and `await OrderSet.apply_async(...)` from async resolvers — the dispatch is trivially explicit.

**`apply_async` blocking-hook caveat (per N7 of [`docs/feedback.md`][feedback] rev1, mirroring [`filters/sets.py:1410-1421`][filters-base] verbatim).** `OrderSet.apply_async` does **not** wrap consumer hooks (`check_<field>_permission` gates) in `sync_to_async`. The built-in pipeline does no synchronous I/O — `get_flat_orders` is pure parsing, `Ordering.resolve()` builds expressions in-memory, and `queryset.order_by(*expressions)` is a queryset method call that does not hit the database — so the package itself never blocks the event loop. But a consumer hook that issues a blocking ORM call (e.g., `check_name_permission(request)` doing a `User.objects.get(...)` lookup against the default database) WILL block the event loop without raising any warning. Consumers porting a sync `check_<field>_permission` body into an async resolver MUST verify the body is non-blocking; the recommended pattern is to do any required I/O inside the resolver's awaited `get_queryset` step (which IS dispatched through the sync/async machinery in [`relay.py`][relay]) and pass the resolved authorization signal into the permission hook as a request attribute. The `OrderSet` GLOSSARY entry calls this out so consumers reaching for async resolvers see the caveat before they ship.

**Optimizer cooperation.** Order clauses are pure queryset-method calls (`queryset.order_by(...)`); they do not change the result type, do not invalidate `select_related` / `prefetch_related`, and do not affect the optimizer's plan cache. The shipped [Queryset diffing][glossary-queryset-diffing] cooperation handles them by default. A live HTTP test pins the cooperation under `assertNumQueries(N)`.

**Forward composition contract.** When [`apply_cascade_permissions`][glossary-apply_cascade_permissions] ships in `0.0.10`, it slots into step 1 (the `get_queryset` hook); when [Per-field permission hooks][glossary-per-field-permission-hooks] ship, they slot into the field-resolver layer that runs AFTER step 8 (queryset traversal completes before field resolvers fire). When [`DjangoConnectionField`][glossary-djangoconnectionfield] ships in `0.0.9`, the connection field consumes the `OrderArgumentsFactory` output as its `orderBy:` argument; the connection field's pagination math runs AFTER step 7's `order_by(...)` is applied.

Justification:

- Symmetry with the filter side's apply pipeline (sync/async split, `check_permissions` active-input-only scope, `info.context.request` extraction with `HttpRequest` fallback, `GraphQLError` import path) keeps the two subsystems on one shape. A future maintainer reading both subsystems' apply pipelines sees the same skeleton with minor adaptations.
- The order side's pipeline is genuinely simpler than the filter side's: no operator-bag (no `and_` / `or_` / `not_`), no form validation (no `BaseFilterSet.form.is_valid()` step — the cookbook's `AdvancedOrderSet` doesn't use forms), no related-queryset filter-scope constraint (no `RelatedOrder(queryset=...)` parameter — the cookbook's `RelatedOrder` accepts only `orderset` and `field_name`). The eight-step pipeline reflects this simplification.
- The filter-first-then-order resolver pattern is the canonical SQL shape — `WHERE` clauses narrow the row set, then `ORDER BY` arranges the result. Reversing the order would still produce the same SQL (PostgreSQL / SQLite / MySQL all reorder `WHERE` and `ORDER BY` in the same plan), but the consumer-readable shape (`filter` then `order_by`) makes the intent legible at the resolver site.

Alternatives considered (and rejected):

- **Re-derive child visibility querysets for nested `RelatedOrder` branches** (mirroring the filter side's H1). Rejected — the order side does not have the see-through-to-hidden-rows vulnerability the filter side has. Ordering by a hidden relation's field does not expose the hidden row's data; it only affects which visible parent rows surface first. The shipped filter subsystem already covers the joinable visibility case via H1; the order side does not need a parallel guard.
- **Apply `OrderSet.apply_*` BEFORE the filter** (`get_queryset` → `Order.apply_*` → `Filter.apply_*`). Rejected — the produced SQL is identical (Postgres / SQLite / MySQL reorder `WHERE` / `ORDER BY` plan), but the resolver-readable shape suffers. The filter-first ordering matches the consumer's mental model.
- **Skip step 6 (`check_permissions`).** Rejected — the cookbook's [`AdvancedOrderSet.check_permissions`][upstream-cookbook-orderset] is a useful surface for consumers who want to gate ordering on user role (`order by name DESC` for staff only); the active-input-only narrowing makes the surface low-noise (gates fire only when relevant).
- **Use bare-string `order_by` arguments (`["-name", "shelf__code"]`)** instead of `OrderBy` expressions. Rejected per [Decision 5](#decision-5--ordering-enum-and-argument-shape) — bare strings cannot express NULLS positioning.

### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle

The card body's "Decide whether the input-type factory's namespace shares the `TypeRegistry` or has its own" question is answered: **the input-class namespace is the [`django_strawberry_framework.orders.inputs`][orders-inputs] module's own global namespace**, separate from the model-to-`DjangoType` registry at [`django_strawberry_framework.registry.registry`][registry] (which powers [`Meta.primary`][glossary-metaprimary]) AND separate from the shipped [`django_strawberry_framework.filters.inputs`][filters-inputs] namespace.

Implementation: every generated order input class is a real module global of `django_strawberry_framework.orders.inputs`, set at finalize time via `setattr(sys.modules["django_strawberry_framework.orders.inputs"], name, cls)`. The class names are stable and class-derived (e.g., `f"{OrderSet.__name__}InputType"` → `"GalaxyOrderInputType"`). The "registry" IS the module's `__dict__` — there is no separate `_input_type_registry: dict[str, type]`, because Strawberry's `LazyType.resolve_type` reads `module.__dict__` directly and cannot traverse a sidecar dict (mirrors the filter side's H1 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027]). A lifecycle ledger (a private `dict[str, type[OrderSet]]` at `django_strawberry_framework.orders.inputs._materialized_names`) tracks `class_name → orderset_class` provenance so re-materialization is idempotent and clears cleanly.

The order-input namespace and the filter-input namespace are **disjoint**: an `OrderSet.__name__` of `BranchFilter` would produce `BranchFilterInputType` colliding with the filter side, but the package's [`OrderSet`][glossary-orderset] subclasses use a `*Order` naming convention by precedent (cookbook + strawberry-django), so `BranchOrder` → `BranchOrderInputType` and `BranchFilter` → `BranchFilterInputType` never overlap. The namespaces remain disjoint by module path even if the names happened to collide: Strawberry's `strawberry.lazy("django_strawberry_framework.orders.inputs")` and `strawberry.lazy("django_strawberry_framework.filters.inputs")` are two distinct module-import paths that resolve to two distinct `module.__dict__` lookups.

Lifecycle contract (mirrors the filter side's lifecycle from [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 9):

- **Registration is idempotent for the same `(name, orderset_class)` pair.** Calling `materialize_input_class("GalaxyOrderInputType", cls_a)` twice with the same `cls_a` is a no-op; the second call neither raises nor reassigns the module global.
- **Registration raises [`ConfigurationError`][glossary-configurationerror] when the same name is claimed by a DIFFERENT orderset class.** `materialize_input_class("GalaxyOrderInputType", cls_a)` followed by `materialize_input_class("GalaxyOrderInputType", cls_b)` raises with both classes' qualified names in the message.
- **`registry.clear()` (the model-to-`DjangoType` registry's clear) clears the order input lifecycle ledger and removes every materialized class from the module's global namespace.** The shared clear point lets test-fixture reload patterns reset all three subsystems (`TypeRegistry`, filter-inputs, order-inputs) in one call.
- **Import-cycle-safe integration.** [`django_strawberry_framework/registry.py`][registry] uses local imports inside `TypeRegistry.clear()` for both the filter-input clear AND the order-input clear (mirrors M5 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev3 + M4 of rev8):

  ```python
  # django_strawberry_framework/registry.py — adds two order-side blocks
  # next to the shipped filter-side blocks. The existing model-state
  # clears (8 lines) and filter-side blocks are unchanged from
  # DONE-027-0.0.8; only the two order-side blocks are new. Field
  # names below are verbatim from registry.py:43-50 (per B3 of
  # docs/feedback.md rev1; spec-rev1 mis-named these as
  # `_types_by_model` / `_primary_types`).
  class TypeRegistry:
      def clear(self) -> None:
          # Shipped model-state clears (UNCHANGED — verbatim from
          # registry.py:404-410).
          self._types.clear()
          self._primaries.clear()
          self._models.clear()
          self._enums.clear()
          self._definitions.clear()
          self._pending.clear()
          self._finalized = False

          # Filter-input namespace clears (shipped DONE-027-0.0.8 —
          # UNCHANGED). Both blocks use `pass` + `else:` so a partial-
          # load environment never short-circuits a later cleanup phase
          # added below.
          try:
              from .filters.inputs import clear_filter_input_namespace
          except ImportError:
              pass
          else:
              clear_filter_input_namespace()
          try:
              from .filters import _helper_referenced_filtersets
          except ImportError:
              pass
          else:
              _helper_referenced_filtersets.clear()

          # Order-input namespace clears (this card adds these two
          # blocks). Per B2 of docs/feedback.md rev1, BOTH blocks use
          # `except ImportError: pass` + `else:` — NOT `return` on the
          # last block, because a future card may add a fifth clear
          # phase (e.g., aggregates 0.1.3) and a `return` here would
          # silently skip it on a partial-load environment. The
          # symmetric `pass` + `else:` shape is the latent-footgun fix
          # the filter side's `clear_filter_input_namespace` body
          # explicitly calls out (M-core-4 review).
          try:
              from .orders.inputs import clear_order_input_namespace
          except ImportError:
              pass
          else:
              clear_order_input_namespace()
          try:
              from .orders import _helper_referenced_ordersets
          except ImportError:
              pass
          else:
              _helper_referenced_ordersets.clear()
  ```

  A package test imports `django_strawberry_framework.registry` alone (before importing `django_strawberry_framework.orders`) and verifies `registry.clear()` runs without `ImportError` — pinning the import-cycle-safe contract for the new local imports (mirrors `test_registry_clear_works_without_filters_imported` from the filter side).
- **Partial-finalize recovery.** If `finalize_django_types()` raises mid-phase-2.5, the lifecycle ledger and the module globals retain whatever was materialized before the raise. A subsequent `finalize_django_types()` call resumes; the idempotent `(name, orderset_class)` check lets already-materialized classes pass through cleanly.
- **Public `clear_order_input_namespace()` helper.** Exposed from `django_strawberry_framework.orders.inputs` so tests that need to clear the order namespace WITHOUT clearing the full `TypeRegistry` have a dedicated entry point. `registry.clear()` calls this helper internally.

Justification:

- Per-subsystem module globals match Strawberry's `LazyType.resolve_type` semantics (module-path-only, not object-path) — verified during the filter side's rev2 H1.
- The two Layer-3 subsystems each own their own per-module namespace; collapsing both into the `TypeRegistry` would mix string-keyed input-class entries with model-keyed `DjangoType` entries, weakening the type contract.
- The shared `registry.clear()` entry point keeps the test-fixture reload pattern (the canonical `_reload_project_schema_for_acceptance_tests` fixture at [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`][fakeshop-test-library-reload]) working unchanged — one call clears all three subsystems.
- Sibling Aggregation subsystem (`0.1.3`) will reuse this exact lifecycle shape with `django_strawberry_framework.aggregates.inputs` as a fourth co-cleared namespace.

Alternatives considered (and rejected):

- **Sidecar `_input_type_registry: dict[str, type]` in `orders.inputs`.** Rejected per the filter side's H1 — Strawberry's `LazyType.resolve_type` cannot reach into a dict.
- **Single shared `_input_type_registry: dict[str, type]` across filter + order subsystems.** Rejected — the namespaces are disjoint by module path; sharing one dict would force the same module path on both subsystems and either confuse `LazyType.resolve_type` (which reads `module.__dict__`) or require a wrapper module that re-exports both subsystems' classes.
- **Skip the `clear_order_input_namespace()` integration with `registry.clear()`.** Rejected — test-fixture reload patterns would leak between test runs.

### Decision 10 — Joint `0.0.8` cut

`0.0.8` ships two cards as a bundle: `DONE-027-0.0.8` (Filtering subsystem — already shipped under `[Unreleased]` per its own Decision 10 + the L5 contingency NOT-triggered branch because it shipped first) and `WIP-ALPHA-028-0.0.8` (this card — Ordering subsystem). **This card is the last `0.0.8` card to ship**, so the L5 contingency from [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] Decision 10 and [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 10 applies — **this card owns the joint-cut version bump quintet**.

Slice 5 of this card lands the bump atomically:

(a) `pyproject.toml`'s `version = "0.0.7"` → `version = "0.0.8"`.
(b) [`django_strawberry_framework/__init__.py`'s `__version__ = "0.0.7"`][package-init] → `__version__ = "0.0.8"`.
(c) [`tests/base/test_init.py`'s pinned version assertion][test-base-init] (`"0.0.7"` → `"0.0.8"`).
(d) The `[Unreleased]` → `[0.0.8] - <DATE>` promotion in `CHANGELOG.md` (with the current date). The `[Unreleased]` section already carries the Filtering subsystem's `### Added` / `### Changed` bullets from `DONE-027-0.0.8`'s Slice 5; this card's Slice 5 appends the Ordering subsystem's bullets to the same `[Unreleased]` block BEFORE the promotion, so the resulting `[0.0.8]` section carries both subsystems' bullets in a single dated release entry.
(e) Doc sweeps that follow from the bump: `docs/README.md` moves filter + order symbols from "Coming in `0.1.0`" to "Shipped today (`0.0.8`)"; `README.md` adds the order symbols to the shipped-symbol bullet list under the `0.0.8` boundary.

Justification:

- Each card lands self-contained code, tests, and docs; the version bump is the joint cut-over signal.
- Doing the bump on the filter card would have caused the cohort's two cards to compete for `0.0.8`; the L5 contingency (last card owns) is the precedent both prior specs (spec-016 and spec-021) pinned.
- Precedent: [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] Decision 10 pinned the same posture for the `0.0.7` five-card cohort (where the `safe_wrap_connection_method` card ended up owning the bump under L5); [`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][spec-025] Decision 8 documented the same post-cut behavior.
- The `[Unreleased] → [0.0.8]` promotion happens in this card's Slice 5 because that is the same commit that lands the version bump trio — keeping them in one atomic commit prevents a release-tag mismatch between `pyproject.toml` and `CHANGELOG.md`.

**Contingency check.** This card is currently the last `0.0.8` card scheduled. If a maintainer adds a new `WIP-ALPHA-NNN-0.0.8` card AFTER this card moves to in-progress but BEFORE this card merges (an unusual but possible scenario), and that new card ships before this one, then the L5 contingency does NOT apply to this card — the new last card owns the bump instead. In that case, this card's Slice 5 drops the version-bump quintet AND drops the `[Unreleased] → [0.0.8]` promotion; the new card's Slice 5 picks them up.

**Deterministic check (N6 of [`docs/feedback.md`][feedback] rev1).** The Slice-5 author runs this command at merge time:

```bash
grep -E 'WIP-ALPHA-[0-9]+-0\.0\.8' KANBAN.md
```

If the only match is this card (`WIP-ALPHA-028-0.0.8`), the L5 contingency applies and Slice 5 lands the version-bump quintet. If any other `WIP-ALPHA-NNN-0.0.8` card matches, the Slice 5 author drops the version-bump steps and the other card's Slice 5 carries them. The check is deterministic and self-contained — no honor-system pass through judgment-of-the-day. DoD item 24 below references this command.

Alternatives considered (and rejected):

- **Defer the version bump to a separate maintainer-cut card** (a hypothetical `WIP-CUT-NNN-0.0.8` that does nothing but stamp the release). Rejected: adds a third card to the `0.0.8` cohort for zero implementation gain; the L5 contingency already covers the joint-cut case cleanly.
- **Bump on the Filtering card AND let this card ship under `[Unreleased]`.** Rejected: the Filtering card explicitly deferred the bump per its Decision 10 / L5 contingency NOT-triggered branch; flipping that decision retroactively would require an amendment to a shipped spec, which is the wrong direction.

### Decision 11 — `order_input_type(OrderSet)` consumer helper

The package ships a small public helper at [`django_strawberry_framework.orders.order_input_type`][orders], parallel to the shipped `filter_input_type(FilterSet)`:

```python
from typing import Annotated, TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from django_strawberry_framework.orders import OrderSet


def order_input_type(orderset_class: type["OrderSet"]) -> object:
    """Return the Annotated[...] forward-reference for the orderset's GraphQL input class.

    The returned annotation is the canonical Strawberry forward-reference
    idiom: ``Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]``.
    Consumer resolvers use it as the type annotation for an ``order_by:`` argument
    (which Strawberry's auto-camel-case translates to ``orderBy:`` on the GraphQL
    surface). Strawberry collects the annotation at @strawberry.type decoration
    time, defers resolution, and resolves it via LazyType.resolve_type at
    schema-build time — by which point finalize_django_types() has materialized
    the input class as a module global of django_strawberry_framework.orders.inputs
    (per Decision 6).
    """
    # Validation runs eagerly even though the returned annotation is lazy.
    from django_strawberry_framework.orders.sets import OrderSet
    if not (isinstance(orderset_class, type) and issubclass(orderset_class, OrderSet)):
        raise TypeError(
            "order_input_type() requires an OrderSet subclass; got "
            f"{orderset_class!r}"
        )
    # Record the OrderSet for the orphan check at finalize time
    # (order_input_type-referenced ordersets that are never wired via
    # Meta.orderset_class raise ConfigurationError at finalize — mirrors
    # the filter side's H5 from docs/spec-027-filters-0_0_8.md rev5).
    _helper_referenced_ordersets.add(orderset_class)
    name = f"{orderset_class.__name__}InputType"
    # Annotated[<str_variable>, ...] wraps the runtime-computed string as a
    # typing.ForwardRef in the first __args__ position — the same typing
    # contract the filter side ships per M4 of rev5 + M4 of rev6 of
    # docs/spec-027-filters-0_0_8.md. Do NOT refactor into a literal string
    # interpolated outside the Annotated call; LazyType.resolve_type requires
    # the ForwardRef-wrapped form to resolve via module.__dict__.
    return Annotated[name, strawberry.lazy("django_strawberry_framework.orders.inputs")]
```

Consumers use it as a normal Python type annotation in a resolver signature:

```python
@strawberry.field
def all_galaxies(
    self,
    info: strawberry.Info,
    order_by: order_input_type(GalaxyOrder) | None = None,
) -> list[GalaxyType]:
    queryset = GalaxyType.get_queryset(models.Galaxy.objects.all(), info)
    if order_by is not None:
        queryset = GalaxyOrder.apply_sync(order_by, queryset, info)
    return queryset
```

**Evaluation timing.** Strawberry evaluates the annotation during schema declaration / collection — same mechanics as the filter side per M6 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev5. With normal annotations the call evaluates at module-load time; with `from __future__ import annotations` (PEP 563), Strawberry resolves it via `typing.get_type_hints(resolver, ...)` at type-collection time, evaluating the string in the resolver's `__globals__`. Implications: (a) `GalaxyOrder` MUST be importable from the resolver module's globals at type-processing time; (b) `order_input_type` is safe to call repeatedly with the same `OrderSet` (the `_helper_referenced_ordersets` set ledger is idempotent on repeated calls).

**Orphan `OrderSet` validation.** An `OrderSet` referenced via `order_input_type(MyOrder)` but never wired via `Meta.orderset_class = MyOrder` on any `DjangoType` would not be materialized by finalizer phase 2.5 — `LazyType.resolve_type` would raise `KeyError` for `MyOrderInputType` at `strawberry.Schema(...)` time. The package fails loud at finalize per the same shape the filter side ships (H5 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev5):

- `order_input_type` records every `OrderSet` it is called with into a module-level `_helper_referenced_ordersets: set[type[OrderSet]]` in [`django_strawberry_framework.orders`][orders].
- Finalizer phase 2.5 (after iterating `Meta.orderset_class`-wired ordersets) compares the helper-referenced set against the set of wired ordersets; for every orphan, raises [`ConfigurationError`][glossary-configurationerror] with: `"OrderSet '<MyOrder>' is referenced via order_input_type(...) but never assigned to a DjangoType via Meta.orderset_class. Add 'orderset_class = <MyOrder>' to the relevant DjangoType's Meta."`
- `registry.clear()` clears `_helper_referenced_ordersets` along with the model-to-`DjangoType` registry and the order-input namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- New test `test_orphan_order_input_type_reference_raises_at_finalize` pins this.

Justification:

- Symmetry with the shipped `filter_input_type` is the load-bearing argument — the two helpers are intentionally the same shape so consumers using both subsystems see one mental model. A future maintainer reading the code finds two helpers with one design.
- Eager validation (`TypeError` at call time for a non-`OrderSet`) catches misuse at the resolver-declaration site instead of letting Strawberry surface a more cryptic schema-build-time error.
- The orphan-validation shape closes the same trap the filter side closed in rev5: without it, an `order_input_type(StandaloneOrder)` reference would surface as a `LazyType.resolve_type` `KeyError` at `strawberry.Schema(...)` time, well after the resolver-declaration site.

Alternatives considered (and rejected):

- **No helper; consumers spell out `Annotated[...]` themselves.** Rejected: ties consumer code to the package's internal module path; bypasses validation; not the package's `Meta`-driven shape.
- **Helper returns `<Name>OrderInputType` directly (a class).** Rejected: the class doesn't exist yet at module-load time — it's materialized later by `finalize_django_types()`. Returning a class at module-load time would force the helper to eagerly run the finalizer, which contradicts definition-order independence.
- **Helper is a method on `OrderSet`: `GalaxyOrder.input_type()`.** Rejected: viable shape, but adds class-method surface to every `OrderSet` for the sake of one call site per resolver. The module-level function form is the smaller import and the more discoverable doc entry — and matches the filter side's helper shape.
- **Defer the helper to `0.0.9`** (let `DjangoConnectionField` accept `orderset_class=` directly). Rejected: `0.0.8` consumers cannot wait for `0.0.9` to expose a working `orderBy:` argument; this card's [Goals](#goals) item 5 requires a consumer-facing path now.

### Decision 12 — Layer 6 and DISTINCT ON deferred to `0.0.9`

The [`KANBAN.md`][kanban] card body explicitly raises the Layer-6 design question: "Layer 6 (memoized dynamic OrderSet generation): **no cookbook counterpart**. The cookbook ships no `orderset_factories.py` and no `_dynamic_orderset_cache` — only the filter side has the dynamic-factory mechanism. Our ordering subsystem must either design Layer 6 fresh (mirroring the filter side's `filterset_factories.py::_dynamic_filterset_cache`) or skip the dynamic-ordering-for-connection-field case and require explicit `orderset_class` declarations on every consumer. **Pin this decision in the spec.**" The card body also raises the DISTINCT ON question implicitly via the cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` modifiers and [`AdvancedOrderSet.apply_distinct`][upstream-cookbook-orderset] Window-function emulation.

**Decision: both Layer 6 and DISTINCT ON ship in `0.0.9`, NOT this card.**

Layer 6 deferral rationale:

- **No `0.0.8` consumer surface needs it.** `DjangoListField` is out of scope per [Non-goals](#non-goals) (its two-argument `(root, info)` wrapper doesn't preserve resolver arguments). `DjangoConnectionField` does not exist yet. The dynamic-factory machinery would be invented for a hypothetical caller.
- **Even if the connection field landed in `0.0.8`**, the simplest connection-field design requires an explicit `orderset_class` declaration on every connection field that wants order arguments — same shape the cookbook's connection field uses. The dynamic-factory cache is an optimization for the case where the consumer wants `orderBy:` on a connection field WITHOUT declaring a sibling `OrderSet` class; deferring the optimization until the use case is real is the right call.
- **Forward path.** When [`DjangoConnectionField`][glossary-djangoconnectionfield] (`0.0.9`) lands, that card decides whether to:
  - **(a)** design Layer 6 fresh mirroring the filter side's [`django_graphene_filters/filterset_factories.py::_dynamic_filterset_cache`][upstream-cookbook-filterset-factories] (cache keyed by `(model, fields, extra_meta)`, generating an anonymous `OrderSet` subclass on demand), OR
  - **(b)** require explicit `Meta.orderset_class` on every connection field. This card's design supports either choice — the explicit-declaration path works today; the dynamic-factory path would slot in at `factories.py::get_orderset_class` + `factories.py::_dynamic_orderset_cache` without disturbing the shipped Layers 1-5.

DISTINCT ON deferral rationale:

- **The cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` conflate two distinct concerns.** Direction and DISTINCT ON partitioning are orthogonal — a consumer wanting `ORDER BY name ASC` with `DISTINCT ON (category)` is forced into the cookbook's enum shape (a `category: ASC_DISTINCT` modifier on the partition field) which is hard to read. Six members (ASC / DESC / four NULLS variants) is already at the edge of legibility for a leaf-field enum; adding DISTINCT modifiers would push it to eight or more.
- **A separate `Meta.distinct = ("category",)` declaration** is the cleaner shape: ordering names the sort columns, distinct names the partition columns, and a `distinct_on:` argument (or a per-`OrderSet` flag) controls when DISTINCT ON applies. The design space is large enough to deserve its own decision.
- **PostgreSQL-only native DISTINCT ON** vs the cookbook's Window-function emulation for non-PostgreSQL backends is a separate question (the cookbook ships both code paths via `apply_distinct` / `_apply_distinct_postgres` / `_apply_distinct_emulated`). Deciding which to ship, when, and how to declare backend assumptions is a `0.0.9` design — not a `0.0.8` one.
- **Forward path.** The `0.0.9` cohort grows a sibling `WIP-ALPHA-NNN-0.0.9 — DISTINCT ON support` card (or the design lands inside the `DjangoConnectionField` card) with its own `Meta.distinct` design, a `distinct_on:` argument, and the PostgreSQL-native / Window-emulation choice.

Justification:

- Layer 6 has no consumer in `0.0.8`; designing it now would invent machinery for a hypothetical caller.
- DISTINCT ON deserves a clean design (partition vs sort orthogonality) that the cookbook's enum-modifier shape obscures.
- Both deferrals are forward-compatible — this card's shipped surface does not block either future design.

Alternatives considered (and rejected):

- **Ship Layer 6 in `0.0.8` mirroring the filter side's `_dynamic_filterset_cache`.** Rejected — no `0.0.8` consumer needs it; the connection-field card is the natural home for the design.
- **Ship DISTINCT ON in `0.0.8` via the cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` + `apply_distinct` port.** Rejected — the enum shape conflates orthogonal concerns; a separate `Meta.distinct` design is cleaner; the design space deserves its own card.
- **Ship DISTINCT ON in `0.0.8` via a separate `Meta.distinct = (...)` design.** Rejected as scope creep — the `0.0.8` cut is already large (filter + order subsystems); adding a third design decision (DISTINCT ON's partition-vs-sort orthogonality + PostgreSQL-vs-emulation choice) bloats the cut.

**Forward-compatibility previews (per O1 + O2 of [`docs/feedback.md`][feedback] rev1).** These are intentional non-commitments — the `0.0.9` design is not blocked by anything this card pins, but a future reader benefits from knowing which directions remain open:

- **O1 — `Meta.distinct` shape.** The `0.0.9` DISTINCT ON design has not been chosen yet. Two shapes are forward-compatible with this card's surface: (a) a tuple-of-column-names declaration `Meta.distinct = ("category", "name")` — direct and minimal, but asymmetric with the `Meta.filterset_class` / `Meta.orderset_class` pattern (which both reference *classes*); (b) a class-reference declaration `Meta.distinct_class = MyDistinct` where `MyDistinct` is a `Meta`-driven class carrying the partition-column declarations and optional `check_*_permission` gates — symmetric with the rest of the Meta-key surface but heavier. The `0.0.9` card chooses one; this card's `Meta` validator does not need to know which yet, because `Meta.distinct` and `Meta.distinct_class` are both currently in the deferred-key set's "not yet declared" frontier (neither is in `DEFERRED_META_KEYS` today — `base.py:48-55` carries only `orderset_class`, `aggregate_class`, `fields_class`, `search_fields` — and the validator's typo guard at `_validate_meta` time would reject either as an unknown key, which is fine for `0.0.8`). **Staleness caveat (per N-new-3 of [`docs/feedback.md`][feedback] rev2):** this state is accurate AS OF `0.0.8`. The `0.0.9` design may add either key to `DEFERRED_META_KEYS` before its corresponding subsystem ships, per the deferred-key promotion-gate convention — at which point the typo-guard rejection becomes a "deferred key" rejection with a different error message. A future reader cross-checking against the live `DEFERRED_META_KEYS` value should expect this divergence and not panic.
- **O2 — Layer 6 escape-hatch shape.** The `0.0.9` `DjangoConnectionField` card may want BOTH paths: an explicit `Meta.orderset_class` declaration AND a dynamic-factory fallback for the case where the connection field is declared as `connection_for(Model)` without a sibling `OrderSet` class. This card's design supports both forward-compatibly — Layers 1-5 are independent of the existence of a Layer 6 cache, and `factories.py::get_orderset_class` + `factories.py::_dynamic_orderset_cache` (the symbols Layer 6 would introduce) can be added without disturbing the shipped layer set. **The `0.0.8` shape does not foreclose the factory path** — a future reader of Decision 12 should know this card is forward-compatible to both choices, not committed to the explicit-only path.

### Decision 13 — Live HTTP coverage strategy

Package coverage is earned through fakeshop live `/graphql/` HTTP flows where practical per the [`docs/TREE.md`][tree] coverage-priority rule ("Any package coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against fakeshop MUST be earned in `examples/fakeshop/test_query/`").

Live HTTP tests (Slice 4) land in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] and cover (13 tests total): scalar-field ascending order, scalar-field descending order with NULLS positioning, forward-FK relation order, reverse-FK relation order with denormalized-multiplicity asserted (per M5 of [`docs/feedback.md`][feedback] rev1), M2M relation order through the absolute-import-path `RelatedOrder` resolution, flat-shorthand path order (`Meta.fields = ["shelf__code"]` → `shelfCode:` per M2 of rev1), composition with the shipped Filtering subsystem, composition with the optimizer (`assertNumQueries(N)` against a filtered + ordered queryset with nested selection), root `get_queryset` honoring, **split-pair active-input-only `check_*_permission` discipline** — `denies_for_active_field` + `quiet_for_inactive_field` per M6 of rev1, multi-field priority ordering, AND **two no-op edge-case tests** — `orderBy: []` empty-list pass-through + `orderBy: [{ name: null }]` null-direction skip per M7 of rev1.

Package-internal tests (`tests/orders/`) land in **7 files total** per N4 of [`docs/feedback.md`][feedback] rev1: 1 `__init__.py` shell + 4 mirror test files (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`) + 1 phase-2.5-binding-pass test (`test_finalizer.py`) + 1 cross-card composition test (`test_composition.py`, Slice 6). Each file covers what the live HTTP path cannot easily reach: cycle-safe expansion via `_is_expanding_fields` recursion guard, `LazyRelatedClassMixin.resolve_lazy_class` two-step resolution failure paths, `Ordering` enum's `resolve(field_path)` returning correct `OrderBy` expressions, `get_flat_orders` recursive parsing across nested `RelatedOrder` inputs, [`ConfigurationError`][glossary-configurationerror] surface for invalid `Meta.fields`, etc.

Justification:

- Mirrors the shipped filter side's coverage strategy per [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 12 — same trees, same split, same coverage-priority rule.
- The live HTTP path exercises the most ORM cooperation (`order_by(...)` interacting with `select_related` / `prefetch_related`) — properties an in-process `schema.execute_sync(...)` test cannot easily capture without significant SQL-shape setup.
- The package-internal `tests/orders/` tree catches edge cases (cycle detection, error shapes, NULLS positioning) the live HTTP path cannot reach without contrived orderset declarations.

Alternatives considered (and rejected):

- **Skip live HTTP coverage; cover everything via `tests/orders/`.** Rejected per the [`docs/TREE.md`][tree] coverage-priority rule.
- **Cover everything via live HTTP; skip package-internal tests.** Rejected — cycle-detection / error-surface paths are not reachable through normal consumer GraphQL queries.

## Implementation plan

The card ships as **six slices** aligned with the [Slice checklist](#slice-checklist). Slices 1–5 each map to one commit; Slice 6 lands in this card's PR (NOT held — the Filtering subsystem already shipped, so the composition smoke test has both halves available). The per-commit breakdown exists for review legibility; squashing Slices 1–5 + Slice 6 into a single PR is acceptable given the cohesive scope.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Foundation (`base.py` + `sets.py` + `inputs.py` skeleton + the `apply_sync` / `apply_async` classmethod pair) | [`django_strawberry_framework/orders/__init__.py`][orders], [`django_strawberry_framework/orders/base.py`][orders], [`django_strawberry_framework/orders/sets.py`][orders], [`django_strawberry_framework/orders/inputs.py`][orders] (Ordering enum + namespace skeleton), [`tests/orders/__init__.py`][test-orders] (new), [`tests/orders/test_base.py`][test-orders] (new), [`tests/orders/test_sets.py`][test-orders] (new) | ~20 (`Ordering` enum members + `resolve()`; `RelatedOrder` accepts class/string/unqualified; `OrderSet` rejects unknown `Meta.fields`; `apply_sync` + `apply_async` (no `apply` dispatcher — dropped per H1 of `docs/feedback.md` rev1); `check_permissions` active-input-only scope; `get_flat_orders` recursive parse) | `+810 / -0` |
| 2 — Factories (`factories.py` BFS) | [`django_strawberry_framework/orders/factories.py`][orders] (new), [`django_strawberry_framework/orders/inputs.py`][orders] (extend), [`tests/orders/test_factories.py`][test-orders] (new), [`tests/orders/test_inputs.py`][test-orders] (new) | ~14 (BFS visits every reachable orderset via `orderset_cls.get_fields()`; `materialize_input_class` idempotent; `clear_order_input_namespace` clears module globals; `convert_order_field_to_input_annotation` emits `Ordering | None` for leaf fields; `_helper_referenced_ordersets` tracks `order_input_type` calls) | `+450 / -0` |
| 3 — Wiring (`Meta.orderset_class` promotion + finalizer phase-2.5 binding + lifecycle helpers + orphan validation) | [`django_strawberry_framework/types/base.py`][base] (`DEFERRED_META_KEYS` → `ALLOWED_META_KEYS` move + validation via `_validate_orderset_class` mirroring `_validate_filterset_class`), [`django_strawberry_framework/types/definition.py`][definition] (add `orderset_class` slot), [`django_strawberry_framework/types/finalizer.py`][finalizer] (phase 2.5 grows `_bind_ordersets()` four-subpass umbrella helper next to `_bind_filtersets()`), [`django_strawberry_framework/orders/__init__.py`][orders] (add `_helper_referenced_ordersets` set + extend `order_input_type` to record into it), [`django_strawberry_framework/registry.py`][registry] (`clear()` adds order-input + helper-set clear blocks), [`tests/types/test_base.py`][test-types] (validator extension), `tests/orders/test_finalizer.py` (new) | ~18 (validator accepts/rejects, four-subpass ordering pins owner-binding-before-expansion, idempotent rerun, partial-finalize recovery, `registry.clear()` co-clear runs filter + order namespaces together, lazy-related-order resolution at finalize, orphan-OrderSet validation at finalize raises `ConfigurationError`) | `+300 / -3` |
| 4 — Live HTTP coverage in fakeshop | [`examples/fakeshop/apps/library/orders.py`][fakeshop-library] (new, carrying `BranchOrder` / `ShelfOrder` / `BookOrder` / `LoanOrder` / `PatronOrder`), [`examples/fakeshop/apps/library/orders_genre.py`][fakeshop-library] (new, carrying `GenreOrder` — cross-module fixture for the Layer-2 absolute-import-path test), [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (extend with `Meta.orderset_class` + `order_input_type(...)` annotations on root resolvers), [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (extend) | 13 (scalar ASC / scalar DESC_NULLS_LAST / forward-FK relation / reverse-FK relation with denormalized-multiplicity asserted (per M5 of rev1) / M2M absolute-import-path RelatedOrder / flat-shorthand path `shelfCode` (per M2 of rev1) / filter + order composition / optimizer cooperation under `assertNumQueries` / root `get_queryset` honoring / split-pair active-input-only `check_<field>_permission` — `denies_for_active_field` + `quiet_for_inactive_field` (per M6 of rev1; counts as two tests) / multi-field priority via list-element ordering / empty-list no-op `orderBy: []` (per M7 of rev1) / null-direction no-op `orderBy: [{ name: null }]` (per M7 of rev1)) | `+330 / -5` |
| 5 — Docs + KANBAN + CHANGELOG + version bump | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`README.md`][readme], [`TODAY.md`][today], [`KANBAN.md`][kanban], [`CHANGELOG.md`][changelog], `pyproject.toml`, [`django_strawberry_framework/__init__.py`][package-init], [`tests/base/test_init.py`][test-base-init] | 0 | `+110 / -30` |
| 6 — Cross-card composition smoke test with the shipped Filtering subsystem | [`tests/orders/test_composition.py`][test-orders-composition] (new) | 1 (filter + order composition: SQL carries both WHERE and ORDER BY; SDL exposes both `filter:` and `orderBy:` arguments on the same field) | `+45 / -0` |

Total expected delta (Slices 1–6): ~2000 lines across six slices.

The six slices must be authored in order. Slice 2 depends on Slice 1 (the factories consume the `OrderSet` metaclass and the `RelatedOrder` primitive); Slice 3 depends on Slice 2 (the finalizer-phase-2.5 binding calls `OrderArgumentsFactory(...)`); Slice 4 depends on Slice 3 (the fakeshop live HTTP coverage threads through the promoted `Meta.orderset_class`); Slice 5 depends on Slice 4 (the docs reference the live HTTP coverage as the canonical "what this looks like" example, AND the version bump must be the last touch); Slice 6 depends on Slices 3+4 (the composition test needs both the wiring AND the live fakeshop declarations).

## Edge cases and constraints

- **Same-module `RelatedOrder` references** (e.g., `BranchOrder` and `ShelfOrder` declared in the same `orders.py` with `RelatedOrder("ShelfOrder")` and `RelatedOrder(BranchOrder)` respectively). The Layer-2 module-fallback resolution handles this; the absolute-path lookup fails (the module isn't fully loaded yet) and the `bound_class.__module__` retry succeeds. Same shape the filter side ships.
- **Cross-module `RelatedOrder` references via absolute path** (e.g., `RelatedOrder("apps.library.orders_genre.GenreOrder")`). The Layer-2 absolute-path lookup succeeds; the `bound_class.__module__` retry is never reached. Exercised by the fakeshop `BookOrder.genres` declaration per [Slice 4](#slice-checklist).
- **Circular `RelatedOrder` cycles** (`A → B → A`). The Layer-4 `_is_expanding_fields` recursion guard breaks the cycle; the cache writes only when no string `_orderset` remains on any related order (the two-condition guard). A genuine cycle exhausts the guard and raises [`ConfigurationError`][glossary-configurationerror] with the offending class named.
- **`Meta.fields = "__all__"`** (the shorthand). Expands to every **concrete** model field (the cookbook's [`get_concrete_field_names`][upstream-cookbook-mixins] semantics — excludes relations). Relations only become orderable when the consumer declares an explicit `RelatedOrder(...)`. Narrower than the filter side's `"__all__"` (which includes PK / FK columns for `GlobalIDFilter` reachability) because ordering does NOT need a Relay-vs-scalar branch — `ORDER BY id` against any model works the same regardless of whether the type is Relay-Node-shaped (the SQL `ORDER BY` clause references the column, not the GraphQL ID type).
- **`Meta.fields = ["shelf__code"]`** (the double-underscore path shorthand). Pinned GraphQL shape: **renders as a flat field named `shelfCode` with an `Ordering` leaf** (`orderBy: [{ shelfCode: ASC }]`) — NOT a nested-relation shape `orderBy: [{ shelf: { code: ASC } }]`. Consumers reaching for a nested-relation surface declare an explicit `RelatedOrder(ShelfOrder)` instead. Mirrors the filter side's L1 of rev4 flat-field shape; the runtime normalizer maps the flat field's Python attr to the Django source path via the same `FieldSpec.django_source_path` discipline the filter side ships per M5 of [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] rev8.
- **`Meta.orderset_class = AdminOrder` on a secondary `Meta.primary = False` `DjangoType`**. Per [`Meta.primary`][glossary-metaprimary], the secondary type is registered and reverse-discoverable; the order binding runs on the secondary type's definition exactly the same way it runs on the primary's. The input-type namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) is name-keyed so two `DjangoType`s on the same model with different `orderset_class`es generate two distinct input types.
- **`Meta.orderset_class` on a `DjangoType` that also declares `Meta.interfaces = (relay.Node,)`**. The order binding runs at phase 2.5 after the Relay-Node injection. The `Ordering` enum's leaf-field type does NOT depend on Relay shape (no Relay-vs-scalar branch — ordering by `id` uses the Django PK column regardless), so the order side has no equivalent to the filter side's [Decision 4](#decision-4--upstream-primitives-parity-floor)'s owner-aware FK/PK conditional.
- **Order on a field that is NOT in the `DjangoType`'s `Meta.fields`** (e.g., the type exposes `name` but the orderset declares `description` as orderable). The order clause still applies to the queryset; the consumer can order on columns they cannot select. This matches the cookbook's behavior and is intentional.
- **Order that raises a Django ORM error at queryset-translation time** (e.g., an `ORDER BY relation__field` where the related model's column doesn't exist on the underlying backend). The Django `FieldError` / `NotImplementedError` propagates as a `GraphQLError`; the framework does not pre-validate the backend's supported expressions.
- **Recursion-protected `get_fields`**. When an `OrderSet`'s `Meta.fields` references a relation that loops back to itself (e.g., `RelatedOrder("Self")` for a self-referential model), the `__dict__["_is_expanding_fields"]` recursion guard breaks the loop; the expanded fields stop at one level of self-reference.
- **`Meta.fields` referencing a model property (not a field)**. Rejected at type creation with [`ConfigurationError`][glossary-configurationerror]; only model fields are orderable. Ordering on a property requires a custom expression declaration with an explicit ORM expression (out of scope for this card; deferred to a future custom-expression card).
- **Empty `orderBy:` input** (`orderBy: []`). The apply pipeline returns the unordered queryset; no `order_by(...)` call is made. The optimizer's [Queryset diffing][glossary-queryset-diffing] cooperation is unaffected.
- **`orderBy: [{ name: null }]`** (an `Ordering` field set to GraphQL null). The apply pipeline treats it as if the field were omitted — `Ordering | None = None` is the field type, so `null` decodes to `None`, and `None` directions are skipped in `get_flat_orders` (no `order_by` argument is emitted for that field). The consumer gets no error; the queryset's row order falls through to the next list element (or default ordering if no other element is present).
- **`orderBy: [{ shelf: null }]`** (a `RelatedOrder` field set to GraphQL null). Same as above — the nested `RelatedOrder` input is `None`, so `get_flat_orders` skips the branch.
- **`orderBy: [{ name: ASC }, { name: DESC }]`** (the same field appearing twice with conflicting directions). The list-element-order tie-breaker mechanism means the SECOND entry never affects the result — Django's `order_by(*expressions)` honors the FIRST occurrence of each column (PostgreSQL / SQLite / MySQL all behave this way). The package does NOT pre-validate the consumer's input; the consumer is responsible for the redundant declaration. A live HTTP test pins this behavior for documentation purposes.
- **Async resolver returning an ordered queryset**. Strawberry's async path awaits the resolver; the queryset's `order_by(...)` clause applies normally. The optimizer's async-path support (shipped in `0.0.2`) cooperates without retrofit.
- **`OrderSet`-derived input class name collision across two ordersets that share `__name__`**. Rejected by the per-module input-class namespace's name uniqueness check (per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) lifecycle clause): same `(name, orderset_class)` pair is idempotent; same name from a different orderset raises [`ConfigurationError`][glossary-configurationerror] with both ordersets' qualified names.
- **Partial-finalize recovery for the input-class namespace.** If `finalize_django_types()` raises mid-phase-2.5 (e.g., on an unresolved `RelatedOrder`), already-materialized classes stay in the `django_strawberry_framework.orders.inputs` module's `__dict__` and the lifecycle ledger keeps their provenance. A subsequent `finalize_django_types()` call resumes; idempotent `(name, orderset_class)` keys let already-materialized classes pass through cleanly.
- **Fakeshop schema-reload pattern with already-materialized order inputs.** The reload pattern (`registry.clear()` → reload app schema modules → reload project schema and URLconf) clears the model-to-`DjangoType` registry, the filter-input namespace, AND the order-input namespace in the same `registry.clear()` call; reload then re-runs `finalize_django_types()` and re-materializes the input classes fresh. No stale globals leak between test runs.
- **`order_input_type(orderset_class)` validation**. The helper validates eagerly (`TypeError` at call time for a non-`OrderSet`) even though the returned `Annotated[...]` annotation is lazy. Same shape the filter side's `filter_input_type` ships.
- **Multi-database cooperation**. An `.order_by(...)` clause does not change the queryset's `_db` alias; the multi-database cooperation contract shipped in `DONE-023-0.0.7` (per [Multi-database cooperation][glossary-multi-database-cooperation]) is untouched by order clauses. A future multi-DB test in [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] could exercise the cross-shard ordering shape but is out of scope for this card.

## Test plan

Tests live in two trees, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement is mandatory.

### `tests/orders/` (new tree)

Package tests; system-under-test is `django_strawberry_framework` itself. Five files mirror the source layout one-to-one per the [`docs/TREE.md`][tree] mirror rule:

- [`tests/orders/__init__.py`][test-orders] — empty `__init__.py` shell so pytest collects under `tests.orders.<module>` matching the existing `tests/types/__init__.py` / `tests/optimizer/__init__.py` / `tests/filters/__init__.py` convention.
- [`tests/orders/test_base.py`][test-orders] — covers `RelatedOrder` + the shared `LazyRelatedClassMixin` (via sibling import from `filters.base`). Tests: `RelatedOrder` accepts class / absolute path / unqualified name forms; failed resolution raises [`ConfigurationError`][glossary-configurationerror] with the offending name; `bind_orderset` is called by the metaclass; the shared `LazyRelatedClassMixin` resolves the same way for ordersets as for filtersets (sibling-import test confirms behavioral equivalence).
- [`tests/orders/test_sets.py`][test-orders] — covers `OrderSetMetaclass` + `OrderSet`. Tests: metaclass collects `RelatedOrder` declarations into `cls.related_orders` (MRO-respected, with bases overridden by current class per the cookbook's `OrderSetMetaclass.__new__` shape); metaclass calls `bind_orderset`; `get_fields()` triggers Layer-4 expansion; expansion cache writes only when no string `_orderset` remains; `_is_expanding_fields` breaks cycles; `check_permissions` recurses through `RelatedOrder`s **with active-input-only scope** (per-field gates fire only for fields present in the normalized input); unknown `Meta.fields` raises [`ConfigurationError`][glossary-configurationerror]; **`OrderSet.apply_sync(input_value, queryset, info)` and `apply_async(input_value, queryset, info)` classmethod pair** — the shared apply pipeline normalizes a Strawberry input into a flat list of `(field_path, Ordering)` tuples (consulting `get_flat_orders`), extracts `request` from `info.context` (canonical `request` attribute with `HttpRequest` fallback), runs `check_permissions` with active-input-only scope, applies `queryset.order_by(*expressions)` where each expression is `Ordering.resolve(field_path)`, returns the ordered queryset; tests cover `apply_sync` and `apply_async` success, `apply_sync` with multi-field priority via list-element ordering, `apply_sync` propagating a `GraphQLError` raised by `check_permissions`, `check_permissions` active-input-only scope (`test_check_permissions_only_fires_for_active_order_fields`), `info.context` shape (`test_apply_extracts_request_from_info_context_request_attribute` + `test_apply_extracts_request_from_bare_httprequest_context`); `Ordering.resolve(field_path)` returns the correct `F(...).asc(nulls_first=...)` / `desc(nulls_last=...)` expression for each of the six enum members; **`test_order_accepts_field_not_in_djangotype_meta_fields`** (per M8 of [`docs/feedback.md`][feedback] rev1) — construct a `DjangoType` with `Meta.fields = ("name",)` AND an `OrderSet` with `Meta.fields = ["name", "description"]`; assert (a) the `DjangoType`'s SDL exposes only `name` (NOT `description`); (b) the generated `OrderInputType` SDL exposes both `name: Ordering` AND `description: Ordering`; (c) `apply_sync({description: ASC}, qs, info)` produces `ORDER BY description ASC` on the queryset. Pins the intentional behavior documented in [Edge cases](#edge-cases-and-constraints) ("the consumer can order on columns they cannot select").
- [`tests/orders/test_factories.py`][test-orders] — covers `OrderArgumentsFactory`. Tests: BFS visits every reachable orderset via `orderset_cls.get_fields()`; cycle-safe forward reference resolves via the `Annotated["Name", strawberry.lazy("django_strawberry_framework.orders.inputs")]` shape; the factory derives input field shape from resolved fields, NOT from a parallel map; per-module input-class namespace registers under stable class-derived names; two connection fields on the same model share an input type when the same `OrderSet` is wired; **input-shape parity** — the Strawberry input type derived for `BookOrder.shelf` accepts a `ShelfOrderInputType` shape (via the lazy forward reference) and for `BookOrder.genres` accepts a `GenreOrderInputType` shape; leaf scalar fields accept `Ordering | None` (verified via SDL assertion).
- [`tests/orders/test_inputs.py`][test-orders] — covers `_build_input_fields` + `convert_order_field_to_input_annotation` + `normalize_input_value` + `materialize_input_class` + `order_input_type` + `Ordering`. Tests: `_build_input_fields` emits `RelatedOrder` fields as `Annotated["TargetOrderInputType", strawberry.lazy(...)] | None` and leaf fields as `Ordering | None`; `convert_order_field_to_input_annotation` always returns `Ordering | None` for leaf fields (verified table-driven across scalar / choice / FK / PK / `BigIntegerField` types — ordering does NOT differentiate the value type, only the direction); `normalize_input_value` walks nested `RelatedOrder` input and produces flat `(field_path, Ordering)` tuples (including the `shelf__code` path for `RelatedOrder("ShelfOrder", field_name="shelf")` branches); **`materialize_input_class("Name", cls)`** sets `module.Name = cls` and writes the lifecycle ledger; re-materialization of the same `(name, orderset_class)` is idempotent; re-materialization of the same name from a different `OrderSet` raises [`ConfigurationError`][glossary-configurationerror]; `clear_order_input_namespace()` removes every materialized global and resets the ledger; `order_input_type(non_orderset)` raises `TypeError`; `order_input_type(MyOrder)` returns the documented `Annotated[...]` shape; **`test_order_input_type_returns_forwardref_in_annotation_args`** — calls `order_input_type(MyOrder)`, asserts `result.__args__[0]` is `typing.ForwardRef` and `result.__args__[0].__forward_arg__ == "MyOrderInputType"`; **`test_order_input_type_is_idempotent_under_repeated_calls`** — calls `order_input_type(MyOrder)` three times; asserts each call returns an equivalent `Annotated[...]` shape and `_helper_referenced_ordersets` size remains `1`; **`Ordering` enum's `resolve()`** — table-driven test asserts each of the six members produces the expected `F(value).asc(nulls_first=...)` / `desc(nulls_last=...)` expression via Django's `OrderBy.as_sql` introspection.

`tests/orders/test_finalizer.py` (new, lands in Slice 3) — covers the phase-2.5 binding pass. Tests: `Meta.orderset_class` promotion accepts an `OrderSet` and rejects a non-`OrderSet`; **four-subpass ordering** — `test_phase_2_5_binds_all_owners_before_expansion`: declare `BookType` (with `orderset_class = BookOrder`) and `ShelfType` (with `orderset_class = ShelfOrder`) where `BookOrder.shelf = RelatedOrder("ShelfOrder")`; arrange the registry so `BookType` is iterated FIRST; instrument `ShelfOrder` with a hook that records whether `_owner_definition` was set when `bind_orderset` is called during `BookOrder.get_fields()` Layer-4 expansion; run `finalize_django_types()`; assert `ShelfOrder._owner_definition` is set BEFORE the expansion hook fires; **orphan `OrderSet` validation** — `test_orphan_order_input_type_reference_raises_at_finalize` declares a `StandaloneOrder` referenced via `order_input_type(StandaloneOrder)` on a root resolver but never assigned to any `DjangoType` via `Meta.orderset_class`; runs `finalize_django_types()`; asserts [`ConfigurationError`][glossary-configurationerror] with `"StandaloneOrder"` in the message AND the suggestion-text about wiring `Meta.orderset_class`; the binding pass runs once per `DjangoType`; `finalize_django_types()` is idempotent (re-running it does not re-materialize globals from scratch); a phase-2.5 raise (e.g., from an unresolved `RelatedOrder`) leaves already-materialized globals in place AND the lifecycle ledger consistent; `registry.clear()` invokes `clear_order_input_namespace()` so both registries reset together; lazy-related-order targets unresolved at finalize raise [`ConfigurationError`][glossary-configurationerror]; **`test_registry_clear_works_without_orders_imported`** — subprocess test that runs `python -c "import django_strawberry_framework.registry; django_strawberry_framework.registry.registry.clear()"` (importing `registry` alone, NOT `orders`); asserts the subprocess exits cleanly (no `ImportError` from the local import inside `TypeRegistry.clear`). Pins the import-cycle-safe contract for the new local imports.

### `tests/orders/test_composition.py` (Slice 6, new)

In-process test that constructs a `DjangoType` with BOTH `Meta.filterset_class` AND `Meta.orderset_class` set, calls `finalize_django_types()`, and asserts:

- Both factories' input types are reachable from the schema (`<TypeName>FilterInputType` AND `<TypeName>OrderInputType` resolve via `strawberry.Schema(...)` introspection).
- A resolver that consumes both arguments produces a queryset whose SQL carries `WHERE <filter>` AND `ORDER BY <order>` clauses in the expected order (verified via `queryset.query.as_sql(...)` introspection — the SQL string check is fragile but the assertion is robust because the queryset's `.where` and `.order_by` attributes are stable Django internals).
- The shared `LazyRelatedClassMixin` resolution works correctly when called from both subsystems in the same finalize pass (verifies the sibling-import sharing doesn't cause a resolution-state leak).
- The Slice 6 conditional clause from the Filtering spec's [Slice checklist](#slice-checklist) (the composition smoke test was "held until [`WIP-ALPHA-022-0.0.8`][kanban] ships") is satisfied by this card carrying the composition test in this card's PR instead of the filter card's PR.

### `tests/types/test_base.py` (extend)

Add a test pinning the `Meta.orderset_class` promotion from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`: `test_meta_orderset_class_is_promoted_to_allowed_meta_keys` asserts `"orderset_class" not in DEFERRED_META_KEYS` AND `"orderset_class" in ALLOWED_META_KEYS`. Pins the "deferred key promoted only when subsystem ships" contract per [Decision 7](#decision-7--metaorderset_class-promotion-gate).

### `examples/fakeshop/test_query/test_library_api.py` (extend)

System-under-test is the live `/graphql/` HTTP endpoint. Coverage MUST be earned here per the [`docs/TREE.md`][tree] coverage-priority rule. **Exactly 13 new live HTTP tests**:

- `test_library_branches_order_by_name_asc` — `{ allLibraryBranches(orderBy: [{ name: ASC }]) { id name } }`; assert response branches are sorted by name ascending.
- `test_library_books_order_by_title_desc_nulls_last` — `{ allLibraryBooks(orderBy: [{ title: DESC_NULLS_LAST }]) { id title } }`; assert NULLS positioning is honored (rows with `title=NULL` appear last); verifies `Ordering.resolve(...)` produces `F('title').desc(nulls_last=True)` expression.
- `test_library_books_order_by_forward_fk_relation` — `{ allLibraryBooks(orderBy: [{ shelf: { code: ASC } }]) { id shelf { code } } }`; assert books sorted by their shelf's code; exercises the same-module `RelatedOrder("ShelfOrder")` resolution.
- `test_library_branches_order_by_reverse_fk_relation` — `{ allLibraryBranches(orderBy: [{ shelves: { code: ASC } }]) { id } }`; **assert the denormalized JOIN+ORDER multiplicity explicitly** per M5 of [`docs/feedback.md`][feedback] rev1: seed a multi-shelf Branch (e.g., `Branch(name="Alpha")` with `Shelf(code="A")`, `Shelf(code="C")`, `Shelf(code="E")`) AND a single-shelf Branch (`Branch(name="Beta")` with `Shelf(code="B")`); assert the response carries Alpha three times (once per its shelves, ordered A → C → E interleaved with Beta) — that is the SQL contract for `LEFT JOIN shelf ON branch.id = shelf.branch_id ORDER BY shelf.code`. Pinning the multiplicity (rather than seeding one-shelf-per-branch to dodge it) catches a future regression where the runtime accidentally `.distinct()`s the queryset. The `RelatedOrder` GLOSSARY entry calls out this multiplicity so consumers reaching for reverse-FK ordering know to expect it.
- `test_library_books_order_by_m2m_absolute_import_path` — `{ allLibraryBooks(orderBy: [{ genres: { name: ASC } }]) { id title } }`; exercises the Layer-2 absolute-import-path lazy resolution end-to-end. `GenreOrder` lives in [`examples/fakeshop/apps/library/orders_genre.py`][fakeshop-library] (separate module per [Slice 4](#slice-checklist)); `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` resolves at finalize via `import_string`.
- `test_library_books_filter_and_order_compose` — `{ allLibraryBooks(filter: { circulationStatus: { exact: AVAILABLE } }, orderBy: [{ title: ASC }]) { id title circulationStatus } }`; assert response contains only `AVAILABLE` books AND they are sorted by title ascending. Pinpoints filter + order composition (the resolver chains `Filter.apply_sync` → `Order.apply_sync`).
- `test_library_books_order_preserves_optimizer_cooperation` — `{ allLibraryBooks(filter: { ... }, orderBy: [{ title: ASC }]) { id title shelf { id code } genres { id name } } }` under `assertNumQueries(N)`; assert the optimizer's `select_related("shelf")` and `prefetch_related("genres")` survive the filter + order clauses. **What this test pins (per H2 of [`docs/feedback.md`][feedback] rev1):** that the package's selection-tree-derived optimizer plan is NOT invalidated by an `.order_by(...)` clause — Django's ORM extends column fetches as needed to execute the `ORDER BY` clause natively. The test does NOT assert the package adds order columns to `plan.only_fields` (it doesn't, and `0.0.8` does not promise that).
- `test_root_get_queryset_runs_before_order_apply` — pin that the resolver calls `<OwnerType>.get_queryset(...)` BEFORE `OrderSet.apply_sync(...)`. Setup: `BranchType.get_queryset(qs, info)` hides branches whose `city == "restricted"` for anonymous users (mirrors the filter side's M1 of rev8 — same `Branch.city` field, same data shape). Seed `branch_public(name="Alpha", city="Boston")` AND `branch_private(name="Zeta", city="restricted")`. Issue `{ allLibraryBranches(orderBy: [{ name: DESC }]) { id name } }` anonymously. Assert ONLY `branch_public` appears in the response — the root `get_queryset` call hides `branch_private` BEFORE the order clause runs, so the order operates on the visibility-scoped queryset (and `branch_private` does not appear at the head of the DESC list).
- `test_order_check_permission_denies_for_active_field` (per M6 of [`docs/feedback.md`][feedback] rev1 — split from a single combined test so a regression in either half surfaces as a named failure) — `BranchOrder` declares `check_name_permission(request)` that raises `GraphQLError("staff only", extensions={"code": "ORDER_PERMISSION_DENIED"})` for non-staff users. Issue `{ allLibraryBranches(orderBy: [{ name: ASC }]) { id } }` anonymously; assert the response carries an `errors` entry with `extensions.code == "ORDER_PERMISSION_DENIED"`.
- `test_order_check_permission_quiet_for_inactive_field` (per M6 of [`docs/feedback.md`][feedback] rev1 — split partner) — same `BranchOrder` declaration as the previous test. Issue `{ allLibraryBranches(orderBy: [{ city: ASC }]) { id } }` anonymously (the gated `name` field is absent from the input); assert no error AND a successful ordered response (active-input-only scope — the gate fires only when the consumer's input names the gated field).
- `test_library_books_order_by_multi_field_priority` — `{ allLibraryBooks(orderBy: [{ shelf: { code: ASC } }, { title: DESC }]) { id title shelf { code } } }`; seed two books on the same shelf with different titles AND two books on different shelves with the same title; assert the list-element-order tie-breaker mechanism produces the expected result order (shelf code dominates; title is secondary).
- `test_library_books_order_by_flat_shorthand_path` (per M2 of [`docs/feedback.md`][feedback] rev1) — declare `BookOrder` with `Meta.fields = ["shelf__code"]` (NO explicit `RelatedOrder(ShelfOrder)`); issue `{ allLibraryBooks(orderBy: [{ shelfCode: ASC }]) { id title } }`; assert the GraphQL surface accepts the flat `shelfCode` field name (NOT `shelf: { code: ASC }`); assert the runtime normalizer reconstructs the Django ORM path as `shelf__code` (verified by assertion against `queryset.query.order_by` or by SQL substring match). Pins the path-shorthand contract whose mirror on the filter side is covered by spec-027 rev4 L1.
- `test_order_empty_list_passes_through` (per M7 of [`docs/feedback.md`][feedback] rev1) — issue `{ allLibraryBranches(orderBy: []) { id name } }`; assert the response succeeds AND the branches appear in the queryset's default order (no `ORDER BY` clause emitted). Pins the no-op contract for the empty list.
- `test_order_null_direction_skips_field` (per M7 of [`docs/feedback.md`][feedback] rev1) — issue `{ allLibraryBranches(orderBy: [{ name: null }]) { id name } }`; assert the response succeeds AND no `ORDER BY name` clause appears in the executed SQL (the `null` direction decodes to `None` in the Strawberry input and `get_flat_orders` skips `None` directions). Pins the no-op contract for null-direction inputs.

All 13 new live HTTP tests reuse the existing `_reload_project_schema_for_acceptance_tests` fixture at [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`][fakeshop-test-library-reload]. This card's order binding runs through finalizer phase 2.5 on the reload, so the fixture continues to work without modification (the phase-2.5 binding pass naturally re-runs on the post-reload `finalize_django_types()` call). No new fixture is required for the 13 new tests.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Flip [`OrderSet`][glossary-orderset] from `planned for 0.0.8` to `shipped (0.0.8)`. Update entry body to describe the shipped contract: declarative `Meta.model` / `Meta.fields` (list form or `"__all__"` shorthand for every concrete model field); `RelatedOrder` for cross-relation traversal; `check_*_permission` denial gates with **active-input-only scope**; list-shaped `orderBy:` argument with list-element-order tie-breaker mechanism; six-member `Ordering` enum with NULLS positioning; cycle-safe lazy resolution via the five-layer port + Layer 6 deferred to `0.0.9`.
  - Flip [`RelatedOrder`][glossary-relatedorder] from `planned for 0.0.8` to `shipped (0.0.8)`. Update body to describe target acceptance (class / absolute path / unqualified name), the shared Layer-2 module-fallback resolution (sibling import from `filters.base.LazyRelatedClassMixin`).
  - Flip [`Meta.orderset_class`][glossary-metaorderset_class] from `planned for 0.0.8` to `shipped (0.0.8)`. Update body to describe the consumer-facing wiring and the promotion-from-`DEFERRED_META_KEYS` gate.
  - Add a new entry `## order_input_type` documenting the consumer helper from [Decision 11](#decision-11--order_input_typeorderset-consumer-helper). Body: factory returning `Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` for resolver-argument annotations; eager validation; consumer usage `order_by: order_input_type(BranchOrder) | None = None`; orphan validation at finalize.
  - Add a new entry `## Ordering` documenting the public direction enum (six members: `ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST`); `resolve(field_path)` method returning Django `OrderBy` expressions.
  - Update the [Index][glossary-index] table's status column for all five entries (three flips + two new).
  - Document `OrderSet` / `RelatedOrder` / `order_input_type` / `Ordering` under the Ordering category of the [Browse by category][glossary] block. The [Public exports][glossary-public-exports] section is NOT updated here because per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) the order symbols live at `django_strawberry_framework.orders`.

- [`docs/README.md`][docs-readme]
  - Move `OrderSet` / `Meta.orderset_class` / `RelatedOrder` / `order_input_type` / `Ordering` from "Coming in `0.1.0`" to "Shipped today (`0.0.8`)" (the version bump lands in this same Slice 5 commit per [Decision 10](#decision-10--joint-008-cut)).

- [`docs/TREE.md`][tree]
  - Flip the `orders/` subpackage entry from `[alpha]` to on-disk. Move from the "target package layout" section to the "current on-disk layout" section.
  - List the five new files (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`); list the mirrored `tests/orders/` tree (`__init__.py`, `test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`, `test_finalizer.py`, `test_composition.py`).
  - Update the "Test layout going forward" section's `tests/orders/` enumeration to match the on-disk reality.

- [`README.md`][readme]
  - Add `OrderSet` / `RelatedOrder` / `order_input_type` / `Ordering` to the shipped-symbol bullet list (under the `0.0.8` boundary, alongside the filter symbols promoted in `DONE-027-0.0.8`'s Slice 5).

- [`GOAL.md`][goal]
  - The astronomy showcase already references `Meta.orderset_class = orders.GalaxyOrder` and the per-app `orders.py` shape — no edit needed there beyond confirming the references resolve.

- [`TODAY.md`][today]
  - Extend the "Shipped capabilities" enumeration with `OrderSet` / `Meta.orderset_class` / `RelatedOrder` / `Ordering` / `order_input_type`.
  - Extend the fakeshop section to describe the new `BranchOrder` / `BookOrder` / `LoanOrder` / `PatronOrder` declarations under [`examples/fakeshop/apps/library/orders.py`][fakeshop-library] and the live HTTP order coverage under [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library].

- [`KANBAN.md`][kanban] (Slice 5)
  - Move `WIP-ALPHA-028-0.0.8` to the Done column with the next available `DONE-NNN-0.0.8` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). Past-tense Done body:

    > "Shipped the ordering subsystem AND owned the joint `0.0.8` cut. [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], and [`Meta.orderset_class`][glossary-metaorderset_class] (promoted out of `DEFERRED_META_KEYS`) land at [`django_strawberry_framework/orders/`][orders] across five files (`base.py`, `sets.py`, `factories.py`, `inputs.py`, `__init__.py`); `tests/orders/` mirrors the layout. Five-layer lazy-resolution pipeline borrowed from `django-graphene-filters` with the same Strawberry-adapted Layer 5 the Filtering subsystem just shipped (`Annotated[\"TypeName\", strawberry.lazy(\"django_strawberry_framework.orders.inputs\")]` over module globals); the shared `LazyRelatedClassMixin` is reused from `filters.base` via sibling import. Layer 6 (dynamic OrderSet generation) deferred to `0.0.9` alongside `DjangoConnectionField` per Decision 12 of `docs/spec-028-orders-0_0_8.md`. The public `Ordering` enum borrowed verbatim from `strawberry-django` (six members: ASC / DESC / ASC_NULLS_FIRST / ASC_NULLS_LAST / DESC_NULLS_FIRST / DESC_NULLS_LAST) — NULLS positioning honored via Django `F(value).asc/desc(nulls_first=...)` expressions. The list-shaped `orderBy: [<T>OrderInputType!]` argument's element order IS the tie-breaker mechanism. The **resolver-facing API is the classmethod pair `OrderSet.apply_sync(input_value, queryset, info)` and `OrderSet.apply_async(input_value, queryset, info)`** (sync resolvers call the former; async resolvers await the latter), mirroring the shipped filter subsystem's shape. The apply pipeline runs `check_permissions` with **active-input-only scope** (per-field `check_<field>_permission` gates fire only when the consumer's input names the field); extracts the request from `info.context.request` (with an `isinstance(info.context, HttpRequest)` fallback); applies `queryset.order_by(*OrderBy_expressions)` after visibility scoping (`<OwnerType>.get_queryset`) and after optional filter narrowing (`<TypeName>Filter.apply_*`). The new `order_input_type(BranchOrder)` helper produces the resolver-annotation shape; the finalizer enforces orphan validation by raising `ConfigurationError` for any OrderSet referenced via `order_input_type` but never wired via `Meta.orderset_class` (tracked via `_helper_referenced_ordersets`). `registry.clear()` co-clears the order input namespace via `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` — alongside the already-shipped filter clears. Per-package input-class namespace is separate from the model-to-`DjangoType` registry AND from the filter-input namespace (`Meta.primary` design preserved). `Meta.orderset_class` promotion runs through finalizer phase 2.5 via `_bind_ordersets()` with four ordered subpasses mirroring the filter side's discipline; the phase binds `_owner_definition`, calls `get_fields()` only after all owners are bound, materializes each generated input class as a module global of `django_strawberry_framework.orders.inputs` before `strawberry.Schema(...)` runs. [`examples/fakeshop/apps/library/`][fakeshop-library] grows `orders.py` (carrying `BranchOrder` / `ShelfOrder` / `BookOrder` / `LoanOrder` / `PatronOrder`) and `orders_genre.py` (carrying `GenreOrder` — cross-module fixture for the Layer-2 absolute-import-path test) wired through `Meta.orderset_class`; root resolvers accept `order_by:` via `order_input_type(<Name>Order)` annotations and call `<OwnerType>.get_queryset(...)` then optionally `<TypeName>Filter.apply_*` then `OrderSet.apply_*`. [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows exactly 13 live HTTP tests covering scalar ASC / scalar DESC_NULLS_LAST / forward-FK / reverse-FK with denormalized-multiplicity-pinned / M2M absolute-import-path RelatedOrder / flat-shorthand path (`shelf__code` → `shelfCode`) / filter + order composition / optimizer cooperation / root `get_queryset` honoring / split-pair active-input-only `check_<field>_permission` (denies-for-active + quiet-for-inactive) / multi-field priority via list-element ordering / empty-list no-op / null-direction no-op. Spec: `docs/spec-028-orders-0_0_8.md`. The version bump from `0.0.7 → 0.0.8` lands in this card's Slice 5 per [Decision 10](#decision-10--joint-008-cut) L5 contingency (this card is the last `0.0.8` card to ship; the Filtering subsystem `DONE-027-0.0.8` had already shipped under `[Unreleased]` without bumping)."
  - Update the card body's `Definition of done` bullet 1 (`docs/spec-orders.md` → `docs/spec-028-orders-0_0_8.md` after the Step-8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)).
  - Update the `### In progress` summary paragraph (anchored at [`KANBAN.md`][kanban] #"### In progress") to remove `WIP-ALPHA-028-0.0.8` from the active list once this card moves to Done; the `### In progress` summary becomes "No active WIP cards" until the next 0.0.9 card moves in.

- [`CHANGELOG.md`][changelog] (Slice 5)
  - **Append** to the existing `[Unreleased]` `### Added` subsection (the section already carries the Filtering subsystem's bullets from `DONE-027-0.0.8`'s Slice 5):

    > "Ordering subsystem — see the KANBAN past-tense body above for the canonical narrative (per M10 of [`docs/feedback.md`][feedback] rev1, the CHANGELOG and KANBAN past-tense bodies are not duplicated; this CHANGELOG bullet references the KANBAN body as the single source of truth). Headline: `OrderSet` / `RelatedOrder` / `Meta.orderset_class` shipped at `django_strawberry_framework/orders/` (five files); public `Ordering` enum (six members with NULLS positioning); cycle-safe five-layer lazy-resolution pipeline (Layer 6 + DISTINCT ON deferred to `0.0.9`); consumer-facing `order_input_type(OrderSet)` helper; finalizer phase-2.5 `_bind_ordersets()` mirroring the shipped filter side's discipline; 13 live HTTP tests in `examples/fakeshop/test_query/test_library_api.py`. Spec: `docs/spec-028-orders-0_0_8.md`."
  - **Append** to the existing `[Unreleased]` `### Changed` subsection:

    > "[`Meta.orderset_class`][glossary-metaorderset_class] is no longer in `DEFERRED_META_KEYS`; declaring `Meta.orderset_class = MyOrder` now wires through to finalizer phase 2.5 and surfaces a working order input on the GraphQL type. Consumers who declared the key against `0.0.7` saw a [`ConfigurationError`][glossary-configurationerror]; against `0.0.8` it produces an order surface."
  - **Promote** `[Unreleased]` to `[0.0.8] - <DATE>` (current date at merge time) per [Decision 10](#decision-10--joint-008-cut) L5 contingency. The promoted `[0.0.8]` section carries BOTH the Filtering subsystem's bullets (from `DONE-027-0.0.8`'s Slice 5) AND the Ordering subsystem's bullets (this card's Slice 5) AND a final `### Internal` bullet noting the version-bump trio.
  - Per the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed", this Slice-5 bullet is the explicit permission for this card.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **Layer 6 deferral vs `DjangoConnectionField` urgency.** Preferred answer per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009): deferred to `0.0.9` alongside `DjangoConnectionField`. The connection field's design will name whether Layer 6 is needed or whether explicit `orderset_class` on every connection field is acceptable. Fallback: if `DjangoConnectionField` ships before Layer 6 is designed, the connection field can be limited to declared `orderset_class`-only ordering (no implicit `model + fields` shortcut); the dynamic-factory cache lands in a follow-up sub-feature card.
- **DISTINCT ON deferral to `0.0.9`.** Preferred answer per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009): a separate `Meta.distinct = (...)` declaration design lands in `0.0.9` (or in a sibling DISTINCT ON card). The cookbook's enum-modifier approach is rejected as confusing. Fallback: if real consumer demand for DISTINCT ON surfaces before `0.0.9` ships, a `0.0.8.1` patch card can add a minimal `Meta.distinct = (...)` declaration without backporting the full design space; the simpler `0.0.8.1` patch ships with PostgreSQL-only support (no Window-function emulation).
- **`Ordering` enum vs cookbook's `OrderDirection`.** Preferred answer per [Decision 5](#decision-5--ordering-enum-and-argument-shape): ship strawberry-django's six-member enum. Fallback: if consumers report wanting the cookbook's `DISTINCT` modifiers in the same enum (rather than a separate `Meta.distinct` declaration), a follow-up card can add `ASC_DISTINCT` / `DESC_DISTINCT` as additional enum members without breaking the existing six; the changes ship as a `### Added` enum-extension rather than a breaking change.
- **List-shaped `orderBy:` vs sibling singular `order:` argument.** Preferred answer per [Decision 5](#decision-5--ordering-enum-and-argument-shape): single list argument. Fallback: if consumers writing `orderBy: [{ name: ASC }]` find the list-of-one shape verbose, a follow-up card can add a sibling singular `order: <TypeName>OrderInputType` argument that the resolver normalizes into a one-element list internally; the list argument stays.
- **Joint-cut version bump in this card (vs a separate maintainer-cut card).** Preferred answer per [Decision 10](#decision-10--joint-008-cut): this card owns the bump per L5 contingency. Fallback: if a new `WIP-ALPHA-NNN-0.0.8` card appears AFTER this card's Slice 1 is in progress and ships before this card merges, the version bump and `[Unreleased] → [0.0.8]` promotion move to the new card's Slice 5; this card's Slice 5 drops both. The DoD item 24 below carries this contingency clause.
- **`order_input_type` orphan validation false-positive.** Preferred answer per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper): the orphan check raises [`ConfigurationError`][glossary-configurationerror] for any `OrderSet` referenced via `order_input_type` but never wired via `Meta.orderset_class`. Fallback: if a real consumer pattern surfaces where a `OrderSet` is referenced via the helper without being wired (e.g., a generic order-input-type alias used across multiple unrelated `DjangoType`s with different orderset classes), the check ships an opt-out via a `Meta.orderset_class = None` declaration; the validator at `_validate_meta` accepts `None` as a sentinel meaning "intentionally orphan". Deferred until the demand surfaces.
- **Multi-`DjangoType`-per-model orderset binding (Meta.primary interaction).** Preferred answer per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle): the input-class namespace is name-keyed, so two `DjangoType`s on the same model with two different `orderset_class`es generate two distinct input types. The order side's strict-reuse check is simpler than the filter side's because ordering does NOT consult Relay shape (no Relay-vs-scalar branch) — the only owner-sensitive question is "do two owners' `related_target_for` resolutions agree?". Fallback: if a real consumer scenario surfaces where two ordersets on the same model should share an input type, a follow-up card adds an optional `Meta.order_input_alias` key.
- **Per-field permission gate scope (active-input-only vs declaration-only).** Preferred answer per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer): active-input-only, matching the filter side's M2 of rev5 discipline. Fallback: if real consumers prefer the cookbook's "fires for every declared filter" shape, a follow-up card can add an opt-in `OrderSet.check_permissions_mode = "declaration"` class attribute; the active-input-only default stays.
- **`Meta.fields = "__all__"` performance and schema-size growth.** Preferred answer: the BFS factory walks every concrete model field; for models with many fields this is O(field_count) at finalize time but the result is cached, so per-request cost is unaffected. Schema-size growth is linear in `field_count` (one input field per ordered column, NOT `field_count × lookup_count` like the filter side). Apollo / GraphiQL inflation is minor. Fallback: if real-world consumer schemas with very-wide models surface noticeable inflation, a follow-up card adds a `Meta.lookup_subset` shorthand or per-app field-set policy.
- **`order_input_type` and `Ordering` GLOSSARY entry deferral.** Preferred answer (mirroring the filter side's M2 of rev3 / M2 of rev6 pattern for `filter_input_type`): [`docs/spec-028-orders-0_0_8-terms.csv`][spec-028-terms] currently lists 41 terms and does NOT include `order_input_type` or `Ordering`, because the corresponding `## order_input_type` and `## Ordering` headings do not yet exist in [`docs/GLOSSARY.md`][glossary] — the entries land during Slice 5 implementation alongside the CSV rows. The spec body documents both as Slice 5 deliverables ([Slice checklist](#slice-checklist) + [Doc updates](#doc-updates) + DoD item 16); the checker exits 0 against the 41-term CSV during the authoring cycle and against a 43-term CSV after Slice 5 lands. Fallback: if over-zealous CSV discipline is preferred during authoring, add the rows at `order_input_type,order_input_type,The consumer helper this card introduces; GLOSSARY entry created in Slice 5.` and `Ordering,ordering,The public direction enum this card introduces (six members); GLOSSARY entry created in Slice 5.` and accept that the checker will fail with missing-glossary-entry errors until Slice 5 lands.
- **Glossary entry parity for internal symbols.** `OrderSetMetaclass`, `OrderArgumentsFactory`, `_dynamic_orderset_cache` (deferred), `get_flat_orders` are internal symbols not currently in [`docs/GLOSSARY.md`][glossary]. Preferred answer: keep them internal — the consumer surface is `OrderSet` / `RelatedOrder` / `Ordering` / `order_input_type` / `Meta.orderset_class`; the internal symbols are documented via this spec's body and via module docstrings. Fallback: if a future card surfaces one as a public re-export, the glossary entry lands with that card.

## Out of scope (explicitly tracked elsewhere)

- **Aggregation** ([`AggregateSet`][glossary-aggregateset], [`RelatedAggregate`][glossary-relatedaggregate], [`Meta.aggregate_class`][glossary-metaaggregate_class], [`get_child_queryset`][glossary-get_child_queryset]) — `0.1.3`. Future Layer-3 sidecar; reuses Layers 1–4 of this card's lazy-resolution pipeline; runs at the aggregate-input layer not the order-input layer.
- **Field selection** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`. Future Layer-3 sidecar; orthogonal to order machinery (field selection gates result-shape, ordering arranges result-order).
- **Search fields** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`. Future Layer-3 sidecar; consumes the shipped Filtering subsystem's `LOOKUP_PREFIXES` + `construct_search` without modification.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions], [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.0.10`. Future Layer-3 sidecar; composes with this card's `check_*_permission` gates per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) without retrofit.
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — `0.0.9`. Consumes the `OrderArgumentsFactory` output as the connection's `orderBy:` argument source. This card's per-module input-class namespace is the registration point.
- **`DjangoNodeField`** ([`DjangoNodeField`][glossary-djangonodefield]) — `0.0.9`. Root-level single-node lookup; orthogonal to ordering.
- **`DjangoConnection`** ([`DjangoConnection`][glossary-djangoconnection]) — `0.0.9`. Generic return-type alias; orthogonal to ordering.
- **Connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]) — `0.0.9`. The optimizer learns `edges { node { ... } }` selections; ordering composes with it without retrofit because ordering applies at queryset-WHERE-equivalent layer, not at the selection-tree layer.
- **`DjangoListField` argument injection** ([`DjangoListField`][glossary-djangolistfield]) — deferred to `0.0.9`. The shipped `DjangoListField` wraps resolvers with a two-argument `(root, info)` callable that does NOT preserve arbitrary resolver arguments; both `filter:` and `order_by:` argument support for `DjangoListField` lands in the `0.0.9` cohort.
- **Layer 6 dynamic `OrderSet` generation** — deferred to `0.0.9` per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).
- **DISTINCT ON** (cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` + `AdvancedOrderSet.apply_distinct`) — deferred to `0.0.9` per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009).
- **`OrderSequence` tie-breaker descriptor** (strawberry-django's per-field sequence) — NOT planned; positional list-element ordering covers the use case per [Decision 5](#decision-5--ordering-enum-and-argument-shape).
- **Custom expressions (ORM `F(...)` / `Func(...)` / `Case` ordering)** — NOT planned for `0.0.8` or `0.0.9`. Consumers needing custom expressions can override the resolver and call `queryset.order_by(F('column').asc(), ...)` directly; the framework's `OrderSet` apply pipeline is bypassed for that custom case. A future card can add `OrderSet.expressions = {...}` if real demand surfaces.
- **Modifying [`DEFERRED_META_KEYS`][base] entries other than `"orderset_class"`.** Out of scope — this card promotes only `"orderset_class"`; the three siblings (`"aggregate_class"`, `"fields_class"`, `"search_fields"`) ship under their own cards.

## Definition of done

The card is complete when all of the following are true:

1. [`docs/spec-028-orders-0_0_8.md`][spec-028] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-028-orders-0_0_8-terms.csv`][spec-028-terms] anchoring every project-specific term used in the spec body to the matching [`docs/GLOSSARY.md`][glossary] heading (per [`docs/SPECS/NEXT.md`][next] Step 7).
2. [`django_strawberry_framework/orders/`][orders] ships as a subpackage with `__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface). The subpackage's `__init__.py` re-exports `OrderSet`, `RelatedOrder`, `Ordering`, `order_input_type`; the top-level package's `__all__` is unchanged.
3. `base.py` ships `RelatedOrder` (port of the cookbook's `BaseRelatedOrder`). The shared `LazyRelatedClassMixin` is reused from [`django_strawberry_framework/filters/base.py::LazyRelatedClassMixin`][filters-base] via sibling import; NOT duplicated.
4. `sets.py` ships `OrderSetMetaclass` and `OrderSet` per Layers 3 + 4 of [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6). `OrderSet` carries: (a) `_owner_definition: DjangoTypeDefinition | None` slot bound at finalizer phase 2.5; (b) **the resolver-facing classmethod pair `apply_sync(input_value, queryset, info) -> QuerySet` and `apply_async(input_value, queryset, info) -> Awaitable[QuerySet]`** per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer); the apply pipeline normalizes a Strawberry input dataclass via the cookbook's `get_flat_orders` algorithm into a flat list of `(field_path, Ordering)` tuples, extracts the request from `info.context.request` with an `HttpRequest` fallback, runs `check_permissions` with **active-input-only scope** (gates fire only for fields present in the normalized input), applies `queryset.order_by(*OrderBy_expressions)` where each expression is `Ordering.resolve(field_path)`, and returns the ordered queryset; (c) **NO `apply(...)` dispatcher** (dropped per H1 of [`docs/feedback.md`][feedback] rev1 — the filter side's `apply` exists for sync-misuse detection that the order side never triggers; symmetric dead weight is not shipped); (d) `get_fields` override for the `Meta.fields = "__all__"` shorthand (every concrete model field, excluding relations); (e) `Meta.model`, `Meta.fields`, `check_permissions`, and the cookbook's `get_flat_orders` recursive parser.
5. `factories.py` ships `OrderArgumentsFactory` (Layer 5 BFS, deriving input field types from the resolved fields on `orderset_cls.get_fields()`). Leaf scalar fields land as `Ordering | None`; `RelatedOrder` fields land as `Annotated["<Target>OrderInputType", strawberry.lazy(...)] | None`. `_dynamic_orderset_cache` is **NOT** shipped (Layer 6 deferred per [Decision 12](#decision-12--layer-6-and-distinct-on-deferred-to-009)).
6. `inputs.py` IS the input-class namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle): order input classes are materialized as real module globals of `django_strawberry_framework.orders.inputs` via `materialize_input_class(name, cls)` (idempotent for `(name, orderset_class)` pairs; raises [`ConfigurationError`][glossary-configurationerror] on name collision against a different orderset). The module ships the `Ordering` enum, `materialize_input_class`, `clear_order_input_namespace`, `_materialized_names` (private ledger), plus `_build_input_fields`, `convert_order_field_to_input_annotation(model_field, owner_definition)`, and `normalize_input_value(order_set_class, raw_value)`.
7. `orders/__init__.py` re-exports `order_input_type` per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper): consumers call `order_input_type(BranchOrder)` on a resolver signature and get back `Annotated["BranchOrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]`. The helper validates eagerly (`TypeError` for non-`OrderSet` arguments) AND records the OrderSet into `_helper_referenced_ordersets` so the finalizer can validate orphans at finalize time.
8. [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] grows an `orderset_class: type | None = None` slot, populated by `DjangoType.__init_subclass__` from `Meta.orderset_class`.
9. [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] no longer contains `"orderset_class"`; [`ALLOWED_META_KEYS`][base] contains `"orderset_class"`; `_validate_meta` validates `Meta.orderset_class` is an `OrderSet` subclass and raises [`ConfigurationError`][glossary-configurationerror] otherwise (via a new `_validate_orderset_class` helper mirroring the shipped `_validate_filterset_class` at [`django_strawberry_framework/types/base.py:72-95`][base]). **The new helper MUST use a local in-function `from ..orders.sets import OrderSet` import** — NOT a top-of-file import — to dodge the `types → orders → types` module-load cycle (the filter side's `_validate_filterset_class` body at [`types/base.py:88`][base] calls this out explicitly; the order side has the same cycle for the same reason because `orders.sets` imports `types.relay` which imports `types.base`). Per N3 of [`docs/feedback.md`][feedback] rev1, the validation runs at `_validate_meta` time — well after both modules have completed module load — so the local import resolves cheaply with no runtime penalty.
10. [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] grows the phase-2.5 order-binding pass per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering): `_bind_ordersets()` runs four ordered subpasses **(1) bind owners, (2) expand fields, (3) orphan-validate against `_helper_referenced_ordersets`, (4) materialize input classes** — matching the shipped `_bind_filtersets()` implementation at [`django_strawberry_framework/types/finalizer.py::_bind_filtersets`][finalizer] verbatim (NOT the inverted subpasses 3-and-4 prescribed by spec-027 rev8 H1 — per B1 of `docs/feedback.md` rev1, the shipped code is the authoritative shape and the spec's prior prescription was an inherited bug). Immediately after the shipped `_bind_filtersets()`. `registry.clear()` invokes `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` so the model-to-`DjangoType` clear, the filter-input clear, the order-input clear, and the orphan-tracking clears share one entry point.
11. `tests/orders/` (new tree) carries five mirror files (`__init__.py`, `test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`) plus `test_finalizer.py` and `test_composition.py` (Slice 6) per the [Test plan](#test-plan); each file covers what its mirror source file ships.
12. [`tests/types/test_base.py`][test-types] grows the `Meta.orderset_class` promotion test per the [Test plan](#test-plan).
13. [`examples/fakeshop/apps/library/`][fakeshop-library] ships `orders.py` (new) carrying `BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder` (same-module `RelatedOrder("ShelfOrder")` references) AND `orders_genre.py` (new) carrying `GenreOrder` (the cross-module fixture so `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` exercises the Layer-2 absolute-import-path branch).
14. [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] grows `Meta.orderset_class = orders.BranchOrder` (and the matching key on `ShelfType` / `BookType` / `LoanType` / `PatronType` / `GenreType`) on the corresponding `DjangoType` classes; root resolvers annotate `order_by:` via `order_input_type(orders.<Name>Order)` per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper) and call the resolved orderset's `apply_sync(order_by_value, queryset, info)` classmethod AFTER calling `<OwnerType>.get_queryset(queryset, info)` and optionally `<TypeName>Filter.apply_sync(filter, queryset, info)`.
15. [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows **exactly 13** live `/graphql/` HTTP tests per the [Test plan](#test-plan) (the rev1 count of 10 expanded by M2 / M5 / M6 / M7 of [`docs/feedback.md`][feedback] rev1 — flat-shorthand path, split-pair active-input-only permission tests, empty-list no-op, null-direction no-op).
16. [`docs/GLOSSARY.md`][glossary] flips [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], and [`Meta.orderset_class`][glossary-metaorderset_class] from `planned for 0.0.8` to `shipped (0.0.8)`; adds a new `## order_input_type` entry per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper); adds a new `## Ordering` entry per [Decision 5](#decision-5--ordering-enum-and-argument-shape); updates entry bodies; updates the [Index][glossary-index] table for all five entries; lists `OrderSet` / `RelatedOrder` / `order_input_type` / `Ordering` under the Ordering category of the [Browse by category][glossary] block.
17. [`docs/spec-028-orders-0_0_8-terms.csv`][spec-028-terms] anchors every project-specific term in the spec body to its [`docs/GLOSSARY.md`][glossary] heading; running [`uv run python scripts/check_spec_glossary.py --spec docs/spec-028-orders-0_0_8.md`][check-spec-glossary] reports `OK: <N> terms`.
18. [`docs/TREE.md`][tree] flips the `orders/` subpackage entry from `[alpha]` to on-disk; the mirror `tests/orders/` tree is enumerated; "Test layout going forward" reflects the new tree.
19. [`docs/README.md`][docs-readme] moves order symbols from "Coming in `0.1.0`" to "Shipped today" in the same Slice 5 commit that lands the version bump.
20. [`README.md`][readme] adds `OrderSet` / `RelatedOrder` / `order_input_type` / `Ordering` to the shipped-symbol bullet list.
21. [`TODAY.md`][today] extends the shipped-capabilities and fakeshop sections.
22. [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.8` (moved from `WIP-ALPHA-028-0.0.8` in Slice 5) with the past-tense body in [Doc updates](#doc-updates); the `Definition of done` bullet 1 points at the structured spec filename.
23. [`CHANGELOG.md`][changelog] `[Unreleased]` block accumulates the Ordering subsystem's `### Added` and `### Changed` bullets alongside the Filtering subsystem's bullets from `DONE-027-0.0.8`'s Slice 5; the same Slice 5 commit then promotes `[Unreleased]` to `[0.0.8] - <DATE>` per [Decision 10](#decision-10--joint-008-cut). The CHANGELOG-edit permission for this card comes from this DoD item per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed".
24. **Version bump quintet lands in this card's Slice 5** per [Decision 10](#decision-10--joint-008-cut) L5 contingency: (a) `pyproject.toml`'s `version = "0.0.7"` → `version = "0.0.8"`; (b) [`django_strawberry_framework/__init__.py`'s `__version__ = "0.0.7"`][package-init] → `__version__ = "0.0.8"`; (c) [`tests/base/test_init.py`'s pinned version assertion][test-base-init] (`"0.0.7"` → `"0.0.8"`); (d) the `[Unreleased]` → `[0.0.8] - <DATE>` promotion in `CHANGELOG.md` (the Slice-5 author substitutes the actual merge date for `<DATE>`); (e) a single Slice 5 commit. **Contingency check (deterministic per N6 of [`docs/feedback.md`][feedback] rev1):** Slice-5 author runs `grep -E 'WIP-ALPHA-[0-9]+-0\.0\.8' KANBAN.md`; if the only match is this card, lands the quintet; otherwise drops it (the new last `0.0.8` card owns the bump).
25. Top-level `__all__` is NOT widened (subpackage import path is the right grain per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface)).
26. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — verified by CI's `fail_under = 100` gate, not by the worker locally (per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits").
27. Slice 6 (the cross-card composition smoke test with the shipped Filtering subsystem) lands in this card's PR; no held-until-sibling clause.
28. Worker-local validation: `uv run ruff format .` passes and `uv run ruff check --fix .` passes. The worker does NOT run pytest as part of completing this card; pytest is invoked only by CI or by an explicit maintainer ask.

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
[feedback]: feedback.md
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-choice-enum-generation]: GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoconnection]: GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filter_input_type]: GLOSSARY.md#filter_input_type
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-get_child_queryset]: GLOSSARY.md#get_child_queryset
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-index]: GLOSSARY.md#index
[glossary-metaaggregate_class]: GLOSSARY.md#metaaggregate_class
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaoptimizer-hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-optimizerhint]: GLOSSARY.md#optimizerhint
[glossary-order_input_type]: GLOSSARY.md#order_input_type
[glossary-ordering]: GLOSSARY.md#ordering
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-public-exports]: GLOSSARY.md#public-exports
[glossary-queryset-diffing]: GLOSSARY.md#queryset-diffing
[glossary-relatedaggregate]: GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: GLOSSARY.md#relatedfilter
[glossary-relatedorder]: GLOSSARY.md#relatedorder
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-schema-export-management-command]: GLOSSARY.md#schema-export-management-command
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary]: GLOSSARY.md
[spec-028-terms]: spec-028-orders-0_0_8-terms.csv
[spec-028]: spec-028-orders-0_0_8.md
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[next-step-8]: SPECS/NEXT.md#step-8--archive-prior-specs-and-update-cross-references
[spec-015]: SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-018]: SPECS/spec-018-meta_primary-0_0_6.md
[spec-019]: SPECS/spec-019-consumer_overrides_scalar-0_0_6.md
[spec-020]: SPECS/spec-020-list_field-0_0_7.md
[spec-021]: SPECS/spec-021-apps-0_0_7.md
[spec-022]: SPECS/spec-022-export_schema-0_0_7.md
[spec-023]: SPECS/spec-023-multi_db-0_0_7.md
[spec-025]: SPECS/spec-025-scalar_map_helper-0_0_7.md
[spec-027]: SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../django_strawberry_framework/types/base.py
[definition]: ../django_strawberry_framework/types/definition.py
[filters-base]: ../django_strawberry_framework/filters/base.py
[filters-inputs]: ../django_strawberry_framework/filters/inputs.py
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[optimizer-plans]: ../django_strawberry_framework/optimizer/plans.py
[optimizer-walker]: ../django_strawberry_framework/optimizer/walker.py
[orders-inputs]: ../django_strawberry_framework/orders/inputs.py
[orders]: ../django_strawberry_framework/orders/
[package-init]: ../django_strawberry_framework/__init__.py
[registry]: ../django_strawberry_framework/registry.py
[registry-typeregistry]: ../django_strawberry_framework/registry.py
[relay]: ../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-orders]: ../tests/orders/
[test-orders-composition]: ../tests/orders/test_composition.py
[test-types]: ../tests/types/

<!-- examples/ -->
[fakeshop-library]: ../examples/fakeshop/apps/library/
[fakeshop-library-schema]: ../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-library-reload]: ../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-multi-db]: ../examples/fakeshop/test_query/test_multi_db.py

<!-- scripts/ -->
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
[strawberry-lazy]: https://strawberry.rocks
[upstream-cookbook]: https://github.com/devind-team/django-graphene-filters
[upstream-cookbook-filterset-factories]: https://github.com/devind-team/django-graphene-filters
[upstream-cookbook-mixins]: https://github.com/devind-team/django-graphene-filters
[upstream-cookbook-order-arguments-factory]: https://github.com/devind-team/django-graphene-filters
[upstream-cookbook-orders]: https://github.com/devind-team/django-graphene-filters
[upstream-cookbook-orderset]: https://github.com/devind-team/django-graphene-filters
[upstream-graphene-filter-fields]: https://github.com/graphql-python/graphene-django
[upstream-strawberry-ordering]: https://github.com/strawberry-graphql/strawberry-django
