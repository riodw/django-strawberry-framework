"""Converter tests for the DRF serializer-field -> Strawberry annotation registry (spec-039 Slice 1).

Covers ``django_strawberry_framework/rest_framework/serializer_converter.py``:

- ``convert_serializer_field`` scalar mappings + required-ness for every supported
  ``serializers.Field`` class (text-like -> ``str`` via the MRO walk, the numeric /
  temporal / uuid / json / list / multi-choice cases);
- the fail-loud dispatch: a custom ``serializers.Field`` subclass with no supported
  ancestor raises ``ConfigurationError`` (the load-bearing no-catch-all assertion -
  no silent ``String`` fallback), and a nested serializer / a relation-child
  ``ListField`` raise;
- the relation / file kind flags the input builder finalizes;
- the renamed-field reverse map (declared name -> GraphQL name; backing column via
  ``source``; declared name preserved as ``target_name``), the id-like-suffix rule,
  the dotted-``source`` rejection, the serializer-only relation (``queryset.model``),
  and the M3 missing-primary-DjangoType raise.

The relation id-type (Relay-``GlobalID`` vs raw pk, single + multi) is pinned at
the ``resolve_serializer_field`` build site over a real model's primary
``DjangoType``; those assertions live here (where the converter resolves the id)
and in ``test_inputs.py`` (where the built input field's type is asserted).

System-under-test runs against the products ``Item`` / ``Category`` fixtures per
``AGENTS.md`` (and package-local Relay / non-Relay target ``DjangoType``s).
"""

from __future__ import annotations

import datetime
import decimal
import itertools
import uuid
from enum import Enum
from typing import get_args, get_origin

import pytest
import strawberry
from apps.products import models as product_models
from django.db import models
from rest_framework import serializers
from strawberry import relay

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework import serializer_converter
from django_strawberry_framework.rest_framework.serializer_converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    SerializerFieldConversion,
    backing_model_field,
    convert_serializer_field,
    register_serializer_field_converter,
    resolve_serializer_field,
    serializer_field_graphql_name,
    serializer_only_relation_annotation,
)


@pytest.fixture
def _restore_converter_registry():
    """Snapshot + restore the module converter registry so a test registration cannot leak.

    The serializer-field converter registry (spec-039 rev6 #11) mirrors the read-side
    ``SCALAR_MAP``: a mutable module dict NOT reset by ``registry.clear()``, so a test
    that registers a converter restores the snapshot on teardown.
    """
    snapshot = dict(serializer_converter._SERIALIZER_FIELD_CONVERTERS)
    yield
    serializer_converter._SERIALIZER_FIELD_CONVERTERS.clear()
    serializer_converter._SERIALIZER_FIELD_CONVERTERS.update(snapshot)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry so each test's products / fixture ``DjangoType``s start clean."""
    registry.clear()
    yield
    registry.clear()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_serializer_converter__{next(_app_label_counter)}"


def _bind(field: serializers.Field, name: str) -> serializers.Field:
    """Bind a serializer field (DRF populates ``field_name`` / ``source`` / ``source_attrs``).

    The schema-time discovery reads bound fields (DRF binds during ``.fields``
    materialization), so the converter's ``source``-axis / ``field_name`` reads
    require a bound field. Direct converter tests bind explicitly.
    """
    field.bind(name, None)
    return field


