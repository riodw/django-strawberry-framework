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

import pytest
import strawberry
from apps.products import models as product_models
from django.db import models
from rest_framework import serializers
from strawberry import relay

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework.serializer_converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    backing_model_field,
    convert_serializer_field,
    resolve_serializer_field,
    serializer_field_graphql_name,
)


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
