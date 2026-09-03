"""Mutation input tests for generated Input/PartialInput, FieldError, and the payload wrapper.

Covers the spec-036 generation substrate
(``django_strawberry_framework/mutations/inputs.py``):

- ``editable_input_fields`` selection (pk / auto-timestamp / reverse exclusion,
  M2M inclusion, ``fields`` / ``exclude`` narrowing + unknown-name rejection);
- ``input_field_required`` (the create-required rule);
- ``build_mutation_input`` create vs partial shapes, FK/O2O ``<field>_id`` mapping,
  M2M ``list[<id>]``, Relay-vs-non-Relay id type, and the consumer-override seam;
- ``mutation_input_type_name`` stable full-shape names + shape-derived narrowed
  names, with dedupe + the distinct-shape collision ``ConfigurationError`` via
  ``materialize_mutation_input_class``;
- the ``FileField`` / ``ImageField`` -> ``Upload`` input mapping (required /
  optional shapes, ``| None`` widening, ``Meta.fields`` / ``Meta.exclude``
  narrowing, and the lifted spec-036 merge-override carve-out)
  (spec-037);
- ``FieldError`` / ``build_payload_type`` envelope shape + the ``node`` / ``result``
  slot;
- the ``FieldError`` public export.

System-under-test is the generator itself, run against the realistic products
``Item`` / ``Category`` FK fixtures plus minimal package-local fixture models for
the M2M, non-Relay-target, and ``FileField`` / ``ImageField`` shapes products does
not carry (spec-036 test plan; products is every-Relay and has no M2M /
file field).
"""

from __future__ import annotations

import itertools

import pytest
import strawberry
from apps.products import models as product_models
from apps.products.schema import CategoryType, ItemType
from django.db import models
from strawberry import UNSET, relay
from strawberry.types.base import StrawberryList, StrawberryOptional

import django_strawberry_framework
from django_strawberry_framework import DjangoType, strawberry_config
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations import FieldError as FieldErrorFromPackage
from django_strawberry_framework.mutations.inputs import (
    CREATE,
    EXCLUDED,
    INPUTS_MODULE_PATH,
    NON_FIELD_ERROR_KEY,
    PARTIAL,
    FieldError,
    annotate_queryset_relation,
    build_mutation_input,
    build_payload_type,
    clear_mutation_input_namespace,
    editable_input_fields,
    input_field_required,
    materialize_mutation_input_class,
    model_column_input_annotation,
    model_column_write_annotation,
    model_column_write_kind,
    mutation_input_field_specs,
    mutation_input_type_name,
    payload_object_slot,
    related_model_of_queryset,
    relation_id_annotation,
    relation_id_scalar,
    require_queryset_related_model,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.scalars import Upload


@pytest.fixture(autouse=True)
def _isolate_registry_and_ledger():
    """Reset registry + the mutation-input ledger so each test starts clean.

    ``clear_mutation_input_namespace`` is not wired into
    ``registry.clear()`` here, so the ledger is cleared explicitly
    here. ``registry.clear()`` is still needed because the products
    ``DjangoType``s and the local fixtures register themselves on import /
    declaration.
    """
    registry.clear()
    clear_mutation_input_namespace()
    yield
    registry.clear()
    clear_mutation_input_namespace()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_mutation_inputs__{next(_app_label_counter)}"


def _field_map(input_cls: type) -> dict[str, object]:
    """Return ``python_name -> StrawberryField`` for a built input class."""
    return {f.python_name: f for f in input_cls.__strawberry_definition__.fields}


def _is_optional(field) -> bool:
    """Return whether a Strawberry field's annotation is ``T | None``."""
    return isinstance(field.type, StrawberryOptional)


def _inner_type(field):
    """Return the inner type of a ``StrawberryOptional`` field, else the type itself."""
    return field.type.of_type if isinstance(field.type, StrawberryOptional) else field.type


# ---------------------------------------------------------------------------
# Module-path constant
# ---------------------------------------------------------------------------


def test_inputs_module_path_constant():
    """The hoisted constant matches the actual dotted path of ``inputs.py``."""
    assert INPUTS_MODULE_PATH == "django_strawberry_framework.mutations.inputs"


def test_non_field_error_key_is_django_all_sentinel():
    """The non-field error key is pinned to Django's ``"__all__"`` sentinel."""
    assert NON_FIELD_ERROR_KEY == "__all__"


# ---------------------------------------------------------------------------
# editable_input_fields - selection
# ---------------------------------------------------------------------------


def test_editable_fields_exclude_pk_auto_timestamps_and_reverse_relations():
    """pk, ``auto_now`` / ``auto_now_add`` (``editable=False``), and reverse FKs are dropped."""
    names = [f.name for f in editable_input_fields(product_models.Item)]
    # Kept: editable columns + the forward FK.
    assert names == [
        "name",
        "description",
        "category",
        "attachment",
        "is_private",
    ]
    # Dropped explicitly.
    assert "id" not in names  # auto pk (editable=True but primary_key)
    assert "created_date" not in names  # auto_now_add / editable=False
    assert "updated_date" not in names  # auto_now / editable=False
    assert "entries" not in names  # reverse FK


def test_editable_fields_narrow_by_fields():
    """``fields`` narrows to the named columns in the given order."""
    names = [
        f.name for f in editable_input_fields(product_models.Item, fields=("name", "category"))
    ]
    assert names == ["name", "category"]


def test_editable_fields_freezes_one_shot_sequences():
    """One-shot ``fields`` / ``exclude`` iterables survive validation and narrowing."""
    selected = editable_input_fields(
        product_models.Item,
        fields=iter(("name", "category")),
    )
    excluded = editable_input_fields(
        product_models.Item,
        exclude=iter(("description", "is_private")),
    )
    assert [field.name for field in selected] == ["name", "category"]
    assert [field.name for field in excluded] == ["name", "category", "attachment"]


def test_editable_fields_narrow_by_exclude():
    """``exclude`` drops the named columns, preserving declaration order."""
    names = [
        f.name
        for f in editable_input_fields(product_models.Item, exclude=("description", "is_private"))
    ]
    assert names == ["name", "category", "attachment"]


def test_editable_fields_rejects_fields_and_exclude_together():
    """Declaring both ``fields`` and ``exclude`` raises ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):
        editable_input_fields(product_models.Item, fields=("name",), exclude=("description",))


def test_editable_fields_rejects_unknown_fields_name():
    """An unknown / non-editable name in ``fields`` raises ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="unknown field"):
        editable_input_fields(product_models.Item, fields=("name", "created_date"))


