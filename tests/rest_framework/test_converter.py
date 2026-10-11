"""Converter tests for the DRF serializer-field -> Strawberry annotation registry.

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
  and the missing-primary-DjangoType raise;
- a choice field admitting a value (a declared choice, or ``""`` from ``allow_blank``) its
  choice column does not list (refused: declared, ``source``-mapped, ``extra_kwargs``, an
  integer column) beside the accepted ``blank=True`` column, the read-back comparison and the
  serializer-only field;
- a grouped choice column: a declared flat ``ChoiceField`` checked against the column's
  flattened values (accepted, or refused for a value the column does not list), an
  ``ArrayField`` whose ``base_field`` is grouped, and the refusal of every field that would
  take the column's read enum;
- a ``Choices.__empty__`` ``(None, label)`` pair left to ``allow_null``: the auto
  ``ModelSerializer`` field, a serializer-only ``ChoiceField`` / ``MultipleChoiceField`` and an
  ``ArrayField`` element build with no ``_None`` member;
- a ``MultipleChoiceField`` over a single-value choice column (refused: declared,
  ``source``-mapped, ``serializer_choice_field``-generated) beside the accepted
  ``ArrayField`` (element values checked against its ``base_field``), ``JSONField`` and
  non-choice text columns.

The relation id-type (Relay-``GlobalID`` vs raw pk, single + multi) is pinned at
the ``resolve_serializer_field`` build site over a real model's primary
``DjangoType``; those assertions live here (where the converter resolves the id)
and in ``test_inputs.py`` (where the built input field's type is asserted).
Live input shapes: ``examples/fakeshop/test_query/test_library_api.py`` serializer
introspection rows.

System-under-test runs against the products ``Item`` / ``Category`` fixtures per
``AGENTS.md``, a package-local Relay ``DjangoType`` over library ``Genre``,
``Book.circulation_status`` as the choices column and ``scalars.MediaSpecimen``
as the file column.
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from collections.abc import Callable, Iterator
from enum import Enum
from typing import TYPE_CHECKING, Any, get_args, get_origin

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalar_models
from django.db import models
from rest_framework import serializers
from strawberry import relay
from typing_extensions import override

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
    require_one_segment_source,
    resolve_serializer_field,
    serializer_field_graphql_name,
    serializer_only_relation_annotation,
)
from django_strawberry_framework.scalars import Upload
from tests._idioms import bind_unparented

if TYPE_CHECKING:
    from django_strawberry_framework.rest_framework.serializer_converter import DRFField
    from django_strawberry_framework.utils.typing import ConcreteField


@pytest.fixture
def _restore_converter_registry() -> Iterator[None]:
    """Snapshot + restore the module converter registry so a test registration cannot leak.

    The serializer-field converter registry mirrors the read-side ``SCALAR_MAP``: a
    mutable module dict NOT reset by ``registry.clear()``, so a test that registers a
    converter restores the snapshot on teardown.
    """
    snapshot = dict(serializer_converter._SERIALIZER_FIELD_CONVERTERS)
    yield
    serializer_converter._SERIALIZER_FIELD_CONVERTERS.clear()
    serializer_converter._SERIALIZER_FIELD_CONVERTERS.update(snapshot)


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry so each test's products / fixture ``DjangoType``s start clean."""
    registry.clear()
    yield
    registry.clear()


def _concrete_field(model: type[models.Model], name: str) -> ConcreteField:
    """Read ``model``'s concrete column ``name`` (``get_field`` also returns reverse relations)."""
    field = model._meta.get_field(name)
    assert isinstance(field, models.Field)
    return field


