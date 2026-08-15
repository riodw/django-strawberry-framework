# Spec: DjangoType Foundation

## Problem statement

`django-strawberry-framework` needs a first load-bearing primitive that both graphene-django and strawberry-graphql-django already provide: a way to turn a Django model into a GraphQL type. In this package that primitive must be DRF-shaped, meaning configuration lives in a nested `Meta` class, not in stacked decorators. This same primitive must also solve the most common GraphQL performance failure mode — N+1 relation queries — because every later subsystem ([`FilterSet`][glossary-filterset], [`OrderSet`][glossary-orderset], [`AggregateSet`][glossary-aggregateset], permissions, connection fields) will sit on top of it.

## Prior art

The example project this spec is driven by is `examples/fakeshop/`: the `Category`, `Item`, `Property`, and `Entry` models in `examples/fakeshop/apps/products/models.py`, with seed helpers in the sibling `services.py` and package tests under `tests/`.

graphene-django's overlapping foundation is `DjangoObjectType` plus the model/type registry and the field converter layer — `graphene_django/types.py::DjangoObjectType`, `graphene_django/registry.py::Registry`, and `graphene_django/converter.py::convert_django_field` (see "References" for the checkout this package reads them from). That gives us the core Meta options, the model registry, scalar field conversion, enum-from-choices, Relay node support, and relation-field generation.

strawberry-graphql-django's overlapping foundation is `@strawberry_django.type(...)`, `StrawberryDjangoField`, and its own optimizer extension, documented at `https://strawberry.rocks/docs/django/guide/types` and `https://strawberry.rocks/docs/django/guide/optimizer` and implemented in `strawberry_django/type.py` / `strawberry_django/fields/field.py`. That gives us the modern parts graphene-django lacks: automatic `select_related` / `prefetch_related` / column-projection optimization, field-level optimization hints, and a clean integration with Strawberry's type system.

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

Add a [`DjangoType`][glossary-djangotype] base class and a `DjangoOptimizerExtension` so that consumers can declare a Strawberry GraphQL type from a Django model using a DRF-shaped `Meta` class and have relation resolution optimized by default.

## Non-goals

This spec does not implement `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, [`DjangoConnectionField`][glossary-djangoconnectionfield], [`apply_cascade_permissions`][glossary-apply-cascade-permissions], [per-field permission hooks][glossary-per-field-permission-hooks], mutations, polymorphic interfaces, or the full relay connection story. Those follow later. The first spec only creates the foundation that later specs can attach to.

Deliberation for this spec lives in its companion [rationale file][spec-001-rationale]: the alternatives each decision rejected and why each lost, the argument that produced this combined type-generation-plus-optimizer scope, the per-slice implementation history, the post-Slice-7 deferral list, and the open questions this spec carried. Its second half is the reconciliation record — for every section below whose contract now reads differently than it first did, why it changed, which claim the package falsified, which alternative correction was rejected, and which claims this spec is no longer permitted to make. Read the spec for what holds; read that file for why it holds.

## Proposed public surface

This spec adds three public names at the package root:

`DjangoType`

`DjangoOptimizerExtension`

`auto` (re-exported from `strawberry`)

It also adds internal support modules — `registry.py`, `exceptions.py`, the converter layer at `types/converters.py`, and a `py.typed` marker — plus the package-level logger. Every later public name in this package (`finalize_django_types`, the connection and relay fields, the mutation family, the filter and order sidecars) belongs to the spec that shipped it, not to this one.

The `auto` re-export is a pass-through of `strawberry.auto` so consumers can annotate fields inside a `DjangoType` without a separate `import strawberry`.

```python
from django_strawberry_framework import DjangoType, DjangoOptimizerExtension, auto
from django_strawberry_framework.exceptions import ConfigurationError
```

## `DjangoType`

`DjangoType` is a base class with an `__init_subclass__` pipeline that reads a nested `Meta` class, synthesizes Strawberry annotations from the Django model, and registers the resulting type for later relation lookup. Collection is separate from finalization: subclass creation collects, and a later `finalize_django_types()` pass resolves the recorded relation targets and applies `strawberry.type` to every collected class. `spec-010-foundation-0_0_4.md` owns that pass; this spec owns what subclass creation collects.

The consumer surface is intentionally DRF-like:

required: [`Meta.model`][glossary-metamodel]

optional: [`Meta.fields`][glossary-metafields] as `"__all__"` or a list of field names

optional: [`Meta.exclude`][glossary-metaexclude] as a list of field names, mutually exclusive with `fields`

optional: [`Meta.interfaces`][glossary-metainterfaces], for example `(relay.Node,)`

optional: [`Meta.name`][glossary-metaname] to override the GraphQL type name

optional: [`Meta.description`][glossary-metadescription]

Subclasses without their own `Meta` are treated as abstract intermediates: nothing is validated, selected, or registered for them. This lets consumers layer shared scoping logic (tenant filtering, soft-delete, audit) into a base class that downstream concrete types inherit. The one thing such a base does carry away is the `get_queryset` sentinel, stamped ahead of the `Meta`-absent early return so a scoping base is visible to the optimizer through its concrete subclasses — see "`get_queryset`" below.

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

`Meta` validation must reject a future-surface key rather than silently accept noop config: a key naming a feature whose spec has not shipped raises [`ConfigurationError`][glossary-configurationerror], and so does any key in neither the allowed nor the deferred set (the typo guard). The two sets are `django_strawberry_framework/types/base.py::ALLOWED_META_KEYS` and `::DEFERRED_META_KEYS`, and a key moves from deferred to allowed in the change that ships its feature — `filterset_class` and `orderset_class` made that move at `0.0.8`, leaving `aggregate_class`, `fields_class`, and `search_fields` deferred.

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
        aggregate_class = CategoryAggregate  # ConfigurationError: aggregate_class is not supported yet
        fields_class = CategoryFieldSet      # ConfigurationError
        search_fields = ("name",)            # ConfigurationError
```

