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
from django_strawberry_framework.rest_framework import inputs as serializer_inputs
from django_strawberry_framework.rest_framework.inputs import (
    SERIALIZER_INPUTS_MODULE_PATH,
    NestedSerializerConfig,
    SerializerInputShape,
    build_serializer_input_class,
    build_serializer_inputs,
    clear_serializer_input_namespace,
    describe_serializer_input,
    get_serializer_for_schema,
    guard_create_required_serializer_fields,
    materialize_serializer_input_class,
    resolve_effective_serializer_fields,
)
from django_strawberry_framework.rest_framework.serializer_converter import (
    NESTED_MULTI,
    NESTED_SINGLE,
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


def test_meta_exclude_rejects_unknown_name():
    """An unknown name in ``exclude`` raises naming the unknown field (the ``exclude`` arm of the guard)."""
    with pytest.raises(ConfigurationError, match="unknown or non-writable"):
        resolve_effective_serializer_fields(_item_serializer(), exclude=("nmae",))


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


def test_allow_null_difference_yields_distinct_descriptor_names():
    """Two divergent shapes over one serializer differing ONLY in a field's ``allow_null`` get distinct names (spec-039 High / M2).

    The descriptor identity records the EMITTED (post-nullable-widening) annotation, not the
    base one: a ``required=True, allow_null=False`` field is ``str`` while ``required=True,
    allow_null=True`` is ``str | None``. Two hook field maps over the SAME serializer that
    differ ONLY in a same-name field's ``allow_null`` are therefore DISTINCT descriptors and
    take distinct descriptor-derived names - so the per-shape build cache cannot hand the
    second declaration the first's cached class (which would give it the wrong nullability).
    The live ``/graphql/`` proof is
    ``examples/fakeshop/test_query/test_library_api.py``
    ``::test_serializer_hooks_differing_only_in_allow_null_bind_distinct_nullability_over_http``;
    this is the focused pure-function backstop on the descriptor token (the ``allow_null`` axis
    beside the annotation-type axis above).
    """

    class Ser(serializers.Serializer):
        x = serializers.CharField()

    def _field_map(*, allow_null: bool) -> dict:
        class _HookSer(serializers.Serializer):
            x = serializers.CharField()
            note = serializers.CharField(required=True, allow_null=allow_null)

        return dict(_HookSer().fields)

    # Both hook shapes ({x, note}) diverge from Ser's default ({x}), so each takes a
    # descriptor-derived name; ``note`` is required in both (nullability driven only by
    # allow_null), so the emitted ``str`` vs ``str | None`` is the sole differing axis.
    cre_non_null, _, _, _ = build_serializer_inputs(Ser, field_map=_field_map(allow_null=False))
    cre_nullable, _, _, _ = build_serializer_inputs(Ser, field_map=_field_map(allow_null=True))
    assert cre_non_null.__name__ != cre_nullable.__name__


def test_descriptor_name_distinguishes_relation_target_model():
    """Two relation shapes differing ONLY in ``related_model`` get DISTINCT names (spec-039).

    The per-shape build cache already separates them (``InputFieldSpec.related_model``
    is part of the frozen ``field_specs`` tuple), so the generated NAME must separate
    them too - otherwise two distinct descriptors (a ``target`` relation pointed at
    different models by a schema hook) collide on one materialized name. Exercises the
    ``related_model`` fold in the per-field token directly.
    """
    from django_strawberry_framework.rest_framework.inputs import serializer_input_type_name
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class HookSer(serializers.Serializer):
        pass

    def _name_for(target_model: type) -> str:
        spec = InputFieldSpec(
            input_attr="target_id",
            graphql_name="targetId",
            target_name="target",
            kind=RELATION_SINGLE,
            source=None,
            related_model=target_model,
        )
        # A divergent (non-full) shape, so the descriptor-derived per-field token names it.
        return serializer_input_type_name(
            HookSer,
            "create",
            is_full_shape=False,
            field_specs=(spec,),
            annotations=("relay.GlobalID",),  # identical annotation for both targets
            required_state=(True,),
        )

    # Same field name + same annotation + same kind, only the target model differs.
    assert _name_for(product_models.Item) != _name_for(product_models.Category)


# NOTE: the unsupported-default-field recovery (``_default_full_shape_identity`` swallowing
# a WALK-time ``ConfigurationError``, not only a discovery-time one) is now earned LIVE over
# ``/graphql/`` per the ``test_query`` live-first rule, by
# ``examples/fakeshop/test_query/test_library_api.py``
# ``::test_create_shelf_via_hook_narrowed_serializer_recovers_unsupported_default_field``
# (an unsupported ``SlugRelatedField(many=True)`` default field a schema hook narrows away).
# The companion discovery-error -> None branch is earned live by the same suite's
# ``::test_create_shelf_via_schema_hook_serializer_executes_over_http``. The former
# package-only ``test_unsupported_default_field_does_not_reject_supported_hook_map`` was
# retired with that promotion (the converter's non-PK relation rejects stay covered by
# ``test_converter.py``); the pure-function name derivation stays unit-tested above by
# ``test_descriptor_name_distinguishes_relation_target_model``.


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


def test_read_only_field_dropped_before_create_guard():
    """A ``read_only`` field is DROPPED before the create-required guard sees the writable set.

    A ``read_only`` field is never an input field, so it is dropped from the writable set
    BEFORE the create-required-narrowing guard runs - the guard sees only writable required
    fields and is not tripped by the (already-dropped) read-only one. Explicitly EXCLUDING a
    read-only field is a different path that raises (see
    ``test_excluding_read_only_field_raises_non_writable``); this test pins only the default
    drop, which the prior name (``..._exclusion_does_not_trip_guard``) misdescribed.
    """

    class S(serializers.Serializer):
        name = serializers.CharField()
        ro = serializers.CharField(read_only=True)

    # ``ro`` is dropped automatically; the guard sees only writable required fields.
    cre, _, _, _ = build_serializer_inputs(S)  # no raise
    assert set(_field_map(cre)) == {"name"}


def test_excluding_read_only_field_raises_non_writable():
    """Explicitly excluding a ``read_only`` field raises unknown-or-non-writable (NOT a silent no-op).

    ``Meta.exclude`` is validated against the WRITABLE field set (after the read-only drop),
    so naming a ``read_only`` field in ``exclude`` is an unknown-or-non-writable error: the
    field is simply not in the set the narrowing is checked against. (A read-only field is
    never an input field, so neither selecting nor excluding it is meaningful - both arms fail
    loud, matching the ``fields`` arm; the resolver docstring no longer calls the exclude a
    no-op.)
    """

    class S(serializers.Serializer):
        name = serializers.CharField()
        ro = serializers.CharField(read_only=True)

    with pytest.raises(ConfigurationError, match="unknown or non-writable"):
        resolve_effective_serializer_fields(S, exclude=("ro",))


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


# ---------------------------------------------------------------------------
# Aggregate schema-time diagnostics (spec-039 rev6 #5)
# ---------------------------------------------------------------------------


def test_multiple_schema_time_problems_aggregate_into_one_error():
    """Several bad fields surface in ONE ConfigurationError (not one-fix-rerun-per-field) (#5)."""
    _register_products_types()

    class CustomField(serializers.Field):
        def to_internal_value(self, data):  # pragma: no cover - never reached in conversion.
            return data

        def to_representation(self, value):  # pragma: no cover - never reached in conversion.
            return value

    class MultiBadSer(serializers.ModelSerializer):
        # A non-PK relation (unsupported) ...
        slug_rel = serializers.SlugRelatedField(
            slug_field="name",
            queryset=product_models.Category.objects.all(),
        )
        # ... and an unmapped custom field (unsupported) - two distinct problems.
        weird = CustomField()

        class Meta:
            model = product_models.Item
            fields = ("slug_rel", "weird")

    with pytest.raises(ConfigurationError) as exc:
        build_serializer_inputs(MultiBadSer, guard_required=False)
    message = str(exc.value)
    # One aggregated error naming BOTH offending fields at once.
    assert "2 schema-time problem(s)" in message
    assert "slug_rel" in message
    assert "weird" in message


def test_single_schema_time_problem_raises_verbatim():
    """A SINGLE problem is raised verbatim (no aggregate header), preserving the precise message (#5)."""
    _register_products_types()

    class OneBadSer(serializers.ModelSerializer):
        slug_rel = serializers.SlugRelatedField(
            slug_field="name",
            queryset=product_models.Category.objects.all(),
        )

        class Meta:
            model = product_models.Item
            fields = ("slug_rel",)

    with pytest.raises(ConfigurationError, match="PrimaryKeyRelatedField") as exc:
        build_serializer_inputs(OneBadSer, guard_required=False)
    # No aggregate header for a single problem.
    assert "schema-time problem(s)" not in str(exc.value)


def test_generated_input_field_carries_drf_metadata_description():
    """A built input field carries the DRF ``help_text`` + constraint description (#9)."""

    class DescribedSer(serializers.Serializer):
        label = serializers.CharField(help_text="A label.", max_length=8)

    cre, _, _, _ = build_serializer_inputs(DescribedSer)
    (field,) = [f for f in cre.__strawberry_definition__.fields if f.python_name == "label"]
    assert field.description is not None
    assert "A label." in field.description
    assert "max_length=8" in field.description


def test_injected_fields_subtract_from_create_required_guard():
    """A required field a narrowing drops but that is DECLARED injected does not raise (rev6 #2)."""
    ser = _required_field_serializer()
    # Dropping `required_scalar` (narrow to `maybe`) is fine when it is declared injected.
    guard_create_required_serializer_fields(
        ser,
        ("maybe",),
        injected_fields=("required_scalar",),
    )  # no raise


def test_dropped_required_not_injected_still_raises():
    """A dropped required field NOT declared injected STILL raises (the guard is not blanket) (rev6 #2)."""
    ser = _required_field_serializer()
    with pytest.raises(ConfigurationError, match="required_scalar"):
        guard_create_required_serializer_fields(
            ser,
            ("maybe",),
            injected_fields=("something_else",),
        )


# ---------------------------------------------------------------------------
# Shape debug/introspection registry (spec-039 rev6 #15)
# ---------------------------------------------------------------------------


def test_describe_serializer_input_reports_shape():
    """``describe_serializer_input`` describes a built shape and returns ``None`` for an unknown name (rev6 #15)."""
    from django_strawberry_framework.rest_framework.inputs import describe_serializer_input

    class SourceSer(serializers.Serializer):
        display_name = serializers.CharField(source="name")

    _cre, cre_shape, _par, _par_shape = build_serializer_inputs(SourceSer)
    description = describe_serializer_input(cre_shape.type_name)
    assert description is not None
    assert "serializer:" in description
    assert "operation: create" in description
    assert "name:" in description
    assert "display_name" in description  # a field appears in the description
    assert "source='name'" in description
    assert describe_serializer_input("NoSuchGeneratedInput") is None


def test_materialize_collision_message_enriched_with_shape_description():
    """A distinct-class materialize collision enriches the error with the registered shape (rev6 #15)."""
    _register_products_types()
    cre, shape = build_serializer_input_class(_item_serializer(), operation_kind="create")
    materialize_serializer_input_class(shape.type_name, cre)  # first: ok

    class OtherSer(serializers.Serializer):
        different = serializers.CharField()

    other_cls, _other_shape = build_serializer_input_class(OtherSer, operation_kind="create")
    with pytest.raises(ConfigurationError) as exc:
        materialize_serializer_input_class(shape.type_name, other_cls)
    message = str(exc.value)
    assert "Shape registered under" in message
    assert "serializer:" in message


def test_schema_fingerprint_sensitive_to_choices_and_help_text():
    """The hook fingerprint changes when only choice members or help_text differ (rev6 rev2 P2)."""
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class C1(serializers.Serializer):
        color = serializers.ChoiceField(choices=[("r", "R")])

    class C2(serializers.Serializer):
        color = serializers.ChoiceField(choices=[("b", "B")])

    assert serializer_schema_fingerprint(dict(C1().fields)) != serializer_schema_fingerprint(
        dict(C2().fields),
    )

    class H1(serializers.Serializer):
        note = serializers.CharField(help_text="one")

    class H2(serializers.Serializer):
        note = serializers.CharField(help_text="two")

    assert serializer_schema_fingerprint(dict(H1().fields)) != serializer_schema_fingerprint(
        dict(H2().fields),
    )


def test_schema_fingerprint_sensitive_to_converter_extras():
    """The fingerprint changes when a ``ModelField`` wrapped field or a ``ListField`` child differs (rev6 rev2 P2)."""
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class ModelFieldA(serializers.Serializer):
        wrapped = serializers.ModelField(
            model_field=product_models.Item._meta.get_field("name"),
        )

    class ModelFieldB(serializers.Serializer):
        wrapped = serializers.ModelField(
            model_field=product_models.Item._meta.get_field("is_private"),
        )

    assert serializer_schema_fingerprint(
        {"wrapped": ModelFieldA().fields["wrapped"]},
    ) != serializer_schema_fingerprint({"wrapped": ModelFieldB().fields["wrapped"]})

    class ListA(serializers.Serializer):
        items = serializers.ListField(child=serializers.IntegerField())

    class ListB(serializers.Serializer):
        items = serializers.ListField(child=serializers.CharField())

    assert serializer_schema_fingerprint(dict(ListA().fields)) != serializer_schema_fingerprint(
        dict(ListB().fields),
    )


# ===========================================================================
# Opt-in nested serializer inputs (spec-039 rev6 #17)
# ===========================================================================


def _nested_child_serializer():
    """A plain nested serializer (two scalars) for the nested-input build tests."""

    class Child(serializers.Serializer):
        code = serializers.CharField()
        note = serializers.CharField(required=False)

    return Child


def test_nested_serializer_config_defaults_and_root_import():
    """``NestedSerializerConfig`` is importable from the package root and defaults to all-None (rev6 #17)."""
    import django_strawberry_framework as dsf

    assert dsf.NestedSerializerConfig is NestedSerializerConfig
    config = NestedSerializerConfig()
    assert config.fields is None
    assert config.exclude is None
    assert config.optional_fields is None
    assert config.nested_fields is None


def test_nested_single_field_builds_recursive_input():
    """A single opted-in nested serializer field builds a nested input class + records nested_specs (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        title = serializers.CharField()
        detail = child()

    cls, shape = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    fields = _field_map(cls)
    assert set(fields) == {"title", "detail"}
    detail_spec = next(s for s in shape.field_specs if s.target_name == "detail")
    assert detail_spec.kind == NESTED_SINGLE
    assert [s.target_name for s in detail_spec.nested_specs] == ["code", "note"]


def test_nested_multi_field_builds_list_of_nested_input():
    """A ``many=True`` opted-in nested serializer builds a ``list[<nested>]`` field (kind nested_multi) (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        title = serializers.CharField()
        items = child(many=True)

    _cls, shape = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"items": NestedSerializerConfig()},
    )
    items_spec = next(s for s in shape.field_specs if s.target_name == "items")
    assert items_spec.kind == NESTED_MULTI
    assert [s.target_name for s in items_spec.nested_specs] == ["code", "note"]


