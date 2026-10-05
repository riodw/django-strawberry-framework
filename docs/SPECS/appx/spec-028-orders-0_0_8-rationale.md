# Rationale companion: spec-028 (Ordering subsystem)

This file carries each Decision's justification and the alternatives it rejected for [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028]; the spec carries the contract.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-028-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<X_Y_Z>.md` filename pinned in [`docs/SPECS/NEXT.md`][next] bakes the card number and the target release into the name, so the spec sorts and resolves beside every other numbered spec.
- The topic slug `orders` matches the [`django_strawberry_framework/orders/`][orders] subpackage, the cookbook's `orders.py`, and the filter side's `filters` slug.

### Alternatives considered (and rejected)

- **Use the card body's `docs/spec-orders.md` verbatim.** Rejected: it breaks the structured-filename convention and puts an unnumbered spec in a numbered corpus.
- **Longer topic slug `ordering_subsystem`** (the card title). Rejected: `orders` already names the subject, matches the subpackage, and keeps the sibling set families (`filters`, `orders`) named symmetrically.

## Decision 2 — Subpackage layout and public export surface

Spec: [Decision 2 — Subpackage layout and public export surface][spec-028-d2].

### Justification

- The surface (six `__all__` names plus the advanced and internal symbols the three-tier contract lists) is too large for one legible module, and the five-file layout is the filter subsystem's, so both set families read as one shape.
- `RelatedOrder` reaches the Layer-2 resolver and the target-binding plumbing (`_bind_owner` / `_resolved_target` / `_set_target`) through [`django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`][sets-mixins], shared with `RelatedFilter`. One implementation means a resolution fix lands for both families at once; a copy under `orders/base.py` would silently bifurcate the behavior.
- The order-side names in `orders/inputs.py` (`FieldSpec`, `build_input_class`, `_input_type_name_for`, `_iter_orderset_subclasses`, `materialize_input_class`, `clear_order_input_namespace`) are aliases and thin wrappers over [`django_strawberry_framework/utils/inputs.py`][utils-inputs] because they ARE the addressable contract: [Decision 9][spec-028-d9]'s lifecycle clauses, `registry.clear()`, and the test suite reach the subsystem through them, while one implementation serves both families.
- `OrderSet` ships no instance-method `check_permissions`: the inherited classmethod `_run_permission_checks` is the single entry point, so the active-input-only scope cannot be bypassed through a second spelling, and no instance has to carry per-request input state just so an alias can forward to the classmethod.
- `_helper_referenced_ordersets` lives in `orders/__init__.py` beside its only writer, the consumer helper. It clears through its own `register_subsystem_clear` row because it tracks consumer resolver-annotation references, a lifecycle unrelated to the namespace ledger in `orders/inputs.py`.
- Re-exporting from the subpackage rather than the top-level package keeps the opt-in sidecar surface out of the top-level `__all__`, which every consumer (including optimizer-only ones) imports.

### Alternatives considered (and rejected)

- **Flat `django_strawberry_framework/orders.py` single-file module.** Rejected: the surface is too large to review in one file, and it breaks the one-shape symmetry with `filters/`.
- **Top-level re-export (`from django_strawberry_framework import OrderSet`).** Rejected: ordering is opt-in; widening the top-level `__all__` for every consumer adds churn for the ones who never order.
- **Reach `LazyRelatedClassMixin` through `filters/base.py`.** Rejected: building an orderset would load the whole filter subsystem and couple the two families' import graphs; the neutral `sets_mixins.py` module keeps them independent.

## Decision 3 — Five-layer port plus a deferred Layer 6

Spec: [Decision 3 — Five-layer port plus a deferred Layer 6][spec-028-d3].

### Justification

