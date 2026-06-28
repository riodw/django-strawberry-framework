"""Serializer-derived input tests for the generated ``<Serializer>Input`` / ``PartialInput`` (spec-039).

Covers ``django_strawberry_framework/rest_framework/inputs.py`` (Slice 1 generation
substrate):

- ``get_serializer_for_schema`` discovery from a no-arg ``serializer_class()`` +
  ``.fields`` (the loud-rejection guard wraps the LAZY ``.fields`` read, proven by a
  kwarg-requiring serializer AND a ``self.context``-reading ``get_fields()``);
- the two generated inputs: ``<Serializer>Input`` (create; requiredness from
  ``field.required`` minus ``optional_fields``) and ``<Serializer>PartialInput``
  (every field optional);
- ``read_only`` / ``HiddenField`` dropped, ``Meta.fields`` / ``Meta.exclude``
  narrowing + fail-loud, ``Meta.optional_fields`` force-optional, the
  ``optional_fields = "__all__"`` bare-string rejection, the empty-effective-set
  raise, the serializer-only (non-model) field included;
- the ``SerializerInputShape`` descriptor identity (distinct names for differing
  ``optional_fields`` / annotations, identical descriptors dedupe, two distinct
  descriptors on one name raise);
- the create-required-narrowing guard + its waiver + the per-declaration discipline;
- nullability / defaults (M2);
- the input-attr / GraphQL-name / writable-source collisions;
- module-global materialization.

System-under-test runs against the products ``Item`` / ``Category`` fixtures per
``AGENTS.md`` plus package-local Relay / non-Relay target ``DjangoType``s.
"""

from __future__ import annotations

import itertools
import sys

import pytest
from apps.products import models as product_models
from django.db import models
from rest_framework import serializers
from strawberry import UNSET, relay
from strawberry.types.base import StrawberryOptional

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework.inputs import (
    SERIALIZER_INPUTS_MODULE_PATH,
    SerializerInputShape,
    build_serializer_input_class,
    build_serializer_inputs,
    clear_serializer_input_namespace,
    get_serializer_for_schema,
    guard_create_required_serializer_fields,
    materialize_serializer_input_class,
    resolve_effective_serializer_fields,
)
from django_strawberry_framework.rest_framework.serializer_converter import (
    RELATION_SINGLE,
    SCALAR,
)
from django_strawberry_framework.scalars import Upload


@pytest.fixture(autouse=True)
def _isolate_registry_and_ledger():
    """Reset registry + the serializer-input ledger so each test starts clean.

    Slice 1 does not wire ``clear_serializer_input_namespace`` into
    ``registry.clear()`` (that is Slice 2), so the ledger is cleared explicitly.
    """
    registry.clear()
    clear_serializer_input_namespace()
    yield
    registry.clear()
    clear_serializer_input_namespace()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_serializer_inputs__{next(_app_label_counter)}"


def _field_map(input_cls: type) -> dict[str, object]:
    """Return ``python_name -> StrawberryField`` for a built input class."""
    return {f.python_name: f for f in input_cls.__strawberry_definition__.fields}


def _is_optional(field) -> bool:
    """Return whether a Strawberry field's annotation is ``T | None``."""
    return isinstance(field.type, StrawberryOptional)


def _inner_type(field):
    """Return the inner type of a ``StrawberryOptional`` field, else the type itself."""
    return field.type.of_type if isinstance(field.type, StrawberryOptional) else field.type


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


def _item_serializer():
    """A ``ModelSerializer`` over products ``Item`` (name + FK category + is_private)."""

    class ItemSer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

    return ItemSer


# ---------------------------------------------------------------------------
# Module-path constant
# ---------------------------------------------------------------------------


def test_inputs_module_path_constant():
    """The hoisted constant matches the actual dotted path of ``rest_framework/inputs.py``."""
    assert SERIALIZER_INPUTS_MODULE_PATH == "django_strawberry_framework.rest_framework.inputs"


# ---------------------------------------------------------------------------
# get_serializer_for_schema - discovery + the LAZY .fields guard
# ---------------------------------------------------------------------------


def test_get_serializer_for_schema_reads_fields():
    """Discovery returns the serializer's bound field dict in declaration order."""

    class S(serializers.Serializer):
        name = serializers.CharField()
        age = serializers.IntegerField()

    discovered = get_serializer_for_schema(S)
    assert list(discovered) == ["name", "age"]
    assert isinstance(discovered["name"], serializers.CharField)