Field-selection defaults: when neither `fields` nor `exclude` is declared on `Meta`, the type behaves as if `fields = "__all__"` were set. This matches DRF's permissive default and avoids forcing every consumer to spell out `fields = "__all__"` for the common case. The deprecation warning graphene-django emits in this scenario is intentionally not reproduced here.

`Meta.interfaces` is validated at subclass creation and applied at finalization: `django_strawberry_framework/types/relay.py::apply_interfaces` injects the declared interfaces into `cls.__bases__` before `strawberry.type` runs. Direct subclassing (`class CategoryType(DjangoType, relay.Node):`) stays an equivalent spelling — both forms are recognized by the same Relay-shape predicate — so a consumer may use either. Declaring `relay.Node` by either route makes the type Relay-Node-shaped, which suppresses the synthesized primary-key annotation in favour of the interface's `id: GlobalID!`; that contract is [Relay Node integration][glossary-relay-node-integration], owned by `spec-015-relay_interfaces-0_0_5.md`.

## [Scalar field conversion][glossary-scalar-field-conversion]

The converter layer mirrors graphene-django's coverage but emits Strawberry/Python-native types instead of graphene field instances. The map itself is `django_strawberry_framework/types/converters.py::SCALAR_MAP`, and `::scalar_for_field` is the single lookup shared by field conversion and filter-input conversion, so a column resolves to the same scalar on both sides.

`CharField`, `TextField`, `SlugField`, `EmailField`, `URLField`, `GenericIPAddressField` -> `str`

`FilePathField` -> `str` (filesystem path; semantically distinct from `FileField` but Strawberry-side it is just a string scalar)

`IntegerField`, `SmallIntegerField`, `PositiveIntegerField`, `PositiveSmallIntegerField` -> `int`

`AutoField`, `BigAutoField`, `SmallAutoField` -> `int` (Django primary-key column types). On a Relay-Node-shaped type the synthesized primary-key annotation is suppressed and the `relay.Node` interface supplies `id: GlobalID!` instead; the pk column stays selected as an optimizer connector column. The `GlobalID` payload is governed by `Meta.globalid_strategy` / the `RELAY_GLOBALID_STRATEGY` setting, owned by `spec-031-globalid_encoding-0_0_9.md`.

`BigIntegerField`, `PositiveBigIntegerField` -> custom [`BigInt`][glossary-bigint-scalar] scalar

`BooleanField` -> `bool`

`FloatField` -> `float`

