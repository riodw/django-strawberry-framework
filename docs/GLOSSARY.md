# Glossary

Glossary of every public symbol, `Meta` key, configuration argument, and named behavior in `django-strawberry-framework`. Every entry below has a stable anchor — `#djangotype`, `#fk-id-elision`, `#metafilterset_class`, and so on — so this file is intended to be linked directly from documentation, code comments, example projects, and migration notes.

Companion files:

- [`../GOAL.md`][goal] — the pitch / vision and a complete `1.0.0`-shape walkthrough (the astronomy showcase).
- [`../TODAY.md`][today] — the current example-app usage snapshot.
- [`../KANBAN.md`][kanban] — per-card ship sequencing.
- [`../BACKLOG.md`][backlog] — strategic post-`1.0.0` differentiators.

## Status legend

- `shipped` — implemented, tested, available in the current package surface.
- `planned for X.Y.Z` — committed package direction, not implemented yet; tracked in [`../KANBAN.md`][kanban] against a target patch version.
- `deferred` — reserved for later design or blocked on another feature.
- `alpha constraint` — current behavior that works but is intentionally narrower than the eventual API.
- `post-1.0.0` — strategic differentiation tracked in [`../BACKLOG.md`][backlog], not on the roadmap to `1.0.0`.

Current package version: `0.0.13`. Alpha-quality — suitable for internal tools and prototypes, not production. The `1.0.0` release is the API-freeze boundary; after `1.0.0` ships, strict semantic versioning applies to every entry below.

## Public exports

Symbols re-exported from `django_strawberry_framework`:

