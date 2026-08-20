"""DRF serializer-field -> Strawberry input conversion + the per-input-field reverse map (spec-039).

The serializer-flavor analog of ``forms/converter.py`` (spec-038): a DRF
``serializers.Field``-keyed registry mapping each supported serializer field to
its Strawberry annotation + required-ness, in the graphene-django
``convert_serializer_field`` parity shape, raised through the package's own
``ConfigurationError``.

It is NOT a parallel copy of the read-side scalar table. Where a
``ModelSerializer`` field has a backing model column (resolved via the field's
``source``), the annotation routes through the read-side ``convert_scalar`` /
``convert_choices_to_enum`` / ``model_column_write_annotation`` at
``resolve_serializer_field`` (keyed on the resolved ``models.Field``),
so a ``choices`` column resolves to the SAME generated enum the read
``DjangoType`` synthesizes (the symmetric wire contract). The two key spaces -
DRF ``serializers.Field`` here, ``models.Field`` on the read side - stay strictly
separate.

**Fail-loud dispatch (spec-039 Decision 4).** Dispatch rides the shared
``utils/converters.py::convert_with_mro`` skeleton: ordered ``isinstance``
prechecks (relation / file / list / multi-choice kinds that must win before the
scalar registry MRO walk reaches a parent class), then the scalar registry MRO
walk, then a RAISING fallthrough. It is deliberately NOT ``functools.singledispatch``
with the graphene-django ``serializers.Field -> String`` catch-all, which would
shadow the raise so every custom field silently became ``String`` (the
``ImproperlyConfigured`` parity, lost). An unmapped ``serializers.Field`` subclass
raises ``ConfigurationError`` naming the field + class.

**The public converter registry.** The scalar registry the MRO
walk consults is a ``serializers.Field`` class -> converter-callable dict (each returns
a ``SerializerFieldConversion``), seeded with the built-in scalars + the expanded
capability matrix (``DictField`` / ``HStoreField`` -> ``JSON``; ``IPAddressField`` /
``FilePathField`` / ``DurationField`` -> ``str``; ``ModelField`` through its wrapped
column). ``register_serializer_field_converter(FieldClass, converter, *, override=False)``
is the SANCTIONED extension so a consumer supports their OWN DRF field without patching
the framework - the MRO walk then resolves it, while an UNregistered custom field still
hits the raising fallthrough (no silent ``String``). Mirrors the read-side
``types/converters.py::SCALAR_MAP`` mutable-module-dict hook. A serializer-only
``ChoiceField`` is upgraded to a generated GraphQL enum at the build site;
a consumer-declared serializer field whose scalar disagrees with its backing model
column's scalar fails loud rather than silently picking the column.

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
from collections.abc import Callable
from typing import Any

import strawberry
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from rest_framework import serializers

from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_type_name
from ..mutations.inputs import (
    annotate_queryset_relation,
    model_column_write_annotation,
    model_column_write_kind,
)
from ..registry import register_subsystem_clear, registry
from ..scalars import Upload
from ..types.converters import build_enum_from_choices, convert_scalar, scalar_for_field
from ..utils.converters import (
    convert_with_mro,
    finish_field_conversion,
    make_kind_converter,
    make_scalar_converter,
)

# The decode kinds the reverse-map record carries. The four base kinds are
# single-sourced in ``utils/inputs.py`` (one conceptual enum,
# not a per-flavor copy); re-exported here (the ``as`` form marks the explicit
# re-export) so the resolver + the tests keep addressing them on this
# module. ``NESTED_SINGLE`` / ``NESTED_MULTI`` are the serializer-only
# nested-serializer kinds: an EXPLICITLY-opted-in nested
# ``Serializer`` (single) / ``ListSerializer`` (many), whose recursion is owned
# by ``rest_framework/inputs.py`` (this converter module has no knowledge of
# the recursion; it only names the kinds + detects a nested field).
from ..utils.inputs import FILE as FILE
from ..utils.inputs import RELATION_MULTI as RELATION_MULTI
from ..utils.inputs import RELATION_SINGLE as RELATION_SINGLE
from ..utils.inputs import SCALAR as SCALAR
from ..utils.inputs import FieldConversionBase, InputFieldSpec
from ..utils.strings import graphql_camel_name, pascal_case

NESTED_SINGLE: str = "nested_single"
NESTED_MULTI: str = "nested_multi"


class SerializerFieldConversion(FieldConversionBase):
    """The annotation + decode kind + required-ness ``convert_serializer_field`` returns.

    The serializer-flavor analog of ``forms/converter.py::FormFieldConversion``.
    ``required`` is the serializer field's own ``field.required``; ``annotation``
    is the resolved Strawberry annotation for a SCALAR field (incl. ``list[...]``
    for a scalar ``ListField`` / ``MultipleChoiceField``). For a relation / file
    field the annotation is finalized at the ``rest_framework/inputs.py`` build
    site (where the backing column - if any - and the related primary
    ``DjangoType`` are known, so the Relay-``GlobalID``-vs-raw-pk id type can be
    resolved), so those kinds carry ``annotation=None`` here and only the ``kind``
    is authoritative. The ``(annotation, kind, required)`` value-object shape -
    including the ``kind=SCALAR`` default a consumer-registered converter
    relies on - is the shared
    ``utils/inputs.py::FieldConversionBase``.
    """

    __slots__ = ()


SerializerFieldConverter = Callable[[serializers.Field], SerializerFieldConversion]


def _scalar_converter(annotation: Any) -> SerializerFieldConverter:
    """Return a converter emitting a ``SCALAR``-kind conversion for a fixed annotation.

    Thin flavor wrapper around ``make_scalar_converter``: requiredness is
    ``field.required`` (the serializer default). The form table passes
    ``required_of=form_field_required`` instead (NullBoolean). The built-in
    scalar entries are CONVERTERS (not bare annotations) so the ONE registry
    the MRO walk consults holds a uniform ``field -> SerializerFieldConversion``
    shape for both built-in and consumer-registered fields.
    """
    return make_scalar_converter(SerializerFieldConversion, annotation)


def _model_field_converter(field: serializers.Field) -> SerializerFieldConversion:
    """Map ``serializers.ModelField`` through its wrapped Django ``model_field``.

    A ``ModelField`` proxies a concrete Django model field for (de)serialization; its
    GraphQL scalar is that wrapped field's scalar, resolved through the shared read-side
    ``scalar_for_field`` MRO walk - so a ``ModelField`` over an unsupported column fails
    loud THERE (never a silent ``String``), and a ``ModelField`` with no wrapped
    ``model_field`` cannot be typed and fails loud here.
    """
    model_field = getattr(field, "model_field", None)
    if model_field is None:
        raise ConfigurationError(
            f"Serializer field {field.field_name!r} is a ModelField with no wrapped model_field; "
            "it has no concrete column to resolve a GraphQL scalar from. Drop it via "
            "Meta.fields / Meta.exclude, or give it a model_field.",
        )
    return SerializerFieldConversion(
        annotation=scalar_for_field(model_field),
        kind=SCALAR,
        required=field.required,
    )


# The built-in converters seeded into the live registry. Every entry is EXPLICIT (the
# no-catch-all contract, ``GOAL.md``): the expanded rows (``DictField`` /
# ``IPAddressField`` / ``FilePathField`` / ``DurationField`` / ``ModelField``) are each a
# deliberate mapping, never an accidental fallthrough. ``DurationField`` -> ``str`` is a
# DELIBERATE scalar (DRF renders a duration as an ISO-8601-ish string on the wire + parses
# it back at validation), NOT an accidental string. ``DictField`` -> ``JSON`` also covers
# ``HStoreField`` (a ``DictField`` subclass) through the MRO walk; ``IPAddressField`` and
# ``FilePathField`` are ``CharField`` / ``ChoiceField`` subclasses whose explicit entries
# keep them ``str`` (``FilePathField``'s explicit ``str`` also keeps its dynamic
# filesystem-path choices OUT of the serializer-only choice-enum path).
_BUILTIN_SCALAR_CONVERTERS: dict[type[serializers.Field], SerializerFieldConverter] = {
    serializers.CharField: _scalar_converter(str),
    serializers.ChoiceField: _scalar_converter(str),
    serializers.IntegerField: _scalar_converter(int),
    serializers.FloatField: _scalar_converter(float),
    serializers.DecimalField: _scalar_converter(decimal.Decimal),
    serializers.BooleanField: _scalar_converter(bool),
    serializers.UUIDField: _scalar_converter(uuid.UUID),
    serializers.DateTimeField: _scalar_converter(datetime.datetime),
    serializers.DateField: _scalar_converter(datetime.date),
    serializers.TimeField: _scalar_converter(datetime.time),
    serializers.JSONField: _scalar_converter(strawberry.scalars.JSON),
    serializers.DictField: _scalar_converter(strawberry.scalars.JSON),
    serializers.IPAddressField: _scalar_converter(str),
    serializers.FilePathField: _scalar_converter(str),
    serializers.DurationField: _scalar_converter(str),
    serializers.ModelField: _model_field_converter,
}

# The LIVE registry (built-ins + consumer registrations), the MRO-walk target in
# ``convert_serializer_field``. Seeded from the built-ins; ``register_serializer_field_converter``
# mutates it. Like the read-side ``SCALAR_MAP`` it is a mutable module dict (a module
# reload re-seeds it), so a consumer registration persists for the process and is NOT
# reset by ``registry.clear()``.
_SERIALIZER_FIELD_CONVERTERS: dict[type, SerializerFieldConverter] = dict(
    _BUILTIN_SCALAR_CONVERTERS,
)


_CONVERT_RELATION_MULTI = make_kind_converter(SerializerFieldConversion, RELATION_MULTI)
_CONVERT_RELATION_SINGLE = make_kind_converter(SerializerFieldConversion, RELATION_SINGLE)
_CONVERT_FILE = make_kind_converter(SerializerFieldConversion, FILE)
_CONVERT_MULTIPLE_CHOICE = make_kind_converter(
    SerializerFieldConversion,
    SCALAR,
    annotation=list[str],
)


def register_serializer_field_converter(
    field_class: type,
    converter: SerializerFieldConverter,
    *,
    override: bool = False,
) -> None:
    """Register a converter for a consumer DRF ``serializers.Field`` subclass.

    The sanctioned extension so a consumer supports their OWN DRF field WITHOUT patching
    the framework, keeping the fail-loud no-catch-all guarantee: after registration the
    ``convert_serializer_field`` MRO walk resolves ``field_class`` (and its unregistered
    subclasses) to ``converter``, while an UNregistered custom field still raises.
    ``converter`` is a ``callable(field) -> SerializerFieldConversion`` returning the SAME
    structured shape the built-in converters return (``SerializerFieldConversion(
    annotation=<scalar>, required=field.required)`` - ``kind`` defaults to ``SCALAR``).
    ``field_class`` must be a ``serializers.Field`` subclass; re-registering an
    already-registered class raises unless ``override=True`` (a typo / double registration
    fails loud rather than silently shadowing).

    Mirrors the read-side ``types/converters.py::SCALAR_MAP`` extension hook (a mutable
    module dict); the registration persists for the process.
    """
    if not (isinstance(field_class, type) and issubclass(field_class, serializers.Field)):
        raise ConfigurationError(
            "register_serializer_field_converter: field_class must be a serializers.Field "
            f"subclass; got {field_class!r}.",
        )
    if not callable(converter):
        raise ConfigurationError(
            f"register_serializer_field_converter: converter for {field_class.__name__!r} must be "
            f"a callable(field) -> SerializerFieldConversion; got {converter!r}.",
        )
    if field_class in _SERIALIZER_FIELD_CONVERTERS and not override:
        raise ConfigurationError(
            f"A serializer-field converter is already registered for {field_class.__name__!r}; "
            "pass override=True to replace it, or register a distinct subclass.",
        )
    _SERIALIZER_FIELD_CONVERTERS[field_class] = converter


# Serializer-only ``ChoiceField`` generated enums, keyed by the
# descriptor-derived enum name so two inputs referencing the SAME serializer-only choice
# field share ONE enum object (Strawberry rejects two distinct types under one GraphQL
# name). Reset by ``registry.clear()`` via the registered subsystem clear so a fresh
# finalize re-emits (the parked-globals discipline the input namespaces use). The
# read-side model-choice enums live in ``registry`` keyed by ``(model, field_name)``; a
# serializer-only choice has no model, so it needs this separate name-keyed cache.
_SERIALIZER_CHOICE_ENUMS: dict[str, type] = {}


def clear_serializer_choice_enums() -> None:
    """Reset the serializer-only choice-enum cache for a fresh build (the registered clear)."""
    _SERIALIZER_CHOICE_ENUMS.clear()


register_subsystem_clear(clear_serializer_choice_enums, owner="rest_framework.choice_enums")


def is_nested_serializer_field(field: serializers.Field) -> bool:
    """Return whether ``field`` is a nested ``Serializer`` / ``ListSerializer``.

    A nested ``Serializer`` / ``ModelSerializer`` field (single) or a
    ``ListSerializer`` (a ``many=True`` nested serializer) - both are
    ``serializers.BaseSerializer`` subclasses. Used by ``rest_framework/inputs.py`` to tell an
    EXPLICITLY-opted-in nested field (``Meta.nested_fields``) apart from a scalar / relation /
    file field BEFORE calling ``resolve_serializer_field`` (which still rejects an
    un-opted-in nested field via ``_reject_nested_serializer``).
    """
    return isinstance(field, serializers.BaseSerializer)


def nested_serializer_child(
    field: serializers.Field,
) -> tuple[serializers.BaseSerializer, bool]:
    """Return ``(child_serializer_instance, many)`` for a nested serializer field.

    A ``ListSerializer`` (``many=True``) carries the item serializer on ``.child`` and is
    ``many=True``; a plain nested ``Serializer`` / ``ModelSerializer`` IS the item serializer and
    is ``many=False``. The returned instance is BOUND (its ``.fields`` are the nested input's
    schema-time field map), which the recursive nested build in ``rest_framework/inputs.py``
    walks with the SAME machinery the top level uses.
    """
    if isinstance(field, serializers.ListSerializer):
        return field.child, True
    return field, False


def _reject_nested_serializer(field: serializers.Field) -> None:
    """Raise if ``field`` is a nested ``Serializer`` / ``ListSerializer`` NOT explicitly opted in.

    Nested serializer writes are OPT-IN ONLY: a ``Serializer`` /
    ``ModelSerializer`` field or a ``ListSerializer`` (a ``many=True`` nested serializer) has no
    flat scalar / id input shape, so - UNLESS the mutation EXPLICITLY declares it in
    ``Meta.nested_fields`` (handled in ``rest_framework/inputs.py`` before this converter is
    reached) - it fails loud here rather than silently degrading. The opt-in nested build lives
    in the ``inputs.py`` walk (which never routes an opted-in nested field through this
    converter); this raise is the fail-loud default for an un-opted-in nested field.
    """
    if isinstance(field, serializers.BaseSerializer):
        raise ConfigurationError(
            f"Serializer field {field.field_name!r} is a nested "
            f"{type(field).__name__}; nested serializer writes are opt-in only. Declare it in the "
            f"mutation's Meta.nested_fields ({{{field.field_name!r}: NestedSerializerConfig(...)}}) - "
            "the serializer must implement create()/update() for the nested write - drop it via "
            "Meta.fields / Meta.exclude, or model the relation with a PrimaryKeyRelatedField.",
        )


def _reject_unsupported_relation_field(field: serializers.Field) -> None:
    """Raise unless ``field`` is a PK relation (spec-039 Decision 7).

    The package types every relation input as a ``GlobalID`` / raw-pk that decodes
    to a PRIMARY KEY, so only ``serializers.PrimaryKeyRelatedField`` (single) and a
    ``serializers.ManyRelatedField`` whose ``child_relation`` is a
    ``PrimaryKeyRelatedField`` (``many=True``) have matching decode semantics. A
    ``SlugRelatedField`` / ``HyperlinkedRelatedField`` / custom writable
    ``RelatedField`` expects a slug / URL / custom representation, NOT a pk -
    accepting it would emit a GraphQL contract that silently misdecodes (a decoded
    pk fed into a slug-expecting field). It fails loud here (the package's
    no-silent-degrade contract, ``GOAL.md``) until the spec defines an input shape +
    decode for those kinds. ``read_only`` relations are dropped before this is
    reached, so only a WRITABLE non-PK relation raises.
    """
    if isinstance(field, serializers.ManyRelatedField):
        child = field.child_relation
        if not isinstance(child, serializers.PrimaryKeyRelatedField):
            raise ConfigurationError(
                f"Serializer field {field.field_name!r} is a ManyRelatedField wrapping a "
                f"{type(child).__name__}; only PrimaryKeyRelatedField(many=True) is supported "
                "(the relation input decodes to a primary key). A slug / URL / custom related "
                "field has no pk-based input shape - drop it via Meta.fields / Meta.exclude, or "
                "model the relation with PrimaryKeyRelatedField(many=True).",
            )
        return
    if isinstance(field, serializers.RelatedField) and not isinstance(
        field,
        serializers.PrimaryKeyRelatedField,
    ):
        raise ConfigurationError(
            f"Serializer relation field {field.field_name!r} is a {type(field).__name__}; only "
            "PrimaryKeyRelatedField is supported (the relation input decodes to a primary key). "
            "A slug / URL / custom related field has no pk-based input shape - drop it via "
            "Meta.fields / Meta.exclude, or use a PrimaryKeyRelatedField.",
        )


def _list_child_conversion(field: serializers.ListField) -> SerializerFieldConversion:
    """Map a ``ListField`` to ``list[<scalar child>]``, or raise for a non-scalar child.

    A ``ListField(child=IntegerField())`` becomes ``list[int]`` by recursing the
    child through the SAME scalar registry. A relation / nested-serializer child
    raises ``ConfigurationError`` (the spec-039 contract: only a scalar
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


def _finish_serializer_conversion(
    result: Any,
    field: serializers.Field,
) -> SerializerFieldConversion:
    """Finish one registry result and enforce the scalar-extension boundary.

    Built-in kind prechecks return a finished conversion directly. Scalar registry entries,
    including consumer registrations, return callables; a malformed extension must fail as a
    typed configuration error rather than leaking ``AttributeError`` later from the input
    builder. A registered scalar converter also cannot smuggle a relation / file kind through
    the scalar registry, because those kinds require the framework-owned prechecks and build-site
    metadata.
    """
    if isinstance(result, SerializerFieldConversion):
        return result
    try:
        conversion = finish_field_conversion(result, field)
    except ConfigurationError:
        raise
    except Exception as exc:
        raise ConfigurationError(
            f"Registered serializer-field converter for {_safe_type_name(field)!r} on field "
            f"{_safe_arg_repr(getattr(field, 'field_name', None))} raised "
            f"{_safe_type_name(exc)} while converting the field.",
        ) from exc
    if not isinstance(conversion, SerializerFieldConversion):
        raise ConfigurationError(
            f"Registered serializer-field converter for {_safe_type_name(field)!r} on field "
            f"{_safe_arg_repr(getattr(field, 'field_name', None))} must return "
            f"SerializerFieldConversion; got {_safe_type_name(conversion)}.",
        )
    if conversion.kind != SCALAR:
        raise ConfigurationError(
            f"Registered serializer-field converter for {_safe_type_name(field)!r} on field "
            f"{_safe_arg_repr(getattr(field, 'field_name', None))} must return a scalar "
            f"conversion; got kind {conversion.kind!r}.",
        )
    return conversion


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

    Dispatch rides the shared ``utils/converters.py::convert_with_mro`` skeleton:
    the relation / file / list / multi-choice prechecks run
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

    **Nullability:** the annotation nullability the build site applies
    follows ``field.allow_null`` (orthogonal to requiredness); this converter
    returns the BASE (non-nullable) scalar annotation and the build site widens.
    ``allow_blank`` is not encoded.
    """
    del is_input  # graphene-parity, accepted-and-ignored.

    def _relation_multi(field_: serializers.Field) -> SerializerFieldConversion:
        # H5: only PrimaryKeyRelatedField(many=True) (a ManyRelatedField of a PK
        # child) is a supported relation input; a non-PK child raises here.
        _reject_unsupported_relation_field(field_)
        return _CONVERT_RELATION_MULTI(field_)

    def _relation_single(field_: serializers.Field) -> SerializerFieldConversion:
        # H5: only PrimaryKeyRelatedField is a supported single relation input; a
        # SlugRelatedField / HyperlinkedRelatedField / custom RelatedField raises.
        _reject_unsupported_relation_field(field_)
        return _CONVERT_RELATION_SINGLE(field_)

    def _list(field_: serializers.ListField) -> SerializerFieldConversion:
        return _list_child_conversion(field_)

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
            (serializers.FileField, _CONVERT_FILE),
            (serializers.ListField, _list),
            (serializers.MultipleChoiceField, _CONVERT_MULTIPLE_CHOICE),
        ],
        scalar_registry=_SERIALIZER_FIELD_CONVERTERS,
        fallthrough_error_factory=_unsupported_serializer_field,
    )
    return _finish_serializer_conversion(result, field)


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
        f"Unsupported serializer field type {_safe_type_name(field)!r} on serializer "
        f"field {field.field_name!r}. convert_serializer_field has no mapping for it "
        "and no supported ancestor; register a supported base class, or drop it via "
        "Meta.fields / Meta.exclude.",
    )


def _relation_cardinality(field: serializers.Field) -> bool:
    """Return whether a DRF relation field validates a collection of related objects."""
    return isinstance(field, serializers.ManyRelatedField)


def _model_relation_cardinality(field: models.Field) -> bool:
    """Return whether a Django relation field exposes a collection-valued side."""
    return bool(
        getattr(field, "many_to_many", False) or getattr(field, "one_to_many", False),
    )


def _reject_relation_cardinality_mismatch(field: serializers.Field, column: models.Field) -> None:
    """Reject a serializer relation whose collection shape disagrees with its model relation.

    ``resolve_serializer_field`` otherwise selected cardinality from the Django column while
    DRF validated cardinality from the serializer field. A consumer can legally declare
    ``PrimaryKeyRelatedField(many=True, source="category")`` over a foreign key; without this
    guard the schema emits one scalar id while DRF requires a list (and the inverse mismatch
    emits a list while DRF requires one id). The generated input must describe the same shape
    the runtime serializer validates.
    """
    serializer_many = _relation_cardinality(field)
    model_many = _model_relation_cardinality(column)
    if serializer_many == model_many:
        return
    expected = "many=True" if model_many else "a single related object"
    actual = "many=True" if serializer_many else "a single related object"
    raise ConfigurationError(
        f"Serializer relation field {field.field_name!r} has a cardinality mismatch: it declares "
        f"{actual}, but its backing model relation {column.model.__name__}.{column.name} "
        f"requires {expected}. Align the "
        "serializer relation's many= shape with the model relation, or map the field to a "
        "serializer-only target with an explicit queryset.",
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


def serializer_field_description(field: serializers.Field) -> str | None:
    """Return a GraphQL input-field description from a DRF field's metadata, or ``None``.

    Threads DRF validation metadata into the SDL as DOCUMENTATION (never a second
    validator - runtime validation stays in DRF): ``field.help_text`` becomes the
    description head, and a coherent constraint summary (``min_length`` / ``max_length`` /
    ``min_value`` / ``max_value``, plus ``allow_blank`` when permitted and ``allow_empty``
    when forbidden) is appended. A field with neither help text nor constraints yields
    ``None`` (no description emitted, so ``build_strawberry_input_class`` leaves the field
    undescribed). Graphene-django threads only ``help_text``; this surfaces the DRF
    validation summary too without changing coercion semantics.
    """
    try:
        parts: list[str] = []
        help_text = getattr(field, "help_text", None)
        if help_text:
            parts.append(str(help_text))
        facts: list[str] = []
        for attr in (
            "min_length",
            "max_length",
            "min_value",
            "max_value",
        ):
            value = getattr(field, attr, None)
            if value is not None:
                facts.append(f"{attr}={value}")
        if getattr(field, "allow_blank", False):
            facts.append("allow_blank=true")
        if getattr(field, "allow_empty", None) is False:
            facts.append("allow_empty=false")
        if facts:
            parts.append("Constraints: " + ", ".join(facts) + ".")
        return " ".join(parts) if parts else None
    except BaseException as exc:
        try:
            field_name = _safe_arg_repr(getattr(field, "field_name", None))
        except BaseException:
            field_name = "<unavailable>"
        raise ConfigurationError(
            f"Serializer field {field_name} has metadata that cannot be rendered as a GraphQL "
            "description.",
        ) from exc


def require_one_segment_source(
    field: serializers.Field,
    *,
    field_label: str,
    must_map_to: str,
) -> None:
    """Raise if a bound field's ``source`` is dotted or ``source='*'``.

    Bound DRF fields populate ``source_attrs`` as ``[]`` for ``source="*"`` and a
    multi-element list for a dotted ``source``. Either has no single write-back
    attribute, so every schema-time path that needs one segment (model-column
    resolve and opted-in nested writes) routes through this helper - the one
    detection of the fail-loud one-segment source policy (spec-039 Decision 7 /
    ). ``field_label`` / ``must_map_to`` keep the diagnostic nouns at
    each call site (column vs nested write) without a second predicate copy.
    """
    source_attrs = getattr(field, "source_attrs", None)
    if source_attrs is not None and len(source_attrs) != 1:
        # ``source="*"`` -> ``[]``; dotted ``source="a.b"`` -> ``["a", "b"]``.
        raise ConfigurationError(
            f"{field_label} declares a dotted source / source='*' "
            f"({field.source!r}); {must_map_to} (omit source, or "
            "use a one-segment source).",
        )


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
    field (spec-039 Decision 7 - the renamed-fields rule) via
    ``require_one_segment_source``: either form traverses a nested attribute path
    that has no single backing column, so it fails loud rather than silently
    resolving the wrong column.
    """
    if model is None:
        return None
    require_one_segment_source(
        field,
        field_label=f"Serializer field {field.field_name!r}",
        must_map_to="a model-column-backed field must map to a single concrete column",
    )
    source = field.source if field.source else field.field_name
    try:
        return model._meta.get_field(source)
    except FieldDoesNotExist:
        return None


def _require_relation_primary(field_name: str, related_model: type[models.Model]) -> type:
    """Return the related model's primary ``DjangoType``, raising if none is registered.

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


def serializer_only_relation_annotation(
    field: serializers.Field,
    kind: str,
) -> tuple[str, Any, type[models.Model]]:
    """Map a column-LESS serializer relation field to ``(python_attr, annotation, related_model)``.

    The serializer-flavor analog of
    ``forms/inputs.py::_model_less_relation_annotation``: a relation field with no
    backing model column (a relation on a plain ``Serializer``, or a relation
    whose ``source`` names no concrete column) resolves its related model from
    ``field.queryset.model`` (the single ``PrimaryKeyRelatedField``) or
    ``field.child_relation.queryset.model`` (a ``ManyRelatedField``). The id type
    rides ``annotate_queryset_relation`` after ``_require_relation_primary`` (spec-039 M3:
    a missing primary is a class-creation error, not a raw-pk fallback).

    A relation with neither a backing column NOR a concrete ``queryset.model``
    (a ``read_only=True`` relation has no queryset, but read-only fields are
    dropped before this is reached; a queryset assigned only at request time is
    not visible at schema build) raises ``ConfigurationError`` naming the field -
    it cannot be typed.
    """
    related_field = field.child_relation if kind == RELATION_MULTI else field
    many = kind == RELATION_MULTI
    input_attr, _ = serializer_field_graphql_name(field.field_name, kind)
    return annotate_queryset_relation(
        getattr(related_field, "queryset", None),
        many=many,
        python_attr=input_attr,
        primary_of=lambda model: _require_relation_primary(field.field_name, model),
        missing=lambda: ConfigurationError(
            f"Serializer relation field {field.field_name!r} has no backing model column "
            "and no concrete queryset.model at schema build, so its related model - and "
            "thus its id type - cannot be resolved. Declare it on a ModelSerializer over a "
            "relation column, or give it a concrete queryset "
            "(e.g. PrimaryKeyRelatedField(queryset=Model.objects.all())).",
        ),
    )


def _is_consumer_declared(field: serializers.Field) -> bool:
    """Return whether ``field`` was EXPLICITLY declared on its serializer (not auto-generated).

    DRF's ``SerializerMetaclass`` records explicitly-declared fields in the serializer
    class's ``_declared_fields``; ``ModelSerializer`` AUTO-generates the rest from
    ``Meta.fields``. A field bound to a serializer carries ``field.parent`` (the serializer
    instance), so its declared-ness is ``field.field_name in
    type(field.parent)._declared_fields``. An unbound field (no ``parent``) is treated as
    not-declared (the auto-generated default). This is the signal the type-override conflict
    policy uses to tell a consumer's EXPLICIT serializer contract from a
    model-backed auto-generated field.
    """
    parent = getattr(field, "parent", None)
    if parent is None:
        return False
    return field.field_name in getattr(type(parent), "_declared_fields", {})


def _scalar_name(scalar: Any) -> str:
    """Return a readable name for a scalar annotation (for the conflict diagnostic)."""
    return getattr(scalar, "__name__", None) or repr(scalar)


def _model_backed_scalar_annotation(
    field: serializers.Field,
    column: models.Field,
    type_name: str,
) -> Any:
    """Resolve a model-backed serializer SCALAR under the type-override conflict policy.

    An AUTO-generated ``ModelSerializer`` field routes through the read-side
    ``convert_scalar`` (so a ``choices`` column resolves to the SAME enum the read
    ``DjangoType`` synthesizes - the symmetric wire contract, and the model-backed
    enum-reuse keeps).

    A CONSUMER-DECLARED field is an EXPLICIT serializer contract, so its declared scalar
    must AGREE with the model column's scalar; a disagreement (``count =
    IntegerField(source="a_char_col")`` - int vs str) FAILS LOUD naming the field, its
    ``source``, and both scalars rather than silently picking the model column (the
    graphene-django trap this improves on). The ``source`` is in the diagnostic so a benign
    rename (``display_name = CharField(source="name")`` - str vs str, agrees) is trivially
    told apart from a true type mismatch. A ``choices`` column keeps the enum symmetry (both
    sides intend the enum), so the check is skipped there; a consumer-declared field whose
    serializer converter is not a plain scalar defers to the model converter (its own guards
    apply).

    **Declared choices are a schema-affecting override.** A CONSUMER-DECLARED
    ``ChoiceField`` / ``MultipleChoiceField`` (even ``source``-mapped to a plain model column)
    emits the GENERATED serializer-only enum from its DECLARED choices, rather than collapsing
    back to the column's scalar (``String``) - the declared choices are part of the public
    mutation contract, so they must survive (never silently lost).
    """
    if _is_consumer_declared(field) and _is_enumerable_serializer_choice(field):
        return _serializer_choice_annotation(field, type_name)
    model_annotation = convert_scalar(column, type_name, force_nullable=False)
    if not _is_consumer_declared(field) or column.choices:
        return model_annotation
    serializer_conversion = convert_serializer_field(field)
    if serializer_conversion.kind != SCALAR or serializer_conversion.annotation is None:
        return model_annotation
    model_scalar = scalar_for_field(column)
    serializer_scalar = serializer_conversion.annotation
    if serializer_scalar != model_scalar:
        raise ConfigurationError(
            f"Serializer field {field.field_name!r} (source {column.name!r}) declares a GraphQL "
            f"scalar {_scalar_name(serializer_scalar)} that disagrees with the backing model "
            f"column {column.model.__name__}.{column.name}'s scalar {_scalar_name(model_scalar)}. "
            "A consumer-declared serializer field is an explicit contract; the framework will not "
            "silently pick the model column. Align the serializer field's type with the column, "
            "declare it as a serializer-only field (no backing column), or drop it via "
            "Meta.fields / Meta.exclude.",
        )
    return model_annotation


def _is_enumerable_serializer_choice(field: serializers.Field) -> bool:
    """Return whether a serializer-only ``ChoiceField`` should generate a GraphQL enum.

    A serializer-only ``ChoiceField`` / ``MultipleChoiceField`` with static choices maps to
    a generated enum (schema precision over the graphene-django ``str``). A ``FilePathField``
    is EXCLUDED - it is a ``ChoiceField`` subclass whose choices are dynamic filesystem paths,
    not a stable GraphQL enum - staying the ``str`` its registry entry maps it to.
    Model-backed choice fields never reach here (they route through the read-side model-choice
    enum at the ``column is not None`` branch).
    """
    return isinstance(field, serializers.ChoiceField) and not isinstance(
        field,
        serializers.FilePathField,
    )


def _enum_member_map(enum_cls: type) -> dict[str, Any]:
    """Return an enum's ``{member_name: value}`` map (for the choice-enum collision check)."""
    return {member.name: member.value for member in enum_cls}