`DecimalField` -> `decimal.Decimal`

`DateField` -> `datetime.date`

`DateTimeField` -> `datetime.datetime`

`TimeField` -> `datetime.time`

`UUIDField` -> `uuid.UUID`

`JSONField` / `HStoreField` -> Strawberry JSON scalar

`ArrayField` -> `list[inner_type]`

`FileField` / `ImageField` -> a structured `DjangoFileType` / `DjangoImageType` read-output object, nullable by default. That mapping lives in a separate `FIELD_OUTPUT_TYPE_MAP` kept deliberately off `SCALAR_MAP`, so the filter / scalar-input shape for a file column stays `str` and no output object can reach a GraphQL input; the split is owned by `spec-037-upload_file_image_mapping-0_0_11.md`.

`DurationField` and `BinaryField` are deliberately absent from the default map: Strawberry ships no first-party scalar for `datetime.timedelta` or `bytes`, so both raise the unsupported-field-type `ConfigurationError` below until a consumer registers one (`SCALAR_MAP[BinaryField] = strawberry.scalars.Base64` is the conventional plug). Registering an entry is the non-subclass extension hook; subclassing a supported Django field needs no registration at all, because the lookup walks `type(field).__mro__`.

`null=True` maps to `T | None`.

The `BigInt` scalar serializes to a JSON string (not number) so values past `2**53` survive round-tripping through clients that lose precision on large numbers; inbound values parse via `int()`.

Choice fields are routed to a generated Strawberry `Enum` rather than to their raw scalar type. The naming rule, caching strategy, member-name sanitization, `TextChoices` / `IntegerChoices` support, `null=True` interaction, and test surface are pinned in "Choice field enum generation" below.

`type_name` is the consumer-facing `DjangoType` class name. It threads through from `__init_subclass__` so `convert_choices_to_enum` can build the spec-mandated `<TypeName><FieldName>Enum` name. `convert_choices_to_enum(field, type_name) -> type[Enum]` carries the same parameter; enum reuse is keyed on `(field.model, field.name)` in the registry, independent of `type_name`, so two `DjangoType`s pointing at the same choice column share the same enum even if their class names differ.

A field type missing from `SCALAR_MAP` must raise `ConfigurationError` naming the offending field, never fall back to `typing.Any`: a silent `Any` fallback masks unsupported columns at schema-build time and surfaces them as opaque type errors much later (Strawberry has no native `Any` scalar mapping), while the raise fails fast with the field path in the message and a one-line fix (extend `SCALAR_MAP` or add the field to `Meta.exclude`).

The rejected `typing.Any` fallback and the slice-by-slice deferral order for this section are recorded in the [rationale file][spec-001-rationale].

## Choice field enum generation

Django choice columns route through a generated Strawberry `Enum` instead of mapping to their raw scalar type. This completes the scalar-conversion surface: the `if field.choices:` branch in `convert_scalar` plus the `convert_choices_to_enum` body.

### Naming rule

The generated enum's GraphQL name is `f"{type_name}{PascalCase(field.name)}Enum"`:

- `type_name` is the consumer-facing `DjangoType` class name, threaded down from `__init_subclass__` through `convert_field_output` into `convert_scalar`.
- `PascalCase(field.name)` converts a snake_case Django field name to PascalCase: `is_active` -> `IsActive`, `status` -> `Status`, `payment_method` -> `PaymentMethod`.

The first `DjangoType` to read a given `(model, field_name)` wins the name. Sibling `DjangoType`s pointing at the same column reuse the cached enum regardless of their own `type_name` — see "Caching and reuse" below.

### Algorithm

`django_strawberry_framework/types/converters.py::convert_choices_to_enum`, signature `(field, type_name) -> type[Enum]`:

1. Check `registry.get_enum(field.model, field.name)`; if a cached enum exists, return it unchanged. The cache check comes first so a cached column never re-derives a name or re-runs the rejections.
2. Compute `enum_name = f"{type_name}{PascalCase(field.name)}Enum"`.
3. Delegate the build to `::build_enum_from_choices`, which owns every rule below.
4. Cache via `registry.register_enum(field.model, field.name, enum_cls)` and return the enum class.