def test_editable_fields_rejects_unknown_exclude_name():
    """An unknown / non-editable name in ``exclude`` raises ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="unknown field"):
        editable_input_fields(product_models.Item, exclude=("nope",))


def test_editable_fields_excludes_non_editable_many_to_many():
    """A ManyToManyField declared with ``editable=False`` is excluded from editable_input_fields."""

    class Tag(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            app_label = _unique_app_label()

    class Article(models.Model):
        title = models.CharField(max_length=100)
        editable_tags = models.ManyToManyField(Tag, related_name="editable_articles")
        non_editable_tags = models.ManyToManyField(
            Tag,
            related_name="non_editable_articles",
            editable=False,
        )

        class Meta:
            app_label = _unique_app_label()

    fields = editable_input_fields(Article)
    field_names = [f.name for f in fields]
    assert "title" in field_names
    assert "editable_tags" in field_names
    assert "non_editable_tags" not in field_names

    with pytest.raises(ConfigurationError, match="non-editable or unknown field"):
        editable_input_fields(Article, fields=("title", "non_editable_tags"))

    with pytest.raises(ConfigurationError, match="non-editable or unknown field"):
        editable_input_fields(Article, exclude=("non_editable_tags",))


# ---------------------------------------------------------------------------
# input_field_required - the create-required rule
# ---------------------------------------------------------------------------


def test_input_field_required_rule():
    """Required only with no usable default: no ``default`` / ``blank`` / ``null``."""
    by_name = {f.name: f for f in editable_input_fields(product_models.Item)}
    assert input_field_required(by_name["name"]) is True  # TextField, no default
    assert input_field_required(by_name["description"]) is False  # blank=True, default=""
    assert input_field_required(by_name["is_private"]) is False  # default=False


# ---------------------------------------------------------------------------
# build_mutation_input - create / partial shapes
# ---------------------------------------------------------------------------


def test_create_input_required_and_optional_shapes():
    """ItemInput: name + categoryId required; description / isPrivate optional + UNSET.

    The FK ``category_id`` is required (no usable default) and camelCases to
    ``categoryId``; its id TYPE (GlobalID vs raw pk) is pinned by the dedicated
    Relay-vs-non-Relay tests, which control the related primary's Relay shape
    without depending on finalization injecting ``relay.Node`` into the products
    types' ``__bases__``.
    """
    cls = build_mutation_input(product_models.Item, operation_kind=CREATE, primary_type=ItemType)
    fields = _field_map(cls)

    assert not _is_optional(fields["name"])
    assert _inner_type(fields["name"]) is str

    assert not _is_optional(fields["category_id"])
    assert fields["category_id"].graphql_name == "categoryId"

    assert _is_optional(fields["description"])
    assert _inner_type(fields["description"]) is str
    assert fields["description"].default is UNSET

    assert _is_optional(fields["is_private"])
    assert _inner_type(fields["is_private"]) is bool
    assert fields["is_private"].default is UNSET
    assert fields["is_private"].graphql_name == "isPrivate"

    # The auto pk / timestamps never reach the input.
    assert "id" not in fields
    assert "created_date" not in fields
    assert "updated_date" not in fields


def test_partial_input_all_fields_optional_and_unset():
    """ItemPartialInput: every field optional + UNSET-defaulted, incl. name / categoryId."""
    cls = build_mutation_input(product_models.Item, operation_kind=PARTIAL, primary_type=ItemType)
    fields = _field_map(cls)
    for name in (
        "name",
        "description",
        "category_id",
        "is_private",
    ):
        assert _is_optional(fields[name]), name
        assert fields[name].default is UNSET, name


def test_create_input_name_is_canonical_model_input():
    """The full editable shape takes the stable ``<Model>Input`` name."""
    cls = build_mutation_input(product_models.Item, operation_kind=CREATE, primary_type=ItemType)
    assert cls.__name__ == "ItemInput"


def test_partial_input_name_is_canonical_model_partial_input():
    """The full editable shape takes the stable ``<Model>PartialInput`` name."""
    cls = build_mutation_input(product_models.Item, operation_kind=PARTIAL, primary_type=ItemType)
    assert cls.__name__ == "ItemPartialInput"


# ---------------------------------------------------------------------------
# relation_id_scalar / relation_id_annotation (write-flavor id-type owner)
# ---------------------------------------------------------------------------


def test_relation_id_scalar_is_globalid_iff_primary_is_relay():
    """Relay primary -> GlobalID; non-Relay or missing primary -> raw pk scalar."""
    relay_model, relay_type = _make_relay_target()
    assert relation_id_scalar(relay_model, relay_type) is relay.GlobalID
    plain_model, plain_type = _make_non_relay_target()
    assert relation_id_scalar(plain_model, plain_type) is int
    assert relation_id_scalar(plain_model, None) is int


def test_relation_id_annotation_wraps_multi_as_list_of_the_same_scalar():
    """Cardinality wrap is the only extra axis on top of ``relation_id_scalar``."""
    relay_model, relay_type = _make_relay_target()
    assert relation_id_annotation(relay_model, relay_type, many=False) is relay.GlobalID
    assert relation_id_annotation(relay_model, relay_type, many=True) == list[relay.GlobalID]
    plain_model, _plain_type = _make_non_relay_target()
    assert relation_id_annotation(plain_model, None, many=False) is int
    assert relation_id_annotation(plain_model, None, many=True) == list[int]


class _QuerySet:
    """Minimal queryset stand-in for column-less related-model discovery tests."""

    def __init__(self, model: type | None = None) -> None:
        self.model = model


def test_related_model_of_queryset_reads_model_or_none():
    """``queryset.model`` is the column-less related-model basis; missing stays ``None``."""

    class Target:
        pass

    assert related_model_of_queryset(_QuerySet(Target)) is Target
    assert related_model_of_queryset(None) is None
    assert related_model_of_queryset(_QuerySet(None)) is None


def test_require_queryset_related_model_raises_flavor_error_when_untyped():
    """Missing ``queryset.model`` raises the caller's configuration error, not AttributeError."""
    with pytest.raises(ConfigurationError, match="missing qs"):
        require_queryset_related_model(
            None,
            missing=lambda: ConfigurationError("missing qs"),
        )


def test_annotate_queryset_relation_packages_id_type_and_related_model():
    """Column-less wrap returns ``(python_attr, annotation, related_model)`` over the shared id type."""
    relay_model, relay_type = _make_relay_target()
    python_attr, annotation, related_model = annotate_queryset_relation(
        _QuerySet(relay_model),
        many=False,
        python_attr="target_id",
        primary_of=lambda _model: relay_type,
        missing=lambda: ConfigurationError("untyped"),
    )
    assert python_attr == "target_id"
    assert annotation is relay.GlobalID
    assert related_model is relay_model

    python_attr, annotation, related_model = annotate_queryset_relation(
        _QuerySet(relay_model),
        many=True,
        python_attr="targets",
        primary_of=lambda _model: relay_type,
        missing=lambda: ConfigurationError("untyped"),
    )
    assert python_attr == "targets"
    assert annotation == list[relay.GlobalID]
    assert related_model is relay_model


def test_form_and_serializer_column_less_relation_share_queryset_annotation():
    """Form and serializer column-less relation helpers import the same owner."""
    from django_strawberry_framework.forms import inputs as form_inputs
    from django_strawberry_framework.rest_framework import (
        serializer_converter as ser_converter,
    )

    assert form_inputs.annotate_queryset_relation is annotate_queryset_relation
    assert ser_converter.annotate_queryset_relation is annotate_queryset_relation


# ---------------------------------------------------------------------------
# model_column_input_annotation - non-relation column typing
# ---------------------------------------------------------------------------


def test_model_column_input_annotation_maps_file_and_scalar_columns():
    """A non-relation column types as ``Upload`` when it is a file, else ``convert_scalar``."""
    from django_strawberry_framework.types.converters import convert_scalar

    class Probe(models.Model):
        name = models.TextField()
        attachment = models.FileField()

        class Meta:
            app_label = _unique_app_label()

    python_attr, graphql_name, annotation = model_column_input_annotation(
        Probe._meta.get_field("attachment"),
        "ProbeInput",
        primary_of=lambda _model: None,
    )
    assert python_attr == "attachment"
    assert graphql_name == "attachment"
    assert annotation is Upload

    name_field = Probe._meta.get_field("name")
    python_attr, graphql_name, annotation = model_column_input_annotation(
        name_field,
        "ProbeInput",
        primary_of=lambda _model: None,
    )
    assert python_attr == "name"
    assert graphql_name == "name"
    assert annotation == convert_scalar(name_field, "ProbeInput", force_nullable=False)