def _serializer_choice_enum(field: serializers.Field, type_name: str) -> type:
    """Build (or dedupe) the generated enum for a serializer-only ``ChoiceField``.

    Reuses the shared ``types/converters.py::build_enum_from_choices`` core (the SAME
    grouped-form / value-sanitization / sanitize-collision rules the read-side model enum
    applies), so a serializer-only choice enum cannot drift from a model-choice enum. DRF's
    ``ChoiceField.choices`` is a value -> display mapping (already flattened), so its
    ``.items()`` are the ``(value, label)`` pairs the builder expects. The enum is cached by
    its descriptor-derived name so two inputs referencing the same serializer-only choice
    field share ONE enum object (Strawberry rejects two distinct types under one GraphQL
    name); a name reused with a DIFFERENT member set fails loud rather than silently reusing
    the first.
    """
    enum_name = f"{type_name}{pascal_case(field.field_name)}Enum"
    enum_cls = build_enum_from_choices(
        list(field.choices.items()),
        enum_name,
        source_label=f"serializer field {field.field_name!r}",
    )
    cached = _SERIALIZER_CHOICE_ENUMS.get(enum_name)
    if cached is not None:
        if _enum_member_map(cached) != _enum_member_map(enum_cls):
            raise ConfigurationError(
                f"Serializer-only choice enum {enum_name!r} is generated with two different member "
                "sets across shapes; rename one serializer field so its generated enum name is "
                "unique, or align the choices.",
            )
        return cached
    _SERIALIZER_CHOICE_ENUMS[enum_name] = enum_cls
    return enum_cls


