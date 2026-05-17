"""Convert Django model fields to Strawberry-compatible Python types.

Two halves:

- ``convert_scalar(field, type_name)`` — scalar columns
  (``CharField`` -> ``str`` etc.) and choice fields (-> generated ``Enum``).
- ``convert_relation(field)`` — FK / OneToOne / reverse / M2M, returning
  the registered target ``DjangoType`` in the correct GraphQL cardinality
  shape.

All field-shape introspection lives here so ``types.py`` stays focused on
``Meta`` orchestration.
"""

import datetime
import decimal
import keyword
import re
import uuid
from enum import Enum
from typing import Any

import strawberry
from django.db import models

from ..exceptions import ConfigurationError
from ..optimizer.field_meta import FieldMeta
from ..registry import registry
from ..scalars import BigInt
from ..utils.strings import pascal_case
from .relations import PendingRelationAnnotation

SCALAR_MAP: dict[type[models.Field], Any] = {
    models.AutoField: int,
    models.BigAutoField: int,
    models.SmallAutoField: int,
    models.CharField: str,
    models.TextField: str,
    models.SlugField: str,
    models.EmailField: str,
    models.URLField: str,
    models.GenericIPAddressField: str,
    models.FilePathField: str,
    models.IntegerField: int,
    models.BigIntegerField: BigInt,
    models.SmallIntegerField: int,
    models.PositiveIntegerField: int,
    models.PositiveSmallIntegerField: int,
    models.PositiveBigIntegerField: BigInt,
    models.BooleanField: bool,
    models.FloatField: float,
    models.DecimalField: decimal.Decimal,
    models.DateField: datetime.date,
    models.DateTimeField: datetime.datetime,
    models.TimeField: datetime.time,
    models.DurationField: datetime.timedelta,
    models.JSONField: strawberry.scalars.JSON,
    models.UUIDField: uuid.UUID,
    models.BinaryField: bytes,
    models.FileField: str,
    models.ImageField: str,
}


def _resolve_array_field() -> type[models.Field] | None:
    """Soft-import postgres ``ArrayField``.

    Returns ``None`` if ``django.contrib.postgres.fields`` is unavailable so
    package import succeeds on dev environments without the postgres driver.
    """
    try:
        from django.contrib.postgres.fields import ArrayField
    except ImportError:
        return None
    return ArrayField


def _resolve_hstore_field() -> type[models.Field] | None:
    """Soft-import postgres ``HStoreField``.

    Returns ``None`` if ``django.contrib.postgres.fields`` is unavailable so
    package import succeeds on dev environments without the postgres driver.
    """
    try:
        from django.contrib.postgres.fields import HStoreField
    except ImportError:
        return None
    return HStoreField


_ARRAY_FIELD_CLS: type[models.Field] | None = _resolve_array_field()
_HSTORE_FIELD_CLS: type[models.Field] | None = _resolve_hstore_field()