def test_kwarg_requiring_serializer_rejected_loudly():
    """A serializer whose ``__init__`` requires a kwarg is rejected under default discovery."""

    class KwargSer(serializers.Serializer):
        email = serializers.EmailField()

        def __init__(self, *args, user, **kwargs):
            super().__init__(*args, **kwargs)
            self.user = user

    with pytest.raises(ConfigurationError, match="schema-time field set"):
        get_serializer_for_schema(KwargSer)


def test_context_reading_get_fields_rejected_at_fields_access():
    """A serializer whose ``get_fields()`` reads ``self.context`` raises at ``.fields`` access.

    Proves the guard wraps ``.fields`` materialization, not ``serializer_class()``:
    construction succeeds (no kwargs), but ``.fields`` -> ``get_fields()`` reads
    ``self.context`` which is unset under no-arg discovery, raising there.
    """

    class CtxSer(serializers.Serializer):
        def get_fields(self):
            _ = self.context["tenant"]  # raises at .fields access, not construction
            return {}

    # Construction itself does NOT raise (proves the guard is not on the constructor).
    CtxSer()
    with pytest.raises(ConfigurationError, match="schema-time field set"):
        get_serializer_for_schema(CtxSer)


def test_schema_hook_stable_field_map_generates_input():
    """A stable ``field_map`` supplied to the generator builds the input without no-arg discovery.

    The Slice-2 ``get_serializer_for_schema()`` classmethod hook returns a stable map
    for a context-requiring serializer; the generators build off the supplied
    ``field_map`` directly (no monkeypatching of the module-level discovery - the
    bind threads the hook's result through this parameter).
    """

    class CtxSer(serializers.Serializer):
        def get_fields(self):  # pragma: no cover - never called; field_map is supplied.
            _ = self.context["tenant"]
            return {}

    stable = {"name": _bound(serializers.CharField(), "name")}
    cre, _shape, _par, _pshape = build_serializer_inputs(CtxSer, field_map=dict(stable))
    assert set(_field_map(cre)) == {"name"}


def _bound(field: serializers.Field, name: str) -> serializers.Field:
    """Bind a serializer field for use in a hand-built stable field map."""
    field.bind(name, None)
    return field


# ---------------------------------------------------------------------------
# The two generated inputs - create + partial requiredness
# ---------------------------------------------------------------------------


def test_create_input_required_and_optional_shapes():
    """``<Serializer>Input``: required fields non-optional, optional fields ``| None`` + UNSET."""
    _register_products_types()
    cre, _, _, _ = build_serializer_inputs(_item_serializer())
    assert cre.__name__ == "ItemSerInput"
    fields = _field_map(cre)

    # ``name`` (required TextField) is non-optional.
    assert not _is_optional(fields["name"])
    assert _inner_type(fields["name"]) is str

    # The FK ``category`` -> ``category_id`` / ``categoryId``, required.
    assert not _is_optional(fields["category_id"])
    assert fields["category_id"].graphql_name == "categoryId"

    # ``is_private`` has a model default, so DRF reports it ``required=False`` -> optional + UNSET.
    assert _is_optional(fields["is_private"])
    assert fields["is_private"].default is UNSET


def test_partial_input_all_fields_optional():
    """``<Serializer>PartialInput``: every field optional + UNSET."""
    _register_products_types()
    _, _, par, _ = build_serializer_inputs(_item_serializer())
    assert par.__name__ == "ItemSerPartialInput"
    fields = _field_map(par)
    for name in ("name", "category_id", "is_private"):
        assert _is_optional(fields[name]), name
        assert fields[name].default is UNSET, name


def test_serializer_only_field_included():
    """A serializer-only (non-model) field appears in the input (derives from the serializer)."""

    class ContactSer(serializers.Serializer):
        name = serializers.CharField()
        captcha = serializers.CharField(required=False)

    cre, _, _, _ = build_serializer_inputs(ContactSer)
    fields = _field_map(cre)
    assert set(fields) == {"name", "captcha"}
    assert not _is_optional(fields["name"])
    assert _is_optional(fields["captcha"])


# ---------------------------------------------------------------------------
# Relation id mapping - Relay vs raw pk, serializer-only
# ---------------------------------------------------------------------------


