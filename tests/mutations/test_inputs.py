"""Mutation input tests for generated Input/PartialInput, FieldError, and the payload wrapper.

Covers the spec-036 Slice 1 generation substrate
(``django_strawberry_framework/mutations/inputs.py``):

- ``editable_input_fields`` selection (pk / auto-timestamp / reverse exclusion,
  M2M inclusion, ``fields`` / ``exclude`` narrowing + unknown-name rejection);
- ``input_field_required`` (the Major-1 create-required rule);
- ``build_mutation_input`` create vs partial shapes, FK/O2O ``<field>_id`` mapping,
  M2M ``list[<id>]``, Relay-vs-non-Relay id type, and the consumer-override seam;
- ``mutation_input_type_name`` stable full-shape names + shape-derived narrowed
  names, with dedupe + the distinct-shape collision ``ConfigurationError`` via
  ``materialize_mutation_input_class``;
- the ``Upload`` staged-seam ``NotImplementedError`` for file/image columns;
- ``FieldError`` / ``build_payload_type`` envelope shape + the ``node`` / ``result``
  slot;
- the ``FieldError`` public export.

System-under-test is the generator itself, run against the realistic products
``Item`` / ``Category`` FK fixtures plus minimal package-local fixture models for
the M2M, non-Relay-target, and ``FileField`` shapes products does not carry
(spec-036 Slice 1 test plan; products is every-Relay and has no M2M / file field).
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
from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations import FieldError as FieldErrorFromPackage
from django_strawberry_framework.mutations.inputs import (
    CREATE,
    INPUTS_MODULE_PATH,
    NON_FIELD_ERROR_KEY,
    PARTIAL,
    FieldError,
    build_mutation_input,
    build_payload_type,
    clear_mutation_input_namespace,
    editable_input_fields,
    input_field_required,
    materialize_mutation_input_class,
    mutation_input_type_name,
    payload_object_slot,
)
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry_and_ledger():
    """Reset registry + the mutation-input ledger so each test starts clean.

    Slice 1 does not wire ``clear_mutation_input_namespace`` into
    ``registry.clear()`` (that is Slice 2), so the ledger is cleared explicitly
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
    """The non-field error key is pinned to Django's ``"__all__"`` sentinel (AR-M3)."""
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


def test_editable_fields_narrow_by_exclude():
    """``exclude`` drops the named columns, preserving declaration order."""
    names = [
        f.name
        for f in editable_input_fields(product_models.Item, exclude=("description", "is_private"))
    ]
    assert names == ["name", "category"]


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


# ---------------------------------------------------------------------------
# input_field_required - the Major-1 create-required rule
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
    # M2M is always optional (resolver replace/clear/omit contract, AR-M1).
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
# Consumer-override seam (spec-010 relation-override / AR-M2)
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
    """Different field sets that share a pascalized token stream get distinct names (bug 8).

    A per-segment-capitalize token (``IsPrivate``) keeps interior capitals, so a bare
    concatenation re-decomposes ambiguously: ``("a_b", "c")`` and ``("a", "b_c")``
    both collapse onto ``ABC`` - a generated GraphQL type-name collision that trips
    the AR-M6 distinct-shape raise at materialize. A single-leading-capital token
    (``[A-Z][a-z0-9]*``, underscores removed) makes the concatenation uniquely
    decomposable at uppercase boundaries, so the suffix is injective over field-name
    sets (``AbC`` vs ``ABc``) while staying underscore-free (Strawberry's GraphQL
    name converter leaves the PascalCase name unchanged).
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
    assert left == "ItemAbCInput" and right == "ItemABcInput"


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
# materialize_mutation_input_class - dedupe + collision raise (AR-H1 / AR-M6)
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
    """Two DISTINCT classes under one name raise ``ConfigurationError`` (AR-H1 / AR-M6)."""
    cls_a = build_mutation_input(product_models.Item, operation_kind=CREATE, primary_type=ItemType)
    cls_b = build_mutation_input(
        product_models.Category,
        operation_kind=CREATE,
        primary_type=CategoryType,
    )
    materialize_mutation_input_class("CollidingInput", cls_a)
    with pytest.raises(ConfigurationError, match="DjangoMutation"):
        materialize_mutation_input_class("CollidingInput", cls_b)


# ---------------------------------------------------------------------------
# Upload staged seam (TODO-ALPHA-037-0.0.11) - fail loud, never silent str
# ---------------------------------------------------------------------------


def test_file_field_raises_not_implemented_error():
    """A ``FileField`` reaching the generator fails loud (the 037 staged seam)."""

    class HasFile(models.Model):
        attachment = models.FileField()

        class Meta:
            app_label = _unique_app_label()

    class HasFileType(DjangoType, relay.Node):
        class Meta:
            model = HasFile
            fields = ("id",)

    with pytest.raises(NotImplementedError, match="TODO-ALPHA-037-0.0.11"):
        build_mutation_input(HasFile, operation_kind=CREATE, primary_type=HasFileType)


def test_image_field_raises_not_implemented_error():
    """An ``ImageField`` reaching the generator fails loud (the 037 staged seam)."""

    class HasImage(models.Model):
        avatar = models.ImageField()

        class Meta:
            app_label = _unique_app_label()

    class HasImageType(DjangoType, relay.Node):
        class Meta:
            model = HasImage
            fields = ("id",)

    with pytest.raises(NotImplementedError, match="Upload"):
        build_mutation_input(HasImage, operation_kind=CREATE, primary_type=HasImageType)


# ---------------------------------------------------------------------------
# FieldError + payload wrapper (Decision 7 / AR-H5)
# ---------------------------------------------------------------------------


def test_field_error_envelope_shape():
    """``FieldError`` has ``field: str`` (non-null) + ``messages: list[str]`` (non-null list)."""
    definition = FieldError.__strawberry_definition__
    fields = {f.python_name: f for f in definition.fields}
    assert fields["field"].type is str
    assert isinstance(fields["messages"].type, StrawberryList)
    assert fields["messages"].type.of_type is str


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

    Pins AR-H5: a ``Property``-shaped payload exposes ``node`` (Relay) / ``result``
    (non-Relay), NEVER a ``property``-named field.
    """
    payload = build_payload_type("CreateProperty", object_type=ItemType, object_slot="node")
    fields = {f.python_name for f in payload.__strawberry_definition__.fields}
    assert "property" not in fields
    assert "node" in fields


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
