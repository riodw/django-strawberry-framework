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

## Scope creep into the N+1 problem

This document is `spec-django_types.md`, so its strict scope is the type-generation foundation: the `DjangoType` base class, Meta options, scalar and relation field conversion, the registry, the `get_queryset` hook, choice-field enum generation, and type naming. Anything in this spec that addresses the runtime resolver-optimization problem is creep into N+1 territory that, in a stricter project layout, would live in its own document such as `spec-optimizer.md`.

The places this spec reaches into N+1 are concrete. The Goal sentence promises "relation resolution optimized by default" alongside type generation. The Proposed public surface lists `DjangoOptimizerExtension` as a top-level package name. The `## N+1 strategy` section is entirely optimizer territory, including the `select_related` / `prefetch_related` / `only()` rules and the `get_queryset` + `Prefetch` downgrade rule borrowed from strawberry-graphql-django PR #583. The `## get_queryset` section frames the hook as something "the optimizer must respect," which leaks the optimizer's existence into what would otherwise be a pure type-system primitive, and adds the `has_custom_get_queryset()` introspection helper that exists solely so the optimizer can detect overrides. Slices 4, 5, and 6 of the suggested implementation order are entirely optimizer work (extension scaffolding, `only()`, the `Prefetch` downgrade). The Testing strategy lists "optimizer query counts on relation traversal" and the visibility-leak scenario for the downgrade rule. One of the open questions and two of the references are about the optimizer rather than type generation.

Reason for the creep, and decision to keep it: an N+1 fix cannot be specced in isolation because the problem only exists once a type system resolves relations across the ORM graph, and the load-bearing `get_queryset` + `Prefetch` rule in particular is what makes per-type visibility filtering actually work across joins. Splitting the optimizer into its own follow-up spec would mean shipping a foundation that is broken-by-default until that follow-up lands. We chose to bundle one combined foundation here rather than two specs that depend on each other in lockstep.

If this document is ever split, the optimizer is the natural cut line. The seam is clean: `DjangoType` knows about `get_queryset` and exposes `has_custom_get_queryset()`; the optimizer is the only consumer of that introspection. Lifting Slices 4 through 6, the `## N+1 strategy` section, the `DjangoOptimizerExtension` public name, and the optimizer-shaped sentences in `## Goal` and `## get_queryset` into a `spec-optimizer.md` would leave a coherent type-generation-only document behind.

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

Subclasses without their own `Meta` are treated as abstract intermediates and pass through `__init_subclass__` untouched. This lets consumers layer shared scoping logic (tenant filtering, soft-delete, audit) into a base class that downstream concrete types inherit:

```python
class TenantScopedType(DjangoType):
    """Abstract intermediate — no Meta, just a shared get_queryset."""

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.filter(tenant=info.context.tenant)


class CategoryType(TenantScopedType):
    class Meta:
        model = Category
        fields = "__all__"
```

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

Field-selection defaults: when neither `fields` nor `exclude` is declared on `Meta`, the type behaves as if `fields = "__all__"` were set. This matches DRF's permissive default and avoids forcing every consumer to spell out `fields = "__all__"` for the common case. The deprecation warning graphene-django emits in this scenario is intentionally not reproduced here.

`Meta.interfaces` parking: the key is accepted by validation (it is in `ALLOWED_META_KEYS`) but not yet wired through `__init_subclass__`. Until a future slice injects declared interfaces into `cls.__bases__` before `strawberry.type` finalization, consumers wanting a Strawberry interface (e.g., `relay.Node`) should subclass it directly: `class CategoryType(DjangoType, relay.Node):`. The `Meta.interfaces` tuple still validates without raising; it just has no effect.

## Scalar field conversion

The converter layer should mirror graphene-django's coverage but emit Strawberry/Python-native types instead of graphene field instances.

`CharField`, `TextField`, `SlugField`, `EmailField`, `URLField`, `GenericIPAddressField` -> `str`

`FilePathField` -> `str` (filesystem path; semantically distinct from `FileField` but Strawberry-side it is just a string scalar)

`IntegerField`, `SmallIntegerField`, `PositiveIntegerField`, `PositiveSmallIntegerField`, `PositiveBigIntegerField` -> `int`

`AutoField`, `BigAutoField`, `SmallAutoField` -> `int` (Django primary-key column types; relay `GlobalID` remapping is the open question below)

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

The `BigInt` scalar serializes to a JSON string (not number) so values past `2**53` survive round-tripping through clients that lose precision on large numbers; inbound values parse via `int()`.

