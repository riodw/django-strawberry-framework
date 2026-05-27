# Glossary

Glossary of every public symbol, `Meta` key, configuration argument, and named behavior in `django-strawberry-framework`. Every entry below has a stable anchor — `#djangotype`, `#fk-id-elision`, `#metafilterset_class`, and so on — so this file is intended to be linked directly from documentation, code comments, example projects, and migration notes.

Companion files:

- [`../GOAL.md`](../GOAL.md) — the pitch / vision and a complete `1.0.0`-shape walkthrough (the astronomy showcase).
- [`../TODAY.md`](../TODAY.md) — the current example-app usage snapshot.
- [`../KANBAN.md`](../KANBAN.md) — per-card ship sequencing.
- [`../BACKLOG.md`](../BACKLOG.md) — strategic post-`1.0.0` differentiators.

## Status legend

- `shipped` — implemented, tested, available in the current package surface.
- `planned for X.Y.Z` — committed package direction, not implemented yet; tracked in [`../KANBAN.md`](../KANBAN.md) against a target patch version.
- `deferred` — reserved for later design or blocked on another feature.
- `alpha constraint` — current behavior that works but is intentionally narrower than the eventual API.
- `post-1.0.0` — strategic differentiation tracked in [`../BACKLOG.md`](../BACKLOG.md), not on the roadmap to `1.0.0`.

Current package version: `0.0.7`. Alpha-quality — suitable for internal tools and prototypes, not production. The `1.0.0` release is the API-freeze boundary; after `1.0.0` ships, strict semantic versioning applies to every entry below.

## Public exports

Symbols re-exported from `django_strawberry_framework`:

