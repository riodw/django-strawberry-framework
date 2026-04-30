"""Convert Django model fields to Strawberry-compatible Python types.

Two halves:

- ``convert_scalar(field, type_name)`` — scalar columns
  (``CharField`` -> ``str`` etc.) and choice fields (-> generated ``Enum``).
- ``convert_relation(field)`` — FK / OneToOne / reverse / M2M, returning
  a forward reference to the target ``DjangoType`` so definition order is
  free.

All field-shape introspection lives here so ``types.py`` stays focused on
``Meta`` orchestration.
"""

import datetime
import decimal
import uuid
from enum import Enum
from typing import Any

from django.db import models

# TODO(slice 2): define and export a ``BigInt`` Strawberry scalar so
# ``BigIntegerField`` maps to a 64-bit integer that survives JSON
# serialization. Build it via Strawberry's ``scalar()`` helper with
# ``name="BigInt"``, ``serialize=str`` (so JSON clients receive a string
# and avoid silent truncation past 2**53), and ``parse_value=int`` for
# the inbound side. Once defined, add ``models.BigIntegerField: BigInt``
# to ``SCALAR_MAP``.

# TODO(slice 2): handle ``ArrayField`` -> ``list[inner_type]`` by
# inspecting ``field.base_field`` (itself a Django Field) and recursing
# through ``convert_scalar`` to resolve the inner annotation.

# TODO(slice 2): handle ``JSONField`` and ``HStoreField`` via Strawberry's
# JSON scalar (``strawberry.scalars.JSON``). Both columns deserialize to
# native Python dict / list shapes; the GraphQL schema sees them as ``JSON``.

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
    """Map a Django scalar field to a Python / Strawberry type.

    Algorithm:

    1. Look up ``type(field)`` in ``SCALAR_MAP``; fall back to ``Any``.
    2. If the field declares ``choices``, route through
       ``convert_choices_to_enum(field, type_name)`` to obtain (or build
       and cache) the corresponding Strawberry enum.
    3. If the field is nullable (``null=True``), widen to ``T | None``.
    4. Return the resolved type.

    Args:
        field: A bound Django model field.
        type_name: The consumer-facing ``DjangoType`` class name, used to
            name generated choice enums (``f"{type_name}{FieldName}Enum"``).
            Threaded down from ``DjangoType.__init_subclass__``.
    """
    # TODO(slice 2): implement the four-step algorithm above. Use
    # ``SCALAR_MAP.get(type(field), Any)`` for the base lookup. Emit a
    # logger warning when the ``Any`` fallback fires so unknown columns
    # are visible during development. Prefer ``isinstance`` over ``type
    # is`` only if subclass tolerance becomes an issue (Django's built-in
    # field hierarchy is shallow, so direct ``type(field)`` lookup is
    # sufficient for the canonical cases).
    raise NotImplementedError("Scalar field conversion pending Slice 2")


def convert_choices_to_enum(field: models.Field, type_name: str) -> type[Enum]:
    """Generate (or fetch from registry) a Strawberry ``Enum`` for ``field.choices``.

    Algorithm:

    1. Check ``registry.get_enum(field.model, field.name)``; return the
       cached enum if present.
    2. Compute ``enum_name = f"{type_name}{FieldName}Enum"`` where
       ``FieldName`` is ``field.name`` in PascalCase.
    3. Build a ``{member_name: value}`` mapping from ``field.choices``,
       sanitizing member names to valid Python identifiers.
    4. Build the enum via ``Enum(enum_name, members)`` and decorate with
       ``strawberry.enum``.
    5. Cache via ``registry.register_enum(field.model, field.name, enum_cls)``
       so sibling ``DjangoType``s reuse the same enum.
    6. Return the enum class.
    """
    # TODO(slice 7): implement the six-step algorithm above. Sanitize
    # member names by replacing non-identifier characters with underscores
    # and prefixing with ``MEMBER_`` if the result starts with a digit.
    # Reject Django's grouped-choices form (nested tuples) for now; raise
    # ``ConfigurationError`` with a clear message rather than silently
    # flattening.
    raise NotImplementedError("Choice-field enum generation pending Slice 7")


def convert_relation(field: models.Field) -> Any:
    """Map a Django relation field to a forward reference to the target ``DjangoType``.

    Cardinality table:

    - Forward FK (``many_to_one``) -> target type, nullable iff
      ``field.null``.
    - Forward OneToOne (``one_to_one``) -> target type, nullable iff
      ``field.null``.
    - Reverse FK (``one_to_many`` on the related descriptor) ->
      ``list[target_type]`` (always non-nullable; an empty list when no
      rows exist).
    - Reverse OneToOne (``one_to_one`` on the related descriptor) ->
      target type or ``None`` (always conceptually nullable).
    - Forward / reverse M2M (``many_to_many``) -> ``list[target_type]``.

    Args:
        field: A bound Django relation field or related-object descriptor.
            Forward FK / OneToOne / M2M live on the source model;
            reverse-side fields live on the related model and surface
            here via ``Model._meta.get_fields()``.
    """
    # TODO(slice 3): implement the cardinality table above. Use
    # ``field.many_to_one`` / ``field.one_to_one`` / ``field.one_to_many``
    # / ``field.many_to_many`` flags (all available on Django's
    # ``Field`` and ``ForeignObjectRel`` descriptors) to disambiguate.
    # Fetch the target reference via
    # ``registry.lazy_ref(field.related_model)``; apply nullable / list
    # widening as the cardinality dictates. Reverse-side ``null`` is not
    # meaningful at the schema level; treat the cardinality flag as the
    # authority.
    raise NotImplementedError("Relation conversion pending Slice 3")