Choice fields are routed to a generated Strawberry `Enum` rather than to their raw scalar type. The naming rule, caching strategy, member-name sanitization, `TextChoices` / `IntegerChoices` support, `null=True` interaction, and test surface are pinned in "Choice field enum generation" below.

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
    models.GenericIPAddressField: str,
    models.FilePathField: str,
    models.IntegerField: int,
    models.SmallIntegerField: int,
    models.PositiveIntegerField: int,
    models.PositiveSmallIntegerField: int,
    models.PositiveBigIntegerField: int,
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
    py_type = SCALAR_MAP.get(type(field))
    if py_type is None:
        raise ConfigurationError(
            f"Unsupported Django field type {type(field).__name__!r} on "
            f"{field.model.__name__}.{field.name}. Add an entry to "
            "SCALAR_MAP or exclude this field via Meta.exclude.",
        )
    if field.choices:
        py_type = convert_choices_to_enum(field, type_name)
    if field.null:
        py_type = py_type | None
    return py_type
```

`type_name` is the consumer-facing `DjangoType` class name. It threads through from `__init_subclass__` so `convert_choices_to_enum` can build the spec-mandated `<TypeName><FieldName>Enum` name. `convert_choices_to_enum(field, type_name) -> type[Enum]` carries the same parameter; enum reuse is keyed on `(field.model, field.name)` in the registry, independent of `type_name`, so two `DjangoType`s pointing at the same choice column share the same enum even if their class names differ.

Deviation from earlier draft: the illustrative code originally fell back to `typing.Any` when `type(field)` was missing from `SCALAR_MAP`. Slice 2 instead raises `ConfigurationError` naming the offending field. The reasoning is that a silent `Any` fallback masks unsupported columns at schema-build time and surfaces them as opaque type errors much later (Strawberry has no native `Any` scalar mapping); `ConfigurationError` fails fast with the field path in the message and a one-line fix (extend `SCALAR_MAP` or add the field to `Meta.exclude`).

Slice 2 implementation subset: the converter above is the eventual end-state. Slice 2 implements the `SCALAR_MAP` lookup, the unsupported-type raise, and the `field.null` widening. The `if field.choices:` branch is deferred to Slice 7 (choice-field enum generation) so coverage stays at 100% without an unreached path. `type_name` is therefore unused in Slice 2 and is annotated as such; it is preserved in the signature so the Slice 7 change is purely additive.

Deferred scalar conversions: `BigIntegerField` -> custom `BigInt` scalar, `ArrayField` -> `list[inner_type]`, and `JSONField` / `HStoreField` -> Strawberry JSON scalar are all spec'd above but not implemented in Slice 2 because the fakeshop example models do not exercise them. They can be added without further design work as soon as a fakeshop model (or a real consumer) declares one. The TODO comments for each live in `django_strawberry_framework/converters.py` so they surface in code search.

## Choice field enum generation

Slice 7 routes Django choice columns through a generated Strawberry `Enum` instead of mapping them to their raw scalar type. This completes the scalar-conversion surface — it is the only branch `convert_scalar` deferred in Slice 2. The change consists of adding the `if field.choices:` branch to `convert_scalar` and implementing `convert_choices_to_enum`. With Slices 4 through 6 moved to `spec-optimizer.md`, Slice 7 is unblocked as soon as Slice 3 has shipped, and is the only remaining slice in this spec.

### Naming rule

The generated enum's GraphQL name is `f"{type_name}{PascalCase(field.name)}Enum"`:

- `type_name` is the consumer-facing `DjangoType` class name, threaded down from `__init_subclass__` into `convert_scalar`.
- `PascalCase(field.name)` converts a snake_case Django field name to PascalCase: `is_active` -> `IsActive`, `status` -> `Status`, `payment_method` -> `PaymentMethod`.

The first `DjangoType` to read a given `(model, field_name)` wins the name. Sibling `DjangoType`s pointing at the same column reuse the cached enum regardless of their own `type_name` — see "Caching and reuse" below.

### Algorithm

`convert_choices_to_enum(field, type_name) -> type[Enum]`:

1. Reject Django's grouped-choices form (a sequence of `(group_label, [...inner_pairs])` tuples) by raising `ConfigurationError`. The choices source must be a flat sequence of `(value, label)` pairs.
2. Check `registry.get_enum(field.model, field.name)`; if a cached enum exists, return it unchanged.
3. Compute `enum_name = f"{type_name}{PascalCase(field.name)}Enum"`.
4. Build the member mapping: for each `(value, label)` pair in `field.choices`, derive a member name by sanitizing the value — coerce non-string values to `str()` first (so `IntegerField` choices produce identifiers), replace non-identifier characters with `_`, then prefix with `MEMBER_` if the sanitized result starts with a digit.
5. Build `enum_cls = Enum(enum_name, members)` and decorate it with `strawberry.enum` so Strawberry recognizes it at schema build.
6. Cache via `registry.register_enum(field.model, field.name, enum_cls)`.
7. Return the enum class.

Sanitization runs on the value, not the label. graphene-django and strawberry-graphql-django sanitize labels (`"Active"` -> `ACTIVE`) because labels are human-readable phrases that round-trip cleanly to identifiers; values can be opaque (`"M"`, `"F"`, `1`, `2`) and produce uglier members (`M`, `F`, `MEMBER_1`, `MEMBER_2`). Slice 7 takes the value-based path because labels are display strings consumers may translate or restyle, and coupling the GraphQL schema to them is fragile — the `MEMBER_<digit>` prefix in step 4 is the explicit cost of this trade-off.

### Value semantics

The enum's value (from Python's `Enum` perspective) is the Django choice's first tuple element — the database value, unchanged. Round-tripping a choice through GraphQL reads the enum at the resolver boundary and returns the underlying database value to Django, so existing query filters (`Model.objects.filter(status="active")`) continue to work without translation.

### Django `TextChoices` / `IntegerChoices` support

Django's `models.TextChoices` and `models.IntegerChoices` (introduced in Django 3.0) expose a class-based choices API that ultimately resolves to the same flat `(value, label)` sequence on `field.choices`. Slice 7 supports both forms transparently — the iteration over `field.choices` treats them identically. The grouped-choices rejection only fires when a consumer manually constructs nested-tuple choices.

### Caching and reuse

The registry caches enums on `(field.model, field.name)`, deliberately independent of `type_name`. Two `DjangoType`s reading the same column share the same enum object:

```python
class ItemTypeA(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "status")