def _register_products_types() -> None:
    """Register non-Relay ``DjangoType``s for products ``Item`` / ``Category``."""

    class CategoryType(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")


def _make_relay_target():
    """A registered Relay-Node-shaped ``DjangoType`` over a fresh model."""

    class RelayTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = _unique_app_label()

    class RelayTargetType(DjangoType, relay.Node):
        class Meta:
            model = RelayTarget
            fields = ("id", "name")

    return RelayTarget, RelayTargetType


# ---------------------------------------------------------------------------
# Scalar field annotations + required-ness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        (serializers.CharField(), str),
        (serializers.EmailField(), str),
        (serializers.SlugField(), str),
        (serializers.URLField(), str),
        (serializers.RegexField(regex=r".*"), str),
        (serializers.ChoiceField(choices=["a", "b"]), str),
        (serializers.IntegerField(), int),
        (serializers.FloatField(), float),
        (serializers.DecimalField(max_digits=5, decimal_places=2), decimal.Decimal),
        (serializers.BooleanField(), bool),
        (serializers.UUIDField(), uuid.UUID),
        (serializers.DateField(), datetime.date),
        (serializers.DateTimeField(), datetime.datetime),
        (serializers.TimeField(), datetime.time),
        (serializers.JSONField(), strawberry.scalars.JSON),
    ],
)
def test_scalar_field_annotations(field, expected):
    """Each supported scalar serializer field maps to its Strawberry annotation, kind ``scalar``."""
    conversion = convert_serializer_field(_bind(field, "f"))
    assert conversion.annotation == expected
    assert conversion.kind == SCALAR


def test_required_ness_reflects_field_required():
    """``required`` mirrors ``field.required`` for both states."""
    assert (
        convert_serializer_field(_bind(serializers.CharField(required=True), "f")).required is True
    )
    assert (
        convert_serializer_field(_bind(serializers.CharField(required=False), "f")).required
        is False
    )


def test_email_field_maps_via_mro_under_charfield():
    """A known subclass (``EmailField``) resolves to its ``CharField`` parent's scalar (MRO walk)."""
    assert convert_serializer_field(_bind(serializers.EmailField(), "f")).annotation is str


def test_is_input_parameter_is_accepted_and_ignored():
    """``is_input`` is threaded for graphene-parity but does not branch (spec-039 SR-3)."""
    a = convert_serializer_field(_bind(serializers.CharField(), "f"), is_input=True)
    b = convert_serializer_field(_bind(serializers.CharField(), "f"), is_input=False)
    assert a.annotation is b.annotation is str
    assert a.kind == b.kind == SCALAR


# ---------------------------------------------------------------------------
# List / multi-choice
# ---------------------------------------------------------------------------


def test_list_field_scalar_child_maps_to_list():
    """``ListField(child=IntegerField())`` -> ``list[int]`` (recursive through the scalar registry)."""
    field = _bind(serializers.ListField(child=serializers.IntegerField()), "nums")
    conversion = convert_serializer_field(field)
    assert conversion.annotation == list[int]
    assert conversion.kind == SCALAR


def test_multiple_choice_field_maps_to_list_str():
    """``MultipleChoiceField`` -> ``list[str]`` (precedes the scalar ``ChoiceField`` -> ``str``)."""
    field = _bind(serializers.MultipleChoiceField(choices=["a", "b"]), "tags")
    conversion = convert_serializer_field(field)
    assert conversion.annotation == list[str]
    assert conversion.kind == SCALAR


def test_list_field_relation_child_raises():
    """A ``ListField`` whose child is a relation raises (only a scalar child is supported)."""
    _register_products_types()
    field = _bind(
        serializers.ListField(
            child=serializers.PrimaryKeyRelatedField(
                queryset=product_models.Category.objects.all(),
            ),
        ),
        "cats",
    )
    with pytest.raises(ConfigurationError, match="ListField whose child"):
        convert_serializer_field(field)


def test_list_field_nested_serializer_child_raises():
    """A ``ListField`` whose child is a nested serializer raises."""

    class Inner(serializers.Serializer):
        x = serializers.CharField()

    field = _bind(serializers.ListField(child=Inner()), "items")
    with pytest.raises(ConfigurationError):
        convert_serializer_field(field)


def test_list_field_file_child_raises():
    """A ``ListField`` whose child is a ``FileField`` raises (a FILE-kind child is not a scalar).

    A ``FileField`` child is neither a relation nor a nested serializer (those raise
    earlier), so it reaches the scalar-child guard: ``convert_serializer_field`` returns
    a ``FILE`` kind with a ``None`` annotation, which is rejected.
    """
    field = _bind(serializers.ListField(child=serializers.FileField()), "files")
    with pytest.raises(ConfigurationError, match="does not resolve to a scalar"):
        convert_serializer_field(field)


