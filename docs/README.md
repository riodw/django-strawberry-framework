# django-strawberry-framework

`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL. It lets Django teams build GraphQL APIs from Django models using the familiar `class Meta` style instead of a decorator-heavy surface.

For the project pitch, migration context, and the canonical documentation map, start from [`../README.md`][readme]. For the long-term destination, see [`../GOAL.md`][goal]. For the current capability snapshot, see [`../TODAY.md`][today]. For contributor / maintainer workflow (dev setup, format, test, build, publish), see [`../CONTRIBUTING.md`][contributing].

## Installation

```shell
# pip
pip install django-strawberry-framework
# uv
uv add django-strawberry-framework
```

## Quick start

```python
import strawberry
from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types, strawberry_config
from myapp.models import Category, Item


class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")


class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category")


@strawberry.type
class Query:
    @strawberry.field
    def all_items(self) -> list[ItemType]:
        return Item.objects.all()


finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

The optimizer is a module-level singleton wrapped in a factory — that preserves the instance-bound [Plan cache][glossary-plan-cache] (Strawberry runs the callable per request and gets the same instance back) and emits no deprecation warning (the entry is a callable, not an instance).

That is the shipped surface: `class Meta` configures the type, `finalize_django_types()` resolves relations after all `DjangoType` modules are imported, and the optimizer extension turns nested selections into Django ORM `select_related`, `prefetch_related`, and `only` calls. Relation fields can point at target types declared earlier or later, as long as every target type is registered before finalization.

### Relay Node

Add `Meta.interfaces = (relay.Node,)` to declare a Relay-node-shaped type. The package wires `id: GlobalID!`, the four `resolve_*` defaults, and `is_type_of` injection without any decorators on the consumer class.

```python
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType, finalize_django_types
from myapp.models import Category


class CategoryNode(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        interfaces = (relay.Node,)


finalize_django_types()
```