`build_enum_from_choices(choice_pairs, enum_name, *, source_label)` is the shared core, and it is shared on purpose: the DRF serializer `ChoiceField` / `MultipleChoiceField` path (`django_strawberry_framework/rest_framework/serializer_converter.py`) builds its enums through the same function, so the rejections and the sanitization rules cannot drift between the two flavors. `source_label` names the offending field in every raised message — `"Model.field"` on the read side, the serializer field name on the other — so both callers share one message shape. The two key spaces stay separate: the read side keys the cache on `(model, field_name)`, the serializer side on the descriptor-derived enum name.

Three rejections, all `ConfigurationError`:

- **Empty choices.** A field declaring `choices` with an empty sequence has no members to build.
- **Django's grouped-choices form** (a sequence of `(group_label, [...inner_pairs])` tuples). The choices source must be a flat sequence of `(value, label)` pairs. Detection reads the *label* slot for a list / tuple, not the value slot: in the grouped form the value slot holds the human-readable group name, so testing it would false-negative.
- **Two choice values that sanitize to the same member name.** The message names the colliding member and every value that produced it.

Member names are sanitized from the choice value, in this order: coerce to `str()` (so `IntegerChoices` produce identifiers); rewrite ASCII non-identifier characters to `_`; prefix `MEMBER_` when the result is empty or starts with a digit; prefix `_` when the result is a Python keyword; prefix `MEMBER_` when the result is a GraphQL-reserved enum value (`true` / `false` / `null`), starts with `__`, or is a name Python's `enum` reserves (`mro`, a `_sunder_` name, or the generated class's private `_<EnumName>__` namespace). The order is load-bearing: folding the keyword and reserved rewrites into one condition changes which values the collision rejection above reports.

Sanitization runs on the value, not the label. Labels are display strings consumers may translate or restyle, and coupling the GraphQL schema to them is fragile; the `MEMBER_<digit>` prefix is the explicit cost of that choice. The rejected label-based alternative is in the [rationale file][spec-001-rationale].

### Value semantics

The enum's value (from Python's `Enum` perspective) is the Django choice's first tuple element — the database value, unchanged. Round-tripping a choice through GraphQL reads the enum at the resolver boundary and returns the underlying database value to Django, so existing query filters (`Model.objects.filter(status="active")`) continue to work without translation.

### Django `TextChoices` / `IntegerChoices` support

Django's `models.TextChoices` and `models.IntegerChoices` (introduced in Django 3.0) expose a class-based choices API that ultimately resolves to the same flat `(value, label)` sequence on `field.choices`. Both forms are supported transparently — the iteration over `field.choices` treats them identically. The grouped-choices rejection only fires when a consumer manually constructs nested-tuple choices.

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

This is intentional, but it leaves the published schema name dependent on Python import order — the trap class-based naming was meant to avoid. Consumers who want a stable, predictable name should declare the `DjangoType` they want to win first (or, eventually, override via a [`Meta.choice_enum_names`][glossary-metachoice-enum-names] mapping once such a key exists).

### `null=True` interaction

A nullable choice field widens to `EnumType | None`, matching the general scalar-nullability rule. The order inside `convert_scalar` is: scalar lookup -> choices branch (replaces `py_type` with the enum) -> `null` widening. So `CharField(choices=[...], null=True)` produces `<GeneratedEnum> | None`.

### Test surface

`tests/types/test_converters.py` ships a session-scoped `pytest` fixture that defines an in-test `ChoiceFixture` Django model with `TextField(choices=[...])` columns (one non-null, one nullable) under a synthetic `app_label`. Declaring the synthetic `app_label` on the fixture model's own `Meta` is what registers it; no explicit `django.apps.apps.register_model` call is involved, and nothing is torn down from Django's app registry — an autouse `registry.clear()` fixture supplies the isolation instead. The products example has no choice columns, so the fixture is the only path that exercises choice-field enum generation.

Required tests, all in `tests/types/test_converters.py`:

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

