# Features

This file is the **per-feature capability catalog** for `django-strawberry-framework`. Think of it as the glossary: every public symbol (`DjangoType`, `FilterSet`, `apply_cascade_permissions`, …), every `Meta` key, and every behavior contract has an entry below.

Most readers come here with one of two questions:

- **"Is X shipped today?"** → use the [Capabilities at a glance](#capabilities-at-a-glance) matrix. Click a row to jump to the section that defines it.
- **"What exactly does X do?"** → use the per-subsystem section that owns X.

What this file is **not**:

- **The pitch / vision.** That's [`../GOAL.md`](../GOAL.md), which shows a complete `1.0.0` Django app (the astronomy showcase) demonstrating every capability in real code.
- **The per-card ship sequencing.** That's [`../KANBAN.md`](../KANBAN.md), which tracks each planned capability against a target patch version.
- **The strategic post-`1.0.0` roadmap.** That's [`../BETTER.md`](../BETTER.md), which holds differentiation items beyond parity.

For the example-project current usage snapshot, see [`../TODAY.md`](../TODAY.md).

## Feature status

Status labels used throughout this file:

- `shipped` — implemented, tested, available in the current package surface.
- `planned for X.Y.Z` — committed package direction, not implemented yet; tracked in [`../KANBAN.md`](../KANBAN.md) against a target patch version.
- `deferred` — reserved for later design or blocked on another feature.
- `alpha constraint` — current behavior that works but is intentionally narrower than the eventual API.
- `post-1.0.0` — strategic differentiation tracked in [`../BETTER.md`](../BETTER.md), not on the roadmap to `1.0.0`.

## Current package surface

Current package version: `0.0.5`. Alpha-quality — suitable for internal tools and prototypes, not production.

Public exports from `django_strawberry_framework`:

- [`DjangoType`](#django-model-to-strawberry-type-generation) — model-backed Strawberry type base class.
- [`DjangoOptimizerExtension`](#automatic-orm-optimization) — Strawberry schema extension that does ORM optimization.
- [`OptimizerHint`](#optimizer-hints) — typed wrapper for per-relation optimizer overrides.
- [`finalize_django_types`](#definition-order-independence) — synchronization point that resolves pending relations and applies `strawberry.type(cls, ...)` decoration.
- `auto` — re-export from Strawberry for `auto`-typed field annotations inside this package's import surface.
- `__version__` — package version string.

## Capabilities at a glance

Status-by-capability index. Click a row to jump to the section that defines it.

| Capability | Status |
|---|---|
| [`DjangoType` — model-backed Strawberry types](#django-model-to-strawberry-type-generation) | shipped (`0.0.5`) |
| [Definition-order-independent finalization](#definition-order-independence) | shipped (`0.0.4`) |
| [`Meta.interfaces = (relay.Node,)` — Relay Node integration](#relay-node-integration) | shipped (`0.0.5`) |
| [Scalar field conversion (text / int / bool / decimal / date-time / UUID / binary / file / null)](#django-field-conversion) | shipped (`0.0.1`+) |
| [Choice enum generation](#django-field-conversion) | shipped (`0.0.1`) |
| [Relation handling (forward / reverse FK / OneToOne / M2M)](#relation-handling) | shipped (`0.0.1`+) |
| [`get_queryset` visibility hook](#queryset-visibility-hook) | shipped (`0.0.1`) |
| [Optimizer (`select_related` / `prefetch_related` / `only`)](#automatic-orm-optimization) | shipped (`0.0.2`) |
| [Optimizer plan caching](#optimizer-cache-and-planning-features) | shipped (`0.0.3`) |
| [FK-id elision for `{ relation { id } }`](#join-avoidance-and-projection) | shipped (`0.0.3`) |
| [`OptimizerHint` + `Meta.optimizer_hints`](#optimizer-hints) | shipped (`0.0.3`) |
| [Strictness mode (`off` / `warn` / `raise`)](#optimizer-observability-and-safety) | shipped (`0.0.3`) |
| [Schema audit (`DjangoOptimizerExtension.check_schema`)](#optimizer-observability-and-safety) | shipped (`0.0.3`) |
| [Queryset diffing / consumer-shaped queryset cooperation](#queryset-diffing-and-consumer-cooperation) | shipped (`0.0.3`) |
| [Specialized scalars (`BigIntegerField` / `JSONField` / `ArrayField` / `HStoreField`)](#specialized-scalar-conversions) | planned for `0.0.6` |
| [`Meta.primary` — multiple `DjangoType`s per model](#metaprimary) | planned for `0.0.6` |
| [Scalar field override semantics](#scalar-field-override-semantics) | planned for `0.0.6` |
| [`DjangoListField` (non-Relay list)](#djangolistfield) | planned for `0.0.7` |
| [Django `AppConfig`](#django-appconfig) | planned for `0.0.7` |
| [Schema export management command](#schema-export-management-command) | planned for `0.0.7` |
| [Multi-database cooperation contract](#multi-database-cooperation) | planned for `0.0.7` |
| [`FilterSet` + `Meta.filterset_class`](#filterset) | planned for `0.0.8` |
| [`OrderSet` + `Meta.orderset_class`](#orderset) | planned for `0.0.8` |
| [`DjangoConnectionField` + `DjangoConnection[T]` return type](#djangoconnectionfield) | planned for `0.0.9` |
| [`DjangoNodeField` (single-node lookup)](#full-relay-story) | planned for `0.0.9` |
| [Full Relay story (root `node()` / connection / validation)](#full-relay-story) | planned for `0.0.9` |
| [Connection-aware optimizer planning](#connection-aware-optimizer-planning) | planned for `0.0.9` |
| [`apply_cascade_permissions` + per-field permissions](#permissions-subsystem) | planned for `0.0.10` |
| [Mutations + auto-generated `Input` / `PartialInput` types](#mutations-subsystem) | planned for `0.0.11` |
| [`Upload` scalar + `DjangoFileType` / `DjangoImageType`](#upload-scalar) | planned for `0.0.11` |
| [Form-based mutations (`DjangoFormMutation` / `DjangoModelFormMutation`)](#form-based-mutations) | planned for `0.0.11` |
| [DRF serializer mutations (`SerializerMutation`)](#drf-serializer-mutations) | planned for `0.0.11` |
| [Auth mutations (`login` / `logout` / `register`) + `current_user`](#auth-mutations) | planned for `0.0.11` |
| [Channels ASGI router (`DjangoGraphQLProtocolRouter`)](#channels-asgi-router) | planned for `0.0.12` |
| [Debug-toolbar middleware](#debug-toolbar-middleware) | planned for `0.0.12` |
| [Test client helper (`TestClient` / `AsyncTestClient` / `GraphQLTestCase`)](#test-client-helper) | planned for `0.0.12` |
| [Response-extensions debug middleware](#response-extensions-debug-middleware) | planned for `0.0.12` |
| [`FieldSet` + `Meta.fields_class`](#fieldset) | planned for `0.1.1` |
| [`Meta.search_fields`](#metasearch_fields) | planned for `0.1.2` |
| [`AggregateSet` + `Meta.aggregate_class`](#aggregateset) | planned for `0.1.3` |
| [Stable choice-enum naming overrides (`Meta.choice_enum_names`)](#stable-choice-enum-naming-overrides) | planned for `0.1.4` |
| Apollo Federation | post-`1.0.0` (BETTER item 34) |
| First-class multi-db / sharding-aware optimizer | post-`1.0.0` (BETTER item 41) |

## Quick comparison

| Concern | graphene-django | strawberry-graphql-django | this package |
| --- | --- | --- | --- |
| Configuration shape | `class Meta` | decorators | `class Meta` |
| Async resolvers | retrofitted | native | native |
| Modern typing | `graphene.String()` style declarations | type hints | type hints |
| Built-in N+1 optimizer | external patterns | shipped | shipped + plan cache + FK-id elision + queryset diffing + strictness |
| Filter / order / aggregate | shipped | shipped | planned for `0.0.8` / `0.0.8` / `0.1.3` |
| Stable today | yes | yes | alpha |

For the migration code diffs from each upstream stack, see [`../GOAL.md`'s Migration shape section](../GOAL.md#migration-shape).

## DRF-shaped GraphQL API

Status: shipped foundation, planned query features.

The package uses nested `Meta` classes as the consumer-facing configuration surface. The goal is a GraphQL API style that feels like DRF, django-filter, and Django model declarations instead of a stack of Strawberry decorators.

Shipped `Meta` keys:

- `Meta.model` — required for every concrete `DjangoType`.
- `Meta.fields` — tuple/list of field names, or `"__all__"`, or omitted (defaults to `"__all__"`).
- `Meta.exclude` — tuple/list of field names to exclude.
- `Meta.name` — override the GraphQL type name (defaults to the Python class name).
- `Meta.description` — override the GraphQL type description.
- `Meta.optimizer_hints` — per-relation optimizer overrides; see [Optimizer hints](#optimizer-hints).
- `Meta.interfaces` — tuple of Strawberry interface classes; see [Relay Node integration](#relay-node-integration).

Validation:

- Unknown `Meta` keys raise `ConfigurationError` so typos do not silently alter the schema.
- Deferred `Meta` keys (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`) are rejected until the feature that owns them ships.

### Relay Node integration

Status: shipped.

`Meta.interfaces` accepts a tuple of Strawberry interface classes; when `relay.Node` is among them, the `DjangoType` becomes a Relay-node-shaped GraphQL type with `id: GlobalID!` and the four `resolve_*` defaults wired through `cls.get_queryset` (the model's default manager plus the type's visibility hook).

```python
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType
from myapp.models import Category


class CategoryNode(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        interfaces = (relay.Node,)
```

Shipped behavior:

- Default `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` classmethods are injected when `relay.Node` is declared; consumer-declared overrides are preserved via Strawberry's `__func__` identity test (matches `strawberry-django`).
- When `relay.Node` is in `Meta.interfaces`, the synthesized Django `id: int!` annotation is suppressed and the Relay-supplied `id: GlobalID!` from the interface is used instead. The Django primary key remains selected as a connector column for the optimizer.
- Both sync and async paths for `resolve_node` and `resolve_nodes`; `resolve_id_attr` and `resolve_id` are sync.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Non-Relay Strawberry interfaces (`@strawberry.interface`-decorated classes) are accepted without Relay-specific wiring.

The optimizer node-lookup path: optimizer-extension cooperation on the per-node `resolve_node` resolver is deferred to a follow-up slice; root-level list resolvers continue to receive full `DjangoOptimizerExtension` treatment today.

## Django model to Strawberry type generation

Status: shipped with alpha constraints.

`DjangoType` reads Django model metadata and builds a Strawberry type. It preserves Django concepts rather than replacing them with a custom data layer.

Shipped:

- model field selection with `fields` and `exclude`
- default `fields = "__all__"` behavior when neither selector is supplied
- GraphQL type-name and description overrides
- scalar annotation generation (see [Django field conversion](#django-field-conversion))
- relation annotation generation (see [Relation handling](#relation-handling))
- choice enum generation (see [Django field conversion](#django-field-conversion))
- relation resolver generation
- type registry registration
- definition-order-independent relation finalization (see [Definition-order independence](#definition-order-independence))
- abstract / intermediate base support when a subclass has no `Meta`

Current alpha constraints:

- one `DjangoType` per Django model (the [`Meta.primary`](#metaprimary) card promotes this to a primary-declaration contract)
- manual override validation for relation cardinality is deferred; the package trusts relation-field annotations supplied by the consumer

### Definition-order independence

Status: shipped.

`DjangoType` collection is split from Strawberry finalization. Class creation records Django metadata and pending relation targets, while `finalize_django_types()` resolves those pending relations, attaches generated relation resolvers, and decorates each collected type with `strawberry.type`.

Call `finalize_django_types()` once during single-threaded schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed. Calling it a second time is a no-op. Declaring a new concrete `DjangoType` after finalization raises `ConfigurationError`; tests should use `registry.clear()` and fresh type classes when they need a new registry lifecycle.

Supported relation cycles:

- forward FK and reverse FK
- forward OneToOne and reverse OneToOne
- forward and reverse M2M
- multi-cycle graphs that combine those relation shapes

Unresolved relation targets fail during finalization with an error that names the source model, source field, and target model. The most common cause is that a Python module containing the target `DjangoType` was never imported before finalization.

Supported forward-reference / manual relation shapes:

- generated relation annotations for target types declared before or after the source type
- same-module string annotations such as `items: list["ItemType"]`
- stringified annotations from `from __future__ import annotations`
- cross-module `Annotated[..., strawberry.lazy("module.path")]` annotations when the consumer wants Strawberry's explicit lazy import path
- annotation-only relation overrides, which keep the generated resolver
- `strawberry.field(resolver=...)` and `@strawberry.field` relation overrides, which keep the consumer resolver

Validation that a manual relation annotation matches the Django relation cardinality is deferred. Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships.

## Django field conversion

Status: shipped for common Django fields, deferred for some specialized fields.

Shipped scalar support:

- text-like fields (`CharField` / `TextField`) → `str`
- integer and auto fields (`IntegerField` / `AutoField` / `BigAutoField` / `SmallIntegerField` / `PositiveIntegerField`) → `int`
- boolean fields → `bool`
- float fields → `float`
- decimal fields → `decimal.Decimal`
- date / datetime / time / duration fields → Python-native time types
- UUID fields → `uuid.UUID`
- binary fields → `bytes`
- file and image fields → string path/URL values
- `null=True` → `T | None`
- Relay `GlobalID` mapping for auto IDs when `Meta.interfaces = (relay.Node,)` is declared

Shipped choice support:

- Django `choices` generate Strawberry enums
- enum objects are cached by `(model, field_name)`
- member names are sanitized from stored database values, not display labels
- grouped choices are rejected clearly

Deferred field conversion (see [Specialized scalar conversions](#specialized-scalar-conversions)):

- plain `BigIntegerField` with JSON-safe `BigInt`
- PostgreSQL `ArrayField`
- `JSONField`
- PostgreSQL `HStoreField`

The stable choice-enum naming override surface ships separately; see [Stable choice-enum naming overrides](#stable-choice-enum-naming-overrides).

## Relation handling

Status: shipped.

The package maps Django relation cardinality into GraphQL type shape and resolver behavior.

Shipped relation conversion:

- forward `ForeignKey` → target type, nullable when the field is nullable
- forward `OneToOneField` → target type, nullable when the field is nullable
- reverse `ForeignKey` → `list[target_type]`
- many-to-many → `list[target_type]`
- reverse one-to-one → target type or `None`

Shipped resolver behavior:

- many-side resolvers return lists, not Django managers
- reverse one-to-one resolvers return `None` when the related row does not exist
- forward resolvers can return FK-id stubs when the optimizer safely elides a join (see [Join avoidance and projection](#join-avoidance-and-projection))
- relation access cooperates with Django's prefetch and relation caches
- consumer-authored `strawberry.field` relation overrides are preserved instead of being clobbered by generated resolvers

Consumer overrides are responsible for their own queryset shape. If an override re-shapes a relation queryset with `.order_by(...)`, `.filter(...)`, or similar, it can bypass the framework's prefetched relation cache and introduce per-parent lazy queries.

## Queryset visibility hook

Status: shipped.

If you've used DRF, you already know this hook. `DjangoType.get_queryset(cls, queryset, info, **kwargs)` runs once per type, defaults to identity, and is where permission filters, tenant scoping, soft-delete, staff/public visibility splits, and request-user filters live.

The load-bearing behavior is optimizer cooperation: `has_custom_get_queryset()` reports whether a type or inherited intermediate base overrides the hook, and the optimizer downgrades a JOIN to a `Prefetch` when a target type defines one. Your visibility filter survives relation traversal instead of being bypassed by a raw `select_related` join.

## Automatic ORM optimization

Status: shipped.

`DjangoOptimizerExtension` translates selected GraphQL fields into Django ORM optimization calls. It is opt-in at Strawberry schema construction time.

Shipped behavior:

- root-gated optimization for root resolvers returning Django `QuerySet`s
- passthrough for non-root resolvers and non-`QuerySet` results
- `select_related` for safe single-valued relation chains
- `prefetch_related` for many-side relations
- generated `Prefetch` objects for child querysets
- nested prefetch chains for nested GraphQL selections
- `only` projection for selected scalar columns
- connector-column inclusion so Django can attach joined and prefetched rows without lazy loads
- custom `get_queryset` downgrade from join to `Prefetch`
- async resolver support

## Optimizer cache and planning features

Status: shipped.

The optimizer includes performance and correctness features beyond the baseline N+1 avoidance pattern.

Shipped value:

- **Plan cache.** The same query 10,000×/sec walks the selection tree once, not 10,000 times. Cache keys ignore filter variables that do not affect selection shape, so a query with many filter combinations can still reuse one cached plan.
- **Selection-shape keys.** Cache keys include the selected operation AST, relevant `@skip` / `@include` variables, target model, and root runtime path.
- **Multi-operation safety.** `query A { ... } query B { ... }` in one document never shares a plan across operations.
- **Named-fragment safety.** Directives inside named fragments are tracked into the cache key.
- **Introspection.** `cache_info()` exposes hit, miss, and size counts.
- **Request-scope safety.** Plans that embed request-scoped `get_queryset` results are marked uncacheable.
- **Low per-request overhead.** `DjangoType` precomputes optimizer field metadata at class creation, and cached plans are never mutated while reconciling against a specific queryset.

## Join avoidance and projection

Status: shipped.

The optimizer can avoid unnecessary database work in common relation shapes.

Shipped value:

- **FK-id elision.** `{ category { id } }` reads `category_id` off the parent row — no JOIN, no second query.
- **Safe fallback.** The optimizer falls back to a join when the target selection needs more than the primary key, when the target ID has a custom resolver, or when a target `get_queryset` hook must run.
- **Branch isolation.** Aliases and sibling root fields do not leak elision state into each other.
- **Column projection.** Scalar selections become `only()` projections.
- **Connector preservation.** Projection plans include connector columns for `select_related`, reverse FK, FK/OneToOne, and M2M attachment paths so Django can stitch related rows without lazy loads.

## Optimizer hints

Status: shipped.

Override the optimizer per relation when you know better than it does — skip a relation entirely, force a join, or hand it your own `Prefetch` for filtered children. Configure it in the same `class Meta` you already declared the type with:

```python
from django.db.models import Prefetch
from django_strawberry_framework import DjangoType, OptimizerHint
from myapp.models import Category, Item


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

Supported hint modes:

- `OptimizerHint.SKIP` — exclude a relation from automatic planning.
- `OptimizerHint.select_related()` — force `select_related`.
- `OptimizerHint.prefetch_related()` — force `prefetch_related`.
- `OptimizerHint.prefetch(Prefetch(...))` — use a consumer-provided `Prefetch` object and stop walking below that relation.

Validation:

- hint field names must exist on the model
- hint values must be `OptimizerHint` instances
- invalid hints fail at type creation with `ConfigurationError`

## Optimizer observability and safety

Status: shipped.

The optimizer exposes what it did instead of forcing consumers to infer behavior from SQL logs.

Shipped observability:

- latest plan stashed on `info.context.dst_optimizer_plan`
- FK-id elisions stashed on context
- strictness planned resolver keys stashed on context
- lookup paths stashed on context in strictness mode
- dict and object context support

Shipped N+1 detection:

- `strictness="off"` for silent production default
- `strictness="warn"` for logged warnings
- `strictness="raise"` for fail-fast tests/dev checks
- warnings / errors only when an unplanned relation access would actually lazy-load

Shipped schema audit:

- `DjangoOptimizerExtension.check_schema(schema)` audits schema-reachable `DjangoType`s
- hidden fields and `OptimizerHint.SKIP` fields are ignored
- relation targets without registered `DjangoType`s are reported as warnings

## Queryset diffing and consumer cooperation

Status: shipped.

The optimizer does not assume it owns the queryset. It reconciles framework-generated plans against queryset work the consumer already applied.

Shipped value:

- **Queryset cooperation.** If your resolver already calls `select_related("category")`, the optimizer does not reapply it.
- **Prefetch cooperation.** If your resolver returns `Category.objects.prefetch_related(Prefetch("items", queryset=...))`, the consumer `Prefetch` wins over less-specific automatic work.
- **Subtree-aware reconciliation.** `prefetch_related("items", "items__entries")` cooperates with the optimizer's nested `Prefetch("items", ...)` instead of raising Django's "lookup already seen with a different queryset" error.
- **Plain-string absorption.** Safe consumer string prefetches can be absorbed by richer optimizer `Prefetch` objects.
- **Cache safety.** Cached plans are copied before queryset-specific diffing, so one resolver's queryset shape cannot mutate a plan reused by another request.

## Planned subsystems

Per-subsystem preview of what lands between now and `1.0.0`. Each entry below has a `Status: planned for X.Y.Z` line and a brief contract preview; the canonical user-facing shape of the feature-complete API lives in [`../GOAL.md`'s astronomy showcase](../GOAL.md#what-success-looks-like-in-your-code); per-card ship sequencing lives in [`../KANBAN.md`](../KANBAN.md).

### Specialized scalar conversions

Status: planned for `0.0.6`.

`BigIntegerField` → JSON-safe `BigInt` scalar (string-serialized at the wire to survive JavaScript's 53-bit integer limit); `JSONField` → `strawberry.scalars.JSON`; PostgreSQL `ArrayField` → typed `list[T]` (recursive through `field.base_field`); PostgreSQL `HStoreField` → `dict[str, str | None]` (soft-registered, only when `django.contrib.postgres` is installed).

### `Meta.primary`

Status: planned for `0.0.6`.

Allows multiple `DjangoType` subclasses for one Django model. `Meta.primary = True` declares the type used for nested-relation resolution (`AdminItemType` vs `ItemType` for the same `Item` model). Today the registry rejects a second `DjangoType` for a model that already has one; this `Meta` key promotes the behavior to a primary-declaration contract with an explicit primary.

### Scalar field override semantics

Status: planned for `0.0.6`.

The stable contract layer for consumer-authored scalar field overrides, parallel to the shipped relation-override contract from `0.0.4` (`DONE-006`). Today consumers can override relation fields via annotation-only or `strawberry.field(resolver=...)` patterns; scalar field overrides remain an implementation detail until this card promotes the contract.

### `DjangoListField`

Status: planned for `0.0.7`.

Non-Relay `list[T]` root and nested fields. The smallest entry point for migrants coming from `graphene-django`'s `DjangoListField` and for use cases that do not need pagination, edges, or page-info. Accepts a `DjangoType`, derives the queryset from `Meta.model`, applies the type-level `get_queryset`, cooperates with the optimizer, accepts filter / ordering input when those subsystems are configured.

### Django `AppConfig`

Status: planned for `0.0.7`.

`django_strawberry_framework/apps.py` ships an `AppConfig` so consumers can add the package to `INSTALLED_APPS` and use Django checks / signal hooks against it.

### Schema export management command

Status: planned for `0.0.7`.

`manage.py export_schema [path]` writes the GraphQL SDL to a file. Mirrors `strawberry-django`'s `export_schema` command.

### Multi-database cooperation

Status: planned for `0.0.7`.

Pins the existing `router.db_for_read` cooperation in `types/resolvers.py` with a spec, tests, and a `FEATURES.md` status entry. Multi-db cooperation already exists in source today — this card documents it as a contract: the optimizer plans correctly under `.using()`, `Prefetch` chains respect routing, strictness mode tracks the originating connection, `get_queryset` downgrades respect routing. The companion BETTER.md item 41 covers first-class sharding-aware planning post-`1.0.0`.

### `FilterSet`

Status: planned for `0.0.8`.

Declarative filter classes with `Meta.model`, `Meta.fields` (dict form `{"name": ["exact", "icontains"]}` or `"__all__"` shorthand), `RelatedFilter` for cross-relation traversal (accepts class, absolute import path, or unqualified name for circular cases), `check_*_permission` denial gates, explicit-queryset scope boundaries that nested filters cannot bypass. Logical `and` / `or` / `not` operators on the input shape. Generated input types use stable class-derived names so two connection fields on the same model resolve to the same `FilterInputType` (Apollo cache friendly). The lazy-resolution architecture is borrowed verbatim from `django-graphene-filters` — six-layer pipeline; five layers are library-agnostic and port directly; only the cycle-safe forward reference (Graphene's `lambda:` → Strawberry's `strawberry.lazy()`) is engine-adapted.

### `OrderSet`

Status: planned for `0.0.8`.

Declarative ordering with `Meta.fields` (list form `["name", "created_date"]` or `"__all__"` shorthand), `RelatedOrder` for cross-relation traversal, `check_*_permission` gates. Reuses the filtering subsystem's lazy-resolution architecture verbatim with `OrderSet` substituted for `FilterSet`.

### `DjangoConnectionField`

Status: planned for `0.0.9`.

Relay-style connection field with `edges` / `node` / `pageInfo` / `totalCount`, cursor-based pagination, `filter` / `orderBy` / `search` arguments that flow into the connection's `DjangoType`'s `filterset_class` / `orderset_class` / `search_fields`. Composes with the optimizer for nested-selection planning. Works at root fields and at nested relation fields.

### Full Relay story

Status: planned for `0.0.9`.

The connective tissue between Relay Node (shipped in `0.0.5`) and Connection ([`DjangoConnectionField`](#djangoconnectionfield) above): `DjangoNodeField(SomeNode)` for root single-node lookup (the `category: GalaxyNode = DjangoNodeField(GalaxyNode)` shape in [`../GOAL.md`'s astronomy showcase](../GOAL.md#what-success-looks-like-in-your-code)), root `node(id:)` / `nodes(ids:)` query helpers, reverse-FK / M2M relation-as-Connection upgrade, cursor pagination math, schema-validation diagnostics, test helpers. The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`) as part of this card.

### Connection-aware optimizer planning

Status: planned for `0.0.9`.

The optimizer learns to recognize `edges { node { ... } }` selections and plan `Prefetch` chains correctly across connection-paginated relations. Without this, nested connections fall back to per-row queries.

### Permissions subsystem

Status: planned for `0.0.10`.

`apply_cascade_permissions(cls, queryset, info)` — cascades each `DjangoType`'s `get_queryset` filter to its related types when reaching through FK / M2M. Per-field permission hooks via `check_*_permission` methods on the type's `FieldSet`. Field-level redaction (silent safe-value fallback) and denial (raise via `GraphQLError`). Composes with filter / order / aggregate permission gates and with the post-write return value of mutations.

### Mutations subsystem

Status: planned for `0.0.11`.

`DjangoMutation` base class with `Meta`-driven configuration; auto-generated `Input` (all fields required) and `PartialInput` (all fields optional) types from Django models that preserve the relation-override contract from the foundation slice; shared `errors: list[FieldError]` envelope reused across every mutation flavor; sync and async resolver paths; composition with the optimizer for the post-write return value (re-fetching the mutated row with the right `select_related` / `prefetch_related` for the response selection).

### `Upload` scalar

Status: planned for `0.0.11`.

Strawberry `Upload` scalar mapping for `FileField` / `ImageField` on mutation inputs. `DjangoFileType` / `DjangoImageType` output types carrying `name` / `path` / `size` / `url`.

### Form-based mutations

Status: planned for `0.0.11`.

`DjangoFormMutation` (consumes Django `Form`) and `DjangoModelFormMutation` (consumes `ModelForm`) — declarative `Meta.form_class` shape; validation errors surface through the shared `errors: list[FieldError]` envelope (populated from `form.errors`); the post-save object is the mutation return value.

### DRF serializer mutations

Status: planned for `0.0.11`.

`SerializerMutation` consumes DRF `Serializer` / `ModelSerializer` via `Meta.serializer_class`, `Meta.lookup_field`, `Meta.model_operations`, `Meta.optional_fields`. Existing Serializers move to GraphQL without re-declaring validation; input-type factory derives the Strawberry input shape from the serializer's fields. Soft dependency on `rest_framework`.

### Auth mutations

Status: planned for `0.0.11`.

`login` / `logout` / `register` mutations plus a `current_user` query helper. Opt-in via explicit import; not bundled into the default schema. Composes with the existing `DjangoMutation` envelope and with `django.contrib.auth`.

### Channels ASGI router

Status: planned for `0.0.12`.

`DjangoGraphQLProtocolRouter` — a Channels `ProtocolTypeRouter`-wrapping helper for consumers using Channels. Soft dependency on `channels`; symbol name is intentionally distinct from `strawberry-django`'s `AuthGraphQLProtocolTypeRouter` to avoid migration ambiguity (the migration guide maps the equivalents).

### Debug-toolbar middleware

Status: planned for `0.0.12`.

`django-debug-toolbar` SQL-panel integration during `/graphql/` requests. Mirrors `strawberry-django`'s `middlewares/debug_toolbar.py` shape.

### Test client helper

Status: planned for `0.0.12`.

`TestClient`, `AsyncTestClient`, and a `GraphQLTestCase` base class for live HTTP-level testing patterns. Mirrors `strawberry-django`'s `test/client.py`.

### Response-extensions debug middleware

Status: planned for `0.0.12`.

Surfaces executed SQL queries and raised exceptions through the GraphQL response's `extensions` envelope so frontend clients can read them without the toolbar. Distinct from [Debug-toolbar middleware](#debug-toolbar-middleware): this is in-response, that is server-side panel — both useful, not mutually exclusive.

### `FieldSet`

Status: planned for `0.1.1`.

Declarative field selection class for the `Meta.fields_class` surface. Carries field-level permission checks (`check_*_permission` denial gates), custom field resolvers (`resolve_*` overrides), computed fields (class-level annotations), and redaction / deny-value behavior. Integrates with generated model fields; declared per-type via `Meta.fields_class = MyTypeFieldSet`.

### `Meta.search_fields`

Status: planned for `0.1.2`.

Declarative search across model fields (and relation paths). Single `search: String` argument on connection fields fans out across the listed fields as an OR'd `icontains` filter — equivalent to `django-graphene-filters`'s `Meta.search_fields = ("name", "description", "category__name")` shape.

### `AggregateSet`

Status: planned for `0.1.3`.

`AggregateSet` with `Sum` / `Count` / `Avg` / `Min` / `Max` / `Mode` / `Uniques` / `GroupBy`, `RelatedAggregate` traversal, custom `compute_*_*` stats declared via `Meta.custom_stats`, sync and async paths via `compute` / `acompute`, selection-set-aware computation (only requested stats are computed), `get_child_queryset` cascade hook for excluding private rows when traversing into children.

### Stable choice-enum naming overrides

Status: planned for `0.1.4`.

`Meta.choice_enum_names = {"status": "ItemStatusEnum"}` overrides the first-`DjangoType`-wins enum-naming behavior that ships today. Pins a stable contract for renaming generated choice enums.

## Planned integration goals

Cross-subsystem invariants that the Layer-3 cards collectively satisfy by `1.0.0`:

- Deferred `Meta` keys become accepted only when their subsystem applies them end-to-end (this rule resolves entirely at `1.0.0`).
- Filters, orders, aggregates, mutations, permissions, and connection fields all compose with the optimizer.
- The validation-error envelope is shared across every mutation flavor for a consistent client contract.
- Fakeshop GraphQL schema activates only as its dependencies ship; never references unshipped features.

## Enhancements over strawberry-graphql-django

For the migration code diff coming from `strawberry-graphql-django`, see [`../GOAL.md`'s Coming-from-strawberry-graphql-django section](../GOAL.md#coming-from-strawberry-graphql-django). The enhancements below are the specific package-level capabilities gained.

API enhancements:

- DRF-shaped nested `Meta` configuration instead of decorator-first configuration
- field selection, future filters, future orders, future aggregates, future permissions, and optimizer hints all belong to one class-local configuration surface
- deferred features fail loudly instead of becoming accepted no-ops
- typed optimizer hints replace mixed strings / dicts / decorator flags

Optimizer performance enhancements:

- cached optimization plans for hot repeated operations
- directive-aware cache keys that ignore variables unrelated to selection shape
- named-fragment directive support in cache keys
- selected-operation hashing for multi-operation documents
- precomputed field metadata instead of per-request `_meta.get_fields()` walks
- FK-id elision for `id`-only forward relation selections
- queryset diffing before applying framework plans
- subtree-aware prefetch reconciliation

Optimizer correctness and debugging enhancements:

- branch-sensitive resolver keys for aliases and sibling root fields
- strictness mode for warning or raising on accidental N+1s
- plan introspection through `info.context`
- schema audit for unregistered relation targets
- cached-plan immutability during queryset-specific diffing
- consumer `Prefetch` objects respected as more specific than automatic plans

Django-stack enhancements:

- visibility filtering remains in `get_queryset`
- query planning uses standard Django ORM primitives
- database routing and relation / prefetch caches are preserved
- future features are shaped around DRF / django-filter conventions rather than Strawberry decorator conventions

## Enhancements over graphene-django

For the migration code diff coming from `graphene-django`, see [`../GOAL.md`'s Coming-from-graphene-django section](../GOAL.md#coming-from-graphene-django). The enhancements below are the specific package-level capabilities gained.

Engine and typing enhancements:

- Strawberry is the underlying GraphQL engine
- modern Python annotations drive GraphQL type generation
- async-compatible resolver lifecycle
- typed package marker for static-analysis consumers
- no dependency on Graphene's older type system

Django API enhancements:

- DRF-style `Meta` surface stays familiar to graphene-django users
- `ConfigurationError` catches unsupported and misspelled config early
- choice fields generate Strawberry enums while preserving database values
- relation cardinality is inferred from Django model metadata
- type-level `get_queryset` remains the central visibility hook

ORM optimization enhancements:

- built-in N+1 optimizer is part of the shipped foundation
- nested relation selections are optimized automatically
- `only` projection reduces selected columns
- `Prefetch` downgrade preserves permission/visibility filtering across relation boundaries
- strictness mode and plan introspection make query behavior testable

Future migration advantage:

- planned filters, orders, aggregates, connection fields, and permissions target the familiar Django / DRF mental model
- teams can move toward Strawberry without giving up Django-shaped schema declarations

## Deferred and future work

Items beyond the `0.1.0` / `1.0.0` roadmap are tracked in [`../BETTER.md`](../BETTER.md). They are not committed to a ship version — they graduate into [`../KANBAN.md`](../KANBAN.md) cards when scheduled.

Roadmap-adjacent items already in `BETTER.md`:

- Apollo Federation support (deferred unless a real consumer asks) — BETTER item 34
- model-property / cached-property optimizer hints — folded into BETTER item 14 (`Meta.computed_fields`)
- shared queryset introspection helpers (`utils/queryset.py`) — BETTER item 36
- public-surface promotion discipline — BETTER item 37
- layered manual relation-override test policy — BETTER item 38
- first-class multi-db / sharding-aware optimizer — BETTER item 41

Strategic differentiators that go beyond either upstream — e.g. unified declarative permissions, selection-aware annotations, content-versioned Node types, optimizer "explain" extension, OpenTelemetry integration, Django-signal-driven subscriptions, persisted queries, per-tenant schema variants, soft-delete cooperation — also live in [`../BETTER.md`](../BETTER.md).

Dedicated migration guides are tracked in [`../KANBAN.md`](../KANBAN.md) (graphene-django, strawberry-graphql-django, DRF / django-filter), so this file can stay focused on package capabilities.