def test_model_column_write_kind_classifies_relation_file_and_scalar():
    """A backing column is relation / file / scalar by the one shared classifier."""
    from django_strawberry_framework.utils.inputs import (
        FILE,
        RELATION_MULTI,
        RELATION_SINGLE,
        SCALAR,
    )

    class Probe(models.Model):
        name = models.TextField()
        attachment = models.FileField()
        parent = models.ForeignKey("self", on_delete=models.CASCADE)
        peers = models.ManyToManyField("self")

        class Meta:
            app_label = _unique_app_label()

    assert model_column_write_kind(Probe._meta.get_field("name")) == SCALAR
    assert model_column_write_kind(Probe._meta.get_field("attachment")) == FILE
    assert model_column_write_kind(Probe._meta.get_field("parent")) == RELATION_SINGLE
    assert model_column_write_kind(Probe._meta.get_field("peers")) == RELATION_MULTI


def test_model_column_write_annotation_maps_file_and_scalar():
    """Annotation-only mapping is Upload for a file column, else convert_scalar."""
    from django_strawberry_framework.types.converters import convert_scalar

    class Probe(models.Model):
        name = models.TextField()
        attachment = models.FileField()

        class Meta:
            app_label = _unique_app_label()

    attachment = Probe._meta.get_field("attachment")
    assert (
        model_column_write_annotation(
            attachment,
            "ProbeInput",
            primary_of=lambda _model: None,
        )
        is Upload
    )
    name_field = Probe._meta.get_field("name")
    assert model_column_write_annotation(
        name_field,
        "ProbeInput",
        primary_of=lambda _model: None,
    ) == convert_scalar(name_field, "ProbeInput", force_nullable=False)


def test_form_and_serializer_column_kind_share_model_column_owner():
    """Form reverse-map kind and serializer column resolve import the same owners."""
    from django_strawberry_framework.forms import inputs as form_inputs
    from django_strawberry_framework.rest_framework import (
        serializer_converter as ser_converter,
    )

    assert form_inputs.model_column_write_kind is model_column_write_kind
    assert ser_converter.model_column_write_kind is model_column_write_kind
    assert ser_converter.model_column_write_annotation is model_column_write_annotation


# ---------------------------------------------------------------------------
# build_mutation_input - relation id mapping (FK + M2M, Relay vs non-Relay)
# ---------------------------------------------------------------------------


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


def _make_non_relay_target():
    """A registered non-Relay ``DjangoType`` over a fresh model (raw int pk)."""

    class PlainTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = _unique_app_label()

    class PlainTargetType(DjangoType):
        class Meta:
            model = PlainTarget
            fields = ("id", "name")

    return PlainTarget, PlainTargetType


def test_fk_to_relay_target_uses_globalid_id():
    """A forward FK to a Relay-Node primary becomes ``<field>_id: GlobalID``."""
    relay_target, _ = _make_relay_target()

    class Owner(models.Model):
        rel = models.ForeignKey(relay_target, on_delete=models.CASCADE)

        class Meta:
            app_label = _unique_app_label()

    class OwnerType(DjangoType, relay.Node):
        class Meta:
            model = Owner
            fields = ("id",)

    cls = build_mutation_input(Owner, operation_kind=CREATE, primary_type=OwnerType)
    fields = _field_map(cls)
    assert "rel_id" in fields
    assert _inner_type(fields["rel_id"]) is relay.GlobalID
    assert fields["rel_id"].graphql_name == "relId"


# ---------------------------------------------------------------------------
# ``Meta.interfaces``-declared Relay targets: the phase-2.5 ordering dependency
#
# ``Meta.interfaces = (relay.Node,)`` is the documented consumer surface and the
# route every fakeshop type uses, but ``relay.Node`` reaches the declaring type's
# MRO only when ``finalize_django_types`` runs ``apply_interfaces``. Both the
# relation-id scalar (``relation_id_scalar``) and the payload object slot
# (``payload_object_slot``) gate on ``implements_relay_node``, which READS that MRO,
# and the mutation bind that consumes both is a LATER phase-2.5 step. Hoist the bind
# above ``apply_interfaces`` and every ``Meta.interfaces``-declared type silently
# degrades - a relation input to a raw pk (defeating the ``GlobalID``-shaped
# visibility check in ``decode_visible_relation_ids``) and a payload to the
# ``result`` slot. The other Relay rows in this module inherit ``relay.Node``
# directly, for which the predicate is true from class creation, so the ordering is
# unobservable there; these two rows are the only package-tier witnesses.
# ---------------------------------------------------------------------------


def _declare_meta_interfaces_mutation():
    """Declare an FK-to-``Meta.interfaces``-target create mutation and finalize.

    Returns ``(CreateOwner, InterfacesTargetType, OwnerType)`` after
    ``finalize_django_types()``, asserting on the way through that the declared
    interface was NOT in the MRO beforehand - the injection is what phase 2.5
    performs and what the bind must see.
    """
    from django_strawberry_framework import DjangoMutation, finalize_django_types

    class InterfacesTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = _unique_app_label()

    class InterfacesTargetType(DjangoType):
        class Meta:
            model = InterfacesTarget
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class Owner(models.Model):
        rel = models.ForeignKey(InterfacesTarget, on_delete=models.CASCADE)

        class Meta:
            app_label = _unique_app_label()

    class OwnerType(DjangoType):
        class Meta:
            model = Owner
            fields = ("id",)
            interfaces = (relay.Node,)

    class CreateOwner(DjangoMutation):
        class Meta:
            model = Owner
            operation = "create"

    assert not issubclass(InterfacesTargetType, relay.Node)
    assert not issubclass(OwnerType, relay.Node)

    finalize_django_types()

    return CreateOwner, InterfacesTargetType, OwnerType


def test_fk_to_meta_interfaces_relay_target_uses_globalid_id():
    """A target declaring Relay through ``Meta.interfaces`` gets a ``GlobalID`` relation id."""
    create_owner, target_type, owner_type = _declare_meta_interfaces_mutation()

    assert issubclass(target_type, relay.Node)
    assert issubclass(owner_type, relay.Node)
    fields = _field_map(create_owner._input_class)
    assert "rel_id" in fields
    assert _inner_type(fields["rel_id"]) is relay.GlobalID


def test_meta_interfaces_primary_binds_a_node_slot_payload():
    """A primary declaring Relay through ``Meta.interfaces`` binds a ``node``-slot payload.

    The second, independent consequence of the same injection reaching the bind:
    ``payload_object_slot`` returns ``"node"`` only for a Relay-Node target, so a
    payload materialized before ``apply_interfaces`` carries ``result`` instead -
    a breaking wire change on every ``Meta.interfaces``-declared mutation target.
    Pinned separately from the relation-id row above because the two read the
    predicate at different call sites.
    """
    from django_strawberry_framework.mutations.inputs import _materialized_names

    create_owner, _target_type, owner_type = _declare_meta_interfaces_mutation()

    assert payload_object_slot(owner_type) == "node"
    payload = _materialized_names[create_owner._payload_type_name]
    payload_fields = {f.python_name for f in payload.__strawberry_definition__.fields}
    assert "node" in payload_fields
    assert "result" not in payload_fields


def test_fk_to_non_relay_target_uses_raw_pk_scalar():
    """A forward FK to a non-Relay primary becomes ``<field>_id`` of the raw pk scalar."""
    plain_target, _ = _make_non_relay_target()

    class Owner(models.Model):
        rel = models.ForeignKey(plain_target, on_delete=models.CASCADE)

        class Meta:
            app_label = _unique_app_label()

    class OwnerType(DjangoType, relay.Node):
        class Meta:
            model = Owner
            fields = ("id",)

    cls = build_mutation_input(Owner, operation_kind=CREATE, primary_type=OwnerType)
    fields = _field_map(cls)
    # AutoField pk -> int raw scalar (NOT GlobalID).
    assert _inner_type(fields["rel_id"]) is int