def test_serializer_only_many_related_field_maps_to_globalid_list():
    """A serializer-only ``PrimaryKeyRelatedField(many=True)`` -> ``list[GlobalID]`` (the column-less M2M annotation).

    The ``many=True`` (``ManyRelatedField``) analog of the single serializer-only relation:
    no backing column, so the related model resolves from ``child_relation.queryset.model``
    and the id type follows the Relay-vs-raw-pk rule against the target's primary.
    """
    relay_target, _ = _make_relay_target()
    field = _bind(
        serializers.PrimaryKeyRelatedField(many=True, queryset=relay_target.objects.all()),
        "targets",
    )
    input_attr, annotation, related_model = serializer_only_relation_annotation(
        field,
        RELATION_MULTI,
    )
    assert input_attr == "targets"
    assert annotation == list[relay.GlobalID]
    assert related_model is relay_target


def test_nested_serializer_field_raises():
    """A nested ``Serializer`` field raises (the 036 nested-write non-goal)."""

    class Inner(serializers.Serializer):
        x = serializers.CharField()

    with pytest.raises(ConfigurationError, match="nested"):
        convert_serializer_field(_bind(Inner(), "inner"))


def test_list_serializer_field_raises():
    """A ``ListSerializer`` (a ``many=True`` nested serializer) raises."""

    class Inner(serializers.Serializer):
        x = serializers.CharField()

    with pytest.raises(ConfigurationError, match="nested"):
        convert_serializer_field(_bind(Inner(many=True), "items"))


# ---------------------------------------------------------------------------
# Relation / file kind flags
# ---------------------------------------------------------------------------


def test_primary_key_related_field_is_relation_single():
    """``PrimaryKeyRelatedField`` -> kind ``relation_single`` (annotation finalized at build site)."""
    _register_products_types()
    field = _bind(
        serializers.PrimaryKeyRelatedField(queryset=product_models.Category.objects.all()),
        "category",
    )
    conversion = convert_serializer_field(field)
    assert conversion.kind == RELATION_SINGLE
    assert conversion.annotation is None


def test_many_related_field_is_relation_multi():
    """``PrimaryKeyRelatedField(many=True)`` (a ``ManyRelatedField``) -> kind ``relation_multi``."""
    _register_products_types()
    field = _bind(
        serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=product_models.Category.objects.all(),
        ),
        "cats",
    )
    conversion = convert_serializer_field(field)
    assert conversion.kind == RELATION_MULTI
    assert conversion.annotation is None


def test_slug_related_field_raises_non_pk_relation():
    """A writable ``SlugRelatedField`` (a non-PK relation) fails loud (spec-039 H5).

    Only ``PrimaryKeyRelatedField`` decodes to a primary key; a slug-expecting field has
    no pk-based input shape, so it raises rather than silently misdecoding a pk.
    """
    _register_products_types()
    field = _bind(
        serializers.SlugRelatedField(
            slug_field="name",
            queryset=product_models.Category.objects.all(),
        ),
        "category",
    )
    with pytest.raises(ConfigurationError, match="PrimaryKeyRelatedField"):
        convert_serializer_field(field)


def test_many_related_field_non_pk_child_raises():
    """A ``ManyRelatedField`` wrapping a non-PK child (``SlugRelatedField(many=True)``) fails loud (H5)."""
    _register_products_types()
    field = _bind(
        serializers.SlugRelatedField(
            many=True,
            slug_field="name",
            queryset=product_models.Category.objects.all(),
        ),
        "cats",
    )
    with pytest.raises(ConfigurationError, match="PrimaryKeyRelatedField"):
        convert_serializer_field(field)


def test_file_and_image_fields_are_file_kind():
    """``FileField`` / ``ImageField`` -> kind ``file`` (the ``Upload`` annotation is build-site)."""
    assert convert_serializer_field(_bind(serializers.FileField(), "f")).kind == FILE
    # ``ImageField`` requires Pillow at validate time, but construction +
    # conversion only read the class, so no Pillow dependency here.
    assert convert_serializer_field(_bind(serializers.ImageField(), "f")).kind == FILE


