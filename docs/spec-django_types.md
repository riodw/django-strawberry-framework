# Spec: DjangoType Foundation

## Problem statement

`django-strawberry-framework` needs a first load-bearing primitive that both graphene-django and strawberry-graphql-django already provide: a way to turn a Django model into a GraphQL type. In this package that primitive must be DRF-shaped, meaning configuration lives in a nested `Meta` class, not in stacked decorators. This same primitive must also solve the most common GraphQL performance failure mode — N+1 relation queries — because every later subsystem (`FilterSet`, `OrderSet`, `AggregateSet`, permissions, connection fields) will sit on top of it.

## Current state

The package source currently contains only `django_strawberry_framework/conf.py`. The aspirational example schema at `examples/fakeshop/fakeshop/products/schema.py` already assumes the existence of `DjangoType`, `DjangoConnectionField`, and `apply_cascade_permissions`. The sibling files `examples/fakeshop/fakeshop/products/filters.py`, `orders.py`, `aggregates.py`, and `fields.py` likewise assume a future package surface, but none of those names exist yet.

The example data model is already stable enough to drive this spec: `Category`, `Item`, `Property`, and `Entry` in `examples/fakeshop/fakeshop/products/models.py`, with seed helpers in `examples/fakeshop/fakeshop/products/services.py` and real-world integration tests in `tests/`.

graphene-django's overlapping foundation is `DjangoObjectType` plus the model/type registry and the field converter layer at `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py:132-258`, `registry.py:1-42`, and `converter.py:182-507`. That gives us the core Meta options, the model registry, scalar field conversion, enum-from-choices, Relay node support, and relation-field generation.

strawberry-graphql-django's overlapping foundation is `@strawberry_django.type(...)`, `StrawberryDjangoField`, and the `DjangoOptimizerExtension`, documented at `https://strawberry.rocks/docs/django/guide/types`, `https://strawberry.rocks/docs/django/guide/optimizer`, and implemented in `strawberry_django/type.py` / `strawberry_django/fields/field.py`. That gives us the modern parts graphene-django lacks: automatic `select_related` / `prefetch_related` / `only()` optimization, field-level optimization hints, and a clean integration with Strawberry's type system.

## What both libraries overlap on

Both libraries, despite different APIs, solve the same foundational problem set:

model -> GraphQL type generation

scalar Django field -> GraphQL scalar conversion

relation field generation for FK / OneToOne / reverse FK / M2M

a type-level queryset hook (`get_queryset`) for scoping data

a registry that lets relation conversion look up the target GraphQL type by model

Relay node / global ID support

choices -> enum conversion

This overlap is the right scope for the first spec. Anything beyond that — filter argument generation, ordering, aggregations, per-field permissions, sentinel nodes — depends on this foundation and should be deferred.

## Goal

Add a `DjangoType` base class and a `DjangoOptimizerExtension` so that consumers can declare a Strawberry GraphQL type from a Django model using a DRF-shaped `Meta` class and have relation resolution optimized by default.

## Non-goals

This spec does not implement `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `DjangoConnectionField`, `apply_cascade_permissions`, per-field permission hooks, mutations, polymorphic interfaces, or the full relay connection story. Those follow later. The first spec only creates the foundation that later specs can attach to.

## Proposed public surface

This spec adds three public names at the package root:

`DjangoType`

`DjangoOptimizerExtension`

`auto` (re-exported from `strawberry`)

It also adds internal support modules: `registry.py`, `converters.py`, `exceptions.py`, and a `py.typed` marker.

The `auto` re-export is a pass-through of `strawberry.auto` so consumers can annotate fields inside a `DjangoType` without a separate `import strawberry`.

```python
from django_strawberry_framework import DjangoType, DjangoOptimizerExtension, auto
from django_strawberry_framework.exceptions import ConfigurationError
```

## `DjangoType`

`DjangoType` is a base class with a metaclass (or equivalent `__init_subclass__` pipeline) that reads a nested `Meta` class, synthesizes Strawberry annotations from the Django model, registers the resulting type for later relation lookup, and then finalizes the class as a Strawberry type.

The consumer surface is intentionally DRF-like:

required: `Meta.model`

optional: `Meta.fields` as `"__all__"` or a list of field names

optional: `Meta.exclude` as a list of field names, mutually exclusive with `fields`

optional: `Meta.interfaces`, for example `(relay.Node,)`

optional: `Meta.name` to override the GraphQL type name

optional: `Meta.description`

The metaclass must reject unsupported future-surface keys for now. If a consumer declares `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, or `search_fields` before those specs ship, raise `ConfigurationError` rather than silently accepting noop config.