def test_o2o_to_relay_target_uses_globalid_id():
    """A forward OneToOne to a Relay-Node primary also becomes ``<field>_id: GlobalID``."""
    relay_target, _ = _make_relay_target()

    class Profile(models.Model):
        owner = models.OneToOneField(relay_target, on_delete=models.CASCADE)

        class Meta:
            app_label = _unique_app_label()

    class ProfileType(DjangoType, relay.Node):
        class Meta:
            model = Profile
            fields = ("id",)

    cls = build_mutation_input(Profile, operation_kind=CREATE, primary_type=ProfileType)
    fields = _field_map(cls)
    assert _inner_type(fields["owner_id"]) is relay.GlobalID


def test_m2m_to_relay_target_becomes_list_of_globalid():
    """A forward M2M to a Relay-Node primary becomes ``list[GlobalID]`` (and is optional)."""
    relay_target, _ = _make_relay_target()

    class Owner(models.Model):
        tags = models.ManyToManyField(relay_target)

        class Meta:
            app_label = _unique_app_label()

    class OwnerType(DjangoType, relay.Node):
        class Meta:
            model = Owner
            fields = ("id",)

    cls = build_mutation_input(Owner, operation_kind=CREATE, primary_type=OwnerType)
    fields = _field_map(cls)
    assert "tags" in fields
    # M2M is always optional (resolver replace/clear/omit contract).
    assert _is_optional(fields["tags"])
    list_part = fields["tags"].type.of_type
    assert isinstance(list_part, StrawberryList)
    assert list_part.of_type is relay.GlobalID


def test_m2m_to_non_relay_target_becomes_list_of_raw_pk():
    """A forward M2M to a non-Relay primary becomes ``list[<pk scalar>]``."""
    plain_target, _ = _make_non_relay_target()

    class Owner(models.Model):
        tags = models.ManyToManyField(plain_target)

        class Meta:
            app_label = _unique_app_label()

    class OwnerType(DjangoType, relay.Node):
        class Meta:
            model = Owner
            fields = ("id",)

    cls = build_mutation_input(Owner, operation_kind=CREATE, primary_type=OwnerType)
    fields = _field_map(cls)
    list_part = fields["tags"].type.of_type
    assert isinstance(list_part, StrawberryList)
    assert list_part.of_type is int


# ---------------------------------------------------------------------------
# Consumer-override seam (spec-010 relation-override)
# ---------------------------------------------------------------------------


def test_consumer_override_skips_generated_field():
    """A python attr in ``overrides`` is skipped so a consumer field is not clobbered."""
    cls = build_mutation_input(
        product_models.Item,
        operation_kind=CREATE,
        primary_type=ItemType,
        overrides=frozenset({"category_id"}),
    )
    fields = _field_map(cls)
    assert "category_id" not in fields
    # The non-overridden columns still generate.
    assert "name" in fields


def test_consumer_override_freezes_one_shot_iterable():
    """Every attr in a direct iterable override is skipped from the generated remainder."""
    cls = build_mutation_input(
        product_models.Item,
        operation_kind=CREATE,
        primary_type=ItemType,
        overrides=iter(("category_id", "attachment")),
    )
    fields = _field_map(cls)
    assert "category_id" not in fields
    assert "attachment" not in fields
    assert "name" in fields


# ---------------------------------------------------------------------------
# build_mutation_input - generated-field collision guard (silent-drop parity)
# ---------------------------------------------------------------------------


def test_fk_id_attr_collision_with_m2m_is_fail_loud():
    """A forward FK ``category`` (-> ``category_id``) colliding with a forward M2M literally
    named ``category_id`` raises ``ConfigurationError`` rather than silently dropping one input.

    Both generate the input attr ``category_id`` (the FK remaps to ``<field>_id``; the M2M
    keeps its plain field name), so ``build_strawberry_input_class`` would write the second
    over the first in its annotations dict, dropping a writable column. Crucially this is a
    Django-legal, snake-case pair: an M2M has no local column, so Django's own field-name
    clash check (``models.E006``) does NOT fire against the FK's ``category_id`` attname -
    the framework must catch and name the collision itself, mirroring the form / serializer
    generated-input guards (``iter_input_field_collisions``).
    """
    relay_target, _ = _make_relay_target()

    class Owner(models.Model):
        category = models.ForeignKey(relay_target, on_delete=models.CASCADE, related_name="+")
        category_id = models.ManyToManyField(relay_target, related_name="+")

        class Meta:
            app_label = _unique_app_label()

    class OwnerType(DjangoType, relay.Node):
        class Meta:
            model = Owner
            fields = ("id",)

    with pytest.raises(ConfigurationError) as exc:
        build_mutation_input(Owner, operation_kind=CREATE, primary_type=OwnerType)
    message = str(exc.value)
    assert "category_id" in message
    assert "'category'" in message
    assert "collide" in message

    # One consumer attr cannot disambiguate two model fields. The collision must
    # survive the override skip instead of treating both columns as customized.
    with pytest.raises(ConfigurationError, match="same attribute 'category_id'"):
        build_mutation_input(
            Owner,
            operation_kind=CREATE,
            primary_type=OwnerType,
            overrides=frozenset({"category_id"}),
        )


def test_camel_case_graphql_name_collision_is_fail_loud():
    """Two columns whose names default-camel-case to ONE GraphQL name raise rather than
    silently dropping one input.

    ``foo_bar`` and ``fooBar`` produce DISTINCT input attrs (the input-attr arm passes) but
    the SAME ``graphql_name`` ``fooBar``; Strawberry would collapse the two onto one schema
    field with no error. The graphql-name arm catches and names them, at parity with the
    form / serializer flavors and the read-type guard ``types/finalizer.py::_audit_field_surface``.
    """

    class CamelCollide(models.Model):
        foo_bar = models.IntegerField()
        fooBar = models.IntegerField()  # noqa: N815 - intentional collision fixture

        class Meta:
            app_label = _unique_app_label()

    class CamelCollideType(DjangoType, relay.Node):
        class Meta:
            model = CamelCollide
            fields = ("id",)

    with pytest.raises(ConfigurationError) as exc:
        build_mutation_input(CamelCollide, operation_kind=CREATE, primary_type=CamelCollideType)
    message = str(exc.value)
    assert "fooBar" in message
    assert "collide" in message

    # Unlike an attr collision, distinct Python attrs can be disambiguated by a
    # consumer wire alias. Audit the effective merged surface, not the discarded
    # generated name for the overridden field.
    remainder = build_mutation_input(
        CamelCollide,
        operation_kind=CREATE,
        primary_type=CamelCollideType,
        overrides=frozenset({"foo_bar"}),
    )

    @strawberry.input
    class ConsumerInput:
        foo_bar: int = strawberry.field(name="fooBarAlternate")

    merged = strawberry.input(type("ResolvedCamelInput", (ConsumerInput, remainder), {}))
    materialize_mutation_input_class("ResolvedCamelInput", merged)


def test_no_false_positive_collision_on_ordinary_model():
    """The collision guard does not false-positive on a normal model (products ``Item``).

    ``Item`` (name / description / category FK / attachment / is_private) has no colliding
    generated attrs or GraphQL names, so the full editable create input still builds.
    """
    cls = build_mutation_input(product_models.Item, operation_kind=CREATE, primary_type=ItemType)
    assert set(_field_map(cls)) == {
        "name",
        "description",
        "category_id",
        "attachment",
        "is_private",
    }