def test_fk_to_non_relay_products_target_uses_raw_pk_id():
    """The products ``Item.category`` FK (non-Relay) becomes a raw pk id; reverse map preserved."""
    _register_products_types()
    cre, cshape, _, _ = build_serializer_inputs(_item_serializer())
    fields = _field_map(cre)
    assert _inner_type(fields["category_id"]) is int
    cat_spec = next(s for s in cshape.field_specs if s.target_name == "category")
    assert cat_spec.input_attr == "category_id"
    assert cat_spec.graphql_name == "categoryId"
    assert cat_spec.kind == RELATION_SINGLE


def test_serializer_only_relation_to_relay_target_uses_globalid():
    """A serializer-only relation to a Relay primary becomes ``<name>_id: GlobalID``."""
    relay_target, _ = _make_relay_target()

    class PickSer(serializers.Serializer):
        target = serializers.PrimaryKeyRelatedField(queryset=relay_target.objects.all())

    cre, _, _, _ = build_serializer_inputs(PickSer)
    fields = _field_map(cre)
    assert _inner_type(fields["target_id"]) is relay.GlobalID


# ---------------------------------------------------------------------------
# FileField -> Upload
# ---------------------------------------------------------------------------


def test_file_field_maps_to_upload():
    """A serializer ``FileField`` maps to ``Upload``."""

    class AvatarSer(serializers.Serializer):
        avatar = serializers.FileField()

    cre, _, _, _ = build_serializer_inputs(AvatarSer)
    fields = _field_map(cre)
    assert _inner_type(fields["avatar"]) is Upload


# ---------------------------------------------------------------------------
# choices over a ModelSerializer column -> the SAME read-side enum
# ---------------------------------------------------------------------------


def test_choices_modelserializer_field_resolves_to_read_side_enum():
    """A ``ModelSerializer`` field over a model ``choices`` column reuses the read converter's enum.

    Proves the model-backed overlap routes through ``convert_scalar`` /
    ``convert_choices_to_enum`` (the symmetric wire contract), not a parallel
    serializer-field table.
    """
    from django_strawberry_framework.types.converters import convert_choices_to_enum

    class Widget(models.Model):
        status = models.TextField(choices=[("a", "A"), ("b", "B")])

        class Meta:
            app_label = _unique_app_label()

    class WidgetType(DjangoType):
        class Meta:
            model = Widget
            fields = ("id", "status")

    class WidgetSer(serializers.ModelSerializer):
        class Meta:
            model = Widget
            fields = ("status",)

    cre, _, _, _ = build_serializer_inputs(WidgetSer)
    fields = _field_map(cre)
    read_enum = convert_choices_to_enum(Widget._meta.get_field("status"), "WidgetSerInput")
    assert _inner_type(fields["status"]).wrapped_cls is read_enum


# ---------------------------------------------------------------------------
# read_only / HiddenField dropped + Meta.fields / Meta.exclude narrowing
# ---------------------------------------------------------------------------


def test_read_only_and_hidden_fields_dropped():
    """``read_only`` and ``HiddenField`` fields are dropped from the input."""

    class S(serializers.Serializer):
        name = serializers.CharField()
        ro = serializers.CharField(read_only=True)
        hid = serializers.HiddenField(default="x")

    cre, _, _, _ = build_serializer_inputs(S)
    assert set(_field_map(cre)) == {"name"}


def test_fields_narrowing_omits_dropped_field():
    """``Meta.fields`` narrows the input; ``Meta.exclude`` drops the named field."""
    _register_products_types()
    cre, _, _, _ = build_serializer_inputs(
        _item_serializer(),
        fields=("name", "category", "is_private"),
        guard_required=False,
    )
    assert "is_private" in _field_map(cre)
    cre2, _, _, _ = build_serializer_inputs(
        _item_serializer(),
        exclude=("is_private",),
        guard_required=False,
    )
    assert "is_private" not in _field_map(cre2)


def test_meta_fields_rejects_bare_string():
    """A bare-string ``Meta.fields`` raises (it would iterate as characters)."""
    with pytest.raises(ConfigurationError, match="bare string"):
        resolve_effective_serializer_fields(_item_serializer(), fields="name")


def test_meta_fields_rejects_unknown_name():
    """An unknown name (a typo) raises naming the unknown field."""
    with pytest.raises(ConfigurationError, match="unknown or non-writable"):
        resolve_effective_serializer_fields(_item_serializer(), fields=("nmae",))