# ---------------------------------------------------------------------------
# Fail-loud dispatch - no base-Field catch-all (the load-bearing assertion)
# ---------------------------------------------------------------------------


def test_unknown_custom_field_subclass_raises():
    """A custom ``serializers.Field`` subclass with no supported ancestor raises ``ConfigurationError``.

    The catch-all-shadowing regression: a ``serializers.Field -> str`` catch-all
    would make this silently become ``String``. The raise proves no such catch-all
    exists - there is no silent ``String`` fallback.
    """

    class CustomField(serializers.Field):
        def to_internal_value(self, data):  # pragma: no cover - never called in conversion.
            return data

        def to_representation(self, value):  # pragma: no cover - never called in conversion.
            return value

    with pytest.raises(
        ConfigurationError,
        match="Unsupported serializer field type 'CustomField'",
    ):
        convert_serializer_field(_bind(CustomField(), "x"))


# ---------------------------------------------------------------------------
# id-like suffix rule (declared-name driven, no doubled IdId / PkId)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("declared", "expected_attr", "expected_graphql"),
    [
        ("category", "category_id", "categoryId"),
        ("category_id", "category_id", "categoryId"),
        ("category_pk", "category_pk", "categoryPk"),
    ],
)
def test_id_like_suffix_rule(declared, expected_attr, expected_graphql):
    """A single relation's declared name drives the input attr / GraphQL name (no doubling)."""
    attr, graphql = serializer_field_graphql_name(declared, RELATION_SINGLE)
    assert attr == expected_attr
    assert graphql == expected_graphql


def test_multi_relation_keeps_plain_name():
    """A multi relation keeps the plain declared name (already a collection of ids)."""
    attr, graphql = serializer_field_graphql_name("cats", RELATION_MULTI)
    assert attr == "cats"
    assert graphql == "cats"


# ---------------------------------------------------------------------------
# Renamed fields - the source axis
# ---------------------------------------------------------------------------


def test_renamed_scalar_resolves_backing_column_via_source():
    """``full_name = CharField(source="name")`` resolves the ``name`` column, keeps the declared name."""
    _register_products_types()

    class RenamedSer(serializers.ModelSerializer):
        full_name = serializers.CharField(source="name")

        class Meta:
            model = product_models.Item
            fields = ("full_name",)

    field = RenamedSer().fields["full_name"]
    # Backing column resolved via source, not declared name.
    column = backing_model_field(product_models.Item, field)
    assert column.name == "name"
    python_attr, _annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert python_attr == "full_name"
    assert spec.graphql_name == "fullName"
    assert spec.target_name == "full_name"  # declared name preserved in reverse map
    assert spec.source == "name"
    assert spec.kind == SCALAR


def test_renamed_relation_resolves_backing_column_and_id_like_name():
    """``category_pk = PrimaryKeyRelatedField(source="category")`` -> ``categoryPk``, column via source."""
    _register_products_types()

    class RenamedSer(serializers.ModelSerializer):
        category_pk = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
            source="category",
        )

        class Meta:
            model = product_models.Item
            fields = ("category_pk",)

    field = RenamedSer().fields["category_pk"]
    python_attr, _annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert python_attr == "category_pk"  # already id-like, no doubling
    assert spec.graphql_name == "categoryPk"
    assert spec.target_name == "category_pk"
    assert spec.source == "category"
    assert spec.kind == RELATION_SINGLE
    # H4: the relation's target model is recorded on the spec at build time so the
    # Slice-3 decode never re-discovers the serializer field set per request.
    assert spec.related_model is product_models.Category