def test_digit_boundary_columns_do_not_silently_collide_in_generated_input():
    """Two editable columns differing only by an underscore-adjacent digit survive distinctly.

    ``field_2`` and ``field2`` produce DISTINCT ``graphql_camel_name`` values
    (``field_2`` vs ``field2``), so the generated-input collision guard -- which
    compares ``graphql_camel_name`` -- does NOT reject the pair. But when the
    ``name=`` alias was pinned only on divergence, ``field_2`` (equal to its own
    camel-name) carried no alias, so Strawberry's ``NameConverter`` re-derived it
    to ``field2`` via ``to_camel_case`` and silently overwrote the sibling
    ``field2`` -- dropping one consumer-declared column from the generated
    ``<Model>Input`` SDL with no error. The shared generated-input builder now
    pins every package-derived wire name, so both survive.
    """

    class DigitBoundary(models.Model):
        field_2 = models.IntegerField()
        field2 = models.IntegerField()

        class Meta:
            app_label = _unique_app_label()

    class DigitBoundaryType(DjangoType, relay.Node):
        class Meta:
            model = DigitBoundary
            fields = ("id",)

    input_cls = build_mutation_input(
        DigitBoundary,
        operation_kind=CREATE,
        primary_type=DigitBoundaryType,
    )

    # ``from __future__ import annotations`` stringizes source-level annotations,
    # so set the resolver's ``__annotations__`` to real objects to reference the
    # generated input class as a schema-field argument type.
    def _probe(inp) -> int:
        return 1

    _probe.__annotations__ = {"inp": input_cls, "return": int}

    @strawberry.type
    class Query:
        probe: int = strawberry.field(resolver=_probe)

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    sdl = schema.as_str()
    block = sdl[sdl.index("input DigitBoundaryInput") :]
    block = block[: block.index("}")]
    # Both distinct wire names present -- no silent collapse to a single ``field2``.
    assert "field_2:" in block
    assert "field2:" in block


# ---------------------------------------------------------------------------
# mutation_input_type_name - stable full name + shape-derived narrowed name
# ---------------------------------------------------------------------------


def test_type_name_full_shape_is_canonical():
    """The full editable shape resolves to ``<Model>Input`` / ``<Model>PartialInput``."""
    full = tuple(f.name for f in editable_input_fields(product_models.Item))
    assert (
        mutation_input_type_name(product_models.Item, CREATE, full, full_field_names=full)
        == "ItemInput"
    )
    assert (
        mutation_input_type_name(product_models.Item, PARTIAL, full, full_field_names=full)
        == "ItemPartialInput"
    )


def test_type_name_narrowed_shape_is_deterministic_and_distinct():
    """A narrowed shape gets a deterministic, non-canonical, set-derived name."""
    full = tuple(f.name for f in editable_input_fields(product_models.Item))
    narrowed = ("name", "category")
    name_a = mutation_input_type_name(product_models.Item, CREATE, narrowed, full_field_names=full)
    # Deterministic across calls; order-independent (set identity).
    name_b = mutation_input_type_name(
        product_models.Item,
        CREATE,
        ("category", "name"),
        full_field_names=full,
    )
    assert name_a == name_b
    assert name_a != "ItemInput"
    assert name_a.startswith("Item") and name_a.endswith("Input")


def test_type_name_token_boundaries_do_not_collide():
    """Different field sets that share a pascalized token stream get distinct names.

    A per-segment-capitalize token (``IsPrivate``) keeps interior capitals, so a bare
    concatenation re-decomposes ambiguously: ``("a_b", "c")`` and ``("a", "b_c")``
    both collapse onto ``ABC`` - a generated GraphQL type-name collision that trips
    the distinct-shape collision raise at materialize. A single-leading-capital token
    (letter underscores collapsed, no interior capital) makes the concatenation
    uniquely decomposable at uppercase boundaries, so the suffix is injective over
    field-name sets (``AbC`` vs ``ABc``). Underscore-before-digit is retained so the
    type stem stays distinct on the wire under the pinned ``strawberry.input(name=)``.
    """
    full = ("not_the_narrowed_set",)  # any set != either narrowing, so both are "narrowed"
    left = mutation_input_type_name(
        product_models.Item,
        CREATE,
        ("a_b", "c"),
        full_field_names=full,
    )
    right = mutation_input_type_name(
        product_models.Item,
        CREATE,
        ("a", "b_c"),
        full_field_names=full,
    )
    assert left != right
    assert left == "ItemA_ubCInput" and right == "ItemAB_ucInput"


def test_type_name_digit_boundary_narrowings_stay_distinct():
    """``field_2`` / ``field2`` Meta.fields narrowings mint distinct input type names.

    ``pascalize_token`` used to strip every underscore (``field_2`` / ``field2`` both
    -> ``Field2``), so two legitimate narrowed shapes claimed one GraphQL input type
    name and the second materialize raised a distinct-shape collision. Retaining
    underscore-before-digit keeps the tokens injective; the shared builder pins
    ``strawberry.input(name=)`` so the underscore survives on the wire.
    """
    full = ("not_the_narrowed_set",)

    class DigitBoundary(models.Model):
        field_2 = models.IntegerField()
        field2 = models.IntegerField()

        class Meta:
            app_label = _unique_app_label()

    class DigitBoundaryType(DjangoType, relay.Node):
        class Meta:
            model = DigitBoundary
            fields = ("id",)

    left_name = mutation_input_type_name(
        DigitBoundary,
        CREATE,
        ("field_2",),
        full_field_names=full,
    )
    right_name = mutation_input_type_name(
        DigitBoundary,
        CREATE,
        ("field2",),
        full_field_names=full,
    )
    assert left_name == "DigitBoundaryField_u2Input"
    assert right_name == "DigitBoundaryField2Input"
    assert left_name != right_name

    left = build_mutation_input(
        DigitBoundary,
        operation_kind=CREATE,
        primary_type=DigitBoundaryType,
        fields=("field_2",),
    )
    right = build_mutation_input(
        DigitBoundary,
        operation_kind=CREATE,
        primary_type=DigitBoundaryType,
        fields=("field2",),
    )
    materialize_mutation_input_class(left.__name__, left)
    materialize_mutation_input_class(right.__name__, right)  # must not collide

    def _probe(left_inp, right_inp) -> int:
        return 1

    _probe.__annotations__ = {"left_inp": left, "right_inp": right, "return": int}

    @strawberry.type
    class Query:
        probe: int = strawberry.field(resolver=_probe)

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    sdl = schema.as_str()
    assert "input DigitBoundaryField_u2Input" in sdl
    assert "input DigitBoundaryField2Input" in sdl


def test_type_name_other_legal_boundaries_do_not_collide():
    """Underscores after digits, collapsed letters, and capitals remain injective."""
    full = ("not_the_narrowed_set",)

    for left_field, right_field in (("a_b", "ab"), ("field2_x", "field2x"), ("fooBar", "foobar")):
        left = mutation_input_type_name(
            product_models.Item,
            CREATE,
            (left_field,),
            full_field_names=full,
        )
        right = mutation_input_type_name(
            product_models.Item,
            CREATE,
            (right_field,),
            full_field_names=full,
        )
        assert left != right


def test_build_empty_field_set_raises_configuration_error():
    """An empty effective field set fails loud as ``ConfigurationError`` (bug 6).

    ``Meta.fields = ()`` (or an ``exclude`` covering every editable column) would
    build an empty ``@strawberry.input``, which Strawberry rejects only at
    ``Schema(...)`` build with a raw ``ValueError: Input Object type ... must define
    one or more fields.`` The generator rejects it at the framework boundary first,
    naming the model.
    """
    with pytest.raises(ConfigurationError, match="has no fields"):
        build_mutation_input(
            product_models.Category,
            operation_kind=CREATE,
            primary_type=CategoryType,
            fields=(),
        )


# ---------------------------------------------------------------------------
# materialize_mutation_input_class - dedupe + collision raise
# ---------------------------------------------------------------------------


