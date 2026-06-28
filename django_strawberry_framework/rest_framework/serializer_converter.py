"""DRF serializer-field -> Strawberry input conversion + the per-input-field reverse map (spec-039).

The serializer-flavor analog of ``forms/converter.py`` (spec-038): a DRF
``serializers.Field``-keyed registry mapping each supported serializer field to
its Strawberry annotation + required-ness, in the graphene-django
``convert_serializer_field`` parity shape, raised through the package's own
``ConfigurationError``.

It is NOT a parallel copy of the read-side scalar table. Where a
``ModelSerializer`` field has a backing model column (resolved via the field's
``source``), the annotation routes through the read-side ``convert_scalar`` /
``convert_choices_to_enum`` / ``relation_input_annotation`` at the
``rest_framework/inputs.py`` build site (keyed on the resolved ``models.Field``),
so a ``choices`` column resolves to the SAME generated enum the read
``DjangoType`` synthesizes (the symmetric wire contract). The two key spaces -
DRF ``serializers.Field`` here, ``models.Field`` on the read side - stay strictly
separate.

**Fail-loud dispatch (spec-039 Decision 4 / P1.4).** Dispatch rides the shared
``utils/converters.py::convert_with_mro`` skeleton: ordered ``isinstance``
prechecks (relation / file / list / multi-choice kinds that must win before the
scalar registry MRO walk reaches a parent class), then the scalar registry MRO
walk, then a RAISING fallthrough. It is deliberately NOT ``functools.singledispatch``
with the graphene-django ``serializers.Field -> String`` catch-all, which would
shadow the raise so every custom field silently became ``String`` (the
``ImproperlyConfigured`` parity, lost). An unmapped ``serializers.Field`` subclass
raises ``ConfigurationError`` naming the field + class.

**The reverse map + the ``source`` axis (spec-039 Decision 7).** The generated
input GraphQL name comes from the DECLARED serializer field name via the id-like
suffix rule (``category`` / ``category_id`` -> ``categoryId``, ``category_pk`` ->
``categoryPk`` - no doubled ``...IdId`` / ``...PkId``), NOT from ``source``. The
backing ``models.Field`` is resolved through the field's ``source`` (one-segment
or equal to the declared name). A dotted ``source`` / ``source="*"`` on a
model-column-converting field raises ``ConfigurationError``. The unified
``utils/inputs.py::InputFieldSpec`` records the reverse map - ``target_name`` is
the DECLARED serializer field name (the ``validated_data`` key), with the extra
``source`` axis carrying the resolved one-segment source.
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from typing import Any

import strawberry
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from rest_framework import serializers
from strawberry import relay

from ..exceptions import ConfigurationError
from ..mutations.inputs import relation_input_annotation
from ..registry import registry
from ..scalars import Upload
from ..types.converters import convert_scalar, scalar_for_field
from ..types.relay import implements_relay_node
from ..utils.converters import convert_with_mro
from ..utils.inputs import InputFieldSpec, graphql_camel_name

# The four decode kinds the reverse-map record carries, mirroring
# ``forms/converter.py``'s module constants so the Slice 3 resolver + the tests
# address ONE source of truth instead of bare string literals.
SCALAR: str = "scalar"
RELATION_SINGLE: str = "relation_single"
RELATION_MULTI: str = "relation_multi"
FILE: str = "file"

# Each supported DRF ``serializers.Field`` class -> the scalar annotation it maps
# to. Registered INDIVIDUALLY (not via a base-``Field`` catch-all) so subclasses
# resolve through the MRO walk in ``convert_with_mro`` - ``EmailField`` /
# ``SlugField`` / ``URLField`` / ``RegexField`` resolve under ``CharField``, the
# parity behavior. ``ChoiceField`` -> ``str`` is the default; a ``ChoiceField``
# over a ``ModelSerializer`` model's ``choices`` column is routed through the
# read-side enum at the build site instead (keyed on the backing ``models.Field``).
# ``PrimaryKeyRelatedField`` / ``ManyRelatedField`` / ``FileField`` / ``ImageField`` /
# ``ListField`` / ``MultipleChoiceField`` are deliberately NOT in this scalar table -
# they resolve by ``kind`` in the prechecks before the walk reaches them.
#
# Resolution is the shared MRO walk inside ``convert_with_mro`` (the same idiom
# ``types/converters.py::scalar_for_field`` uses) so the MOST-specific registered
# class wins regardless of insertion order. This module never re-spells the walk -
# it only supplies this registry + the prechecks (the P1.4 import-not-redefine
# contract).
_SCALAR_SERIALIZER_FIELDS: dict[type[serializers.Field], Any] = {
    serializers.CharField: str,
    serializers.ChoiceField: str,
    serializers.IntegerField: int,
    serializers.FloatField: float,
    serializers.DecimalField: decimal.Decimal,
    serializers.BooleanField: bool,
    serializers.UUIDField: uuid.UUID,
    serializers.DateTimeField: datetime.datetime,
    serializers.DateField: datetime.date,
    serializers.TimeField: datetime.time,
    serializers.JSONField: strawberry.scalars.JSON,
}


class SerializerFieldConversion:
    """The annotation + decode kind + required-ness ``convert_serializer_field`` returns.

    The serializer-flavor analog of ``forms/converter.py::FormFieldConversion``.
    ``required`` is the serializer field's own ``field.required``; ``annotation``
    is the resolved Strawberry annotation for a SCALAR field (incl. ``list[...]``
    for a scalar ``ListField`` / ``MultipleChoiceField``). For a relation / file
    field the annotation is finalized at the ``rest_framework/inputs.py`` build
    site (where the backing column - if any - and the related primary
    ``DjangoType`` are known, so the Relay-``GlobalID``-vs-raw-pk id type can be
    resolved), so those kinds carry ``annotation=None`` here and only the ``kind``
    is authoritative.
    """

    __slots__ = ("annotation", "kind", "required")

    def __init__(
        self,
        *,
        annotation: Any,
        kind: str,
        required: bool,
    ) -> None:
        self.annotation = annotation
        self.kind = kind
        self.required = required


def _reject_nested_serializer(field: serializers.Field) -> None:
    """Raise if ``field`` is a nested ``Serializer`` / ``ListSerializer`` (the 036 nested-write non-goal).

    Nested serializer writes are an explicit non-goal (the ``036`` nested-write
    carve-out): a ``Serializer`` / ``ModelSerializer`` field or a
    ``ListSerializer`` (a ``many=True`` nested serializer) has no flat scalar / id
    input shape, so it fails loud here rather than silently degrading.
    """
    if isinstance(field, (serializers.BaseSerializer, serializers.ListSerializer)):
        raise ConfigurationError(
            f"Serializer field {field.field_name!r} is a nested "
            f"{type(field).__name__}; nested serializer writes are not supported "
            "(the flat input shape has no representation for them). Drop it via "
            "Meta.fields / Meta.exclude, or model the relation with a "
            "PrimaryKeyRelatedField.",
        )


def _list_child_conversion(field: serializers.ListField) -> SerializerFieldConversion:
    """Map a ``ListField`` to ``list[<scalar child>]``, or raise for a non-scalar child.

    A ``ListField(child=IntegerField())`` becomes ``list[int]`` by recursing the
    child through the SAME scalar registry. A relation / nested-serializer child
    raises ``ConfigurationError`` (the spec-039 Slice-1 contract: only a scalar
    child is supported - a list of relation ids is expressed as
    ``PrimaryKeyRelatedField(many=True)``, not ``ListField(child=relation)``).
    """
    child = field.child
    _reject_nested_serializer(child)
    if isinstance(child, (serializers.RelatedField, serializers.ManyRelatedField)):
        raise ConfigurationError(
            f"Serializer field {field.field_name!r} is a ListField whose child is a "
            f"{type(child).__name__} (a relation); only a scalar child is supported. "
            "Express a list of relation ids with PrimaryKeyRelatedField(many=True).",
        )
    child_conversion = convert_serializer_field(child)
    if child_conversion.kind != SCALAR or child_conversion.annotation is None:
        raise ConfigurationError(
            f"Serializer field {field.field_name!r} is a ListField whose child "
            f"{type(child).__name__} does not resolve to a scalar annotation; only a "
            "scalar child is supported.",
        )
    return SerializerFieldConversion(
        annotation=list[child_conversion.annotation],
        kind=SCALAR,
        required=field.required,
    )


def convert_serializer_field(
    field: serializers.Field,
    *,
    is_input: bool = True,
) -> SerializerFieldConversion:
    """Map a DRF ``serializers.Field`` to its Strawberry annotation + decode kind.

    Returns a ``SerializerFieldConversion`` carrying the resolved scalar
    ``annotation`` (``None`` for the relation / file kinds, finalized at the
    build site), the decode ``kind``, and ``required`` from ``field.required``.

    ``is_input`` is the graphene-django ``convert_serializer_field(field,
    is_input=...)`` parity parameter - **accepted-and-ignored** (spec-039
    Decision 7 / SR-3): for 0.0.13 the converter only ever runs on the input
    side, so there is deliberately NO ``if not is_input:`` branch (a dead branch
    would gate-fail ``fail_under=100``). It is threaded so a future read-side
    caller does not have to widen the signature.

    Dispatch rides the shared ``utils/converters.py::convert_with_mro`` skeleton
    (spec-039 P1.4): the relation / file / list / multi-choice prechecks run
    first (they subclass scalar fields the registry would otherwise match), then
    the scalar registry MRO walk, then a RAISING fallthrough - never a
    ``serializers.Field -> str`` catch-all.

    - relation kinds first: ``ManyRelatedField`` (a ``many=True`` relation) ->
      ``relation_multi``; a plain ``PrimaryKeyRelatedField`` -> ``relation_single``
      (annotation finalized at the build site over the related primary
      ``DjangoType``);
    - ``FileField`` / ``ImageField`` -> ``file`` (``ImageField`` subclasses
      ``FileField``);
    - ``ListField`` -> ``list[<scalar child>]`` (recursive; a relation /
      nested-serializer child raises);
    - ``MultipleChoiceField`` -> ``list[str]`` (it subclasses ``ChoiceField`` so
      it must precede the scalar ``ChoiceField`` -> ``str``);
    - a nested ``Serializer`` / ``ListSerializer`` field raises (the nested-write
      non-goal);
    - then the scalar registry MRO walk;
    - else the fallthrough RAISES ``ConfigurationError`` naming the field + class.

    **Nullability (M2):** the annotation nullability the build site applies
    follows ``field.allow_null`` (orthogonal to requiredness); this converter
    returns the BASE (non-nullable) scalar annotation and the build site widens.
    ``allow_blank`` is not encoded.
    """
    del is_input  # graphene-parity, accepted-and-ignored (spec-039 SR-3).
    required = field.required

    def _relation_multi(_field: serializers.Field) -> SerializerFieldConversion:
        return SerializerFieldConversion(annotation=None, kind=RELATION_MULTI, required=required)

    def _relation_single(_field: serializers.Field) -> SerializerFieldConversion:
        return SerializerFieldConversion(annotation=None, kind=RELATION_SINGLE, required=required)

    def _file(_field: serializers.Field) -> SerializerFieldConversion:
        return SerializerFieldConversion(annotation=None, kind=FILE, required=required)

    def _list(field_: serializers.ListField) -> SerializerFieldConversion:
        return _list_child_conversion(field_)

    def _multiple_choice(_field: serializers.Field) -> SerializerFieldConversion:
        return SerializerFieldConversion(annotation=list[str], kind=SCALAR, required=required)

    def _nested(field_: serializers.Field) -> SerializerFieldConversion:
        # A nested ``Serializer`` / ``ListSerializer`` always raises; the handler
        # never returns, so the skeleton never falls through on it.
        _reject_nested_serializer(field_)
        raise AssertionError("unreachable")  # pragma: no cover - _reject_ always raises here.

    result = convert_with_mro(
        field,
        isinstance_prechecks=[
            # ``ManyRelatedField`` is the ``many=True`` relation wrapper;
            # ``RelatedField`` covers the single ``PrimaryKeyRelatedField``. Both
            # precede any scalar match. ``ListSerializer`` / ``Serializer`` reject
            # before ``ListField`` so a nested serializer is named, not list-mapped.
            ((serializers.BaseSerializer, serializers.ListSerializer), _nested),
            (serializers.ManyRelatedField, _relation_multi),
            (serializers.RelatedField, _relation_single),
            (serializers.FileField, _file),
            (serializers.ListField, _list),
            (serializers.MultipleChoiceField, _multiple_choice),
        ],
        scalar_registry=_SCALAR_SERIALIZER_FIELDS,
        fallthrough_error_factory=_unsupported_serializer_field,
    )
    if isinstance(result, SerializerFieldConversion):
        return result
    # The scalar registry MRO walk returned a bare annotation - wrap it as a
    # ``SCALAR``-kind conversion (``EmailField`` / ``SlugField`` / ``URLField`` /
    # ``RegexField`` under ``CharField``; ``UUIDField`` is its own entry).
    return SerializerFieldConversion(annotation=result, kind=SCALAR, required=required)


def _unsupported_serializer_field(field: serializers.Field) -> ConfigurationError:
    """Build the fail-loud ``ConfigurationError`` for an unmapped ``serializers.Field``.

    The fallthrough factory ``convert_with_mro`` raises when a field is matched by
    neither a precheck nor the scalar registry: an unregistered
    ``serializers.Field`` subclass with no supported ancestor (the graphene-django
    ``ImproperlyConfigured`` parity, raised as the package's own
    ``ConfigurationError``). The no-catch-all contract - raise, never silently
    coerce to ``String`` - lives in this wording.
    """
    return ConfigurationError(
        f"Unsupported serializer field type {type(field).__name__!r} on serializer "
        f"field {field.field_name!r}. convert_serializer_field has no mapping for it "
        "and no supported ancestor; register a supported base class, or drop it via "
        "Meta.fields / Meta.exclude.",
    )


def serializer_field_graphql_name(field_name: str, kind: str) -> tuple[str, str]:
    """Return ``(input_attr, graphql_name)`` for a serializer field by the id-like-suffix rule.

    The GraphQL name comes from the DECLARED serializer field name (NOT
    ``source``). For a relation the ``036`` ``<name>_id`` scheme applies, but with
    the id-like-suffix dedupe (spec-039 Decision 7 - the renamed-fields rule):

    - a non-relation scalar / file field camel-cases its declared name with no
      suffix (``full_name`` -> ``fullName``);
    - a single relation whose declared name already ENDS in an id-like suffix
      (``_id`` / ``_pk``) keeps that name (``category_id`` -> input attr
      ``category_id`` / ``categoryId``; ``category_pk`` -> ``category_pk`` /
      ``categoryPk``) so no doubled ``...IdId`` / ``...PkId`` is produced;
    - a single relation whose declared name has no id-like suffix gets the
      ``<name>_id`` scheme (``category`` -> ``category_id`` / ``categoryId``);
    - a multi relation keeps the plain declared name (it is already a collection
      of ids - ``cats`` -> ``cats`` / ``cats``), matching ``relation_input_annotation``.
    """
    if kind == RELATION_MULTI:
        return field_name, graphql_camel_name(field_name)
    if kind == RELATION_SINGLE:
        # No doubled ``...IdId`` / ``...PkId``: a declared name already ending in an
        # id-like suffix keeps that name; otherwise the ``036`` ``<name>_id`` scheme.
        input_attr = field_name if field_name.endswith(("_id", "_pk")) else f"{field_name}_id"
        return input_attr, graphql_camel_name(input_attr)
    return field_name, graphql_camel_name(field_name)


def backing_model_field(model: type[models.Model] | None, field: serializers.Field) -> Any:
    """Return the backing ``models.Field`` for a serializer field via its ``source``, or ``None``.

    For a ``ModelSerializer`` field over a concrete column, the backing
    ``models.Field`` is resolved through the field's ``source`` (one-segment or
    equal to the declared name), NOT its declared name - so a ``full_name =
    CharField(source="name")`` resolves the ``name`` column. The resolved column
    is what the build site hands to the read-side ``models.Field``-keyed
    converters (the symmetric wire contract).

    A serializer with no model (a plain ``Serializer``), or a field whose
    one-segment source names no concrete column (a serializer-only extra field),
    yields ``None`` - the caller routes it through the model-less path.

    **Dotted ``source`` / ``source="*"`` is rejected** for a model-column-converting
    field (spec-039 Decision 7 - the renamed-fields rule): a bound serializer field
    populates ``source_attrs`` as ``[]`` for ``source="*"`` and a multi-element list
    for a dotted ``source``; either traverses a nested attribute path that has no
    single backing column, so it fails loud rather than silently resolving the
    wrong column.
    """
    if model is None:
        return None
    source_attrs = getattr(field, "source_attrs", None)
    if source_attrs is not None and len(source_attrs) != 1:
        # ``source="*"`` -> ``[]``; dotted ``source="a.b"`` -> ``["a", "b"]``.
        raise ConfigurationError(
            f"Serializer field {field.field_name!r} declares a dotted source / source='*' "
            f"({field.source!r}); a model-column-backed field must map to a single "
            "concrete column (omit source, or use a one-segment source).",
        )
    source = field.source if field.source else field.field_name
    try:
        return model._meta.get_field(source)
    except FieldDoesNotExist:
        return None


def _require_relation_primary(field_name: str, related_model: type[models.Model]) -> type:
    """Return the related model's primary ``DjangoType``, raising if none is registered (M3).

    The serializer flavor is STRICTER than the form / model fallback (spec-039
    Decision 7 / M3): where ``relation_input_annotation`` falls back to the raw pk
    scalar when no primary ``DjangoType`` is registered for the related model, the
    serializer converter raises a class-creation ``ConfigurationError`` naming the
    field + target model. A serializer relation is meaningless without a typed
    target (the resolver must decode the id to a row of a known ``DjangoType``), so
    a missing primary is a build-time configuration error, not a silent raw-pk
    degrade. The form fallback is left byte-unchanged (its own non-goal).
    """
    primary = registry.get(related_model)
    if primary is None:
        raise ConfigurationError(
            f"Serializer relation field {field_name!r} targets model "
            f"{related_model.__name__!r}, which has no registered primary DjangoType. "
            "A serializer relation needs a typed target to decode its id; register a "
            "primary DjangoType for the target model, or drop the field via "
            "Meta.fields / Meta.exclude.",
        )
    return primary


def serializer_only_relation_annotation(field: serializers.Field, kind: str) -> tuple[str, Any]:
    """Map a column-LESS serializer relation field to its ``(python_attr, annotation)`` (F4).

    The serializer-flavor analog of
    ``forms/inputs.py::_model_less_relation_annotation``: a relation field with no
    backing model column (a relation on a plain ``Serializer``, or a relation
    whose ``source`` names no concrete column) resolves its related model from
    ``field.queryset.model`` (the single ``PrimaryKeyRelatedField``) or
    ``field.child_relation.queryset.model`` (a ``ManyRelatedField``). The id type
    follows the SAME Relay-``GlobalID``-vs-raw-pk rule as the model-backed path -
    ``relay.GlobalID`` when the related model's primary ``DjangoType`` is
    Relay-Node-shaped, else the related model's raw pk scalar.

    A relation with neither a backing column NOR a concrete ``queryset.model``
    (a ``read_only=True`` relation has no queryset, but read-only fields are
    dropped before this is reached; a queryset assigned only at request time is
    not visible at schema build) raises ``ConfigurationError`` naming the field -
    it cannot be typed.
    """
    related_field = field.child_relation if kind == RELATION_MULTI else field
    queryset = getattr(related_field, "queryset", None)
    related_model = getattr(queryset, "model", None)
    if related_model is None:
        raise ConfigurationError(
            f"Serializer relation field {field.field_name!r} has no backing model column "
            "and no concrete queryset.model at schema build, so its related model - and "
            "thus its id type - cannot be resolved. Declare it on a ModelSerializer over a "
            "relation column, or give it a concrete queryset "
            "(e.g. PrimaryKeyRelatedField(queryset=Model.objects.all())).",
        )
    primary = _require_relation_primary(field.field_name, related_model)
    if implements_relay_node(primary):
        id_scalar: Any = relay.GlobalID
    else:
        id_scalar = scalar_for_field(related_model._meta.pk)
    input_attr, _ = serializer_field_graphql_name(field.field_name, kind)
    if kind == RELATION_MULTI:
        return input_attr, list[id_scalar]
    return input_attr, id_scalar


def resolve_serializer_field(
    field: serializers.Field,
    model: type[models.Model] | None,
    type_name: str,
) -> tuple[str, Any, InputFieldSpec]:
    """Resolve one serializer field to its ``(python_attr, base_annotation, InputFieldSpec)``.

    The serializer-flavor analog of ``forms/inputs.py::_field_triple_and_spec``,
    extended with the ``source`` axis. A ``ModelSerializer`` field with a backing
    column (resolved via ``source``) routes through the read-side converters
    (keyed on the resolved ``models.Field``): a relation column ->
    ``relation_input_annotation`` (``<name>_id`` / the Relay-vs-raw-pk id type); a
    file/image column -> ``Upload``; else ``convert_scalar`` (the symmetric enum
    for ``choices``). A column-less field uses ``convert_serializer_field`` (the
    model-less table) for the kind, and the relation / file annotations are
    finalized here (where ``Upload`` and the serializer-only relation id-type are
    known).

    The GraphQL name is ALWAYS derived from the DECLARED serializer field name via
    the id-like-suffix rule (never ``source``). Returns the BASE (non-nullable)
    annotation; the create/partial requiredness + ``allow_null`` widening is
    applied by the caller. The returned ``InputFieldSpec`` records the reverse map
    the Slice 3 resolver consults - ``target_name`` is the DECLARED serializer
    field name (the ``validated_data`` key), ``source`` the resolved one-segment
    source.
    """
    field_name = field.field_name
    column = backing_model_field(model, field)
    # ``source`` axis: the resolved one-segment source (``None`` when it equals
    # the declared name - keeps the reverse map terse and form-symmetric).
    source = field.source if (field.source and field.source != field_name) else None

    if column is not None and getattr(column, "is_relation", False):
        # Model-backed relation: the read-side ``relation_input_annotation`` owns the
        # ``<column.name>_id`` attr + Relay-vs-raw-pk id type. The GraphQL name,
        # though, follows the DECLARED serializer name (id-like-suffix rule), so a
        # renamed ``category_pk = PrimaryKeyRelatedField(source="category")`` exposes
        # ``categoryPk`` while the column is resolved via ``source``.
        kind = RELATION_MULTI if getattr(column, "many_to_many", False) else RELATION_SINGLE
        # M3: the serializer flavor requires a registered primary DjangoType for
        # the target (stricter than the model fallback). Resolve + validate it
        # here, then hand it to ``relation_input_annotation`` so the id type is the
        # SAME Relay-vs-raw-pk decision the read side makes (a non-Relay target
        # still legitimately uses the raw pk - M3 forbids a MISSING primary, not a
        # non-Relay one).
        primary = _require_relation_primary(field_name, column.related_model)
        _, _, annotation = relation_input_annotation(column, related_primary_type=primary)
        python_attr, graphql_name = serializer_field_graphql_name(field_name, kind)
    elif column is not None and isinstance(column, (models.FileField, models.ImageField)):
        kind = FILE
        annotation = Upload
        python_attr, graphql_name = serializer_field_graphql_name(field_name, kind)
    elif column is not None:
        kind = SCALAR
        annotation = convert_scalar(column, type_name, force_nullable=False)
        python_attr, graphql_name = serializer_field_graphql_name(field_name, kind)
    else:
        # Column-less serializer field: the model-less converter owns the kind;
        # relation / file annotations are finalized here.
        conversion = convert_serializer_field(field)
        kind = conversion.kind
        if kind == FILE:
            annotation = Upload
            python_attr, graphql_name = serializer_field_graphql_name(field_name, kind)
        elif kind in (RELATION_SINGLE, RELATION_MULTI):
            python_attr, annotation = serializer_only_relation_annotation(field, kind)
            graphql_name = graphql_camel_name(python_attr)
        else:
            annotation = conversion.annotation
            python_attr, graphql_name = serializer_field_graphql_name(field_name, kind)

    spec = InputFieldSpec(
        input_attr=python_attr,
        graphql_name=graphql_name,
        target_name=field_name,
        kind=kind,
        source=source,
    )
    return python_attr, annotation, spec