def test_nested_config_narrows_nested_fields():
    """``NestedSerializerConfig(fields=...)`` narrows the NESTED input's field set (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        detail = child()

    _cls, shape = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig(fields=("code",))},
    )
    detail_spec = next(s for s in shape.field_specs if s.target_name == "detail")
    assert [s.target_name for s in detail_spec.nested_specs] == ["code"]


def test_nested_config_deeper_nesting_opts_in_grandchild():
    """A ``NestedSerializerConfig.nested_fields`` opts a DEEPER nested serializer in (rev6 #17)."""

    class Grand(serializers.Serializer):
        leaf = serializers.CharField()

    class Child(serializers.Serializer):
        code = serializers.CharField()
        grand = Grand()

    class Parent(serializers.Serializer):
        child = Child()

    _cls, shape = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={
            "child": NestedSerializerConfig(nested_fields={"grand": NestedSerializerConfig()}),
        },
    )
    child_spec = next(s for s in shape.field_specs if s.target_name == "child")
    grand_spec = next(s for s in child_spec.nested_specs if s.target_name == "grand")
    assert grand_spec.kind == NESTED_SINGLE
    assert [s.target_name for s in grand_spec.nested_specs] == ["leaf"]


def test_nested_field_without_opt_in_still_rejects():
    """A nested serializer field NOT named in ``nested_configs`` fails loud (nesting is opt-in only) (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        detail = child()

    with pytest.raises(ConfigurationError, match="opt-in only"):
        build_serializer_input_class(Parent, operation_kind="create")


def test_nested_cycle_guard_fails_loud():
    """A self-nesting serializer (a class re-entering the recursion path) fails loud (rev6 #17)."""

    class SelfNest(serializers.Serializer):
        x = serializers.CharField()

        def get_fields(self):
            fields = super().get_fields()
            fields["me"] = SelfNest()
            return fields

    with pytest.raises(ConfigurationError, match="cycle"):
        build_serializer_input_class(
            SelfNest,
            operation_kind="create",
            nested_configs={"me": NestedSerializerConfig()},
        )


def test_nested_depth_guard_fails_loud(monkeypatch):
    """Nesting deeper than ``_NESTED_MAX_DEPTH`` (distinct serializers, no cycle) fails loud (rev6 #17)."""
    monkeypatch.setattr(serializer_inputs, "_NESTED_MAX_DEPTH", 1)

    class Inner(serializers.Serializer):
        y = serializers.CharField()

    class Outer(serializers.Serializer):
        inner = Inner()

    with pytest.raises(ConfigurationError, match="maximum nesting depth"):
        build_serializer_input_class(
            Outer,
            operation_kind="create",
            nested_configs={"inner": NestedSerializerConfig()},
        )


def test_nested_config_key_not_in_effective_set_raises():
    """A ``nested_fields`` key naming a field NOT in the effective set fails loud (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        detail = child()

    with pytest.raises(ConfigurationError, match="not in the effective input set"):
        build_serializer_input_class(
            Parent,
            operation_kind="create",
            nested_configs={"ghost": NestedSerializerConfig()},
        )


def test_nested_config_key_naming_scalar_raises():
    """A ``nested_fields`` key naming a SCALAR (not a nested serializer) fails loud (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        title = serializers.CharField()
        detail = child()

    with pytest.raises(ConfigurationError, match="not a nested serializer"):
        build_serializer_input_class(
            Parent,
            operation_kind="create",
            nested_configs={"title": NestedSerializerConfig(), "detail": NestedSerializerConfig()},
        )


def test_identical_nested_shape_dedupes_to_one_class():
    """Two builds of the same nested shape resolve the nested input to ONE cached class object (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        detail = child()

    first, _ = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    second, _ = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    # The nested field annotation resolves to the SAME cached nested class (the dedupe cache hit).
    first_nested = _field_map(first)["detail"].type
    second_nested = _field_map(second)["detail"].type

    def _unwrap(t):
        return getattr(t, "of_type", t)

    assert _unwrap(first_nested) is _unwrap(second_nested)


def test_distinct_nested_shapes_yield_distinct_top_names():
    """Two DIFFERENT nested shapes give the top inputs DISTINCT descriptor-derived names (rev6 #17)."""

    class ChildA(serializers.Serializer):
        code = serializers.CharField()

    class ChildB(serializers.Serializer):
        code = serializers.CharField()
        extra = serializers.IntegerField()

    class ParentA(serializers.Serializer):
        detail = ChildA()

    class ParentB(serializers.Serializer):
        detail = ChildB()

    _a, shape_a = build_serializer_input_class(
        ParentA,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    _b, shape_b = build_serializer_input_class(
        ParentB,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    assert shape_a.type_name != shape_b.type_name


def test_build_serializer_inputs_threads_nested_into_both_shapes():
    """``build_serializer_inputs`` threads ``nested_configs`` into BOTH the create + partial shapes (rev6 #17)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        detail = child()

    create_cls, create_shape, partial_cls, partial_shape = build_serializer_inputs(
        Parent,
        guard_required=False,
        nested_configs={"detail": NestedSerializerConfig()},
    )
    assert "detail" in _field_map(create_cls)
    assert "detail" in _field_map(partial_cls)
    assert (
        next(s for s in create_shape.field_specs if s.target_name == "detail").kind
        == NESTED_SINGLE
    )
    assert (
        next(s for s in partial_shape.field_specs if s.target_name == "detail").kind
        == NESTED_SINGLE
    )


def test_recursive_fingerprint_sensitive_to_nested_shape_change():
    """The fingerprint recurses into an OPTED-IN nested serializer's fields (a nested change is detected) (rev6 #17)."""
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class ChildA(serializers.Serializer):
        code = serializers.CharField()

    class ChildB(serializers.Serializer):
        code = serializers.CharField()
        extra = serializers.CharField()

    class ParentA(serializers.Serializer):
        detail = ChildA()

    class ParentB(serializers.Serializer):
        detail = ChildB()

    # Opt the nested field in (rev6 #17 review P2): only then does the fingerprint descend.
    configs = {"detail": NestedSerializerConfig()}
    fp_a = serializer_schema_fingerprint(dict(ParentA().fields), nested_configs=configs)
    fp_b = serializer_schema_fingerprint(dict(ParentB().fields), nested_configs=configs)
    assert fp_a != fp_b
    # The recursion actually descended into the child map (not a shallow marker): ``extra`` shows up.
    assert "extra" in repr(fp_b)
    assert "extra" not in repr(fp_a)


def test_recursive_fingerprint_terminates_on_nested_cycle():
    """The recursive fingerprint terminates (a cycle marker) for an OPTED-IN self-nesting serializer (rev6 #17)."""
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class SelfNest(serializers.Serializer):
        x = serializers.CharField()

        def get_fields(self):
            fields = super().get_fields()
            fields["me"] = SelfNest()
            return fields

    # Opt ``me`` in at two levels so the recursion re-enters SelfNest and hits the on-path cycle
    # guard (rev6 #17 review P2: an unopted nested field is not descended into at all).
    configs = {"me": NestedSerializerConfig(nested_fields={"me": NestedSerializerConfig()})}
    fingerprint = serializer_schema_fingerprint(dict(SelfNest().fields), nested_configs=configs)
    # It terminated (no RecursionError) and the nested axis carries the cycle marker.
    flat = repr(fingerprint)
    assert "<cycle>" in flat


def test_describe_serializer_input_reports_nested_fields():
    """``describe_serializer_input`` lists a nested field's own child field names (rev6 #17 / #15)."""
    child = _nested_child_serializer()

    class Parent(serializers.Serializer):
        detail = child()

    _cls, shape = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    description = describe_serializer_input(shape.type_name)
    assert description is not None
    assert "kind=nested_single" in description
    assert "nested_fields=[code, note]" in description


def test_fingerprint_skips_read_only_nested_serializer():
    """The fingerprint does NOT descend into a read-only nested serializer (rev6 #17 review P1).

    A read-only nested output serializer whose ``get_fields()`` raises if read must not break
    class validation - it never produces an input field, so the writable-scoped fingerprint
    skips it (its ``.fields`` is never materialized).
    """
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class RaisingChild(serializers.Serializer):
        def get_fields(self):
            raise RuntimeError("child fields should not be read")

    class Parent(serializers.Serializer):
        name = serializers.CharField()
        child = RaisingChild(read_only=True)

    # No RuntimeError: the read-only nested field is dropped before fingerprinting.
    fingerprint = serializer_schema_fingerprint(dict(Parent().fields))
    # Only the writable ``name`` field is fingerprinted (the read-only child is absent).
    assert len(fingerprint) == 1
    assert fingerprint[0][0] == "name"


def test_fingerprint_wraps_nested_fields_error_as_configuration_error():
    """An OPTED-IN nested serializer whose ``.fields`` cannot be read is a clear ConfigurationError (rev6 #17 review P1)."""
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class RaisingWritableChild(serializers.Serializer):
        def get_fields(self):
            raise RuntimeError("cannot read no-arg")

    class Parent(serializers.Serializer):
        child = RaisingWritableChild()  # writable + opted in -> reached by the fingerprint

    with pytest.raises(ConfigurationError, match="Could not materialize the nested serializer"):
        serializer_schema_fingerprint(
            dict(Parent().fields),
            nested_configs={"child": NestedSerializerConfig()},
        )


def test_fingerprint_unopted_nested_raising_child_is_shallow_not_materialized():
    """An UNOPTED nested field is NOT descended into - a raising ``get_fields()`` is never read (rev6 #17 review P2).

    The prior behavior descended into every writable nested serializer, so an unopted,
    context-sensitive child raised a misleading "opted in via Meta.nested_fields..."
    materialization error at class validation - shadowing the canonical opt-in error the field
    walk raises. The fingerprint now records a shallow marker for an unopted nested field without
    reading its ``.fields``; the field walk (``build_serializer_input_class``) is what raises the
    opt-in error.
    """
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class RaisingChild(serializers.Serializer):
        def get_fields(self):
            raise RuntimeError("unopted nested child fields must not be read")

    class Parent(serializers.Serializer):
        name = serializers.CharField()
        child = RaisingChild()  # writable but NOT opted in

    # No nested_configs -> the unopted child is a shallow marker, not descended into (no RuntimeError).
    fingerprint = serializer_schema_fingerprint(dict(Parent().fields))
    child_entry = next(entry for entry in fingerprint if entry[0] == "child")
    assert child_entry[-1] == ("<unopted-nested>", "RaisingChild", False)
    # The canonical opt-in error surfaces from the field walk, not the materialization wrap.
    with pytest.raises(ConfigurationError, match="opt-in only"):
        build_serializer_input_class(Parent, operation_kind="create")


def test_nested_source_axis_recorded_single_and_many():
    """A nested field with ``source=`` records the normalized source axis (rev6 #17 review P1)."""

    class Inner(serializers.Serializer):
        x = serializers.CharField()

    class ParentSingle(serializers.Serializer):
        renamed = Inner(source="actual")

    _cls, shape = build_serializer_input_class(
        ParentSingle,
        operation_kind="create",
        nested_configs={"renamed": NestedSerializerConfig()},
    )
    assert next(s for s in shape.field_specs if s.target_name == "renamed").source == "actual"

    class ParentMany(serializers.Serializer):
        renamed = Inner(source="actual", many=True)

    _cls2, shape2 = build_serializer_input_class(
        ParentMany,
        operation_kind="create",
        nested_configs={"renamed": NestedSerializerConfig()},
    )
    assert next(s for s in shape2.field_specs if s.target_name == "renamed").source == "actual"


def test_nested_dotted_source_rejected():
    """A nested field with a dotted source / ``source='*'`` fails loud (rev6 #17 review P1)."""

    class Inner(serializers.Serializer):
        x = serializers.CharField()

    class Parent(serializers.Serializer):
        renamed = Inner(source="a.b")

    with pytest.raises(ConfigurationError, match="dotted source"):
        build_serializer_input_class(
            Parent,
            operation_kind="create",
            nested_configs={"renamed": NestedSerializerConfig()},
        )


def test_fingerprint_propagates_nested_configuration_error_unwrapped():
    """A nested ``get_fields()`` raising ConfigurationError propagates it unchanged, not double-wrapped (rev6 #17 review P1)."""
    from django_strawberry_framework.rest_framework.inputs import serializer_schema_fingerprint

    class BadConfigChild(serializers.Serializer):
        def get_fields(self):
            raise ConfigurationError("a specific nested config error")

    class Parent(serializers.Serializer):
        child = BadConfigChild()

    with pytest.raises(ConfigurationError, match="a specific nested config error"):
        serializer_schema_fingerprint(
            dict(Parent().fields),
            nested_configs={"child": NestedSerializerConfig()},
        )