- [`BigInt`](#bigint-scalar) — JSON-safe scalar for 64-bit integer fields.
- [`DjangoListField`](#djangolistfield) — non-Relay `list[T]` factory function for root Query fields.
- [`DjangoType`](#djangotype) — model-backed Strawberry type base class.
- [`DjangoOptimizerExtension`](#djangooptimizerextension) — Strawberry schema extension that does ORM optimization.
- [`OptimizerHint`](#optimizerhint) — typed wrapper for per-relation optimizer overrides.
- [`finalize_django_types`](#finalize_django_types) — synchronization point that resolves pending relations and applies `strawberry.type` decoration.
- [`strawberry_config`](#strawberry_config) — factory returning a `StrawberryConfig` pre-populated with the package's `scalar_map`.
- `auto` — re-export from Strawberry for `auto`-typed field annotations inside this package's import surface.
- `__version__` — package version string.

Symbols available from the `django_strawberry_framework.test` subpackage (consumer test utilities):

- [`safe_wrap_connection_method`](#safe_wrap_connection_method) — cooperative wrap helper for monkey-patching `connections[alias]` methods without clobbering Django's `_DatabaseFailure` wrapper (the wrap-time half of the [Django Trac #37064 hardening](#django-trac-37064-hardening) defense-in-depth).

_Note:_ The import path is clean by construction — the registration path uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload via the [`strawberry_config`](#strawberry_config) factory, so no `DeprecationWarning` is emitted.

## Index

Alphabetical lookup. Each row links to the entry; the status column reflects current availability.

| Entry | Status |
|---|---|
| [`AggregateSet`](#aggregateset) | planned for `0.1.3` |
| [`apply_cascade_permissions`](#apply_cascade_permissions) | planned for `0.0.10` |
| [Auth mutations](#auth-mutations) | planned for `0.0.11` |
| [`BigInt` scalar](#bigint-scalar) | shipped (`0.0.6`) |
| [Choice enum generation](#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](#configurationerror) | shipped (`0.0.1`) |
| [Connection-aware optimizer planning](#connection-aware-optimizer-planning) | planned for `0.0.9` |
| [Debug-toolbar middleware](#debug-toolbar-middleware) | planned for `0.0.12` |
| [Definition-order independence](#definition-order-independence) | shipped (`0.0.4`) |
| [Django `AppConfig`](#django-appconfig) | shipped (`0.0.7`) |
| [`DjangoConnection`](#djangoconnection) | planned for `0.0.9` |
| [`DjangoConnectionField`](#djangoconnectionfield) | planned for `0.0.9` |
| [`DjangoFileType`](#djangofiletype) | planned for `0.0.11` |
| [`DjangoFormMutation`](#djangoformmutation) | planned for `0.0.11` |
| [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) | planned for `0.0.12` |
| [`DjangoImageType`](#djangoimagetype) | planned for `0.0.11` |
| [`DjangoListField`](#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoModelFormMutation`](#djangomodelformmutation) | planned for `0.0.11` |
| [`DjangoMutation`](#djangomutation) | planned for `0.0.11` |
| [`DjangoNodeField`](#djangonodefield) | planned for `0.0.9` |
| [`DjangoOptimizerExtension`](#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](#djangotype) | shipped (`0.0.5`) |
| [`FieldError` envelope](#fielderror-envelope) | planned for `0.0.11` |
| [`FieldSet`](#fieldset) | planned for `0.1.1` |
| [`FilterSet`](#filterset) | planned for `0.0.8` |
| [`finalize_django_types`](#finalize_django_types) | shipped (`0.0.4`) |
| [FK-id elision](#fk-id-elision) | shipped (`0.0.3`) |
| [`get_child_queryset`](#get_child_queryset) | planned for `0.1.3` |
| [`get_queryset` visibility hook](#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`GraphQLTestCase`](#graphqltestcase) | planned for `0.0.12` |
| [Input type generation](#input-type-generation) | planned for `0.0.11` |
| [`Meta.aggregate_class`](#metaaggregate_class) | planned for `0.1.3` |
| [`Meta.choice_enum_names`](#metachoice_enum_names) | planned for `0.1.4` |
| [`Meta.description`](#metadescription) | shipped |
| [`Meta.exclude`](#metaexclude) | shipped |
| [`Meta.fields`](#metafields) | shipped |
| [`Meta.fields_class`](#metafields_class) | planned for `0.1.1` |
| [`Meta.filterset_class`](#metafilterset_class) | planned for `0.0.8` |
| [`Meta.interfaces`](#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.model`](#metamodel) | shipped |
| [`Meta.name`](#metaname) | shipped |
| [`Meta.optimizer_hints`](#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`Meta.orderset_class`](#metaorderset_class) | planned for `0.0.8` |
| [`Meta.primary`](#metaprimary) | shipped (`0.0.6`) |
| [`Meta.search_fields`](#metasearch_fields) | planned for `0.1.2` |
| [Multi-database cooperation](#multi-database-cooperation) | shipped (`0.0.7`) |
| [`only()` projection](#only-projection) | shipped (`0.0.2`) |
| [`OptimizerHint`](#optimizerhint) | shipped (`0.0.3`) |
| [`OrderSet`](#orderset) | planned for `0.0.8` |
| [Per-field permission hooks](#per-field-permission-hooks) | planned for `0.0.10` |
| [Plan cache](#plan-cache) | shipped (`0.0.3`) |
| [Queryset diffing](#queryset-diffing) | shipped (`0.0.3`) |
| [`RelatedAggregate`](#relatedaggregate) | planned for `0.1.3` |
| [`RelatedFilter`](#relatedfilter) | planned for `0.0.8` |
| [`RelatedOrder`](#relatedorder) | planned for `0.0.8` |
| [Relation handling](#relation-handling) | shipped (`0.0.1`+) |
| [Relay Node integration](#relay-node-integration) | shipped (`0.0.5`) |
| [Response-extensions debug middleware](#response-extensions-debug-middleware) | planned for `0.0.12` |
| [`safe_wrap_connection_method`](#safe_wrap_connection_method) | shipped (`0.0.7`) |
| [Scalar field conversion](#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Scalar field override semantics](#scalar-field-override-semantics) | shipped (`0.0.6`) |
| [Schema audit](#schema-audit) | shipped (`0.0.3`) |
| [Schema export management command](#schema-export-management-command) | shipped (`0.0.7`) |
| [`SerializerMutation`](#serializermutation) | planned for `0.0.11` |
| [Specialized scalar conversions](#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [strawberry_config](#strawberry_config) | shipped ([Unreleased]) |
| [Strictness mode](#strictness-mode) | shipped (`0.0.3`) |
| [`TestClient`](#testclient) | planned for `0.0.12` |
| [Django Trac #37064 hardening](#django-trac-37064-hardening) | shipped (`0.0.7`) |
| [`Upload` scalar](#upload-scalar) | planned for `0.0.11` |

## Browse by category

For readers exploring rather than looking up a specific term:

- **Type generation:** [`DjangoType`](#djangotype) · [`Meta.model`](#metamodel) · [`Meta.fields`](#metafields) · [`Meta.exclude`](#metaexclude) · [`Meta.name`](#metaname) · [`Meta.description`](#metadescription) · [`Meta.primary`](#metaprimary) · [`Meta.interfaces`](#metainterfaces) · [Definition-order independence](#definition-order-independence) · [`finalize_django_types`](#finalize_django_types) · [`ConfigurationError`](#configurationerror).
- **Field conversion:** [Scalar field conversion](#scalar-field-conversion) · [Choice enum generation](#choice-enum-generation) · [Relation handling](#relation-handling) · [Specialized scalar conversions](#specialized-scalar-conversions) · [Scalar field override semantics](#scalar-field-override-semantics) · [`Meta.choice_enum_names`](#metachoice_enum_names).
- **Optimizer:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [`OptimizerHint`](#optimizerhint) · [`Meta.optimizer_hints`](#metaoptimizer_hints) · [Plan cache](#plan-cache) · [FK-id elision](#fk-id-elision) · [`only()` projection](#only-projection) · [Queryset diffing](#queryset-diffing) · [Strictness mode](#strictness-mode) · [Schema audit](#schema-audit) · [Multi-database cooperation](#multi-database-cooperation) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning).
- **Filtering:** [`FilterSet`](#filterset) · [`RelatedFilter`](#relatedfilter) · [`Meta.filterset_class`](#metafilterset_class).
- **Ordering:** [`OrderSet`](#orderset) · [`RelatedOrder`](#relatedorder) · [`Meta.orderset_class`](#metaorderset_class).
- **Aggregation:** [`AggregateSet`](#aggregateset) · [`RelatedAggregate`](#relatedaggregate) · [`Meta.aggregate_class`](#metaaggregate_class) · [`get_child_queryset`](#get_child_queryset).
- **Field selection:** [`FieldSet`](#fieldset) · [`Meta.fields_class`](#metafields_class).
- **Search:** [`Meta.search_fields`](#metasearch_fields).
- **Permissions:** [`get_queryset` visibility hook](#get_queryset-visibility-hook) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [Per-field permission hooks](#per-field-permission-hooks).
- **Relay:** [Relay Node integration](#relay-node-integration) · [`DjangoNodeField`](#djangonodefield) · [`DjangoConnectionField`](#djangoconnectionfield) · [`DjangoConnection`](#djangoconnection) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning).
- **List fields:** [`DjangoListField`](#djangolistfield) · [Relation handling](#relation-handling).
- **Mutations:** [`DjangoMutation`](#djangomutation) · [`DjangoFormMutation`](#djangoformmutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`SerializerMutation`](#serializermutation) · [Input type generation](#input-type-generation) · [`FieldError` envelope](#fielderror-envelope) · [Auth mutations](#auth-mutations).
- **File / image uploads:** [`Upload` scalar](#upload-scalar) · [`DjangoFileType`](#djangofiletype) · [`DjangoImageType`](#djangoimagetype).
- **Integration / tooling:** [Django `AppConfig`](#django-appconfig) · [Schema export management command](#schema-export-management-command) · [`DjangoGraphQLProtocolRouter`](#djangographqlprotocolrouter) · [Debug-toolbar middleware](#debug-toolbar-middleware) · [Response-extensions debug middleware](#response-extensions-debug-middleware).
- **Testing:** [`safe_wrap_connection_method`](#safe_wrap_connection_method) · [Django Trac #37064 hardening](#django-trac-37064-hardening) · [`TestClient`](#testclient) · [`GraphQLTestCase`](#graphqltestcase).

---

## `AggregateSet`

**Status:** planned for `0.1.3`.

Declarative aggregate class with `Sum` / `Count` / `Avg` / `Min` / `Max` / `Mode` / `Uniques` / `GroupBy`, [`RelatedAggregate`](#relatedaggregate) traversal, custom `compute_*_*` stats declared via `Meta.custom_stats`, sync and async paths via `compute` / `acompute`. Computation is selection-set-aware — only requested stats are computed. The [`get_child_queryset`](#get_child_queryset) cascade hook excludes private rows when traversing into children. Declared per-type via [`Meta.aggregate_class`](#metaaggregate_class).

**See also:** [`Meta.aggregate_class`](#metaaggregate_class) · [`RelatedAggregate`](#relatedaggregate) · [`get_child_queryset`](#get_child_queryset).

## `apply_cascade_permissions`

**Status:** planned for `0.0.10`.

Cascades each `DjangoType`'s [`get_queryset`](#get_queryset-visibility-hook) filter to its related types when reaching through FK / M2M. Used inside a type's `get_queryset` override:

```python
@classmethod
def get_queryset(cls, queryset, info):
    return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

Composes with filter / order / aggregate permission gates and with the post-write return value of mutations.

**See also:** [`get_queryset` visibility hook](#get_queryset-visibility-hook) · [Per-field permission hooks](#per-field-permission-hooks).

## Auth mutations

**Status:** planned for `0.0.11`.

`login` / `logout` / `register` mutations plus a `current_user` query helper. Opt-in via explicit import; not bundled into the default schema. Composes with [`DjangoMutation`](#djangomutation) and `django.contrib.auth`.

**See also:** [`DjangoMutation`](#djangomutation).

## `BigInt` scalar

**Status:** shipped (`0.0.6`).

JSON-safe scalar typically used to map Django's 64-bit integer fields `BigIntegerField` and `PositiveBigIntegerField` (not `BigAutoField`). Technically arbitrary-precision: serialized via Python `str(int_value)`, which handles any `int`. Wire format is a decimal string to survive GraphQL's signed 32-bit `Int` boundary (executing a query returning an `int`-annotated value past `2**31 - 1` raises a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`). Strict parser accepts Python `int` (excluding `bool`) and strings matching `^(0|-?[1-9][0-9]*)$` — plain ASCII decimal, optional leading minus for non-zero, no leading zeroes (except `"0"` itself), no underscores, no plus sign, no Unicode digits. Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`. Part of [Specialized scalar conversions](#specialized-scalar-conversions).

Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol. The migration applies to any schema that resolves to `BigInt` — including [`DjangoType`](#djangotype) schemas whose fields are backed by `BigIntegerField` or `PositiveBigIntegerField` (resolved to `BigInt` by the [`Specialized scalar conversions`](#specialized-scalar-conversions) converter table) even when the consumer never imports or annotates `BigInt` directly.

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

**Status:** planned for `0.0.9`.

The optimizer learns to recognize `edges { node { ... } }` selections and plan `Prefetch` chains correctly across connection-paginated relations. Without this, nested connections fall back to per-row queries.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [Plan cache](#plan-cache) · [`DjangoOptimizerExtension`](#djangooptimizerextension).

## Debug-toolbar middleware

**Status:** planned for `0.0.12`.

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

**Status:** planned for `0.0.9`.

Generic return-type alias `DjangoConnection[T]` for fields that produce Relay connections. Used as the return annotation for [`DjangoConnectionField`](#djangoconnectionfield) declarations.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [Relay Node integration](#relay-node-integration).

## `DjangoConnectionField`

**Status:** planned for `0.0.9`.

Relay-style connection field with `edges` / `node` / `pageInfo` / `totalCount`, cursor-based pagination, and `filter` / `orderBy` / `search` arguments that flow into the connection's `DjangoType`'s [`filterset_class`](#metafilterset_class) / [`orderset_class`](#metaorderset_class) / [`search_fields`](#metasearch_fields). Composes with the optimizer for nested-selection planning. Works at root fields and at nested relation fields.

**See also:** [`DjangoConnection`](#djangoconnection) · [`DjangoNodeField`](#djangonodefield) · [Relay Node integration](#relay-node-integration) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning).

## `DjangoFileType`

**Status:** planned for `0.0.11`.

Output type for `FileField` carrying `name` / `path` / `size` / `url`. Paired with the [`Upload` scalar](#upload-scalar) on the input side.

**See also:** [`Upload` scalar](#upload-scalar) · [`DjangoImageType`](#djangoimagetype).

## `DjangoFormMutation`

**Status:** planned for `0.0.11`.

`DjangoMutation` subclass that consumes a Django `Form`. Declared via `Meta.form_class`; validation errors surface through the shared [`FieldError` envelope](#fielderror-envelope) (populated from `form.errors`); the post-save object is the mutation return value.

**See also:** [`DjangoMutation`](#djangomutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`FieldError` envelope](#fielderror-envelope).

## `DjangoGraphQLProtocolRouter`

**Status:** planned for `0.0.12`.

A Channels `ProtocolTypeRouter`-wrapping helper for consumers using Channels. Soft dependency on `channels`; symbol name is intentionally distinct from `strawberry-django`'s `AuthGraphQLProtocolTypeRouter` to avoid migration ambiguity.

## `DjangoImageType`

**Status:** planned for `0.0.11`.

Output type for `ImageField` carrying `name` / `path` / `size` / `url` plus image dimensions where Pillow is available.

**See also:** [`Upload` scalar](#upload-scalar) · [`DjangoFileType`](#djangofiletype).

## `DjangoListField`

**Status:** shipped (`0.0.7`).

Non-Relay `list[T]` **root Query field**. The smallest entry point for migrants coming from `graphene-django`'s `DjangoListField` and for use cases that do not need pagination, edges, or page-info. Implemented as a **factory function** (not a class): consumer usage is `all_branches: list[BranchType] = DjangoListField(BranchType)`, and Strawberry's `@strawberry.type` class-body walk picks up the factory's return value the same way it picks up `strawberry.field(...)`. Outer-list nullability is driven by the consumer's class-attribute annotation — `list[T]` renders as `[T!]!` and `list[T] | None` renders as `[T!]`. The default resolver pulls `target_type.__django_strawberry_definition__.model._default_manager.all()` and applies the type-level [`get_queryset`](#get_queryset-visibility-hook) in both sync and async contexts (the sync path rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults). A consumer-supplied `resolver=` overrides the default body; when its return value is a Django `Manager` or `QuerySet`, the wrapper coerces the `Manager` to a `QuerySet` and applies `target_type.get_queryset(qs, info)` (graphene-django parity), so a custom resolver still honors the visibility hook. Async consumer resolvers are detected at construction time via `inspect.iscoroutinefunction` and routed through an `async def` wrapper that awaits the coroutine before applying the isinstance check. Python `list` returns from sync or async resolvers pass through unchanged. Optimizer cooperation rides the existing root-gated [`DjangoOptimizerExtension`](#djangooptimizerextension) hook (`info.path.prev is None`), so root-position `DjangoListField` selections receive `select_related` / `prefetch_related` / `only` planning automatically; nested non-root usage is functional but not root-optimized in `0.0.7`. Standard field-level metadata pass-through (`description`, `deprecation_reason`, `directives`) is forwarded into the inner `strawberry.field(...)` call.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) (the Relay-shaped equivalent).

## `DjangoModelFormMutation`

**Status:** planned for `0.0.11`.

`DjangoMutation` subclass that consumes a Django `ModelForm` declared via `Meta.form_class`. Errors and return-shape contracts match [`DjangoFormMutation`](#djangoformmutation).

**See also:** [`DjangoFormMutation`](#djangoformmutation) · [`DjangoMutation`](#djangomutation).

## `DjangoMutation`

**Status:** planned for `0.0.11`.

Base class for mutations with `Meta`-driven configuration; auto-generates [`Input` / `PartialInput`](#input-type-generation) types from Django models that preserve the relation-override contract; shared [`FieldError` envelope](#fielderror-envelope) reused across every mutation flavor; sync and async resolver paths; composition with the optimizer for the post-write return value (re-fetching the mutated row with the right `select_related` / `prefetch_related` for the response selection).

**See also:** [`DjangoFormMutation`](#djangoformmutation) · [`DjangoModelFormMutation`](#djangomodelformmutation) · [`SerializerMutation`](#serializermutation) · [Input type generation](#input-type-generation) · [`FieldError` envelope](#fielderror-envelope).

## `DjangoNodeField`

**Status:** planned for `0.0.9`.

Root-level single-node lookup field — the `category: GalaxyNode = DjangoNodeField(GalaxyNode)` shape in [`../GOAL.md`'s astronomy showcase](../GOAL.md#what-success-looks-like-in-your-code). Resolves a single `DjangoType` instance by Relay `GlobalID`, running the target type's [`get_queryset`](#get_queryset-visibility-hook) hook.

**See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [Relay Node integration](#relay-node-integration).

## `DjangoOptimizerExtension`

**Status:** shipped (`0.0.2`).

Strawberry schema extension that translates selected GraphQL fields into Django ORM optimization calls. Opt-in at Strawberry schema construction time:

```python
schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
```

Shipped behavior:

- root-gated optimization for root resolvers returning Django `QuerySet`s
- passthrough for non-root resolvers and non-`QuerySet` results
- `select_related` for safe single-valued relation chains
- `prefetch_related` for many-side relations
- generated `Prefetch` objects for child querysets
- nested prefetch chains for nested GraphQL selections
- [`only`](#only-projection) projection for selected scalar columns
- connector-column inclusion so Django can attach joined and prefetched rows without lazy loads
- custom [`get_queryset`](#get_queryset-visibility-hook) downgrade from join to `Prefetch`
- async resolver support

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

**See also:** all [`Meta.*`](#index) keys · [`finalize_django_types`](#finalize_django_types) · [Definition-order independence](#definition-order-independence) · [Relay Node integration](#relay-node-integration).

## `FieldError` envelope

**Status:** planned for `0.0.11`.

Shared `errors: list[FieldError]` envelope returned by every mutation flavor — [`DjangoMutation`](#djangomutation), [`DjangoFormMutation`](#djangoformmutation), [`DjangoModelFormMutation`](#djangomodelformmutation), [`SerializerMutation`](#serializermutation). Each `FieldError` carries a `field` path and a `messages: list[str]`. Populated automatically from `form.errors` / `serializer.errors` / `ValidationError` raised inside `DjangoMutation.perform_mutation`.

**See also:** [`DjangoMutation`](#djangomutation) · [`DjangoFormMutation`](#djangoformmutation) · [`SerializerMutation`](#serializermutation).

## `FieldSet`

**Status:** planned for `0.1.1`.

Declarative field-selection class for the [`Meta.fields_class`](#metafields_class) surface. Carries field-level permission checks ([`check_*_permission`](#per-field-permission-hooks) denial gates), custom field resolvers (`resolve_*` overrides), computed fields (class-level annotations), and redaction / deny-value behavior. Integrates with generated model fields; declared per-type via `Meta.fields_class = MyTypeFieldSet`.

**See also:** [`Meta.fields_class`](#metafields_class) · [Per-field permission hooks](#per-field-permission-hooks).

## `FilterSet`

**Status:** planned for `0.0.8`.

Declarative filter classes with `Meta.model`, `Meta.fields` (dict form `{"name": ["exact", "icontains"]}` or `"__all__"` shorthand), [`RelatedFilter`](#relatedfilter) for cross-relation traversal (accepts class, absolute import path, or unqualified name for circular cases), `check_*_permission` denial gates, and explicit-queryset scope boundaries that nested filters cannot bypass. Logical `and` / `or` / `not` operators on the input shape. Generated input types use stable class-derived names so two connection fields on the same model resolve to the same `FilterInputType` (Apollo cache friendly).

The lazy-resolution architecture is borrowed verbatim from `django-graphene-filters` — a six-layer pipeline; five layers are library-agnostic and port directly; only the cycle-safe forward reference (Graphene's `lambda:` → Strawberry's `strawberry.lazy()`) is engine-adapted.

**See also:** [`Meta.filterset_class`](#metafilterset_class) · [`RelatedFilter`](#relatedfilter) · [`OrderSet`](#orderset).

## `finalize_django_types`

**Status:** shipped (`0.0.4`).

Synchronization point that resolves pending relation annotations and applies `strawberry.type(cls, ...)` decoration to every collected `DjangoType`. Required because Strawberry resolves field annotations eagerly at decoration time, while Django relations may target a `DjangoType` whose module hasn't been imported yet.

Call it once during single-threaded schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed:

```python
from django_strawberry_framework import finalize_django_types
import apps.products.schema  # registers DjangoType subclasses
import apps.library.schema

finalize_django_types()

schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
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

The load-bearing behavior is optimizer cooperation: `has_custom_get_queryset()` reports whether a type or inherited intermediate base overrides the hook, and the optimizer downgrades a JOIN to a `Prefetch` when a target type defines one. Your visibility filter survives relation traversal instead of being bypassed by a raw `select_related` join.

**See also:** [`apply_cascade_permissions`](#apply_cascade_permissions) · [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Per-field permission hooks](#per-field-permission-hooks).

## `GraphQLTestCase`

**Status:** planned for `0.0.12`.

`unittest.TestCase` subclass for live HTTP-level testing patterns. Mirrors `strawberry-django`'s `test/client.py`. Provides `query()` / `mutate()` helpers and assertion shortcuts.

**See also:** [`TestClient`](#testclient).

## Input type generation

**Status:** planned for `0.0.11`.

[`DjangoMutation`](#djangomutation) auto-generates two input types from a Django model declared in `Meta.model`:

- **`Input`** — every field required (matches `Model.objects.create(...)` semantics).
- **`PartialInput`** — every field optional (matches `Model.objects.update(...)` semantics).

Both preserve the relation-override contract from the foundation slice: consumer-authored input fields are honored rather than clobbered by generated ones.

**See also:** [`DjangoMutation`](#djangomutation) · [`Upload` scalar](#upload-scalar).

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

**Status:** planned for `0.0.8`.

References a [`FilterSet`](#filterset) subclass that defines the filter input for this `DjangoType`. Surfaces as the `filter:` argument on [`DjangoConnectionField`](#djangoconnectionfield).

```python
class GalaxyType(DjangoType):
    class Meta:
        model = Galaxy
        filterset_class = filters.GalaxyFilter
```

**See also:** [`FilterSet`](#filterset).

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

**Status:** planned for `0.0.8`.

References an [`OrderSet`](#orderset) subclass that defines ordering input for this `DjangoType`. Surfaces as the `orderBy:` argument on [`DjangoConnectionField`](#djangoconnectionfield).

**See also:** [`OrderSet`](#orderset).

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

**See also:** [FK-id elision](#fk-id-elision) · [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Plan cache](#plan-cache).

## `OptimizerHint`

**Status:** shipped (`0.0.3`).

Typed wrapper for per-relation optimizer overrides. Pass instances through [`Meta.optimizer_hints`](#metaoptimizer_hints).

Supported modes:

- `OptimizerHint.SKIP` — exclude a relation from automatic planning (the optimizer leaves it alone).
- `OptimizerHint.select_related()` — force `select_related`.
- `OptimizerHint.prefetch_related()` — force `prefetch_related`.
- `OptimizerHint.prefetch(Prefetch(...))` — use a consumer-provided `Prefetch` object and stop walking below that relation.

**See also:** [`Meta.optimizer_hints`](#metaoptimizer_hints) · [`DjangoOptimizerExtension`](#djangooptimizerextension).

## `OrderSet`

**Status:** planned for `0.0.8`.

Declarative ordering with `Meta.fields` (list form `["name", "created_date"]` or `"__all__"` shorthand), [`RelatedOrder`](#relatedorder) for cross-relation traversal, `check_*_permission` gates. Reuses the filtering subsystem's lazy-resolution architecture verbatim with `OrderSet` substituted for `FilterSet`.

**See also:** [`Meta.orderset_class`](#metaorderset_class) · [`RelatedOrder`](#relatedorder) · [`FilterSet`](#filterset).

## Per-field permission hooks

**Status:** planned for `0.0.10`.

Methods named `check_<field>_permission` on the type's [`FieldSet`](#fieldset) gate access to that field. Two failure modes:

- **Redaction** — silent safe-value fallback (`None`, empty string, sentinel) so the response shape stays stable.
- **Denial** — raise `GraphQLError` so the response carries an `errors` entry for that path.

Composes with filter / order / aggregate permission gates and with the post-write return value of mutations.

**See also:** [`FieldSet`](#fieldset) · [`apply_cascade_permissions`](#apply_cascade_permissions) · [`get_queryset` visibility hook](#get_queryset-visibility-hook).

## Plan cache

**Status:** shipped (`0.0.3`).

Caches optimizer plans across requests. The same query 10,000×/sec walks the selection tree once, not 10,000 times.

Properties:

- **Selection-shape keys.** Cache keys include the selected operation AST, relevant `@skip` / `@include` variables, target model, and root runtime path.
- **Variable filtering.** Filter-variable values that do not affect selection shape are excluded from the key, so a query with many filter combinations reuses one cached plan.
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

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Plan cache](#plan-cache) · [`OptimizerHint`](#optimizerhint).

## `RelatedAggregate`

**Status:** planned for `0.1.3`.

Field declaration on an [`AggregateSet`](#aggregateset) for cross-relation aggregate traversal. Accepts a target `AggregateSet` class (or its import path for circular cases), parallel to [`RelatedFilter`](#relatedfilter) / [`RelatedOrder`](#relatedorder) in the filter / order subsystems.

**See also:** [`AggregateSet`](#aggregateset) · [`get_child_queryset`](#get_child_queryset).

## `RelatedFilter`

**Status:** planned for `0.0.8`.

Field declaration on a [`FilterSet`](#filterset) for cross-relation filter traversal. Accepts a target `FilterSet` class, an absolute import path, or an unqualified name for circular references. The unqualified-name form is resolved lazily, matching `django-graphene-filters`'s six-layer pipeline.

**See also:** [`FilterSet`](#filterset) · [`RelatedOrder`](#relatedorder).

## `RelatedOrder`

**Status:** planned for `0.0.8`.

Field declaration on an [`OrderSet`](#orderset) for cross-relation ordering traversal. Same lazy-resolution semantics as [`RelatedFilter`](#relatedfilter).

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
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise [`ConfigurationError`](#configurationerror) at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Non-Relay Strawberry interfaces (`@strawberry.interface`-decorated classes) are accepted without Relay-specific wiring.

Optimizer-extension cooperation on the per-node `resolve_node` resolver is deferred to a follow-up slice; root-level list resolvers continue to receive full [`DjangoOptimizerExtension`](#djangooptimizerextension) treatment today.

**See also:** [`Meta.interfaces`](#metainterfaces) · [`DjangoNodeField`](#djangonodefield) · [`DjangoConnectionField`](#djangoconnectionfield) · [Connection-aware optimizer planning](#connection-aware-optimizer-planning).

## Response-extensions debug middleware

**Status:** planned for `0.0.12`.

Surfaces executed SQL queries and raised exceptions through the GraphQL response's `extensions` envelope so frontend clients can read them without the toolbar. Distinct from [Debug-toolbar middleware](#debug-toolbar-middleware): this is in-response surfacing, that is server-side panel.

**See also:** [Debug-toolbar middleware](#debug-toolbar-middleware).

## `safe_wrap_connection_method`

**Status:** shipped (`0.0.7`).

Cooperative wrap helper for consumers (or third-party libraries) who need to replace a method on a Django `connections[alias]` between `setUpClass` and `tearDownClass`. Mirrors `django-debug-toolbar`'s wrap-time isinstance check at `debug_toolbar.panels.sql.tracking.wrap_cursor`: refuses to clobber Django's `_DatabaseFailure` wrapper when it's already in place, returning `False` instead. Returns `True` and installs the consumer-provided wrapper otherwise.

```python
from django.db import connections
from django_strawberry_framework.test import safe_wrap_connection_method

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
- file and image fields → string path / URL values
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

`DjangoOptimizerExtension.check_schema(schema)` walks every schema-reachable `DjangoType` and reports relation targets without registered `DjangoType`s as warnings. Hidden fields and [`OptimizerHint.SKIP`](#optimizerhint) fields are ignored. Intended for use as a unit-test assertion or a CI gate.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Strictness mode](#strictness-mode).

## Schema export management command

**Status:** shipped (`0.0.7`).

`django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`; `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, and missing positional argument; no `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7`.

**See also:** [Django `AppConfig`](#django-appconfig).

## `SerializerMutation`

**Status:** planned for `0.0.11`.

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

**See also:** [Scalar field conversion](#scalar-field-conversion) · [`BigInt` scalar](#bigint-scalar).

## strawberry_config

**Status:** shipped ([Unreleased]).

Factory returning a [`StrawberryConfig`](https://strawberry.rocks) pre-populated with the package's `scalar_map` — the registration path consumers use to bind package-defined scalars (today: [`BigInt`](#bigint-scalar); next: [`Upload`](#upload-scalar) in `0.0.11`) into their `strawberry.Schema(...)` call.

```python
from django_strawberry_framework import strawberry_config

schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[DjangoOptimizerExtension()],
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
- `"raise"` — fail-fast `RuntimeError` for tests / dev checks.

Warnings and errors fire only when the relation access actually causes a lazy load — false positives from unhit prefetches do not trigger.

Planned resolver keys and lookup paths are stashed on `info.context` for introspection during strictness incidents.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [Schema audit](#schema-audit).

## `TestClient`

**Status:** planned for `0.0.12`.

`TestClient` and `AsyncTestClient` helpers for live HTTP-level testing patterns. Mirrors `strawberry-django`'s `test/client.py` shape. Companion: [`GraphQLTestCase`](#graphqltestcase).

**See also:** [`GraphQLTestCase`](#graphqltestcase).

## Django Trac #37064 hardening

**Status:** shipped (`0.0.7`).

Defensive patch for [Django Trac #37064](https://code.djangoproject.com/ticket/37064) (closed upstream as `wontfix`). The package applies the patch automatically at `DjangoStrawberryFrameworkConfig.ready` time, replacing `django.test.testcases.SimpleTestCase._remove_databases_failures` (the class where Django defines the method; `TransactionTestCase` and `TestCase` inherit it) with a variant that adds an `isinstance(method, _DatabaseFailure)` guard before the `setattr(..., method.wrapped)` step. Prevents the unrecoverable `AttributeError: 'function' object has no attribute 'wrapped'` at `tearDownClass` that the ticket documents.

Consumers get the hardening for free by having `"django_strawberry_framework"` in `INSTALLED_APPS` — no `conftest.py` workaround, no base test class to inherit, no settings key required.

Pairs with [`safe_wrap_connection_method`](#safe_wrap_connection_method) (the wrap-time half of the same defense-in-depth pattern).

**See also:** [`safe_wrap_connection_method`](#safe_wrap_connection_method) · [Multi-database cooperation](#multi-database-cooperation) · [Django `AppConfig`](#django-appconfig).

## `Upload` scalar

**Status:** planned for `0.0.11`.

Strawberry `Upload` scalar mapping for `FileField` / `ImageField` on mutation inputs. Paired with [`DjangoFileType`](#djangofiletype) / [`DjangoImageType`](#djangoimagetype) on the output side.

**See also:** [`DjangoFileType`](#djangofiletype) · [`DjangoImageType`](#djangoimagetype) · [`DjangoMutation`](#djangomutation).

---

## Cross-subsystem invariants

Goals that the Layer-3 cards collectively satisfy by `1.0.0`:

- Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end. This rule resolves entirely at `1.0.0`.
- Filters, orders, aggregates, mutations, permissions, and connection fields all compose with [`DjangoOptimizerExtension`](#djangooptimizerextension).
- The [`FieldError` envelope](#fielderror-envelope) is shared across every mutation flavor for a consistent client contract.
- Example-project schemas reference only shipped features — never unshipped ones.

## Beyond `1.0.0`

Strategic differentiators that go past `1.0.0` parity live in [`../BACKLOG.md`](../BACKLOG.md). Roadmap-adjacent items already tracked there:

- Apollo Federation support — `BETTER` item 34
- Model-property / cached-property optimizer hints — folded into `BETTER` item 14 (`Meta.computed_fields`)
- Shared queryset introspection helpers (`utils/queryset.py`) — `BETTER` item 36
- Public-surface promotion discipline — `BETTER` item 37
- Layered manual relation-override test policy — `BETTER` item 38
- First-class multi-db / sharding-aware optimizer — `BETTER` item 41

Dedicated migration guides (graphene-django, strawberry-graphql-django, DRF / django-filter) are tracked in [`../KANBAN.md`](../KANBAN.md) so this file can stay focused on capability lookup. For the migration code diffs, see [`../GOAL.md`'s Migration shape section](../GOAL.md#migration-shape).