```python
# Minimal, scalars only
class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = "__all__"


# Full surface
class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category", "is_private")
        name = "Item"
        description = "A generated item produced from a Faker provider."
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return queryset.filter(is_private=False)
```

Deferred-key rejection — every line below raises `ConfigurationError` until the spec that owns the feature ships:

```python
class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = "__all__"
        filterset_class = CategoryFilter   # ConfigurationError: filterset_class is not supported yet
        orderset_class = CategoryOrder     # ConfigurationError
        aggregate_class = CategoryAggregate  # ConfigurationError
        fields_class = CategoryFieldSet    # ConfigurationError
        search_fields = ("name",)          # ConfigurationError
```

## Scalar field conversion

The converter layer should mirror graphene-django's coverage but emit Strawberry/Python-native types instead of graphene field instances.

`CharField`, `TextField`, `SlugField`, `EmailField`, `URLField` -> `str`

`IntegerField`, `SmallIntegerField`, `PositiveIntegerField` -> `int`

`BigIntegerField` -> custom `BigInt` scalar

`BooleanField` -> `bool`

`FloatField` -> `float`

`DecimalField` -> `decimal.Decimal`

`DateField` -> `datetime.date`

`DateTimeField` -> `datetime.datetime`

`TimeField` -> `datetime.time`

`DurationField` -> `datetime.timedelta`

`UUIDField` -> `uuid.UUID`

`JSONField` / `HStoreField` -> Strawberry JSON scalar

`BinaryField` -> `bytes`

`FileField` / `ImageField` -> `str` (URL/path)

`ArrayField` -> `list[inner_type]`

`null=True` maps to `T | None`.

Choice fields produce a generated strawberry `Enum` named `<TypeName><FieldName>Enum`. Those enums are cached in the registry keyed by `(model, field_name)` so multiple `DjangoType`s reading the same model field reuse the same enum.

```python
# django_strawberry_framework/converters.py — illustrative shape
import datetime
import decimal
import uuid
from typing import Any

from django.db import models

SCALAR_MAP: dict[type[models.Field], type] = {
    models.CharField: str,
    models.TextField: str,
    models.SlugField: str,
    models.EmailField: str,
    models.URLField: str,
    models.IntegerField: int,
    models.SmallIntegerField: int,
    models.PositiveIntegerField: int,
    models.BooleanField: bool,
    models.FloatField: float,
    models.DecimalField: decimal.Decimal,
    models.DateField: datetime.date,
    models.DateTimeField: datetime.datetime,
    models.TimeField: datetime.time,
    models.DurationField: datetime.timedelta,
    models.UUIDField: uuid.UUID,
    models.BinaryField: bytes,
    models.FileField: str,
    models.ImageField: str,
}


def convert_scalar(field: models.Field, type_name: str) -> Any:
    py_type: Any = SCALAR_MAP.get(type(field), Any)
    if field.choices:
        py_type = convert_choices_to_enum(field, type_name)
    if field.null:
        py_type = py_type | None
    return py_type
```

`type_name` is the consumer-facing `DjangoType` class name. It threads through from `__init_subclass__` so `convert_choices_to_enum` can build the spec-mandated `<TypeName><FieldName>Enum` name. `convert_choices_to_enum(field, type_name) -> type[Enum]` carries the same parameter; enum reuse is keyed on `(field.model, field.name)` in the registry, independent of `type_name`, so two `DjangoType`s pointing at the same choice column share the same enum even if their class names differ.

## Relation field conversion

Forward FK and OneToOne map to the target `DjangoType`, nullable iff the Django field is nullable.

Reverse FK and reverse OneToOne map to the target `DjangoType` or `list[target_type]` depending on cardinality.

Forward and reverse M2M map to `list[target_type]`.

If the target model's `DjangoType` has not yet been registered, use Strawberry forward references so definition order does not matter.

This spec intentionally keeps relation field resolution inside the type system rather than introducing a separate consumer-facing decorator API. Consumers should be able to write one `class CategoryType(DjangoType): class Meta: ...` and have relations appear automatically.

