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
from ..registry import registry
from ..utils.relations import is_many_side_relation_kind, relation_kind
from ..utils.strings import pascal_case
from .relations import PendingRelationAnnotation

# TODO(future): define and export a ``BigInt`` Strawberry scalar so
# ``BigIntegerField`` maps to a 64-bit integer that survives JSON
# serialization. Build it via Strawberry's ``scalar()`` helper with
# ``name="BigInt"``, ``serialize=str`` (so JSON clients receive a string
# and avoid silent truncation past 2**53), and ``parse_value=int`` for
# the inbound side. Once defined, add ``models.BigIntegerField: BigInt``
# to ``SCALAR_MAP``. The example fakeshop models use ``BigAutoField``
# (mapped to ``int``) and no plain ``BigIntegerField``.

# TODO(future): handle ``ArrayField`` -> ``list[inner_type]`` by
# inspecting ``field.base_field`` (itself a Django Field) and recursing
# through ``convert_scalar`` to resolve the inner annotation.

# TODO(future): handle ``JSONField`` and ``HStoreField`` via Strawberry's
# JSON scalar (``strawberry.scalars.JSON``). Both columns deserialize to
# native Python dict / list shapes; the GraphQL schema sees them as ``JSON``.

SCALAR_MAP: dict[type[models.Field], type] = {
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
    """Map a Django scalar field to a Python / Strawberry type.

    Algorithm:

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
        ConfigurationError: no class in ``type(field).__mro__`` is in
            ``SCALAR_MAP``, or ``field.choices`` is in Django's grouped
            form (raised from ``convert_choices_to_enum``).
    """
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


def resolved_relation_annotation(field: models.Field, target_type: type) -> Any:
    """Return the concrete annotation for ``field`` pointing at ``target_type``."""
    # TODO(spec-fieldmeta-ssot): read cardinality + nullable from a
    # ``FieldMeta`` instead of ``relation_kind(field)`` + raw
    # ``getattr(field, "null", False)``. ``FieldMeta`` is the canonical
    # SSoT for relation shape — see ``optimizer/field_meta.py``
    # module docstring.
    kind = relation_kind(field)
    if is_many_side_relation_kind(kind):
        return list[target_type]
    if kind == "reverse_one_to_one" or getattr(field, "null", False):
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
    return resolved_relation_annotation(field, target_type)