def test_model_backed_slug_related_field_raises():
    """A ``SlugRelatedField`` over a model RELATION column fails loud at resolve (spec-039 H5).

    The model-backed relation branch (``column.is_relation``) would otherwise type the
    field as a pk-decoding GlobalID / raw-pk input, silently misdecoding a pk into a
    slug-expecting field. It fails loud instead.
    """
    _register_products_types()

    class SlugSer(serializers.ModelSerializer):
        category = serializers.SlugRelatedField(
            slug_field="name",
            queryset=product_models.Category.objects.all(),
        )

        class Meta:
            model = product_models.Item
            fields = ("category",)

    field = SlugSer().fields["category"]
    with pytest.raises(ConfigurationError, match="PrimaryKeyRelatedField"):
        resolve_serializer_field(field, product_models.Item, "X")


def test_dotted_source_on_model_column_field_raises():
    """A dotted ``source`` on a model-column-converting field raises ``ConfigurationError``."""
    _register_products_types()

    class DottedSer(serializers.ModelSerializer):
        nm = serializers.CharField(source="category.name")

        class Meta:
            model = product_models.Item
            fields = ("nm",)

    field = DottedSer().fields["nm"]
    with pytest.raises(ConfigurationError, match="dotted source"):
        backing_model_field(product_models.Item, field)


def test_star_source_on_model_column_field_raises():
    """A ``source="*"`` on a model-column-converting field raises ``ConfigurationError``."""
    _register_products_types()
    field = _bind(serializers.CharField(source="*"), "whole")
    with pytest.raises(ConfigurationError, match="dotted source"):
        backing_model_field(product_models.Item, field)


# ---------------------------------------------------------------------------
# Serializer-only relation (queryset.model) + M3 missing primary DjangoType
# ---------------------------------------------------------------------------


def test_serializer_only_relation_resolves_target_from_queryset_model():
    """A plain-``Serializer`` relation resolves its target from ``field.queryset.model`` (F4)."""
    _register_products_types()

    class PlainSer(serializers.Serializer):
        cat = serializers.PrimaryKeyRelatedField(queryset=product_models.Category.objects.all())

    field = PlainSer().fields["cat"]
    python_attr, annotation, spec = resolve_serializer_field(field, None, "X")
    assert python_attr == "cat_id"
    assert spec.kind == RELATION_SINGLE
    # Category's primary DjangoType is non-Relay -> raw pk scalar (int).
    assert annotation is int


def test_serializer_only_relation_to_relay_target_uses_globalid():
    """A serializer-only relation to a Relay primary becomes ``GlobalID``."""
    relay_target, _ = _make_relay_target()

    class PlainSer(serializers.Serializer):
        target = serializers.PrimaryKeyRelatedField(queryset=relay_target.objects.all())

    field = PlainSer().fields["target"]
    _python_attr, annotation, _spec = resolve_serializer_field(field, None, "X")
    assert annotation is relay.GlobalID


def test_relation_with_no_backing_column_and_no_queryset_raises():
    """A read-only-ish relation with no column and no concrete queryset.model raises.

    A ``read_only=True`` relation carries no queryset; routed through the
    column-less path (no model) it cannot resolve a target and raises.
    """
    _register_products_types()

    class PlainSer(serializers.Serializer):
        rel = serializers.PrimaryKeyRelatedField(read_only=True)

    field = PlainSer().fields["rel"]
    with pytest.raises(ConfigurationError, match="no concrete queryset.model"):
        resolve_serializer_field(field, None, "X")


def test_relation_target_with_no_registered_primary_raises():
    """A relation whose target model has no registered primary DjangoType raises (M3)."""

    # No DjangoType registered for Category in this test -> M3 fires.
    class ItemSer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("category",)

    field = ItemSer().fields["category"]
    with pytest.raises(ConfigurationError, match="no registered primary DjangoType"):
        resolve_serializer_field(field, product_models.Item, "X")


# ---------------------------------------------------------------------------
# Expanded DRF scalar capability matrix (spec-039 rev6 #7) - no catch-all
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        (serializers.DictField(), strawberry.scalars.JSON),
        (serializers.IPAddressField(), str),
        (serializers.FilePathField(path="/tmp"), str),
        (serializers.DurationField(), str),
    ],
)
def test_expanded_scalar_matrix(field, expected):
    """The rev6 #7 scalars each map to their EXPLICIT annotation, kind ``scalar``.

    ``DictField`` -> ``JSON``; ``IPAddressField`` / ``FilePathField`` -> ``str``;
    ``DurationField`` -> ``str`` (a DELIBERATE scalar - DRF renders a duration as an
    ISO-8601-ish string on the wire, not an accidental fallthrough).
    """
    conversion = convert_serializer_field(_bind(field, "f"))
    assert conversion.annotation == expected
    assert conversion.kind == SCALAR