def test_identical_shape_dedupes_via_ledger():
    """Materializing the same class twice under one name is a no-op (identical shapes dedupe)."""
    cls = build_mutation_input(product_models.Item, operation_kind=CREATE, primary_type=ItemType)
    materialize_mutation_input_class("ItemInput", cls)
    # Idempotent re-materialize of the SAME (name, cls) pair: no raise.
    materialize_mutation_input_class("ItemInput", cls)
    import sys

    assert sys.modules[INPUTS_MODULE_PATH].ItemInput is cls


def test_distinct_shapes_colliding_on_one_name_raise_configuration_error():
    """Two DISTINCT classes under one name raise ``ConfigurationError``."""
    cls_a = build_mutation_input(product_models.Item, operation_kind=CREATE, primary_type=ItemType)
    cls_b = build_mutation_input(
        product_models.Category,
        operation_kind=CREATE,
        primary_type=CategoryType,
    )
    materialize_mutation_input_class("CollidingInput", cls_a)
    with pytest.raises(ConfigurationError, match="DjangoMutation"):
        materialize_mutation_input_class("CollidingInput", cls_b)


def test_materializer_rejects_consumer_alias_colliding_with_generated_remainder():
    """A merged input is audited after inheritance combines both field surfaces."""

    @strawberry.input
    class ConsumerInput:
        custom: str = strawberry.field(name="name")

    remainder = build_mutation_input(
        product_models.Item,
        operation_kind=CREATE,
        primary_type=ItemType,
    )
    merged = strawberry.input(type("MergedItemInput", (ConsumerInput, remainder), {}))

    with pytest.raises(ConfigurationError, match="same GraphQL field name 'name'"):
        materialize_mutation_input_class("MergedItemInput", merged)


# ---------------------------------------------------------------------------
# Upload mapping (spec-037) - FileField/ImageField become Upload
# ---------------------------------------------------------------------------


def test_required_file_field_maps_to_upload():
    """A plain required ``FileField`` create input maps to ``Upload`` and is NOT optional.

    The python attr is the model field name (``attachment``), never
    ``attachment_id`` (that is the FK relation scheme); a file/image column is a
    SCALAR input.
    """

    class HasFile(models.Model):
        attachment = models.FileField()

        class Meta:
            app_label = _unique_app_label()

    class HasFileType(DjangoType, relay.Node):
        class Meta:
            model = HasFile
            fields = ("id",)

    cls = build_mutation_input(HasFile, operation_kind=CREATE, primary_type=HasFileType)
    fields = _field_map(cls)
    assert "attachment" in fields
    assert "attachment_id" not in fields
    assert not _is_optional(fields["attachment"])
    assert _inner_type(fields["attachment"]) is Upload


def test_required_image_field_maps_to_upload():
    """A plain required ``ImageField`` create input maps to ``Upload`` and is required."""

    class HasImage(models.Model):
        avatar = models.ImageField()

        class Meta:
            app_label = _unique_app_label()

    class HasImageType(DjangoType, relay.Node):
        class Meta:
            model = HasImage
            fields = ("id",)

    cls = build_mutation_input(HasImage, operation_kind=CREATE, primary_type=HasImageType)
    fields = _field_map(cls)
    assert not _is_optional(fields["avatar"])
    assert _inner_type(fields["avatar"]) is Upload


def test_file_field_camel_cases_graphql_name():
    """A multi-word file column camel-cases its GraphQL alias like any scalar input."""

    class HasArt(models.Model):
        cover_art = models.FileField()

        class Meta:
            app_label = _unique_app_label()

    class HasArtType(DjangoType, relay.Node):
        class Meta:
            model = HasArt
            fields = ("id",)

    cls = build_mutation_input(HasArt, operation_kind=CREATE, primary_type=HasArtType)
    fields = _field_map(cls)
    assert _inner_type(fields["cover_art"]) is Upload
    assert fields["cover_art"].graphql_name == "coverArt"


def test_blank_file_field_widens_to_upload_optional():
    """A ``blank=True`` file column is optional + ``UNSET``-defaulted with inner ``Upload``.

    ``blank`` is the ``input_field_required`` ``not field.blank`` branch.
    """

    class HasBlankFile(models.Model):
        attachment = models.FileField(blank=True)

        class Meta:
            app_label = _unique_app_label()

    class HasBlankFileType(DjangoType, relay.Node):
        class Meta:
            model = HasBlankFile
            fields = ("id",)

    cls = build_mutation_input(HasBlankFile, operation_kind=CREATE, primary_type=HasBlankFileType)
    fields = _field_map(cls)
    assert _is_optional(fields["attachment"])
    assert fields["attachment"].default is UNSET
    assert _inner_type(fields["attachment"]) is Upload


def test_null_file_field_widens_to_upload_optional():
    """A ``null=True`` file column is optional + ``UNSET``-defaulted with inner ``Upload``.

    ``null`` is the ``input_field_required`` ``field.null`` branch (distinct from
    the ``blank`` branch above), so both requiredness paths are pinned.
    """

    class HasNullFile(models.Model):
        attachment = models.FileField(null=True)

        class Meta:
            app_label = _unique_app_label()

    class HasNullFileType(DjangoType, relay.Node):
        class Meta:
            model = HasNullFile
            fields = ("id",)

    cls = build_mutation_input(HasNullFile, operation_kind=CREATE, primary_type=HasNullFileType)
    fields = _field_map(cls)
    assert _is_optional(fields["attachment"])
    assert fields["attachment"].default is UNSET
    assert _inner_type(fields["attachment"]) is Upload


def test_partial_input_file_field_always_optional_upload():
    """Every partial input file column is optional + ``UNSET``-defaulted, even when required-on-create."""

    class HasFile(models.Model):
        attachment = models.FileField()  # required on create

        class Meta:
            app_label = _unique_app_label()

    class HasFileType(DjangoType, relay.Node):
        class Meta:
            model = HasFile
            fields = ("id",)

    cls = build_mutation_input(HasFile, operation_kind=PARTIAL, primary_type=HasFileType)
    fields = _field_map(cls)
    assert _is_optional(fields["attachment"])
    assert fields["attachment"].default is UNSET
    assert _inner_type(fields["attachment"]) is Upload


def test_file_field_narrowed_by_meta_fields_and_exclude():
    """A file column is included / excluded by model field name via ``fields`` / ``exclude``."""

    class HasFileAndName(models.Model):
        name = models.TextField()
        attachment = models.FileField()

        class Meta:
            app_label = _unique_app_label()

    class HasFileAndNameType(DjangoType, relay.Node):
        class Meta:
            model = HasFileAndName
            fields = ("id",)

    # ``fields`` dropping the file column drops it from the input.
    only_name = build_mutation_input(
        HasFileAndName,
        operation_kind=CREATE,
        primary_type=HasFileAndNameType,
        fields=("name",),
    )
    assert "attachment" not in _field_map(only_name)

    # ``fields`` naming the file column keeps it as ``Upload``.
    with_file = build_mutation_input(
        HasFileAndName,
        operation_kind=CREATE,
        primary_type=HasFileAndNameType,
        fields=("name", "attachment"),
    )
    assert _inner_type(_field_map(with_file)["attachment"]) is Upload

    # ``exclude`` of the file column drops it too.
    excluded = build_mutation_input(
        HasFileAndName,
        operation_kind=CREATE,
        primary_type=HasFileAndNameType,
        exclude=("attachment",),
    )
    assert "attachment" not in _field_map(excluded)