def _serializer_choice_annotation(field: serializers.Field, type_name: str) -> Any:
    """Return the generated enum annotation for an enumerable ``ChoiceField``.

    A ``ChoiceField`` -> a single generated enum; a ``MultipleChoiceField`` (a ``ChoiceField``
    subclass) -> ``list[<enum>]``. Shared by the column-less path
    (``_serializer_only_scalar_annotation``) and the model-backed path
    (``_model_backed_scalar_annotation``), so a declared choice field emits the SAME generated
    enum whether or not it maps to a model column.
    """
    enum_cls = _serializer_choice_enum(field, type_name)
    if isinstance(field, serializers.MultipleChoiceField):
        return list[enum_cls]
    return enum_cls


def _serializer_only_scalar_annotation(
    field: serializers.Field,
    conversion: SerializerFieldConversion,
    type_name: str,
) -> Any:
    """Resolve a column-less serializer SCALAR annotation, upgrading choices to enums.

    A serializer-only ``ChoiceField`` becomes a generated enum; a ``MultipleChoiceField``
    (a ``ChoiceField`` subclass, so its base conversion is ``list[str]``) becomes
    ``list[<enum>]``. Every other scalar keeps its converter annotation.
    """
    if not _is_enumerable_serializer_choice(field):
        return conversion.annotation
    return _serializer_choice_annotation(field, type_name)