- [`BigInt`](#bigint-scalar) — JSON-safe scalar for 64-bit integer fields.
- [`DjangoConnection`](#djangoconnection) — generic Relay connection return-type alias (`DjangoConnection[T]`).
- [`DjangoConnectionField`](#djangoconnectionfield) — Relay connection field factory over a Relay-Node-shaped `DjangoType`.
- [`DjangoFileType`](#djangofiletype) — structured read-output object for a `FileField` column (`name` / `path` / `size` / `url`).
- [`DjangoFormMutation`](#djangoformmutation) — plain `Form` mutation base (model-less sibling): `Meta.form_class`, pinned `ok` + `errors` payload, no object slot.
- [`DjangoImageType`](#djangoimagetype) — structured read-output object for an `ImageField` column (`DjangoFileType` fields plus `width` / `height`).
- [`DjangoListField`](#djangolistfield) — non-Relay `list[T]` factory function for root Query fields.
- [`DjangoModelFormMutation`](#djangomodelformmutation) — `ModelForm` mutation base subclassing `DjangoMutation`; returns the post-save object in the uniform `node` / `result` slot.
- [`DjangoModelPermission`](#djangomodelpermission) — default write-authorization class (Django `add` / `change` / `delete` model perms) for `Meta.permission_classes`.
- [`DjangoMutation`](#djangomutation) — model-driven create / update / delete mutation base configured through a nested `class Meta`.
- [`DjangoMutationField`](#djangomutationfield) — write-side field factory exposing a `DjangoMutation` on the schema's `Mutation` type.
- [`DjangoNodeField`](#djangonodefield) — root Relay `node(id:)` refetch field factory (bare interface and typed forms).
- [`DjangoNodesField`](#djangonodesfield) — root Relay `nodes(ids:)` batch refetch field factory.
- [`DjangoType`](#djangotype) — model-backed Strawberry type base class.
- [`DjangoOptimizerExtension`](#djangooptimizerextension) — Strawberry schema extension that does ORM optimization.
- [`FieldError`](#fielderror-envelope) — public typed validation-error type (`field` + `messages`) in the shared mutation-payload envelope.
- [`OptimizerHint`](#optimizerhint) — typed wrapper for per-relation optimizer overrides.
- [`SerializerMutation`](#serializermutation) — DRF `ModelSerializer` mutation base subclassing `DjangoMutation` (`Meta.serializer_class`); a lazy root export under the soft `djangorestframework` guard (resolved via `__getattr__`, not in `__all__` while DRF is soft).
- [`SyncMisuseError`](#syncmisuseerror) — typed marker for sync resolver paths that receive an async `get_queryset` coroutine.
- [`Upload`](#upload-scalar) — re-exported Strawberry built-in scalar for `FileField` / `ImageField` mutation inputs.
- [`apply_cascade_permissions`](#apply_cascade_permissions) — cascade a type's `get_queryset` visibility through its single-column forward FK / OneToOne edges (sync).
- [`aapply_cascade_permissions`](#apply_cascade_permissions) — async twin of `apply_cascade_permissions` (`sync_to_async` wrap); shares the entry.
- [`finalize_django_types`](#finalize_django_types) — synchronization point that resolves pending relations and applies `strawberry.type` decoration.
- [`strawberry_config`](#strawberry_config) — factory returning a `StrawberryConfig` pre-populated with the package's `scalar_map`.
- [`auto`](#auto-typed-annotations) — re-export from Strawberry for `auto`-typed field annotations (the declare-but-infer marker).
- `__version__` — package version string.

Symbols available from the `django_strawberry_framework.extensions` subpackage (opt-in schema extensions):

- [`DjangoDebugExtension`](#djangodebugextension) — off-by-default development extension that reports executed SQL and execution exceptions through `response.extensions.debug`.

Symbols available from the `django_strawberry_framework.testing` subpackage (consumer test utilities):

- [`TestClient`](#testclient) — sync GraphQL test client over `django.test.Client`: post an operation, decode it, and get a typed [`Response`](#testclient) carrying the raw `HttpResponse`.
- [`AsyncTestClient`](#testclient) — the async twin over `django.test.AsyncClient` (Django's in-process ASGI handler; no `asgi.py` required).
- [`Response`](#testclient) — the typed result dataclass (`errors` / `data` / `extensions` plus the raw `response`).
- [`GraphQLTestMixin`](#graphqltestcase) — the `graphene-django`-shaped unittest mixin (`self.query(...)` + `assertResponseNoErrors` / `assertResponseHasErrors`), delegating to [`TestClient`](#testclient).
- [`GraphQLTestCase`](#graphqltestcase) — `(GraphQLTestMixin, django.test.TestCase)`, the common concrete combination.
- [`GraphQLTransactionTestCase`](#graphqltestcase) — `(GraphQLTestMixin, django.test.TransactionTestCase)` for on-commit / real-commit flows.
- [`safe_wrap_connection_method`](#safe_wrap_connection_method) — cooperative wrap helper for monkey-patching `connections[alias]` methods without clobbering Django's `_DatabaseFailure` wrapper (the wrap-time half of the [Django Trac #37064 hardening](#django-trac-37064-hardening) defense-in-depth).
- `global_id_for` / `decode_global_id` — public Relay test helpers at the `django_strawberry_framework.testing.relay` submodule path (NOT re-exported from the `testing` root, by design); mint and decode the strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits. See [Relay Node integration](#relay-node-integration).


Symbols available from the `django_strawberry_framework.auth` submodule (the opt-in session-auth surface - deliberately NOT re-exported from the package root, so the opt-in stays structural and a consumer who skips auth never imports `django.contrib.auth` machinery):

- [`login_mutation`](#auth-mutations) / [`logout_mutation`](#auth-mutations) / [`register_mutation`](#auth-mutations) / [`current_user`](#auth-mutations) - the four session-auth field factories (see [Auth mutations](#auth-mutations)); each accepts `permission_classes=` with the explicit allow-any default.

_Note:_ The import path is clean by construction — the registration path uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload via the [`strawberry_config`](#strawberry_config) factory, so no `DeprecationWarning` is emitted.

## Index

Alphabetical lookup. Each row links to the entry; the status column reflects current availability.

| Entry | Status |
|---|---|
| [`AggregateSet`](#aggregateset) | planned for `0.1.3` |
| [`apply_cascade_permissions`](#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Async SQL-capture boundary](#async-sql-capture-boundary) | planned for `0.0.14` |
| [Auth mutations](#auth-mutations) | shipped (`0.0.13`) |
| [`BigInt` scalar](#bigint-scalar) | shipped (`0.0.6`) |
| [Bounded query-log rollover](#bounded-query-log-rollover) | planned for `0.0.14` |
| [Channels request adapter](#channels-request-adapter) | planned for `0.0.14` |
| [Choice enum generation](#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](#configurationerror) | shipped (`0.0.1`) |
| [Connection-aware optimizer planning](#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [Cookbook parity](#cookbook-parity) | planned through `1.0.0` |
| [Debug exception row](#debug-exception-row) | planned for `0.0.14` |
| [Debug payload availability](#debug-payload-availability) | planned for `0.0.14` |
| [Debug SQL row](#debug-sql-row) | planned for `0.0.14` |
| [Debug-toolbar middleware](#debug-toolbar-middleware) | planned for `0.0.14` |
| [Definition-order independence](#definition-order-independence) | shipped (`0.0.4`) |
| [Developer-only debug posture](#developer-only-debug-posture) | planned for `0.0.14` |
| [Django `AppConfig`](#django-appconfig) | shipped (`0.0.7`) |
| [Django debug-cursor capture](#django-debug-cursor-capture) | planned for `0.0.14` |
| [`DjangoConnection`](#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoConnectionField`](#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoDebugExtension`](#djangodebugextension) | planned for `0.0.14` |
| [`DjangoFileType`](#djangofiletype) | shipped (`0.0.11`) |
| [`DjangoFormMutation`](#djangoformmutation) | shipped (`0.0.12`) |
| [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) | planned for `0.0.14` |
| [`DjangoImageType`](#djangoimagetype) | shipped (`0.0.11`) |
| [`DjangoListField`](#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoModelFormMutation`](#djangomodelformmutation) | shipped (`0.0.12`) |
| [`DjangoModelPermission`](#djangomodelpermission) | shipped (`0.0.11`) |
| [`DjangoMutation`](#djangomutation) | shipped (`0.0.11`) |
| [`DjangoMutationField`](#djangomutationfield) | shipped (`0.0.11`) |
| [`DjangoNodeField`](#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoNodesField`](#djangonodesfield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](#djangotype) | shipped (`0.0.5`) |
| [Eviction-simulated absence](#eviction-simulated-absence) | shipped (`0.0.13`) |
| [`FieldError` envelope](#fielderror-envelope) | shipped (`0.0.11`) |
| [`FieldSet`](#fieldset) | planned for `0.1.1` |
| [`FilterSet`](#filterset) | shipped (`0.0.8`) |
| [`filter_input_type`](#filter_input_type) | shipped (`0.0.8`) |
| [`finalize_django_types`](#finalize_django_types) | shipped (`0.0.4`) |
| [FK-id elision](#fk-id-elision) | shipped (`0.0.3`) |
| [`get_child_queryset`](#get_child_queryset) | planned for `0.1.3` |
| [`get_queryset` visibility hook](#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Graphene debug migration](#graphene-debug-migration) | planned for `0.0.14` |
| [`GraphQLTestCase`](#graphqltestcase) | planned for `0.0.14` |
| [Hard dependency](#hard-dependency) | shipped |
| [Input type generation](#input-type-generation) | shipped (`0.0.11`) |
| [Joint version cut](#joint-version-cut) | shipped (`0.0.13`) |
| [Live-first coverage mandate](#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Masking-extension ordering](#masking-extension-ordering) | planned for `0.0.14` |
| [`Meta.aggregate_class`](#metaaggregate_class) | planned for `0.1.3` |
| [`Meta.choice_enum_names`](#metachoice_enum_names) | planned for `0.1.4` |
| [`Meta.connection`](#metaconnection) | shipped (`0.0.9`) |
| [`Meta.description`](#metadescription) | shipped |
| [`Meta.exclude`](#metaexclude) | shipped |
| [`Meta.fields`](#metafields) | shipped |
| [`Meta.fields_class`](#metafields_class) | planned for `0.1.1` |
| [`Meta.filterset_class`](#metafilterset_class) | shipped (`0.0.8`) |
| [`Meta.globalid_strategy`](#metaglobalid_strategy) | shipped (`0.0.9`) |
| [`Meta.interfaces`](#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.model`](#metamodel) | shipped |
| [`Meta.name`](#metaname) | shipped |
| [`Meta.nullable_overrides`](#metanullable_overrides) | shipped (`0.0.9`) |
| [`Meta.optimizer_hints`](#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`Meta.orderset_class`](#metaorderset_class) | shipped (`0.0.8`) |
| [`Meta.primary`](#metaprimary) | shipped (`0.0.6`) |
| [`Meta.relation_shapes`](#metarelation_shapes) | shipped (`0.0.9`) |
| [`Meta.required_overrides`](#metarequired_overrides) | shipped (`0.0.9`) |
| [`Meta.search_fields`](#metasearch_fields) | planned for `0.1.2` |
| [Multi-database cooperation](#multi-database-cooperation) | shipped (`0.0.7`) |
| [`only()` projection](#only-projection) | shipped (`0.0.2`) |
| [`OptimizerHint`](#optimizerhint) | shipped (`0.0.3`) |
| [`Ordering`](#ordering) | shipped (`0.0.8`) |
| [`OrderSet`](#orderset) | shipped (`0.0.8`) |
| [`order_input_type`](#order_input_type) | shipped (`0.0.8`) |
| [PEP 562 lazy export](#pep-562-lazy-export) | shipped (`0.0.13`) |
| [Per-field permission hooks](#per-field-permission-hooks) | planned for `0.1.1` |
| [Per-operation extension isolation](#per-operation-extension-isolation) | planned for `0.0.14` |
| [Plan cache](#plan-cache) | shipped (`0.0.3`) |
| [Probe URLconf](#probe-urlconf) | shipped (repository test pattern) |
| [Queryset diffing](#queryset-diffing) | shipped (`0.0.3`) |
| [Reference-counted cursor coordinator](#reference-counted-cursor-coordinator) | planned for `0.0.14` |
| [`RelatedAggregate`](#relatedaggregate) | planned for `0.1.3` |
| [`RelatedFilter`](#relatedfilter) | shipped (`0.0.8`) |
| [`RelatedOrder`](#relatedorder) | shipped (`0.0.8`) |
| [Relation handling](#relation-handling) | shipped (`0.0.1`+) |
| [Relay Node integration](#relay-node-integration) | shipped (`0.0.5`) |
| [RELAY_GLOBALID_STRATEGY](#relay_globalid_strategy) | shipped (`0.0.9`) |
| [`request_from_info`](#request_from_info) | shipped (`0.0.8`) |
| [`require_optional_module`](#require_optional_module) | planned for `0.0.14` |
| [Response-extension merge semantics](#response-extension-merge-semantics) | planned for `0.0.14` |
| [Response-extensions debug middleware](#response-extensions-debug-middleware) | planned for `0.0.14` |
| [`safe_wrap_connection_method`](#safe_wrap_connection_method) | shipped (`0.0.7`) |
| [Scalar field conversion](#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Scalar field override semantics](#scalar-field-override-semantics) | shipped (`0.0.6`) |
| [Schema audit](#schema-audit) | shipped (`0.0.3`) |
| [Schema export management command](#schema-export-management-command) | shipped (`0.0.7`) |
| [Schema introspection management command](#schema-introspection-management-command) | shipped (`0.0.9`) |
| [Schema reload discipline](#schema-reload-discipline) | shipped |
| [`seed_data`](#seed_data) | shipped |
| [`SerializerMutation`](#serializermutation) | shipped (`0.0.13`) |
| [Single-upstream parity](#single-upstream-parity) | shipped |
| [Soft dependency](#soft-dependency) | shipped (`0.0.13`) |
| [Specialized scalar conversions](#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [Strawberry extension lifecycle](#strawberry-extension-lifecycle) | planned for `0.0.14` |
| [strawberry_config](#strawberry_config) | shipped (`0.0.7`) |
| [Strictness mode](#strictness-mode) | shipped (`0.0.3`) |
| [`SyncMisuseError`](#syncmisuseerror) | shipped (`0.0.5`) |
| [`TestClient`](#testclient) | planned for `0.0.14` |
| [Django Trac #37064 hardening](#django-trac-37064-hardening) | shipped (`0.0.7`) |
| [`Upload` scalar](#upload-scalar) | shipped (`0.0.11`) |
| [Cross-subsystem invariants](#cross-subsystem-invariants) | planned for 1.0.0 |
| [`auto`-typed annotations](#auto-typed-annotations) | shipped (`0.0.9`) |

## Browse by category

For readers exploring rather than looking up a specific term:

- **Type generation:** [`DjangoType`](#djangotype) · [`Meta.model`](#metamodel) · [`Meta.fields`](#metafields) · [`Meta.exclude`](#metaexclude) · [`Meta.name`](#metaname) · [`Meta.description`](#metadescription) · [`Meta.primary`](#metaprimary) · [`Meta.interfaces`](#metainterfaces) · [`Meta.connection`](#metaconnection) · [`Meta.relation_shapes`](#metarelation_shapes) · [`Meta.globalid_strategy`](#metaglobalid_strategy) · [`Meta.nullable_overrides`](#metanullable_overrides) · [`Meta.required_overrides`](#metarequired_overrides) · [Definition-order independence](#definition-order-independence) · [`finalize_django_types`](#finalize_django_types) · [`ConfigurationError`](#configurationerror).
- **Field conversion:** [Scalar field conversion](#scalar-field-conversion) · [Choice enum generation](#choice-enum-generation) · [Relation handling](#relation-handling) · [Specialized scalar conversions](#specialized-scalar-conversions) · [Scalar field override semantics](#scalar-field-override-semantics) · [`Meta.nullable_overrides`](#metanullable_overrides) · [`Meta.required_overrides`](#metarequired_overrides) · [`Meta.choice_enum_names`](#metachoice_enum_names) · [`auto`-typed annotations](#auto-typed-annotations).
- **Optimizer:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [`OptimizerHint`](#optimizerhint) · [`Meta.optimizer_hints`](#metaoptimizer_hints) · [Plan cache](#plan-cache) · [FK-id elision](#fk-id-elision) · [`only()` projection](#only-projection) · [Queryset diffing](#queryset-diffing) · [Strictness mode](#strictness-mode) · [Schema audit](#schema-audit) · [Multi-database cooperation](#multi-database-cooperation) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning).
- **Filtering:** [`FilterSet`](#filterset) · [`RelatedFilter`](#relatedfilter) · [`filter_input_type`](#filter_input_type) · [`Meta.filterset_class`](#metafilterset_class).
- **Ordering:** [`OrderSet`](#orderset) · [`RelatedOrder`](#relatedorder) · [`Ordering`](#ordering) · [`order_input_type`](#order_input_type) · [`Meta.orderset_class`](#metaorderset_class).
- **Aggregation:** [`AggregateSet`](#aggregateset) · [`RelatedAggregate`](#relatedaggregate) · [`Meta.aggregate_class`](#metaaggregate_class) · [`get_child_queryset`](#get_child_queryset).
- **Field selection:** [`FieldSet`](#fieldset) · [`Meta.fields_class`](#metafields_class).
- **Search:** [`Meta.search_fields`](#metasearch_fields).
- **Permissions:** [`get_queryset` visibility hook](#get_queryset-visibility-hook) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [`DjangoModelPermission`](#djangomodelpermission) · [Per-field permission hooks](#per-field-permission-hooks) · [`request_from_info`](#request_from_info) · [Channels request adapter](#channels-request-adapter).
- **Relay:** [Relay Node integration](#relay-node-integration) · [RELAY_GLOBALID_STRATEGY](#relay_globalid_strategy) · [`DjangoNodeField`](#djangonodefield) · [`DjangoNodesField`](#djangonodesfield) · [`DjangoConnectionField`](#djangoconnectionfield) · [`DjangoConnection`](#djangoconnection) · [`Meta.connection`](#metaconnection) · [`Meta.relation_shapes`](#metarelation_shapes) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning) · [`SyncMisuseError`](#syncmisuseerror).
- **List fields:** [`DjangoListField`](#djangolistfield) · [Relation handling](#relation-handling).
- **Mutations:** [`DjangoMutation`](#djangomutation) · [`DjangoMutationField`](#djangomutationfield) · [`DjangoFormMutation`](#djangoformmutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`SerializerMutation`](#serializermutation) · [Input type generation](#input-type-generation) · [`FieldError` envelope](#fielderror-envelope) · [Auth mutations](#auth-mutations).
- **File / image uploads:** [`Upload` scalar](#upload-scalar) · [`DjangoFileType`](#djangofiletype) · [`DjangoImageType`](#djangoimagetype).
- **Integration / tooling:** [Django `AppConfig`](#django-appconfig) · [Schema export management command](#schema-export-management-command) · [Schema introspection management command](#schema-introspection-management-command) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) · [Debug-toolbar middleware](#debug-toolbar-middleware) · [Response-extensions debug middleware](#response-extensions-debug-middleware) · [Soft dependency](#soft-dependency) · [Joint version cut](#joint-version-cut) · [PEP 562 lazy export](#pep-562-lazy-export) · [`require_optional_module`](#require_optional_module) · [Single-upstream parity](#single-upstream-parity) · [Async SQL-capture boundary](#async-sql-capture-boundary) · [Bounded query-log rollover](#bounded-query-log-rollover) · [Cookbook parity](#cookbook-parity) · [Debug exception row](#debug-exception-row) · [Debug payload availability](#debug-payload-availability) · [Debug SQL row](#debug-sql-row) · [Developer-only debug posture](#developer-only-debug-posture) · [Django debug-cursor capture](#django-debug-cursor-capture) · [`DjangoDebugExtension`](#djangodebugextension) · [Graphene debug migration](#graphene-debug-migration) · [Hard dependency](#hard-dependency) · [Masking-extension ordering](#masking-extension-ordering) · [Per-operation extension isolation](#per-operation-extension-isolation) · [Reference-counted cursor coordinator](#reference-counted-cursor-coordinator) · [Response-extension merge semantics](#response-extension-merge-semantics) · [Strawberry extension lifecycle](#strawberry-extension-lifecycle).
- **Testing:** [`safe_wrap_connection_method`](#safe_wrap_connection_method) · [Django Trac #37064 hardening](#django-trac-37064-hardening) · [`TestClient`](#testclient) · [`GraphQLTestCase`](#graphqltestcase) · [Live-first coverage mandate](#live-first-coverage-mandate) · [Eviction-simulated absence](#eviction-simulated-absence) · [Schema reload discipline](#schema-reload-discipline) · [`seed_data`](#seed_data) · [Probe URLconf](#probe-urlconf).

---

## `AggregateSet`

**Status:** planned for `0.1.3`.

Declarative aggregate class with `Sum` / `Count` / `Avg` / `Min` / `Max` / `Mode` / `Uniques` / `GroupBy`, [`RelatedAggregate`](#relatedaggregate) traversal, custom `compute_*_*` stats declared via `Meta.custom_stats`, sync and async paths via `compute` / `acompute`. Computation is selection-set-aware — only requested stats are computed. The [`get_child_queryset`](#get_child_queryset) cascade hook excludes private rows when traversing into children. Declared per-type via [`Meta.aggregate_class`](#metaaggregate_class).

**See also:** [`Meta.aggregate_class`](#metaaggregate_class) · [`RelatedAggregate`](#relatedaggregate) · [`get_child_queryset`](#get_child_queryset).

## `apply_cascade_permissions`

**Status:** shipped (`0.0.10`).

Cascades each [`DjangoType`](#djangotype)'s [`get_queryset`](#get_queryset-visibility-hook) visibility to its related types across **single-column forward FK / OneToOne edges** (M2M, reverse relations, `GenericForeignKey` / `GenericRelation`, and the multi-table-inheritance `<parent>_ptr` parent link are out of scope). Called inside a type's `get_queryset` override:

```python
@classmethod
def get_queryset(cls, queryset, info):
    user = getattr(getattr(info.context, "request", None), "user", None)
    if user and user.is_staff:
        return queryset
    return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

**The walk.** Per call the helper walks `cls`'s model `_meta` edges and, for each single-column forward relation, resolves the target type through the registry primary lookup, skips any target without a custom `get_queryset` (the identity default adds nothing), and intersects `Q(<fk>__in=<target visible pks>) | Q(<fk>__isnull=True)` into the caller's queryset. The target visibility subquery is the target type's own `get_queryset` run against the target model's rows, pinned to the caller's resolved DB alias (`queryset.db`). The walk is depth-1; transitive cascade emerges because each target's hook may itself call the helper.

**Four invariants.** (1) A module-level `ContextVar` seen-set guards cycles — re-entry on a type already walking returns the partially-narrowed queryset (never raises), and the root call resets the var in a `finally` so request isolation holds under WSGI and ASGI. (2) Single-column forward scope only. (3) Nullable-FK rows are preserved by the `__isnull=True` disjunct. (4) Every target subquery is pinned to the caller's resolved alias so sharded callers never compose a cross-database `__in`.

**`fields=` validation is loud.** Passing `fields=` scopes the walk to the named edges; a bare string is rejected up front (so `fields="item"` fails loudly instead of iterating its characters), and an unknown or non-cascadable name raises [`ConfigurationError`](#configurationerror) naming the field, the model, and the model's cascadable set.

**Sync / async pair.** The sync helper closes the coroutine and raises [`SyncMisuseError`](#syncmisuseerror) if a target hook returns one (an `async def` hook met from the sync walk); `aapply_cascade_permissions(cls, queryset, info, fields=None)` is the async twin — it runs the same walk through `sync_to_async(thread_sensitive=True)` so blocking consumer-hook work (e.g. `user.has_perm(...)` permission-table reads) stays off the event loop:

```python
qs = await aapply_cascade_permissions(cls, qs, info)
```

**Composition.** The cascade narrows rows first; the shipped [`FilterSet`](#filterset) / [`OrderSet`](#orderset) `check_<field>_permission` input gates then judge input on the surviving rows (a denial never leaks a cascade-hidden row's existence). It composes with [connections](#djangoconnectionfield) (edges and `totalCount` narrow together), [node refetch](#djangonodefield) (a hidden row refetches as `null`), [list fields](#djangolistfield), and nested filter branches through their existing `get_queryset` seams — under the optimizer's `Prefetch` downgrade, with **zero** added query round-trips (the `__in` subqueries compile into the caller's single `SELECT`).

**See also:** [`get_queryset` visibility hook](#get_queryset-visibility-hook) · [Per-field permission hooks](#per-field-permission-hooks).

## Async SQL-capture boundary

**Status:** planned for `0.0.14`.

The execution-color boundary of [`DjangoDebugExtension`](#djangodebugextension). Exception capture is result-based and therefore works for sync and async operations. SQL capture is guaranteed on Django's sync path but is normally empty on async execution: the extension brackets the event-loop thread's thread-local connection objects, while Django ORM work runs in `sync_to_async` executor threads with different connection objects. The [Reference-counted cursor coordinator](#reference-counted-cursor-coordinator) guarantees restoration for overlapping async operations, but it cannot attribute executor-thread SQL to an operation. Under `DJANGO_ALLOW_ASYNC_UNSAFE`, concurrent loop-thread ORM work can be cross-attributed. This is a documented fidelity limit, not a partial async guarantee.

**See also:** [`DjangoDebugExtension`](#djangodebugextension) · [Django debug-cursor capture](#django-debug-cursor-capture) · [Per-operation extension isolation](#per-operation-extension-isolation).

## Auth mutations

**Status:** shipped (`0.0.13`).

The opt-in session-auth surface over `django.contrib.auth` (`0.0.13`): four field factories at the `django_strawberry_framework.auth` submodule path - `login_mutation()`, `logout_mutation()`, `register_mutation()`, and the `current_user()` query helper - imported explicitly and never injected into a schema (the opt-in is structural: nothing is re-exported from the package root, and a consumer who skips auth never pays its import). `login(username:, password:)` authenticates against the configured backends and establishes the Django session, returning the user in the uniform payload slot; a failed authentication (wrong password, unknown username, inactive user) is ONE non-field [`FieldError`](#fielderror-envelope) - `"Incorrect username/password"`, deliberately undifferentiated so there is no account-enumeration oracle - never a raised error. `logout` returns the pinned model-less `{ ok, errors }` payload (`ok` is whether an authenticated session existed; teardown is idempotent). `register(data: RegisterInput!)` is a narrow [`DjangoMutation`](#djangomutation) `create` over `get_user_model()` whose generated input is structurally limited to `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` - the privilege columns (`is_staff` / `is_superuser` / `groups` / `user_permissions`) are unreachable by construction - with `validate_password(password, user)` failures keyed to `password` (the constructed instance is passed, so similarity validators compare against the submitted username) and the password stored only through `set_password` (hashed before `full_clean()`; the plaintext never reaches a model column). `current_user()` returns the session actor typed as the consumer's primary user [`DjangoType`](#djangotype), or `null` for an anonymous request (an expected state, never an error), with no [`get_queryset`](#get_queryset-visibility-hook) re-run - the actor-not-lookup rule; `login`'s payload user likewise skips visibility and the optimizer re-fetch, while `register`'s node comes back through the standard planned re-fetch.

Every factory accepts `permission_classes=` through the standard `check_permission` machinery; the auth **default is the explicit empty list (allow-any)** - the deliberate, documented inversion of the write family's deny-by-default ([`DjangoModelPermission`](#djangomodelpermission) / deny-all), because an auth surface that requires authentication is a contradiction. A user-typed auth field declared with no registered primary user `DjangoType` fails loudly at [`finalize_django_types`](#finalize_django_types) naming the fix (`Meta.model = get_user_model()`; `Meta.primary = True` when the model has several types); a logout-only schema is exempt (its payload references no user type). **The consumer `UserType`'s field selection IS the authenticated read surface**: whatever that type selects is what `login` / `register` / `me` return - select explicitly (never `fields = "__all__"` over the user model) and keep `password` and the privilege columns off it; note a `get_queryset` written for row-redaction does not reach `me` / `login`'s node (only the field selection governs what an actor sees of themselves there). Session transport requires Django's `SessionMiddleware` + `AuthenticationMiddleware` on the `/graphql/` path (a sessionless deployment surfaces Django's own error); the `0.0.14` [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) ships the Channels session **transport** (`AuthMiddlewareStack` on both protocols) and the package's **read-path** request contract consumes it ([`request_from_info`](#request_from_info) resolves the Channels context to the [Channels request adapter](#channels-request-adapter), so `current_user` and the permission gates work over the router), but session-**mutating** auth execution (`login` / `logout` / `register`) through Channels consumers remains unverified: the [`TestClient`](#testclient) card (`DONE-043-0.0.14`) resolves this to a dedicated follow-on card, because its helpers wrap Django's HTTP test clients (`django.test.Client` / `AsyncClient`), not Channels communicators.

**See also:** [`DjangoMutation`](#djangomutation), [`FieldError` envelope](#fielderror-envelope), [`DjangoModelPermission`](#djangomodelpermission).

## `BigInt` scalar

**Status:** shipped (`0.0.6`).

JSON-safe scalar typically used to map Django's 64-bit integer fields `BigIntegerField` and `PositiveBigIntegerField` (not `BigAutoField`). Technically arbitrary-precision: serialized via Python `str(int_value)`, which handles any `int`. Wire format is a decimal string to survive GraphQL's signed 32-bit `Int` boundary (executing a query returning an `int`-annotated value past `2**31 - 1` raises a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`). Strict parser accepts Python `int` (excluding `bool`) and strings matching `^(0|-?[1-9][0-9]*)$` — plain ASCII decimal, optional leading minus for non-zero, no leading zeroes (except `"0"` itself), no underscores, no plus sign, no Unicode digits. Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`. Part of [Specialized scalar conversions](#specialized-scalar-conversions).

Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])` (the optimizer is a module-level singleton wrapped in a factory — see [`DjangoOptimizerExtension`](#djangooptimizerextension)). Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol. The migration applies to any schema that resolves to `BigInt` — including [`DjangoType`](#djangotype) schemas whose fields are backed by `BigIntegerField` or `PositiveBigIntegerField` (resolved to `BigInt` by the [`Specialized scalar conversions`](#specialized-scalar-conversions) converter table) even when the consumer never imports or annotates `BigInt` directly.

**See also:** [Scalar field conversion](#scalar-field-conversion) · [Specialized scalar conversions](#specialized-scalar-conversions).

## Bounded query-log rollover

**Status:** planned for `0.0.14`.

The best-effort capture boundary created by Django's bounded `queries_log` deque. [`DjangoDebugExtension`](#djangodebugextension) snapshots each log's length, materializes the deque at teardown, and reads from `min(snapshot, current_length)`, so a reset or shortened log cannot raise. If a full deque rolls over while keeping the same length, however, a length snapshot cannot distinguish old rows from new rows and the operation may report some or none of its queries. Django's own `CaptureQueriesContext` has the same limitation. The default 9000-row limit makes this pathological, but the behavior is documented and tested rather than represented as exact capture.

**See also:** [Django debug-cursor capture](#django-debug-cursor-capture) · [Debug SQL row](#debug-sql-row).

## Channels request adapter

**Status:** planned for `0.0.14`.

The request-like object [`request_from_info`](#request_from_info) returns for Strawberry's Channels context shape (planned with the `0.0.14` [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) card, its Decision 11). Strawberry's Channels consumers hand resolvers a dict context (`{"request": ChannelsRequest, "response": TemporalResponse}`) whose `ChannelsRequest` wraps `consumer` + `body`, with the authenticated actor at `request.consumer.scope["user"]`.

The adapter **wraps** the original `ChannelsRequest` rather than replacing it with a narrow two-field object: it exposes `.user`, `.session`, and `.scope` explicitly from `consumer.scope`, and **delegates every other attribute to the wrapped request via `__getattr__`** — so consumer-written code that receives the resolved request (the [`FilterSet`](#filterset) / [`OrderSet`](#orderset) `check_<field>_permission` input gates, [`DjangoModelPermission`](#djangomodelpermission) overrides, DRF serializer hooks) keeps reading `request.headers`, `request.COOKIES`, `request.path`, `request.method`, or `request.consumer` under Channels instead of raising `AttributeError`. Duck-typed: `utils/permissions.py` imports nothing from `channels`, and the adapter works for consumers who wire Strawberry's Channels consumers without the router. Read path only — session-mutating [Auth mutations](#auth-mutations) over Channels stay deferred.

**See also:** [`request_from_info`](#request_from_info) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) · [Auth mutations](#auth-mutations).

## Choice enum generation

**Status:** shipped (`0.0.1`).

`CharField` / `TextField` with `choices=...` generates a Strawberry enum. Member names are sanitized from stored database values (not display labels), so the GraphQL contract is stable against label changes. Enum objects are cached by `(model, field_name)`. Grouped choices are rejected with [`ConfigurationError`](#configurationerror).

Stable cross-type enum naming overrides ship later — see [`Meta.choice_enum_names`](#metachoice_enum_names).

**See also:** [Scalar field conversion](#scalar-field-conversion) · [`Meta.choice_enum_names`](#metachoice_enum_names).

## `ConfigurationError`

**Status:** shipped (`0.0.1`).

Raised at type-creation or finalization time when consumer configuration is invalid or inconsistent. Examples:

- unknown `Meta` keys (typo detection)
- deferred `Meta` keys whose owning subsystem hasn't shipped
- unresolved relation targets at finalization
- declaring a new concrete `DjangoType` after [`finalize_django_types()`](#finalize_django_types) has been called
- invalid optimizer hints (unknown field name, wrong type)
- `CompositePrimaryKey` models declared with `Meta.interfaces = (relay.Node,)`

Validation errors raise early and loudly rather than silently mutating the schema.

**See also:** [`DjangoType`](#djangotype) · [`finalize_django_types`](#finalize_django_types).

## Connection-aware optimizer planning

**Status:** shipped (`0.0.9`).

The optimizer recognizes synthesized `<field>Connection` selections inside a parent's selection walk — via the declaring type's `DjangoTypeDefinition``.relation_connections` metadata, never by reaching into [`DjangoConnectionField`](#djangoconnectionfield) internals — and plans a windowed `Prefetch` for each under a package-reserved `_dst_<field>_connection` `to_attr`. The window is built from `RowNumber()` / `Count(1)` window functions partitioned by the parent attach key, with the slice derived from the connection's resolved `first` / `last` / `before` / `after` arguments capped by `relay_max_results`; the child plan carries the target's visibility, projections, and any deeper nested connections, and reproduces the pipeline's deterministic (pk-terminal) order so cursors match. For a keyset-mode target, the nested window instead uses that target type's declared `Meta.cursor_field` as the complete order, matching root keyset cursor bytes by construction; a nested `orderBy:` sidecar deliberately leaves that response key unplanned for the per-parent pipeline rather than overriding the cursor order.

The generated connection class then serves `edges`, cursors, `pageInfo`, and `totalCount` from the prefetched window's row-number annotations plus its conditional count/keyset-seek annotations or count-free n+1 probe — one batched query per relation window, zero per-parent queries on the fast path. Retained marker rows directly serve `first: 0`, overshot offset `after:`, and corresponding forward keyset empty pages: a physically empty planned window proves the parent has no rows, while a marker-only window carries the true count and page flags. Genuine fallbacks stay distinct. A sidecar or unsupported backward window normally leaves only that response key unplanned (and the resolver refuses a stale sidecar window defensively); `last: 0` is likewise unplanned so Strawberry's serve-all quirk runs per-parent; conflicting argument payloads for one response key leave that connection fully unplanned; and a handed-off wrapper missing a required count or seek annotation recovers through its defensive per-parent callable. Argument-driven non-planning emits a debug log naming the response key and reason. Whole-relation fallbacks remain visible to [Strictness mode](#strictness-mode): [`OptimizerHint`](#optimizerhint)`.SKIP, an unwindowable relation or child queryset (including `.distinct()`), and a relation shape recognized only on a secondary [`DjangoType`](#djangotype). The `.distinct()` fallback is a correctness guard: SQL evaluates window functions before `DISTINCT`, so a `Count(1) OVER` over a distinct child would over-count — the relation is conservatively left per-parent instead. The mechanism needs a window-capable backend (the package floor `Django>=5.2` with SQLite ≥ 3.25 covers every supported configuration); an exotic backend without window support raises its own `NotSupportedError`, and the recourse is `relation_shapes = {"<field>": "list"}` or running without the optimizer.

The nested fetch strategy is fixed per [`DjangoOptimizerExtension`](#djangooptimizerextension) instance: `"windowed"` is the default, `"lateral"` plans a Postgres-capable `CROSS JOIN LATERAL` queryset, and `"auto"` keeps one cache-stable lateral-capable window plan whose fetch-time decision follows the nested queryset's effective DB alias (including `.using(...)` and router choices). PostgreSQL uses lateral SQL when the query shape is supported; every non-Postgres alias and every unrecognized lateral shape executes the same already-windowed ORM body, so fallback changes performance rather than pagination correctness.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [Plan cache](#plan-cache) · [`DjangoOptimizerExtension`](#djangooptimizerextension).

## Cookbook parity

**Status:** planned through `1.0.0`.

The repository's obligation to validate migration claims against the working `django-graphene-filters` cookbook, not a hypothetical Graphene application. Domain declarations in `cookbook/recipes/schema.py` establish the app-level `Meta`-driven target; project-level composition in `cookbook/schema.py` and `cookbook/settings.py` establishes engine configuration such as debug wiring. Import-only migration applies to the domain declaration surface. Aggregate schema extensions, middleware settings, and client wire behavior migrate through an explicit recipe. Spec 044 applies this rule through the [Graphene debug migration](#graphene-debug-migration).

**See also:** [Graphene debug migration](#graphene-debug-migration) · [Single-upstream parity](#single-upstream-parity).

## Debug exception row

**Status:** planned for `0.0.14`.

One item in `extensions.debug.exceptions`. The wire keys mirror graphene-django's `DjangoDebugException`: `excType` is `str(type(exc))`, `message` is `str(exc)`, and `stack` is rendered from the terminal exception's own `__traceback__`. Collection begins only when an execution-result `GraphQLError` has a non-null `original_error`; nested `GraphQLError.original_error` links are walked to the terminal exception with identity-based cycle protection. Pure parse and validation errors are excluded, while resolver errors, explicitly raised `GraphQLError`s, completion errors, and scalar-serialization errors are included. This result-level scope is intentionally broader than graphene-django's resolver wrapper.

**See also:** [`DjangoDebugExtension`](#djangodebugextension) · [Debug payload availability](#debug-payload-availability) · [Masking-extension ordering](#masking-extension-ordering).

## Debug payload availability

**Status:** planned for `0.0.14`.

When `extensions.debug` is present. An enabled schema emits both `sql` and `exceptions` lists for every operation that reaches execution, including successful operations, resolver failures, mutations, and introspection. Parse and validation failures carry no `debug` key because Strawberry asks extensions for results before `on_operation` teardown has assembled the payload. A coerced non-GraphQL exception that escapes execution can carry the payload because teardown has run before the engine's recovery response. `get_results()` is therefore a pure, idempotent stash read and may be called more than once.

**See also:** [Strawberry extension lifecycle](#strawberry-extension-lifecycle) · [Response-extension merge semantics](#response-extension-merge-semantics).

## Debug SQL row

**Status:** planned for `0.0.14`.

One item in `extensions.debug.sql`. The six wire keys are `vendor`, `alias`, `sql`, `duration`, `isSlow`, and `isSelect`, preserving the graphene-django client vocabulary where Django's query log can supply the value. `duration` is float seconds from Django's three-decimal log string; `isSlow` uses graphene's `duration > 10` threshold; `isSelect` uses its leading-`SELECT` sniff. Deliberately omitted are `rawSql`, `params`, `startTime`, `stopTime`, and the Postgres-only `transId`, `transStatus`, `isoLevel`, and `encoding` fields. `executemany` and transaction-management statements retain Django's own logged form.

**See also:** [Django debug-cursor capture](#django-debug-cursor-capture) · [Bounded query-log rollover](#bounded-query-log-rollover) · [Multi-database cooperation](#multi-database-cooperation).

## Debug-toolbar middleware

**Status:** planned for `0.0.14`.

`django-debug-toolbar`'s SQL-panel window into Strawberry `/graphql/` requests. `DebugToolbarMiddleware` (`django_strawberry_framework/middleware/debug_toolbar.py`) subclasses the stock `debug_toolbar.middleware.DebugToolbarMiddleware` and is referenced by its dotted path near the front of `MIDDLEWARE`, **replacing** the stock toolbar entry it subclasses (listing both runs the toolbar twice). It mirrors `strawberry-django`'s `middlewares/debug_toolbar.py` (itself based on the archived `django-graphiql-debug-toolbar`), contributing exactly two GraphQL-shaped overrides and leaving everything else — panels, request tracking, history storage, handle rendering, and the inherited show-toolbar gating (`SHOW_TOOLBAR_CALLBACK` / `INTERNAL_IPS`) — to the stock toolbar. `process_view` tags a request when its resolved `view_class` is a Strawberry Django view (`strawberry.django.views.BaseView`; non-Strawberry views pass straight through). `_postprocess` chains to the stock method first, then appends the GraphiQL bridge template to a tagged 200 HTML page and injects a top-level `debugToolbar` payload (the toolbar `requestId` plus each enabled panel's `title` / `nav_subtitle`, `TemplatesPanel` skipped) into tagged `application/json` operation responses, refreshing `Content-Length` only when already present and passing streaming responses through untouched. Injection is **view-scoped, not IDE-scoped**: while the toolbar is enabled every JSON response from a Strawberry view carries the `debugToolbar` key — from GraphiQL or a programmatic client alike — and the bridge template strips it only inside the GraphiQL page; `IntrospectionQuery` operations are skipped so history-churning IDEs (Apollo Sandbox) do not evict real results.

Wiring is the toolbar's own three pieces with one package-specific swap: list `"debug_toolbar"` in `INSTALLED_APPS`, list this class's dotted path in `MIDDLEWARE` replacing the stock entry, and add `debug_toolbar_urls()` to the URLconf. Two setup omissions fail loudly and specifically: leaving `debug_toolbar_urls()` out fails **every** toolbar-processed request with `NoReverseMatch` (the stock postprocess renders the toolbar — which reverses `djdt:` routes — for every processed response, so this is not a quiet panel-click 404), and omitting `"debug_toolbar"` from `INSTALLED_APPS` raises `ImproperlyConfigured` at leaf import (an `apps.is_installed` pre-check that turns Django's cryptic `HistoryEntry` app-label `RuntimeError` into one actionable message). The bridge template resolves because consumers already list `django_strawberry_framework` in `INSTALLED_APPS` (the app-dirs loader finds `templates/django_strawberry_framework/debug_toolbar.html`); the toolbar's own `django.contrib.staticfiles` + `STATIC_URL` prerequisite still applies, and its absence surfaces on `/graphql/` traffic under this middleware.

[Soft dependency](#soft-dependency) on `django-debug-toolbar` (the package's third, after `djangorestframework` and `channels`). Importing this leaf module is the opt-in boundary — Django's `MIDDLEWARE` dotted path reaches it via `import_string` at startup — so `require_debug_toolbar()`, a thin wrapper over [`require_optional_module`](#require_optional_module), runs at import time: a toolbar-less machine gets one actionable install-hint `ImportError` naming the verified `django-debug-toolbar>=7.0.0` floor, while `import django_strawberry_framework` and `import django_strawberry_framework.middleware` both stay clean. Two deliberate robustness divergences from the verbatim upstream borrow: `process_view` guards `issubclass` with `isinstance(view, type)` (the middleware runs for all global traffic, so a non-class `view_class` attached by an unrelated decorator must not `TypeError`/500 the view), and `_get_payload` returns `None` when a declared-JSON response cannot be decoded with its charset, cannot be parsed, or decodes to a non-object value; `_postprocess` then performs no package-specific body or `Content-Length` rewrite, so an unusual response remains available to the caller rather than becoming a 500. This is a Django HTTP middleware on the raw request/response pair, **not** a Channels integration.

Distinct from the [Response-extensions debug middleware](#response-extensions-debug-middleware) — this is the server-side toolbar panel; that is in-response surfacing through the GraphQL response's `extensions` envelope. Both useful, not mutually exclusive.

**See also:** [Response-extensions debug middleware](#response-extensions-debug-middleware) · [Soft dependency](#soft-dependency) · [`require_optional_module`](#require_optional_module) · [`DjangoOptimizerExtension`](#djangooptimizerextension).

## Definition-order independence

**Status:** shipped (`0.0.4`).

`DjangoType` collection is split from Strawberry finalization. Class creation records Django metadata and pending relation targets; [`finalize_django_types()`](#finalize_django_types) resolves those pending relations, attaches generated relation resolvers, and decorates each collected type with `strawberry.type`.

Supported relation cycles:

- forward FK and reverse FK
- forward OneToOne and reverse OneToOne
- forward and reverse M2M
- multi-cycle graphs that combine those shapes

Supported forward-reference / manual relation shapes:

- generated relation annotations for target types declared before or after the source type
- same-module string annotations such as `items: list["ItemType"]`
- stringified annotations from `from __future__ import annotations`
- cross-module `Annotated[..., strawberry.lazy("module.path")]` annotations
- annotation-only relation overrides, which keep the generated resolver
- `strawberry.field(resolver=...)` and `@strawberry.field` relation overrides, which keep the consumer resolver

Unresolved relation targets fail during finalization with an error that names the source model, source field, and target model. The most common cause is that the Python module containing the target `DjangoType` was never imported before finalization.

Validation that a manual relation annotation matches the Django relation cardinality is deferred.

**See also:** [`finalize_django_types`](#finalize_django_types) · [`DjangoType`](#djangotype) · [Relation handling](#relation-handling).

## Developer-only debug posture

**Status:** planned for `0.0.14`.

The security contract for response-side debugging. [`DjangoDebugExtension`](#djangodebugextension) is off by default and intended only for development-controlled schemas because it returns interpolated SQL plus raw exception types, messages, and tracebacks to the GraphQL client. It can intentionally reveal details that a masking extension hides from the standard `errors` array. The initial surface has no settings gate, request predicate, redaction hook, row cap, or configurable slow-query threshold; consumers control exposure by whether the class appears in the schema's `extensions=` list. Never enable it on an internet-facing production schema.

**See also:** [`DjangoDebugExtension`](#djangodebugextension) · [Masking-extension ordering](#masking-extension-ordering).

## Django `AppConfig`

**Status:** shipped (`0.0.7`).

`django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. The `ready()` body imports `django_strawberry_framework._django_patches` and calls `apply()` to install the [Django Trac #37064 hardening](#django-trac-37064-hardening) at Django app-load time. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's implicit single-AppConfig discovery resolves the explicit class.

**See also:** [Django Trac #37064 hardening](#django-trac-37064-hardening) · [Schema export management command](#schema-export-management-command).

## Django debug-cursor capture

**Status:** planned for `0.0.14`.

The SQL fidelity source used by [`DjangoDebugExtension`](#djangodebugextension). For every alias in `connections.all()`, the extension saves and enables `connection.force_debug_cursor`, snapshots `len(connection.queries_log)`, then restores the saved flag and serializes new log rows at teardown. This is the flag-and-snapshot mechanism of Django's `CaptureQueriesContext` without constructing that context directly, because its `__enter__` eagerly opens every configured connection. Enabling `force_debug_cursor` makes `CursorDebugWrapper` populate `queries_log` independently of `settings.DEBUG`; the extension adds no package-owned cursor wrapper and does not force unused aliases open.

**See also:** [Reference-counted cursor coordinator](#reference-counted-cursor-coordinator) · [Bounded query-log rollover](#bounded-query-log-rollover) · [Debug SQL row](#debug-sql-row).

## `DjangoConnection`

**Status:** shipped (`0.0.9`).

Generic Relay connection base `DjangoConnection[T]`, a `strawberry.relay.ListConnection` subclass that owns the package's `first` + `last` mutual-exclusivity guard (which Strawberry's `SliceMetadata.from_arguments` does not provide), consumes optimized nested windows, and dispatches `Meta.cursor_field` sources to the package's keyset slicer. Ordinary non-window offset sources still delegate to Strawberry's `ListConnection`; the base itself carries no `total_count` field. [`DjangoConnectionField`](#djangoconnectionfield) never hands the schema this generic base directly; it resolves each node type through a generated concrete `<TypeName>Connection` subclass (the `totalCount` opt-in via [`Meta.connection`](#metaconnection) only controls whether the `total_count` members are added), because a bare generic alias loses the `resolve_connection` override at Strawberry's generic specialization.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [Relay Node integration](#relay-node-integration).

## `DjangoConnectionField`

**Status:** shipped (`0.0.9`).

Relay-style connection field with `edges` / `node` / `pageInfo` / `totalCount`, cursor-based pagination, and `filter:` / `orderBy:` arguments derived from the wrapped `DjangoType`'s [`filterset_class`](#metafilterset_class) / [`orderset_class`](#metaorderset_class) sidecars via a synthesized resolver signature (no hand-written list resolver, no parallel argument declarations). Opt-in `totalCount` via [`Meta.connection`](#metaconnection)`= {"total_count": True}` resolves through a generated per-target `<TypeName>Connection` class — counted on the post-filter pre-slice queryset, selection-gated, per connection instance. The composition pipeline runs `get_queryset` visibility -> `filter` -> `orderBy` -> default deterministic pk-ordering -> optimizer-plan -> cursor slice, and a package-owned guard rejects `first` + `last` together with a `GraphQLError`. The `search:` argument is reserved for `Meta.search_fields` (`0.1.2`) and is not generated in `0.0.9`. As of `0.0.9`, relations between Relay-Node-shaped types synthesize `<field>Connection` siblings through this same machinery — see [`Meta.relation_shapes`](#metarelation_shapes).

The field owns its own optimizer cooperation point (the plan-application logic extracted from [`DjangoOptimizerExtension`](#djangooptimizerextension)`._optimize`) because Strawberry's connection slicing hides the pre-slice queryset from the schema middleware. That seam now also feeds nested `<field>Connection` window planning: a selected nested connection gets a windowed `Prefetch` so its page costs no per-parent query — see [Connection-aware optimizer planning](#connection-aware-optimizer-planning) (shipped `0.0.9`). A [Strictness mode](#strictness-mode) `"raise"` run now flags an unplanned, unserved nested-connection access through the same resolver-key vocabulary the generated list-relation resolvers use.

**See also:** [`DjangoConnection`](#djangoconnection) · [`DjangoNodeField`](#djangonodefield) · [Relay Node integration](#relay-node-integration) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning) · [`Meta.relation_shapes`](#metarelation_shapes).

## `DjangoDebugExtension`

**Status:** planned for `0.0.14`.

The public Strawberry `SchemaExtension` exported from `django_strawberry_framework.extensions` by spec 044. Consumers opt in with the **class** in `strawberry.Schema(..., extensions=[..., DjangoDebugExtension])`; the class is not exported from the package root and fakeshop does not enable it globally. One fresh instance per operation captures [Debug SQL rows](#debug-sql-row) and [Debug exception rows](#debug-exception-row), then returns `{"debug": {"sql": [...], "exceptions": [...]}}` through Strawberry's response-extension seam. It is the concrete symbol behind [Response-extensions debug middleware](#response-extensions-debug-middleware), requires `strawberry-graphql>=0.316.0` for instance isolation, and follows the [Developer-only debug posture](#developer-only-debug-posture).

**See also:** [Strawberry extension lifecycle](#strawberry-extension-lifecycle) · [Per-operation extension isolation](#per-operation-extension-isolation) · [Django debug-cursor capture](#django-debug-cursor-capture) · [Debug payload availability](#debug-payload-availability).

## `DjangoFileType`

**Status:** shipped (`0.0.11`).

Resolver-backed output object for a `FileField` column, carrying `name` (non-null), `path` / `size` / `url` (nullable, storage-safe). The `path` / `size` / `url` subfields delegate to the shared `_safe_file_attr` guard, which degrades to `null` on the storage-shaped errors a non-filesystem backend or a vanished file raises (`ValueError` / `OSError` / `NotImplementedError`); `SuspiciousFileOperation` is deliberately **not** swallowed (it propagates as a path-traversal security signal). An empty / absent file resolves the **whole object** to `null`, never a `FieldFile.url` exception. Mapped on **read** via the new `FIELD_OUTPUT_TYPE_MAP` (kept off the shared [`SCALAR_MAP`](#scalar-field-conversion) / filter-input path, so no output object reaches a [`FilterSet`](#filterset) input). A consumer `attachment: str` annotation override bypasses it and keeps the legacy `str` (name / URL) shape per [Scalar field override semantics](#scalar-field-override-semantics). Paired with the [`Upload` scalar](#upload-scalar) on the input side.

**See also:** [`Upload` scalar](#upload-scalar) · [`DjangoImageType`](#djangoimagetype).

## `DjangoFormMutation`

**Status:** shipped (`0.0.12`).

The model-less sibling base for a plain Django `Form` mutation, declared via `Meta.form_class`. Unlike [`DjangoModelFormMutation`](#djangomodelformmutation) it is **not** a [`DjangoMutation`](#djangomutation) subclass: a plain `Form` has no model, so it has its own lightweight metaclass and carries **no** [`DjangoType`](#djangotype) object slot in its payload. It is accepted by the generalized [`DjangoMutationField`](#djangomutationfield) family and shares the form pipeline (`is_valid()` -> `form.errors` -> [`FieldError`](#fielderror-envelope) -> `perform_mutate`) and the form-field converter. Its generated `<Name>Payload` is pinned to exactly two fields -- `ok: Boolean!` and `errors: [FieldError!]!` -- with no cleaned-data output fields. On `form.is_valid()` success `perform_mutate(self, form, info) -> None` runs (its default calls `form.save()` when present, else is a no-op; a consumer overrides it for the real side effect) and the payload is `ok: true, errors: []`; on a validation failure `perform_mutate` does not run and the payload is `ok: false` with one [`FieldError`](#fielderror-envelope) per offending field (the form's `NON_FIELD_ERRORS` bucket keyed under the `"__all__"` sentinel) -- the same envelope every flavor returns. A write-authorization denial is a top-level `GraphQLError`, never a payload entry. It has its own `forms/sets.py` declaration registry + `bind_form_mutations()` entry point wired into [`finalize_django_types`](#finalize_django_types) phase 2.5. Exported from the package root.

**See also:** [`DjangoMutation`](#djangomutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`FieldError` envelope](#fielderror-envelope).

## `DjangoGraphQLProtocolRouter`

**Status:** planned for `0.0.14`.

The package's Channels transport helper (`django_strawberry_framework/routers.py`, the one-import ASGI / WebSocket migration aid): a `channels.routing.ProtocolTypeRouter` subclass wiring GraphQL onto **both** HTTP and WebSocket with the exact upstream composition — HTTP is `AuthMiddlewareStack(URLRouter([graphql, *django_fallback]))` (the optional Django ASGI fallback is HTTP-branch-only, appended **after** the GraphQL route), WebSocket is `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([graphql])))` (origin validation is WS-branch-only; a cross-origin **or missing-`Origin`** handshake is denied against `ALLOWED_HOSTS`) — over `strawberry.channels`'s `GraphQLHTTPConsumer` / `GraphQLWSConsumer` (engine-owned, never subclassed). The constructor is byte-compatible with upstream `strawberry_django.routers.AuthGraphQLProtocolTypeRouter` — `(schema, django_application=None, url_pattern="^graphql")` — so a migrant changes exactly the import line; the symbol name is intentionally distinct so the module never impersonates the upstream API. The schema passes through untouched (extensions ride along — a [`DjangoOptimizerExtension`](#djangooptimizerextension) schema keeps it); `url_pattern` is a `re_path` regex matched with the leading slash stripped, so the `^graphql` default also matches `/graphql/` (pass `^graphql/$` for an exact path). Channels' `ProtocolTypeRouter` raises `ValueError` for unmapped scope types — uvicorn's startup `lifespan` probe logs a benign "ASGI 'lifespan' protocol appears unsupported", not breakage.

[Soft dependency](#soft-dependency) on `channels` (the second, after `djangorestframework`), behavior matrix: `import django_strawberry_framework` and `import django_strawberry_framework.routers` both succeed without channels; only symbol access — the explicit `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`, or the submodule `import *` (`__all__` names the lazy [PEP 562 export](#pep-562-lazy-export)) — raises `ImportError` whose hint names the verified `channels>=4.3.2` floor (one floor covering the package's whole advertised Django range through 6.0). The guard is `require_channels()`, a thin wrapper over [`require_optional_module`](#require_optional_module); present-but-incompatible installs get **split** actionable errors naming which half is broken — a failing `channels.*` import names the channels floor, a failing `strawberry.channels` consumer import names both `channels>=4.3.2` and `strawberry-graphql>=0.262.0`. `AuthMiddlewareStack` puts the session machinery and `scope["user"]` on both protocols, and the package's **read-path** request contract consumes it: [`request_from_info`](#request_from_info) resolves Strawberry's Channels context to the [Channels request adapter](#channels-request-adapter), so `current_user` and the permission gates work over the router; session-mutating [Auth mutations](#auth-mutations) over Channels consumers remain unverified. Not demonstrated in the fakeshop example (WSGI-only, no `asgi.py`) — the tests live in `tests/test_routers.py`, the documented genuinely-unreachable-live case of the [live-first coverage mandate](#live-first-coverage-mandate).

**See also:** [Auth mutations](#auth-mutations) · [`TestClient`](#testclient) · [Soft dependency](#soft-dependency) · [Channels request adapter](#channels-request-adapter) · [`request_from_info`](#request_from_info).

## `DjangoImageType`

**Status:** shipped (`0.0.11`).

Subclasses [`DjangoFileType`](#djangofiletype) and adds nullable `width` / `height` image dimensions, resolved through the same `_safe_file_attr` guard so a missing / corrupt image or a backend that cannot read dimensions degrades them to `null`. An `ImageField` column resolves here (not `DjangoFileType`) via the `FIELD_OUTPUT_TYPE_MAP` MRO precedence — the `ImageField` row precedes the `FileField` row, so the `ImageField` subclass matches its own row first.

**See also:** [`Upload` scalar](#upload-scalar) · [`DjangoFileType`](#djangofiletype).

## `DjangoListField`

**Status:** shipped (`0.0.7`).

Non-Relay `list[T]` **root Query field**. The smallest entry point for migrants coming from `graphene-django`'s `DjangoListField` and for use cases that do not need pagination, edges, or page-info. Implemented as a **factory function** (not a class): consumer usage is `all_branches: list[BranchType] = DjangoListField(BranchType)`, and Strawberry's `@strawberry.type` class-body walk picks up the factory's return value the same way it picks up `strawberry.field(...)`. Outer-list nullability is driven by the consumer's class-attribute annotation — `list[T]` renders as `[T!]!` and `list[T] | None` renders as `[T!]`. The default resolver pulls `target_type.__django_strawberry_definition__.model._default_manager.all()` and applies the type-level [`get_queryset`](#get_queryset-visibility-hook) in both sync and async contexts (the sync path rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults). A consumer-supplied `resolver=` overrides the default body; when its return value is a Django `Manager` or `QuerySet`, the wrapper coerces the `Manager` to a `QuerySet` and applies `target_type.get_queryset(qs, info)` (graphene-django parity), so a custom resolver still honors the visibility hook. Async consumer resolvers are detected at construction time via the partial-aware `is_async_callable` predicate (checked on the resolver, on its `__call__` so callable-instance resolvers with `async def __call__` are covered, and through a one-hop `functools.partial`) and routed through an `async def` wrapper that awaits the coroutine before applying the isinstance check. Python `list` returns from sync or async resolvers pass through unchanged. Optimizer cooperation rides the existing root-gated [`DjangoOptimizerExtension`](#djangooptimizerextension) hook (`info.path.prev is None`), so root-position `DjangoListField` selections receive `select_related` / `prefetch_related` / `only` planning automatically; nested non-root usage is functional but not root-optimized in `0.0.7`. Standard field-level metadata pass-through (`description`, `deprecation_reason`, `directives`) is forwarded into the inner `strawberry.field(...)` call.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) (the Relay-shaped equivalent).

## `DjangoModelFormMutation`

**Status:** shipped (`0.0.12`).

The `ModelForm` mutation base, declared via `Meta.form_class`. It **subclasses** [`DjangoMutation`](#djangomutation), overriding `_resolve_model` to return `Meta.form_class._meta.model`, and so reuses the base value: the primary [`DjangoType`](#djangotype) payload in the uniform `node` / `result` slot, the [`DjangoModelPermission`](#djangomodelpermission) default (authorized for free through the model override), the visibility-scoped `update` locate, and the optimizer re-fetch (the G2 gate keeps `select_related` / `prefetch_related` but suppresses `.only(...)` under the mutation operation). Its input is form-derived rather than model-column derived, and `Meta.operation` is restricted to `"create"` / `"update"` (no form `delete`). Validation runs `form.is_valid()` then `form.save()`; `form.errors` populate the shared [`FieldError` envelope](#fielderror-envelope) (`NON_FIELD_ERRORS` keyed under `"__all__"`) and the post-save row is returned in the uniform slot. Bound at [`finalize_django_types`](#finalize_django_types) phase 2.5 alongside the other [`DjangoMutation`](#djangomutation) bases. Exported from the package root.

An `update` uses a partial GraphQL input but still performs full `ModelForm` validation. The resolver reconstructs every omitted declared field from the located instance, overlays the values the client supplied, and binds that complete data set to the form. Consequently, an untouched stored value that no longer satisfies the current form -- for example, a row written before a validator was tightened -- blocks an otherwise unrelated update. This is deliberate: the framework does not silently exempt invalid fields from `ModelForm` validation. Supply a valid replacement in the same mutation; if `Meta.fields` / `Meta.exclude` removed that field from the generated input, broaden the mutation input or repair the row out of band first.

**See also:** [`DjangoFormMutation`](#djangoformmutation) · [`DjangoMutation`](#djangomutation) · [`FieldError` envelope](#fielderror-envelope).

## `DjangoModelPermission`

**Status:** shipped (`0.0.11`).

The default write-authorization permission class consumers pass to [`DjangoMutation`](#djangomutation)'s `Meta.permission_classes` (which defaults to `[DjangoModelPermission]`). It enforces the Django `add` / `change` / `delete` **model permissions** — `create` requires `add`, `update` requires `change`, `delete` requires `delete` — so an anonymous caller or one missing the relevant model perm is denied. Write authorization is a first-class, DRF-shaped contract run by all three operations through an overridable `check_permission(info, operation, data, instance=None)` hook (`create` runs the check before validation with `instance=None`; `update` / `delete` run it after the visibility lookup with the located instance). It is kept **separate** from [`get_queryset`](#get_queryset-visibility-hook) visibility: can-view ≠ can-write — `get_queryset` scopes which rows are *visible*, `permission_classes` decides whether they may be *written*. A denial raises a top-level `GraphQLError` (not a [`FieldError`](#fielderror-envelope) envelope entry). An *unset* `Meta.permission_classes` resolves to `[DjangoModelPermission]` (the safe default — anonymous denied); an explicit **empty** `Meta.permission_classes = []` disables write authorization entirely (AllowAny), a deliberate opt-out of the safe default that mirrors DRF — there is no accidental route into it, so use `[]` only for an intentionally public write surface. A `check_permission` / `has_permission` hook must be **synchronous** (return a `bool`): the write pipeline runs the auth check synchronously, so an `async def` hook is rejected with a `SyncMisuseError` rather than silently treated as allow. Exported from the package root.

**See also:** [`DjangoMutation`](#djangomutation) · [`get_queryset` visibility hook](#get_queryset-visibility-hook) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [Per-field permission hooks](#per-field-permission-hooks).

## `DjangoMutation`

**Status:** shipped (`0.0.11`).

Base class for the write side, configured through a nested `class Meta` (the DRF shape, not Strawberry decorators). `Meta.model` names the Django model; `Meta.operation` selects the verb — one of `"create"` / `"update"` / `"delete"`. Optional `Meta.fields` / `Meta.exclude` narrow the generated input shape; `Meta.input_class` / `Meta.partial_input_class` supply a hand-written input (which must follow the generated field-naming scheme); `Meta.permission_classes` sets write authorization (see [`DjangoModelPermission`](#djangomodelpermission)). The class is registered at creation and bound at [`finalize_django_types`](#finalize_django_types) phase 2.5, which resolves the model's **primary** [`DjangoType`](#djangotype) for the return payload and materializes the generated [`Input` / `PartialInput`](#input-type-generation) and `<Name>Payload` classes before `strawberry.Schema(...)` runs. The create / update resolver pipeline runs visibility-scoped locate (update only) → authorize → decode → `full_clean()` → write → optimizer-re-fetch → payload, sync and async, with the write inside one `transaction.atomic()` (async via a single `sync_to_async(thread_sensitive=True)`). Authorization deliberately precedes relation decoding so a denied caller cannot probe related-object visibility. Validation failures surface through the shared [`FieldError` envelope](#fielderror-envelope) rather than raising at the GraphQL boundary; permission denial instead raises a top-level `GraphQLError` and nulls the mutation field.

Relation IDs are checked through the related model's registered primary [`DjangoType`](#djangotype) visibility scope when one exists; hidden and missing targets are indistinguishable. An unregistered related model has no GraphQL visibility policy, so raw primary keys receive default-manager existence validation only and any existing row may be attached. Many-to-many values are full replacements: a provided list becomes the complete set, `[]` clears, omission leaves an update unchanged, and `null` is invalid; there is no additive add/remove input shape.

The post-write row is re-fetched and optimizer-planned for the response selection through the default manager, not the target type's visibility queryset (under the mutation operation the G2 gate keeps `select_related` / `prefetch_related` but suppresses [`.only(...)`](#only-projection)). This deliberately lets the actor round-trip the row it just wrote, including an update that moves the row outside its subsequent read visibility. Exposed on the schema's `Mutation` type through the [`DjangoMutationField`](#djangomutationfield) factory. Exported from the package root.

**See also:** [`DjangoMutationField`](#djangomutationfield) · [Input type generation](#input-type-generation) · [`FieldError` envelope](#fielderror-envelope) · [`DjangoModelPermission`](#djangomodelpermission) · [`DjangoFormMutation`](#djangoformmutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`SerializerMutation`](#serializermutation).

## `DjangoMutationField`

**Status:** shipped (`0.0.11`).

Field factory exposing a [`DjangoMutation`](#djangomutation) on the schema's `Mutation` type — the write-side sibling of [`DjangoConnectionField`](#djangoconnectionfield). Assigned to a class attribute with **no** class-attribute annotation (`create_item = DjangoMutationField(CreateItem)`): the return `<Name>Payload` is materialized at finalization and has no importable name at import, so the factory types the field itself via a `strawberry.lazy` forward-ref to the generated payload (resolved at schema build). It synthesizes the per-operation resolver argument signature — `data: <Model>Input!` for create, `id:` + `data: <Model>PartialInput!` for update, `id:` for delete — and dispatches the sync or async resolver via the same async-detection asymmetry [`DjangoListField`](#djangolistfield) uses (`is_async_callable` at construction for a consumer resolver, runtime async-context detection for the default resolver). Exported from the package root.

**See also:** [`DjangoMutation`](#djangomutation) · [`DjangoConnectionField`](#djangoconnectionfield) · [`FieldError` envelope](#fielderror-envelope).

## `DjangoNodeField`

**Status:** shipped (`0.0.9`).

Root single-node refetch field, shipped in two forms: the Relay-spec bare interface form `node: relay.Node | None = DjangoNodeField()` (the literal `node(id: ID!): Node` field) and the typed form `genre: GenreType | None = DjangoNodeField(GenreType)` — both nullable-by-contract (the resolver is dispatched `required=False` unconditionally; the optional annotation is the supported spelling). The synthesized resolver declares `id: strawberry.ID` (a raw string, deliberately not `relay.GlobalID`, so malformed ids reach the package) and decodes **server-side** through the strategy-aware decode dispatch — model-label, type-name, and transitional payloads all resolve, and the client's claim of which type an id belongs to is never trusted. Resolution dispatches to the target type's `resolve_node` default, honoring [`get_queryset`](#get_queryset-visibility-hook): hidden, missing, and uncoercible-pk ids return `null` (the hidden and missing paths share one queryset code path — no existence leak); a malformed id raises `GraphQLError` with `extensions={"code": "GLOBALID_INVALID"}`; the typed form rejects an id that decodes to a different type with a `GraphQLError` naming the expected and received types. A declared node field on a registry with no Relay-Node-shaped types raises [`ConfigurationError`](#configurationerror) at finalization. A schema whose *only* root field is the interface-typed `node` must pass its concrete types via `strawberry.Schema(types=[...])` or expose them through other fields (engine behavior, documented in the field docstring).

**See also:** [`DjangoNodesField`](#djangonodesfield) · [`DjangoConnectionField`](#djangoconnectionfield) · [Relay Node integration](#relay-node-integration) · [`Meta.globalid_strategy`](#metaglobalid_strategy).

## `DjangoNodesField`

**Status:** shipped (`0.0.9`).

Root batch refetch field — the Relay-spec `nodes(ids: [ID!]!): [Node]!` sibling of [`DjangoNodeField`](#djangonodefield), in the same two forms: bare (`nodes: list[relay.Node | None] = DjangoNodesField()`) and typed (`DjangoNodesField(GenreType)`, which additionally runs the per-id declared-target check). Ids are decoded server-side and resolved **per-type batched** (`resolve_nodes` once per distinct type, honoring [`get_queryset`](#get_queryset-visibility-hook)) with input order preserved and duplicate ids supported. Well-formed-but-invisible/missing/uncoercible-pk ids become positional `null` holes; a malformed id — or a wrong-type id in the typed form — anywhere in the batch fails the **whole field** (`GraphQLError`, `GLOBALID_INVALID` for malformed; the `[Node]!` non-null nulls the enclosing `data`). The batch is deliberately uncapped in `0.0.9` (parity with both upstreams; request-size limiting belongs to the consumer's transport layer).

**See also:** [`DjangoNodeField`](#djangonodefield) · [Relay Node integration](#relay-node-integration) · [`get_queryset` visibility hook](#get_queryset-visibility-hook).

## `DjangoOptimizerExtension`

**Status:** shipped (`0.0.2`).

Strawberry schema extension that translates selected GraphQL fields into Django ORM optimization calls. Opt-in at Strawberry schema construction time:

```python
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])
```

Use a module-level singleton wrapped in a factory — that preserves the instance-bound [Plan cache](#plan-cache) (Strawberry runs the callable per request and gets the same instance back) and emits no deprecation warning (the entry is a callable, not an instance).

Shipped behavior:

- root-gated optimization for root resolvers returning Django `QuerySet`s
- `Manager` shorthand coercion (`return Model.objects` is coerced via `.all()` and optimized as if the consumer had written `Model.objects.all()`)
- passthrough for non-root resolvers and non-`QuerySet` results
- `select_related` for safe single-valued relation chains
- `prefetch_related` for many-side relations
- generated `Prefetch` objects for child querysets
- nested prefetch chains for nested GraphQL selections
- [`only`](#only-projection) projection for selected scalar columns
- connector-column inclusion so Django can attach joined and prefetched rows without lazy loads
- [FK-id elision](#fk-id-elision) for forward-FK selections that touch only the target's `id`
- custom [`get_queryset`](#get_queryset-visibility-hook) downgrade from join to `Prefetch`
- async resolver support
- multi-type plan-cache separation: primary-return and secondary-return resolvers on the same Django model receive distinct cache entries via the resolver's origin Strawberry type
- evaluated-queryset pass-through (G1, `0.0.10`): if the consumer's root resolver already evaluated the queryset (`len(qs)`, `bool(qs)`, slicing), `_optimize` returns it unchanged rather than re-executing it through an `.only()` / `select_related` clone
- non-`QUERY` column-projection suppression (G2, `0.0.10`): for mutation / subscription operations the optimizer applies no [`only`](#only-projection) column deferral at plan-build time — `select_related` / `prefetch_related` still apply, but the returned queryset carries no selection-shaped deferred-field set

What the optimizer will not touch: a queryset the consumer already evaluated (G1), and column projection on non-`QUERY` operations (G2).

Constructor accepts a `strictness` argument — see [Strictness mode](#strictness-mode). Classmethod [`check_schema`](#schema-audit) audits schema-reachable `DjangoType`s.

**See also:** [`OptimizerHint`](#optimizerhint) · [`Meta.optimizer_hints`](#metaoptimizer_hints) · [Plan cache](#plan-cache) · [FK-id elision](#fk-id-elision) · [`only()` projection](#only-projection) · [Queryset diffing](#queryset-diffing) · [Strictness mode](#strictness-mode) · [Schema audit](#schema-audit) · [Multi-database cooperation](#multi-database-cooperation).

## `DjangoType`

**Status:** shipped (`0.0.5`).

Model-backed Strawberry type base class. Each subclass declares a nested `class Meta` referencing a Django model; the class is registered at definition time and decorated with `strawberry.type` at finalization. The primary public surface.

```python
from django_strawberry_framework import DjangoType

class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
```

Shipped capability:

- model field selection with [`Meta.fields`](#metafields) and [`Meta.exclude`](#metaexclude)
- default `fields = "__all__"` when neither selector is supplied
- GraphQL type-name and description overrides via [`Meta.name`](#metaname) / [`Meta.description`](#metadescription)
- scalar annotation generation (see [Scalar field conversion](#scalar-field-conversion))
- relation annotation generation (see [Relation handling](#relation-handling))
- choice enum generation (see [Choice enum generation](#choice-enum-generation))
- type registry registration
- definition-order-independent relation finalization (see [Definition-order independence](#definition-order-independence))
- abstract / intermediate base support when a subclass has no `Meta`
- multiple `DjangoType`s per Django model supported via [`Meta.primary`](#metaprimary)

Current alpha constraints:

- manual override validation for relation cardinality is deferred; the package trusts relation-field annotations supplied by the consumer

`Meta` validation: unknown `Meta` keys raise [`ConfigurationError`](#configurationerror); deferred `Meta` keys are rejected until the feature that owns them ships.

Validation contracts (errors surface as [`ConfigurationError`](#configurationerror) at type-creation time):

- **`Meta.interfaces` shape and contents.** Tuple/list of Strawberry interface classes, or a single interface class. Strings, sets, dicts, generators, `DjangoType` subclasses, duplicates, and non-`@strawberry.interface` / non-`relay`-interface classes are rejected with messages naming the offending value.
- **Relay-`id` collision guard.** When the type is Relay-Node-shaped (via `Meta.interfaces = (relay.Node,)` or direct inheritance), declaring `id = strawberry.field(...)` or an `id` annotation that is not `relay.NodeID[<pk_type>]` raises. Escape hatches: `@classmethod resolve_id` for a custom id resolver, `id: relay.NodeID[<pk_type>]` for a custom id annotation, a resolver-backed sibling field (e.g. `display_id`) for GraphQL field-level metadata, or remove `relay.Node` from `Meta.interfaces`.
- **Consumer-override surface (scalar and relation, annotation and assignment).** A consumer-written annotation (`category: AdminCategoryType`, `description: int`) or `strawberry.field(...)` assignment (`category = strawberry.field(resolver=...)`, `description = strawberry.field(resolver=...)`) on either a relation column or a scalar column is preserved; the four cases collectively form the `consumer_authored_fields` short-circuit. Non-`StrawberryField` class attributes that shadow a Django field name raise with a message naming the field, the column kind, and the remediation.

**See also:** all [`Meta.*`](#index) keys · [`finalize_django_types`](#finalize_django_types) · [Definition-order independence](#definition-order-independence) · [Relay Node integration](#relay-node-integration).

## Eviction-simulated absence

**Status:** shipped (`0.0.13`).

The [soft-dependency](#soft-dependency) test discipline: a dependency's absence is **simulated** inside the one dev environment — a `builtins.__import__` block plus strict `sys.modules` eviction with full restore (`tests/rest_framework/test_soft_dependency.py`; reused by the `0.0.14` channels card) — never a separate uninstalled CI matrix (one env, one `uv run pytest` gate).

Two refinements the channels card pins. The restore is **two-sided**: a blocked-then-retried import re-executes the module and rebinds the parent package's attribute to a fresh module object, so the fixture saves/restores the parent attribute together with the `sys.modules` entries, putting the *original module object* back in both places — otherwise the attribute path and the import path hold two live modules with independent caches, an order-dependent identity flake under `pytest-xdist`. And eviction is also how **degraded** (present-but-incompatible) installs are tested: evicting the module drops its module-global class cache (`_ROUTER_CLASS`) with it, so a blocked builder import actually fires regardless of earlier construction tests. The install hint is drift-checked against a **re-typed literal** in the test file (the `_HINT_SUBSTRING` discipline) — a test asserting the imported constant against itself could never notice the hint drifting from the dev-group floor.

**See also:** [Soft dependency](#soft-dependency) · [`SerializerMutation`](#serializermutation) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter).

## `FieldError` envelope

**Status:** shipped (`0.0.11`).

Shared `errors: list[FieldError]` envelope returned by every mutation flavor — [`DjangoMutation`](#djangomutation) and (reusing it unchanged) the `0.0.12` [`DjangoFormMutation`](#djangoformmutation) / [`DjangoModelFormMutation`](#djangomodelformmutation) and the `0.0.13` [`SerializerMutation`](#serializermutation) / [Auth mutations](#auth-mutations). The public `FieldError` `@strawberry.type` carries a `field: str` path and `messages: list[str]` (graphene-django's `ErrorType` shape). It is surfaced through a generated `<Name>Payload` wrapper that carries the mutated object in a uniform slot — `node` for a Relay-Node target, `result` for a non-Node target, never a model-derived name — plus `errors: list[FieldError]!`. A `full_clean()` `ValidationError` (including a `validate_constraints()` `UniqueConstraint` violation caught before `save()`, with multi-field constraints keyed to Django's `"__all__"` non-field sentinel) populates the envelope and returns a null object rather than raising at the GraphQL boundary; a concurrent-race `IntegrityError` maps to the same envelope as a documented fallback. (A write-authorization denial is a top-level `GraphQLError`, **not** a `FieldError` entry — see [`DjangoModelPermission`](#djangomodelpermission).) The type is **defined and frozen here** so the downstream flavor cards reuse the byte-identical shape.

**See also:** [`DjangoMutation`](#djangomutation) · [Input type generation](#input-type-generation) · [`DjangoModelPermission`](#djangomodelpermission) · [`DjangoFormMutation`](#djangoformmutation) · [`SerializerMutation`](#serializermutation).

## `FieldSet`

**Status:** planned for `0.1.1`.

Declarative field-selection class for the [`Meta.fields_class`](#metafields_class) surface. Carries field-level permission checks ([`check_*_permission`](#per-field-permission-hooks) denial gates), custom field resolvers (`resolve_*` overrides), computed fields (class-level annotations), and redaction / deny-value behavior. Integrates with generated model fields; declared per-type via `Meta.fields_class = MyTypeFieldSet`.

**See also:** [`Meta.fields_class`](#metafields_class) · [Per-field permission hooks](#per-field-permission-hooks).

## `FilterSet`

**Status:** shipped (`0.0.8`).

Declarative filter classes with `Meta.model`, `Meta.fields` (dict form `{"name": ["exact", "icontains"]}` or `"__all__"` shorthand), [`RelatedFilter`](#relatedfilter) for cross-relation traversal (accepts class, absolute import path, or unqualified name for circular cases), `check_*_permission` denial gates with **active-input-only scope** (per-field gates fire only when the consumer's input names the field), and explicit-`queryset=` **filter-scope constraint** (NOT a security boundary; visibility / security is the job of [`get_queryset`](#get_queryset-visibility-hook), not `RelatedFilter(queryset=...)`). Logical `and` / `or` / `not` operators on the input shape. Generated input types use stable class-derived names so two connection fields on the same model resolve to the same `FilterInputType` (Apollo cache friendly).

The lazy-resolution architecture is borrowed verbatim from `django-graphene-filters` — a cycle-safe six-layer pipeline; five layers are library-agnostic and port directly, only Layer 5's cycle-safe forward reference (Graphene's `lambda:` → Strawberry's `Annotated["TypeName", strawberry.lazy("django_strawberry_framework.filters.inputs")]`) is engine-adapted. `FilterSet` IS a `django_filters.filterset.BaseFilterSet` subclass, so every `Filter` / `FilterMethod` / form-cleaning primitive from `django-filter` carries over.

The resolver-facing API is the classmethod pair `FilterSet.apply_sync(input_value, queryset, info)` and `FilterSet.apply_async(input_value, queryset, info)` — sync resolvers call the former, async resolvers await the latter. The apply pipeline derives child visibility querysets from each ACTIVE [`RelatedFilter`](#relatedfilter) branch's target [`DjangoType.get_queryset(...)`](#get_queryset-visibility-hook) so a nested filter cannot match a parent through a child the visibility hook would hide; extracts the request from `info.context.request`; explicitly calls `filterset.form.is_valid()` and raises `GraphQLError("Invalid filter input", extensions={"code": "FILTER_INVALID", "errors": filterset.errors.get_json_data()})` on failure.

**See also:** [`Meta.filterset_class`](#metafilterset_class) · [`RelatedFilter`](#relatedfilter) · [`filter_input_type`](#filter_input_type) · [`OrderSet`](#orderset).

## `filter_input_type`

**Status:** shipped (`0.0.8`).

Consumer helper for resolver-argument annotations. `filter_input_type(BranchFilter)` returns `Annotated["BranchFilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` — the lazy-resolution shape Strawberry consumes when constructing the schema. The helper validates eagerly (`TypeError` for non-[`FilterSet`](#filterset) arguments) and records the FilterSet against an internal `_helper_referenced_filtersets` ledger so [`finalize_django_types`](#finalize_django_types) can fail loudly for orphans — FilterSets passed to `filter_input_type` but never wired via [`Meta.filterset_class`](#metafilterset_class) — at finalize time.

Consumer usage on a plain `@strawberry.field` resolver:

```python
from django_strawberry_framework.filters import filter_input_type
from apps.library.filters import BranchFilter


@strawberry.type
class Query:
    @strawberry.field
    def all_library_branches(
        self,
        info,
        filter: filter_input_type(BranchFilter) | None = None,
    ) -> list[BranchType]:
        queryset = BranchType.get_queryset(Branch.objects.all(), info)
        if filter is not None:
            queryset = BranchFilter.apply_sync(filter, queryset, info)
        return queryset
```

**See also:** [`FilterSet`](#filterset) · [`Meta.filterset_class`](#metafilterset_class).

## `finalize_django_types`

**Status:** shipped (`0.0.4`).

Synchronization point that resolves pending relation annotations and applies `strawberry.type(cls, ...)` decoration to every collected `DjangoType`. Required because Strawberry resolves field annotations eagerly at decoration time, while Django relations may target a `DjangoType` whose module hasn't been imported yet.

Call it once during single-threaded schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed:

```python
from django_strawberry_framework import finalize_django_types
import apps.products.schema  # registers DjangoType subclasses
import apps.library.schema

finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])
```

Calling it a second time is a no-op. The collected type registry and finalized flag are
process-global, and finalization mutates the collected Python classes in place. A process therefore
has one schema-build lifecycle: multiple `strawberry.Schema` objects may reuse that same finalized
type set, but disjoint independently finalized type sets in one interpreter are unsupported.
Declaring a new concrete `DjangoType` after finalization raises
[`ConfigurationError`](#configurationerror); tests that need a new registry lifecycle should use
`registry.clear()` and fresh type classes, because clearing the registry cannot undo mutations on
classes from the prior lifecycle.

**See also:** [Definition-order independence](#definition-order-independence) · [`DjangoType`](#djangotype) · [`ConfigurationError`](#configurationerror).

## FK-id elision

**Status:** shipped (`0.0.3`).

For `{ category { id } }` and similar `id`-only forward-relation selections, the optimizer reads the FK column off the parent row — no JOIN, no second query, no Python attribute access on a related instance.

Safety properties:

- falls back to a join when the target selection needs more than the primary key
- falls back when the target ID has a custom resolver
- falls back when a target [`get_queryset`](#get_queryset-visibility-hook) hook must run
- branch-isolated: aliases and sibling root fields do not leak elision state into each other

FK-id elisions are stashed on `info.context.dst_optimizer_plan.fk_id_elisions` (tuple, as part of the plan) and `info.context.dst_optimizer_fk_id_elisions` (standalone set, for resolver-time membership checks).

As of `0.0.10`, elision stays enabled under non-`QUERY` operations, with a consumer-`.only()` loaded-check: a consumer-returned `.only(...)` queryset survives queryset diffing and can defer the FK column even when the optimizer suppresses its own `.only()`, so the elision stub verifies the FK column is loaded on the parent row and falls back loudly ([strictness](#strictness-mode)-visible) when a consumer projection deferred it, rather than a silent per-row lazy load.

**See also:** [`only()` projection](#only-projection) · [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Plan cache](#plan-cache).

## `get_child_queryset`

**Status:** planned for `0.1.3`.

Cascade hook on [`AggregateSet`](#aggregateset) called when aggregation traverses into a child queryset (via [`RelatedAggregate`](#relatedaggregate)). Lets consumers exclude private rows before they contribute to `Count` / `Sum` / `Avg` / etc., parallel to how [`apply_cascade_permissions`](#apply_cascade_permissions) gates filter traversal.

**See also:** [`AggregateSet`](#aggregateset) · [`RelatedAggregate`](#relatedaggregate) · [`apply_cascade_permissions`](#apply_cascade_permissions).

## `get_queryset` visibility hook

**Status:** shipped (`0.0.1`).

`DjangoType.get_queryset(cls, queryset, info, **kwargs)` runs once per type, defaults to identity, and is where permission filters, tenant scoping, soft-delete, staff/public visibility splits, and request-user filters live:

```python
class ItemType(DjangoType):
    class Meta:
        model = Item

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return queryset.filter(is_private=False)
```

The load-bearing behavior is optimizer cooperation: `has_custom_get_queryset()` reports whether a type or inherited intermediate base overrides the hook, and the optimizer downgrades a JOIN to a `Prefetch` when a target type defines one. Your visibility filter survives relation traversal instead of being bypassed by a raw `select_related` join. A type's `get_queryset` is also the seam [`apply_cascade_permissions`](#apply_cascade_permissions) composes: the cascade is called *from inside* this hook to reach the type's single-column forward FK / OneToOne targets, running each target type's own `get_queryset` to narrow which parent rows stay visible. Inheritance through an abstract base that overrides `get_queryset` without declaring `Meta` is supported — the sentinel flip runs before the `meta is None` early-return so the abstract-shared-base pattern reports correctly on concrete subclasses.

**See also:** [`apply_cascade_permissions`](#apply_cascade_permissions) · [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Per-field permission hooks](#per-field-permission-hooks).

## Graphene debug migration

**Status:** planned for `0.0.14`.

The concrete migration from graphene-django's debug subsystem to [`DjangoDebugExtension`](#djangodebugextension). The Graphene project-level pair is an aggregate `_debug: DjangoDebug` query field plus `graphene_django.debug.DjangoDebugMiddleware` in `GRAPHENE["MIDDLEWARE"]`; `DjangoDebugSQL` and `DjangoDebugException` define its selected row shapes. The Strawberry migration removes the field and middleware setting, adds `DjangoDebugExtension` to the aggregate schema's `extensions=` list, and changes clients from selecting `_debug` to reading `response.extensions.debug`. Domain app schemas and `Meta` declarations remain unchanged. This is capability parity, not wire compatibility.

**See also:** [Cookbook parity](#cookbook-parity) · [Single-upstream parity](#single-upstream-parity) · [Debug SQL row](#debug-sql-row) · [Debug exception row](#debug-exception-row).

## `GraphQLTestCase`

**Status:** planned for `0.0.14`.

The `graphene-django`-shaped unittest family: `GraphQLTestMixin` (the reusable mixin) plus its two concrete two-line combinations `GraphQLTestCase` (`(GraphQLTestMixin, django.test.TestCase)`) and `GraphQLTransactionTestCase` (`(GraphQLTestMixin, django.test.TransactionTestCase)`), imported from `django_strawberry_framework.testing`. The mixin's `self.query(...)` delegates to a [`TestClient`](#testclient) built over the test case's own `self.client` (so login / cookie state applies and the body-building lives in one place), returning the typed `Response`; it defaults `assert_no_errors=False` (graphene parity - the flipped default from the pytest-flavored [`TestClient`](#testclient)). The assertion helpers keep graphene's names and semantics: `assertResponseNoErrors` (HTTP 200 **and** no `errors`) and `assertResponseHasErrors` (an `errors` key present - GraphQL still returns HTTP 200). The per-class `GRAPHQL_URL` endpoint knob outranks the `TESTING_ENDPOINT` settings key and is itself outranked by a per-call `url=`. There is deliberately **no** `mutate()` helper - a mutation posts through `query()` like any operation (neither upstream ships one). The `GraphQLTestCase` name and mixin-first shape come from `graphene-django`'s `utils/testing.py`; the underlying HTTP client mirrors `strawberry-django`'s `test/client.py`.

**See also:** [`TestClient`](#testclient).

## Hard dependency

**Status:** shipped.

A package installed unconditionally with `django-strawberry-framework`, so package code may import it without an optional-import guard or install hint. Django and `strawberry-graphql` are hard dependencies. Spec 044 adds no dependency: `SchemaExtension` comes from the existing Strawberry requirement and SQL capture comes from Django; it only raises the Strawberry version floor for [Per-operation extension isolation](#per-operation-extension-isolation). This is the opposite of a [Soft dependency](#soft-dependency), whose feature boundary must remain import-clean when the extra is absent.

**See also:** [Soft dependency](#soft-dependency) · [`require_optional_module`](#require_optional_module) · [Per-operation extension isolation](#per-operation-extension-isolation).

## Input type generation

**Status:** shipped (`0.0.11`).

[`DjangoMutation`](#djangomutation) auto-generates two input types from the model's **editable** fields (narrowed by the mutation's own `Meta.fields` / `Meta.exclude` — **not** the read-side [`DjangoType`](#djangotype) selection), reusing the read-side scalar / choice-enum / specialized-scalar converters so read and write share one wire contract:

- **`<Model>Input`** — the create shape (`Model.objects.create(...)` semantics). A field is required only when it has no usable Django `default`, is not `null=True`, and (for text fields) is not `blank=True`; fields that do have a default / blank / null are optional (`strawberry.UNSET`). This is the DRF `required=False`-from-`default`/`blank`/`null` rule, not a blanket "every field required".
- **`<Model>PartialInput`** — every field optional, `UNSET`-defaulted (matches `Model.objects.update(...)` semantics).

Editable-field selection drops the pk, `auto_now` / `auto_now_add` / `editable=False` columns, and reverse relations. A forward FK / OneToOne becomes a single `<field>_id` typed as the target's id — a `GlobalID` for a Relay-Node target, the raw pk scalar otherwise — type-checked against the relation target at decode (a wrong-type id is a [`FieldError`](#fielderror-envelope), never a cross-model pk lookup); an M2M becomes `list[<id>]` (replace-on-provide / clear-on-empty / unchanged-on-omit). The canonical full editable shape takes the stable `<Model>Input` / `<Model>PartialInput` name; a narrowed (`Meta.fields` / `Meta.exclude`) shape takes a deterministic shape-derived name, and two **distinct** shapes colliding on one generated name raise [`ConfigurationError`](#configurationerror) at finalization (identical shapes dedupe and share one type). All are materialized as module globals. The relation-override contract from `spec-010` holds: a consumer-authored input field is honored, not clobbered by a generated one.

**See also:** [`DjangoMutation`](#djangomutation) · [`FieldError` envelope](#fielderror-envelope) · [`Upload` scalar](#upload-scalar).

## Joint version cut

**Status:** shipped (`0.0.13`).

The release rule when multiple kanban cards share one patch version: the version bump and the public release-status wording are owned by the **last** card to land — the joint cut — never by an individual card's slices. First applied at the joint `0.0.13` cut ([`SerializerMutation`](#serializermutation) + [Auth mutations](#auth-mutations)); in force for `0.0.14`, where four cards share the line ([`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter), [Debug-toolbar middleware](#debug-toolbar-middleware), [`TestClient`](#testclient) / [`GraphQLTestCase`](#graphqltestcase), and [Response-extensions debug middleware](#response-extensions-debug-middleware)).

Moved only by the cut — the version quintet: `[project].version` in `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, this glossary's package-version line, and the package's own `version` entry in `uv.lock`. Also deferred to the cut: the glossary status flips to `shipped (...)`, the `README.md` / `docs/README.md` "Coming next" → "Shipped today" moves, and the `CHANGELOG.md` bullets (which additionally require an explicit maintainer grant). `uv.lock` **dependency** entries are not version state — a card's own dependency-gate lock regeneration lands with that card.

## Live-first coverage mandate

**Status:** shipped (`0.0.4`).

The repo's test-placement rule (pinned in `AGENTS.md` and `docs/TREE.md` #"Coverage priority"; established by the `0.0.4` testing shift): if a package line can be covered by a real fakeshop `/graphql/` GraphQL request, the covering test lives in the live acceptance suite (`examples/fakeshop/test_query/`); root `tests/` is reserved for package internals, invalid configuration, registry/finalizer mechanics, and paths genuinely unreachable through a realistic GraphQL request. Mock only when the real path is impossible.

A package-tests placement for new surface area must be justified as genuinely-unreachable-live — e.g. the `0.0.14` [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter): the fakeshop example is WSGI-only (no `asgi.py`), so no live request can reach a Channels router line. When coverage is later promoted to the live tier, the package-only stand-in test is deleted rather than kept as duplicate weight (the package coverage gate, `fail_under = 100`, keeps the swap honest).

## Masking-extension ordering

**Status:** planned for `0.0.14`.

The ordering contract between [`DjangoDebugExtension`](#djangodebugextension) and an error-masking `SchemaExtension` such as Strawberry's `MaskErrors`. Extension context teardowns unwind last-in, first-out. `MaskErrors` replaces result errors with copies whose `original_error` is `None`; therefore the debug class must be listed **after** the masker so debug teardown runs first and records the original exception. Reversing the order yields an empty debug `exceptions` list. Even with correct ordering, the standard GraphQL `errors` remain masked while the debug payload is deliberately unmasked.

**See also:** [Debug exception row](#debug-exception-row) · [Developer-only debug posture](#developer-only-debug-posture) · [Strawberry extension lifecycle](#strawberry-extension-lifecycle).

## `Meta.aggregate_class`

**Status:** planned for `0.1.3`.

References an [`AggregateSet`](#aggregateset) subclass that defines aggregates for this `DjangoType`. Surfaces as `aggregates` arguments on [`DjangoConnectionField`](#djangoconnectionfield).

```python
class GalaxyType(DjangoType):
    class Meta:
        model = Galaxy
        aggregate_class = aggregates.GalaxyAggregate
```

**See also:** [`AggregateSet`](#aggregateset).

## `Meta.choice_enum_names`

**Status:** planned for `0.1.4`.

`Meta.choice_enum_names = {"status": "ItemStatusEnum"}` overrides the first-`DjangoType`-wins enum-naming behavior that ships today. Pins a stable contract for renaming generated choice enums.

**See also:** [Choice enum generation](#choice-enum-generation).

## `Meta.connection`

**Status:** shipped (`0.0.9`).

Relay-connection options for a `DjangoType`. In `0.0.9`, the accepted shape is `{"total_count": bool}` and the key is valid only on a Relay-Node-shaped type — when [`Meta.interfaces`](#metainterfaces) includes `strawberry.relay.Node`, or the type inherits `relay.Node` directly.

When `total_count` is true, [`DjangoConnectionField`](#djangoconnectionfield) resolves the type through a concrete per-target connection class exposing `totalCount`; otherwise it uses [`DjangoConnection`](#djangoconnection)`[T]` without that field. The option is type-level, not per field, so a node type has one stable connection shape.

```python
class GenreType(DjangoType):
    class Meta:
        model = Genre
        interfaces = (relay.Node,)
        connection = {"total_count": True}
```

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [`DjangoConnection`](#djangoconnection) · [Relay Node integration](#relay-node-integration) · [`Meta.interfaces`](#metainterfaces).

## `Meta.description`

**Status:** shipped.

Overrides the GraphQL type description (defaults to the class docstring).

**See also:** [`DjangoType`](#djangotype) · [`Meta.name`](#metaname).

## `Meta.exclude`

**Status:** shipped.

Tuple / list of model field names to exclude from the generated GraphQL type. Mutually exclusive with the all-fields default of [`Meta.fields`](#metafields). Validated against the model — unknown names raise [`ConfigurationError`](#configurationerror).

**See also:** [`Meta.fields`](#metafields) · [`DjangoType`](#djangotype).

## `Meta.fields`

**Status:** shipped.

Tuple / list of model field names, or `"__all__"`, or omitted (defaults to `"__all__"`). Names must reference real model fields or shipped relation accessors. Mixing scalar fields and relation fields is allowed.

**See also:** [`Meta.exclude`](#metaexclude) · [`DjangoType`](#djangotype) · [Relation handling](#relation-handling).

## `Meta.fields_class`

**Status:** planned for `0.1.1`.

References a [`FieldSet`](#fieldset) subclass that defines field-level permission checks, custom resolvers, computed fields, and redaction behavior for this `DjangoType`.

**See also:** [`FieldSet`](#fieldset) · [Per-field permission hooks](#per-field-permission-hooks).

## `Meta.filterset_class`

**Status:** shipped (`0.0.8`).

References a [`FilterSet`](#filterset) subclass that defines the filter input for this [`DjangoType`](#djangotype). The key is the consumer-facing wiring seam: declaring `Meta.filterset_class = MyFilter` promotes the binding out of `DEFERRED_META_KEYS`, validates the class is a `FilterSet` subclass at type-creation time, and routes through [`finalize_django_types`](#finalize_django_types) phase 2.5 — which binds the owner (`filterset_class._owner_definition = definition`), validates owner compatibility, calls `filterset_cls.get_filters()` (Layer 4 expansion), runs the BFS argument factory (Layer 5), and materializes every generated input class as a module global of `django_strawberry_framework.filters.inputs` before `strawberry.Schema(...)` runs. Consumers reach the resulting filter input from a resolver via [`filter_input_type`](#filter_input_type).

```python
class GalaxyType(DjangoType):
    class Meta:
        model = Galaxy
        filterset_class = filters.GalaxyFilter
```

**See also:** [`FilterSet`](#filterset) · [`filter_input_type`](#filter_input_type).

## `Meta.globalid_strategy`

**Status:** shipped (`0.0.9`).

A net-new, Relay-Node-gated `Meta` key selecting how a [`DjangoType`](#djangotype) encodes the type-name slot of its Relay `GlobalID`. Valid only when [`Meta.interfaces`](#metainterfaces) includes `strawberry.relay.Node`; declaring it on a non-Relay-Node type raises [`ConfigurationError`](#configurationerror). The four strategies:

- `"model"` (the `0.0.9` default) — the Django model label `app_label.modelname:<pk>` (e.g. `products.item:42`), so renaming a GraphQL type never invalidates a cached id.
- `"type"` — the GraphQL type name ([`Meta.name`](#metaname) or the class name), byte-identical to the pre-`0.0.9` payload; the opt-out for type-scoped auth / cache scopes and standard-Relay interop.
- `"type+model"` — transitional: emits the model-anchored payload while decoding both old type-anchored and new model-anchored ids, the bridge for a deployed schema.
- a callable `(type_cls, model, root, info) -> str` — a fully custom type-name slot (encode-only in `0.0.9`); arity and sync-ness are validated at type-creation time and a non-`str` return raises [`ConfigurationError`](#configurationerror).

Precedence is `Meta.globalid_strategy` → [`RELAY_GLOBALID_STRATEGY`](#relay_globalid_strategy) → `"model"`, resolved once at finalization and frozen for the schema's lifetime.

```python
class ItemType(DjangoType):
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        globalid_strategy = "type+model"
```

**See also:** [`RELAY_GLOBALID_STRATEGY`](#relay_globalid_strategy) · [Relay Node integration](#relay-node-integration) · [`Meta.interfaces`](#metainterfaces) · [`Meta.name`](#metaname) · [`ConfigurationError`](#configurationerror).

## `Meta.interfaces`

**Status:** shipped (`0.0.5`).

Tuple of Strawberry interface classes the generated GraphQL type implements. When `strawberry.relay.Node` is among them, the `DjangoType` becomes a Relay-node-shaped type — see [Relay Node integration](#relay-node-integration) for the full contract.

```python
import strawberry
from strawberry import relay

class CategoryNode(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        interfaces = (relay.Node,)
```

Non-Relay Strawberry interfaces (`@strawberry.interface`-decorated classes) are accepted without Relay-specific wiring.

**See also:** [Relay Node integration](#relay-node-integration) · [`DjangoType`](#djangotype).

## `Meta.model`

**Status:** shipped.

The Django model class this `DjangoType` is generated from. Required for every concrete `DjangoType`. Abstract base `DjangoType`s without a `Meta` are allowed and do not register.

**See also:** [`DjangoType`](#djangotype) · [`Meta.primary`](#metaprimary).

## `Meta.name`

**Status:** shipped.

Overrides the GraphQL type name (defaults to the Python class name).

**See also:** [`DjangoType`](#djangotype) · [`Meta.description`](#metadescription).

## `Meta.nullable_overrides`

**Status:** shipped (`0.0.9`).

Tuple / list of **non-relation** field names whose GraphQL nullability is forced to nullable (`T` → `T | None`) regardless of the Django column's `null`. The companion [`Meta.required_overrides`](#metarequired_overrides) forces the opposite direction (`T | None` → `T`). Together they decouple a non-relation field's GraphQL nullability from its database column without an `AlterField` migration or a consumer-authored annotation:

```python
class NullabilityOverrideBookType(DjangoType):
    class Meta:
        model = Book
        fields = ("id", "title", "subtitle")
        nullable_overrides = ("title",)     # NOT NULL column -> String
        required_overrides = ("subtitle",)  # null=True column -> String!
```

The override threads a tri-state `force_nullable` into [Scalar field conversion](#scalar-field-conversion)'s `convert_scalar`, so the widening decision is computed once and applied uniformly across plain scalars, [choice enums](#choice-enum-generation) (the enum's nullability flips; its members are unchanged), `ArrayField` (the outer `list[inner]` nullability flips; the inner element nullability still follows `base_field.null`), and `HStoreField`.

**Non-relation scope.** The override applies to non-relation model fields — scalar columns and, as of `0.0.11`, the file/image output objects (`required_overrides` forces a non-null `DjangoFileType!`). Relation-field overrides are rejected (deferred — the many-side list-vs-element nullability ambiguity is its own design).

**Validation at type creation** (every failure raises [`ConfigurationError`](#configurationerror) naming the field):

- **unknown** — a name not on `model._meta` (mirrors the [`Meta.optimizer_hints`](#metaoptimizer_hints) typo guard).
- **excluded** — a name not in the post-[`Meta.fields`](#metafields) / [`Meta.exclude`](#metaexclude) selected set (kept distinct from *unknown* so the [`Meta.exclude`](#metaexclude) contract is not collapsed).
- **consumer-authored** — a name with a consumer annotation / `strawberry.field` assignment (the annotation already controls nullability per [Scalar field override semantics](#scalar-field-override-semantics)).
- **relation** — a relation field name (non-relation scope).
- **Relay-suppressed pk** — the pk on a [`relay.Node`](#metainterfaces)-shaped type (its nullability is the interface's `id: GlobalID!` contract).
- **both-sets collision** — a name in both `nullable_overrides` and `required_overrides` (contradictory; raised at the shape stage).

**See also:** [`Meta.required_overrides`](#metarequired_overrides) · [Scalar field conversion](#scalar-field-conversion) · [Scalar field override semantics](#scalar-field-override-semantics) · [Choice enum generation](#choice-enum-generation) · [`ConfigurationError`](#configurationerror).

## `Meta.optimizer_hints`

**Status:** shipped (`0.0.3`).

Per-relation optimizer overrides — a dict mapping relation field name to an [`OptimizerHint`](#optimizerhint) instance. Configured in the same `class Meta` you already declared the type with:

```python
from django.db.models import Prefetch
from django_strawberry_framework import DjangoType, OptimizerHint

class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")
        optimizer_hints = {
            "items": OptimizerHint.prefetch(
                Prefetch("items", queryset=Item.objects.filter(is_published=True)),
            ),
        }
```

Validation: hint field names must exist on the model; hint values must be `OptimizerHint` instances; invalid hints fail at type creation with [`ConfigurationError`](#configurationerror).

**See also:** [`OptimizerHint`](#optimizerhint) · [`DjangoOptimizerExtension`](#djangooptimizerextension).

## `Meta.orderset_class`

**Status:** shipped (`0.0.8`).

References an [`OrderSet`](#orderset) subclass that defines ordering input for this `DjangoType`. Describes the consumer-facing wiring and the promotion-from-`DEFERRED_META_KEYS` gate.

Consumer wiring: declaring `Meta.orderset_class = MyOrder` surfaces an `orderBy: [<T>OrderInputType!]` argument on plain `@strawberry.field` resolvers that opt in via `order_by: list[order_input_type(MyOrder)] | None = None` (and on [`DjangoConnectionField`](#djangoconnectionfield), which resolves ordering from this already-resolved sidecar directly). The argument is list-shaped — list-element order is the multi-field tie-breaker mechanism.

Promotion gate: no longer in `DEFERRED_META_KEYS` since `0.0.8`. Declaring the key against `0.0.7` raised a [`ConfigurationError`](#configurationerror); against `0.0.8` it produces a working order surface. Finalizer phase 2.5 owns the binding via `_bind_ordersets()`: each declared `Meta.orderset_class` value has its `_owner_definition` wired to the owning [`DjangoType`](#djangotype), its `get_fields()` resolved after all owners are bound, and the generated input class materialized as a module global of `django_strawberry_framework.orders.inputs` before `strawberry.Schema(...)` runs.

**See also:** [`OrderSet`](#orderset) · [`RelatedOrder`](#relatedorder) · [`order_input_type`](#order_input_type) · [`Ordering`](#ordering) · [`finalize_django_types`](#finalize_django_types).

## `Meta.primary`

**Status:** shipped (`0.0.6`).

Boolean flag (default `False`) declared on a `DjangoType`'s nested `Meta` to opt one of several types on the same Django model into the **primary** role. The primary type is the one auto-synthesized relation fields resolve to and the one [`registry.get(model)`](#djangotype) returns. Secondary types are still registered and reverse-discoverable via `registry.model_for_type(SecondaryType)`, so resolvers returning a secondary type stay planable through [`DjangoOptimizerExtension`](#djangooptimizerextension).

Ambiguity rules:

- One `DjangoType` for a model, `Meta.primary` absent or `False` — allowed (backward compat).
- Multiple `DjangoType`s, exactly one with `Meta.primary = True` — allowed; relation targets resolve to the primary.
- Multiple `DjangoType`s, two or more with `Meta.primary = True` — rejected at the second registration: `ConfigurationError("Cannot register <class> as primary for <model>; <existing> is already the primary type")`.
- Multiple `DjangoType`s, none with `Meta.primary = True` — rejected at [`finalize_django_types()`](#finalize_django_types): `ConfigurationError` listing the model and every registered class, with fix sentence `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`.

Registry surface: `primary_for(model)` returns the declared primary or `None`; `types_for(model)` returns the tuple of every registered type in declaration order; `models_with_multiple_types()` iterates models with two or more registered types (used by the finalize-time ambiguity audit).

The already-shipped consumer relation-override paths (annotation overrides like `category: AdminCategoryType` and assigned `strawberry.field` relation resolvers) are preserved unchanged and may legitimately target a secondary `DjangoType`. The optimizer's plan cache keys include the resolver's origin Strawberry type, so a primary-return and a secondary-return resolver on the same model do not share a cached plan.

**See also:** [`Meta.model`](#metamodel) · [`DjangoType`](#djangotype) · [`finalize_django_types`](#finalize_django_types) · [`ConfigurationError`](#configurationerror).

## `Meta.relation_shapes`

**Status:** shipped (`0.0.9`).

Per-relation narrowing key for the relation-as-Connection upgrade. On a Relay-Node-shaped [`DjangoType`](#djangotype), every selected many-side relation (reverse FK, forward / reverse M2M) whose target type is also Relay-Node-shaped synthesizes a `<field>Connection` sibling at finalization Phase 2.5 by default, reusing the shipped [`DjangoConnectionField`](#djangoconnectionfield) machinery — per-target connection classes, sidecar-derived `filter:` / `orderBy:` arguments, and the target type's [`Meta.connection`](#metaconnection) `totalCount` opt-in. `Meta.relation_shapes` is a `dict[str, str]` with values `"list"` / `"connection"` / `"both"` (`"both"` is the implicit default): `"connection"` suppresses the `list[T]` field, `"list"` suppresses the connection. Validated at type creation — unknown keys / values / shapes, a key naming a non-relation / non-many-side / unselected field, a key naming a consumer-authored relation (the override owns the shape), and declaring the key on a non-Relay-Node type all raise [`ConfigurationError`](#configurationerror); an explicit shape naming a relation whose target is not Relay-Node-shaped raises at finalization, while non-Node targets degrade silently (stay list-only) under the implicit default. As of `0.0.9` the synthesized `<field>Connection` siblings are optimizer-planned: a selected nested connection gets a windowed `Prefetch` so its page resolves in one query per relation per request rather than per parent — see [Connection-aware optimizer planning](#connection-aware-optimizer-planning). A synthesized relation connection still runs a sync pipeline with no `resolver=` seam, so a Relay target whose `get_queryset` is `async def` raises `SyncMisuseError` on every query of its `<field>Connection`; narrow that relation with `relation_shapes = {"<field>": "list"}` until an async connection pipeline lands.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [`Meta.connection`](#metaconnection) · [Relay Node integration](#relay-node-integration) · [`DjangoType`](#djangotype).

## `Meta.required_overrides`

**Status:** shipped (`0.0.9`).

Tuple / list of **non-relation** field names whose GraphQL nullability is forced to required (`T | None` → `T`) regardless of the Django column's `null`. It is the inverse-direction companion to [`Meta.nullable_overrides`](#metanullable_overrides); both share one tri-state `force_nullable` seam through [Scalar field conversion](#scalar-field-conversion), the same non-relation scope (scalar columns and, as of `0.0.11`, file/image output objects), and the same type-creation validation (unknown / excluded / consumer-authored / relation / Relay-suppressed-pk targets and the both-sets collision all raise [`ConfigurationError`](#configurationerror)). See [`Meta.nullable_overrides`](#metanullable_overrides) for the full validation table and the choice / array / hstore behavior.

**`required_overrides` changes the GraphQL contract, not the data.** Declaring `required_overrides = ("x",)` renders `x` as `T!` but does NOT alter the Django column (`null=True` stays) or sanitize runtime values — a resolver returning a row with `x is None` hits a Strawberry non-null violation at query time. The consumer must guarantee the invariant at the resolver boundary (e.g. `.exclude(x__isnull=True)`), exactly as for any non-null GraphQL field backed by nullable storage. On a file/image column it is also the opt-out from the **default-nullable** output object (spec-037 Decision 4): `required_overrides` renders `DjangoFileType!` / `DjangoImageType!` instead of the default `… | None`, with the same contract-not-data caveat — an empty stored file then trips the non-null violation. (Symmetrically, [`Meta.nullable_overrides`](#metanullable_overrides) is always safe — widening to `T | None` never violates a non-null contract.)

**See also:** [`Meta.nullable_overrides`](#metanullable_overrides) · [Scalar field conversion](#scalar-field-conversion) · [Scalar field override semantics](#scalar-field-override-semantics) · [`ConfigurationError`](#configurationerror).

## `Meta.search_fields`

**Status:** planned for `0.1.2`.

Declarative search across model fields (and relation paths). Single `search: String` argument on connection fields fans out across the listed fields as an OR'd `icontains` filter — equivalent to `django-graphene-filters`'s `Meta.search_fields = ("name", "description", "category__name")` shape.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [`FilterSet`](#filterset).

## Multi-database cooperation

**Status:** shipped (`0.0.7`).

Documented cooperation surface — what the package guarantees under Django's multi-database machinery. Four axes:

1. `router.db_for_read` on FK-id elision stubs — parent row forwarded as the `instance=` hint when present, `None` otherwise.
2. Explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`](#djangooptimizerextension) for root querysets.
3. Consumer-provided `Prefetch(queryset=...)` via [`OptimizerHint.prefetch(...)`](#optimizerhint) round-trips with its `_db` intact — generated `Prefetch` child querysets do NOT inherit the root alias.
4. Strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases.

Companion `BACKLOG.md` item 41 covers first-class sharding-aware planning post-`1.0.0`.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [`get_queryset` visibility hook](#get_queryset-visibility-hook).

## `only()` projection

**Status:** shipped (`0.0.2`).

Scalar GraphQL selections become Django `.only(...)` projections so unselected columns are not fetched from the database. Connector columns required for `select_related`, reverse FK, FK / OneToOne, and M2M attachment paths are preserved automatically so Django can stitch related rows without lazy loads.

As of `0.0.10`, `.only(...)` is applied for `QUERY` operations only (G2): a mutation / subscription queryset keeps `select_related` / `prefetch_related` but carries no column deferral, so a mutation-returned queryset never carries a selection-shaped deferred-field set (see [`DjangoOptimizerExtension`](#djangooptimizerextension)). As of `0.0.11` the G2 mutation gate is exercised **live** by the products write surface — the `spec-035` G2 live-test handoff is discharged ([`DjangoMutation`](#djangomutation)).

**See also:** [FK-id elision](#fk-id-elision) · [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Plan cache](#plan-cache).

## `OptimizerHint`

**Status:** shipped (`0.0.3`).

Typed wrapper for per-relation optimizer overrides. Pass instances through [`Meta.optimizer_hints`](#metaoptimizer_hints).

Supported modes:

- `OptimizerHint.SKIP` — exclude a relation from automatic planning (the optimizer leaves it alone).
- `OptimizerHint.select_related()` — force `select_related`.
- `OptimizerHint.prefetch_related()` — force `prefetch_related`.
- `OptimizerHint.prefetch(Prefetch(...))` — use a consumer-provided `Prefetch` object and stop walking below that relation.

Validation: ``OptimizerHint(...)`` rejects conflicting flag combinations at
construction time and raises [`ConfigurationError`](#configurationerror).
The factories (`SKIP`, `select_related()`, `prefetch_related()`,
`prefetch(Prefetch(...))`) are the documented consumer API; direct
construction is supported but the same four shapes are the only ones the
walker dispatches, and any other combination — `skip=True` with any of the
three other flags, `force_select=True` with `force_prefetch=True`,
`prefetch_obj=` set with `force_select=True` or `force_prefetch=True`, or a
`prefetch_obj=` value that is not a `django.db.models.Prefetch` instance —
is rejected before the hint can reach `Meta.optimizer_hints`.

**See also:** [`Meta.optimizer_hints`](#metaoptimizer_hints) · [`DjangoOptimizerExtension`](#djangooptimizerextension).

## `Ordering`

**Status:** shipped (`0.0.8`).

Direction enum used as the leaf value in generated order input types. Six members: `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`. The `resolve(field_path)` method returns Django `OrderBy` expressions: `ASC` / `DESC` map to `F(field_path).asc()` / `F(field_path).desc()` (no NULLS positioning); the four NULLS-positioning members map to `F(field_path).asc(nulls_first=True)` / `F(field_path).asc(nulls_last=True)` / `F(field_path).desc(nulls_first=True)` / `F(field_path).desc(nulls_last=True)` respectively. [`OrderSet`](#orderset) calls `Ordering.resolve(...)` for every active input field and passes the resulting `OrderBy` expressions to `queryset.order_by(...)` in list-element order. An omitted field and a field supplied with an explicit GraphQL `null` direction are equivalent no-ops: neither reaches `resolve`, contributes an ordering term, or fires that field's active-input-only permission gate.

**See also:** [`OrderSet`](#orderset) · [`order_input_type`](#order_input_type).

## `OrderSet`

**Status:** shipped (`0.0.8`).

Declarative `Meta.model` / `Meta.fields` (list form or `"__all__"` shorthand for every column-backed model field — includes forward FK / OneToOne columns; excludes reverse relations and M2M managers); [`RelatedOrder`](#relatedorder) for cross-relation traversal; `check_*_permission` denial gates with **active-input-only scope** plus active-branch double-dispatch for `RelatedOrder` branches (parent's `check_<branch>_permission` fires alongside child orderset's field gates, deduped per `(OrderSet class, method name)`); list-shaped `orderBy:` argument with list-element-order tie-breaker mechanism; six-member [`Ordering`](#ordering) enum with NULLS positioning; cycle-safe lazy resolution via the five-layer port. Layer 6 (dynamic `OrderSet` generation against a connection-field meta dict) is a standing deferred non-goal: the connection field ([`DjangoConnectionField`](#djangoconnectionfield)) resolves ordering from the already-resolved [`Meta.orderset_class`](#metaorderset_class) sidecar directly rather than auto-generating an `OrderSet`, so no dynamic order factory is shipped.

To-many paths are row-preserving: ascending terms order each parent by `Min(path)` and descending terms by `Max(path)`, so reverse-FK / M2M joins do not duplicate nodes or inflate `totalCount`. A root `DjangoConnectionField` cursor-slices that grouped queryset and appends its deterministic primary-key tiebreaker. Nested relation connections carrying `orderBy:` deliberately bypass window/lateral planning and use the per-parent pipeline, so a to-many aggregate is never stacked below the optimizer's row-number window. This contract runs unchanged on SQLite and PostgreSQL.

The resolver-facing API is the classmethod pair `OrderSet.apply_sync(input_value, queryset, info)` and `OrderSet.apply_async(input_value, queryset, info)` (sync resolvers call the former; async resolvers await the latter), mirroring the shipped filter subsystem's shape. `orderBy: []`, an empty input object, omitted fields, and explicit `null` directions contribute no terms and preserve the queryset's existing order.

**See also:** [`Meta.orderset_class`](#metaorderset_class) · [`RelatedOrder`](#relatedorder) · [`Ordering`](#ordering) · [`order_input_type`](#order_input_type) · [`FilterSet`](#filterset).

## `order_input_type`

**Status:** shipped (`0.0.8`).

Factory returning the **element type** `Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` for resolver-argument annotations; eager validation; consumer usage `order_by: list[order_input_type(BranchOrder)] | None = None` (the list wrap matches the `orderBy: [<T>OrderInputType!]` list-shaped GraphQL argument); orphan validation at finalize.

The helper validates its [`OrderSet`](#orderset) argument eagerly so a typo at the resolver signature site fails loud at module import. Finalize-time orphan validation catches helper-referenced order sets that were never wired through [`Meta.orderset_class`](#metaorderset_class) — tracked via a `_helper_referenced_ordersets` ledger that `registry.clear()` co-clears.

**See also:** [`OrderSet`](#orderset) · [`Ordering`](#ordering) · [`Meta.orderset_class`](#metaorderset_class).

## PEP 562 lazy export

**Status:** shipped (`0.0.13`).

The module-level `__getattr__` mechanism (PEP 562) behind every [soft-dependency](#soft-dependency) symbol: the guarded name is materialized on first attribute access instead of at module import, so importing the module never pays for the optional integration, and the install-hint `ImportError` fires at the consumer's own `from ... import` line. Two package instances: the package root's `__getattr__` resolves the DRF names ([`SerializerMutation`](#serializermutation)) — deliberately kept **out** of the root `__all__`, so `from django_strawberry_framework import *` stays DRF-free; and `routers.py`'s resolves [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) (planned `0.0.14`) — deliberately listed **in** the submodule `__all__`, so `from ...routers import *` reaches for the name (star import calls `getattr` per `__all__` entry), fires the guard, and raises the same install hint as the explicit import.

Because a lazily-exported name is never a static module global, the `__all__` line carries a scoped `# noqa: F822` (ruff's undefined-name-in-`__all__` check is a false positive for a PEP 562 export). Behavior matrix: `from module import name` triggers `__getattr__` and propagates its `ImportError`; unrelated attribute misses raise plain `AttributeError`, never the install hint.

**See also:** [Soft dependency](#soft-dependency) · [`SerializerMutation`](#serializermutation) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter).

## Per-field permission hooks

**Status:** planned for `0.1.1`.

Methods named `check_<field>_permission` on the type's [`FieldSet`](#fieldset) gate access to that field. Two failure modes:

- **Redaction** — silent safe-value fallback (`None`, empty string, sentinel) so the response shape stays stable.
- **Denial** — raise `GraphQLError` so the response carries an `errors` entry for that path.

The read gate's surface is pinned now (Decision 2 of the `0.0.10` permissions spec) and the implementation lands with the `0.1.1` [`FieldSet`](#fieldset) card: the **host** is `FieldSet` (wired via [`Meta.fields_class`](#metafields_class), which stays in `DEFERRED_META_KEYS` until then); the **signature** is `check_<field>_permission(self, info)` (an `info`-shaped read gate that runs per resolved field — distinct from the `(self, request)`-shaped input gates that judge filter / order *input*). **Composition with the cascade:** a field gate does **not** short-circuit cascade visibility — [`apply_cascade_permissions`](#apply_cascade_permissions) narrows the queryset first and field gates run only on surviving rows, so a field denial never leaks the existence of a cascade-hidden row.

Composes with filter / order / aggregate permission gates and with the post-write return value of mutations.

**See also:** [`FieldSet`](#fieldset) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [`get_queryset` visibility hook](#get_queryset-visibility-hook).

## Per-operation extension isolation

**Status:** planned for `0.0.14`.

The guarantee that every GraphQL operation gets a distinct stateful extension instance and engine-owned `execution_context`. Strawberry versions before 0.316.0 cached sync class-created extensions on `Schema._sync_extensions`, so concurrent requests could overwrite one shared instance's context. Spec 044 raises the hard `strawberry-graphql` floor to 0.316.0 and documents the class-form opt-in, which the engine now materializes per operation. [`DjangoDebugExtension`](#djangodebugextension) consequently uses plain instance attributes. The optimizer deliberately keeps its different singleton-in-a-factory shape because its cross-request [Plan cache](#plan-cache) is shared and its per-request state is isolated elsewhere.

**See also:** [`DjangoDebugExtension`](#djangodebugextension) · [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Hard dependency](#hard-dependency).

## Plan cache

**Status:** shipped (`0.0.3`).

Caches optimizer plans across requests. The same query 10,000×/sec walks the selection tree once, not 10,000 times.

Properties:

- **Selection-shape keys.** Cache keys include the selected operation AST, relevant `@skip` / `@include` variables, target model, root runtime path, and the resolver's origin Strawberry type.
- **Variable filtering.** Filter-variable values that do not affect selection shape are excluded from the key, so a query with many filter combinations reuses one cached plan. As of `0.0.9` this is refined for paginated nested connections: variables feeding a **nested** connection's `first` / `last` / `before` / `after` arguments ARE hashed into the key (their values are baked into the windowed prefetch), while variables feeding **root** pagination arguments stay out (root slicing happens post-plan in `ConnectionExtension`), including through root-level fragments. A variable that does not affect plan content still stays out.
- **Multi-operation safety.** `query A { ... } query B { ... }` in one document never shares a plan across operations.
- **Named-fragment safety.** Directives inside named fragments are tracked into the cache key.
- **Request-scope safety.** Plans that embed request-scoped [`get_queryset`](#get_queryset-visibility-hook) results are marked uncacheable.
- **Cache immutability.** Cached plans are copied before queryset-specific diffing, so one resolver's queryset shape cannot mutate a plan reused by another request.
- **Introspection.** `DjangoOptimizerExtension.cache_info()` exposes hit / miss / size counts.
- **Low per-request overhead.** `DjangoType` precomputes optimizer field metadata at class creation.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Queryset diffing](#queryset-diffing) · [FK-id elision](#fk-id-elision).

## Probe URLconf

**Status:** shipped (repository test pattern).

A test-local Django URL configuration used to exercise an opt-in schema shape over real HTTP without changing the example project's shipped URLconf. A module-level `urlpatterns` mounts Strawberry's Django view over a purpose-built schema, and `pytest.mark.urls` selects that URLconf for the test. The request still travels through Django's request/response and JSON serialization path, so it belongs in `examples/fakeshop/test_query/` under the [Live-first coverage mandate](#live-first-coverage-mandate). Spec 044 uses this pattern because [`DjangoDebugExtension`](#djangodebugextension) is off by default in fakeshop.

**See also:** [Live-first coverage mandate](#live-first-coverage-mandate) · [Schema reload discipline](#schema-reload-discipline) · [`TestClient`](#testclient).

## Queryset diffing

**Status:** shipped (`0.0.3`).

The optimizer does not assume it owns the queryset. It reconciles framework-generated plans against queryset work the consumer already applied.

Cooperation rules:

- **Queryset cooperation.** If your resolver already calls `select_related("category")`, the optimizer does not reapply it.
- **Prefetch cooperation.** If your resolver returns `Category.objects.prefetch_related(Prefetch("items", queryset=...))`, the consumer `Prefetch` wins over less-specific automatic work.
- **Subtree-aware reconciliation.** `prefetch_related("items", "items__entries")` cooperates with the optimizer's nested `Prefetch("items", ...)` instead of raising Django's "lookup already seen with a different queryset" error.
- **Plain-string absorption.** Safe consumer string prefetches can be absorbed by richer optimizer `Prefetch` objects.
- **`only()` cooperation.** If your resolver already calls `.only(...)` to enforce a column-level projection (e.g., a permission boundary that restricts which columns leave the database), the optimizer drops its own `only_fields` rather than chaining a second `.only(...)` that would replace yours — Django's `QuerySet.only(...).only(...)` replaces (not merges) the deferred-field set. `.defer(...)` is not treated as a consumer projection because `.defer()` and `.only()` compose cleanly in Django.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Plan cache](#plan-cache) · [`OptimizerHint`](#optimizerhint).

## Reference-counted cursor coordinator

**Status:** planned for `0.0.14`.

The module-private, lock-protected coordinator that makes [`DjangoDebugExtension`](#djangodebugextension)'s `force_debug_cursor` bracket overlap-safe. The first active user of a connection saves its prior flag and enables instrumentation; overlapping users increment a depth; only the final release restores the saved value and removes the map entry. Every extension instance keeps its own query-log snapshot, while `contextlib.ExitStack` owns token release so partial multi-alias acquisition and operation failures unwind correctly. The coordinator manages one Boolean flag only: it does not observe queries, attribute rows, or replace Django's cursor wrapper.

**See also:** [Django debug-cursor capture](#django-debug-cursor-capture) · [Async SQL-capture boundary](#async-sql-capture-boundary).

## `RelatedAggregate`

**Status:** planned for `0.1.3`.

Field declaration on an [`AggregateSet`](#aggregateset) for cross-relation aggregate traversal. Accepts a target `AggregateSet` class (or its import path for circular cases), parallel to [`RelatedFilter`](#relatedfilter) / [`RelatedOrder`](#relatedorder) in the filter / order subsystems.

**See also:** [`AggregateSet`](#aggregateset) · [`get_child_queryset`](#get_child_queryset).

## `RelatedFilter`

**Status:** shipped (`0.0.8`).

Field declaration on a [`FilterSet`](#filterset) for cross-relation filter traversal. Accepts a target `FilterSet` class, an absolute import path (`"apps.library.filters_genre.GenreFilter"`), or an unqualified name (`"BookFilter"`) for same-module circular references. The unqualified-name form is resolved lazily via Layer 2's module-fallback resolution — try as an absolute import path first, fall back to prepending the binding `FilterSet`'s `__module__`; if that second attempt also fails, the raw `ImportError` from the module-prefixed path propagates unchanged (the resolver does not rewrap it into a [`ConfigurationError`](#configurationerror), and the surfaced error names only that single attempted path, not both). The finalize-time rewrap into a [`ConfigurationError`](#configurationerror) happens a layer up, when `finalize_django_types()` expands the binding `FilterSet` and names the offending set rather than both import attempts. Matches `django-graphene-filters`'s six-layer pipeline.

An explicit `queryset=` argument is a **filter-scope constraint** intersected with the active branch's queryset, NOT a security boundary — the constraint applies only when the related branch is active in the normalized input, so it cannot serve as a visibility gate. Visibility / security is the job of [`get_queryset`](#get_queryset-visibility-hook) on the target [`DjangoType`](#djangotype); the apply pipeline derives the child visibility queryset from `<TargetType>.get_queryset(...)` for every active `RelatedFilter` branch before the parent JOIN runs, so nested filters cannot see through visibility to hidden related rows.

**See also:** [`FilterSet`](#filterset) · [`RelatedOrder`](#relatedorder).

## `RelatedOrder`

**Status:** shipped (`0.0.8`).

Field declaration on an [`OrderSet`](#orderset) for cross-relation ordering traversal. Accepts a target `OrderSet` class, an absolute import path (`"apps.library.orders_genre.GenreOrder"`), or an unqualified name (`"BookOrder"`) for same-module circular references. The shared Layer-2 module-fallback resolution is a sibling import from `sets_mixins.LazyRelatedClassMixin` — the neutral shared module per the package's set-family discipline, not `filters.base` as named in earlier revisions; the unqualified-name form is resolved lazily — try as an absolute import path first, fall back to prepending the binding `OrderSet`'s `__module__`; if that second attempt also fails, the raw `ImportError` from the module-prefixed path propagates unchanged (the resolver does not rewrap it into a [`ConfigurationError`](#configurationerror), and the surfaced error names only that single attempted path, not both). The finalize-time rewrap into a [`ConfigurationError`](#configurationerror) happens a layer up, when `finalize_django_types()` expands the binding `OrderSet` and names the offending set rather than both import attempts.

Position-side-channel note: ordering by a hidden related column changes the *position* of visible parent rows based on data the user cannot read. The consumer-side defense is the parent-side `check_<branch>_permission` gate on the active `RelatedOrder` branch — the apply pipeline fires the parent's branch gate alongside the child orderset's field gates (active-branch double-dispatch) so the parent can deny ordering through a sensitive relation.

**See also:** [`OrderSet`](#orderset) · [`RelatedFilter`](#relatedfilter).

## Relation handling

**Status:** shipped (`0.0.1`+).

`DjangoType` maps Django relation cardinality into GraphQL type shape and resolver behavior. Each cardinality has its own sub-anchor for direct linking.

### Forward `ForeignKey`

Target type, nullable when the field is nullable. The optimizer plans `select_related` for this shape or — under safe conditions — performs [FK-id elision](#fk-id-elision).

### Forward `OneToOneField`

Target type, nullable when the field is nullable.

### Reverse `ForeignKey`

`list[target_type]`. The optimizer plans `prefetch_related`. Many-side resolvers return Python lists, not Django managers.

### Reverse `OneToOneField`

Target type or `None`. Returns `None` when the related row does not exist (no `RelatedObjectDoesNotExist` raised at the GraphQL boundary).

### Forward `ManyToManyField`

`list[target_type]`. Optimizer plans `prefetch_related`.

### Reverse `ManyToManyField`

`list[target_type]`. Symmetric with forward M2M.

### Resolver behavior

- many-side resolvers return lists, not Django managers
- forward resolvers can return FK-id stubs when the optimizer safely elides a join (see [FK-id elision](#fk-id-elision))
- relation access cooperates with Django's prefetch and relation caches
- consumer-authored `strawberry.field` relation overrides are preserved instead of being clobbered by generated resolvers
- consumer overrides are responsible for their own queryset shape — re-shaping a relation queryset with `.order_by(...)` / `.filter(...)` can bypass the framework's prefetched relation cache

**See also:** [`DjangoType`](#djangotype) · [`Meta.optimizer_hints`](#metaoptimizer_hints) · [FK-id elision](#fk-id-elision) · [Definition-order independence](#definition-order-independence).

## Relay Node integration

**Status:** shipped (`0.0.5`).

When [`Meta.interfaces`](#metainterfaces) includes `strawberry.relay.Node`, the `DjangoType` becomes a Relay-node-shaped GraphQL type with `id: GlobalID!` and the four `resolve_*` defaults wired through `cls.get_queryset` (the model's default manager plus the type's visibility hook).

Shipped behavior:

- Default `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` classmethods are injected when `relay.Node` is declared; consumer-declared overrides are preserved via Strawberry's `__func__` identity test (matches `strawberry-django`).
- When `relay.Node` is in `Meta.interfaces`, the synthesized Django `id: int!` annotation is suppressed and the Relay-supplied `id: GlobalID!` from the interface is used instead. The Django primary key remains selected as a connector column for the optimizer.
- Both sync and async paths for `resolve_node` and `resolve_nodes`; `resolve_id_attr` and `resolve_id` are sync.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- The framework rejects the "async `get_queryset` invoked from a sync resolver context" misuse with [`SyncMisuseError`](#syncmisuseerror) — a typed marker that multiple-inherits `ConfigurationError` AND `RuntimeError` so consumers may catch either base class while future code can match `SyncMisuseError` directly without depending on substring-of-message checks. Raised by `utils/querysets.py`'s shared `apply_type_visibility_sync` whenever a sync resolver surface's `cls.get_queryset` returns a coroutine — the Relay node defaults (`resolve_node` / `resolve_nodes`), the connection sync pipeline, the optimizer's sync prefetch-child visibility, and the filter related-visibility derive all route through it; the unawaited coroutine is closed before the raise so Python does not emit `RuntimeWarning: coroutine was never awaited`.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise [`ConfigurationError`](#configurationerror) at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Non-Relay Strawberry interfaces (`@strawberry.interface`-decorated classes) are accepted without Relay-specific wiring.

Optimizer-extension cooperation on the per-node `resolve_node` resolver is deferred to a follow-up slice; root-level list resolvers continue to receive full [`DjangoOptimizerExtension`](#djangooptimizerextension) treatment today.

As of `0.0.9` the default `GlobalID` payload is the Django **model label** (`app_label.modelname:<pk>`, e.g. `products.item:42`) rather than the GraphQL type name, so renaming a GraphQL type (or [`Meta.name`](#metaname)) no longer invalidates cached client ids. [`Meta.globalid_strategy`](#metaglobalid_strategy) (per type) and [`RELAY_GLOBALID_STRATEGY`](#relay_globalid_strategy) (schema-wide) select `model` (default), `type` (the legacy GraphQL-type-name opt-out, byte-identical to the pre-`0.0.9` payload), `type+model` (transitional decode of old type-anchored ids while emitting model-anchored ones), or a callable encoder; precedence is `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → `model`. The `node_id` slot, the FK-`id` round-trip, and the composite-pk rejection are unchanged — only the type-name slot moved. With `DONE-032-0.0.9` the root refetch surface is shipped: [`DjangoNodeField`](#djangonodefield) / [`DjangoNodesField`](#djangonodesfield) decode every emitted payload server-side and dispatch to these `resolve_node` / `resolve_nodes` defaults, and many-side relations between Relay-Node-shaped types synthesize connection siblings per [`Meta.relation_shapes`](#metarelation_shapes).

**See also:** [`Meta.interfaces`](#metainterfaces) · [`Meta.globalid_strategy`](#metaglobalid_strategy) · [`RELAY_GLOBALID_STRATEGY`](#relay_globalid_strategy) · [`DjangoNodeField`](#djangonodefield) · [`DjangoNodesField`](#djangonodesfield) · [`DjangoConnectionField`](#djangoconnectionfield) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning).

## RELAY_GLOBALID_STRATEGY

**Status:** shipped (`0.0.9`).

The schema-wide default Relay `GlobalID` encode strategy, read from `DJANGO_STRAWBERRY_FRAMEWORK["RELAY_GLOBALID_STRATEGY"]`. It sets the project-wide default that every Relay-Node-shaped [`DjangoType`](#djangotype) inherits unless the type declares its own [`Meta.globalid_strategy`](#metaglobalid_strategy); precedence is `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → `"model"`. It accepts the same values as the per-type key: `"model"` (default), `"type"`, `"type+model"`, or a synchronous `(type_cls, model, root, info) -> str` callable encoder; see [`Meta.globalid_strategy`](#metaglobalid_strategy) for the full strategy table. Callable strategies are encode-only and have no `GlobalID` decode path.

The setting is read through the thin `conf.py` reader and validated at schema finalization by the same shared validator the `Meta` key uses; an unknown string, incompatible callable signature, or async callable raises [`ConfigurationError`](#configurationerror). The resolved strategy is frozen at schema-build time — the `GlobalID` format is a stable schema contract, not request-scoped state.

```python
DJANGO_STRAWBERRY_FRAMEWORK = {
    "RELAY_GLOBALID_STRATEGY": "type+model",
}
```

**See also:** [`Meta.globalid_strategy`](#metaglobalid_strategy) · [Relay Node integration](#relay-node-integration) · [`ConfigurationError`](#configurationerror).

## `request_from_info`

**Status:** shipped (`0.0.8`).

The shared request-resolution helper in `django_strawberry_framework/utils/permissions.py`: every framework surface that needs the acting user — the auth `current_user` query, mutation permission checks ([`DjangoModelPermission`](#djangomodelpermission)), the filter / order `check_*_permission` gates, and serializer-mutation hooks — resolves the Django request through this one function, never through a local decoder. Accepted context shapes: the canonical Strawberry-Django attribute shape (`info.context.request`) and a bare `HttpRequest` (the Django test-client default). Any other shape raises [`ConfigurationError`](#configurationerror) naming the caller's `family_label` (`FilterSet` / `OrderSet` / `DjangoMutation`) so the consumer sees which surface failed.

Hard single-siting rule: every new request/context shape is supported inside this helper only — callers must not grow local request decoders. The `0.0.14` [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) card extends the helper with Strawberry's Channels context shape (a mapping context whose `"request"` value exposes `consumer.scope`, duck-typed with no `channels` import in `utils/`), resolving to the [Channels request adapter](#channels-request-adapter) — a wrapper exposing `.user` / `.session` / `.scope` from the scope and delegating every other attribute to the wrapped `ChannelsRequest` via `__getattr__` — for the read path; session-mutating [Auth mutations](#auth-mutations) over Channels stay deferred.

**See also:** [Channels request adapter](#channels-request-adapter) · [`DjangoModelPermission`](#djangomodelpermission) · [Auth mutations](#auth-mutations) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter).

## `require_optional_module`

**Status:** planned for `0.0.14`.

The raising optional-dependency primitive planned for `utils/imports.py` — the package's single optional-import owner, beside the best-effort `import_attr_if_importable` and the loaded-only `loaded_attr` — landing in Slice 1 of the `0.0.14` [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) card. Signature `require_optional_module(module_name, *, install_hint)`: imports the module via `importlib.import_module` and returns it unchanged; on `ImportError` raises a new `ImportError` carrying `install_hint`, chaining the original. No memoization — [eviction-simulated absence](#eviction-simulated-absence) tests must be able to re-hit real imports. **No `feature_label` parameter**: the feature-specific text lives entirely in the caller's `install_hint` (an unused label is ceremony), and hint strings stay single-sited at the feature owner (`routers.py::_CHANNELS_INSTALL_HINT`). `require_channels()` is a thin wrapper over it; migrating `require_drf()` onto the same primitive is a deliberate follow-on non-goal (its hint is byte-pinned by the `_HINT_SUBSTRING` tests).

**See also:** [Soft dependency](#soft-dependency) · [Eviction-simulated absence](#eviction-simulated-absence) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter).

## Response-extension merge semantics

**Status:** planned for `0.0.14`.

How Strawberry combines extension metadata into `ExecutionResult.extensions`. The runner calls each extension's `get_results()` and applies dictionaries in schema `extensions=` list order; a later extension wins if two publish the same key. [`DjangoDebugExtension`](#djangodebugextension) owns the `debug` key and does not guard a collision with a consumer extension. Its values are JSON-native strings, floats, booleans, lists, and dictionaries so every supported transport can serialize them. This merge order is distinct from the reverse, last-in-first-out teardown order covered by [Masking-extension ordering](#masking-extension-ordering).

**See also:** [Strawberry extension lifecycle](#strawberry-extension-lifecycle) · [Debug payload availability](#debug-payload-availability).

## Response-extensions debug middleware

**Status:** planned for `0.0.14`.

The named 0.0.14 capability that surfaces executed SQL and raised execution exceptions through the GraphQL response's `extensions.debug` map. Its public implementation is [`DjangoDebugExtension`](#djangodebugextension), an off-by-default Strawberry extension exported from `django_strawberry_framework.extensions`. The payload always has `sql` and `exceptions` lists after execution; parse and validation failures omit the key. SQL uses [Django debug-cursor capture](#django-debug-cursor-capture), and exceptions use the [Debug exception row](#debug-exception-row) contract.

The complete implementation vocabulary is split into focused entries: [Strawberry extension lifecycle](#strawberry-extension-lifecycle), [Per-operation extension isolation](#per-operation-extension-isolation), [Reference-counted cursor coordinator](#reference-counted-cursor-coordinator), [Bounded query-log rollover](#bounded-query-log-rollover), [Debug SQL row](#debug-sql-row), [Debug payload availability](#debug-payload-availability), [Masking-extension ordering](#masking-extension-ordering), [Async SQL-capture boundary](#async-sql-capture-boundary), [Response-extension merge semantics](#response-extension-merge-semantics), and [Developer-only debug posture](#developer-only-debug-posture).

Distinct from [Debug-toolbar middleware](#debug-toolbar-middleware): this is in-response client-visible surfacing, while the toolbar is a server-side SQL panel. Both are useful and may coexist. A graphene-django consumer follows the documented [Graphene debug migration](#graphene-debug-migration), validated against [Cookbook parity](#cookbook-parity).

**See also:** [`DjangoDebugExtension`](#djangodebugextension) · [Debug-toolbar middleware](#debug-toolbar-middleware) · [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Multi-database cooperation](#multi-database-cooperation).

## `safe_wrap_connection_method`

**Status:** shipped (`0.0.7`).

Cooperative wrap helper for consumers (or third-party libraries) who need to replace a method on a Django `connections[alias]` between `setUpClass` and `tearDownClass`. Mirrors `django-debug-toolbar`'s wrap-time isinstance check at `debug_toolbar.panels.sql.tracking.wrap_cursor`: refuses to clobber Django's `_DatabaseFailure` wrapper when it's already in place, returning `False` instead. Returns `True` and installs the consumer-provided wrapper otherwise.

```python
from django.db import connections
from django_strawberry_framework.testing import safe_wrap_connection_method

connection = connections["default"]
original = connection.cursor
installed = safe_wrap_connection_method(connection, "cursor", my_wrapper)
# installed is False if Django's _DatabaseFailure is already in place;
# the connection method is left untouched in that case.
```

The wrap-time half of the package's defense-in-depth against Django Trac #37064 (closed upstream as `wontfix`). The unwrap-time half ([Django Trac #37064 hardening](#django-trac-37064-hardening)) is applied automatically by `DjangoStrawberryFrameworkConfig.ready` so consumers who use the helper are auto-protected at both ends; consumers who don't are still auto-protected at the unwrap end.

**See also:** [Django Trac #37064 hardening](#django-trac-37064-hardening) · [`TestClient`](#testclient) · [`GraphQLTestCase`](#graphqltestcase).

## Scalar field conversion

**Status:** shipped (`0.0.1`+).

Shipped scalar support:

- text-like fields (`CharField` / `TextField`) → `str`
- integer and auto fields (`IntegerField` / `AutoField` / `BigAutoField` / `SmallIntegerField` / `PositiveIntegerField`) → `int`
- `BigIntegerField` / `PositiveBigIntegerField` → [`BigInt`](#bigint-scalar) (string-serialized at the wire; `PositiveBigIntegerField` switched from `int` to `BigInt` in `0.0.6` — breaking wire-format change)
- boolean fields → `bool`
- float fields → `float`
- decimal fields → `decimal.Decimal`
- date / datetime / time fields → Python-native time types (note: ``DurationField`` is intentionally absent from the default map because Strawberry has no first-party scalar for ``datetime.timedelta``; register a custom scalar via ``SCALAR_MAP[DurationField] = MyDurationScalar``)
- UUID fields → `uuid.UUID`
- ``BinaryField`` is intentionally absent from the default map (no first-party Strawberry scalar for ``bytes``); the conventional plug is ``SCALAR_MAP[BinaryField] = strawberry.scalars.Base64``
- file and image fields → a three-way split: on **read**, a `FileField` / `ImageField` column converts to a structured [`DjangoFileType`](#djangofiletype) / [`DjangoImageType`](#djangoimagetype) output object — nullable by default in the SDL regardless of the column's `null` / `blank` (an empty stored file resolves to `null`) — via the new `FIELD_OUTPUT_TYPE_MAP`, kept off this shared map; the **filter / scalar-input** value stays `str` (the `FileField` / `ImageField` rows in `SCALAR_MAP` are unchanged); the **mutation input** is the [`Upload`](#upload-scalar) scalar
- `JSONField` → `strawberry.scalars.JSON`
- PostgreSQL `ArrayField` → typed `list[T]` (recursive through `field.base_field`; soft-registered, only when `django.contrib.postgres.fields` imports successfully; nested `ArrayField` and outer `choices` rejected with [`ConfigurationError`](#configurationerror))
- PostgreSQL `HStoreField` → `strawberry.scalars.JSON` (soft-registered, only when `django.contrib.postgres.fields` imports successfully; outer `choices` rejected with [`ConfigurationError`](#configurationerror))
- `null=True` → `T | None`
- Relay `GlobalID` mapping for auto IDs when [`Meta.interfaces = (relay.Node,)`](#metainterfaces) is declared

**Subclass MRO walk.** Consumer subclasses of any supported Django field class (e.g., `class TrimmedCharField(models.CharField)`, third-party encrypted / money fields) resolve to the parent's annotation automatically — the converter walks `type(field).__mro__` until it matches, so subclasses inherit without explicit registration. Subclasses whose MRO contains no registered Django field class raise [`ConfigurationError`](#configurationerror) at type creation (with [`Meta.exclude`](#metaexclude) or a consumer annotation override — see [Scalar field override semantics](#scalar-field-override-semantics) — named as the consumer recourses).

Choice support is documented separately under [Choice enum generation](#choice-enum-generation).

**See also:** [Choice enum generation](#choice-enum-generation) · [Specialized scalar conversions](#specialized-scalar-conversions) · [Scalar field override semantics](#scalar-field-override-semantics).

## Scalar field override semantics

**Status:** shipped (`0.0.6`).

The four-corner override matrix is now complete: annotation-only and assigned-`strawberry.field` scalar overrides land alongside the matching annotation-only and assigned-`strawberry.field` relation overrides. The consumer's annotation or assigned field wins over the auto-synthesized one via the unified `consumer_authored_fields` short-circuit in `DjangoType.__init_subclass__` and `_build_annotations`.

Opt-out continues via [`Meta.exclude`](#metaexclude); field-level metadata (description, deprecation, default) continues through the assigned `strawberry.field(...)` path that shipped in `0.0.5`.

**Converter validations are bypassed for overridden fields.** `_build_annotations`'s scalar short-circuit skips every `convert_scalar` validation and side effect for an overridden field, so the consumer's annotation is authoritative. Three behavior changes worth highlighting: (a) an unsupported scalar field — for example an `IntegerField` subclass whose MRO contains no registered ancestor that would otherwise raise [`ConfigurationError`](#configurationerror) — is overrideable now; (b) a grouped-choices field declared as `choices=[("g1", [...])]` that would otherwise raise is overrideable now; (c) a nested `ArrayField(ArrayField(...))` that would otherwise raise is overrideable now. [`Meta.exclude`](#metaexclude) and annotation override are now parallel consumer recourses for unsupported scalar fields (see [Scalar field conversion](#scalar-field-conversion)).

**`relay.Node` `id` collision rejected at type-creation time.** Two sub-restrictions: (1) assigned `id = <StrawberryField>` overrides are uniformly rejected on Relay-Node-shaped types; the supported alternatives are `relay.NodeID[<pk_type>]` for a custom id annotation, `@classmethod resolve_id` for a custom id resolver, and a **resolver-backed sibling field** — `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case. A metadata-only sibling such as `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance. (2) Inherited `id` annotations on a Relay-Node-shaped subclass slip past the guard at class-creation time and are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry sees no `id` annotation on the child, applies the Relay-supplied `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`. Annotation `id: relay.NodeID[...]` is accepted in direct, PEP 563 / stringified, and mixed (resolved-id-with-unresolved-sibling) forms; non-`id` overrides are accepted unchanged.

**Field-level GraphQL metadata on the Relay-supplied `id` field is not configurable in `0.0.6`.** The documented workaround is the resolver-backed sibling field named above; a metadata-only sibling without a resolver is NOT recommended.

**See also:** [`DjangoType`](#djangotype) · [Definition-order independence](#definition-order-independence).

## Schema audit

**Status:** shipped (`0.0.3`).

`DjangoOptimizerExtension.check_schema(schema)` walks every schema-reachable `DjangoType` (descending through object fields, union members, and the concrete implementations of any interface type encountered, so a `DjangoType` reachable only via an interface-typed root field still participates) and reports relation targets without registered `DjangoType`s as warnings. Identical `(source_model, field_name)` warnings produced by multi-type overlap are deduped to one warning per pair so multi-type models do not double-report. Hidden fields and [`OptimizerHint.SKIP`](#optimizerhint) fields are ignored. Intended for use as a unit-test assertion or a CI gate.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Strictness mode](#strictness-mode).

## Schema export management command

**Status:** shipped (`0.0.7`).

`django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`. `--path` omitted writes SDL to `self.stdout`; `--path <file>` writes UTF-8 SDL to the named path and reports `Wrote schema to <file>` via `self.style.SUCCESS`. The write is unconditionally destructive: an existing target is replaced without prompting, and the command does not create a missing parent directory. `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, missing positional argument, bare `--path` with no value, empty-string `--path`, and file-write `OSError` (missing parent directory, permission denied, target is a directory). No `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7`.

**See also:** [Django `AppConfig`](#django-appconfig) · [Schema introspection management command](#schema-introspection-management-command).

## Schema introspection management command

**Status:** shipped (`0.0.9`).

`django_strawberry_framework/management/commands/inspect_django_type.py` ships `Command(BaseCommand)` as `manage.py inspect_django_type <Type> [--schema <selector>]` — a diagnostic that prints, per selected field, the Django field name → Django field type → resolved GraphQL type → nullability → which converter row fired. It is a strict reader of the existing introspection surface: the resolved GraphQL type and nullability are read from the authoritative post-finalize record — `origin.__annotations__` for auto-synthesized scalar and relation fields (already reflecting `Meta.nullable_overrides` / `Meta.required_overrides`), except a `relation_shapes` `"connection"`-shaped relation, whose suppressed list annotation forces the row to read the synthesized `<rel>_connection` sibling from `origin.__strawberry_definition__`; and the finalized Strawberry field metadata `origin.__strawberry_definition__` for consumer-authored fields (annotation or `strawberry.field` overrides), whose `origin.__annotations__` entry is an unrenderable `StrawberryAnnotation` or unresolved forward-ref string; an unresolved forward reference surfaces as Strawberry's `UNRESOLVED` sentinel and raises `CommandError` rather than printing a bogus type — while [`SCALAR_MAP`](#scalar-field-conversion) is re-walked only to NAME the converter row, never to re-derive nullability via `convert_scalar`.

The positional `type` argument dispatches by shape: a **dotted** object path (`apps.library.schema.BookType`) resolves via Django's `import_string`, and a dotted import failure raises `CommandError` carrying the **original** error (never masked by a registry fallback); a **bare** name (`BookType`) resolves via a unique `__name__` registry lookup (a post-schema-import convenience). The optional `--schema <selector>` is imported first via Strawberry's `import_module_symbol(..., default_symbol_name="schema")` (mirroring [Schema export management command](#schema-export-management-command), accepting both `config.schema` and `config.schema:schema`) so a cold CLI process registers + finalizes every type before resolution. The command does not invoke `finalize_django_types()` itself: `--schema` must identify the project's real schema module, whose import owns registration and finalization. On a [Relay-Node-shaped](#relay-node-integration) type the suppressed primary key reports the interface-supplied `GlobalID!` / `relay.Node id` row rather than indexing the (absent) `origin.__annotations__[pk_name]`.

`CommandError` is raised for: an unresolvable argument; an ambiguous bare name (≥2 registered types share the `__name__` — each candidate is listed on its own line as a fully-qualified `module.qualname` object path, with its model, so the path can be passed directly to the command); a resolved symbol that is not a [`DjangoType`](#djangotype) subclass; a `DjangoType` with no `__django_strawberry_definition__` (abstract / no-`Meta` base — "not a registered DjangoType"); and a `DjangoType` whose `definition.finalized is False` ("`finalize_django_types()` has not run — pass `--schema …`"). The last two are distinct branches. No `--json` / `--watch` mode in `0.0.9` (single human-readable table, matching the `export_schema` posture).

**See also:** [Schema export management command](#schema-export-management-command) · [`DjangoType`](#djangotype) · [Relay Node integration](#relay-node-integration) · [Scalar field conversion](#scalar-field-conversion).

## Schema reload discipline

**Status:** shipped.

The fakeshop suites' order-independence-by-reconstruction rule, single-sited in `examples/fakeshop/schema_reload.py`: any test that rebuilds the aggregate `config.schema` calls `reload_all_project_schemas()`, which clears the global type registry, re-imports every contributing app's `apps.<app>.schema` in dependency-safe order (`glossary` before `kanban`, whose card-term type FKs into the glossary app), then reloads `config.schema` + `config.urls` and clears Django's URL caches.

The rule exists because package tests under root `tests/` call `registry.clear()` for isolation while `config.schema` composes every app's `Query` / `Mutation`: a partial (one-app) reload leaves the other apps unregistered, so the combined build raises a `LazyType` `KeyError` — or `DuplicatedTypeName` when a stale re-imported schema module survives in `sys.modules` — under collection orders that did not happen to pre-materialize the types. `pytest-xdist`'s `--dist loadscope` localizes the flake to whichever worker drew both files, which is why the reload must be complete and per-test rather than fixed by ordering. Every `test_query/` acceptance suite's autouse fixture delegates to the helper (via `test_query/conftest.py`); package tests that execute real GraphQL through fakeshop (e.g. the [Debug-toolbar middleware](#debug-toolbar-middleware) suite) call it on fixture setup, before any URLconf steps.

## `seed_data`

**Status:** shipped.

fakeshop's deterministic catalog seed helper (`apps.products.services.seed_data(count, db_alias="default")`): for every discovered Faker provider it ensures one `Category`, one `Property` per provider method, and at least `count` `Item` rows (creating only the shortfall), each new `Item` carrying one `Entry` per `Property`. `is_private` flags alternate by sorted index for an exact, run-deterministic 50/50 public/private split.

The repo's seed-helper rule: a test that needs products-app rows starts with `seed_data(1)` (or an explicit `seed_data(N)`) as its first executable line rather than hand-building models — so SQL-emitting tests (optimizer-shape assertions, the [Debug-toolbar middleware](#debug-toolbar-middleware) SQL-panel tests) hit real rows through the same path as every other suite.

## `SerializerMutation`

**Status:** shipped (`0.0.13`).

Consumes a DRF `Serializer` / `ModelSerializer` via `Meta.serializer_class`. It **subclasses** [`DjangoMutation`](#djangomutation), overriding `_resolve_model` to return `Meta.serializer_class.Meta.model` (the `ModelSerializer`-driven contract), and so reuses the base value: the primary [`DjangoType`](#djangotype) payload in the uniform `node` / `result` slot, the [`DjangoModelPermission`](#djangomodelpermission) default (authorized for free through the model override), the visibility-scoped `update` locate, and the optimizer re-fetch (the G2 gate keeps `select_related` / `prefetch_related` but suppresses `.only(...)` under the mutation operation). Its input is **serializer-derived** rather than model-column derived — the `serializer_converter` field map plus the serializer-input generator build the `<Serializer>Input` / `<Serializer>PartialInput` from the serializer's schema-time fields. Validation runs `serializer.is_valid()` then `serializer.save()`; `serializer.errors` populate the shared [`FieldError` envelope](#fielderror-envelope) (DRF's `non_field_errors` keyed under the `"__all__"` sentinel) and the post-save row is returned in the uniform slot. Bound at [`finalize_django_types`](#finalize_django_types) phase 2.5 alongside the other [`DjangoMutation`](#djangomutation) bases.

It **deliberately does not adopt graphene-django's serializer-mutation keys**: it uses `Meta.operation` (`"create"` / `"update"` only — DRF serializers do not delete), **not** graphene's runtime-dispatched `Meta.model_operations`, so an auto-dispatching `["create", "update"]` migrant becomes two package mutations each with an explicit `operation`; and it locates the `update` target by decoding the `id:` argument through the type's [`get_queryset`](#get_queryset-visibility-hook), **not** a `Meta.lookup_field`. `Meta.fields` / `Meta.exclude` (mutually exclusive) and `Meta.optional_fields` narrow the generated input; `Meta.permission_classes` carries the same write-auth seam.

`djangorestframework` is a **soft** dependency: `import django_strawberry_framework` succeeds without DRF, and `from django_strawberry_framework import *` stays DRF-free. `SerializerMutation` is the one net-new public symbol — a lazy root export resolved through the package `__getattr__` under the soft DRF guard, **not** in `__all__`. A DRF-absent consumer who reaches a serializer-mutation module (or the root symbol) gets a single install-hint `ImportError` naming `djangorestframework>=3.17.0`.

**See also:** [`DjangoMutation`](#djangomutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`FieldError` envelope](#fielderror-envelope) · [`DjangoModelPermission`](#djangomodelpermission).

## Single-upstream parity

**Status:** shipped.

The honest-parity posture for Alpha cards whose surface exists in only one of the two reference libraries. `KANBAN.md`'s "Alpha cards must claim upstream parity" decision requires each Alpha card to name its upstream equivalents in `strawberry-graphql-django` (🍓) and `graphene-django` (⚛️); when only one upstream ships the surface, the card claims parity with that single upstream and records the other's absence plainly instead of fabricating an equivalent. Precedents: [Auth mutations](#auth-mutations) (spec-040), [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) (spec-041), and the [Debug-toolbar middleware](#debug-toolbar-middleware) (spec-042 — 🍓-only: `graphene-django`'s debug story is the in-response `DjangoDebug` subsystem tracked by the [Response-extensions debug middleware](#response-extensions-debug-middleware) sibling card).

## Soft dependency

**Status:** shipped (`0.0.13`).

The package's architecture for optional integrations — `djangorestframework` (shipped `0.0.13`, [`SerializerMutation`](#serializermutation)) and `channels` (planned `0.0.14`, [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter)). Three parts, one discipline:

- **One guard, one hint.** A `require_*()` function (`require_drf()`; `require_channels()` on the `0.0.14` card) wraps the optional import into a single `ImportError` whose message is one module-level install-hint constant (`_DRF_INSTALL_HINT` / `_CHANNELS_INSTALL_HINT`) naming the verified floor. No memoization, so absence tests can re-hit the guard. The shared primitive lives in `utils/imports.py` — the package's single optional-import owner (`import_attr_if_importable`, `loaded_attr`; [`require_optional_module`](#require_optional_module) lands with the channels card) — new optional-import handling belongs there, never hand-rolled at a new call site.
- **Lazy name resolution.** A [PEP 562 lazy export](#pep-562-lazy-export) `__getattr__` (the package root for the DRF names; module-level in `routers.py` for the router) materializes the guarded symbol on first access, so `import django_strawberry_framework` never pays for an integration the consumer didn't ask for, and the install hint fires at the consumer's own `from ... import` line.
- **[Eviction-simulated absence](#eviction-simulated-absence) tests.** Absence is simulated — a `builtins.__import__` block plus strict `sys.modules` eviction and restore (`tests/rest_framework/test_soft_dependency.py`) — never a separate uninstalled CI matrix. The install hint is drift-checked against a re-typed literal in the test file (the `_HINT_SUBSTRING` discipline), and the dependency gate adds the dev-group row and regenerates `uv.lock` in the same commit.

**See also:** [`SerializerMutation`](#serializermutation) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter).

## Specialized scalar conversions

**Status:** shipped (`0.0.6`).

Adds these mappings to [Scalar field conversion](#scalar-field-conversion):

- `BigIntegerField` → JSON-safe [`BigInt`](#bigint-scalar) scalar (string-serialized at the wire to survive JavaScript's 53-bit integer limit)
- `PositiveBigIntegerField` → `BigInt`
- `JSONField` → `strawberry.scalars.JSON`
- PostgreSQL `ArrayField` → typed `list[T]` (recursive through `field.base_field`)
- PostgreSQL `HStoreField` → `strawberry.scalars.JSON` (soft-registered, only when `django.contrib.postgres.fields` imports successfully)
- `FileField` / `ImageField` read output → structured [`DjangoFileType`](#djangofiletype) / [`DjangoImageType`](#djangoimagetype) objects, nullable by default in the SDL regardless of the column's `null` / `blank` (an empty stored file resolves to `null`; `required_overrides` opts into a non-null object). Switched from `str` in `0.0.11` — breaking wire-format change, parallel to the `PositiveBigIntegerField` → `BigInt` `0.0.6` precedent; opt out of the structured object per field with an `attachment: str` annotation override. The filter / scalar-input value stays `str`; the mutation input is the [`Upload`](#upload-scalar) scalar

**See also:** [Scalar field conversion](#scalar-field-conversion) · [`BigInt` scalar](#bigint-scalar).

## Strawberry extension lifecycle

**Status:** planned for `0.0.14`.

The engine contract [`DjangoDebugExtension`](#djangodebugextension) rides. Strawberry's `SchemaExtension.on_operation` is a generator-style context hook around one GraphQL operation; a synchronous generator can serve both sync and async execution colors. The extension acquires SQL instrumentation before `yield` and assembles its payload during teardown. `SchemaExtension.get_results()` then returns per-operation metadata that Strawberry merges into `ExecutionResult.extensions`. Happy-path result collection occurs after teardown; parse and validation early returns collect before teardown. That ordering defines [Debug payload availability](#debug-payload-availability), while schema-list order defines [Response-extension merge semantics](#response-extension-merge-semantics).

**See also:** [Per-operation extension isolation](#per-operation-extension-isolation) · [Masking-extension ordering](#masking-extension-ordering).

## strawberry_config

**Status:** shipped (`0.0.7`).

Factory returning a [`StrawberryConfig`](https://strawberry.rocks) pre-populated with the package's `scalar_map` — the registration path consumers use to bind package-defined scalars (today: [`BigInt`](#bigint-scalar)) into their `strawberry.Schema(...)` call.

```python
from django_strawberry_framework import strawberry_config

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

Consumers composing custom scalars on top pass them via `extra_scalar_map=`:

```python
MyULID = NewType("MyULID", str)
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(extra_scalar_map={MyULID: my_ulid_definition}),
)
```

Consumers tuning non-scalar `StrawberryConfig` fields (`auto_camel_case`, `relay_max_results`, `name_converter`, etc.) pass those keyword arguments directly — the helper forwards every kwarg other than `extra_scalar_map=` to upstream `StrawberryConfig(...)`:

```python
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(auto_camel_case=False, relay_max_results=200),
)
```

The keyword-only `extra_scalar_map=` and the `**config_kwargs` passthrough compose: `strawberry_config(extra_scalar_map={MyULID: my_ulid_definition}, relay_max_results=200)` is supported. The single field the helper refuses to forward is `scalar_map=` (ownership goes through `extra_scalar_map=`); passing `scalar_map=` raises `ValueError`. Collision with a package-defined scalar in `extra_scalar_map` also raises `ValueError`; register the consumer scalar under a different `NewType` / class to keep both. Each call returns a fresh `StrawberryConfig` instance with a fresh `scalar_map` dict; mutations on the returned object do not leak across calls.

**See also:** [`BigInt scalar`](#bigint-scalar) · [`Upload scalar`](#upload-scalar) · [`Specialized scalar conversions`](#specialized-scalar-conversions).

## Strictness mode

**Status:** shipped (`0.0.3`).

`DjangoOptimizerExtension(strictness="off" | "warn" | "raise")` controls how the optimizer reacts when an unplanned relation access would actually lazy-load (an accidental N+1).

- `"off"` — silent production default.
- `"warn"` — logged warning per occurrence.
- `"raise"` — fail-fast `OptimizerError` for tests / dev checks.

Warnings and errors fire only when the relation access actually causes a lazy load — false positives from unhit prefetches do not trigger.

As of `0.0.9`, connection paths participate too: an unplanned, unserved nested-`<field>Connection` access fires the same `OptimizerError` (`"raise"`) / logged warning (`"warn"`) contract through the same resolver-key vocabulary the list relations use, so a nested connection that falls back to per-parent resolution (sidecar `filter:` / `orderBy:` input, divergent aliases, an `OptimizerHint.SKIP` relation, a `.distinct()` target) is no longer a silent N+1 — see [Connection-aware optimizer planning](#connection-aware-optimizer-planning).

Planned resolver keys and lookup paths are stashed on `info.context` for introspection during strictness incidents.

Interface / union sibling-concrete-type fragment narrowing (the would-be G3 strictness interaction) is deferred to the abstract-return optimizer entry card (the `BACKLOG.md` `polymorphic_interface_connections` work); strictness behavior is unchanged by that deferred work.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Schema audit](#schema-audit).

## `SyncMisuseError`

**Status:** shipped (`0.0.5`).

Typed marker for the "async `get_queryset` hook invoked from a sync resolver context" misuse. Multiple-inherits [`ConfigurationError`](#configurationerror) AND `RuntimeError` so existing handlers continue to match while future code can match the subclass directly.

- Raised by the shared `apply_type_visibility_sync` (the 0.0.9 single-sited visibility routing) on every sync visibility surface — the [Relay Node integration](#relay-node-integration) defaults `resolve_node` / `resolve_nodes`, the [`DjangoConnectionField`](#djangoconnectionfield) sync pipeline, the optimizer's sync prefetch-child build, and the [`FilterSet`](#filterset) related-visibility derive — when `cls.get_queryset` returns a coroutine; the unawaited coroutine is closed before the raise.
- Caught and rewrapped by [`FilterSet.apply`](#filterset)'s sync dispatcher so the package's two `async get_queryset` misuse surfaces emit a single typed exception.
- Exported through `django_strawberry_framework` so consumers can import it without reaching into private `types.relay`.

**See also:** [Relay Node integration](#relay-node-integration) · [`ConfigurationError`](#configurationerror) · [`FilterSet`](#filterset).

## `TestClient`

**Status:** planned for `0.0.14`.

`TestClient` / `AsyncTestClient` and the typed `Response` - thin wrappers over Django's `django.test.Client` / `django.test.AsyncClient` that post a GraphQL operation with the right content type, decode it, and return a typed `Response(errors, data, extensions, response)` carrying the raw `HttpResponse` beside the decoded triple. Imported from `django_strawberry_framework.testing` (never the package root). Construct `TestClient(path=None, client=None)`; the endpoint resolves once at construction (constructor `path=` > `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` > the `"/graphql/"` default), and a per-call `query(..., url=...)` override routes a single request without mutating the stored `path`. `query()` gains `operation_name=` and returns the typed `Response`; its default `assert_no_errors=True` raises `AssertionError` on a GraphQL-errors response (an explicit raise, so it holds under `python -O`). Multipart uploads ride the same call: `query(..., variables={"data": {"image": None}}, files={"data.image": f})` binds each path-keyed file part to its `None` placeholder (nested input objects and list indexes included, validated at the source). `login(user)` brackets a block with `force_login` / `logout` (the async twin wraps both in `sync_to_async`). Subclasses Strawberry's `strawberry.test.BaseGraphQLTestClient` over the package's existing hard `strawberry-graphql` dependency, so the family adds **no** new dependency, guard, or install hint. Companion: [`GraphQLTestCase`](#graphqltestcase).

**See also:** [`GraphQLTestCase`](#graphqltestcase).

## Django Trac #37064 hardening

**Status:** shipped (`0.0.7`).

Defensive patch for [Django Trac #37064](https://code.djangoproject.com/ticket/37064) (closed upstream as `wontfix`). The package applies the patch automatically at `DjangoStrawberryFrameworkConfig.ready` time, replacing `django.test.testcases.SimpleTestCase._remove_databases_failures` (the class where Django defines the method; `TransactionTestCase` and `TestCase` inherit it) with a variant that adds an `isinstance(method, _DatabaseFailure)` guard before the `setattr(..., method.wrapped)` step. Prevents the unrecoverable `AttributeError: 'function' object has no attribute 'wrapped'` at `tearDownClass` that the ticket documents.

Consumers get the hardening for free by having `"django_strawberry_framework"` in `INSTALLED_APPS` — no `conftest.py` workaround, no base test class to inherit, no settings key required.

Pairs with [`safe_wrap_connection_method`](#safe_wrap_connection_method) (the wrap-time half of the same defense-in-depth pattern).

**See also:** [`safe_wrap_connection_method`](#safe_wrap_connection_method) · [Multi-database cooperation](#multi-database-cooperation) · [Django `AppConfig`](#django-appconfig).

## `Upload` scalar

**Status:** shipped (`0.0.11`).

Strawberry's built-in `Upload` scalar (`NewType("Upload", bytes)`), **re-exported** from the package root (`from django_strawberry_framework import Upload`). It needs **no** `_PACKAGE_SCALAR_MAP` entry because it already resolves through Strawberry's built-in `DEFAULT_SCALAR_REGISTRY` — the deliberate contrast with the package-custom [`BigInt`](#bigint-scalar) scalar, which is absent from the default registry and must be bound through [`strawberry_config`](#strawberry_config). Generated [`DjangoMutation`](#djangomutation) `Input` / `PartialInput` types map a `FileField` / `ImageField` editable column to `Upload` (required per the shipped per-field rule — a `blank=False` / `null=False` / no-default file column is required in the create `Input`, optional otherwise and in `PartialInput`; widened to `Upload | None` on `blank` / `null`). Paired with [`DjangoFileType`](#djangofiletype) / [`DjangoImageType`](#djangoimagetype) on the output side.

**See also:** [`DjangoFileType`](#djangofiletype) · [`DjangoImageType`](#djangoimagetype) · [`DjangoMutation`](#djangomutation).

---

## Cross-subsystem invariants

**Status:** planned for 1.0.0.

Goals that the Layer-3 cards collectively satisfy by `1.0.0`:

- Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end. This rule resolves entirely at `1.0.0`.
- Filters, orders, aggregates, mutations, permissions, and connection fields all compose with [`DjangoOptimizerExtension`](#djangooptimizerextension).
- The [`FieldError` envelope](#fielderror-envelope) is shared across every mutation flavor for a consistent client contract.
- Example-project schemas reference only shipped features — never unshipped ones.

## `auto`-typed annotations

**Status:** shipped (`0.0.9`).

Strawberry's `auto` sentinel, re-exported from `django_strawberry_framework`, used as a field annotation (`field: auto`) to **declare a field for inclusion while deferring its GraphQL type to model inference** — the declare-but-infer marker. `DjangoType.__init_subclass__` detects the `StrawberryAuto` sentinel and routes the field back through the package's scalar / relation synthesis instead of treating the annotation as a consumer override.

This is distinct from a concrete consumer annotation: writing `name: str` is a consumer override that bypasses `convert_scalar`, whereas `name: auto` keeps the framework-inferred type (and its nullability / choice-enum handling). Two misuses raise [`ConfigurationError`](#configurationerror) at type creation:

- `auto` on a field **not** in the selected [`Meta.fields`](#metafields) set — an `auto` annotation cannot pull in a field the selection excludes.
- `auto` combined with an assigned `strawberry.field(...)` value on the same name — the assignment and the infer-marker conflict.

Dogfooded in the fakeshop `scalars` app (`OverriddenScalarSpecimenType.note: auto`).

## Beyond `1.0.0`

Strategic differentiators that go past `1.0.0` parity live in [`../BACKLOG.md`][backlog]. Roadmap-adjacent items already tracked there:

- Apollo Federation support — `BETTER` item 34
- Model-property / cached-property optimizer hints — folded into `BETTER` item 14 (`Meta.computed_fields`)
- Shared queryset introspection helpers (`utils/queryset.py`) — `BETTER` item 36
- Public-surface promotion discipline — `BETTER` item 37
- Layered manual relation-override test policy — `BETTER` item 38
- First-class multi-db / sharding-aware optimizer — `BETTER` item 41

Dedicated migration guides (graphene-django, strawberry-graphql-django, DRF / django-filter) are tracked in [`../KANBAN.md`][kanban] so this file can stay focused on capability lookup. For the migration code diffs, see [`../GOAL.md`'s Migration shape section][goal-migration-shape].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../BACKLOG.md
[goal]: ../GOAL.md
[goal-migration-shape]: ../GOAL.md#migration-shape
[goal-what-success-looks-like-in-your-code]: ../GOAL.md#what-success-looks-like-in-your-code
[kanban]: ../KANBAN.md
[today]: ../TODAY.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