def _register_products_types() -> None:
    """Register non-Relay ``DjangoType``s for products ``Item`` / ``Category``."""

    class CategoryType(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")

    assert registry.get(product_models.Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")

    assert registry.get(product_models.Item) is ItemType


def _make_relay_target():
    """Register a Relay-Node ``DjangoType`` over ``library.Genre`` and return both."""
    from apps.library.models import Genre

    class GenreNode(DjangoType, relay.Node):
        class Meta:
            model = Genre
            fields = ("id", "name")

    return Genre, GenreNode


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
def test_scalar_field_annotations(field: DRFField, expected: object):
    """Each supported scalar serializer field maps to its Strawberry annotation, kind ``scalar``."""
    conversion = convert_serializer_field(bind_unparented(field, "f"))
    assert conversion.annotation == expected
    assert conversion.kind == SCALAR


def test_required_ness_reflects_field_required():
    """``required`` mirrors ``field.required`` for both states."""
    assert (
        convert_serializer_field(
            bind_unparented(serializers.CharField(required=True), "f"),
        ).required
        is True
    )
    assert (
        convert_serializer_field(
            bind_unparented(serializers.CharField(required=False), "f"),
        ).required
        is False
    )


def test_email_field_maps_via_mro_under_charfield():
    """A known subclass (``EmailField``) resolves to its ``CharField`` parent's scalar (MRO walk)."""
    assert (
        convert_serializer_field(bind_unparented(serializers.EmailField(), "f")).annotation is str
    )


def test_is_input_parameter_is_accepted_and_ignored():
    """``is_input`` is threaded for graphene-parity but does not branch (spec-039)."""
    a = convert_serializer_field(bind_unparented(serializers.CharField(), "f"), is_input=True)
    b = convert_serializer_field(bind_unparented(serializers.CharField(), "f"), is_input=False)
    assert a.annotation is b.annotation is str
    assert a.kind == b.kind == SCALAR


# ---------------------------------------------------------------------------
# List / multi-choice
# ---------------------------------------------------------------------------


def test_list_field_scalar_child_maps_to_list():
    """``ListField(child=IntegerField())`` -> ``list[int]`` (recursive through the scalar registry)."""
    field = bind_unparented(serializers.ListField(child=serializers.IntegerField()), "nums")
    conversion = convert_serializer_field(field)
    assert conversion.annotation == list[int]
    assert conversion.kind == SCALAR


def test_multiple_choice_field_maps_to_list_str():
    """``MultipleChoiceField`` -> ``list[str]`` (precedes the scalar ``ChoiceField`` -> ``str``)."""
    field = bind_unparented(serializers.MultipleChoiceField(choices=["a", "b"]), "tags")
    conversion = convert_serializer_field(field)
    assert conversion.annotation == list[str]
    assert conversion.kind == SCALAR


def test_list_field_relation_child_raises():
    """A ``ListField`` whose child is a relation raises (only a scalar child is supported)."""
    _register_products_types()
    field = bind_unparented(
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

    class Inner(serializers.Serializer[object]):
        x = serializers.CharField()

    field = bind_unparented(serializers.ListField(child=Inner()), "items")
    with pytest.raises(ConfigurationError):
        convert_serializer_field(field)


def test_list_field_file_child_raises():
    """A ``ListField`` whose child is a ``FileField`` raises (a FILE-kind child is not a scalar).

    A ``FileField`` child is neither a relation nor a nested serializer (those raise
    earlier), so it reaches the scalar-child guard: ``convert_serializer_field`` returns
    a ``FILE`` kind with a ``None`` annotation, which is rejected.
    """
    field = bind_unparented(serializers.ListField(child=serializers.FileField()), "files")
    with pytest.raises(ConfigurationError, match="does not resolve to a scalar"):
        convert_serializer_field(field)


def test_serializer_only_many_related_field_maps_to_globalid_list():
    """A serializer-only ``PrimaryKeyRelatedField(many=True)`` -> ``list[GlobalID]`` (the column-less M2M annotation).

    The ``many=True`` (``ManyRelatedField``) analog of the single serializer-only relation:
    no backing column, so the related model resolves from ``child_relation.queryset.model``
    and the id type follows the Relay-vs-raw-pk rule against the target's primary.
    """
    relay_target, _ = _make_relay_target()
    field = bind_unparented(
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

    class Inner(serializers.Serializer[object]):
        x = serializers.CharField()

    with pytest.raises(ConfigurationError, match="nested"):
        convert_serializer_field(bind_unparented(Inner(), "inner"))


def test_list_serializer_field_raises():
    """A ``ListSerializer`` (a ``many=True`` nested serializer) raises."""

    class Inner(serializers.Serializer[object]):
        x = serializers.CharField()

    with pytest.raises(ConfigurationError, match="nested"):
        convert_serializer_field(bind_unparented(Inner(many=True), "items"))


def test_is_nested_serializer_field_detects_nested_and_scalar():
    """``is_nested_serializer_field`` is True for a nested serializer / list, False for a scalar."""

    class Inner(serializers.Serializer[object]):
        x = serializers.CharField()

    assert serializer_converter.is_nested_serializer_field(bind_unparented(Inner(), "single"))
    assert serializer_converter.is_nested_serializer_field(
        bind_unparented(Inner(many=True), "many"),
    )
    assert not serializer_converter.is_nested_serializer_field(
        bind_unparented(serializers.CharField(), "s"),
    )


def test_nested_serializer_child_reports_single_vs_many():
    """``nested_serializer_child`` peels a ``ListSerializer`` to its child (many=True) vs a single (many=False)."""

    class Inner(serializers.Serializer[object]):
        x = serializers.CharField()

    single = bind_unparented(Inner(), "single")
    child_single, many_single = serializer_converter.nested_serializer_child(single)
    assert child_single is single
    assert many_single is False

    many = bind_unparented(Inner(many=True), "many")
    child_many, many_flag = serializer_converter.nested_serializer_child(many)
    assert isinstance(child_many, Inner)
    assert many_flag is True


def test_resolve_serializer_field_rejects_nested_over_relation_column():
    """A nested serializer over a REVERSE-relation column fails loud, not misrouted as a relation.

    ``resolve_serializer_field`` rejects a nested serializer FIRST, before the backing-column
    lookup - so a ``CategorySerializer.items = ItemInline(many=True)`` (whose ``items`` source
    resolves to the reverse-relation column) is a clear opt-in error, never silently typed as a
    relation-id input.
    """

    class ItemInline(serializers.ModelSerializer[product_models.Item]):
        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("name",)

    class CategorySer(serializers.ModelSerializer[product_models.Category]):
        items = ItemInline(many=True)

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Category
            fields = ("name", "items")

    field = CategorySer().fields["items"]
    with pytest.raises(ConfigurationError, match="opt-in only"):
        resolve_serializer_field(field, product_models.Category, "CategorySerInput")


# ---------------------------------------------------------------------------
# Relation / file kind flags
# ---------------------------------------------------------------------------


def test_primary_key_related_field_is_relation_single():
    """``PrimaryKeyRelatedField`` -> kind ``relation_single`` (annotation finalized at build site)."""
    _register_products_types()
    field = bind_unparented(
        serializers.PrimaryKeyRelatedField(queryset=product_models.Category.objects.all()),
        "category",
    )
    conversion = convert_serializer_field(field)
    assert conversion.kind == RELATION_SINGLE
    assert conversion.annotation is None


def test_many_related_field_is_relation_multi():
    """``PrimaryKeyRelatedField(many=True)`` (a ``ManyRelatedField``) -> kind ``relation_multi``."""
    _register_products_types()
    field = bind_unparented(
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
    """A writable ``SlugRelatedField`` (a non-PK relation) fails loud.

    Only ``PrimaryKeyRelatedField`` decodes to a primary key; a slug-expecting field has
    no pk-based input shape, so it raises rather than silently misdecoding a pk.
    """
    _register_products_types()
    field = bind_unparented(
        serializers.SlugRelatedField(
            slug_field="name",
            queryset=product_models.Category.objects.all(),
        ),
        "category",
    )
    with pytest.raises(ConfigurationError, match="PrimaryKeyRelatedField"):
        convert_serializer_field(field)


def test_many_related_field_non_pk_child_raises():
    """A ``ManyRelatedField`` wrapping a non-PK child (``SlugRelatedField(many=True)``) fails loud."""
    _register_products_types()
    field = bind_unparented(
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
    assert convert_serializer_field(bind_unparented(serializers.FileField(), "f")).kind == FILE
    # ``ImageField`` requires Pillow at validate time, but construction +
    # conversion only read the class, so no Pillow dependency here.
    assert convert_serializer_field(bind_unparented(serializers.ImageField(), "f")).kind == FILE


# ---------------------------------------------------------------------------
# Fail-loud dispatch - no base-Field catch-all (the load-bearing assertion)
# ---------------------------------------------------------------------------


def test_unknown_custom_field_subclass_raises():
    """A custom ``serializers.Field`` subclass with no supported ancestor raises ``ConfigurationError``.

    The catch-all-shadowing regression: a ``serializers.Field -> str`` catch-all
    would make this silently become ``String``. The raise proves no such catch-all
    exists - there is no silent ``String`` fallback.
    """

    class CustomField(serializers.Field[object, object, object, object]):
        @override
        def to_internal_value(self, data: object):  # never called in conversion.
            return data

        @override
        def to_representation(self, value: object):  # never called in conversion.
            return value

    with pytest.raises(
        ConfigurationError,
        match="Unsupported serializer field type 'CustomField'",
    ):
        convert_serializer_field(bind_unparented(CustomField(), "x"))


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
def test_id_like_suffix_rule(declared: str, expected_attr: str, expected_graphql: str):
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

    class RenamedSer(serializers.ModelSerializer[product_models.Item]):
        full_name = serializers.CharField(source="name")

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("full_name",)

    field = RenamedSer().fields["full_name"]
    # Backing column resolved via source, not declared name.
    column = backing_model_field(product_models.Item, field)
    assert column is not None
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

    class RenamedSer(serializers.ModelSerializer[product_models.Item]):
        category_pk = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
            source="category",
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("category_pk",)

    field = RenamedSer().fields["category_pk"]
    python_attr, _annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert python_attr == "category_pk"  # already id-like, no doubling
    assert spec.graphql_name == "categoryPk"
    assert spec.target_name == "category_pk"
    assert spec.source == "category"
    assert spec.kind == RELATION_SINGLE
    # The relation's target model is recorded on the spec at build time so the
    # The decode step never re-discovers the serializer field set per request.
    assert spec.related_model is product_models.Category


def test_model_backed_relation_cardinality_mismatch_raises():
    """A DRF ``many=True`` relation cannot masquerade as a scalar FK input."""
    _register_products_types()

    class MismatchedSer(serializers.ModelSerializer[product_models.Item]):
        category_ids = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=product_models.Category.objects.all(),
            source="category",
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("category_ids",)

    field = MismatchedSer().fields["category_ids"]
    with pytest.raises(ConfigurationError, match="cardinality"):
        resolve_serializer_field(field, product_models.Item, "X")


def _register_relay_shelf_primary() -> None:
    class ShelfProbeType(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    assert registry.get(library_models.Shelf) is ShelfProbeType


def _register_tagged_item_primary() -> None:
    class TaggedItemProbeType(DjangoType):
        class Meta:
            model = library_models.TaggedItem
            fields = ("id",)
            primary = True

    assert registry.get(library_models.TaggedItem) is TaggedItemProbeType


def _register_membership_card_primary() -> None:
    class MembershipCardProbeType(DjangoType):
        class Meta:
            model = library_models.MembershipCard
            fields = ("id", "barcode")
            primary = True

    assert registry.get(library_models.MembershipCard) is MembershipCardProbeType


def test_many_pk_related_field_over_reverse_fk_column_emits_multi():
    """A many relation over a one_to_many column emits a list id input, not one scalar id.

    ``Branch.shelves`` is a ``ManyToOneRel``: collection-shaped (``one_to_many=True``)
    but ``many_to_many=False``, so the column classifier alone would emit a single id.
    The runtime ``ManyRelatedField`` validates a LIST of pks, and the generated input
    must describe the same shape the runtime serializer validates - so after the
    cardinality guard aligns the two sides, the emitted kind follows the serializer
    field's cardinality (``relation_multi`` / a list annotation / the plain name).
    """
    _register_relay_shelf_primary()

    class BranchSer(serializers.ModelSerializer[library_models.Branch]):
        shelves = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Shelf.objects.all(),
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Branch
            fields = ("name", "shelves")

    field = BranchSer().fields["shelves"]
    assert isinstance(field, serializers.ManyRelatedField)
    _python_attr, annotation, spec = resolve_serializer_field(
        field,
        library_models.Branch,
        "ProbeInput",
    )
    assert spec.kind == RELATION_MULTI
    assert _python_attr == "shelves"  # a multi relation keeps the plain declared name
    assert spec.input_attr == "shelves"
    assert spec.graphql_name == "shelves"
    assert spec.related_model is library_models.Shelf
    assert get_origin(annotation) is list
    assert relay.GlobalID in get_args(annotation)


def test_many_pk_related_field_over_generic_relation_column_emits_multi():
    """The same alignment over a ``GenericRelation`` column (also one_to_many, not m2m)."""
    _register_tagged_item_primary()
    tags_rel = library_models.Branch._meta.get_field("tags")
    assert tags_rel.one_to_many is True and tags_rel.many_to_many is False

    class BranchTagSer(serializers.ModelSerializer[library_models.Branch]):
        tagged = serializers.PrimaryKeyRelatedField(
            many=True,
            source="tags",
            queryset=library_models.TaggedItem.objects.all(),
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Branch
            fields = ("name", "tagged")

    field = BranchTagSer().fields["tagged"]
    _attr, annotation, spec = resolve_serializer_field(
        field,
        library_models.Branch,
        "ProbeInput",
    )
    assert spec.kind == RELATION_MULTI
    assert spec.related_model is library_models.TaggedItem
    assert get_origin(annotation) is list


def test_single_pk_related_field_over_reverse_o2o_column_emits_single():
    """A single relation over a reverse OneToOneRel stays a single id input.

    A ``OneToOneRel`` reports ``one_to_many=False`` (it mirrors the forward field's
    ``many_to_one``), so the guard's model classifier calls it single-valued: the
    single spelling passes and the emitted kind stays ``relation_single`` - the
    reverse-O2O sibling of the forward-FK shape.
    """
    _register_membership_card_primary()
    rel = library_models.Patron._meta.get_field("card")
    assert type(rel).__name__ == "OneToOneRel"
    assert serializer_converter._model_relation_cardinality(rel) is False

    class PatronSer(serializers.ModelSerializer[library_models.Patron]):
        card = serializers.PrimaryKeyRelatedField(
            queryset=library_models.MembershipCard.objects.all(),
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Patron
            fields = ("name", "card")

    field = PatronSer().fields["card"]
    _attr, _annotation, spec = resolve_serializer_field(
        field,
        library_models.Patron,
        "ProbeInput",
    )
    assert spec.kind == RELATION_SINGLE
    assert spec.input_attr == "card_id"
    assert spec.graphql_name == "cardId"
    assert spec.related_model is library_models.MembershipCard


def test_many_over_reverse_o2o_column_is_rejected():
    """many=True over a reverse OneToOneRel is a cardinality mismatch (a collection lie)."""

    class PatronSer(serializers.ModelSerializer[library_models.Patron]):
        card = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.MembershipCard.objects.all(),
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Patron
            fields = ("name", "card")

    field = PatronSer().fields["card"]
    with pytest.raises(ConfigurationError, match="cardinality"):
        resolve_serializer_field(field, library_models.Patron, "ProbeInput")


@pytest.mark.parametrize(
    ("model_cls", "column_name", "related_cls"),
    [
        pytest.param(library_models.Branch, "shelves", library_models.Shelf, id="reverse-fk"),
        pytest.param(library_models.Book, "genres", library_models.Genre, id="m2m"),
    ],
)
def test_single_over_collection_column_is_rejected(
    model_cls: type[models.Model],
    column_name: str,
    related_cls: type[models.Model],
) -> None:
    """A single relation over a reverse FK or a many-to-many is a cardinality mismatch."""

    class SingleSer(serializers.ModelSerializer[models.Model]):
        target = serializers.PrimaryKeyRelatedField(
            queryset=related_cls._default_manager.all(),
            source=column_name,
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = model_cls
            fields = ("target",)

    field = SingleSer().fields["target"]
    assert not isinstance(field, serializers.ManyRelatedField)
    with pytest.raises(ConfigurationError, match="cardinality"):
        resolve_serializer_field(field, model_cls, "ProbeInput")


def test_model_backed_slug_related_field_raises():
    """A ``SlugRelatedField`` over a model RELATION column fails loud at resolve.

    The model-backed relation branch (``column.is_relation``) would otherwise type the
    field as a pk-decoding GlobalID / raw-pk input, silently misdecoding a pk into a
    slug-expecting field. It fails loud instead.
    """
    _register_products_types()

    class SlugSer(serializers.ModelSerializer[product_models.Item]):
        category = serializers.SlugRelatedField(
            slug_field="name",
            queryset=product_models.Category.objects.all(),
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("category",)

    field = SlugSer().fields["category"]
    with pytest.raises(ConfigurationError, match="PrimaryKeyRelatedField"):
        resolve_serializer_field(field, product_models.Item, "X")


def test_dotted_source_on_model_column_field_raises():
    """A dotted ``source`` on a model-column-converting field raises ``ConfigurationError``."""
    _register_products_types()

    class DottedSer(serializers.ModelSerializer[product_models.Item]):
        nm = serializers.CharField(source="category.name")

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("nm",)

    field = DottedSer().fields["nm"]
    with pytest.raises(ConfigurationError, match="dotted source"):
        backing_model_field(product_models.Item, field)


def test_star_source_on_model_column_field_raises():
    """A ``source="*"`` on a model-column-converting field raises ``ConfigurationError``."""
    _register_products_types()
    field = bind_unparented(serializers.CharField(source="*"), "whole")
    with pytest.raises(ConfigurationError, match="dotted source"):
        backing_model_field(product_models.Item, field)


def test_require_one_segment_source_rejects_star_and_dotted():
    """The shared one-segment source helper rejects ``source='*'`` and dotted sources.

    ``backing_model_field`` and the nested-input walk both call this owner; column /
    nested nouns stay at the call sites via ``field_label`` / ``must_map_to``.
    """
    star = bind_unparented(serializers.CharField(source="*"), "whole")
    with pytest.raises(ConfigurationError, match="dotted source / source='\\*'"):
        require_one_segment_source(
            star,
            field_label="Serializer field 'whole'",
            must_map_to="a model-column-backed field must map to a single concrete column",
        )
    dotted = bind_unparented(serializers.CharField(source="a.b"), "nm")
    with pytest.raises(ConfigurationError, match="a nested write must map to a single attribute"):
        require_one_segment_source(
            dotted,
            field_label="Nested serializer field 'nm'",
            must_map_to="a nested write must map to a single attribute",
        )
    # One-segment source is the allowed shape (no raise).
    require_one_segment_source(
        bind_unparented(serializers.CharField(source="name"), "nm"),
        field_label="Serializer field 'nm'",
        must_map_to="a model-column-backed field must map to a single concrete column",
    )


# ---------------------------------------------------------------------------
# Serializer-only relation (queryset.model) + missing primary DjangoType
# ---------------------------------------------------------------------------


def test_serializer_only_relation_resolves_target_from_queryset_model():
    """A plain-``Serializer`` relation resolves its target from ``field.queryset.model``."""
    _register_products_types()

    class PlainSer(serializers.Serializer[object]):
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

    class PlainSer(serializers.Serializer[object]):
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

    class PlainSer(serializers.Serializer[object]):
        rel = serializers.PrimaryKeyRelatedField(read_only=True)

    field = PlainSer().fields["rel"]
    with pytest.raises(ConfigurationError, match="no concrete queryset.model"):
        resolve_serializer_field(field, None, "X")


def test_relation_target_with_no_registered_primary_raises():
    """A relation whose target model has no registered primary DjangoType raises."""

    # No DjangoType registered for Category in this test -> the raise fires.
    class ItemSer(serializers.ModelSerializer[product_models.Item]):
        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("category",)

    field = ItemSer().fields["category"]
    with pytest.raises(ConfigurationError, match="no registered primary DjangoType"):
        resolve_serializer_field(field, product_models.Item, "X")


# ---------------------------------------------------------------------------
# Expanded DRF scalar capability matrix - no catch-all
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
def test_expanded_scalar_matrix(field: DRFField, expected: object):
    """Each expanded-matrix scalar maps to its EXPLICIT annotation, kind ``scalar``.

    ``DictField`` -> ``JSON``; ``IPAddressField`` / ``FilePathField`` -> ``str``;
    ``DurationField`` -> ``str`` (a DELIBERATE scalar - DRF renders a duration as an
    ISO-8601-ish string on the wire, not an accidental fallthrough).
    """
    conversion = convert_serializer_field(bind_unparented(field, "f"))
    assert conversion.annotation == expected
    assert conversion.kind == SCALAR


def test_hstore_field_maps_to_json_via_mro():
    """``HStoreField`` (a ``DictField`` subclass) resolves to ``JSON`` through the MRO walk."""
    conversion = convert_serializer_field(bind_unparented(serializers.HStoreField(), "h"))
    assert conversion.annotation == strawberry.scalars.JSON
    assert conversion.kind == SCALAR


def test_model_field_maps_via_wrapped_model_field():
    """``ModelField`` resolves its scalar through the wrapped Django ``model_field`` (#7)."""
    field = serializers.ModelField(model_field=_concrete_field(product_models.Item, "name"))
    conversion = convert_serializer_field(bind_unparented(field, "nm"))
    assert conversion.annotation is str
    assert conversion.kind == SCALAR


def test_model_field_without_wrapped_field_raises():
    """A ``ModelField`` with no wrapped ``model_field`` fails loud (no scalar to resolve)."""
    # basedpyright: the missing wrapped model field is the hostile input under test; drf-stubs
    # types model_field as a Django Field
    field = serializers.ModelField(model_field=None)  # pyright: ignore[reportArgumentType]
    field.field_name = "x"
    with pytest.raises(ConfigurationError, match="ModelField with no wrapped model_field"):
        convert_serializer_field(field)


def test_model_field_over_unsupported_column_fails_loud():
    """A ``ModelField`` over an UNsupported column type raises (via ``scalar_for_field``, no ``String``)."""

    class WeirdField(models.Field[object, object]):
        pass

    weird = WeirdField()
    weird.set_attributes_from_name("weird")
    field = serializers.ModelField(model_field=weird)
    field.field_name = "weird"
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_serializer_field(field)


# ---------------------------------------------------------------------------
# Public converter registry - sanctioned extension, no catch-all
# ---------------------------------------------------------------------------


class _CustomHexField(serializers.Field[object, object, object, object]):
    """A custom DRF field whose MRO has NO supported ancestor (unregistered -> raises)."""

    @override
    def to_internal_value(self, data: object):  # never called in conversion.
        return data

    @override
    def to_representation(self, value: object):  # never called in conversion.
        return value


def test_unregistered_custom_field_raises_then_registered_maps(_restore_converter_registry: None):
    """A custom field raises until a converter is registered, then maps - and no catch-all appears."""
    # Unregistered: the fail-loud raise (no silent ``String``).
    with pytest.raises(
        ConfigurationError,
        match="Unsupported serializer field type '_CustomHexField'",
    ):
        convert_serializer_field(bind_unparented(_CustomHexField(), "c"))

    register_serializer_field_converter(
        _CustomHexField,
        lambda field: SerializerFieldConversion(annotation=str, required=field.required),
    )
    conversion = convert_serializer_field(bind_unparented(_CustomHexField(), "c"))
    assert conversion.annotation is str
    assert conversion.kind == SCALAR


def test_registered_converter_malformed_return_is_configuration_error(
    _restore_converter_registry: None,
):
    """A registered converter must return the typed scalar conversion value object."""
    # basedpyright: the converter returning None is the hostile input under test;
    # register_serializer_field_converter types the parameter as SerializerFieldConverter
    register_serializer_field_converter(_CustomHexField, lambda _field: None)  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError, match="must return SerializerFieldConversion"):
        convert_serializer_field(bind_unparented(_CustomHexField(), "c"))


def test_registered_converter_exception_is_wrapped_as_configuration_error(
    _restore_converter_registry: None,
):
    """A converter that raises is reported against the registry, not as its own exception."""

    def broken_converter(_field: DRFField):
        raise RuntimeError("converter failed")

    register_serializer_field_converter(_CustomHexField, broken_converter)
    with pytest.raises(ConfigurationError, match="raised RuntimeError"):
        convert_serializer_field(bind_unparented(_CustomHexField(), "c"))


def test_registered_converter_relation_kind_is_configuration_error(
    _restore_converter_registry: None,
):
    """A scalar registry extension cannot bypass framework-owned relation handling."""
    register_serializer_field_converter(
        _CustomHexField,
        lambda field: SerializerFieldConversion(
            annotation=None,
            kind=RELATION_SINGLE,
            required=field.required,
        ),
    )
    with pytest.raises(ConfigurationError, match="must return a scalar conversion"):
        convert_serializer_field(bind_unparented(_CustomHexField(), "c"))


def test_register_converter_resolves_unregistered_subclass_via_mro(
    _restore_converter_registry: None,
):
    """A registered converter also covers the field class's unregistered subclasses (MRO walk)."""
    register_serializer_field_converter(
        _CustomHexField,
        lambda field: SerializerFieldConversion(annotation=str, required=field.required),
    )

    class _CustomHexSubclass(_CustomHexField):
        pass

    assert convert_serializer_field(bind_unparented(_CustomHexSubclass(), "c")).annotation is str


def test_register_converter_override_guard(_restore_converter_registry: None):
    """Re-registering an already-mapped class raises unless ``override=True``."""

    def conv(field: DRFField) -> SerializerFieldConversion:
        return SerializerFieldConversion(annotation=int, required=field.required)

    with pytest.raises(ConfigurationError, match="already registered for 'CharField'"):
        register_serializer_field_converter(serializers.CharField, conv)
    # ``override=True`` replaces it.
    register_serializer_field_converter(serializers.CharField, conv, override=True)
    assert (
        convert_serializer_field(bind_unparented(serializers.CharField(), "f")).annotation is int
    )


@pytest.mark.parametrize(
    "field_class",
    [
        pytest.param(int, id="non-field-class"),
        # The likely slip: an instance where the class belongs. The class check runs
        # first, so ``issubclass`` never sees the instance and raises its bare ``TypeError``.
        pytest.param(serializers.CharField(), id="field-instance"),
    ],
)
def test_register_converter_rejects_non_field_class(
    _restore_converter_registry: None,
    field_class: object,
):
    """``field_class`` must be a ``serializers.Field`` subclass."""
    with pytest.raises(ConfigurationError, match="must be a serializers.Field subclass"):
        register_serializer_field_converter(
            # basedpyright: each non-class field_class is the hostile input under test;
            # register_serializer_field_converter types the parameter as type[object]
            field_class,  # pyright: ignore[reportArgumentType]
            lambda field: SerializerFieldConversion(annotation=str, required=field.required),
        )


def test_register_converter_rejects_non_callable(_restore_converter_registry: None):
    """``converter`` must be callable."""
    with pytest.raises(ConfigurationError, match="must be\n?.*callable|callable"):
        # basedpyright: the non-callable converter is the hostile input under test;
        # register_serializer_field_converter types the parameter as SerializerFieldConverter
        register_serializer_field_converter(_CustomHexField, "not-a-callable")  # pyright: ignore[reportArgumentType]


# ---------------------------------------------------------------------------
# Serializer-only ChoiceField -> generated enum
# ---------------------------------------------------------------------------


def test_serializer_only_choicefield_becomes_enum():
    """A serializer-only ``ChoiceField`` resolves to a generated GraphQL enum (schema precision)."""

    class ChoiceSer(serializers.Serializer[object]):
        color = serializers.ChoiceField(choices=[("r", "Red"), ("g", "Green")])

    field = ChoiceSer().fields["color"]
    _attr, annotation, spec = resolve_serializer_field(field, None, "X")
    assert spec.kind == SCALAR
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.value for member in annotation} == {"r", "g"}


def test_serializer_only_multiple_choicefield_becomes_list_enum():
    """A serializer-only ``MultipleChoiceField`` resolves to ``list[<enum>]``."""

    class MultiSer(serializers.Serializer[object]):
        tags = serializers.MultipleChoiceField(choices=[("a", "A"), ("b", "B")])

    field = MultiSer().fields["tags"]
    _attr, annotation, _spec = resolve_serializer_field(field, None, "X")
    assert get_origin(annotation) is list
    (inner,) = get_args(annotation)
    assert issubclass(inner, Enum)
    assert {member.value for member in inner} == {"a", "b"}


def test_serializer_only_multiple_choicefield_allow_blank_enum_has_blank_member():
    """``MultipleChoiceField(allow_blank=True)`` admits ``""`` per element, so its enum carries ``BLANK``."""

    class MultiSer(serializers.Serializer[object]):
        tags = serializers.MultipleChoiceField(choices=[("a", "A")], allow_blank=True)

    field = MultiSer().fields["tags"]
    _attr, annotation, _spec = resolve_serializer_field(field, None, "X")
    (inner,) = get_args(annotation)
    assert {member.name: member.value for member in inner} == {"BLANK": "", "a": "a"}


def test_declared_choicefield_allow_blank_over_model_column_enum_has_blank_member():
    """A declared ``ChoiceField(allow_blank=True)`` over a plain column emits its enum with ``BLANK``."""

    class DeclaredSer(serializers.ModelSerializer[library_models.Shelf]):
        topic = serializers.ChoiceField(choices=[("x", "X")], allow_blank=True)

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Shelf
            fields = ("topic",)

    field = DeclaredSer().fields["topic"]
    _attr, annotation, _spec = resolve_serializer_field(field, library_models.Shelf, "X")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.name: member.value for member in annotation} == {"BLANK": "", "x": "x"}


def _value_refusal(
    serializer_name: str,
    field_name: str,
    missing: str,
    column: str,
    remedy: str,
):
    them = "them" if ", " in missing else "it"
    return (
        f"Serializer {serializer_name} field {field_name!r} admits {missing} over the choice "
        f"column {column}, which does not list {them}. {remedy}"
    )


_BLANK_COLUMN_REMEDY = (
    "Set blank=True on the column, or drop allow_blank from the serializer field."
)


def test_declared_choice_allow_blank_over_strict_choice_column_refused():
    """``allow_blank=True`` over a ``blank=False`` choice column would write an unreadable ``""``."""

    class BlankStatusSer(serializers.ModelSerializer[library_models.Book]):
        circulation_status = serializers.ChoiceField(
            choices=[("available", "Available")],
            allow_blank=True,
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("circulation_status",)

    field = BlankStatusSer().fields["circulation_status"]
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_serializer_field(field, library_models.Book, "X")
    assert str(exc_info.value) == _value_refusal(
        "BlankStatusSer",
        "circulation_status",
        "''",
        "Book.circulation_status",
        _BLANK_COLUMN_REMEDY,
    )


def test_source_mapped_choice_allow_blank_over_strict_choice_column_refused():
    """The column is resolved through ``source``; the message names the declared field."""

    class RenamedStatusSer(serializers.ModelSerializer[library_models.Book]):
        status = serializers.ChoiceField(
            choices=[("available", "Available")],
            allow_blank=True,
            source="circulation_status",
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("status",)

    field = RenamedStatusSer().fields["status"]
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_serializer_field(field, library_models.Book, "X")
    assert str(exc_info.value) == _value_refusal(
        "RenamedStatusSer",
        "status",
        "''",
        "Book.circulation_status",
        _BLANK_COLUMN_REMEDY,
    )


def test_extra_kwargs_allow_blank_over_strict_choice_column_refused():
    """An auto-generated choice field given ``allow_blank`` by ``extra_kwargs`` is refused too."""

    class ExtraBlankSer(serializers.ModelSerializer[library_models.Book]):
        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("circulation_status",)
            extra_kwargs = {"circulation_status": {"allow_blank": True}}

    field = ExtraBlankSer().fields["circulation_status"]
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_serializer_field(field, library_models.Book, "X")
    assert str(exc_info.value) == _value_refusal(
        "ExtraBlankSer",
        "circulation_status",
        "''",
        "Book.circulation_status",
        _BLANK_COLUMN_REMEDY,
    )


@pytest.mark.parametrize(
    (
        "declared",
        "allow_blank",
        "missing",
        "remedy",
    ),
    [
        (
            [("", "-"), ("available", "Available")],
            False,
            "''",
            "Set blank=True on the column, or remove '' from the serializer field's choices.",
        ),
        (
            [("", "-"), ("available", "Available")],
            True,
            "''",
            "Set blank=True on the column, or remove '' from the serializer field's choices and "
            "drop allow_blank from the serializer field.",
        ),
        (
            [("available", "Available"), ("zz", "Z")],
            False,
            "'zz'",
            "Remove 'zz' from the serializer field's choices.",
        ),
        (
            [("zz", "Z"), ("available", "Available")],
            True,
            "'zz', ''",
            "Remove 'zz' from the serializer field's choices and drop allow_blank from the "
            "serializer field.",
        ),
    ],
    ids=[
        "declared-empty",
        "declared-empty-and-allow-blank",
        "unknown-value",
        "unknown-and-blank",
    ],
)
def test_declared_choice_value_missing_from_column_enum_refused(
    declared: list[tuple[str, str]],
    allow_blank: bool,
    missing: str,
    remedy: str,
):
    """Every value the serializer admits must be a member of the column's read enum."""

    class ValueSer(serializers.ModelSerializer[library_models.Book]):
        circulation_status = serializers.ChoiceField(choices=declared, allow_blank=allow_blank)

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("circulation_status",)

    field = ValueSer().fields["circulation_status"]
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_serializer_field(field, library_models.Book, "X")
    assert str(exc_info.value) == _value_refusal(
        "ValueSer",
        "circulation_status",
        missing,
        "Book.circulation_status",
        remedy,
    )


def _integer_choice_column(
    *,
    blank: bool = False,
    null: bool = False,
) -> models.IntegerField[object, object]:
    """An integer choice column bound to a real model (only ``__name__`` is read)."""
    column = models.IntegerField(choices=[(1, "One"), (2, "Two")], blank=blank, null=null)
    column.set_attributes_from_name("rank")
    column.model = product_models.Category
    return column


def test_allow_blank_over_blank_integer_choice_column_refused_without_blank_remedy():
    """An integer column never stores ``""``, so ``blank=True`` is no remedy: only the field is."""

    class RankSer(serializers.Serializer[object]):
        rank = serializers.ChoiceField(choices=[(1, "One")], allow_blank=True)

    column = _integer_choice_column(blank=True, null=True)
    with pytest.raises(ConfigurationError) as exc_info:
        serializer_converter._reject_choice_values_the_column_does_not_list(
            RankSer().fields["rank"],
            column,
        )
    assert str(exc_info.value) == _value_refusal(
        "RankSer",
        "rank",
        "''",
        "Category.rank",
        "Drop allow_blank from the serializer field.",
    )


def test_choice_values_compared_as_the_column_reads_them_back():
    """A declared ``"1"`` over an integer column is stored and read back as ``1``: accepted."""

    class RankSer(serializers.Serializer[object]):
        rank = serializers.ChoiceField(choices=[("1", "One"), (2, "Two")])

    serializer_converter._reject_choice_values_the_column_does_not_list(
        RankSer().fields["rank"],
        _integer_choice_column(),
    )


def test_integer_choices_column_accepts_its_own_choices():
    """An ``IntegerChoices`` column with a field declaring the same choices is accepted."""

    class Rank(models.IntegerChoices):
        LOW = 1, "Low"
        HIGH = 2, "High"

    class RankSer(serializers.Serializer[object]):
        rank = serializers.ChoiceField(choices=Rank.choices)

    column = models.IntegerField(choices=Rank.choices)
    column.set_attributes_from_name("rank")
    column.model = product_models.Category
    serializer_converter._reject_choice_values_the_column_does_not_list(
        RankSer().fields["rank"],
        column,
    )


def test_declared_choice_allow_blank_over_blank_choice_column_accepted():
    """Over a ``blank=True`` choice column both the input enum and the read enum carry ``BLANK``."""
    from django_strawberry_framework.types.converters import convert_choices_to_enum

    class ConditionSer(serializers.ModelSerializer[library_models.Shelf]):
        condition = serializers.ChoiceField(
            choices=library_models.Shelf.Condition.choices,
            allow_blank=True,
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Shelf
            fields = ("condition",)

    field = ConditionSer().fields["condition"]
    _attr, annotation, _spec = resolve_serializer_field(field, library_models.Shelf, "X")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    read_enum = convert_choices_to_enum(
        _concrete_field(library_models.Shelf, "condition"),
        "ShelfReadType",
    )
    assert {member.name: member.value for member in annotation}["BLANK"] == ""
    assert {member.name: member.value for member in read_enum}["BLANK"] == ""


def test_declared_choice_allow_blank_over_strict_non_choice_column_accepted():
    """A column without ``choices`` reads as ``String``, which carries ``""``: not refused.

    ``Book.title`` is ``blank=False``, so only the column's lack of ``choices`` keeps the
    declared field out of the refusal.
    """

    class TitleChoiceSer(serializers.ModelSerializer[library_models.Book]):
        title = serializers.ChoiceField(choices=[("dune", "Dune")], allow_blank=True)

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("title",)

    field = TitleChoiceSer().fields["title"]
    _attr, annotation, _spec = resolve_serializer_field(field, library_models.Book, "X")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.name: member.value for member in annotation} == {"BLANK": "", "dune": "dune"}


def test_serializer_only_choice_allow_blank_on_model_serializer_accepted():
    """A choice field with no backing column keeps the ``BLANK`` member ``allow_blank`` adds."""

    class ExtraChoiceSer(serializers.ModelSerializer[library_models.Book]):
        mood = serializers.ChoiceField(choices=[("calm", "Calm")], allow_blank=True)

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("mood",)

    field = ExtraChoiceSer().fields["mood"]
    _attr, annotation, _spec = resolve_serializer_field(field, library_models.Book, "X")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.name: member.value for member in annotation} == {"BLANK": "", "calm": "calm"}


class _Condition(models.TextChoices):
    __empty__ = "Unassessed"
    GOOD = "good", "Good"
    WORN = "worn", "Worn"


def test_auto_model_serializer_over_empty_label_column_builds_the_read_enum():
    """An auto ``ModelSerializer`` field over an ``__empty__`` column builds; ``None`` is no member.

    DRF copies the column's ``(None, "Unassessed")`` pair into the field's choices; the subset
    check leaves ``None`` to ``allow_null`` (the column's read enum has no member for it), so the
    field resolves to the column's read enum instead of being refused.
    """
    from django_strawberry_framework.types.converters import convert_choices_to_enum

    class AutoConditionSer(serializers.ModelSerializer[library_models.Shelf]):
        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Shelf
            fields = ("condition",)

    field = AutoConditionSer().fields["condition"]
    assert isinstance(field, serializers.ChoiceField)
    assert None in field.choices
    _attr, annotation, _spec = resolve_serializer_field(field, library_models.Shelf, "X")
    read_enum = convert_choices_to_enum(
        _concrete_field(library_models.Shelf, "condition"),
        "ShelfReadType",
    )
    assert annotation is read_enum
    assert [member.name for member in read_enum] == [
        "BLANK",
        "good",
        "worn",
        "damaged",
    ]


@pytest.mark.parametrize("allow_null", [False, True], ids=["strict", "allow-null"])
def test_serializer_only_choice_over_empty_label_choices_gets_no_none_member(allow_null: bool):
    """A serializer-only ``ChoiceField`` over ``__empty__`` choices publishes no ``_None`` member.

    ``None`` is the empty option's label; ``allow_null`` decides whether the field takes it,
    before the choices are read.
    """

    class MoodSer(serializers.Serializer[object]):
        mood = serializers.ChoiceField(choices=_Condition.choices, allow_null=allow_null)

    field = MoodSer().fields["mood"]
    _attr, annotation, _spec = resolve_serializer_field(field, None, "EmptyLabelX")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.name: member.value for member in annotation} == {"good": "good", "worn": "worn"}
    if allow_null:
        assert field.run_validation(None) is None
    else:
        with pytest.raises(serializers.ValidationError):
            field.run_validation(None)


def test_serializer_only_multiple_choice_over_empty_label_choices_keeps_a_non_null_element():
    """A serializer-only ``MultipleChoiceField`` element enum carries no ``_None`` member.

    The element stays non-null: ``allow_null`` on the field nulls the whole list, never an
    element.
    """

    class TagsSer(serializers.Serializer[object]):
        tags = serializers.MultipleChoiceField(choices=_Condition.choices)

    field = TagsSer().fields["tags"]
    _attr, annotation, _spec = resolve_serializer_field(field, None, "EmptyLabelTagsX")
    assert get_origin(annotation) is list
    (inner,) = get_args(annotation)
    assert {member.name: member.value for member in inner} == {"good": "good", "worn": "worn"}


def _multiple_choice_refusal(serializer_name: str, field_name: str) -> str:
    return (
        f"Serializer {serializer_name} field {field_name!r} is a MultipleChoiceField over the "
        "single-value choice column Book.circulation_status: it writes a list, which is not one "
        "of the column's choices. Declare a ChoiceField to write one value, or store many values "
        "in an ArrayField column whose base_field declares the choices."
    )


def _declared_multiple_choice_ser():
    class MultiStatusSer(serializers.ModelSerializer[library_models.Book]):
        circulation_status = serializers.MultipleChoiceField(
            choices=library_models.Book.CirculationStatus.choices,
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("circulation_status",)

    return MultiStatusSer, "circulation_status"


def _source_mapped_multiple_choice_ser():
    class MultiStatusSer(serializers.ModelSerializer[library_models.Book]):
        statuses = serializers.MultipleChoiceField(
            choices=library_models.Book.CirculationStatus.choices,
            source="circulation_status",
        )

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("statuses",)

    return MultiStatusSer, "statuses"


def _generated_multiple_choice_ser():
    class MultiStatusSer(serializers.ModelSerializer[library_models.Book]):
        serializer_choice_field = serializers.MultipleChoiceField

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = library_models.Book
            fields = ("circulation_status",)

    return MultiStatusSer, "circulation_status"


@pytest.mark.parametrize(
    "make_serializer",
    [
        _declared_multiple_choice_ser,
        _source_mapped_multiple_choice_ser,
        _generated_multiple_choice_ser,
    ],
    ids=["declared", "source-mapped", "serializer-choice-field"],
)
def test_multiple_choice_over_single_value_choice_column_refused(
    make_serializer: Callable[
        [],
        tuple[type[serializers.ModelSerializer[library_models.Book]], str],
    ],
):
    """A ``MultipleChoiceField`` stores its list as one value no member of the column's enum reads.

    Every choice it declares is a column choice, so only the list shape is refused.
    """
    serializer_cls, field_name = make_serializer()
    field = serializer_cls().fields[field_name]
    assert isinstance(field, serializers.MultipleChoiceField)
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_serializer_field(field, library_models.Book, "X")
    assert str(exc_info.value) == _multiple_choice_refusal("MultiStatusSer", field_name)


@pytest.mark.parametrize(
    ("model", "column_name"),
    [(library_models.Book, "title"), (scalar_models.ScalarSpecimen, "payload")],
    ids=["text-column", "json-column"],
)
def test_multiple_choice_over_column_without_choices_accepted(
    model: type[models.Model],
    column_name: str,
):
    """A column without ``choices`` has no read enum to hold the list to: the field is accepted."""
    meta = type("Meta", (), {"model": model, "fields": (column_name,)})
    multi_field = serializers.MultipleChoiceField(choices=[("a", "A"), ("b", "B")])
    serializer_cls = type(
        "ListColumnSer",
        (serializers.ModelSerializer,),
        {column_name: multi_field, "Meta": meta},
    )
    field = serializer_cls().fields[column_name]
    _attr, annotation, _spec = resolve_serializer_field(field, model, "X")
    assert get_origin(annotation) is list
    (inner,) = get_args(annotation)
    assert {member.value for member in inner} == {"a", "b"}


class _FakeArrayField(models.Field[object, object]):
    """An ``ArrayField`` stand-in: ``django.contrib.postgres`` needs a Postgres driver."""

    # basedpyright: verbatim forward to Field.__init__; object fails its typed params
    def __init__(self, base_field: models.Field[object, object], **kwargs: Any):  # pyright: ignore[reportExplicitAny]
        super().__init__(**kwargs)
        self.base_field = base_field


def _array_choice_column(monkeypatch: pytest.MonkeyPatch, *, blank: bool = False):
    """A ``tags`` array column whose ``base_field`` declares ``a`` / ``b``."""
    from django_strawberry_framework.types import converters

    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)
    element = models.CharField(max_length=5, choices=[("a", "A"), ("b", "B")], blank=blank)
    column = _FakeArrayField(element)
    for field in (column, element):
        field.set_attributes_from_name("tags")
        field.model = product_models.Category
    return column


# basedpyright: verbatim forward to MultipleChoiceField.__init__; object fails its typed params
def _multi_tags_field(**kwargs: Any) -> DRFField:  # pyright: ignore[reportExplicitAny]
    class TagsSer(serializers.Serializer[object]):
        tags = serializers.MultipleChoiceField(**kwargs)

    return TagsSer().fields["tags"]


def test_multiple_choice_over_array_choice_column_accepted(monkeypatch: pytest.MonkeyPatch):
    """Each element is stored through ``base_field``, whose enum carries every declared choice."""
    column = _array_choice_column(monkeypatch)
    field = _multi_tags_field(choices=[("a", "A"), ("b", "B")])
    annotation = serializer_converter._model_backed_scalar_annotation(field, column, "X")
    assert get_origin(annotation) is list
    (inner,) = get_args(annotation)
    assert {member.value for member in inner} == {"a", "b"}


@pytest.mark.parametrize(
    ("kwargs", "missing", "remedy"),
    [
        (
            {"choices": [("a", "A"), ("zz", "Z")]},
            "'zz'",
            "Remove 'zz' from the serializer field's choices.",
        ),
        ({"choices": [("a", "A")], "allow_blank": True}, "''", _BLANK_COLUMN_REMEDY),
    ],
    ids=["unknown-element", "blank-element"],
)
def test_multiple_choice_element_missing_from_array_base_enum_refused(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, object],
    missing: str,
    remedy: str,
):
    """An element value the ``base_field``'s read enum lacks is refused, named on the column."""
    column = _array_choice_column(monkeypatch)
    field = _multi_tags_field(**kwargs)
    with pytest.raises(ConfigurationError) as exc_info:
        serializer_converter._model_backed_scalar_annotation(field, column, "X")
    assert str(exc_info.value) == _value_refusal(
        "TagsSer",
        "tags",
        missing,
        "Category.tags",
        remedy,
    )


def test_multiple_choice_blank_element_over_blank_array_base_accepted(
    monkeypatch: pytest.MonkeyPatch,
):
    """A ``blank=True`` ``base_field`` reads ``""`` as ``BLANK``, so ``allow_blank`` is accepted."""
    column = _array_choice_column(monkeypatch, blank=True)
    field = _multi_tags_field(choices=[("a", "A")], allow_blank=True)
    annotation = serializer_converter._model_backed_scalar_annotation(field, column, "X")
    (inner,) = get_args(annotation)
    assert {member.name: member.value for member in inner} == {"BLANK": "", "a": "a"}


def test_multiple_choice_over_empty_label_array_base_accepted(monkeypatch: pytest.MonkeyPatch):
    """An ``__empty__`` ``base_field``'s ``(None, label)`` pair is no element value: accepted.

    The field's choices carry ``None`` from ``Choices.__empty__``; the element check leaves it to
    ``allow_null``, and the element enum has no ``_None`` member.
    """
    from django_strawberry_framework.types import converters

    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)
    element = models.CharField(max_length=5, choices=_Condition.choices)
    column = _FakeArrayField(element)
    for model_field in (column, element):
        model_field.set_attributes_from_name("tags")
        model_field.model = product_models.Category
    field = _multi_tags_field(choices=_Condition.choices)
    annotation = serializer_converter._model_backed_scalar_annotation(field, column, "X")
    (inner,) = get_args(annotation)
    assert {member.name: member.value for member in inner} == {"good": "good", "worn": "worn"}


_GROUPED_CHOICES = [("Fiction", [("a", "A"), ("b", "B")]), ("Other", [("c", "C")])]


def _grouped_choice_model():
    """A fresh model whose ``status`` column declares Django's grouped-choices form."""

    class GroupedShelf(models.Model):
        status = models.CharField(max_length=8, choices=_GROUPED_CHOICES)

        class Meta:
            app_label = "test_rest_framework_grouped_choices"

    return GroupedShelf


def _grouped_status_field(
    model: type[models.Model],
    choices: list[tuple[str, str]],
    *,
    allow_blank: bool = False,
) -> DRFField:
    """Bind a declared ``status`` serializer field over ``model``'s grouped column."""
    meta = type("Meta", (), {"model": model, "fields": ("status",)})
    status = serializers.ChoiceField(choices=choices, allow_blank=allow_blank)
    serializer_cls = type(
        "GroupedSer",
        (serializers.ModelSerializer,),
        {"status": status, "Meta": meta},
    )
    return serializer_cls().fields["status"]


@pytest.mark.parametrize(
    "declared",
    [[("a", "A"), ("b", "B")], [("c", "C"), ("a", "A")]],
    ids=["one-group", "across-groups"],
)
def test_declared_flat_choice_over_grouped_column_accepted(declared: list[tuple[str, str]]):
    """A declared flat ``ChoiceField`` is checked against the column's flattened values.

    The column lists ``a`` / ``b`` / ``c`` (Django's ``flatchoices``), so a field declaring a
    subset is accepted and keeps the serializer-only enum from its declared choices; the
    grouped form's lack of a read enum does not reach it.
    """
    model = _grouped_choice_model()
    field = _grouped_status_field(model, declared)
    _attr, annotation, _spec = resolve_serializer_field(field, model, "X")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert [member.value for member in annotation] == [value for value, _label in declared]
    assert registry.get_enum(model, "status") is None


@pytest.mark.parametrize(
    (
        "choices",
        "allow_blank",
        "missing",
        "remedy",
    ),
    [
        (
            [("a", "A"), ("zzz", "Z")],
            False,
            "'zzz'",
            "Remove 'zzz' from the serializer field's choices.",
        ),
        (
            [("a", "A")],
            True,
            "''",
            _BLANK_COLUMN_REMEDY,
        ),
    ],
    ids=["unlisted-value", "blank-over-strict"],
)
def test_declared_choice_over_grouped_column_value_the_column_does_not_list_refused(
    choices: list[tuple[str, str]],
    allow_blank: bool,
    missing: str,
    remedy: str,
):
    """A value outside the grouped column's flattened values is refused with the column fact."""
    model = _grouped_choice_model()
    field = _grouped_status_field(model, choices, allow_blank=allow_blank)
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_serializer_field(field, model, "X")
    assert str(exc_info.value) == _value_refusal(
        "GroupedSer",
        "status",
        missing,
        "GroupedShelf.status",
        remedy,
    )


def _grouped_read_enum_refusal(serializer_name: str, field_name: str, column: str) -> str:
    return (
        f"Serializer {serializer_name} field {field_name!r} takes the read enum of the choice "
        "column "
        f"{column}, which uses Django's grouped-choices form (nested tuples for option groups). "
        "Only the flat (value, label) form has a read enum; flatten the choices source, split "
        "into separate fields, or declare a flat ChoiceField on the serializer."
    )


def _generated_grouped_ser(model: type[models.Model]) -> DRFField:
    meta = type("Meta", (), {"model": model, "fields": ("status",)})
    serializer_cls = type("GeneratedSer", (serializers.ModelSerializer,), {"Meta": meta})
    return serializer_cls().fields["status"]


def _declared_char_grouped_ser(model: type[models.Model]) -> DRFField:
    meta = type("Meta", (), {"model": model, "fields": ("status",)})
    serializer_cls = type(
        "DeclaredCharSer",
        (serializers.ModelSerializer,),
        {"status": serializers.CharField(), "Meta": meta},
    )
    return serializer_cls().fields["status"]


@pytest.mark.parametrize(
    ("make_field", "serializer_name"),
    [(_generated_grouped_ser, "GeneratedSer"), (_declared_char_grouped_ser, "DeclaredCharSer")],
    ids=["generated-choice", "declared-char"],
)
def test_field_taking_the_read_enum_of_a_grouped_column_refused(
    make_field: Callable[[type[models.Model]], DRFField],
    serializer_name: str,
):
    """A field whose input type is the column's read enum is refused: a grouped column has none.

    The auto-generated ``ChoiceField`` carries DRF's flattened choices, which the column lists,
    so the value check passes and the read-enum refusal names the serializer-side remedy.
    """
    model = _grouped_choice_model()
    field = make_field(model)
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_serializer_field(field, model, "X")
    assert str(exc_info.value) == _grouped_read_enum_refusal(
        serializer_name,
        "status",
        "GroupedShelf.status",
    )


def _grouped_array_choice_column(monkeypatch: pytest.MonkeyPatch):
    """A ``tags`` array column whose ``base_field`` declares the grouped choices."""
    from django_strawberry_framework.types import converters

    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)
    element = models.CharField(max_length=8, choices=_GROUPED_CHOICES)
    column = _FakeArrayField(element)
    for model_field in (column, element):
        model_field.set_attributes_from_name("tags")
        model_field.model = product_models.Category
    return column


def test_multiple_choice_over_grouped_array_base_accepted(monkeypatch: pytest.MonkeyPatch):
    """Each element is checked against the grouped ``base_field``'s flattened values."""
    column = _grouped_array_choice_column(monkeypatch)
    field = _multi_tags_field(choices=[("a", "A")])
    annotation = serializer_converter._model_backed_scalar_annotation(field, column, "X")
    assert get_origin(annotation) is list
    (inner,) = get_args(annotation)
    assert [member.value for member in inner] == ["a"]


def test_multiple_choice_element_the_grouped_array_base_does_not_list_refused(
    monkeypatch: pytest.MonkeyPatch,
):
    """An element value outside the grouped ``base_field``'s flattened values is refused."""
    column = _grouped_array_choice_column(monkeypatch)
    field = _multi_tags_field(choices=[("zzz", "Z")])
    with pytest.raises(ConfigurationError) as exc_info:
        serializer_converter._model_backed_scalar_annotation(field, column, "X")
    assert str(exc_info.value) == _value_refusal(
        "TagsSer",
        "tags",
        "'zzz'",
        "Category.tags",
        "Remove 'zzz' from the serializer field's choices.",
    )


def test_list_field_over_grouped_array_base_refused(monkeypatch: pytest.MonkeyPatch):
    """A list field over the array would take the grouped ``base_field``'s read enum: refused."""
    column = _grouped_array_choice_column(monkeypatch)
    serializer_cls = type(
        "ListTagsSer",
        (serializers.Serializer,),
        {"tags": serializers.ListField(child=serializers.CharField())},
    )
    field = serializer_cls().fields["tags"]
    with pytest.raises(ConfigurationError) as exc_info:
        serializer_converter._model_backed_scalar_annotation(field, column, "X")
    assert str(exc_info.value) == _grouped_read_enum_refusal(
        "ListTagsSer",
        "tags",
        "Category.tags",
    )


def test_serializer_only_filepathfield_stays_str_not_enum():
    """A ``FilePathField`` (a ``ChoiceField`` subclass with DYNAMIC choices) stays ``str``, never an enum."""

    class PathSer(serializers.Serializer[object]):
        p = serializers.FilePathField(path="/tmp")

    field = PathSer().fields["p"]
    _attr, annotation, _spec = resolve_serializer_field(field, None, "X")
    assert annotation is str


def test_serializer_only_choice_enum_dedupes_by_name():
    """Two resolves of the same serializer-only choice field share ONE enum object (dedupe)."""

    def _resolve():
        class ChoiceSer(serializers.Serializer[object]):
            color = serializers.ChoiceField(choices=[("r", "Red"), ("g", "Green")])

        return resolve_serializer_field(ChoiceSer().fields["color"], None, "X")[1]

    assert _resolve() is _resolve()


def test_serializer_only_choice_enum_name_collision_with_diverging_members_raises():
    """Reusing an enum NAME with a DIFFERENT member set fails loud (no silent reuse)."""

    class SerA(serializers.Serializer[object]):
        color = serializers.ChoiceField(choices=[("r", "Red")])

    class SerB(serializers.Serializer[object]):
        color = serializers.ChoiceField(choices=[("b", "Blue")])

    resolve_serializer_field(SerA().fields["color"], None, "X")
    with pytest.raises(ConfigurationError, match="two different member sets"):
        resolve_serializer_field(SerB().fields["color"], None, "X")


# ---------------------------------------------------------------------------
# Model-backed type-override conflict policy
# ---------------------------------------------------------------------------


def test_consumer_declared_scalar_disagreeing_with_column_raises():
    """A consumer-declared field whose scalar disagrees with the model column fails loud."""
    _register_products_types()

    class MismatchSer(serializers.ModelSerializer[product_models.Item]):
        name = serializers.IntegerField()  # column is TextField -> str; declared int -> disagree.

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("name",)

    field = MismatchSer().fields["name"]
    with pytest.raises(ConfigurationError, match="disagrees with the backing model column"):
        resolve_serializer_field(field, product_models.Item, "X")


def test_consumer_declared_scalar_agreeing_with_column_ok():
    """A benign rename (``CharField`` over a text column) AGREES and resolves to the model scalar."""
    _register_products_types()

    class AgreeSer(serializers.ModelSerializer[product_models.Item]):
        display_name = serializers.CharField(source="name")

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
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

    class FileOverrideSer(serializers.ModelSerializer[product_models.Item]):
        attachment = serializers.FileField(source="name")

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("attachment",)

    field = FileOverrideSer().fields["attachment"]
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert spec.kind == SCALAR
    assert annotation is str


def test_auto_generated_model_field_is_not_conflict_checked():
    """An AUTO-generated ModelSerializer field routes through the model converter (no conflict check)."""
    _register_products_types()

    class AutoSer(serializers.ModelSerializer[product_models.Item]):
        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("name",)

    field = AutoSer().fields["name"]
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert spec.kind == SCALAR
    assert annotation is str


# ---------------------------------------------------------------------------
# DRF field metadata -> SDL description
# ---------------------------------------------------------------------------


def test_serializer_field_description_combines_help_text_and_constraints():
    """``help_text`` heads the description; a constraint summary is appended (#9)."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    field = bind_unparented(
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

    assert serializer_field_description(bind_unparented(serializers.CharField(), "f")) is None


def test_serializer_field_description_notes_numeric_bounds_and_allow_blank():
    """Numeric bounds + ``allow_blank`` are summarized even without help text (#9)."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    numeric = serializer_field_description(
        bind_unparented(serializers.IntegerField(min_value=0, max_value=9), "n"),
    )
    assert numeric == "Constraints: min_value=0, max_value=9."
    blank = serializer_field_description(
        bind_unparented(serializers.CharField(allow_blank=True), "b"),
    )
    assert blank == "Constraints: allow_blank=true."


def test_serializer_field_description_notes_allow_empty_false():
    """``allow_empty=False`` is included in the SDL metadata summary (#9)."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    field = bind_unparented(
        serializers.ListField(child=serializers.CharField(), allow_empty=False),
        "tags",
    )
    assert serializer_field_description(field) == "Constraints: allow_empty=false."


def test_serializer_field_description_hostile_metadata_is_configuration_error():
    """A hostile help-text descriptor cannot replace the typed schema error."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    class HostileText:
        def __bool__(self):
            raise KeyboardInterrupt("bool trap")

        @override
        def __str__(self):
            raise RuntimeError("str trap")

    # basedpyright: the raising help text is the hostile input under test; drf-stubs types
    # help_text as _StrOrPromise | None
    field = bind_unparented(serializers.CharField(help_text=HostileText()), "name")  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError, match="metadata that cannot be rendered"):
        serializer_field_description(field)


def test_serializer_field_description_handles_an_unreadable_field_name_in_diagnostic():
    """The diagnostic names an unreadable field as ``<unavailable>`` rather than raising itself."""
    from django_strawberry_framework.rest_framework.serializer_converter import (
        serializer_field_description,
    )

    class HostileField:
        @property
        def help_text(self):
            raise RuntimeError("help unavailable")

        @property
        def field_name(self):
            raise RuntimeError("name unavailable")

    with pytest.raises(ConfigurationError, match="Serializer field <unavailable>"):
        # basedpyright: the field whose reads raise is the hostile input under test;
        # serializer_field_description types the parameter as DRFField
        serializer_field_description(HostileField())  # pyright: ignore[reportArgumentType]


def test_declared_choicefield_over_model_column_emits_serializer_enum():
    """A declared ``ChoiceField(source=<model col>, choices=...)`` emits the serializer-only enum.

    The declared choices are a schema-affecting override: even mapped (via ``source``) to a
    plain non-choice model column, the field emits the GENERATED enum from its declared choices,
    never collapsing back to the column's ``String`` scalar.
    """
    _register_products_types()

    class ChoiceOverColumnSer(serializers.ModelSerializer[product_models.Item]):
        status = serializers.ChoiceField(source="name", choices=[("a", "A"), ("b", "B")])

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("status",)

    field = ChoiceOverColumnSer().fields["status"]
    _attr, annotation, spec = resolve_serializer_field(field, product_models.Item, "X")
    assert isinstance(annotation, type) and issubclass(annotation, Enum)
    assert {member.value for member in annotation} == {"a", "b"}
    assert spec.source == "name"  # still writes through to the model column


def test_non_relation_field_over_relation_column_fails_loud():
    """A non-relation field (e.g. CharField) explicitly mapped over a relation column raises ConfigurationError."""
    _register_products_types()

    class BadRelSer(serializers.ModelSerializer[product_models.Item]):
        category = serializers.CharField()

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("category",)

    field = BadRelSer().fields["category"]
    with pytest.raises(ConfigurationError, match="only PrimaryKeyRelatedField is supported"):
        resolve_serializer_field(field, product_models.Item, "BadRelInput")


def test_consumer_declared_scalar_disagreeing_with_choices_column_fails_loud():
    """A consumer-declared field whose scalar disagrees with a choices column fails loud."""
    _register_products_types()

    from apps.library.models import Book

    class BookStatusSer(serializers.ModelSerializer[Book]):
        circulation_status = serializers.IntegerField()

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = Book
            fields = ("circulation_status",)

    field = BookStatusSer().fields["circulation_status"]
    with pytest.raises(ConfigurationError, match="disagrees with the backing model column"):
        resolve_serializer_field(field, Book, "BookStatusSerInput")


def test_list_field_with_no_child_raises_configuration_error():
    """ListField with default child=None raises ConfigurationError requesting a typed child."""
    field = bind_unparented(serializers.ListField(), "tags")
    with pytest.raises(ConfigurationError, match="ListField with no explicit child field"):
        convert_serializer_field(field)


def test_unsupported_serializer_field_without_field_name_raises_cleanly():
    """An unmapped serializer field without field_name raises ConfigurationError without AttributeError."""

    class CustomUnsupported(serializers.Field[object, object, object, object]):
        pass

    field = CustomUnsupported()
    with pytest.raises(
        ConfigurationError,
        match="Unsupported serializer field type 'CustomUnsupported'",
    ):
        convert_serializer_field(field)


def test_unsupported_serializer_field_with_hostile_field_name_repr():
    """An unmapped serializer field with a hostile field_name repr raises ConfigurationError with <unavailable>."""

    class HostileRepr:
        @override
        def __repr__(self):
            raise RuntimeError("hostile repr")

    class HostileField(serializers.Field[object, object, object, object]):
        pass

    field = HostileField()
    # basedpyright: the hostile field_name is the input under test; DRF types the slot as
    # str | None
    field.field_name = HostileRepr()  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(
        ConfigurationError,
        match="on serializer field <unavailable>",
    ):
        convert_serializer_field(field)


def test_backing_model_field_nonexistent_column_returns_none():
    """A serializer field referencing a non-existent model field returns None."""

    class MissingFieldSer(serializers.ModelSerializer[product_models.Item]):
        extra = serializers.CharField(source="nonexistent_column")

        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            fields = ("extra",)

    field = MissingFieldSer().fields["extra"]
    assert backing_model_field(product_models.Item, field) is None


def test_resolve_serializer_field_model_backed_file_field():
    """A FileField backed by a models.FileField resolves to Upload annotation and kind FILE."""

    from apps.scalars.models import MediaSpecimen

    class MediaSpecimenSer(serializers.ModelSerializer[MediaSpecimen]):
        # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = MediaSpecimen
            fields = ("attachment",)

    field = MediaSpecimenSer().fields["attachment"]
    python_attr, annotation, spec = resolve_serializer_field(
        field,
        MediaSpecimen,
        "MediaSpecimenSerInput",
    )
    assert python_attr == "attachment"
    assert annotation is Upload
    assert spec.kind == FILE
    assert spec.graphql_name == "attachment"


def test_resolve_serializer_field_column_less_file_field():
    """A FileField on a plain Serializer resolves to Upload annotation and kind FILE."""

    class PlainFileSer(serializers.Serializer[object]):
        avatar = serializers.FileField()

    field = PlainFileSer().fields["avatar"]
    python_attr, annotation, spec = resolve_serializer_field(field, None, "PlainFileInput")
    assert python_attr == "avatar"
    assert annotation is Upload
    assert spec.kind == FILE
    assert spec.graphql_name == "avatar"