```python
# django_strawberry_framework/converters.py — relation half
from typing import Any

from django.db import models

from .registry import registry


def convert_relation(field: models.Field) -> Any:
    target_model = field.related_model
    target_ref = registry.lazy_ref(target_model)   # forward reference; resolved at schema build
    if field.many_to_many or field.one_to_many:
        return list[target_ref]
    if getattr(field, "null", False):
        return target_ref | None
    return target_ref
```

## Registry

A global registry maps model -> `DjangoType` and `(model, field_name)` -> generated enum. It exists so relation fields and enum conversion can look up already-built types. Registering the same model twice should raise `ConfigurationError` by default. The registry also needs a test-only `clear()` helper for isolation.

```python
# django_strawberry_framework/registry.py — illustrative shape
from enum import Enum
from typing import Any

from django.db import models

from .exceptions import ConfigurationError


class TypeRegistry:
    def __init__(self) -> None:
        self._types: dict[type[models.Model], type] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}

    def register(self, model: type[models.Model], type_cls: type) -> None:
        if model in self._types:
            raise ConfigurationError(
                f"{model.__name__} is already registered as {self._types[model].__name__}",
            )
        self._types[model] = type_cls

    def get(self, model: type[models.Model]) -> type | None:
        return self._types.get(model)

    def lazy_ref(self, model: type[models.Model]) -> Any:
        """Return a forward reference resolved at schema build."""

    def register_enum(
        self,
        model: type[models.Model],
        field_name: str,
        enum_cls: type[Enum],
    ) -> None:
        self._enums[(model, field_name)] = enum_cls

    def get_enum(
        self,
        model: type[models.Model],
        field_name: str,
    ) -> type[Enum] | None:
        return self._enums.get((model, field_name))

    def clear(self) -> None:
        """Test-only — drop all registered types and enums."""
        self._types.clear()
        self._enums.clear()


registry = TypeRegistry()
```

## `get_queryset`

`DjangoType` exposes `@classmethod get_queryset(cls, queryset, info, **kwargs)` with a default identity implementation. This is the single authoritative hook for permission scoping, multi-tenancy, soft-delete filtering, and any future consumer-side queryset constraints. The optimizer must respect it, especially on related fields.

```python
class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = "__all__"

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        if user and user.has_perm("products.view_item"):
            return queryset
        return queryset.filter(is_private=False)
```

`DjangoType` also exposes `has_custom_get_queryset() -> bool` (introspection helper) so the optimizer can detect when a type overrides the default identity implementation. The default implementation returns the queryset unchanged; any subclass override flips this flag to `True`.

## N+1 strategy

The first spec should not treat N+1 as a later enhancement; it is part of the foundation.

The package should ship a Strawberry schema extension named `DjangoOptimizerExtension`. Consumers opt in once at schema construction time. The extension inspects the selected field tree and optimizes the root queryset before evaluation.

Rules:

forward FK / OneToOne -> `select_related`

reverse FK / reverse OneToOne -> `prefetch_related`

M2M -> `prefetch_related`

selected scalar columns -> `only()`

The load-bearing edge case is custom `get_queryset` on the target type. strawberry-graphql-django hit this exact bug in issue #572 and fixed it in PR #583 by converting what would have been `select_related` into a `Prefetch(queryset=target_type.get_queryset(...))` when the target type defines a non-default `get_queryset`. This rule must be part of the first spec because otherwise FK joins bypass per-type visibility filtering and leak rows. We should copy the behaviour, not the decorator surface.

So the rule here is:

if a related field would normally use `select_related`, but the target `DjangoType` overrides `get_queryset`, downgrade that relation to `Prefetch` with the target type's filtered queryset.

That gives us the best part of strawberry-graphql-django's optimizer without adopting its decorator-first public API.

Schema-level opt-in:

```python
import strawberry

from django_strawberry_framework import DjangoOptimizerExtension

schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
```

The downgrade rule, in pseudocode:

```python
# django_strawberry_framework/optimizer.py — load-bearing rule
from django.db.models import Prefetch


def plan_relation(field, target_type, info):
    target_qs = field.related_model.objects.all()
    target_qs = target_type.get_queryset(target_qs, info)

    if field.many_to_many or field.one_to_many:
        return ("prefetch", Prefetch(field.name, queryset=target_qs))

    if target_type.has_custom_get_queryset():
        # would-be select_related downgrades to Prefetch so visibility filters apply
        return ("prefetch", Prefetch(field.name, queryset=target_qs))

    return ("select", field.name)
```

