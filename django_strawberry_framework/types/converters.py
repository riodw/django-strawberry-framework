"""Convert Django model fields to Strawberry-compatible Python types.

Public surface:

- ``convert_scalar(field, type_name)`` - scalar columns
  (``CharField`` -> ``str`` etc.). Walks ``type(field).__mro__`` against
  ``SCALAR_MAP``, then delegates to ``convert_choices_to_enum`` when
  ``field.choices`` is set, then widens to ``T | None`` on ``field.null``.
- ``convert_choices_to_enum(field, type_name)`` - generate (or fetch
  cached) Strawberry ``Enum`` from a Django choice field; called from
  ``convert_scalar`` when ``field.choices`` is set and also importable
  directly for tests / custom resolvers.
- ``resolved_relation_annotation(field, target_type, *, field_meta=None)``
  - render the final relation annotation for ``field`` pointing at a
  resolved ``DjangoType`` (``target_type``). Cardinality / null widening
  is sourced from ``FieldMeta``; reused by ``types/finalizer.py``'s
  deferred-resolution path.
- ``SCALAR_MAP`` - module-level ``dict[type[models.Field], Any]`` mapping
  Django field classes to their Python / Strawberry scalar. Mutable,
  last-write-wins, read on every ``convert_scalar`` call (no caching), so
  post-``finalize_django_types()`` mutations remain visible. The canonical
  extension path for a third-party / consumer field is to **subclass** a
  supported Django field - ``convert_scalar``'s MRO walk picks up the
  parent's scalar without registration. ``SCALAR_MAP[FieldCls] = py_type``
  is the non-subclass extension hook (e.g. unrelated third-party fields
  that store to a non-mapped column type). Notably absent from the
  default map: ``DurationField`` (no first-party Strawberry scalar - a
  consumer must register a custom scalar via ``SCALAR_MAP[DurationField]
  = MyDurationScalar``) and ``BinaryField`` (no first-party Strawberry
  scalar either; ``strawberry.scalars.Base64`` is the conventional plug:
  ``SCALAR_MAP[BinaryField] = strawberry.scalars.Base64``).

All field-shape introspection lives here so ``types/base.py`` stays
focused on ``Meta`` orchestration.
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

# TODO(spec-037 Slice 1): add the read-side file/image object mapping here.
# Pseudo-code:
# - define _safe_file_attr(bound_file, attr) that returns None for storage-shaped
#   ValueError / OSError / NotImplementedError, but lets suspicious path errors
#   and real resolver bugs propagate.
# - define resolver-backed @strawberry.type DjangoFileType with name, path, size,
#   and url; name reads the bound file directly, nullable subfields use the guard.
# - define DjangoImageType(DjangoFileType) with nullable width and height through
#   the same guard.
# - add FIELD_OUTPUT_TYPE_MAP for ImageField before FileField and have the read
#   converter consult it before falling back to the scalar/filter map below.
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
    models.JSONField: strawberry.scalars.JSON,
    models.UUIDField: uuid.UUID,
    # TODO(spec-037 Slice 1): keep these rows as str for FilterSet/scalar-input
    # generation; DjangoFileType / DjangoImageType belong in FIELD_OUTPUT_TYPE_MAP
    # so output object types never leak into GraphQL input objects.
    models.FileField: str,
    models.ImageField: str,
}

_NON_IDENT = re.compile(r"\W+", flags=re.ASCII)
_GRAPHQL_RESERVED_ENUM_VALUES = frozenset(
    {"false", "null", "true"},
)


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


def scalar_for_field(field: models.Field) -> Any:
    """Resolve a Django field to its ``SCALAR_MAP`` Python / Strawberry scalar.

    Walks ``type(field).__mro__`` so consumer-defined subclasses of a supported
    field resolve to the parent's scalar, and raises ``ConfigurationError`` for
    an unsupported field class. This is the single field-class -> scalar lookup
    shared by :func:`convert_scalar` (full DjangoType field conversion) and the
    filter-input converter (``filters.inputs._scalar_from_model_field``), so a
    column resolves to the SAME scalar on the selected-field side and the
    filter-input side -- including consumer-registered ``SCALAR_MAP`` entries.
    It does NOT apply choice substitution or null widening; callers layer those
    on (``convert_scalar`` does; filter inputs handle choices separately).
    """
    for klass in type(field).__mro__:
        if klass in SCALAR_MAP:
            return SCALAR_MAP[klass]
    raise ConfigurationError(
        f"Unsupported Django field type {type(field).__name__!r} on "
        f"{field.model.__name__}.{field.name}. Add an entry to "
        "SCALAR_MAP or exclude this field via Meta.exclude.",
    )


def convert_scalar(
    field: models.Field,
    type_name: str,
    *,
    force_nullable: bool | None = None,
) -> Any:
    """Map a Django scalar field to a Python / Strawberry type.

    Algorithm:

    0. Compute ``effective_null`` from the ``force_nullable`` tri-state
       (``field.null`` when ``force_nullable is None``, else
       ``force_nullable`` itself); this single value drives every outer
       nullability decision below.
    0b. If the field is a sentinel-guarded postgres type (``ArrayField`` /
       ``HStoreField``), dispatch to the matching branch and return early.
       ``ArrayField`` rejects nested arrays and outer ``choices``, then
       recurses on ``base_field`` and wraps in ``list[inner]``.
       ``HStoreField`` rejects outer ``choices``, then returns
       ``strawberry.scalars.JSON``. Both branches widen to ``T | None`` on
       ``effective_null`` themselves.
    1. Walk ``type(field).__mro__`` until a supported Django field class is
       found in ``SCALAR_MAP``; raise ``ConfigurationError`` if unsupported.
    2. If the field declares ``choices``, replace the scalar type with a
       generated ``Enum`` via ``convert_choices_to_enum(field, type_name)``.
    3. If ``effective_null``, widen to ``T | None``.

    Order matters: choices replaces ``py_type`` *before* null widening so
    nullable choice fields end up as ``EnumType | None``, not
    ``(str | None)`` collapsed away. The widening test reads
    ``effective_null`` (not ``field.null``) at every site, so a
    ``force_nullable`` override flips the choice enum's nullability for free.

    Args:
        field: A bound Django model field.
        type_name: The consumer-facing ``DjangoType`` class name. Threaded
            through so the choice-enum path can build a stable
            ``<TypeName><FieldName>Enum`` GraphQL name. Also threaded into
            the recursive ``base_field`` call on ``ArrayField``, so an
            inner choice-bearing element resolves under the outer field's
            name.
        force_nullable: Keyword-only nullability override tri-state.
            ``None`` (default) honors ``field.null`` - identical to the
            pre-override behavior, so every existing call site is
            unaffected. ``True`` emits ``T | None`` regardless of the
            column (force nullable). ``False`` emits ``T`` regardless (force
            required). Sourced per field from ``Meta.nullable_overrides`` /
            ``Meta.required_overrides`` by ``types/base._build_annotations``.
            Only the OUTER field's nullability is affected; the recursive
            ``ArrayField.base_field`` call is left unset, so the inner
            element nullability follows ``base_field.null``.

    Raises:
        ConfigurationError: triggered by any of the following:

            - ``Unsupported Django field type`` - no class in
              ``type(field).__mro__`` is in ``SCALAR_MAP``.
            - ``Nested ArrayField on ...`` - ``ArrayField`` whose
              ``base_field`` is itself an ``ArrayField`` (multi-dim arrays
              are not supported).
            - ``ArrayField on ... declares choices on the outer field`` -
              outer-array ``choices`` are ambiguous at the GraphQL
              boundary; declare choices on ``base_field`` instead.
            - ``HStoreField on ... declares choices`` - ``HStoreField``
              stores a ``dict[str, str | None]`` with no enum-able shape
              at the GraphQL boundary.
            - ``<Model>.<field> uses Django's grouped-choices form`` -
              raised from ``convert_choices_to_enum`` for nested-tuple
              choice declarations.
    """
    # The tri-state collapses to a single boolean computed once: the
    # override (``force_nullable``) wins when set, otherwise the column's
    # ``field.null`` drives the decision. Every outer widening site below
    # reads ``effective_null`` so the override applies uniformly across the
    # ArrayField / HStoreField / choice / scalar branches without per-branch
    # override logic.
    effective_null = field.null if force_nullable is None else force_nullable
    # TODO(spec-037 Slice 1): before the generic scalar path, route FileField /
    # ImageField through FIELD_OUTPUT_TYPE_MAP for DjangoType output only.
    # Pseudo-code:
    # - file_effective_null is force_nullable when the override is set;
    #   otherwise it is bool(field.null or field.blank).
    # - output_type = field_output_type_for_field(field) by MRO.
    # - if output_type exists, return output_type | None when file_effective_null.
    # - do not change scalar_for_field(), because filters still use SCALAR_MAP.
    # Sentinel-guarded ``ArrayField`` dispatch runs **before** the MRO walk
    # so a subclass-of-``models.Field`` test double does not accidentally
    # match a parent in ``SCALAR_MAP``. The recursive call into
    # ``base_field`` re-enters ``convert_scalar`` and naturally inherits
    # choice substitution and inner-null widening; the outer
    # ``effective_null`` widens the resulting ``list[inner]`` here. The
    # recursion is left ``force_nullable``-unset so the inner element
    # nullability follows ``base_field.null`` and is NOT affected by the
    # outer override.
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
        return result | None if effective_null else result
    # Sentinel-guarded ``HStoreField`` dispatch mirrors the ArrayField
    # posture: outer-``choices`` rejection (HStore stores
    # ``dict[str, str | None]`` with no enum-able GraphQL shape), then
    # return ``strawberry.scalars.JSON`` widened on ``effective_null``.
    if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS):
        if field.choices:
            raise ConfigurationError(
                f"HStoreField on {field.model.__name__}.{field.name} declares choices; "
                f"HStore stores a dict[str, str | None] with no enum-able shape at the "
                f"GraphQL boundary. Drop the choices declaration or model the constrained "
                f"shape with a separate field.",
            )
        py_type = strawberry.scalars.JSON
        return py_type | None if effective_null else py_type
    # Shared field-class -> scalar lookup (also used by the filter-input
    # converter) so a column resolves to the same scalar on both sides. Walks
    # the MRO, so consumer subclasses of a supported field resolve to the
    # parent's scalar and an unsupported field raises ``ConfigurationError``.
    py_type = scalar_for_field(field)
    if field.choices:
        py_type = convert_choices_to_enum(field, type_name)
    if effective_null:
        py_type = py_type | None
    return py_type


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

    Rules apply in this order: (1) ASCII non-identifier characters
    rewritten to ``_``; (2) leading-digit or empty result prefixed with
    ``MEMBER_``; (3) Python-keyword result prefixed with ``_``;
    (4) GraphQL-reserved (``true`` / ``false`` / ``null``) or
    ``__``-prefixed result prefixed with ``MEMBER_``. The order is
    load-bearing because the keyword-and-reserved rewrites in steps 3 and
    4 cannot collapse into a single condition without changing how
    downstream collision detection (see ``convert_choices_to_enum``)
    categorises ambiguous values.
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

    1. Coerce ``field.choices`` to a list and reject if empty.
    2. Reject Django's grouped-choices form.
    3. Cache check on ``(field.model, field.name)``; return cached on hit.
    4. Compute enum name ``f"{type_name}{PascalCase(field.name)}Enum"``.
    5. Sanitize member names from choice *values* (not labels) so a label
       edit doesn't churn the GraphQL schema; reject if two values
       sanitize to the same identifier.
    6. Build the ``Enum`` and decorate with ``strawberry.enum``.
    7. Cache via ``registry.register_enum`` and return the enum class.

    The first ``DjangoType`` to read a given ``(model, field_name)`` wins
    the enum's GraphQL name; sibling types pointing at the same column
    receive the cached enum unchanged.

    Raises:
        ConfigurationError: triggered by any of the following:

            - ``field.choices`` is empty - declared but the sequence is
              empty.
            - ``field.choices`` contains nested tuples (Django's
              grouped-choices form). Only the flat ``(value, label)``
              form is supported.
            - two or more choice values sanitize to the same enum member
              (e.g. ``"a-b"`` and ``"a_b"`` both collapse to ``"a_b"``);
              rename one side or split into separate fields.
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
        # rather than ``value`` is the load-bearing distinction - in the
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
            f"{member!r} from values {sorted(map(repr, vals))}"
            for member, vals in sorted(collisions.items())
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