A relation whose target `DjangoType` is not registered yet is not an error and does not force a declaration order on the consumer: subclass creation records it as a pending relation (`django_strawberry_framework/types/relations.py::PendingRelation`) behind a placeholder annotation, and the later `finalize_django_types()` pass resolves every recorded target and writes the concrete annotation, so that [definition order does not matter][glossary-definition-order-independence]. A consumer who writes the relation's annotation themselves — a same-module string annotation, or a `from __future__ import annotations` stringification — keeps it: `django_strawberry_framework/types/base.py::_build_annotations` skips relation deferral for any consumer-authored field name, so the annotation is left untouched and Strawberry resolves the reference. A target that is still unresolvable when finalization runs fails there, with a message naming the source model, the source field, and the target model.

This spec intentionally keeps relation field resolution inside the type system rather than introducing a separate consumer-facing decorator API. Consumers should be able to write one `class CategoryType(DjangoType): class Meta: ...` and have relations appear automatically.

Every field goes through dispatch in `django_strawberry_framework/types/base.py::_build_annotations`: a relation becomes a `PendingRelation` record plus a placeholder annotation, and every other column is converted through `types/converters.py::convert_field_output`. The concrete relation annotation is rendered at finalization by `types/converters.py::resolved_relation_annotation`, which reads cardinality and nullability off the shared `FieldMeta` descriptor rather than re-deriving them. Under `Meta.fields = "__all__"` the products example surfaces relations on Category (`items`, `properties`), Item (`category`, `entries`), Property (`category`, `entries`), and Entry (`property`, `item`).

How relation resolution was staged across Slices 2 and 3, and the dependency-order constraint the first implementation carried, are recorded in the [rationale file][spec-001-rationale].

## Registry

A process-global registry (`django_strawberry_framework/registry.py::TypeRegistry`, exposed as the module-level singleton `registry`) maps Django model -> registered `DjangoType`s and `(model, field_name)` -> generated enum. It exists so relation resolution and enum conversion can look up already-collected types. `TypeRegistry.clear()` is the test-only isolation helper.

Registration is many-to-one, not one-to-one: several `DjangoType`s may register against one model, and `Meta.primary` flags exactly one of them as the relation-resolution target. `TypeRegistry.get(model)` returns the declared primary when there is one, the lone registered type when there is exactly one and no primary flag, and `None` when a model carries several types with no declared primary — an ambiguity `finalize_django_types()` audits. `Meta.primary` and the multi-type contract are owned by `spec-018-meta_primary-0_0_6.md`; this spec owns the lookup the relation half depends on.

Three registration collisions raise [`ConfigurationError`][glossary-configurationerror]: registering one `DjangoType` class against a second model (the reverse collision — the class-to-model map stays one-to-one); declaring a second primary for a model that already has one; and flipping the `primary` flag on an otherwise idempotent re-register, because primary status is a declaration rather than a mutable property.

The registry carries no `lazy_ref`. Definition-order independence is delivered by the pending-relation bookkeeping named under "Relation field conversion" — `add_pending_relation` / `iter_pending_relations` / `discard_pending` plus the `finalize_django_types()` pass — rather than by a lazy forward-reference factory. The three candidate resolution approaches weighed at authoring time, and which one the implementation took, are in the [rationale file][spec-001-rationale].

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

The introspection is wired in two places, both type-system surface this spec owns even though the optimizer is their only consumer. First, `DjangoType` carries the class-var sentinel `_is_default_get_queryset: ClassVar[bool] = True`. Second, `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` stamps it from `::_detect_custom_get_queryset`, which walks `cls.__mro__` and stops at `DjangoType`, so an override declared anywhere between the subclass and the base counts.

Two properties of that wiring are load-bearing and neither survives a naive `"get_queryset" in cls.__dict__` test on the subclass alone:

- **The stamp happens before the `Meta`-absent early return.** An abstract intermediate that declares `get_queryset` without a `Meta` still flips the sentinel, so the concrete subclasses layered on top of it report `has_custom_get_queryset() is True`. This is exactly the shared-scoping base class the `Meta`-less abstract-intermediate rule above exists to support, so testing only the concrete subclass's own `__dict__` would silently drop its visibility filter.
- **The resolved value is also recorded on the type's `DjangoTypeDefinition`.** `has_custom_get_queryset()` reads `types/definition.py::DjangoTypeDefinition.has_custom_get_queryset` once a definition exists and falls back to the negated sentinel before then — still a constant-time attribute read, called once per relation per resolver call by the optimizer.

## N+1 strategy