## Type naming

Default GraphQL type name is the consumer class's `__name__`, matching both graphene-django and Strawberry norms. Relay connection types and edges should follow the same naming family later, but this spec only needs the object-type naming rule and the choice-enum naming rule.

## What this enables immediately after implementation

Once this spec lands, the placeholder example schema in `examples/fakeshop/fakeshop/products/schema.py` can begin shedding its commented scaffold in favor of real `DjangoType` classes. The next spec can then focus narrowly on wiring `filterset_class` into the type and connection field, instead of having to re-solve model conversion and N+1 at the same time.

## Testing strategy

All new package tests go in a new root-level file, not `tests/base/`, because `tests/base/` is reserved for `conf.py` and version checking per AGENTS.md.

The new tests should verify:

Meta validation (`fields`/`exclude`, missing `model`, deferred-key rejection)

scalar field mapping on the fakeshop models

choice-field enum generation on a small test-only model fixture

registry behaviour

FK / reverse / M2M relation field generation

optimizer query counts on relation traversal

the `get_queryset` + optimizer downgrade rule using a hidden related row scenario in the example app

The example tests already exercise admin, services, commands, schema, urls, and models through real Django flows. Those stay as-is; this spec adds focused package tests around the new core types and optimizer.

```python
# tests/test_django_types.py — illustrative
import pytest
import strawberry

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from fakeshop.products import services
from fakeshop.products.models import Category, Item


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db
def test_meta_rejects_filterset_class():
    services.seed_data(1)
    with pytest.raises(ConfigurationError, match="filterset_class"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = "__all__"
                filterset_class = object


@pytest.mark.django_db
def test_optimizer_downgrades_to_prefetch_when_target_has_custom_get_queryset(
    django_assert_num_queries,
):
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return list(Category.objects.all())

    schema = strawberry.Schema(
        query=Query,
        extensions=[DjangoOptimizerExtension()],
    )

    with django_assert_num_queries(2):   # 1 categories, 1 prefetched filtered items
        result = schema.execute_sync("{ allCategories { id name items { id name } } }")
        assert result.errors is None
```

## Suggested implementation slices

Slice 1: scaffolding — `exceptions.py`, `registry.py`, `py.typed`, package re-exports, package logger.

Slice 2: `DjangoType` with scalar field conversion only, enough to map `Category`.

Slice 3: relation conversion for FK / reverse / M2M, still without optimization.

Slice 4: `DjangoOptimizerExtension` with `select_related` / `prefetch_related`.

Slice 5: `only()` optimization.

Slice 6: the `get_queryset` + downgrade-to-`Prefetch` rule.

Slice 7: choice-field enum generation and enum caching.

Each slice should land with tests in the same change so package coverage remains at 100%. Stub bodies between slices use `raise NotImplementedError(...)`; the existing `pyproject.toml` coverage config already lists that line in `exclude_lines`, so a partial scaffold does not break the gate as long as no test reaches the stubbed code path. When a later slice replaces a stub, it must also add the test that covers the new branch.

## Files to add

The seven slices add the following package modules and tests. File paths are relative to the repository root.

### Package source