def test_meta_fields_and_exclude_mutually_exclusive():
    """Declaring both ``fields`` and ``exclude`` raises."""
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):
        resolve_effective_serializer_fields(
            _item_serializer(),
            fields=("name",),
            exclude=("category",),
        )


def test_empty_effective_field_set_raises():
    """An ``exclude`` dropping every field (empty effective set) raises."""
    with pytest.raises(ConfigurationError, match="has no fields"):
        resolve_effective_serializer_fields(
            _item_serializer(),
            exclude=("name", "category", "is_private"),
        )


# ---------------------------------------------------------------------------
# optional_fields force-optional + "__all__" bare-string rejection
# ---------------------------------------------------------------------------


def test_optional_fields_forces_create_field_optional():
    """The ``optional_fields`` PARAMETER forces a create field optional regardless of ``field.required``.

    ``optional_fields`` is the MUTATION's ``Meta`` key (spec-039 Critical-1), threaded
    into the generator as a parameter - NOT read off the serializer's own ``Meta``.
    """

    class S(serializers.Serializer):
        a = serializers.CharField()
        b = serializers.CharField()

    cre, _, _, _ = build_serializer_inputs(S, optional_fields=("a",))
    fields = _field_map(cre)
    assert _is_optional(fields["a"])
    assert not _is_optional(fields["b"])


def test_serializer_meta_optional_fields_is_not_the_api():
    """``optional_fields`` on the SERIALIZER's own ``Meta`` is ignored - it is the mutation key (Critical-1)."""

    class S(serializers.Serializer):
        a = serializers.CharField()
        b = serializers.CharField()

        class Meta:
            optional_fields = ("a",)  # the serializer's own Meta - NOT the input API

    cre, _, _, _ = build_serializer_inputs(S)  # no optional_fields parameter passed
    fields = _field_map(cre)
    # ``a`` stays REQUIRED: the serializer-level Meta key has no effect on the input.
    assert not _is_optional(fields["a"])
    assert not _is_optional(fields["b"])


def test_optional_fields_all_bare_string_rejected():
    """``optional_fields = "__all__"`` (a bare string parameter) is rejected (no field-selector sentinel)."""

    class S(serializers.Serializer):
        a = serializers.CharField()

    with pytest.raises(ConfigurationError, match="bare string"):
        build_serializer_inputs(S, optional_fields="__all__")


# ---------------------------------------------------------------------------
# SerializerInputShape descriptor identity
# ---------------------------------------------------------------------------


def test_optional_fields_difference_yields_distinct_names():
    """Two create inputs over the same serializer but different ``optional_fields`` get distinct names."""

    class Pair(serializers.Serializer):
        a = serializers.CharField()
        b = serializers.CharField()

    cre_opt, _, _, _ = build_serializer_inputs(Pair, optional_fields=("a",))
    cre_noopt, _, _, _ = build_serializer_inputs(Pair)
    # The full no-optional shape takes the canonical name; the optional_fields
    # divergence takes a deterministic descriptor-derived name - so the SAME
    # serializer + field set under different optional_fields never collides.
    assert cre_noopt.__name__ == "PairInput"
    assert cre_opt.__name__ != "PairInput"


def test_differing_annotations_yield_distinct_descriptor_names():
    """Two same-name-set shapes with different annotations get distinct descriptor names."""

    class StrSer(serializers.Serializer):
        x = serializers.CharField()

    class IntSer(serializers.Serializer):
        x = serializers.IntegerField()

    cre_str, _, _, _ = build_serializer_inputs(StrSer, optional_fields=("x",))
    cre_int, _, _, _ = build_serializer_inputs(IntSer, optional_fields=("x",))
    # Both are divergent shapes (optional_fields set); their descriptor-derived
    # suffixes encode the differing annotation, so the names differ.
    assert cre_str.__name__ != cre_int.__name__


def test_identical_descriptor_dedupes_via_ledger():
    """Materializing the same class twice under one name is a no-op (identical descriptors dedupe)."""
    _register_products_types()
    cre, _, _, _ = build_serializer_inputs(_item_serializer())
    materialize_serializer_input_class("ItemSerInput", cre)
    materialize_serializer_input_class("ItemSerInput", cre)  # idempotent, no raise
    assert sys.modules[SERIALIZER_INPUTS_MODULE_PATH].ItemSerInput is cre


