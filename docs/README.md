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

schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[DjangoOptimizerExtension()],
)
```

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

## What just happened?

- `class Meta` tells the package which Django model and fields become a Strawberry type.
- Returning a Django `QuerySet` from the root resolver gives the optimizer something it can shape.
- `DjangoOptimizerExtension()` walks the selected GraphQL fields once at the root and applies one ORM plan.
- Nested relations become joins, prefetches, projections, and strictness checks without replacing your queryset.

## Today and coming next

For the current capability snapshot — what the package can actually do in the example project right now — see [`../TODAY.md`][today]. For the per-feature glossary covering every shipped / planned / deferred capability (deep-linkable by anchor — `GLOSSARY.md#filterset`, `GLOSSARY.md#fk-id-elision`, …), see [`GLOSSARY.md`][glossary]. For the long-term destination and the migration-shape diffs against `graphene-django` and `strawberry-graphql-django`, see [`../GOAL.md`][goal].

A quick summary:

**Shipped today** (`0.0.7`):
- `DjangoType` — model-backed Strawberry types via `class Meta`
- scalar conversion (text, integer, boolean, float, decimal, date/time, UUID, binary, file/image, choice enums)
- specialized scalar conversions (`BigIntegerField` / `PositiveBigIntegerField` → `BigInt`, `JSONField` → `JSON`, PostgreSQL `ArrayField` → `list[T]`, PostgreSQL `HStoreField` → `JSON`)
- relation conversion (forward / reverse FK, forward / reverse OneToOne, forward / reverse M2M)
- `Meta.interfaces = (relay.Node,)` for Relay-node-shaped types with `id: GlobalID!`
- generated relation resolvers, with annotation-only and `strawberry.field` consumer overrides preserved
- definition-order-independent relation finalization via `finalize_django_types()`
- `get_queryset` visibility hook (cooperates with the optimizer via `Prefetch` downgrade)
- `DjangoOptimizerExtension` — automatic ORM optimization: one selection-tree walk produces a `select_related` / `prefetch_related` / `only()` plan that cooperates with querysets you've already shaped (consumer entries are respected, not clobbered). Plan caching, FK-id elision for `{ relation { id } }`, `get_queryset` → `Prefetch` downgrade so visibility filters survive joins, and strictness mode (`off` / `warn` / `raise`) for accidental-N+1 detection are all in the box. See [`GLOSSARY.md`][glossary] for the full optimizer surface.
- `DjangoListField` — non-Relay `list[T]` factory for root Query fields (new in `0.0.7`); default resolver pulls `model._default_manager.all()` and applies the type's `get_queryset` in sync + async contexts. See [`GLOSSARY.md#djangolistfield`][glossary-djangolistfield].
- `OptimizerHint` — per-relation overrides (`SKIP`, `select_related`, `prefetch_related`, custom `Prefetch`)
- model / type registry and `auto` re-export from Strawberry
- `Meta.primary` — multiple `DjangoType` subclasses per Django model with explicit primary-flag opt-in
- annotation-only and `strawberry.field` consumer overrides for scalar fields, symmetric with the shipped relation-override contract (consumer overrides bypass `convert_scalar` validations; `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time)
- `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`).
- `manage.py export_schema` — Django management command that prints or writes the GraphQL SDL for a `strawberry.Schema` symbol (positional dotted path, optional `--path`); migration-parity with `strawberry-django`'s command of the same name. See [`GLOSSARY.md#schema-export-management-command`][glossary-schema-export-management-command].


**Coming in `0.1.0`** (beta — feature parity with `graphene-django` and `strawberry-graphql-django`):
- `DjangoConnectionField` (Relay connection)
- filters, orders, and permissions / cascade permissions
- mutations + auto-generated `Input` types, plus form-based and DRF-serializer-based mutation flavors
- `Upload` scalar and file-field mapping
- auth mutations (`login` / `logout` / `register`) and `current_user` query
- Channels ASGI router, debug-toolbar middleware, test client helper, response-extensions debug

**Coming in `1.0.0`** (stable — `django-graphene-filters` depth + API freeze):
- `FieldSet` (declarative `fields_class`)
- `AggregateSet` with `Sum` / `Count` / `Avg` / `Min` / `Max` / `GroupBy` (`aggregate_class`)
- `Meta.search_fields`
- stable choice-enum naming overrides
- fakeshop GraphQL schema activation end-to-end
- migration and adoption guides
- API freeze: strict SemVer applies from `1.0.0` forward

## Schema setup boundary

`finalize_django_types()` must run once during single-threaded import/schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed. The most common failure mode is forgetting to import a module that contains a related type before finalization.

Recommended:

```python
from django_strawberry_framework import finalize_django_types, strawberry_config

from myapp import types as _types  # noqa: F401

finalize_django_types()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])
```

Wrong order:

```python
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])
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
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
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