class ItemTypeB(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "status")


# Both types share the same generated enum:
assert ItemTypeA.__annotations__["status"] is ItemTypeB.__annotations__["status"]
```

The first type defined wins the enum's name (`ItemTypeAStatusEnum`), even when later types share it. The enum name is for schema introspection only; the runtime behaviour is identical regardless of which type registered it first.

This is intentional, but it leaves the published schema name dependent on Python import order — the trap class-based naming was meant to avoid. Consumers who want a stable, predictable name should declare the `DjangoType` they want to win first (or, eventually, override via a `Meta.choice_enum_names` mapping once such a key exists).

### `null=True` interaction

A nullable choice field widens to `EnumType | None`, matching the general scalar-nullability rule. The order inside `convert_scalar` is: scalar lookup -> choices branch (replaces `py_type` with the enum) -> `null` widening. So `CharField(choices=[...], null=True)` produces `<GeneratedEnum> | None`.

### Test surface

`tests/test_choice_enums.py` ships a session-scoped `pytest` fixture that defines an in-test `ChoiceFixture` Django model with a `TextField(choices=[...])` column, registers it via `django.apps.apps.register_model` under a synthetic `app_label`, and tears down on completion. Fakeshop has no choice columns, so the fixture is the only path that exercises this slice.

Required tests:

- `test_choice_field_generates_strawberry_enum` — a `DjangoType` over the fixture model produces an enum-typed annotation on the choice attribute, named per the rule above.
- `test_choice_enum_cached_in_registry_keyed_by_model_field` — `registry.get_enum(ChoiceFixture, "status")` returns the generated enum after the first build and is identical across subsequent retrievals.
- `test_two_djangotypes_reading_same_choice_field_share_one_enum` — defining two `DjangoType`s over `ChoiceFixture` yields the same enum object on both annotations.
- `test_grouped_choices_form_rejected` — declaring grouped choices on the fixture model and constructing a `DjangoType` over it raises `ConfigurationError`.
- `test_choice_member_name_sanitization` — choice values like `"first-name"` and `"123abc"` produce identifier-safe member names.
- `test_choice_field_with_null_widens_to_enum_or_none` — a nullable choice column produces exactly `EnumType | None`. Pin the union shape (not `EnumType | None | None` or other widened variants) so a future ordering bug in `convert_scalar` surfaces immediately.

## Relation field conversion

Cardinality table:

- Forward FK (`many_to_one`) -> target type, nullable iff `field.null`.
- Forward OneToOne (`one_to_one`) -> target type, nullable iff `field.null`.
- Reverse FK (`one_to_many` on the related descriptor) -> `list[target_type]` (always non-nullable; empty list when no rows exist).
- Reverse OneToOne (`one_to_one` on the related descriptor) -> target type or `None` (always conceptually nullable).
- Forward / reverse M2M (`many_to_many`) -> `list[target_type]`.

Reverse-side `null` is not meaningful at the schema level; the cardinality flag is the authority.

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

Slice 2 -> Slice 3 hand-off: `_build_annotations` in Slice 2 filters relations out entirely (`[f for f in model._meta.get_fields() if not f.is_relation]`) so a model with FKs or reverse rels can be partially mapped (scalars only) without the unimplemented `convert_relation` raising. Slice 3 must flip that filter: every field goes through dispatch, with relations routed to `convert_relation` and scalars to `convert_scalar`. Once that change lands, `Meta.fields = "__all__"` will include relations on Category (`items`, `properties`), Item (`category`, `entries`), Property (`category`), and Entry (`property`, `item`). The `tests/test_django_types.py` placeholders for `test_relation_fk_to_target_djangotype`, `test_relation_reverse_fk_returns_list`, `test_relation_m2m_returns_list`, and `test_forward_reference_resolves_when_target_defined_later` already mark the test surface Slice 3 must fill in.

Slice 3 status (post-implementation): Slice 3 shipped eager-only relation resolution. `convert_relation` looks up the target via `registry.get(field.related_model)` and raises `ConfigurationError` (with a message naming the unregistered model) if the target is not yet declared. `registry.lazy_ref` therefore stays as `NotImplementedError`; the spec's promise of definition-order independence is deferred to a future slice. The practical implication: consumers must declare related `DjangoType`s in dependency order — declare a target type before any type that references it via FK / OneToOne / M2M, or before any type whose model surfaces it via a reverse rel. The fakeshop dependency order is `CategoryType -> (PropertyType, ItemType) -> EntryType`. M2M handling is implemented in `convert_relation` (the `field.many_to_many` branch shares the same line as `field.one_to_many`, so line coverage holds), but no fakeshop model declares an M2M field, so the dedicated test placeholder stays skipped.

## Registry

A global registry maps model -> `DjangoType` and `(model, field_name)` -> generated enum. It exists so relation fields and enum conversion can look up already-built types. Registering the same model twice should raise `ConfigurationError` by default. The registry also needs a test-only `clear()` helper for isolation.

The registry also exposes `lazy_ref(model)`, used by relation conversion when the target type may not yet be registered. Slice 3 picks one of:

- `Annotated["TargetType", strawberry.lazy("module.path")]` for cross-module references, resolved at schema-build time via a named import.
- A string annotation (`"TargetType"`) that `_build_annotations` rewrites once all sibling types are registered. Simplest for same-module references.
- A registry-tracked "pending relation" that `DjangoType.__init_subclass__` post-processes after every subclass has been seen.

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

`spec-optimizer.md` O6 implementation (sentinel flip): the introspection is wired in two places. First, `DjangoType` carries a class-var `_is_default_get_queryset: ClassVar[bool] = True` (already in place since Slice 1's scaffolding). Second, O6 adds a single line to `__init_subclass__` after the strawberry.type call: `if "get_queryset" in cls.__dict__: cls._is_default_get_queryset = False`. This shadows the base class's `True` with a subclass-local `False` whenever the consumer declares their own `get_queryset`. `has_custom_get_queryset` then becomes `return not cls._is_default_get_queryset` — a constant-time attribute read, called once per relation per resolver call by the optimizer.

## N+1 strategy

The first spec should not treat N+1 as a later enhancement; it is part of the foundation.

The package should ship a Strawberry schema extension named `DjangoOptimizerExtension`. Consumers opt in once at schema construction time. The extension wraps each resolver via Strawberry's `resolve` / `aresolve` hooks: when a resolver returns a `QuerySet`, the extension reads `info.selected_fields` to determine which related fields and scalars are selected, looks up each return type in the registry, and lifts the queryset into an optimized one before passing it back to Strawberry's evaluation machinery. Resolvers that return non-`QuerySet` values (mutations, scalars, computed fields, plain lists) pass through unchanged.

Rules:

forward FK / OneToOne -> `select_related`

reverse FK / reverse OneToOne -> `prefetch_related`

M2M -> `prefetch_related`

selected scalar columns -> `only()`

The load-bearing edge case is custom `get_queryset` on the target type. strawberry-graphql-django hit this exact bug in issue #572 and fixed it in PR #583 by converting what would have been `select_related` into a `Prefetch(queryset=target_type.get_queryset(...))` when the target type defines a non-default `get_queryset`. This rule must be part of the first spec because otherwise FK joins bypass per-type visibility filtering and leak rows. We should copy the behaviour, not the decorator surface.

So the rule here is:

if a related field would normally use `select_related`, but the target `DjangoType` overrides `get_queryset`, downgrade that relation to `Prefetch` with the target type's filtered queryset.

That gives us the best part of strawberry-graphql-django's optimizer without adopting its decorator-first public API.

Resolver-to-type tracing (Slice 4): the extension reads each resolver's GraphQL return type via `info.return_type` (Strawberry's per-call return-type metadata). The return type is the consumer's `DjangoType` subclass directly, so the extension pulls `__strawberry_definition__` off it, finds the matching Django model by reverse-walking the registry's `_types` dict, and uses that model to walk `info.selected_fields[0].selections` against `model._meta.get_fields()`. Resolvers that return non-`QuerySet` values (mutations, scalars, computed fields, plain lists) skip the optimizer entirely — the `isinstance(result, QuerySet)` check in the resolve hook guards the path.

`only()` and FK columns (`spec-optimizer.md` O5): when `only()` is applied alongside `select_related`, it must include both the local FK column (e.g. `category_id`) and the joined columns (e.g. `category__id`, `category__name`) for every relation under traversal. Without those, Django marks the joined attributes as deferred and triggers an extra query the moment the resolver accesses them — a silent N+1 that the optimizer was supposed to prevent. strawberry-graphql-django's optimizer documentation calls this out explicitly; we copy the rule. The O5 implementation walks the cardinality plan emitted by the O2 walker and unions the FK columns into the only() set before applying.

`plan_relation` integration (`spec-optimizer.md` O6): the simple Slice 4 cardinality rule (`forward FK / OneToOne -> select_related`) is replaced by a call to `plan_relation(field, target_type, info)`, which returns either `("select", field_name)` for a plain join or `("prefetch", Prefetch(...))` for the visibility-aware downgrade. The select/prefetch loop iterates the planning results rather than the raw cardinality flags. Every plan_relation call also runs `target_type.get_queryset(target_qs, info)` to apply the consumer's visibility filter to the prefetched queryset, so visibility filtering applies regardless of which plan branch fires.

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

Slice 1: scaffolding — `exceptions.py`, `registry.py`, `py.typed`, package re-exports, package logger. Status: shipped.

Slice 2: `DjangoType` with scalar field conversion only, enough to map `Category`. Status: shipped (v0.0.2 prerelease).

Slice 3: relation conversion for FK / reverse / M2M, still without optimization. Status: shipped (eager-only resolution; `lazy_ref` deferred — see Post-slice-7 future work).

Slice 4: `DjangoOptimizerExtension` with `select_related` / `prefetch_related`. Status: shipped as a partial / depth-1-only implementation, then **superseded by `spec-optimizer.md`**. Running the slice's tests surfaced two architectural issues (Strawberry's default resolver chokes on `RelatedManager` for reverse rels; per-resolver hooks cannot emit nested `prefetch_related("items__entries")` chains) that warranted a dedicated optimizer spec. The shipped code (`DjangoOptimizerExtension`, `_optimize`, `_plan`, `_unwrap_return_type`, `_snake_case`, `registry.model_for_type`) stays in tree as the starting point. The rebuild splits across `spec-optimizer.md` slices: O1 lands custom relation-field resolvers in `DjangoType.__init_subclass__` (a separate seam in `types.py`, not a refactor of optimizer code); O2 promotes `_plan` to a pure walker module; O3 swaps the `resolve` / `aresolve` hooks for `on_executing_start`. O4-O6 then layer nested prefetch, `only()`, and the `Prefetch` downgrade onto the rebuilt architecture.

Slice 5: `only()` optimization. **Moved to `spec-optimizer.md` Slice O5** — the `only()` column list and the FK-column inclusion rule both depend on the selection-tree walker introduced in O2, so they cannot land before that walker exists.

Slice 6: the `get_queryset` + downgrade-to-`Prefetch` rule. **Moved to `spec-optimizer.md` Slice O6.** The `_is_default_get_queryset` sentinel on `DjangoType` and the `has_custom_get_queryset()` introspection helper still live in this spec (they are type-system surface). The `__init_subclass__` flip that toggles the sentinel and the `plan_relation`-style downgrade itself move to the optimizer spec because the optimizer is the only consumer.

Slice 7: choice-field enum generation and enum caching. Adds the `if field.choices:` branch to `convert_scalar` (Slice 2 deferred it) plus the `convert_choices_to_enum` body. Status: shipped. With Slices 4 through 6 moved to `spec-optimizer.md`, Slice 7 was the only remaining slice in this spec and landed once Slice 3 had shipped. See the "Choice field enum generation" section above for the full design — naming rule, member-name sanitization, `TextChoices` / `IntegerChoices` support, caching semantics, `null=True` interaction, and test surface.

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
- `tests/test_choice_enums.py` — Enum generation and caching. Because the fakeshop models do not declare `choices`, this test ships a session-scoped `pytest` fixture that defines an in-test `ChoiceFixture` model with a synthetic `app_label`, registers it via `django.apps.apps.register_model` for the session's lifetime, and tears down on completion. The choice-enum path is exercised without polluting the example schema, and slice 7 reuses the same fixture for the cross-type enum-reuse test.

`tests/base/` is not modified by this spec. No tests are added under `examples/fakeshop/.../tests/`.

### Files NOT in this spec

`fields.py`, `filters.py`, `orders.py`, `aggregates.py`, and `permissions.py` belong to later specs. The aspirational `examples/fakeshop/fakeshop/products/{filters,orders,aggregates,fields}.py` files exist already as design placeholders and stay aspirational until those specs ship. The aspirational `schema.py` block remains commented; uncommenting it is the responsibility of whichever later spec ships the last subsystem the example depends on.

Coordination note for whoever uncomments `schema.py`: the `search_fields = (...)` lines on each `*Node` are currently in the outer commented block, not the doubly-commented set. The deferred-key rule in this spec rejects `search_fields` on any `DjangoType.Meta` until the FilterSet spec ships. So before the outer block is uncommented, either move every `search_fields` line into the doubly-commented set (alongside `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`) or land FilterSet first — otherwise `__init_subclass__` will raise `ConfigurationError` on import.

## Post-slice-7 future work

Items the spec called for but are deferred past Slice 7 because the foundation can ship without them. Each is tracked as a TODO in the relevant module so a code search surfaces them.

`registry.lazy_ref` and definition-order independence: Slice 3 shipped eager-only relation lookup, leaving `lazy_ref` as `NotImplementedError`. Lifting the dependency-order constraint requires one of three approaches documented in `lazy_ref`'s docstring (string-annotation rewriting after every sibling registers; a `strawberry.lazy`-backed wrapper that resolves through the registry at schema-build time; or a deferred-`strawberry.type` pass invoked by a `finalize_types()` call). The choice point and test surface are captured by the `test_forward_reference_resolves_when_target_defined_later` placeholder.

`Meta.interfaces` wiring: Slice 2 accepted the key in `ALLOWED_META_KEYS` but never injects declared interfaces into `cls.__bases__` before `strawberry.type` finalizes. Consumers wanting a Strawberry interface (typically `relay.Node`) subclass it directly until this lands.

Scalar-conversion deferrals: `BigInt` scalar (for plain `BigIntegerField`), `ArrayField -> list[inner_type]`, and `JSONField` / `HStoreField -> JSON` are all spec'd in the Scalar field conversion section but not implemented because no fakeshop model exercises them. Each has a `TODO(future)` comment in `django_strawberry_framework/converters.py`.

M2M relation tests: `convert_relation` already handles `many_to_many` (it shares the many-side branch with `one_to_many`, so line coverage holds), but no fakeshop model declares an M2M field, so the dedicated `test_relation_m2m_returns_list` placeholder stays skipped. Adding M2M to a fakeshop model or seeding `User.groups` for a sibling test fills this gap.

Relay `GlobalID` for primary keys: the open question about `MAP_AUTO_ID_AS_GLOBAL_ID`-style remapping resolves once a relay-support spec lands. Until then, `AutoField` / `BigAutoField` / `SmallAutoField` map to `int`.

Example schema uncomment: `examples/fakeshop/fakeshop/products/schema.py` is still a commented-out aspirational design (see the coordination note in the previous section). Slices 4 through 7 do not require it to come uncommented; the package and its tests work without the example schema being wired. Whichever spec ships the last subsystem the example depends on is responsible for the uncomment + the matching `urls.py` change.

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