The first spec should not treat N+1 as a later enhancement; it is part of the foundation. The package ships a Strawberry schema extension named [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], exported from the package root, that consumers opt into once at schema construction time.

`spec-002-optimizer-0_0_2.md` and its family own the optimizer's architecture and implementation — the root-gated hook, the selection-tree walker, nested prefetch chains, [`only()`][glossary-only-projection] projection, and the relation planner. Do not re-derive any of that from this section; what stays here is the shape the type system owes the optimizer, and the rules that had to be settled in the foundation.

The cardinality rules the type system is planned against:

forward FK / OneToOne -> `select_related`

reverse FK / reverse OneToOne -> `prefetch_related`

M2M -> `prefetch_related`

selected scalar columns -> `only()`

A projection over a joined relation must carry the source row's local FK column alongside the joined columns. With the FK column masked out, Django marks the joined attributes deferred and issues a fresh query the moment a resolver touches one — the N+1 the projection exists to remove, reintroduced by the optimization meant to prevent it.

The load-bearing edge case is custom `get_queryset` on the target type. strawberry-graphql-django hit this exact bug in issue #572 and fixed it in PR #583 by converting what would have been `select_related` into a `Prefetch(queryset=target_type.get_queryset(...))` when the target type defines a non-default `get_queryset`. This rule must be part of the first spec because otherwise FK joins bypass per-type visibility filtering and leak rows. We copy the behaviour, not the decorator surface.

So the rule here is:

if a related field would normally use `select_related`, but the target `DjangoType` overrides `get_queryset`, downgrade that relation to `Prefetch` with the target type's filtered queryset.

Visibility filtering is not confined to that downgraded branch. The target type's `get_queryset` is applied to the child queryset of every `Prefetch` the planner builds, the ordinary many-side prefetch included, so a relation the planner builds a queryset for cannot return rows the target type would have filtered out. The downgrade closes the one branch — a collapsed FK join — that has no child queryset to apply it to.

That gives us the best part of strawberry-graphql-django's optimizer without adopting its decorator-first public API. It is also why `has_custom_get_queryset()` is type-system surface rather than optimizer surface: the planner asks the question, but only the type knows the answer.

Schema-level opt-in:

```python
import strawberry

from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types

finalize_django_types()
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    extensions=[lambda: _optimizer],
)
```

The callable-factory form in `extensions=` is what preserves the extension instance's plan cache across operations; the bare-instance form, which Strawberry warns on as of `0.316.0`, is not the supported spelling. That construction contract is owned by `spec-029-consumer_dx_cleanup-0_0_9.md`.

## Type naming

Default GraphQL type name is the consumer class's `__name__`, matching both graphene-django and Strawberry norms, overridable per type with `Meta.name`. Relay connection types and edges follow the same class-derived naming family (`<TypeName>Connection`), which `spec-030-connection_field-0_0_9.md` owns; this spec fixes only the object-type naming rule and the choice-enum naming rule.

## Testing strategy

Package tests for this surface live under `tests/types/` and `tests/optimizer/`, plus `tests/test_registry.py` at the package-test root, with the per-module inventory in "Files to add" below. `tests/base/` is untouched: it is reserved for `conf.py` and version checking per AGENTS.md.

The tests verify:

Meta validation (`fields`/`exclude`, missing `model`, deferred-key rejection)

scalar field mapping on the fakeshop models

choice-field enum generation on a small test-only model fixture

registry behaviour

FK / reverse / M2M relation field generation

optimizer query counts on relation traversal

the `get_queryset` + optimizer downgrade rule using a hidden related row scenario in the example app

The example tests already exercise admin, services, commands, schema, urls, and models through real Django flows. Those stay as-is; this spec adds focused package tests around the core types and the optimizer.

Two placement rules this surface has to honour. First, a package test that declares its own `DjangoType` classes needs an autouse `registry.clear()` fixture. The registry is process-global: it accumulates every declared type for the life of the process, and it refuses a new concrete `DjangoType` once `finalize_django_types()` has run. Without the reset one module's types leak into a later test's schema build, and one test that finalizes breaks every test after it. Second, per AGENTS.md, any behavior reachable through a real GraphQL query against the example project belongs in the live `examples/fakeshop/test_query/` tier rather than in a package test — the optimizer's query counts and the `get_queryset` downgrade are exactly that shape, so the package tier keeps only what a live query cannot reach.