def test_hstore_field_maps_to_json_via_mro():
    """``HStoreField`` (a ``DictField`` subclass) resolves to ``JSON`` through the MRO walk."""
    conversion = convert_serializer_field(_bind(serializers.HStoreField(), "h"))
    assert conversion.annotation == strawberry.scalars.JSON
    assert conversion.kind == SCALAR


def test_model_field_maps_via_wrapped_model_field():
    """``ModelField`` resolves its scalar through the wrapped Django ``model_field`` (#7)."""
    field = serializers.ModelField(model_field=product_models.Item._meta.get_field("name"))
    conversion = convert_serializer_field(_bind(field, "nm"))
    assert conversion.annotation is str
    assert conversion.kind == SCALAR


def test_model_field_without_wrapped_field_raises():
    """A ``ModelField`` with no wrapped ``model_field`` fails loud (no scalar to resolve)."""
    field = serializers.ModelField(model_field=None)
    field.field_name = "x"
    with pytest.raises(ConfigurationError, match="ModelField with no wrapped model_field"):
        convert_serializer_field(field)


def test_model_field_over_unsupported_column_fails_loud():
    """A ``ModelField`` over an UNsupported column type raises (via ``scalar_for_field``, no ``String``)."""

    class WeirdField(models.Field):
        pass

    weird = WeirdField()
    weird.set_attributes_from_name("weird")
    field = serializers.ModelField(model_field=weird)
    field.field_name = "weird"
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_serializer_field(field)


# ---------------------------------------------------------------------------
# Public converter registry (spec-039 rev6 #11) - sanctioned extension, no catch-all
# ---------------------------------------------------------------------------


class _CustomHexField(serializers.Field):
    """A custom DRF field whose MRO has NO supported ancestor (unregistered -> raises)."""

    def to_internal_value(self, data):  # pragma: no cover - never called in conversion.
        return data

    def to_representation(self, value):  # pragma: no cover - never called in conversion.
        return value


def test_unregistered_custom_field_raises_then_registered_maps(_restore_converter_registry):
    """A custom field raises until a converter is registered, then maps - and no catch-all appears."""
    # Unregistered: the fail-loud raise (no silent ``String``).
    with pytest.raises(
        ConfigurationError,
        match="Unsupported serializer field type '_CustomHexField'",
    ):
        convert_serializer_field(_bind(_CustomHexField(), "c"))

    register_serializer_field_converter(
        _CustomHexField,
        lambda field: SerializerFieldConversion(annotation=str, required=field.required),
    )
    conversion = convert_serializer_field(_bind(_CustomHexField(), "c"))
    assert conversion.annotation is str
    assert conversion.kind == SCALAR


def test_register_converter_resolves_unregistered_subclass_via_mro(_restore_converter_registry):
    """A registered converter also covers the field class's unregistered subclasses (MRO walk)."""
    register_serializer_field_converter(
        _CustomHexField,
        lambda field: SerializerFieldConversion(annotation=str, required=field.required),
    )

    class _CustomHexSubclass(_CustomHexField):
        pass

    assert convert_serializer_field(_bind(_CustomHexSubclass(), "c")).annotation is str


def test_register_converter_override_guard(_restore_converter_registry):
    """Re-registering an already-mapped class raises unless ``override=True``."""
    conv = lambda field: SerializerFieldConversion(annotation=int, required=field.required)  # noqa: E731
    with pytest.raises(ConfigurationError, match="already registered for 'CharField'"):
        register_serializer_field_converter(serializers.CharField, conv)
    # ``override=True`` replaces it.
    register_serializer_field_converter(serializers.CharField, conv, override=True)
    assert convert_serializer_field(_bind(serializers.CharField(), "f")).annotation is int