- `django_strawberry_framework/exceptions.py` — `DjangoStrawberryFrameworkError` base class plus two subclasses: `ConfigurationError` (raised by Meta validation, registry collisions, and optimizer planning failures) and `OptimizerError` (raised when the optimizer cannot plan a relation traversal). The base class lets consumers catch the broad family in a single `except` while still distinguishing the specific causes downstream. No Django or Strawberry imports — keeps the exception hierarchy importable from anywhere in the package without circulars.
- `django_strawberry_framework/registry.py` — `TypeRegistry` class plus a module-level singleton `registry`. Holds `model -> DjangoType` and `(model, field_name) -> Enum`. Exposes `register`, `get`, `register_enum`, `get_enum`, `lazy_ref(model)` (forward references for definition-order independence), and `clear()` (test-only).
- `django_strawberry_framework/converters.py` — `SCALAR_MAP`, the `BigInt` scalar definition, `convert_scalar(field)`, `convert_choices_to_enum(model, field, type_name)`, and `convert_relation(field)`. All field-shape introspection lives here so `types.py` stays focused on Meta orchestration.
- `django_strawberry_framework/types.py` — `DjangoType` base class. Owns the `__init_subclass__` (or metaclass) pipeline that validates `Meta`, synthesizes annotations via `converters.py`, registers the resulting type with `registry`, and finalizes it via `@strawberry.type`. Defines the default `get_queryset` classmethod, the `has_custom_get_queryset()` introspection helper, and the deferred-key rejection list (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`).
- `django_strawberry_framework/optimizer.py` — `DjangoOptimizerExtension` (Strawberry `SchemaExtension`). Walks the resolved selection set, looks up each return type in `registry`, and applies `select_related` / `prefetch_related` / `only()` to the root queryset before evaluation. Implements the load-bearing downgrade rule: when a related field's target type defines a non-default `get_queryset`, generate a `Prefetch(...)` keyed on that filtered queryset instead of a `select_related`.
- `django_strawberry_framework/py.typed` — Empty PEP 561 marker so `mypy` and `pyright` consume our annotations from the installed wheel.
- `django_strawberry_framework/__init__.py` — Re-exports `DjangoType`, `DjangoOptimizerExtension`, and `auto` (pass-through of `strawberry.auto`). Keeps `__version__`. Exposes a package-level `logging.getLogger("django_strawberry_framework")` for the optimizer to emit downgrade decisions and other diagnostics.

### Tests

- `tests/test_django_types.py` — Meta validation (required `model`, `fields`/`exclude` mutual exclusivity, deferred-key rejection one assertion per key), scalar mapping against `Category`/`Item`/`Property`/`Entry`, relation generation (FK, reverse FK, M2M), registry behaviour (collision raises, `clear()` works), and the default `get_queryset` identity behaviour.
- `tests/test_optimizer.py` — Query-count assertions via `django_assert_num_queries` for plain FK/reverse/M2M traversal, `only()` projection, and the `get_queryset` + downgrade-to-`Prefetch` rule using `is_private` as the visibility filter on items hanging off categories.
- `tests/test_choice_enums.py` — Enum generation and caching. Because the fakeshop models do not declare `choices`, this test ships a small in-test model fixture (registered against an in-memory app config) so the choice-enum path is exercised without polluting the example schema.

`tests/base/` is not modified by this spec. No tests are added under `examples/fakeshop/.../tests/`.

### Files NOT in this spec

`fields.py`, `filters.py`, `orders.py`, `aggregates.py`, and `permissions.py` belong to later specs. The aspirational `examples/fakeshop/fakeshop/products/{filters,orders,aggregates,fields}.py` files exist already as design placeholders and stay aspirational until those specs ship. The aspirational `schema.py` block remains commented; uncommenting it is the responsibility of whichever later spec ships the last subsystem the example depends on.

Coordination note for whoever uncomments `schema.py`: the `search_fields = (...)` lines on each `*Node` are currently in the outer commented block, not the doubly-commented set. The deferred-key rule in this spec rejects `search_fields` on any `DjangoType.Meta` until the FilterSet spec ships. So before the outer block is uncommented, either move every `search_fields` line into the doubly-commented set (alongside `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`) or land FilterSet first — otherwise `__init_subclass__` will raise `ConfigurationError` on import.

## Open questions

Should the optimizer be opt-in via schema extensions or auto-attached whenever a `DjangoType` appears? Recommendation: opt-in, matching strawberry-graphql-django.

Should `id` auto-map to relay `GlobalID` behind a setting, similar to strawberry-graphql-django's `MAP_AUTO_ID_AS_GLOBAL_ID`? Recommendation: defer until relay support is implemented.

Do we want model-property optimization hints (`model_property`, `cached_model_property`) now? Recommendation: no; defer until the core optimizer exists.

## References

graphene-django Meta and registry foundation: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py:132-258`, `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/registry.py:1-42`

graphene-django field conversion coverage: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py:182-507`

strawberry-graphql-django type generation: `https://strawberry.rocks/docs/django/guide/types`

strawberry-graphql-django optimizer: `https://strawberry.rocks/docs/django/guide/optimizer`

strawberry-graphql-django custom-`get_queryset` / optimizer edge case: issue #572 and PR #583 on `strawberry-graphql/strawberry-django`