def test_file_field_consumer_override_skips_generated_upload_field():
    """A file column in ``overrides`` is SKIPPED, lifting the spec-036 carve-out.

    The old staged ``NotImplementedError`` ran BEFORE the override skip, so a file
    column could not participate in the ``Meta.input_class`` merge override. Now it
    does, exactly like a scalar - this is the load-bearing carve-out-lift assertion.
    """

    class HasFileAndName(models.Model):
        name = models.TextField()
        attachment = models.FileField()

        class Meta:
            app_label = _unique_app_label()

    class HasFileAndNameType(DjangoType, relay.Node):
        class Meta:
            model = HasFileAndName
            fields = ("id",)

    cls = build_mutation_input(
        HasFileAndName,
        operation_kind=CREATE,
        primary_type=HasFileAndNameType,
        overrides=frozenset({"attachment"}),
    )
    fields = _field_map(cls)
    assert "attachment" not in fields  # overridden -> skipped, not clobbered
    assert "name" in fields  # the non-overridden column still generates


# ---------------------------------------------------------------------------
# FieldError + payload wrapper (Decision 7)
# ---------------------------------------------------------------------------


def test_field_error_envelope_shape():
    """``FieldError`` has ``field: str`` (non-null) + ``messages: list[str]`` (non-null list)."""
    definition = FieldError.__strawberry_definition__
    fields = {f.python_name: f for f in definition.fields}
    assert fields["field"].type is str
    assert isinstance(fields["messages"].type, StrawberryList)
    assert fields["messages"].type.of_type is str


def test_field_error_field_set_is_frozen():
    """``FieldError``'s field SET is pinned, so widening the shared envelope is deliberate.

    Every write flavor returns ``errors: list[FieldError]`` off the SAME class
    (spec-036 Decision 7; the form and serializer/auth flavor cards reuse it rather
    than declaring their own), so a field added or removed here changes the wire
    contract for all of them and for every consumer client at once. The shape-by-
    shape row above asserts the two legacy members individually and therefore
    cannot see a third or fourth member arriving - which is how ``codes`` and
    ``path`` landed with nothing failing. Set equality is the gate: a flavor that
    wants a fifth field has to change this row on purpose.
    """
    definition = FieldError.__strawberry_definition__
    assert {f.python_name for f in definition.fields} == {
        "field",
        "messages",
        "codes",
        "path",
    }


def test_field_error_wire_name_set_on_a_generated_payload_is_frozen():
    """The WIRE name set a payload's ``errors`` exposes is pinned, not only the Python set.

    The row above pins the Python attribute set; a consumer selects wire names, so
    a ``strawberry.field(name=...)`` rename or a dropped member is a breaking
    envelope change even when the Python set is untouched. Reached through
    ``build_payload_type`` (the generator every flavor's payload comes from) so the
    assertion covers the type as it actually reaches a client, and the two rows
    fail independently.
    """
    _, relay_type = _make_relay_target()
    payload = build_payload_type("CreateThing", object_type=relay_type, object_slot="node")
    errors_field = {f.python_name: f for f in payload.__strawberry_definition__.fields}["errors"]
    error_type = errors_field.type.of_type
    assert error_type is FieldError
    # No member name carries an underscore, so the auto-camel-case of an
    # un-overridden ``python_name`` is the name itself; an explicit
    # ``strawberry.field(name=...)`` rename surfaces as ``graphql_name`` and fails.
    graphql_names = {
        field.graphql_name or field.python_name
        for field in error_type.__strawberry_definition__.fields
    }
    assert graphql_names == {
        "field",
        "messages",
        "codes",
        "path",
    }


def test_payload_node_slot_for_relay_target():
    """A Relay-Node primary yields a ``node`` slot + a nullable object + ``errors``.

    Uses a local Relay-shaped type (inherits ``relay.Node`` directly) so
    ``implements_relay_node`` is True without depending on ``finalize_django_types``
    injecting ``relay.Node`` into the products types' ``__bases__``.
    """
    _, relay_type = _make_relay_target()
    assert payload_object_slot(relay_type) == "node"
    payload = build_payload_type("CreateThing", object_type=relay_type, object_slot="node")
    assert payload.__name__ == "CreateThingPayload"
    fields = {f.python_name: f for f in payload.__strawberry_definition__.fields}
    assert "node" in fields
    assert isinstance(fields["node"].type, StrawberryOptional)
    assert fields["node"].type.of_type is relay_type
    assert isinstance(fields["errors"].type, StrawberryList)
    assert fields["errors"].type.of_type is FieldError


def test_payload_result_slot_for_non_relay_target():
    """A non-Relay primary yields a ``result`` slot, never a model-derived name."""
    _, plain_type = _make_non_relay_target()
    assert payload_object_slot(plain_type) == "result"
    payload = build_payload_type("CreatePlain", object_type=plain_type, object_slot="result")
    fields = {f.python_name: f for f in payload.__strawberry_definition__.fields}
    assert "result" in fields
    assert isinstance(fields["result"].type, StrawberryOptional)


def test_payload_slot_never_model_derived_for_property_like_model():
    """A model whose name would collide with a builtin uses the uniform slot, not its name.

    The payload slot is uniform: a ``Property``-shaped payload exposes ``node``
    (Relay) / ``result`` (non-Relay), NEVER a ``property``-named field.
    """
    payload = build_payload_type("CreateProperty", object_type=ItemType, object_slot="node")
    fields = {f.python_name for f in payload.__strawberry_definition__.fields}
    assert "property" not in fields
    assert "node" in fields


def test_payload_model_less_shape():
    """A model-less payload (object_type=None) yields ``ok: bool`` + ``errors`` with no object slot."""
    payload = build_payload_type("DoAction", object_type=None)
    assert payload.__name__ == "DoActionPayload"
    fields = {f.python_name: f for f in payload.__strawberry_definition__.fields}
    assert "ok" in fields
    assert fields["ok"].type is bool
    assert "errors" in fields
    assert isinstance(fields["errors"].type, StrawberryList)
    assert fields["errors"].type.of_type is FieldError
    assert "node" not in fields
    assert "result" not in fields


def test_payload_slot_defaults_from_object_type():
    """When object_slot is omitted, it defaults to the uniform slot via payload_object_slot."""
    _, relay_type = _make_relay_target()
    payload_relay = build_payload_type("CreateRelayAuto", object_type=relay_type)
    fields_relay = {f.python_name for f in payload_relay.__strawberry_definition__.fields}
    assert "node" in fields_relay
    assert "errors" in fields_relay

    _, plain_type = _make_non_relay_target()
    payload_plain = build_payload_type("CreatePlainAuto", object_type=plain_type)
    fields_plain = {f.python_name for f in payload_plain.__strawberry_definition__.fields}
    assert "result" in fields_plain
    assert "errors" in fields_plain


# ---------------------------------------------------------------------------
# mutation_input_field_specs - bind-time reverse map (spec-053 D3)
# ---------------------------------------------------------------------------


def test_mutation_input_field_specs_covers_generated_input():
    """Specs cover every generated input attr; FK target_name is ``<field>_id``."""
    from django_strawberry_framework.utils.inputs import RELATION_SINGLE, SCALAR

    input_cls = build_mutation_input(
        product_models.Item,
        operation_kind=CREATE,
        primary_type=ItemType,
    )
    specs, model_fields = mutation_input_field_specs(product_models.Item, input_cls)
    by_attr = {spec.input_attr: spec for spec in specs}
    assert set(by_attr) == set(_field_map(input_cls))
    assert by_attr["name"].kind == SCALAR
    assert by_attr["name"].target_name == "name"
    assert by_attr["category_id"].kind == RELATION_SINGLE
    assert by_attr["category_id"].target_name == "category_id"
    assert by_attr["category_id"].related_model is product_models.Category
    assert model_fields["category_id"] is product_models.Item._meta.get_field("category")
    assert model_fields["name"] is product_models.Item._meta.get_field("name")