- The cookbook's five-layer architecture is the working reference per [`START.md`][start]; reinventing it buys nothing.
- Layer 5 reuses the filter subsystem's Strawberry adaptation, so the lazy-resolution plus module-globals materialization contract is one shape, not two.
- Layers 2-5 run on the shared substrate ([`sets_mixins.py::collect_related_declarations`][sets-mixins], [`sets_mixins.py::expanded_once`][sets-mixins] / [`sets_mixins.py::should_cache_expansion`][sets-mixins], [`utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs]): the cycle guard, the two-condition cache write, and the BFS each exist once for both families. `get_fields()` stores `RelatedOrder` instances without resolving them, so expansion never re-enters another orderset and cannot cycle.
- The factory caches built classes but does not write module globals; the finalizer's phase-2.5 subpass 4 materializes them. Materialization's ordering relative to `strawberry.Schema(...)` is load-bearing ([Decision 6][spec-028-d6]), and a factory that wrote globals as a construction side effect would make that ordering depend on where a caller instantiated it.
- `Meta.fields = "__all__"` tests `getattr(f, "column", None) is not None and not getattr(f, "many_to_many", False)` rather than the cookbook's `hasattr(f, "column")`: a `ManyToManyField`, a `GenericRelation`, and a `GenericForeignKey` all expose `column = None`, so `hasattr` would admit them as order leaves, producing a fan-out join (M2M) or an `OrderBy` against a field with no database column.
- Layer 6 is out because no consumer surface needs an implicit `OrderSet`: every field that takes ordering reads a declared `Meta.orderset_class` ([Decision 12][spec-028-d12]).

### Alternatives considered (and rejected)

- **Design Layer 6 fresh, mirroring the cookbook's filter-side `_dynamic_filterset_cache`.** Rejected: no consumer surface needs it; the connection and list fields read the declared sidecar.
- **Duplicate `LazyRelatedClassMixin` into `orders/base.py`.** Rejected per [Decision 2][spec-028-d2]: two copies of the resolution algorithm drift.
- **Borrow the cookbook's four-member `OrderDirection`** (`ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT`) instead of the six-member `Ordering`. Rejected per [Decision 5][spec-028-d5]: the `_DISTINCT` members conflate a direction with a partition, the fan-out they address is prevented by row-preserving aggregate ordering ([Decision 12][spec-028-d12]), and NULLS positioning is the more broadly useful leaf vocabulary.

## Decision 4 — Upstream-primitives parity floor

Spec: [Decision 4 — Upstream-primitives parity floor][spec-028-d4].

### Justification

- The floor covers what both reference libraries let a schema author express: per-field direction including NULLS positioning, cross-relation ordering, and multi-field priority. Dropping below it would leave queries the upstreams accept inexpressible.
- What only one upstream ships (the cookbook's DISTINCT ON modifiers, strawberry-django's `OrderSequence` and decorator surfaces) is optional under [`START.md`][start]'s parity test, and each has a reason to stay out (Decisions 5 and 12, and the `Meta`-driven shape).

### Alternatives considered (and rejected)

- **Ship `OrderSequence` for explicit tie-breaker control.** Rejected per [Decision 5][spec-028-d5]: the list's element order already is the tie-breaker.
- **Ship DISTINCT ON via a port of the cookbook's `apply_distinct`.** Rejected per [Decision 12][spec-028-d12]: row-preserving aggregate ordering prevents the to-many fan-out it addresses without a PostgreSQL-native partitioning surface.
- **Ship Layer 6 auto-generation.** Rejected: no consumer surface needs it.

## Decision 5 — `Ordering` enum and argument shape

Spec: [Decision 5 — `Ordering` enum and argument shape][spec-028-d5].

### Justification

- NULLS positioning applies on every backend Django supports, while the cookbook's DISTINCT modifiers carry a PostgreSQL-native mental model (its non-PostgreSQL path is a `Window` emulation, `_apply_distinct_emulated`).
- One list-shaped `orderBy:` argument suffices: a one-element list produces the same SQL as a singular argument, so a second argument shape would be redundant.
- No argument-name constant exists: Strawberry derives the `orderBy` GraphQL argument from the resolver's `order_by` parameter by auto-camel-case, so a constant would have no reader.
- `Ordering.resolve` returns an `OrderBy` expression (`F(path).asc/desc(nulls_first=..., nulls_last=...)`) because the bare-string `-name` form cannot express NULLS positioning. `get_flat_orders` returns `(path, direction)` pairs and [`orders/sets.py::OrderSet._resolve_order_expressions`][orders-sets] is the one call site that converts them, so the expression semantics live in one place.
- `is_ascending` is a property anchored on the member-name prefix because it has two consumers, `resolve` (`.asc()` vs `.desc()`) and `_resolve_order_expressions` (`Min` vs `Max` for a to-many term). A second copy could drift, and drift orders a to-many term by the wrong end of its child range with no error; a substring test would misclassify any member embedding `ASC` after its direction.

### Alternatives considered (and rejected)

- **Ship the cookbook's four-member `OrderDirection`** (`ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT`). Rejected: the `_DISTINCT` members are not ported ([Decision 12][spec-028-d12]), and NULLS positioning is more broadly useful.
- **Ship both a singular `order:` and a list `ordering:` argument** (strawberry-django's `ORDER_ARG` / `ORDERING_ARG` pair). Rejected: redundant; a one-element list is the same SQL.
- **Ship `OrderSequence` for explicit tie-breaker control.** Rejected: the list's element order is the tie-breaker, and positional control is more discoverable than a separate descriptor field.
- **Use bare-string ORM orderings (`["-name", "shelf__code"]`)** instead of `OrderBy` expressions. Rejected: bare strings cannot express NULLS positioning.

## Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering

Spec: [Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering][spec-028-d6].

### Justification

- `_bind_ordersets` and `_bind_filtersets` both configure one driver, [`django_strawberry_framework/types/finalizer.py::_bind_sidecar_sets`][finalizer], so the subpass order is structurally identical for both families instead of two implementations claimed to agree; a subpass-order fix cannot land on one side only.
- Every owner is bound before any expansion runs. The filter family's expansion reads the bound owner; for orders the value is that every owner-model compatibility and multi-owner agreement check rejects a mis-wiring before any expansion or materialization happens.
- The owner-model compatibility check is non-optional: without it a `BookOrder` wired onto `BranchType` builds a valid-looking input and applies `Book` paths to a `Branch` queryset, failing as a late Django `FieldError` at query time instead of a finalize-time `ConfigurationError` naming the mis-wiring.
- Orphan validation runs before materialization because materializing first would leave half-populated `_materialized_names` and `OrderArgumentsFactory.input_object_types` entries whenever the orphan check raises; the next `finalize_django_types()` after the consumer fixes the orphan would then skip rebuilds or raise a spurious name collision. Validating first keeps both ledgers empty until every gate passes.
- The order spec passes `post_expand_audit=None`: the filter-only audit exists because a related filter branch scopes through the target type's `get_queryset` and consults Relay shape, while an order hop whose target model no type registers is simply unscoped ([Decision 8][spec-028-d8] step 4: it hides nothing), so there is no unregistered target to refuse, and ordering never consults Relay shape.
- `registry.clear()` replays the order-side clears, so the [`examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests`][fakeshop-test-conftest] reload fixture works unchanged.

### Alternatives considered (and rejected)

- **Single-subpass binding** (one loop calling bind, expand, and materialize per type). Rejected: the filter family's expansion needs every owner bound first, and an owner check failing on a later type would leave earlier types half-materialized.
- **Bind ordersets at type-creation time (`DjangoType.__init_subclass__`).** Rejected: relation targets may not be registered yet (definition-order independence); finalize is the first point where every type is known.
- **Materialize before orphan validation.** Rejected: it leaves stale ledger entries on every orphan failure, so the retry after the fix misfires.
- **Skip orphan validation.** Rejected: an orphan `OrderInput[StandaloneOrder]` reference would surface as a `LazyType.resolve_type` `KeyError` at `strawberry.Schema(...)` time, far from the resolver that wrote it; failing at finalize names the bug at the right place.

## Decision 7 — `Meta.orderset_class` promotion gate

Spec: [Decision 7 — `Meta.orderset_class` promotion gate][spec-028-d7].

### Justification

- The [Cross-subsystem invariants][glossary-cross-subsystem-invariants] rule ("Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end.") applies to every Layer-3 sidecar.
- Accepting the key while no-oping on it is the worst of both: consumers cannot tell whether their order declaration does anything.
- `_validate_meta` raises for any key in [`DEFERRED_META_KEYS`][base] and for any key in neither set (the typo guard), so a key sits in `ALLOWED_META_KEYS` only once its subsystem applies it.

### Alternatives considered (and rejected)

- **Accept the key before the finalizer binding applies it.** Rejected: silently accepting a key whose effect does not exist hides a broken declaration.
- **Keep the key deferred until `DjangoConnectionField` consumes it.** Rejected: root-list resolvers apply `OrderSet.apply_sync(...)` themselves, so the key has an end-to-end consumer without the connection field.

## Decision 8 — Cooperation with filtering, `get_queryset`, and the optimizer

Spec: [Decision 8 — Cooperation with filtering, `get_queryset`, and the optimizer][spec-028-d8].

### Justification

- The apply pipeline keeps the filter side's skeleton (sync/async split, active-input-only permission scope, request resolution through [`utils/permissions.py::request_from_info`][utils-permissions], `from graphql import GraphQLError`), and the permission walk is single-sited on [`sets_mixins.py::ActiveInputPermissionMixin`][sets-mixins], so both families gate identically.
- The order pipeline is simpler than the filter one because the cookbook's ordering has no operator bag (`and_` / `or_` / `not_`), no form validation, and no related-queryset constraint (its `RelatedOrder` takes only `orderset` and `field_name`).
- Filter first, then order, is the readable resolver shape: `WHERE` narrows the rows, `ORDER BY` arranges them. The SQL is the same either way.
- Paths resolve against `queryset.model`, not `Meta.model`: `Meta.model` may be absent (a related-only `OrderSet`) or name a base model while the caller applies the set to a concrete descendant with extra relations. Rooting at class metadata would miss a concrete to-many path and reinstate the fan-out join the aggregate exists to prevent.
- A to-many term orders by a `Min` / `Max` aggregate so the parent row is never multiplied ([Decision 12][spec-028-d12]); every path is pre-validated through [`utils/relations.py::classify_path`][utils-relations] so a bad path raises `ConfigurationError` naming it rather than a Django `FieldError` at execution.
- An `async def check_<field>_permission` is rejected with `SyncMisuseError` rather than awaited or passed through: the pipeline is synchronous on both surfaces, and an un-awaited coroutine is truthy, so an intended denial would become a silent allow, an authorization bypass that fails toward granting access.
- `apply_async` dispatches the permission pass through [`utils/querysets.py::run_in_one_sync_boundary`][utils-querysets], the package's one-boundary primitive (one `thread_sensitive=True` worker per resolution) shared by every async surface, so no subsystem tunes its own boundary.
- A related order term reads only the related rows its target type lets the viewer see, the rule the filter side follows ([spec-027 Decision 8][spec-027-d8] step 3): the order is not projected, but a parent's position is still data, and ordering by a hidden row's column would rank that row's value against every visible one. A hidden row sorting as a missing one is the one reading under which no order input tells hidden apart from absent.
- The visibility test is a correlated `EXISTS` on the primary key of the row the term's own join already reached, not the filter side's parent-level `related_rows_exist`: an order value belongs to one joined row, and a to-many aggregate must drop exactly the hidden children ("the parent reaches some visible child" would let a hidden child's value set the parent's `Min`). Correlating to the existing join adds no join and leaves `GROUP BY` and the parent's `DISTINCT` as they were.
- A hop whose target type does not override `get_queryset` stays unwrapped, so an order over unscoped relations keeps its plain column SQL and keeps qualifying for `Meta.cursor_field` connections.
- A to-many term aggregates the same nested `CASE` value a to-one term orders by rather than passing the tests as `Min(..., filter=Q(...))`: `Min` / `Max` skip a `NULL` exactly as a `FILTER` drops the row, and a `CASE` whose conditions are the tests themselves stays in forms the `DjangoListField` offset guard already reads (`Case`, `When`, an approved aggregate), where a resolved `filter=` becomes a `WhereNode` of `Exact(<test>, True)` lookups the guard cannot certify.
- The test is a distinct exact type, `utils/querysets.py::VisibleRowExists`, because the guard and the keyset order state must tell the framework's visibility test from a consumer's `Exists`, whose subquery may hold anything. It defines nothing, so admitting it by identity in the seal admits no code that is not Django's `Exists`.

### Alternatives considered (and rejected)

- **Accept the position side channel and leave the parent's `check_<branch>_permission` gate as the defense.** Rejected: the gate is opt-in per branch and per spelling, a `Meta.fields` path through an undeclared relation has no branch to gate, and the position bounds the hidden value between its visible neighbours (a low-cardinality column reveals it outright).
- **Order by a correlated `Subquery` of the visible target rows' value.** Rejected: a to-many term would lose the shared `Min` / `Max` aggregate path, and the `DjangoListField` offset guard cannot certify a `Subquery`'s inner query.
- **Apply the order before the filter** (`get_queryset` → `Order.apply_*` → `Filter.apply_*`). Rejected: identical SQL, less legible resolver.
- **Skip the per-field `check_<field>_permission` gates.** Rejected: the cookbook's `AdvancedOrderSet.check_permissions` is a real consumer surface (e.g. order by a sensitive column for staff only), and active-input-only scope keeps it low-noise.
- **Use bare-string `order_by` arguments** instead of `OrderBy` expressions. Rejected per [Decision 5][spec-028-d5]: bare strings cannot express NULLS positioning.

## Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle

Spec: [Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle][spec-028-d9].

### Justification

- Generated input classes are real module globals because Strawberry's `LazyType.resolve_type` imports the named module and reads `module.__dict__[type_name]`; it cannot reach into a sidecar dict.
- Each set family owns its own module namespace (`orders.inputs`, `filters.inputs`); folding them into the `TypeRegistry` would mix string-keyed input classes with model-keyed `DjangoType` entries and weaken the registry's contract.
- Materialized globals stay parked across `clear_order_input_namespace()`: the next finalize overwrites each in place, while deleting them would break a `strawberry.lazy(...)` reference held by a consumer module the reload fixture did not reload.
- Teardown goes through [`django_strawberry_framework/registry.py::register_subsystem_clear`][registry] rather than `registry.py` importing each subsystem's clear. A rename breaks at the owner's own import instead of leaving a ledger silently uncleared; an unimported subsystem registers nothing, so no `ImportError` guard is needed; and each phase is its own row, so no link in a chain can short-circuit a later one and new families need no `registry.py` edit.
- `before_bind=True` on the namespace row marks an emitted-state reset the finalizer replays before every bind pass, so a re-call after a fixed finalize failure rebuilds instead of meeting a spurious name collision. The consumer-helper ledger row omits it: helper references are recorded once, when resolver annotations evaluate, and a pre-bind reset would erase the records the orphan check reads.

### Alternatives considered (and rejected)

- **A private `_input_type_registry: dict[str, type]` in `orders.inputs`.** Rejected: `LazyType.resolve_type` reads `module.__dict__` and cannot traverse a dict.
- **One dict shared by the filter and order families.** Rejected: the namespaces are disjoint by module path; sharing would force one module path on both or a wrapper module re-exporting both families' classes.
- **Leave `clear_order_input_namespace()` out of `registry.clear()`.** Rejected: test-fixture reloads would leak generated state between runs.

## Decision 10 — Version bumps are maintainer-commanded

Spec: [Decision 10 — Version bumps are maintainer-commanded][spec-028-d10].

### Justification

- The release is single-sourced in [`django_strawberry_framework/__init__.py::__version__`][package-init]; bumping it, like promoting a `CHANGELOG.md` heading, is a release action, so a feature card's checklist never mutates release state.
- The rule is about who may bump, which does not change, so the Decision asserts nothing about the current contents of `CHANGELOG.md` or the version literal.

### Alternatives considered (and rejected)

- **Bump implicitly when the card lands.** Rejected: it makes a feature-card checklist mutate release state.
- **A deterministic "the last card of the patch line owns the bump" rule.** Rejected: still an implicit bump; the only trigger is the maintainer's explicit command.

## Decision 11 — `order_input_type(OrderSet)` consumer helper

Spec: [Decision 11 — `order_input_type(OrderSet)` consumer helper][spec-028-d11].

### Justification

- The helper is deliberately the same shape as `filter_input_type`, and both bodies are one function, [`utils/inputs.py::build_lazy_input_annotation`][utils-inputs]. The families differ only in the arguments they pass; the identical parts (eager validation, the orphan-ledger write, the `ForwardRef` form) are the subtle ones, and two copies would be two places to fix a bug.
- Eager `TypeError` validation catches misuse at the resolver signature instead of as a cryptic schema-build error.
- The helper returns the element type; resolvers wrap it as `list[...] | None` because `orderBy:` is a list on the wire.
- `OrderInput[MyOrder]` exists beside the call because a call is not a valid type expression: the generic spelling is what a type checker accepts in an annotation, and its `OrderSet` bound rejects a non-`OrderSet` statically.
- Recording every helper-referenced set lets finalize reject an orphan with an actionable message instead of a `LazyType.resolve_type` `KeyError` at `strawberry.Schema(...)` time.

### Alternatives considered (and rejected)

- **No helper; consumers write `Annotated[...]` themselves.** Rejected: ties consumer code to the package's internal module path and skips validation and orphan tracking.
- **Return the generated input class directly.** Rejected: the class does not exist at module-load time; `finalize_django_types()` materializes it later, and running the finalizer eagerly would break definition-order independence.
- **A method on `OrderSet` (`MyOrder.input_type()`).** Rejected: viable, but it adds class surface to every `OrderSet` for one call site per resolver; the module-level function is the smaller import and matches the filter side.
- **Rely only on field-level wiring** (`DjangoConnectionField` / `DjangoListField` build `orderBy:` from `Meta.orderset_class`). Rejected: a hand-written `@strawberry.field` resolver, like the fakeshop root-list resolvers, still needs an annotation for its own `order_by` parameter.

## Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface

Spec: [Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface][spec-028-d12].

### Justification

- Layer 6 would serve a caller that does not exist; the explicit declaration covers every consumer, and a second, implicit way to acquire an `OrderSet` is surface without demand.
- The row multiplication that motivates DISTINCT ON is solved by the aggregate ordering without a PostgreSQL-native construct, so no backend needs the cookbook's `Window` emulation.
- `NULLS_FIRST` / `NULLS_LAST` positioning is the vocabulary a leaf-field direction enum needs, and six members is already at the edge of legibility.

### Alternatives considered (and rejected)

- **Ship Layer 6 auto-generation mirroring the cookbook's [`django_graphene_filters/filterset_factories.py::_dynamic_filterset_cache`][upstream-cookbook-filterset-factories].** Rejected: no consumer needs it, and it would put an implicit way to acquire an `OrderSet` beside the explicit declaration.
- **Ship the cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` plus an [`apply_distinct`][upstream-cookbook-orderset] port.** Rejected: the members conflate a direction with a partition, and the row multiplication they address is already prevented.
- **A separate `Meta.distinct = ("category",)` declaration with a `distinct_on:` argument.** Rejected: it buys a PostgreSQL-native partitioning surface for a problem the aggregate ordering already solves, and every `Meta` key is permanent public surface.

## Decision 13 — Live HTTP coverage strategy

Spec: [Decision 13 — Live HTTP coverage strategy][spec-028-d13].

### Justification

- Same strategy as the filter side ([`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 12): live HTTP wherever a real query reaches the line, package tests for the rest.
- The live path exercises the ORM cooperation (`order_by(...)` and the to-many aggregate against `select_related` / `prefetch_related`) that an in-process test cannot capture without heavy SQL-shape setup.
- `tests/orders/` reaches what a consumer query cannot: lazy-resolution failure paths, `Ordering.resolve` expressions, the nested `normalize_input_value` walk, and the `ConfigurationError` surface. Mechanics shared with the filter family are pinned in the tree that owns them (`tests/utils/test_permissions.py`, `tests/test_sets_mixins.py`), so one test proves a shared contract for both families.

### Alternatives considered (and rejected)

- **Skip live HTTP coverage; cover everything in `tests/orders/`.** Rejected by the coverage-priority rule in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]: a line reachable from a real query is covered live.
- **Cover everything live; skip package tests.** Rejected: cycle detection and error-surface paths are not reachable through normal consumer queries.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-027-d8]: ../spec-027-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028-d10]: ../spec-028-orders-0_0_8.md#decision-10--version-bumps-are-maintainer-commanded
[spec-028-d11]: ../spec-028-orders-0_0_8.md#decision-11--order_input_typeorderset-consumer-helper
[spec-028-d12]: ../spec-028-orders-0_0_8.md#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface
[spec-028-d13]: ../spec-028-orders-0_0_8.md#decision-13--live-http-coverage-strategy
[spec-028-d1]: ../spec-028-orders-0_0_8.md#decision-1--spec-filename-and-canonical-naming
[spec-028-d2]: ../spec-028-orders-0_0_8.md#decision-2--subpackage-layout-and-public-export-surface
[spec-028-d3]: ../spec-028-orders-0_0_8.md#decision-3--five-layer-port-plus-a-deferred-layer-6
[spec-028-d4]: ../spec-028-orders-0_0_8.md#decision-4--upstream-primitives-parity-floor
[spec-028-d5]: ../spec-028-orders-0_0_8.md#decision-5--ordering-enum-and-argument-shape
[spec-028-d6]: ../spec-028-orders-0_0_8.md#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering
[spec-028-d7]: ../spec-028-orders-0_0_8.md#decision-7--metaorderset_class-promotion-gate
[spec-028-d8]: ../spec-028-orders-0_0_8.md#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer
[spec-028-d9]: ../spec-028-orders-0_0_8.md#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle
[spec-028]: ../spec-028-orders-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../../django_strawberry_framework/types/base.py
[finalizer]: ../../../django_strawberry_framework/types/finalizer.py
[orders-sets]: ../../../django_strawberry_framework/orders/sets.py
[orders]: ../../../django_strawberry_framework/orders/
[package-init]: ../../../django_strawberry_framework/__init__.py
[registry]: ../../../django_strawberry_framework/registry.py
[sets-mixins]: ../../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-test-conftest]: ../../../examples/fakeshop/test_query/conftest.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-cookbook-filterset-factories]: https://github.com/riodw/django-graphene-filters
[upstream-cookbook-orderset]: https://github.com/riodw/django-graphene-filters