def test_distinct_descriptors_colliding_on_one_name_raise():
    """Two DISTINCT classes under one name raise ``ConfigurationError`` (the collision raise)."""
    _register_products_types()
    cre_a, _ = build_serializer_input_class(_item_serializer(), operation_kind="create")

    class OtherSer(serializers.Serializer):
        x = serializers.CharField()

    cre_b, _ = build_serializer_input_class(OtherSer, operation_kind="create")
    materialize_serializer_input_class("CollidingInput", cre_a)
    with pytest.raises(ConfigurationError, match="SerializerMutation"):
        materialize_serializer_input_class("CollidingInput", cre_b)


def test_descriptor_is_its_own_cache_key():
    """The frozen ``SerializerInputShape`` is hashable and is its own cache key."""
    _register_products_types()
    _, cshape, _, _ = build_serializer_inputs(_item_serializer())
    assert isinstance(cshape, SerializerInputShape)
    assert cshape.cache_key is cshape
    # Hashable (frozen dataclass) - usable as a dict key.
    {cshape: 1}


# ---------------------------------------------------------------------------
# Create-required narrowing guard + waiver + per-declaration discipline
# ---------------------------------------------------------------------------


def _required_field_serializer():
    """A serializer with a required scalar, a required relation, and an optional field."""

    class S(serializers.Serializer):
        required_scalar = serializers.CharField()
        maybe = serializers.CharField(required=False)

    return S


def test_create_guard_rejects_dropping_required_scalar():
    """A create ``Meta.fields`` dropping a required scalar raises naming it."""
    with pytest.raises(ConfigurationError, match="required_scalar"):
        build_serializer_inputs(_required_field_serializer(), fields=("maybe",))


def test_create_guard_rejects_dropping_required_relation():
    """A create ``Meta.exclude`` dropping a required relation raises naming it."""
    _register_products_types()
    with pytest.raises(ConfigurationError, match="category"):
        build_serializer_inputs(_item_serializer(), exclude=("category",))


def test_read_only_exclusion_does_not_trip_guard():
    """Excluding a ``read_only`` / ``HiddenField`` field does NOT trip the create guard."""

    class S(serializers.Serializer):
        name = serializers.CharField()
        ro = serializers.CharField(read_only=True)

    # ``ro`` is dropped automatically; the guard sees only writable required fields.
    cre, _, _, _ = build_serializer_inputs(S)  # no raise
    assert set(_field_map(cre)) == {"name"}


def test_create_guard_waiver_does_not_raise():
    """``guard_required=False`` (the get_serializer_kwargs-override waiver) builds without raising."""
    cre, _, _, _ = build_serializer_inputs(
        _required_field_serializer(),
        fields=("maybe",),
        guard_required=False,
    )
    assert "required_scalar" not in _field_map(cre)


def test_guard_runs_per_declaration():
    """The guard fires PER declaration; a waiving build first does not suppress a later one.

    Asserted by calling ``guard_create_required_serializer_fields`` directly (the
    form precedent): a waiving build never runs the guard, so a later non-waiving
    build of the same effective set still raises.
    """
    ser = _required_field_serializer()
    effective = resolve_effective_serializer_fields(ser, fields=("maybe",))
    # First, a waiving build (guard_required=False) materializes the shape - no guard.
    build_serializer_inputs(ser, fields=("maybe",), guard_required=False)
    # A later non-waiving check on the SAME effective set still raises.
    with pytest.raises(ConfigurationError, match="required_scalar"):
        guard_create_required_serializer_fields(ser, effective)


# ---------------------------------------------------------------------------
# Nullability / defaults (M2)
# ---------------------------------------------------------------------------


def test_required_allow_null_field_is_nullable_and_omittable():
    """``required=True, allow_null=True`` -> nullable annotation AND omittable (UNSET default), spec-039 H3.

    GraphQL cannot express required-AND-nullable, so the field is OMITTABLE (default
    ``UNSET``): omission is stripped by the resolver so DRF sees the key MISSING and
    raises its own field-keyed required error IN-BAND, rather than a top-level coercion
    error from a required nullable field with no default (the bug H3 flags). An explicit
    ``null`` still reaches DRF as ``None``.
    """

    class S(serializers.Serializer):
        nick = serializers.CharField(allow_null=True)  # required=True by default

    cre, _, _, _ = build_serializer_inputs(S)
    field = _field_map(cre)["nick"]
    assert _is_optional(field)  # annotation is T | None (allow_null)
    # OMITTABLE (UNSET default): the must-provide half is enforced by DRF, not GraphQL,
    # so omitting the key cannot fail at input-dataclass construction (H3).
    assert field.default is UNSET