See [`GLOSSARY.md`'s Relay Node integration subsection][glossary-relay-node-integration] for the resolver list, composite-pk constraint, and the `is_type_of` injection contract.

As of `0.0.9` the default Relay `GlobalID` payload is the Django model label (`app_label.modelname:<pk>`, e.g. `products.item:42`) rather than the GraphQL type name, so renaming a GraphQL type no longer invalidates cached IDs. `Meta.globalid_strategy` (per type) and `RELAY_GLOBALID_STRATEGY` (schema-wide) select `model` (default), `type` (the legacy GraphQL-type-name opt-out), `type+model` (transitional decode of old type-anchored IDs while emitting model-anchored ones), or a callable encoder. See [`GLOSSARY.md`'s `Meta.globalid_strategy` subsection][glossary-metaglobalid_strategy].

> **Multiple `DjangoType`s per model under the `model` default.** A model-label payload is shared by every `DjangoType` over that model and always decodes to the model's **primary** type (`Meta.primary`). So if two Relay-Node types over one model both use the `model` default, the secondary's `GlobalID`s refetch as the primary — its distinct identity and `get_queryset` scope collapse onto the primary's (under the pre-`0.0.9` type-name default they were distinct and self-routing). This is intentional (a model-anchored ID cannot distinguish secondaries), and finalization emits a warning naming the collapsing secondaries; give a secondary disjoint identity with `Meta.globalid_strategy = "type"`.

## What just happened?

- `class Meta` tells the package which Django model and fields become a Strawberry type.
- Returning a Django `QuerySet` from the root resolver gives the optimizer something it can shape.
- `DjangoOptimizerExtension()` walks the selected GraphQL fields once at the root and applies one ORM plan.
- Nested relations become joins, prefetches, projections, and strictness checks without replacing your queryset.

## Today and coming next

For the current capability snapshot — what the package can actually do in the example project right now — see [`../TODAY.md`][today]. For the per-feature glossary covering every shipped / planned / deferred capability (deep-linkable by anchor — `GLOSSARY.md#filterset`, `GLOSSARY.md#fk-id-elision`, …), see [`GLOSSARY.md`][glossary]. For the long-term destination and the migration-shape diffs against `graphene-django` and `strawberry-graphql-django`, see [`../GOAL.md`][goal].

A quick summary:

**Shipped today** (`0.0.8`):
- `DjangoType` — model-backed Strawberry types via `class Meta`
- scalar conversion (text, integer, boolean, float, decimal, date/time, UUID, binary, file/image, choice enums)
- specialized scalar conversions (`BigIntegerField` / `PositiveBigIntegerField` → `BigInt`, `JSONField` → `JSON`, PostgreSQL `ArrayField` → `list[T]`, PostgreSQL `HStoreField` → `JSON`)
- relation conversion (forward / reverse FK, forward / reverse OneToOne, forward / reverse M2M)
- `Meta.interfaces = (relay.Node,)` for Relay-node-shaped types with `id: GlobalID!`
- generated relation resolvers, with annotation-only and `strawberry.field` consumer overrides preserved
- definition-order-independent relation finalization via `finalize_django_types()`
- `get_queryset` visibility hook (cooperates with the optimizer via `Prefetch` downgrade)
- `DjangoOptimizerExtension` — automatic ORM optimization: one selection-tree walk produces a `select_related` / `prefetch_related` / `only()` plan that cooperates with querysets you've already shaped (consumer entries are respected, not clobbered). Plan caching, FK-id elision for `{ relation { id } }`, `get_queryset` → `Prefetch` downgrade so visibility filters survive joins, and strictness mode (`off` / `warn` / `raise`) for accidental-N+1 detection are all in the box. As of `0.0.9` the walk is connection-aware: a nested `<field>Connection`'s `edges { node }` selection gets a windowed `Prefetch` (one window-function query per relation per request instead of one per parent) and strictness flags an unplanned, unserved nested-connection access. See [`GLOSSARY.md`][glossary] for the full optimizer surface.
- `DjangoListField` — non-Relay `list[T]` factory for root Query fields (new in `0.0.7`); default resolver pulls `model._default_manager.all()` and applies the type's `get_queryset` in sync + async contexts. See [`GLOSSARY.md#djangolistfield`][glossary-djangolistfield].
- `OptimizerHint` — per-relation overrides (`SKIP`, `select_related`, `prefetch_related`, custom `Prefetch`)
- model / type registry and `auto` re-export from Strawberry
- `Meta.primary` — multiple `DjangoType` subclasses per Django model with explicit primary-flag opt-in
- annotation-only and `strawberry.field` consumer overrides for scalar fields, symmetric with the shipped relation-override contract (consumer overrides bypass `convert_scalar` validations; `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time)
- `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`).
- `manage.py export_schema` — Django management command that prints or writes the GraphQL SDL for a `strawberry.Schema` symbol (positional dotted path, optional `--path`); migration-parity with `strawberry-django`'s command of the same name. See [`GLOSSARY.md#schema-export-management-command`][glossary-schema-export-management-command].
- filtering subsystem (new in `0.0.8`) — `FilterSet` declarative filter classes with `Meta.fields` (dict / `"__all__"` shorthand) and the full `django-filter` lookup surface; `RelatedFilter` for cross-relation traversal (class / absolute import path / unqualified-name); `Meta.filterset_class` consumer wiring; the `filter_input_type` resolver-argument helper; finalizer phase-2.5 binding with orphan validation; per-field `check_*_permission` denial gates with active-input-only scope; clean composition with `get_queryset` visibility and the optimizer. See [`GLOSSARY.md#filterset`][glossary-filterset].
- ordering subsystem (new in `0.0.8`) — `OrderSet` declarative ordering classes with `Meta.fields` (list form or `"__all__"` shorthand for every column-backed model field); `RelatedOrder` cross-relation ordering traversal (class / absolute import path / unqualified-name); `Meta.orderset_class` consumer wiring (promoted out of `DEFERRED_META_KEYS`); the public `Ordering` enum (six members with NULLS positioning); the `order_input_type` resolver-argument helper; finalizer phase-2.5 binding with orphan validation; per-field `check_*_permission` denial gates with active-input-only scope plus active-branch dispatch on `RelatedOrder` branches; clean composition with the shipped filter subsystem and the optimizer. See [`GLOSSARY.md#orderset`][glossary-orderset].
- `DjangoConnectionField` (new in `0.0.9`) — Relay connection field over a Relay-Node-shaped `DjangoType`: `edges` / `node` / `pageInfo` cursor pagination on Strawberry's native `relay.connection()`, with `filter:` / `orderBy:` arguments derived from the wrapped type's `Meta.filterset_class` / `Meta.orderset_class` sidecars (no hand-written list resolver, no parallel argument declarations) and an opt-in `totalCount` via `Meta.connection = {"total_count": True}` (counted on the post-filter pre-slice queryset, selection-gated, per connection instance). Composition pipeline runs `get_queryset` visibility → `filter` → `orderBy` → default deterministic pk-ordering → optimizer-plan → cursor slice; the field owns its own optimizer cooperation point. `DjangoConnection[T]` is the generic return-type alias. See [`GLOSSARY.md#djangoconnectionfield`][glossary-djangoconnectionfield].
- `DjangoNodeField` / `DjangoNodesField` (new in `0.0.9`) — root Relay refetch fields, bare interface (`node: relay.Node | None = DjangoNodeField()`, `nodes: list[relay.Node | None] = DjangoNodesField()`) and typed (`genre: GenreType | None = DjangoNodeField(GenreType)`) forms; `id: ID!` raw-string arguments decoded server-side via the strategy-aware dispatch; dispatch to the type's `resolve_node` / `resolve_nodes` honoring `get_queryset`; `null` for hidden/missing/uncoercible-pk ids (no existence leak), `GraphQLError` with `extensions={"code": "GLOBALID_INVALID"}` for malformed ids; `nodes` is per-type-batched, order-preserving, with `null` holes and duplicate-id support. See [`GLOSSARY.md#djangonodefield`][glossary-djangonodefield].
- relation-as-Connection upgrade + `Meta.relation_shapes` (new in `0.0.9`) — every Relay-Node-shaped type's many-side relations whose target is also Relay-Node-shaped gain a `<field>Connection` sibling by default (`"both"`); `Meta.relation_shapes = {"<field>": "list" | "connection" | "both"}` narrows per relation; synthesized at finalization Phase 2.5 reusing the shipped connection machinery (per-target connection classes, sidecar `filter:` / `orderBy:` arguments, target-driven `totalCount`). See [`GLOSSARY.md#metarelation_shapes`][glossary-metarelation_shapes].
- `testing.relay` helpers (new in `0.0.9`) — `django_strawberry_framework.testing.relay.global_id_for(type_cls, id)` (the strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits) and `decode_global_id(gid)` (public re-export of the decode dispatch). See the [`GLOSSARY.md#djangonodefield`][glossary-djangonodefield] cross-refs (the helpers have no own entry; the spec does not create one).
- `Meta.nullable_overrides` / `Meta.required_overrides` (new in `0.0.9`) — two tuple-set `Meta` keys that decouple a scalar field's GraphQL nullability from its Django column (`T!`→`T` or `T`→`T!`) without an `AlterField` migration or a consumer-authored annotation. Validated at type-creation (unknown / excluded / consumer-authored / relation / Relay-suppressed-pk targets and the both-sets collision raise `ConfigurationError`); scalar-only, and the override flips a choice field's generated enum nullability for free. See [`GLOSSARY.md#metanullable_overrides`][glossary-metanullable_overrides].
- `manage.py inspect_django_type` (new in `0.0.9`) — diagnostic command printing a finalized `DjangoType`'s per-field GraphQL resolution table (Django field → resolved GraphQL type → nullability → converter row). Dispatches the positional arg by shape (dotted path vs unique bare-name registry lookup) and accepts `--schema <selector>` to register + finalize on a cold CLI process. See [`GLOSSARY.md#schema-introspection-management-command`][glossary-inspect-django-type].
- `apply_cascade_permissions` / `aapply_cascade_permissions` (new in `0.0.10`) — cascade-permissions subsystem: one call inside a type's `get_queryset` cascades that type's visibility across its single-column forward FK / OneToOne edges, dropping parent rows whose targets a target type's own `get_queryset` hides. Four invariants (`ContextVar` cycle guard, single-column forward scope, nullable-FK preservation, caller-alias pinning), loud `fields=` validation, a sync + `sync_to_async` async pair, and zero added query round-trips (the `__in` subqueries compile into the caller's single `SELECT`); composes with the shipped `check_<field>_permission` gates, connections, node refetch, and list fields through their existing seams. Exported from the package root. See [`GLOSSARY.md#apply_cascade_permissions`][glossary-apply-cascade-permissions].

**Coming next — remaining alpha (`0.0.10` → `0.0.12`):**
- `0.0.10` — optimizer robustness hardening (upstream-comparison guards; the `035` joint-cut sibling)
- `0.0.11` — mutations + auto-generated `Input` types (form-based and DRF-`SerializerMutation` flavors), the `Upload` scalar + file/image field mapping, and auth mutations (`login` / `logout` / `register`)
- `0.0.12` — Channels ASGI router, debug-toolbar middleware, test-client helper, response-extensions debug middleware

**`0.1.0`** — beta release: feature parity with `graphene-django` and `strawberry-graphql-django` (alpha → beta cut-over).

**Beta (`0.1.x`)** — Layer-3 depth on the road to `1.0.0`:
- `0.1.1` — `FieldSet` (declarative `fields_class`)
- `0.1.2` — `Meta.search_fields` + Postgres full-text-search filter primitives
- `0.1.3` — `AggregateSet` (`Sum` / `Count` / `Avg` / `Min` / `Max` / `GroupBy`, `aggregate_class`) + Layer-3 `Meta`-key promotion
- `0.1.4` — stable choice-enum naming overrides
- `0.1.5` — fakeshop GraphQL schema activation end-to-end + product-catalog Layer-3 HTTP tests
- `0.1.6` — migration and adoption guides

**`1.0.0`** — stable release: full `django-graphene-filters` depth + **API freeze** (strict SemVer applies from `1.0.0` forward).

## Schema setup boundary

`finalize_django_types()` must run once during single-threaded import/schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed. The most common failure mode is forgetting to import a module that contains a related type before finalization.

Recommended:

```python
from django_strawberry_framework import finalize_django_types, strawberry_config

from myapp import types as _types  # noqa: F401

finalize_django_types()
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])
```

Wrong order:

```python
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])
finalize_django_types()
```

The second form constructs the Strawberry schema before relation targets are finalized, so exposed relations whose target type was still pending cannot be resolved into concrete `DjangoType`s.

## Running the example project

The repository ships with a fakeshop example project that exercises the shipped surface against a real Django app.

```shell
# Apply migrations to the example app
uv run python examples/fakeshop/manage.py migrate

# Start the dev server (admin + GraphiQL at /graphql/)
uv run python examples/fakeshop/manage.py runserver
```

The dev landing page at `/` links to GraphiQL, the admin, and the seed/delete query-param triggers. For the full example walkthrough see [`../examples/fakeshop/README.md`][fakeshop-readme].

### Seeding the example database

The fakeshop example dynamically discovers **all** Faker providers at runtime and seeds the database accordingly. The command is idempotent — it ensures at least N items exist per provider and only creates the shortfall.

```shell
# Ensure 5 items per provider (default)
uv run python examples/fakeshop/manage.py seed_data

# Ensure 50 items per provider
uv run python examples/fakeshop/manage.py seed_data 50

# Delete the first 10 items (and their cascading entries)
uv run python examples/fakeshop/manage.py delete_data 10

# Delete all items and entries
uv run python examples/fakeshop/manage.py delete_data all

# Wipe all four tables (Category, Property, Item, Entry)
uv run python examples/fakeshop/manage.py delete_data everything
```

The same actions are reachable from the admin via query-param triggers — see the dev landing page at `/` for clickable links.

### Test users

Create test users with individual Django `view_*` permissions for exercising `get_queryset` permission branches. Each set creates 6 users: 1 staff, 1 regular (no perms), and 4 per-model permission users (`view_category`, `view_item`, `view_property`, `view_entry`). All share password `admin`. Superusers are never deleted.

```shell
# Create 1 set of test users (6 users)
uv run python examples/fakeshop/manage.py create_users

# Create 3 sets (18 users)
uv run python examples/fakeshop/manage.py create_users 3

# Delete all non-superusers
uv run python examples/fakeshop/manage.py delete_users all

# Delete the first 5 non-superusers
uv run python examples/fakeshop/manage.py delete_users 5
```

### Sharded mode (multi-DB)

The example ships with an additive two-alias layout for exercising multi-database scenarios. Toggle the secondary shard via `FAKESHOP_SHARDED=1`:

```shell
# Materialize the secondary shard SQLite file (idempotent)
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards

# Larger seed for stress testing
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards --count 5000
```

In sharded mode `default` keeps pointing at `db.sqlite3` (same file as single-DB mode) and `shard_b` adds `db_shard_b.sqlite3`. The two modes share the same `default` file, so a single dev workflow (`manage.py seed_data`, etc.) populates the default alias either way; the sharded mode only ADDS the secondary shard. The committed `db_shard_b.sqlite3` ships with a minimal seed via `seed_shards` so the sharded mode works out of the box.

For the cooperation contract these shards run against — explicit `.using()` `_db` preservation, FK-id elision router hints, consumer-provided `Prefetch(queryset=…)` alias round-trips, and strictness-mode behavior under non-default aliases — see [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation].

## Using the package in your own project

If you want to develop against a local checkout of this package from another Django project:

1. Go to the project you want to install the package in.
2. Add `django-strawberry-framework` to your `pyproject.toml` dependencies.
3. Point it at your local checkout:

```toml
# In your project's pyproject.toml
[tool.uv.sources]
django-strawberry-framework = { path = "../django-strawberry-framework", editable = true }
```

Then run:

```shell
uv sync
```

For status, the milestone roadmap, and contributor signposts, see [`../README.md`'s status section][readme-status] and [`../CONTRIBUTING.md`][contributing].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[readme]: ../README.md
[readme-status]: ../README.md#status
[today]: ../TODAY.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[glossary-apply-cascade-permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy
[glossary-metanullable_overrides]: GLOSSARY.md#metanullable_overrides
[glossary-inspect-django-type]: GLOSSARY.md#schema-introspection-management-command
[glossary-metarelation_shapes]: GLOSSARY.md#metarelation_shapes
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-schema-export-management-command]: GLOSSARY.md#schema-export-management-command

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-readme]: ../examples/fakeshop/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
