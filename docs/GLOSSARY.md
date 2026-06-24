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

Current package version: `0.0.12`. Alpha-quality — suitable for internal tools and prototypes, not production. The `1.0.0` release is the API-freeze boundary; after `1.0.0` ships, strict semantic versioning applies to every entry below.

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
- [`SyncMisuseError`](#syncmisuseerror) — typed marker for sync resolver paths that receive an async `get_queryset` coroutine.
- [`Upload`](#upload-scalar) — re-exported Strawberry built-in scalar for `FileField` / `ImageField` mutation inputs.
- [`apply_cascade_permissions`](#apply_cascade_permissions) — cascade a type's `get_queryset` visibility through its single-column forward FK / OneToOne edges (sync).
- [`aapply_cascade_permissions`](#apply_cascade_permissions) — async twin of `apply_cascade_permissions` (`sync_to_async` wrap); shares the entry.
- [`finalize_django_types`](#finalize_django_types) — synchronization point that resolves pending relations and applies `strawberry.type` decoration.
- [`strawberry_config`](#strawberry_config) — factory returning a `StrawberryConfig` pre-populated with the package's `scalar_map`.
- [`auto`](#auto-typed-annotations) — re-export from Strawberry for `auto`-typed field annotations (the declare-but-infer marker).
- `__version__` — package version string.

Symbols available from the `django_strawberry_framework.testing` subpackage (consumer test utilities):

- [`safe_wrap_connection_method`](#safe_wrap_connection_method) — cooperative wrap helper for monkey-patching `connections[alias]` methods without clobbering Django's `_DatabaseFailure` wrapper (the wrap-time half of the [Django Trac #37064 hardening](#django-trac-37064-hardening) defense-in-depth).
- `global_id_for` / `decode_global_id` — public Relay test helpers at the `django_strawberry_framework.testing.relay` submodule path (NOT re-exported from the `testing` root, by design); mint and decode the strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits. See [Relay Node integration](#relay-node-integration).

_Note:_ The import path is clean by construction — the registration path uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload via the [`strawberry_config`](#strawberry_config) factory, so no `DeprecationWarning` is emitted.

## Index

Alphabetical lookup. Each row links to the entry; the status column reflects current availability.

| Entry | Status |
|---|---|
| [`AggregateSet`](#aggregateset) | planned for `0.1.3` |
| [`apply_cascade_permissions`](#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Auth mutations](#auth-mutations) | planned for `0.0.13` |
| [`BigInt` scalar](#bigint-scalar) | shipped (`0.0.6`) |
| [Choice enum generation](#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](#configurationerror) | shipped (`0.0.1`) |
| [Connection-aware optimizer planning](#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [Debug-toolbar middleware](#debug-toolbar-middleware) | planned for `0.0.14` |
| [Definition-order independence](#definition-order-independence) | shipped (`0.0.4`) |
| [Django `AppConfig`](#django-appconfig) | shipped (`0.0.7`) |
| [`DjangoConnection`](#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoConnectionField`](#djangoconnectionfield) | shipped (`0.0.9`) |
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
| [`FieldError` envelope](#fielderror-envelope) | shipped (`0.0.11`) |
| [`FieldSet`](#fieldset) | planned for `0.1.1` |
| [`FilterSet`](#filterset) | shipped (`0.0.8`) |
| [`filter_input_type`](#filter_input_type) | shipped (`0.0.8`) |
| [`finalize_django_types`](#finalize_django_types) | shipped (`0.0.4`) |
| [FK-id elision](#fk-id-elision) | shipped (`0.0.3`) |
| [`get_child_queryset`](#get_child_queryset) | planned for `0.1.3` |
| [`get_queryset` visibility hook](#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`GraphQLTestCase`](#graphqltestcase) | planned for `0.0.14` |
| [Input type generation](#input-type-generation) | shipped (`0.0.11`) |
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
| [Per-field permission hooks](#per-field-permission-hooks) | planned for `0.1.1` |
| [Plan cache](#plan-cache) | shipped (`0.0.3`) |
| [Queryset diffing](#queryset-diffing) | shipped (`0.0.3`) |
| [`RelatedAggregate`](#relatedaggregate) | planned for `0.1.3` |
| [`RelatedFilter`](#relatedfilter) | shipped (`0.0.8`) |
| [`RelatedOrder`](#relatedorder) | shipped (`0.0.8`) |
| [Relation handling](#relation-handling) | shipped (`0.0.1`+) |
| [Relay Node integration](#relay-node-integration) | shipped (`0.0.5`) |
| [RELAY_GLOBALID_STRATEGY](#relay_globalid_strategy) | shipped (`0.0.9`) |
| [Response-extensions debug middleware](#response-extensions-debug-middleware) | planned for `0.0.14` |
| [`safe_wrap_connection_method`](#safe_wrap_connection_method) | shipped (`0.0.7`) |
| [Scalar field conversion](#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Scalar field override semantics](#scalar-field-override-semantics) | shipped (`0.0.6`) |
| [Schema audit](#schema-audit) | shipped (`0.0.3`) |
| [Schema export management command](#schema-export-management-command) | shipped (`0.0.7`) |
| [Schema introspection management command](#schema-introspection-management-command) | shipped (`0.0.9`) |
| [`SerializerMutation`](#serializermutation) | planned for `0.0.13` |
| [Specialized scalar conversions](#specialized-scalar-conversions) | shipped (`0.0.6`) |
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
- **Permissions:** [`get_queryset` visibility hook](#get_queryset-visibility-hook) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [`DjangoModelPermission`](#djangomodelpermission) · [Per-field permission hooks](#per-field-permission-hooks).
- **Relay:** [Relay Node integration](#relay-node-integration) · [RELAY_GLOBALID_STRATEGY](#relay_globalid_strategy) · [`DjangoNodeField`](#djangonodefield) · [`DjangoNodesField`](#djangonodesfield) · [`DjangoConnectionField`](#djangoconnectionfield) · [`DjangoConnection`](#djangoconnection) · [`Meta.connection`](#metaconnection) · [`Meta.relation_shapes`](#metarelation_shapes) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning) · [`SyncMisuseError`](#syncmisuseerror).
- **List fields:** [`DjangoListField`](#djangolistfield) · [Relation handling](#relation-handling).
- **Mutations:** [`DjangoMutation`](#djangomutation) · [`DjangoMutationField`](#djangomutationfield) · [`DjangoFormMutation`](#djangoformmutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`SerializerMutation`](#serializermutation) · [Input type generation](#input-type-generation) · [`FieldError` envelope](#fielderror-envelope) · [Auth mutations](#auth-mutations).
- **File / image uploads:** [`Upload` scalar](#upload-scalar) · [`DjangoFileType`](#djangofiletype) · [`DjangoImageType`](#djangoimagetype).
- **Integration / tooling:** [Django `AppConfig`](#django-appconfig) · [Schema export management command](#schema-export-management-command) · [Schema introspection management command](#schema-introspection-management-command) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) · [Debug-toolbar middleware](#debug-toolbar-middleware) · [Response-extensions debug middleware](#response-extensions-debug-middleware).
- **Testing:** [`safe_wrap_connection_method`](#safe_wrap_connection_method) · [Django Trac #37064 hardening](#django-trac-37064-hardening) · [`TestClient`](#testclient) · [`GraphQLTestCase`](#graphqltestcase).

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

## Auth mutations

**Status:** planned for `0.0.13`.

`login` / `logout` / `register` mutations plus a `current_user` query helper. Opt-in via explicit import; not bundled into the default schema. Composes with [`DjangoMutation`](#djangomutation) and `django.contrib.auth`.

**See also:** [`DjangoMutation`](#djangomutation).

## `BigInt` scalar

**Status:** shipped (`0.0.6`).

JSON-safe scalar typically used to map Django's 64-bit integer fields `BigIntegerField` and `PositiveBigIntegerField` (not `BigAutoField`). Technically arbitrary-precision: serialized via Python `str(int_value)`, which handles any `int`. Wire format is a decimal string to survive GraphQL's signed 32-bit `Int` boundary (executing a query returning an `int`-annotated value past `2**31 - 1` raises a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`). Strict parser accepts Python `int` (excluding `bool`) and strings matching `^(0|-?[1-9][0-9]*)$` — plain ASCII decimal, optional leading minus for non-zero, no leading zeroes (except `"0"` itself), no underscores, no plus sign, no Unicode digits. Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`. Part of [Specialized scalar conversions](#specialized-scalar-conversions).

Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])` (the optimizer is a module-level singleton wrapped in a factory — see [`DjangoOptimizerExtension`](#djangooptimizerextension)). Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol. The migration applies to any schema that resolves to `BigInt` — including [`DjangoType`](#djangotype) schemas whose fields are backed by `BigIntegerField` or `PositiveBigIntegerField` (resolved to `BigInt` by the [`Specialized scalar conversions`](#specialized-scalar-conversions) converter table) even when the consumer never imports or annotates `BigInt` directly.

**See also:** [Scalar field conversion](#scalar-field-conversion) · [Specialized scalar conversions](#specialized-scalar-conversions).

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

The optimizer recognizes synthesized `<field>Connection` selections inside a parent's selection walk — via the declaring type's `DjangoTypeDefinition``.relation_connections` metadata, never by reaching into [`DjangoConnectionField`](#djangoconnectionfield) internals — and plans a windowed `Prefetch` for each under a package-reserved `_dst_<field>_connection` `to_attr`. The window is built from `RowNumber()` / `Count(1)` window functions partitioned by the parent attach key, with the slice derived from the connection's resolved `first` / `last` / `before` / `after` arguments capped by `relay_max_results`; the child plan carries the target's visibility, projections, and any deeper nested connections, and reproduces the pipeline's deterministic (pk-terminal) order so cursors match.

The generated connection class then serves `edges` / cursors / `pageInfo` / `totalCount` directly from the `_dst_row_number` / `_dst_total_count` annotations on the prefetched rows — one window-function query per relation per request, zero per-parent queries on the fast path — and falls back to the shipped per-parent pipeline for an ambiguous empty window (`first: 0`, an overshot `after:`). A nested connection is left **unplanned** (and falls back per parent, visible to [Strictness mode](#strictness-mode)) when it carries `filter:` / `orderBy:` sidecar input, when aliased duplicates carry divergent arguments, when the relation's hint is [`OptimizerHint`](#optimizerhint)`.SKIP`, when the built child queryset is `.distinct()`, or when only a secondary [`DjangoType`](#djangotype) shapes the relation differently from the model's primary type. The `.distinct()` fallback is a correctness guard: SQL evaluates window functions before `DISTINCT`, so a `Count(1) OVER` over a distinct child would over-count — the relation is conservatively left per-parent instead. The mechanism needs a window-capable backend (the package floor `Django>=5.2` with SQLite ≥ 3.25 covers every supported configuration); an exotic backend without window support raises its own `NotSupportedError`, and the recourse is `relation_shapes = {"<field>": "list"}` or running without the optimizer.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [Plan cache](#plan-cache) · [`DjangoOptimizerExtension`](#djangooptimizerextension).

## Debug-toolbar middleware

**Status:** planned for `0.0.14`.

`django-debug-toolbar` SQL-panel integration during `/graphql/` requests. Mirrors `strawberry-django`'s `middlewares/debug_toolbar.py` shape.

Distinct from the [Response-extensions debug middleware](#response-extensions-debug-middleware) — this is the server-side panel, that is in-response surfacing through the GraphQL response's `extensions` envelope. Both useful, not mutually exclusive.

**See also:** [Response-extensions debug middleware](#response-extensions-debug-middleware).

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

## Django `AppConfig`

**Status:** shipped (`0.0.7`).

`django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. The `ready()` body imports `django_strawberry_framework._django_patches` and calls `apply()` to install the [Django Trac #37064 hardening](#django-trac-37064-hardening) at Django app-load time. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's implicit single-AppConfig discovery resolves the explicit class.

**See also:** [Django Trac #37064 hardening](#django-trac-37064-hardening) · [Schema export management command](#schema-export-management-command).

## `DjangoConnection`

**Status:** shipped (`0.0.9`).

Generic Relay connection base `DjangoConnection[T]`, a `strawberry.relay.ListConnection` subclass that owns the package's `first` + `last` mutual-exclusivity guard (which Strawberry's `SliceMetadata.from_arguments` does not provide) and adds nothing else — it carries no `total_count` field. [`DjangoConnectionField`](#djangoconnectionfield) never hands the schema this generic base directly; it resolves each node type through a generated concrete `<TypeName>Connection` subclass (the `totalCount` opt-in via [`Meta.connection`](#metaconnection) only controls whether the `total_count` members are added), because a bare generic alias loses the `resolve_connection` override at Strawberry's generic specialization.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [Relay Node integration](#relay-node-integration).

## `DjangoConnectionField`

**Status:** shipped (`0.0.9`).

Relay-style connection field with `edges` / `node` / `pageInfo` / `totalCount`, cursor-based pagination, and `filter:` / `orderBy:` arguments derived from the wrapped `DjangoType`'s [`filterset_class`](#metafilterset_class) / [`orderset_class`](#metaorderset_class) sidecars via a synthesized resolver signature (no hand-written list resolver, no parallel argument declarations). Opt-in `totalCount` via [`Meta.connection`](#metaconnection)`= {"total_count": True}` resolves through a generated per-target `<TypeName>Connection` class — counted on the post-filter pre-slice queryset, selection-gated, per connection instance. The composition pipeline runs `get_queryset` visibility -> `filter` -> `orderBy` -> default deterministic pk-ordering -> optimizer-plan -> cursor slice, and a package-owned guard rejects `first` + `last` together with a `GraphQLError`. The `search:` argument is reserved for `Meta.search_fields` (`0.1.2`) and is not generated in `0.0.9`. As of `0.0.9`, relations between Relay-Node-shaped types synthesize `<field>Connection` siblings through this same machinery — see [`Meta.relation_shapes`](#metarelation_shapes).

The field owns its own optimizer cooperation point (the plan-application logic extracted from [`DjangoOptimizerExtension`](#djangooptimizerextension)`._optimize`) because Strawberry's connection slicing hides the pre-slice queryset from the schema middleware. That seam now also feeds nested `<field>Connection` window planning: a selected nested connection gets a windowed `Prefetch` so its page costs no per-parent query — see [Connection-aware optimizer planning](#connection-aware-optimizer-planning) (shipped `0.0.9`). A [Strictness mode](#strictness-mode) `"raise"` run now flags an unplanned, unserved nested-connection access through the same resolver-key vocabulary the generated list-relation resolvers use.

**See also:** [`DjangoConnection`](#djangoconnection) · [`DjangoNodeField`](#djangonodefield) · [Relay Node integration](#relay-node-integration) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning) · [`Meta.relation_shapes`](#metarelation_shapes).

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

A Channels `ProtocolTypeRouter`-wrapping helper for consumers using Channels. Soft dependency on `channels`; symbol name is intentionally distinct from `strawberry-django`'s `AuthGraphQLProtocolTypeRouter` to avoid migration ambiguity.

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

**See also:** [`DjangoFormMutation`](#djangoformmutation) · [`DjangoMutation`](#djangomutation) · [`FieldError` envelope](#fielderror-envelope).

## `DjangoModelPermission`

**Status:** shipped (`0.0.11`).

The default write-authorization permission class consumers pass to [`DjangoMutation`](#djangomutation)'s `Meta.permission_classes` (which defaults to `[DjangoModelPermission]`). It enforces the Django `add` / `change` / `delete` **model permissions** — `create` requires `add`, `update` requires `change`, `delete` requires `delete` — so an anonymous caller or one missing the relevant model perm is denied. Write authorization is a first-class, DRF-shaped contract run by all three operations through an overridable `check_permission(info, operation, data, instance=None)` hook (`create` runs the check before validation with `instance=None`; `update` / `delete` run it after the visibility lookup with the located instance). It is kept **separate** from [`get_queryset`](#get_queryset-visibility-hook) visibility: can-view ≠ can-write — `get_queryset` scopes which rows are *visible*, `permission_classes` decides whether they may be *written*. A denial raises a top-level `GraphQLError` (not a [`FieldError`](#fielderror-envelope) envelope entry). An *unset* `Meta.permission_classes` resolves to `[DjangoModelPermission]` (the safe default — anonymous denied); an explicit **empty** `Meta.permission_classes = []` disables write authorization entirely (AllowAny), a deliberate opt-out of the safe default that mirrors DRF — there is no accidental route into it, so use `[]` only for an intentionally public write surface. A `check_permission` / `has_permission` hook must be **synchronous** (return a `bool`): the write pipeline runs the auth check synchronously, so an `async def` hook is rejected with a `SyncMisuseError` rather than silently treated as allow. Exported from the package root.

**See also:** [`DjangoMutation`](#djangomutation) · [`get_queryset` visibility hook](#get_queryset-visibility-hook) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [Per-field permission hooks](#per-field-permission-hooks).

## `DjangoMutation`

**Status:** shipped (`0.0.11`).

Base class for the write side, configured through a nested `class Meta` (the DRF shape, not Strawberry decorators). `Meta.model` names the Django model; `Meta.operation` selects the verb — one of `"create"` / `"update"` / `"delete"`. Optional `Meta.fields` / `Meta.exclude` narrow the generated input shape; `Meta.input_class` / `Meta.partial_input_class` supply a hand-written input (which must follow the generated field-naming scheme); `Meta.permission_classes` sets write authorization (see [`DjangoModelPermission`](#djangomodelpermission)). The class is registered at creation and bound at [`finalize_django_types`](#finalize_django_types) phase 2.5, which resolves the model's **primary** [`DjangoType`](#djangotype) for the return payload and materializes the generated [`Input` / `PartialInput`](#input-type-generation) and `<Name>Payload` classes before `strawberry.Schema(...)` runs. The resolver pipeline runs decode → authorize → `full_clean()` → write → optimizer-re-fetch → payload, sync and async, with the write inside one `transaction.atomic()` (async via a single `sync_to_async(thread_sensitive=True)`). Validation failures surface through the shared [`FieldError` envelope](#fielderror-envelope) rather than raising at the GraphQL boundary; the post-write row is re-fetched and optimizer-planned for the response selection (under the mutation operation the G2 gate keeps `select_related` / `prefetch_related` but suppresses [`.only(...)`](#only-projection)). Exposed on the schema's `Mutation` type through the [`DjangoMutationField`](#djangomutationfield) factory. Exported from the package root.

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

Calling it a second time is a no-op. Declaring a new concrete `DjangoType` after finalization raises [`ConfigurationError`](#configurationerror); tests that need a new registry lifecycle should use `registry.clear()` and fresh type classes.

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

## `GraphQLTestCase`

**Status:** planned for `0.0.14`.

`unittest.TestCase` subclass for live HTTP-level testing patterns. The `GraphQLTestCase` name and mixin-first shape come from `graphene-django`'s `utils/testing.py` (`GraphQLTestCase` / `GraphQLTestMixin` / `graphql_query`); the underlying HTTP client mirrors `strawberry-django`'s `test/client.py` ([`TestClient`](#testclient) / `AsyncTestClient`). Provides `query()` / `mutate()` helpers and assertion shortcuts.

**See also:** [`TestClient`](#testclient).

## Input type generation

**Status:** shipped (`0.0.11`).

[`DjangoMutation`](#djangomutation) auto-generates two input types from the model's **editable** fields (narrowed by the mutation's own `Meta.fields` / `Meta.exclude` — **not** the read-side [`DjangoType`](#djangotype) selection), reusing the read-side scalar / choice-enum / specialized-scalar converters so read and write share one wire contract:

- **`<Model>Input`** — the create shape (`Model.objects.create(...)` semantics). A field is required only when it has no usable Django `default`, is not `null=True`, and (for text fields) is not `blank=True`; fields that do have a default / blank / null are optional (`strawberry.UNSET`). This is the DRF `required=False`-from-`default`/`blank`/`null` rule, not a blanket "every field required".
- **`<Model>PartialInput`** — every field optional, `UNSET`-defaulted (matches `Model.objects.update(...)` semantics).

Editable-field selection drops the pk, `auto_now` / `auto_now_add` / `editable=False` columns, and reverse relations. A forward FK / OneToOne becomes a single `<field>_id` typed as the target's id — a `GlobalID` for a Relay-Node target, the raw pk scalar otherwise — type-checked against the relation target at decode (a wrong-type id is a [`FieldError`](#fielderror-envelope), never a cross-model pk lookup); an M2M becomes `list[<id>]` (replace-on-provide / clear-on-empty / unchanged-on-omit). The canonical full editable shape takes the stable `<Model>Input` / `<Model>PartialInput` name; a narrowed (`Meta.fields` / `Meta.exclude`) shape takes a deterministic shape-derived name, and two **distinct** shapes colliding on one generated name raise [`ConfigurationError`](#configurationerror) at finalization (identical shapes dedupe and share one type). All are materialized as module globals. The relation-override contract from `spec-010` holds: a consumer-authored input field is honored, not clobbered by a generated one.

**See also:** [`DjangoMutation`](#djangomutation) · [`FieldError` envelope](#fielderror-envelope) · [`Upload` scalar](#upload-scalar).

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

Direction enum used as the leaf value in generated order input types. Six members: `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`. The `resolve(field_path)` method returns Django `OrderBy` expressions: `ASC` / `DESC` map to `F(field_path).asc()` / `F(field_path).desc()` (no NULLS positioning); the four NULLS-positioning members map to `F(field_path).asc(nulls_first=True)` / `F(field_path).asc(nulls_last=True)` / `F(field_path).desc(nulls_first=True)` / `F(field_path).desc(nulls_last=True)` respectively. [`OrderSet`](#orderset) calls `Ordering.resolve(...)` for every active input field and passes the resulting `OrderBy` expressions to `queryset.order_by(...)` in list-element order.

**See also:** [`OrderSet`](#orderset) · [`order_input_type`](#order_input_type).

## `OrderSet`

**Status:** shipped (`0.0.8`).

Declarative `Meta.model` / `Meta.fields` (list form or `"__all__"` shorthand for every column-backed model field — includes forward FK / OneToOne columns; excludes reverse relations and M2M managers); [`RelatedOrder`](#relatedorder) for cross-relation traversal; `check_*_permission` denial gates with **active-input-only scope** plus active-branch double-dispatch for `RelatedOrder` branches (parent's `check_<branch>_permission` fires alongside child orderset's field gates, deduped per `(OrderSet class, method name)`); list-shaped `orderBy:` argument with list-element-order tie-breaker mechanism; six-member [`Ordering`](#ordering) enum with NULLS positioning; cycle-safe lazy resolution via the five-layer port. Layer 6 (dynamic `OrderSet` generation against a connection-field meta dict) is a standing deferred non-goal: the connection field ([`DjangoConnectionField`](#djangoconnectionfield)) resolves ordering from the already-resolved [`Meta.orderset_class`](#metaorderset_class) sidecar directly rather than auto-generating an `OrderSet`, so no dynamic order factory is shipped.

The resolver-facing API is the classmethod pair `OrderSet.apply_sync(input_value, queryset, info)` and `OrderSet.apply_async(input_value, queryset, info)` (sync resolvers call the former; async resolvers await the latter), mirroring the shipped filter subsystem's shape.

**See also:** [`Meta.orderset_class`](#metaorderset_class) · [`RelatedOrder`](#relatedorder) · [`Ordering`](#ordering) · [`order_input_type`](#order_input_type) · [`FilterSet`](#filterset).

## `order_input_type`

**Status:** shipped (`0.0.8`).

Factory returning the **element type** `Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` for resolver-argument annotations; eager validation; consumer usage `order_by: list[order_input_type(BranchOrder)] | None = None` (the list wrap matches the `orderBy: [<T>OrderInputType!]` list-shaped GraphQL argument); orphan validation at finalize.

The helper validates its [`OrderSet`](#orderset) argument eagerly so a typo at the resolver signature site fails loud at module import. Finalize-time orphan validation catches helper-referenced order sets that were never wired through [`Meta.orderset_class`](#metaorderset_class) — tracked via a `_helper_referenced_ordersets` ledger that `registry.clear()` co-clears.

**See also:** [`OrderSet`](#orderset) · [`Ordering`](#ordering) · [`Meta.orderset_class`](#metaorderset_class).

## Per-field permission hooks

**Status:** planned for `0.1.1`.

Methods named `check_<field>_permission` on the type's [`FieldSet`](#fieldset) gate access to that field. Two failure modes:

- **Redaction** — silent safe-value fallback (`None`, empty string, sentinel) so the response shape stays stable.
- **Denial** — raise `GraphQLError` so the response carries an `errors` entry for that path.

The read gate's surface is pinned now (Decision 2 of the `0.0.10` permissions spec) and the implementation lands with the `0.1.1` [`FieldSet`](#fieldset) card: the **host** is `FieldSet` (wired via [`Meta.fields_class`](#metafields_class), which stays in `DEFERRED_META_KEYS` until then); the **signature** is `check_<field>_permission(self, info)` (an `info`-shaped read gate that runs per resolved field — distinct from the `(self, request)`-shaped input gates that judge filter / order *input*). **Composition with the cascade:** a field gate does **not** short-circuit cascade visibility — [`apply_cascade_permissions`](#apply_cascade_permissions) narrows the queryset first and field gates run only on surviving rows, so a field denial never leaks the existence of a cascade-hidden row.

Composes with filter / order / aggregate permission gates and with the post-write return value of mutations.

**See also:** [`FieldSet`](#fieldset) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [`get_queryset` visibility hook](#get_queryset-visibility-hook).

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

The schema-wide default Relay `GlobalID` encode strategy, read from `DJANGO_STRAWBERRY_FRAMEWORK["RELAY_GLOBALID_STRATEGY"]`. It sets the project-wide default that every Relay-Node-shaped [`DjangoType`](#djangotype) inherits unless the type declares its own [`Meta.globalid_strategy`](#metaglobalid_strategy); precedence is `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → `"model"`. It accepts the same string values as the per-type key — `"model"` (default) / `"type"` / `"type+model"` — see [`Meta.globalid_strategy`](#metaglobalid_strategy) for the full strategy table and the callable form (a callable is per-type only).

The setting is read through the thin `conf.py` reader and validated at finalization by the same shared validator the `Meta` key uses; an unknown value raises [`ConfigurationError`](#configurationerror). The resolved strategy is frozen at schema-build time — the `GlobalID` format is a stable schema contract, not request-scoped state.

```python
DJANGO_STRAWBERRY_FRAMEWORK = {
    "RELAY_GLOBALID_STRATEGY": "type+model",
}
```

**See also:** [`Meta.globalid_strategy`](#metaglobalid_strategy) · [Relay Node integration](#relay-node-integration) · [`ConfigurationError`](#configurationerror).

## Response-extensions debug middleware

**Status:** planned for `0.0.14`.

Surfaces executed SQL queries and raised exceptions through the GraphQL response's `extensions` envelope so frontend clients can read them without the toolbar. Distinct from [Debug-toolbar middleware](#debug-toolbar-middleware): this is in-response surfacing, that is server-side panel.

**See also:** [Debug-toolbar middleware](#debug-toolbar-middleware).

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

`django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`. `--path` omitted writes SDL to `self.stdout`; `--path <file>` writes UTF-8 SDL to the named path and reports `Wrote schema to <file>` via `self.style.SUCCESS`. `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, missing positional argument, bare `--path` with no value, empty-string `--path`, and file-write `OSError` (missing parent directory, permission denied, target is a directory). No `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7`.

**See also:** [Django `AppConfig`](#django-appconfig) · [Schema introspection management command](#schema-introspection-management-command).

## Schema introspection management command

**Status:** shipped (`0.0.9`).

`django_strawberry_framework/management/commands/inspect_django_type.py` ships `Command(BaseCommand)` as `manage.py inspect_django_type <Type> [--schema <selector>]` — a diagnostic that prints, per selected field, the Django field name → Django field type → resolved GraphQL type → nullability → which converter row fired. It is a strict reader of the existing introspection surface: the resolved GraphQL type and nullability are read from the authoritative post-finalize record — `origin.__annotations__` for auto-synthesized scalar and relation fields (already reflecting `Meta.nullable_overrides` / `Meta.required_overrides`), except a `relation_shapes` `"connection"`-shaped relation, whose suppressed list annotation forces the row to read the synthesized `<rel>_connection` sibling from `origin.__strawberry_definition__`; and the finalized Strawberry field metadata `origin.__strawberry_definition__` for consumer-authored fields (annotation or `strawberry.field` overrides), whose `origin.__annotations__` entry is an unrenderable `StrawberryAnnotation` or unresolved forward-ref string; an unresolved forward reference surfaces as Strawberry's `UNRESOLVED` sentinel and raises `CommandError` rather than printing a bogus type — while [`SCALAR_MAP`](#scalar-field-conversion) is re-walked only to NAME the converter row, never to re-derive nullability via `convert_scalar`.

The positional `type` argument dispatches by shape: a **dotted** object path (`apps.library.schema.BookType`) resolves via Django's `import_string`, and a dotted import failure raises `CommandError` carrying the **original** error (never masked by a registry fallback); a **bare** name (`BookType`) resolves via a unique `__name__` registry lookup (a post-schema-import convenience). The optional `--schema <selector>` is imported first via Strawberry's `import_module_symbol(..., default_symbol_name="schema")` (mirroring [Schema export management command](#schema-export-management-command), accepting both `config.schema` and `config.schema:schema`) so a cold CLI process registers + finalizes every type before resolution. On a [Relay-Node-shaped](#relay-node-integration) type the suppressed primary key reports the interface-supplied `GlobalID!` / `relay.Node id` row rather than indexing the (absent) `origin.__annotations__[pk_name]`.

`CommandError` is raised for: an unresolvable argument; an ambiguous bare name (≥2 registered types share the `__name__` — candidates listed by `module.qualname`); a resolved symbol that is not a [`DjangoType`](#djangotype) subclass; a `DjangoType` with no `__django_strawberry_definition__` (abstract / no-`Meta` base — "not a registered DjangoType"); and a `DjangoType` whose `definition.finalized is False` ("`finalize_django_types()` has not run — pass `--schema …`"). The last two are distinct branches. No `--json` / `--watch` mode in `0.0.9` (single human-readable table, matching the `export_schema` posture).

**See also:** [Schema export management command](#schema-export-management-command) · [`DjangoType`](#djangotype) · [Relay Node integration](#relay-node-integration) · [Scalar field conversion](#scalar-field-conversion).

## `SerializerMutation`

**Status:** planned for `0.0.13`.

Consumes DRF `Serializer` / `ModelSerializer` via `Meta.serializer_class`, `Meta.lookup_field`, `Meta.model_operations`, `Meta.optional_fields`. Existing serializers move to GraphQL without re-declaring validation; input-type factory derives the Strawberry input shape from the serializer's fields. Soft dependency on `rest_framework`.

**See also:** [`DjangoMutation`](#djangomutation) · [`FieldError` envelope](#fielderror-envelope).

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

`TestClient` and `AsyncTestClient` helpers for live HTTP-level testing patterns. Mirrors `strawberry-django`'s `test/client.py` shape. Companion: [`GraphQLTestCase`](#graphqltestcase).

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