def test_mutation_input_field_specs_rejects_non_column_attr():
    """A merged-input attr that is not a concrete column fails at spec synthesis."""

    @strawberry.input
    class Rogue:
        not_a_column: str

    with pytest.raises(ConfigurationError, match="not_a_column"):
        mutation_input_field_specs(product_models.Item, Rogue)


def test_mutation_input_field_specs_rejects_generic_foreign_key_attr():
    """A virtual relation (GFK) is not a concrete column, even if ``get_field`` finds it."""
    from apps.library import models as library_models

    @strawberry.input
    class Rogue:
        content_object: str

    with pytest.raises(ConfigurationError, match="content_object"):
        mutation_input_field_specs(library_models.TaggedItem, Rogue)


def test_mutation_input_field_specs_classifies_m2m():
    """Forward M2M is ``RELATION_MULTI`` keyed by the field name, not ``<name>_id``."""
    from apps.library import models as library_models

    from django_strawberry_framework.utils.inputs import RELATION_MULTI

    @strawberry.input
    class Probe:
        genres: list[int]

    specs, model_fields = mutation_input_field_specs(library_models.Book, Probe)
    assert specs[0].kind == RELATION_MULTI
    assert specs[0].target_name == "genres"
    assert model_fields["genres"] is library_models.Book._meta.get_field("genres")


def test_mutation_input_field_specs_marks_excluded_kind():
    """``excluded_attrs`` records kind ``EXCLUDED`` without changing target_name."""

    @strawberry.input
    class Probe:
        name: str

    specs, _model_fields = mutation_input_field_specs(
        product_models.Item,
        Probe,
        excluded_attrs={"name"},
    )
    assert specs[0].kind == EXCLUDED
    assert specs[0].target_name == "name"


# ---------------------------------------------------------------------------
# Public export
# ---------------------------------------------------------------------------


def test_field_error_is_public_export():
    """``FieldError`` is exported from the package root and listed in ``__all__``."""
    assert django_strawberry_framework.FieldError is FieldError
    assert FieldErrorFromPackage is FieldError
    assert "FieldError" in django_strawberry_framework.__all__


def test_field_error_payload_uses_a_strawberry_type():
    """Sanity: the payload + FieldError are real ``@strawberry.type`` classes."""
    assert hasattr(FieldError, "__strawberry_definition__")
    payload = build_payload_type("X", object_type=ItemType, object_slot="node")
    # ``strawberry.type`` decoration is detectable via the definition marker.
    assert hasattr(payload, "__strawberry_definition__")
    # Guard against accidental input-vs-type confusion: payloads are output types.
    assert not strawberry.type(payload).__strawberry_definition__.is_input


def test_editable_input_fields_normalizes_its_declared_sequences():
    """A bare string or a duplicate name is rejected here too, not only at the metaclass.

    ``editable_input_fields`` is a PUBLIC generator the auth and form adapters
    call directly, bypassing ``DjangoMutation._validate_meta``. It used to freeze
    its sequences with a bare ``tuple(...)``, so a bare string reaching it
    iterated as characters and a duplicate name collapsed silently - both
    malformed declarations that the same narrowing spine already rejected for
    the form and serializer flavors.
    """
    with pytest.raises(ConfigurationError, match="not a bare string"):
        editable_input_fields(product_models.Item, fields="name")
    with pytest.raises(ConfigurationError, match="duplicate field name"):
        editable_input_fields(product_models.Item, fields=("name", "name"))


# ---------------------------------------------------------------------------
# Attr-name-set parameters reject bare strings (overrides / excluded_attrs)
# ---------------------------------------------------------------------------


def test_build_mutation_input_rejects_bare_string_overrides():
    """A bare ``str`` / ``bytes`` ``overrides`` fails loud instead of char-splitting.

    ``overrides`` freezes through ``frozenset``, so a bare string used to iterate
    as CHARACTERS (bytes as byte INTEGERS) - silently matching no input attr, so
    the caller's override never applied and, while non-empty, the garbage set
    satisfied the ``not overrides`` half of the empty-input guard. The same
    iterate-as-characters defect class ``normalize_field_name_sequence`` rejects
    loudly for ``fields`` / ``exclude`` (the row above), so the set-shaped
    siblings reject it too.
    """
    with pytest.raises(ConfigurationError, match="overrides"):
        build_mutation_input(
            product_models.Item,
            operation_kind=CREATE,
            primary_type=ItemType,
            overrides="category_id",
        )
    with pytest.raises(ConfigurationError, match="overrides"):
        build_mutation_input(
            product_models.Item,
            operation_kind=CREATE,
            primary_type=ItemType,
            overrides=b"name",
        )


def test_bare_string_overrides_cannot_bypass_the_empty_input_guard():
    """No zero-field input class escapes via a garbage ``overrides`` string.

    A model with no editable columns + ``overrides="x"`` used to return an empty
    input class (the char-split set satisfied the guard's ``not overrides``);
    Strawberry only rejected it later at ``Schema(...)`` build with a raw
    ``ValueError``. The generator's fail-loud boundary now holds either way: the
    bare string is rejected before the guard can be satisfied by it.
    """

    class NoEditable(models.Model):
        created_date = models.DateTimeField(auto_now_add=True)
        updated_date = models.DateTimeField(auto_now=True)

        class Meta:
            app_label = _unique_app_label()

    class NoEditableType(DjangoType, relay.Node):
        class Meta:
            model = NoEditable
            fields = ("id",)

    with pytest.raises(ConfigurationError, match="(overrides|has no fields)"):
        build_mutation_input(
            NoEditable,
            operation_kind=CREATE,
            primary_type=NoEditableType,
            overrides="x",
        )


def test_mutation_input_field_specs_rejects_bare_string_excluded_attrs():
    """A bare ``str`` / ``bytes`` ``excluded_attrs`` fails loud, keeping the D6 seam honest.

    ``excluded_attrs`` records the spec-040 D6 capture attrs; frozen through
    ``frozenset``, a bare string used to split into characters that matched no
    attr, silently leaving every spec kind as its column/relation kind (the
    ``password`` capture seam would simply not fire). Sets of names reject the
    bare-string shape like every other names-parameter surface.
    """

    @strawberry.input
    class NameProbe:
        name: str

    with pytest.raises(ConfigurationError, match="excluded_attrs"):
        mutation_input_field_specs(
            product_models.Item,
            NameProbe,
            excluded_attrs="name",
        )
    with pytest.raises(ConfigurationError, match="excluded_attrs"):
        mutation_input_field_specs(
            product_models.Item,
            NameProbe,
            excluded_attrs=b"name",
        )


def test_build_payload_type_rejects_reserved_or_invalid_object_slot():
    """A payload ``object_slot`` colliding with ``ok`` / ``errors`` (or not an identifier)
    fails loud.

    The payload namespace dict keys the object slot beside ``errors`` (and the
    model-less ``ok``), so a slot named ``errors`` used to collapse onto the
    duplicate dict key and silently build a payload with NO object field, and a
    non-identifier slot exploded later inside dataclass codegen with a cryptic
    ``SyntaxError`` (``__dataclass_dflt_node-x__``). The builder rejects both at
    the framework boundary; the uniform slots (``node`` / ``result``) and the
    auto-derivation keep building (pinned by the payload rows above).
    """
    _, relay_type = _make_relay_target()
    for bad_slot in (
        "errors",
        "ok",
        "node-x",
        5,
    ):
        with pytest.raises(ConfigurationError, match="object_slot"):
            build_payload_type(
                "CreateThing",
                object_type=relay_type,
                object_slot=bad_slot,  # type: ignore[arg-type]
            )