def convert_scalar(field: models.Field, type_name: str) -> Any:
    """Map a Django scalar field to a Python / Strawberry type.

    Algorithm:

    0. If the field is a sentinel-guarded postgres type (``ArrayField`` /
       ``HStoreField``), dispatch to the matching branch and return early.
       ``ArrayField`` rejects nested arrays and outer ``choices``, then
       recurses on ``base_field`` and wraps in ``list[inner]``.
       ``HStoreField`` rejects outer ``choices``, then returns
       ``strawberry.scalars.JSON``. Both branches widen to ``T | None`` on
       outer ``field.null`` themselves.
    1. Walk ``type(field).__mro__`` until a supported Django field class is
       found in ``SCALAR_MAP``; raise ``ConfigurationError`` if unsupported.
    2. If the field declares ``choices``, replace the scalar type with a
       generated ``Enum`` via ``convert_choices_to_enum(field, type_name)``.
    3. If the field is nullable, widen to ``T | None``.

    Order matters: choices replaces ``py_type`` *before* null widening so
    nullable choice fields end up as ``EnumType | None``, not
    ``(str | None)`` collapsed away.

    Args:
        field: A bound Django model field.
        type_name: The consumer-facing ``DjangoType`` class name. Threaded
            through so the choice-enum path can build a stable
            ``<TypeName><FieldName>Enum`` GraphQL name.

    Raises:
        ConfigurationError: triggered by any of the following:

            - ``Unsupported Django field type`` — no class in
              ``type(field).__mro__`` is in ``SCALAR_MAP``.
            - ``Nested ArrayField on ...`` — ``ArrayField`` whose
              ``base_field`` is itself an ``ArrayField`` (multi-dim arrays
              are not supported).
            - ``ArrayField on ... declares choices on the outer field`` —
              outer-array ``choices`` are ambiguous at the GraphQL
              boundary; declare choices on ``base_field`` instead.
            - ``HStoreField on ... declares choices`` — ``HStoreField``
              stores a ``dict[str, str | None]`` with no enum-able shape
              at the GraphQL boundary.
            - ``<Model>.<field> uses Django's grouped-choices form`` —
              raised from ``convert_choices_to_enum`` for nested-tuple
              choice declarations.
    """
    # Sentinel-guarded ``ArrayField`` dispatch runs **before** the MRO walk
    # so a subclass-of-``models.Field`` test double does not accidentally
    # match a parent in ``SCALAR_MAP``. The recursive call into
    # ``base_field`` re-enters ``convert_scalar`` and naturally inherits
    # choice substitution and inner-null widening; the outer ``field.null``
    # widens the resulting ``list[inner]`` here.
    if _ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS):
        if isinstance(field.base_field, _ARRAY_FIELD_CLS):
            raise ConfigurationError(
                f"Nested ArrayField on {field.model.__name__}.{field.name} is not supported.",
            )
        if field.choices:
            raise ConfigurationError(
                f"ArrayField on {field.model.__name__}.{field.name} declares choices on the outer "
                f"field; outer-array choices are ambiguous at the GraphQL boundary. Declare choices "
                f"on base_field for element-level enum, or use FilterSet.",
            )
        inner = convert_scalar(field.base_field, type_name)
        result = list[inner]
        return result | None if field.null else result
    # Sentinel-guarded ``HStoreField`` dispatch mirrors the ArrayField
    # posture: outer-``choices`` rejection (HStore stores
    # ``dict[str, str | None]`` with no enum-able GraphQL shape), then
    # return ``strawberry.scalars.JSON`` widened on outer ``field.null``.
    if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS):
        if field.choices:
            raise ConfigurationError(
                f"HStoreField on {field.model.__name__}.{field.name} declares choices; "
                f"HStore stores a dict[str, str | None] with no enum-able shape at the "
                f"GraphQL boundary. Drop the choices declaration or model the constrained "
                f"shape with a separate field.",
            )
        py_type = strawberry.scalars.JSON
        return py_type | None if field.null else py_type
    py_type: Any = None
    # Walk the field's MRO so consumer-defined subclasses of a supported
    # Django field (e.g. ``class TrimmedCharField(models.CharField)`` or
    # third-party encrypted/money field subclasses that ultimately store
    # to a supported column type) resolve to the parent's scalar instead
    # of raising. Exact-type lookup would force every subclass to be
    # registered in ``SCALAR_MAP`` explicitly.
    for klass in type(field).__mro__:
        if klass in SCALAR_MAP:
            py_type = SCALAR_MAP[klass]
            break
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


_NON_IDENT = re.compile(r"\W+", flags=re.ASCII)
_GRAPHQL_RESERVED_ENUM_VALUES = frozenset({"false", "null", "true"})


def _sanitize_member_name(value: Any) -> str:
    """Produce a Strawberry / GraphQL-safe enum member from a Django choice value.

    The choice value (DB-side, not the human label) is the input. We coerce
    to ``str`` so ``IntegerChoices`` work, replace any non-ASCII
    identifier characters with ``_``, prefix with ``MEMBER_`` if the
    result starts with a digit (or is empty), and prefix with an
    underscore if it collides with a Python keyword. GraphQL-reserved enum
    values (``true``, ``false``, ``null``) and introspection-prefixed
    names are also prefixed so Strawberry can build the schema.
    Sanitization is a function of the raw value, not the label, so schema
    member names stay stable when consumers edit human-readable labels.
    """
    sanitized = _NON_IDENT.sub("_", str(value))
    if not sanitized or sanitized[0].isdigit():
        sanitized = f"MEMBER_{sanitized}"
    if keyword.iskeyword(sanitized):
        sanitized = f"_{sanitized}"
    if sanitized.casefold() in _GRAPHQL_RESERVED_ENUM_VALUES or sanitized.startswith("__"):
        sanitized = f"MEMBER_{sanitized}"
    return sanitized