## Suggested implementation slices

Slice 1: scaffolding — `exceptions.py`, `registry.py`, `py.typed`, package re-exports, package logger.

Slice 2: `DjangoType` with scalar field conversion only, enough to map `Category`.

Slice 3: relation conversion for FK / reverse / M2M, still without optimization.

Slices 4-6: the optimizer — `DjangoOptimizerExtension` with `select_related` / `prefetch_related`, then `only()` optimization, then the `get_queryset` + downgrade-to-`Prefetch` rule. These are owned by `spec-002-optimizer-0_0_2.md` (slices O1-O6). The `_is_default_get_queryset` sentinel on `DjangoType` and the `has_custom_get_queryset()` introspection helper stay in this spec: they are type-system surface, and the optimizer is only their consumer.

Slice 7: choice-field enum generation and enum caching. Adds the `if field.choices:` branch to `convert_scalar` (Slice 2 deferred it) plus the `convert_choices_to_enum` body. See the "Choice field enum generation" section above for the full design — naming rule, member-name sanitization, `TextChoices` / `IntegerChoices` support, caching semantics, `null=True` interaction, and test surface.

Why the optimizer slices moved to `spec-002-optimizer-0_0_2.md`, and what the first partial optimizer implementation surfaced, are in the [rationale file][spec-001-rationale].

Each slice should land with tests in the same change so package coverage remains at 100%. Stub bodies between slices use `raise NotImplementedError(...)`; the existing `pyproject.toml` coverage config already lists that line in `exclude_lines`, so a partial scaffold does not break the gate as long as no test reaches the stubbed code path. When a later slice replaces a stub, it must also add the test that covers the new branch.

## Files to add

This spec's slices add the following package modules and tests. Paths are relative to the repository root: `django_strawberry_framework/types/` and `django_strawberry_framework/optimizer/` are packages, `registry.py`, `exceptions.py`, and `py.typed` sit at the package root.

### Package source

- `django_strawberry_framework/exceptions.py` — `DjangoStrawberryFrameworkError` base class plus `ConfigurationError` (raised by Meta validation, registry collisions, and optimizer planning failures) and `OptimizerError` (raised when the optimizer cannot plan a relation traversal). The base class lets consumers catch the broad family in a single `except` while still distinguishing the specific causes downstream. No Django or Strawberry imports — keeps the exception hierarchy importable from anywhere in the package without circulars, which is why later specs have been able to add their own subclasses (`PathResolutionError`, `LookupValidationError`) to the same module.
- `django_strawberry_framework/registry.py` — `TypeRegistry` class plus a module-level singleton `registry`. Holds `model -> DjangoType`s, the per-model primary flag, the pending-relation records, and `(model, field_name) -> Enum`. The surface this spec depends on is `register` / `get` / `register_enum` / `get_enum` / `clear()` (test-only) plus the pending-relation trio `add_pending_relation` / `iter_pending_relations` / `discard_pending`. There is no `lazy_ref` — see "Registry".
- `django_strawberry_framework/types/converters.py` — `SCALAR_MAP`, `scalar_for_field`, `convert_field_output(field, type_name)`, `convert_scalar(field, type_name)`, `convert_choices_to_enum(field, type_name)` with its shared `build_enum_from_choices` core, and `resolved_relation_annotation(field, target_type)`. All field-shape introspection lives here so `types/base.py` stays focused on Meta orchestration. The `BigInt` scalar itself lives in `django_strawberry_framework/scalars.py` and is imported here.
- `django_strawberry_framework/types/base.py` — `DjangoType` base class. Owns the `__init_subclass__` pipeline that validates `Meta`, synthesizes annotations via `converters.py`, and registers the resulting type with `registry`; `strawberry.type` decoration is `types/finalizer.py::finalize_django_types`'s job, not this module's. Defines the default `get_queryset` classmethod, the `has_custom_get_queryset()` introspection helper, `ALLOWED_META_KEYS`, and `DEFERRED_META_KEYS`.
- `django_strawberry_framework/optimizer/` — `DjangoOptimizerExtension` (Strawberry `SchemaExtension`) and the selection-tree walker behind it. Named here because this spec proposed the public name and the downgrade rule; the module's contents are owned by `spec-002-optimizer-0_0_2.md`.
- `django_strawberry_framework/py.typed` — Empty PEP 561 marker so `mypy` and `pyright` consume our annotations from the installed wheel.
- `django_strawberry_framework/__init__.py` — Re-exports `DjangoType`, `DjangoOptimizerExtension`, and `auto` (pass-through of `strawberry.auto`). Keeps `__version__`. Exposes a package-level `logging.getLogger("django_strawberry_framework")` for the optimizer to emit downgrade decisions and other diagnostics.