def test_register_converter_rejects_non_field_class(_restore_converter_registry):
    """``field_class`` must be a ``serializers.Field`` subclass."""
    with pytest.raises(ConfigurationError, match="must be a serializers.Field subclass"):
        register_serializer_field_converter(
            int,  # not a serializers.Field
            lambda field: SerializerFieldConversion(annotation=str, required=field.required),
        )


def test_register_converter_rejects_non_callable(_restore_converter_registry):
    """``converter`` must be callable."""
    with pytest.raises(ConfigurationError, match="must be\n?.*callable|callable"):
        register_serializer_field_converter(_CustomHexField, "not-a-callable")


# ---------------------------------------------------------------------------
# Serializer-only ChoiceField -> generated enum (spec-039 rev6 #6)
# ---------------------------------------------------------------------------


def test_serializer_only_choicefield_becomes_enum():
    """A serializer-only ``ChoiceField`` resolves to a generated GraphQL enum (schema precision)."""

    class ChoiceSer(serializers.Serializer):
        color = serializers.ChoiceField(choices=[("r", "Red"), ("g", "Green")])

    field = ChoiceSer().fields["color"]
    _attr, annotation, spec = resolve_serializer_field(field, None, "X")
    assert spec.kind == SCALAR
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.value for member in annotation} == {"r", "g"}


def test_serializer_only_multiple_choicefield_becomes_list_enum():
    """A serializer-only ``MultipleChoiceField`` resolves to ``list[<enum>]``."""

    class MultiSer(serializers.Serializer):
        tags = serializers.MultipleChoiceField(choices=[("a", "A"), ("b", "B")])

    field = MultiSer().fields["tags"]
    _attr, annotation, _spec = resolve_serializer_field(field, None, "X")
    assert get_origin(annotation) is list
    (inner,) = get_args(annotation)
    assert issubclass(inner, Enum)
    assert {member.value for member in inner} == {"a", "b"}


def test_serializer_only_filepathfield_stays_str_not_enum():
    """A ``FilePathField`` (a ``ChoiceField`` subclass with DYNAMIC choices) stays ``str``, never an enum."""

    class PathSer(serializers.Serializer):
        p = serializers.FilePathField(path="/tmp")

    field = PathSer().fields["p"]
    _attr, annotation, _spec = resolve_serializer_field(field, None, "X")
    assert annotation is str


def test_serializer_only_choice_enum_dedupes_by_name():
    """Two resolves of the same serializer-only choice field share ONE enum object (dedupe)."""

    def _resolve():
        class ChoiceSer(serializers.Serializer):
            color = serializers.ChoiceField(choices=[("r", "Red"), ("g", "Green")])

        return resolve_serializer_field(ChoiceSer().fields["color"], None, "X")[1]

    assert _resolve() is _resolve()


def test_serializer_only_choice_enum_name_collision_with_diverging_members_raises():
    """Reusing an enum NAME with a DIFFERENT member set fails loud (no silent reuse)."""

    class SerA(serializers.Serializer):
        color = serializers.ChoiceField(choices=[("r", "Red")])

    class SerB(serializers.Serializer):
        color = serializers.ChoiceField(choices=[("b", "Blue")])

    resolve_serializer_field(SerA().fields["color"], None, "X")
    with pytest.raises(ConfigurationError, match="two different member sets"):
        resolve_serializer_field(SerB().fields["color"], None, "X")


# ---------------------------------------------------------------------------
# Model-backed type-override conflict policy (spec-039 rev6 #8)
# ---------------------------------------------------------------------------


def test_consumer_declared_scalar_disagreeing_with_column_raises():
    """A consumer-declared field whose scalar disagrees with the model column fails loud."""
    _register_products_types()

    class MismatchSer(serializers.ModelSerializer):
        name = serializers.IntegerField()  # column is TextField -> str; declared int -> disagree.

        class Meta:
            model = product_models.Item
            fields = ("name",)

    field = MismatchSer().fields["name"]
    with pytest.raises(ConfigurationError, match="disagrees with the backing model column"):
        resolve_serializer_field(field, product_models.Item, "X")