def resolve_serializer_field(
    field: serializers.Field,
    model: type[models.Model] | None,
    type_name: str,
) -> tuple[str, Any, InputFieldSpec]:
    """Resolve one serializer field to its ``(python_attr, base_annotation, InputFieldSpec)``.

    The serializer-flavor analog of ``forms/inputs.py::_field_triple_and_spec``,
    extended with the ``source`` axis. A ``ModelSerializer`` field with a backing
    column (resolved via ``source``) routes through the read-side converters
    (keyed on the resolved ``models.Field``): kind via
    ``model_column_write_kind``; a relation / file column's annotation via
    ``model_column_write_annotation`` (Relay-vs-raw-pk id type / ``Upload``);
    a scalar via ``_model_backed_scalar_annotation`` (type-override conflict
    policy: a CONSUMER-DECLARED model-backed scalar whose declared type disagrees
    with the column's fails loud rather than silently picking the column). The
    GraphQL name is ALWAYS derived from the DECLARED serializer field name via
    the id-like-suffix rule (never ``source``). A column-less field uses
    ``convert_serializer_field`` (the model-less table) for the kind, and the
    relation / file annotations are finalized here (where ``Upload`` and the
    serializer-only relation id-type are known); a column-less ``ChoiceField`` /
    ``MultipleChoiceField`` is upgraded to a generated GraphQL enum.

    The GraphQL name is ALWAYS derived from the DECLARED serializer field name via
    the id-like-suffix rule (never ``source``). Returns the BASE (non-nullable)
    annotation; the create/partial requiredness + ``allow_null`` widening is
    applied by the caller. The returned ``InputFieldSpec`` records the reverse map
    the resolver consults - ``target_name`` is the DECLARED serializer
    field name (the ``validated_data`` key), ``source`` the resolved one-segment
    source.
    """
    # reject a nested serializer field FIRST, before the backing-column lookup - a
    # nested serializer over a reverse-relation column (``BranchSerializer.shelves``) would
    # otherwise be misrouted through the model-backed relation branch (silently typed as a
    # relation-id input) instead of failing loud. An EXPLICITLY-opted-in nested field never
    # reaches here (``inputs.py``'s walk routes it to the recursive nested build first); this
    # raise is the fail-loud default for an un-opted-in nested field.
    _reject_nested_serializer(field)
    field_name = field.field_name
    column = backing_model_field(model, field)
    # ``source`` axis: the resolved one-segment source (``None`` when it equals
    # the declared name - keeps the reverse map terse and form-symmetric).
    source = field.source if (field.source and field.source != field_name) else None
    # The relation target model recorded on the spec (``None`` for a non-relation),
    # so the decode reads it off the bind-stashed reverse map instead of
    # re-discovering the serializer field set per request.
    related_model: type[models.Model] | None = None

    if column is not None:
        # Model-backed field: ``model_column_write_kind`` is the one column
        # classifier (shared with ``model_column_input_annotation`` / form).
        # Relation / file annotations ride ``model_column_write_annotation``;
        # SCALAR keeps the type-override conflict policy. The GraphQL name
        # follows the DECLARED serializer name (id-like-suffix rule), so a
        # renamed ``category_pk = PrimaryKeyRelatedField(source="category")``
        # exposes ``categoryPk`` while the column is resolved via ``source``.
        kind = model_column_write_kind(column)
        if kind in (RELATION_SINGLE, RELATION_MULTI):
            # H5: only a PK relation (``PrimaryKeyRelatedField`` / ``ManyRelatedField``
            # of a PK child) decodes to a primary key, so a ``SlugRelatedField`` /
            # ``HyperlinkedRelatedField`` / custom related field over a relation column
            # fails loud here rather than silently misdecoding a pk into a slug-expecting
            # field.
            _reject_unsupported_relation_field(field)
            related_model = column.related_model
            _reject_relation_cardinality_mismatch(field, column)
            # spec-039 M3: the serializer flavor requires a registered primary DjangoType for
            # the target (stricter than the model fallback). Resolve + validate it
            # via ``primary_of`` so the id type is the SAME Relay-vs-raw-pk decision
            # the read side makes (a non-Relay target still legitimately uses the
            # raw pk - M3 forbids a MISSING primary, not a non-Relay one).
            annotation = model_column_write_annotation(
                column,
                type_name,
                primary_of=lambda model: _require_relation_primary(field_name, model),
                kind=kind,
            )
        elif kind == FILE:
            annotation = model_column_write_annotation(
                column,
                type_name,
                primary_of=lambda _model: None,
                kind=kind,
            )
        else:
            annotation = _model_backed_scalar_annotation(field, column, type_name)
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
            python_attr, annotation, related_model = serializer_only_relation_annotation(
                field,
                kind,
            )
            graphql_name = graphql_camel_name(python_attr)
        else:
            # #6: a serializer-only ``ChoiceField`` / ``MultipleChoiceField`` is upgraded
            # to a generated GraphQL enum here (the build site owns ``type_name``); every
            # other scalar keeps its converter annotation.
            annotation = _serializer_only_scalar_annotation(field, conversion, type_name)
            python_attr, graphql_name = serializer_field_graphql_name(field_name, kind)

    spec = InputFieldSpec(
        input_attr=python_attr,
        graphql_name=graphql_name,
        target_name=field_name,
        kind=kind,
        source=source,
        related_model=related_model,
    )
    return python_attr, annotation, spec