def convert_choices_to_enum(field: models.Field, type_name: str) -> type[Enum]:
    """Generate (or fetch from registry) a Strawberry ``Enum`` for ``field.choices``.

    1. Reject Django's grouped-choices form.
    2. Cache check on ``(field.model, field.name)``.
    3. Compute enum name ``f"{type_name}{PascalCase(field.name)}Enum"``.
    4. Sanitize member names from choice *values* (not labels) so a label
       edit doesn't churn the GraphQL schema. Integer or hyphenated
       values produce ``MEMBER_<digit>`` / underscore-mangled names.
    5. Build the ``Enum`` and decorate with ``strawberry.enum``.
    6. Cache via ``registry.register_enum``.
    7. Return the enum class.

    The first ``DjangoType`` to read a given ``(model, field_name)`` wins
    the enum's GraphQL name; sibling types pointing at the same column
    receive the cached enum unchanged.

    Raises:
        ConfigurationError: ``field.choices`` contains nested tuples
            (Django's grouped-choices form) or is empty.
    """
    choices = list(field.choices or [])
    if not choices:
        raise ConfigurationError(
            f"{field.model.__name__}.{field.name} declares choices but the "
            "sequence is empty; choices must be a non-empty flat sequence "
            "of (value, label) pairs.",
        )
    for _value, label in choices:
        # Django's grouped-choices form is
        # ``(group_label, [(value, label), ...])``. In the flat form the
        # second element is always a label string; in the grouped form it
        # is a sequence of (value, label) pairs. Detecting on ``label``
        # rather than ``value`` is the load-bearing distinction — in the
        # grouped form the *value* slot is the human-readable group name
        # (a string), so checking it produces a false negative.
        if isinstance(label, (list, tuple)):
            raise ConfigurationError(
                f"{field.model.__name__}.{field.name} uses Django's grouped-choices "
                "form (nested tuples for option groups). Only the flat "
                "(value, label) form is supported; flatten the choices source or split into "
                "separate fields.",
            )

    cached = registry.get_enum(field.model, field.name)
    if cached is not None:
        return cached

    enum_name = f"{type_name}{pascal_case(field.name)}Enum"
    members: dict[str, Any] = {}
    collisions: dict[str, list[Any]] = {}
    for value, _label in choices:
        member = _sanitize_member_name(value)
        if member in members:
            collisions.setdefault(member, [members[member]]).append(value)
        else:
            members[member] = value
    if collisions:
        details = ", ".join(
            f"{member!r} from values {sorted(map(repr, vals))}" for member, vals in sorted(collisions.items())
        )
        raise ConfigurationError(
            f"{field.model.__name__}.{field.name} choices sanitize to the same enum member: "
            f"{details}.  Rename one side or split into separate fields.",
        )
    enum_cls = Enum(enum_name, members)  # type: ignore[arg-type]
    enum_cls = strawberry.enum(enum_cls)
    registry.register_enum(field.model, field.name, enum_cls)
    return enum_cls


def resolved_relation_annotation(
    field: models.Field,
    target_type: type,
    *,
    field_meta: FieldMeta | None = None,
) -> Any:
    """Return the concrete annotation for ``field`` pointing at ``target_type``."""
    meta = field_meta or FieldMeta.from_django_field(field)
    if meta.is_many_side:
        return list[target_type]
    if meta.nullable:
        return target_type | None
    return target_type


def convert_relation(field: models.Field) -> Any:
    """Map a Django relation field to its target ``DjangoType``.

    Cardinality table:

    - Forward FK (``many_to_one``) -> target type, nullable iff ``field.null``.
    - Forward OneToOne (``one_to_one`` and not ``auto_created``) -> target
      type, nullable iff ``field.null``.
    - Reverse OneToOne (``one_to_one`` and ``auto_created``) -> target type
      or ``None`` (always conceptually nullable; the reverse row may not
      exist).
    - Reverse FK (``one_to_many``) -> ``list[target_type]``.
    - Forward / reverse M2M (``many_to_many``) -> ``list[target_type]``.

    If the target type is not registered yet, return
    ``PendingRelationAnnotation``. The caller records the matching
    ``PendingRelation`` and ``finalize_django_types()`` rewrites the
    annotation after all modules have imported. Callers must record a
    ``PendingRelation`` for any field that returns
    ``PendingRelationAnnotation``; otherwise ``finalize_django_types()``
    cannot rewrite the annotation and Strawberry will raise during schema
    construction.

    Args:
        field: A bound Django relation field or related-object descriptor.
            Forward FK / OneToOne / M2M live on the source model;
            reverse-side fields live on the related model and surface
            here via ``Model._meta.get_fields()``.

    """
    target_model = field.related_model
    target_type = registry.get(target_model)
    if target_type is None:
        return PendingRelationAnnotation
    return resolved_relation_annotation(
        field,
        target_type,
        field_meta=FieldMeta.from_django_field(field),
    )