def test_consumer_declared_scalar_agreeing_with_column_ok():
    """A benign rename (``CharField`` over a text column) AGREES and resolves to the model scalar."""
    _register_products_types()

    class AgreeSer(serializers.ModelSerializer):
        display_name = serializers.CharField(source="name")

        class Meta:
            model = product_models.Item
            fields = ("display_name",)

    field = AgreeSer().fields["display_name"]
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert spec.kind == SCALAR
    assert annotation is str


def test_unbound_model_backed_field_is_treated_as_auto_generated():
    """An unbound field has no serializer parent, so it is not treated as consumer-declared."""
    _register_products_types()
    field = serializers.CharField(source="name")
    field.field_name = "name"
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert spec.kind == SCALAR
    assert annotation is str


def test_declared_model_backed_non_scalar_conversion_defers_to_model_annotation():
    """A declared model-backed field whose converter is not scalar falls back to the column type."""
    _register_products_types()

    class FileOverrideSer(serializers.ModelSerializer):
        attachment = serializers.FileField(source="name")

        class Meta:
            model = product_models.Item
            fields = ("attachment",)

    field = FileOverrideSer().fields["attachment"]
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert spec.kind == SCALAR
    assert annotation is str


def test_auto_generated_model_field_is_not_conflict_checked():
    """An AUTO-generated ModelSerializer field routes through the model converter (no conflict check)."""
    _register_products_types()

    class AutoSer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name",)

    field = AutoSer().fields["name"]
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert spec.kind == SCALAR
    assert annotation is str


# ---------------------------------------------------------------------------
# DRF field metadata -> SDL description (spec-039 rev6 #9)
# ---------------------------------------------------------------------------


def test_serializer_field_description_combines_help_text_and_constraints():
    """``help_text`` heads the description; a constraint summary is appended (#9)."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    field = _bind(
        serializers.CharField(help_text="The item name.", min_length=2, max_length=20),
        "name",
    )
    description = serializer_field_description(field)
    assert description is not None
    assert description.startswith("The item name.")
    assert "min_length=2" in description
    assert "max_length=20" in description


def test_serializer_field_description_none_without_metadata():
    """A field with neither help text nor constraints yields ``None`` (no description emitted)."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    assert serializer_field_description(_bind(serializers.CharField(), "f")) is None


def test_serializer_field_description_notes_numeric_bounds_and_allow_blank():
    """Numeric bounds + ``allow_blank`` are summarized even without help text (#9)."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    numeric = serializer_field_description(
        _bind(serializers.IntegerField(min_value=0, max_value=9), "n"),
    )
    assert numeric == "Constraints: min_value=0, max_value=9."
    blank = serializer_field_description(_bind(serializers.CharField(allow_blank=True), "b"))
    assert blank == "Constraints: allow_blank=true."


def test_serializer_field_description_notes_allow_empty_false():
    """``allow_empty=False`` is included in the SDL metadata summary (#9)."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    field = _bind(serializers.ListField(child=serializers.CharField(), allow_empty=False), "tags")
    assert serializer_field_description(field) == "Constraints: allow_empty=false."


def test_declared_choicefield_over_model_column_emits_serializer_enum():
    """A declared ``ChoiceField(source=<model col>, choices=...)`` emits the serializer-only enum (rev6 rev2 P2).

    The declared choices are a schema-affecting override: even mapped (via ``source``) to a
    plain non-choice model column, the field emits the GENERATED enum from its declared choices,
    never collapsing back to the column's ``String`` scalar.
    """
    _register_products_types()

    class ChoiceOverColumnSer(serializers.ModelSerializer):
        status = serializers.ChoiceField(source="name", choices=[("a", "A"), ("b", "B")])

        class Meta:
            model = product_models.Item
            fields = ("status",)

    field = ChoiceOverColumnSer().fields["status"]
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.value for member in annotation} == {"a", "b"}
    assert spec.source == "name"  # still writes through to the model column