### Tests

- `tests/types/test_base.py` — Meta validation (required `model`, `fields`/`exclude` mutual exclusivity, deferred-key rejection one assertion per key), scalar mapping against `Category`/`Item`/`Property`/`Entry`, and the default `get_queryset` identity behaviour plus the sentinel's inheritance through a `Meta`-less abstract base.
- `tests/types/test_relations.py`, `tests/types/test_definition_relations.py`, `tests/types/test_definition_order.py` — relation generation (FK, reverse FK, forward and reverse M2M) and definition-order independence across the pending-relation / finalize pass.
- `tests/test_registry.py` — registry behaviour: the three registration collisions, the primary lookup, and `clear()`.
- `tests/optimizer/` — the planner's own suite. Query-count assertions for the `get_queryset` + downgrade-to-`Prefetch` rule run in the live `examples/fakeshop/test_query/` tier instead, against the products app's `is_private` visibility filter, because that path is reachable from a real GraphQL query.
- `tests/types/test_converters.py` — scalar conversion and choice-enum generation / caching. Because the products models declare no `choices`, this module ships a session-scoped `pytest` fixture defining an in-test `ChoiceFixture` model under a synthetic `app_label`. The choice-enum path is exercised without polluting the example schema, and the cross-type enum-reuse test reuses the same fixture.

`tests/base/` is not modified by this spec.

### Files NOT in this spec

`fields.py` (the `FieldSet` sidecar), `filters.py`, `orders.py`, `aggregates.py`, and `permissions.py` belong to later specs. Of those, filtering (`spec-027-filters-0_0_8.md`), ordering (`spec-028-orders-0_0_8.md`), and cascade permissions (`spec-034-permissions-0_0_10.md`) have since shipped; `FieldSet` and aggregates have not, and their `Meta` keys are still in `DEFERRED_META_KEYS`.

That deferred set is a live constraint on the example project, not a historical one: a `search_fields` line on any `DjangoType.Meta` raises `ConfigurationError` at import until the search spec ships. The products example therefore carries each such line individually commented out beside the card that will enable it, rather than in a block that could be uncommented wholesale. Any later change that re-enables a block of example `Meta` keys owes the same check — enable a key only in the change that moves it out of `DEFERRED_META_KEYS`.

## References

The two upstream packages are read from the local checkouts AGENTS.md names: graphene-django at `~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django`, strawberry-graphql-django at `~/projects/strawberry-django-main/strawberry_django`.

graphene-django Meta and registry foundation: `graphene_django/types.py::DjangoObjectType` (with `::DjangoObjectTypeOptions` and `::construct_fields`), `graphene_django/registry.py::Registry`

graphene-django field conversion coverage: `graphene_django/converter.py::convert_django_field` and its `singledispatch` registrations, plus `::convert_django_field_with_choices` and `::convert_choice_field_to_enum` for the choices path

strawberry-graphql-django type generation: `https://strawberry.rocks/docs/django/guide/types`

strawberry-graphql-django optimizer: `https://strawberry.rocks/docs/django/guide/optimizer`

strawberry-graphql-django custom-`get_queryset` / optimizer edge case: issue #572 and PR #583 on `strawberry-graphql/strawberry-django`

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-apply-cascade-permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-metachoice-enum-names]: ../GLOSSARY.md#metachoice_enum_names
[glossary-metadescription]: ../GLOSSARY.md#metadescription
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaname]: ../GLOSSARY.md#metaname
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion

<!-- docs/SPECS/ -->
[spec-001-rationale]: appx/spec-001-django_types-0_0_1-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