def test_required_non_null_field_is_required_with_no_default():
    """``required=True, allow_null=False`` -> bare (non-null) annotation, NO default (GraphQL enforces presence)."""

    class S(serializers.Serializer):
        nick = serializers.CharField()  # required=True, allow_null=False

    cre, _, _, _ = build_serializer_inputs(S)
    field = _field_map(cre)["nick"]
    assert not _is_optional(field)  # bare T (non-null)
    # No UNSET default: GraphQL itself enforces presence + non-null for this field.
    assert field.default is not UNSET


def test_field_with_default_is_optional_no_fabricated_default():
    """``required=False`` (a DRF default) -> omittable + UNSET, no fabricated GraphQL default."""

    class S(serializers.Serializer):
        note = serializers.CharField(required=False, default="x")

    cre, _, _, _ = build_serializer_inputs(S)
    field = _field_map(cre)["note"]
    assert _is_optional(field)
    # The GraphQL default is UNSET (omittable), NOT the DRF ``"x"`` default.
    assert field.default is UNSET


# ---------------------------------------------------------------------------
# Collisions - input attr / GraphQL name / writable source
# ---------------------------------------------------------------------------


def test_relation_id_attr_collision_is_fail_loud():
    """A relation ``category`` (-> ``category_id``) colliding with a literal ``category_id`` raises."""
    _register_products_types()

    class CollidingSer(serializers.Serializer):
        category = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
        )
        category_id = serializers.IntegerField()

    with pytest.raises(ConfigurationError) as exc:
        build_serializer_inputs(CollidingSer)
    message = str(exc.value)
    assert "category_id" in message
    assert "collide" in message


def test_camel_case_graphql_name_collision_is_fail_loud():
    """Two fields whose names default-camel-case to ONE GraphQL name raise."""

    class CamelCollideSer(serializers.Serializer):
        foo_bar = serializers.IntegerField()
        fooBar = serializers.IntegerField()  # noqa: N815 - intentional collision fixture

    with pytest.raises(ConfigurationError) as exc:
        build_serializer_inputs(CamelCollideSer)
    assert "collide" in str(exc.value)


def test_two_writable_fields_sharing_one_source_raise():
    """Two WRITABLE fields sharing one one-segment ``source`` raise (no double-write)."""
    _register_products_types()

    class DoubleWriteSer(serializers.ModelSerializer):
        name = serializers.CharField()
        alias = serializers.CharField(source="name")

        class Meta:
            model = product_models.Item
            fields = ("name", "alias")

    with pytest.raises(ConfigurationError, match="sharing one source"):
        build_serializer_inputs(DoubleWriteSer, guard_required=False)


def test_read_only_field_sharing_source_with_writable_is_accepted():
    """A ``read_only`` field sharing a ``source`` with a writable one is accepted (read-only dropped)."""
    _register_products_types()

    class MixedSer(serializers.ModelSerializer):
        name = serializers.CharField()
        name_echo = serializers.CharField(source="name", read_only=True)

        class Meta:
            model = product_models.Item
            fields = ("name", "name_echo")

    # ``name_echo`` is read-only -> dropped, so no source collision.
    cre, _, _, _ = build_serializer_inputs(MixedSer, guard_required=False)
    assert set(_field_map(cre)) == {"name"}


# ---------------------------------------------------------------------------
# Module-global materialization
# ---------------------------------------------------------------------------


def test_materialized_input_is_module_global():
    """A materialized input class is a real global of ``rest_framework.inputs`` (the lazy-ref contract)."""
    _register_products_types()
    cre, _, _, _ = build_serializer_inputs(_item_serializer())
    materialize_serializer_input_class("ItemSerInput", cre)
    assert sys.modules[SERIALIZER_INPUTS_MODULE_PATH].ItemSerInput is cre


# ---------------------------------------------------------------------------
# Reverse map - scalar identity
# ---------------------------------------------------------------------------


def test_scalar_reverse_map_is_identity():
    """A plain scalar field's reverse map is identity (``name`` -> ``name``, kind scalar)."""
    _register_products_types()
    _, cshape, _, _ = build_serializer_inputs(_item_serializer())
    name_spec = next(s for s in cshape.field_specs if s.target_name == "name")
    assert name_spec.input_attr == "name"
    assert name_spec.graphql_name == "name"
    assert name_spec.kind == SCALAR
    assert name_spec.source is None
