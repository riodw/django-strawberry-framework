"""Tests for ``DjangoType`` Meta validation, scalar mapping, relations, registry, and ``get_queryset``.

Slice scope:

- Slice 1 - registry behaviour (``register``, ``get``, collision, ``clear``).
- Slice 2 - Meta validation, scalar field synthesis, default ``get_queryset``,
  Strawberry finalization, ``convert_scalar`` direct unit coverage.
- Slice 3 - relation conversion (forward FK, reverse FK, nullable widening,
  finalization-time unregistered-target rejection); ``_build_annotations`` dispatch on
  ``field.is_relation`` rather than filtering relations out.

The ``has_custom_get_queryset`` sentinel and override-detection have
shipped and are tested directly. Optimizer downgrade-to-``Prefetch``
coverage belongs in ``tests/optimizer/``; the full forward-reference /
definition-order independence path is covered in
``tests/types/test_definition_order.py`` and
``tests/types/test_definition_order_schema.py``.

Where Slice 2 tests originally used ``fields = \"__all__\"`` on ``Category``,
they now either declare related types up front (so the registry resolves
``items`` / ``properties``) or use an explicit fields list to keep the
test focused on the behaviour under examination. ``CATEGORY_SCALAR_FIELDS``
captures the scalar-only field list used in those updated tests.
"""

import datetime
import functools
import itertools

import pytest
from apps.products.models import Category, Entry, Item, Property
from django.db import models

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.optimizer.hints import OptimizerHint
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.base import _detect_custom_get_queryset
from django_strawberry_framework.types.converters import (
    convert_scalar,
    resolved_relation_annotation,
)
from django_strawberry_framework.types.relations import PendingRelationAnnotation

CATEGORY_SCALAR_FIELDS = (
    "id",
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Slice 1 - registry behaviour
# ---------------------------------------------------------------------------


def test_registry_get_returns_none_for_unregistered_model():
    assert registry.get(Category) is None


def test_registry_collision_raises_configuration_error():
    class CategoryTypeA(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            primary = True

    with pytest.raises(
        ConfigurationError,
        match=r"Cannot register CategoryTypeB as primary for Category;.*CategoryTypeA is already the primary type",
    ):

        class CategoryTypeB(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                primary = True


def test_registry_clear_drops_types_and_enums():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert registry.get(Category) is CategoryType
    registry.clear()
    assert registry.get(Category) is None


# ---------------------------------------------------------------------------
# Slice 2 - Meta validation
# ---------------------------------------------------------------------------


def test_subclass_without_meta_passes_through():
    """Intermediate abstract subclasses (no Meta) skip the pipeline."""

    class AbstractType(DjangoType):
        pass

    assert registry.get(Category) is None
    assert not hasattr(AbstractType, "__strawberry_definition__")
    assert AbstractType.has_custom_get_queryset() is False


def test_detect_custom_get_queryset_returns_false_for_non_djangotype_class():
    """The helper is defensive for classes outside the DjangoType hierarchy."""

    class PlainType:
        pass

    assert _detect_custom_get_queryset(PlainType) is False


def test_meta_required_model_raises_when_missing():
    with pytest.raises(ConfigurationError, match="Meta.model is required"):

        class T(DjangoType):
            class Meta:
                fields = CATEGORY_SCALAR_FIELDS


def test_meta_model_must_be_django_model_class():
    with pytest.raises(ConfigurationError, match="Meta.model must be a Django model class"):

        class T(DjangoType):
            class Meta:
                model = "Category"
                fields = CATEGORY_SCALAR_FIELDS


@pytest.mark.parametrize(
    ("attr", "value", "message"),
    [
        ("fields", 123, "Meta.fields must be '__all__' or a non-string sequence"),
        ("fields", "name", "Meta.fields must be '__all__' or a non-string sequence"),
        ("exclude", 123, "Meta.exclude must be a non-string sequence"),
        ("exclude", "name", "Meta.exclude must be a non-string sequence"),
    ],
)
def test_meta_field_selectors_must_have_valid_shapes(attr, value, message):
    meta_cls = type("Meta", (), {"model": Category, attr: value})
    with pytest.raises(ConfigurationError, match=message):
        type("T", (DjangoType,), {"Meta": meta_cls})


def test_meta_optimizer_hints_must_be_mapping_when_declared():
    with pytest.raises(ConfigurationError, match="Meta.optimizer_hints must be a mapping"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                optimizer_hints = []


def test_meta_fields_and_exclude_mutually_exclusive():
    with pytest.raises(ConfigurationError, match="mutually exclusive"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                exclude = ["description"]


def test_meta_fields_and_exclude_mutually_exclusive_via_inheritance():
    """A ``fields`` value inherited from a parent ``Meta`` still trips the guard.

    Pins the ``getattr(meta, ..., None) is not None`` semantics: an earlier
    shape that gated on ``meta.__dict__`` membership would miss this case and
    silently let both directives coexist, with confusing field-selection
    semantics downstream. The child only declares ``exclude``; ``fields``
    comes in from the base class.
    """

    class BaseMeta:
        fields = ("id", "name")

    with pytest.raises(ConfigurationError, match="mutually exclusive"):

        class T(DjangoType):
            class Meta(BaseMeta):
                model = Category
                exclude = ("description",)


@pytest.mark.parametrize(
    "deferred_key",
    ["aggregate_class", "fields_class", "search_fields"],
)
def test_meta_rejects_each_deferred_key(deferred_key):
    """Every key in DEFERRED_META_KEYS must raise until the spec that owns it ships."""
    meta_attrs = {"model": Category, "fields": CATEGORY_SCALAR_FIELDS, deferred_key: object()}
    meta_cls = type("Meta", (), meta_attrs)
    with pytest.raises(ConfigurationError, match=deferred_key):
        type("T", (DjangoType,), {"Meta": meta_cls})


def test_meta_filterset_class_is_promoted_to_allowed_meta_keys():
    """``Meta.filterset_class`` ships in spec-021 Slice 3 (Decision-7 promotion gate)."""
    from django_strawberry_framework.types.base import ALLOWED_META_KEYS, DEFERRED_META_KEYS

    assert "filterset_class" in ALLOWED_META_KEYS
    assert "filterset_class" not in DEFERRED_META_KEYS


def test_meta_orderset_class_is_promoted_to_allowed_meta_keys():
    """``Meta.orderset_class`` ships in spec-028 Slice 3 (Decision-7 promotion gate)."""
    from django_strawberry_framework.types.base import ALLOWED_META_KEYS, DEFERRED_META_KEYS

    assert "orderset_class" in ALLOWED_META_KEYS
    assert "orderset_class" not in DEFERRED_META_KEYS


# TODO(spec-032-full_relay-0_0_9 Slice 1): One named-rejection test per relay
# helper plus the two re-affirmation pins (Decision 8; eight messages total):
#   test_interfaces_rejects_relay_globalid_named / ..._nodeid_named /
#   ..._connection_named / ..._listconnection_named / ..._edge_named /
#   ..._pageinfo_named
#     each helper in Meta.interfaces raises ConfigurationError whose message
#     NAMES the helper, what it is (scalar-like wrapper / annotation helper /
#     generic output type), and the remediation (relay.Node, or
#     Meta.connection / DjangoConnectionField for connection shapes).
#   test_interfaces_rejects_non_interface_class_named
#     the shipped generic rejection still names the offending class (pin).
#   test_connection_key_requires_relay_node
#     the shipped Meta.connection gate message (pin).

# TODO(spec-032-full_relay-0_0_9 Slice 3): Meta.relation_shapes key
# validation beside the other Meta validation (Decision 7):
#   test_meta_relation_shapes_in_allowed_meta_keys
#     in ALLOWED_META_KEYS, not in DEFERRED_META_KEYS.
#   test_relation_shapes_validation_matrix
#     non-dict, bad value, unknown field, non-relation field, single-valued
#     relation, excluded field, non-Relay declaring type each raise
#     ConfigurationError at type creation.
#   test_relation_shapes_on_consumer_authored_relation_raises
#     an explicit key naming a relation with a consumer annotation /
#     strawberry.field override raises with the overrides-own-the-shape
#     message (Revision 3; the silent-accept-then-skip path must not exist).


def test_interfaces_is_shipped_not_deferred():
    """``interfaces`` is a shipped Meta key (in ``ALLOWED_META_KEYS``), not deferred.

    Guards against the prior regression where ``test_meta_rejects_each_deferred_key``
    silently included ``"interfaces"`` and passed for the wrong reason - the
    ``_validate_interfaces`` shape error happens to contain the substring
    ``"interfaces"``, so the deferred-key ``match=`` regex was satisfied by a
    shape-validation message rather than a deferred-key message. The
    ``_validate_interfaces`` Decision-4 validator is the full shipped contract.
    """
    from django_strawberry_framework.types.base import ALLOWED_META_KEYS, DEFERRED_META_KEYS

    assert "interfaces" in ALLOWED_META_KEYS
    assert "interfaces" not in DEFERRED_META_KEYS


def test_select_fields_signature_accepts_validated_specs():
    """``_select_fields`` consumes the already-normalized specs from ``_ValidatedMeta``.

    Pins the Medium fix from ``rev-types__base.md``: the function no longer
    re-runs ``_normalize_fields_spec`` / ``_normalize_sequence_spec`` (those
    ran inside ``_validate_meta``) - it takes the model plus the two
    validated specs directly. Calling with both specs ``None`` returns every
    Django field; passing a fields tuple narrows the result.
    """
    from django_strawberry_framework.types.base import _select_fields

    all_selected = _select_fields(Category, None, None)
    assert {f.name for f in all_selected} >= set(CATEGORY_SCALAR_FIELDS)

    narrowed = _select_fields(Category, ("id", "name"), None)
    assert tuple(f.name for f in narrowed) == ("id", "name")

    excluded = _select_fields(Category, None, ("description",))
    assert "description" not in {f.name for f in excluded}
    assert "name" in {f.name for f in excluded}


def test_meta_filterset_class_rejects_non_filterset_value():
    """``_validate_filterset_class`` rejects non-``FilterSet`` values."""
    with pytest.raises(ConfigurationError, match="must be a FilterSet subclass"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                filterset_class = object


def test_meta_filterset_class_accepts_filterset_subclass():
    """A real ``FilterSet`` subclass is accepted and stored on the definition."""
    from django_strawberry_framework.filters import FilterSet

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            filterset_class = CategoryFilter

    definition = CategoryType.__django_strawberry_definition__
    assert definition.filterset_class is CategoryFilter


def test_meta_connection_in_allowed_meta_keys():
    """``Meta.connection`` ships in spec-030 Slice 1 - a net-new ALLOWED key.

    Net-new ALLOWED, NOT a DEFERRED_META_KEYS promotion (spec-030 Decision 8;
    mirrors the filterset/orderset precedent).
    """
    from django_strawberry_framework.types.base import ALLOWED_META_KEYS, DEFERRED_META_KEYS

    assert "connection" in ALLOWED_META_KEYS
    assert "connection" not in DEFERRED_META_KEYS


def test_meta_connection_non_dict_raises():
    """``Meta.connection`` must be a dict; a non-dict value raises ``ConfigurationError``."""
    from strawberry import relay

    with pytest.raises(ConfigurationError, match="must be a dict"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                connection = "nope"


def test_meta_connection_unknown_subkey_raises():
    """An unrecognized ``Meta.connection`` sub-key raises (typo guard)."""
    from strawberry import relay

    with pytest.raises(ConfigurationError, match="unknown sub-keys"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                connection = {"total_count": True, "bogus": 1}


def test_meta_connection_non_bool_total_count_raises():
    """``Meta.connection['total_count']`` must be a bool; a non-bool raises."""
    from strawberry import relay

    with pytest.raises(ConfigurationError, match="must be a bool"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                connection = {"total_count": "yes"}


def test_meta_connection_non_relay_type_raises():
    """``Meta.connection`` on a type whose ``interfaces`` omits ``relay.Node`` raises."""
    with pytest.raises(ConfigurationError, match="relay.Node"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                connection = {"total_count": True}


def test_meta_connection_accepts_direct_relay_node_inheritance():
    """``Meta.connection`` opt-in works on a direct ``relay.Node`` subclass (P2).

    ``docs/feedback.md`` P2: the Relay-shape gate for ``Meta.connection`` runs in
    ``__init_subclass__`` using the canonical ``_is_relay_shaped`` predicate, so a
    direct ``class Foo(DjangoType, relay.Node)`` - Relay-shaped WITHOUT
    ``Meta.interfaces`` - can opt into ``total_count``, matching the
    ``DjangoConnectionField`` field guard. One consistent definition of
    "Relay-shaped" across both surfaces.
    """
    from strawberry import relay

    class DirectCountNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            connection = {"total_count": True}

    definition = DirectCountNode.__django_strawberry_definition__
    # Relay-shaped via direct inheritance, not the Meta-tuple.
    assert relay.Node not in definition.interfaces
    assert definition.connection == {"total_count": True}


def test_meta_connection_stored_on_definition():
    """The normalized ``Meta.connection`` value lands on ``definition.connection``."""
    from strawberry import relay

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            connection = {"total_count": True}

    definition = CategoryType.__django_strawberry_definition__
    assert definition.connection == {"total_count": True}


def test_meta_connection_absent_leaves_definition_none():
    """A type without ``Meta.connection`` leaves ``definition.connection`` at its ``None`` default."""
    from strawberry import relay

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)

    definition = CategoryType.__django_strawberry_definition__
    assert definition.connection is None


# ---------------------------------------------------------------------------
# spec-031 Slice 1 - Meta.globalid_strategy + RELAY_GLOBALID_STRATEGY precedence
# ---------------------------------------------------------------------------


def test_meta_globalid_strategy_in_allowed_meta_keys():
    """``Meta.globalid_strategy`` ships in spec-031 Slice 1 - a net-new ALLOWED key.

    Net-new ALLOWED, NOT a ``DEFERRED_META_KEYS`` promotion (spec-031 Decision 6;
    mirrors the connection / filterset / orderset precedent).
    """
    from django_strawberry_framework.types.base import ALLOWED_META_KEYS, DEFERRED_META_KEYS

    assert "globalid_strategy" in ALLOWED_META_KEYS
    assert "globalid_strategy" not in DEFERRED_META_KEYS


def test_meta_globalid_strategy_unknown_string_raises():
    """A typo'd strategy string raises ``ConfigurationError`` (typo guard)."""
    from strawberry import relay

    with pytest.raises(ConfigurationError, match="unknown strategy"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = "modle"


def test_meta_globalid_strategy_non_relay_type_raises():
    """``Meta.globalid_strategy`` on a type whose ``interfaces`` omits ``relay.Node`` raises."""
    with pytest.raises(ConfigurationError, match="relay.Node"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                globalid_strategy = "model"


def test_meta_globalid_strategy_wrong_type_raises():
    """A non-string, non-callable value (e.g. ``42``) raises ``ConfigurationError``."""
    from strawberry import relay

    with pytest.raises(ConfigurationError, match="must be one of"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = 42


def test_meta_globalid_strategy_callable_accepted_and_stored():
    """A well-formed sync four-arg encoder validates and is stored on the definition."""
    from strawberry import relay

    def encode(
        type_cls,
        model,
        root,
        info,
    ):
        return "custom"

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            globalid_strategy = encode

    definition = CategoryType.__django_strawberry_definition__
    assert definition.globalid_strategy is encode


def test_meta_globalid_strategy_callable_wrong_arity_raises():
    """A wrong-arity encoder is rejected at type creation (the ``inspect.signature`` check)."""
    from strawberry import relay

    def encode(type_cls, model):
        return "custom"

    with pytest.raises(ConfigurationError, match=r"\(type_cls, model, root, info\)"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = encode


def test_meta_globalid_strategy_async_callable_raises():
    """An ``async def`` encoder is rejected at type creation (the sync-ness check)."""
    from strawberry import relay

    async def encode(
        type_cls,
        model,
        root,
        info,
    ):
        return "custom"

    with pytest.raises(ConfigurationError, match="must be sync"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = encode


def test_meta_globalid_strategy_async_callable_object_raises():
    """A callable *instance* whose ``__call__`` is ``async def`` is rejected too.

    ``inspect.iscoroutinefunction`` returns ``False`` for the instance itself, so
    without the ``__call__`` arm of the sync-ness check this object would survive
    validation and only blow up at first encode (a coroutine return + an unawaited
    -coroutine warning) instead of failing loud at type creation
    (``docs/feedback.md`` P2).
    """
    from strawberry import relay

    class Encoder:
        async def __call__(
            self,
            type_cls,
            model,
            root,
            info,
        ):
            return "custom.label"

    with pytest.raises(ConfigurationError, match="must be sync"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = Encoder()


def test_meta_globalid_strategy_partial_wrapped_async_callable_raises():
    """A ``functools.partial`` around an async callable instance is rejected too.

    ``inspect.iscoroutinefunction`` only unwraps a partial whose ``.func`` is an
    ``async def`` function - NOT a partial around an async callable *instance*, so
    both the partial and its ``__call__`` read as sync. The validator unwraps
    ``partial.func`` before the sync-ness check, so it fails loud at type creation
    instead of leaking a coroutine at the first encode (``docs/feedback.md`` P2).
    """
    from strawberry import relay

    class Encoder:
        async def __call__(
            self,
            type_cls,
            model,
            root,
            info,
        ):
            return "custom.label"

    with pytest.raises(ConfigurationError, match="must be sync"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = functools.partial(Encoder())


def test_meta_globalid_strategy_stored_on_definition():
    """The normalized string strategy lands on ``definition.globalid_strategy``."""
    from strawberry import relay

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            globalid_strategy = "model"

    definition = CategoryType.__django_strawberry_definition__
    assert definition.globalid_strategy == "model"


def test_meta_globalid_strategy_absent_leaves_definition_none():
    """A Relay-Node type without the key leaves the raw slot at its ``None`` default."""
    from strawberry import relay

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)

    definition = CategoryType.__django_strawberry_definition__
    assert definition.globalid_strategy is None


def test_resolve_globalid_strategy_precedence(settings):
    """``_resolve_globalid_strategy`` applies Meta -> setting -> ``"model"`` default.

    Also pins the unknown-setting failure: the setting path validates through
    the same rule as the ``Meta`` path, raising ``ConfigurationError`` whose
    message names ``RELAY_GLOBALID_STRATEGY`` (the setting framing, distinct from
    the type-named ``Meta`` framing).
    """
    from strawberry import relay

    from django_strawberry_framework.types.relay import _resolve_globalid_strategy

    class MetaWinsType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    class NoMetaType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

    meta_def = MetaWinsType.__django_strawberry_definition__
    no_meta_def = NoMetaType.__django_strawberry_definition__

    # Tier 1: Meta override beats the setting.
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RELAY_GLOBALID_STRATEGY": "type+model"}
    assert _resolve_globalid_strategy(meta_def) == "type"

    # Tier 2: setting beats the package default.
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RELAY_GLOBALID_STRATEGY": "type"}
    assert _resolve_globalid_strategy(no_meta_def) == "type"

    # Tier 3: no Meta + no setting -> the "model" package default.
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {}
    assert _resolve_globalid_strategy(no_meta_def) == "model"

    # Unknown setting value -> ConfigurationError naming the setting.
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RELAY_GLOBALID_STRATEGY": "nonsense"}
    with pytest.raises(ConfigurationError, match="RELAY_GLOBALID_STRATEGY"):
        _resolve_globalid_strategy(no_meta_def)


def test_meta_rejects_unknown_key():
    """Typo guard: keys outside the allowed/deferred sets raise."""
    with pytest.raises(ConfigurationError, match="Unknown Meta keys"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                bogus_key = "value"


def test_meta_fields_unknown_name_raises():
    """A typo in ``Meta.fields`` raises ``ConfigurationError`` rather than silently dropping."""
    with pytest.raises(ConfigurationError, match="unknown fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "nmae")  # typo: "nmae" instead of "name"


def test_meta_fields_unknown_name_includes_model_and_available():
    """The error names the model and lists available fields so the typo is obvious."""
    with pytest.raises(ConfigurationError) as exc_info:

        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("nope",)

    msg = str(exc_info.value)
    assert "Category.Meta.fields" in msg
    assert "nope" in msg
    # Mentions some real fields so the consumer sees the available surface.
    assert "name" in msg


def test_meta_exclude_unknown_name_raises():
    """A typo in ``Meta.exclude`` raises rather than silently keeping the field."""
    with pytest.raises(ConfigurationError, match="unknown fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                exclude = ("descriptoin",)  # typo


def test_meta_optimizer_hints_for_excluded_field_raises():
    """A hint for a real Django field that is *excluded* from the type raises.

    Pins the Medium fix from ``rev-types__base.md``: without this check
    the consumer's optimization intent is silently dead because the
    walker never visits an excluded field.
    """
    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                optimizer_hints = {"items": OptimizerHint.prefetch_related()}


def test_meta_optimizer_hints_for_selected_scalar_field_raises():
    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                optimizer_hints = {"name": OptimizerHint.SKIP}


def test_meta_optimizer_hints_with_empty_field_selection_raises_configuration_error():
    """``optimizer_hints`` on an exclude-all selection raises ``ConfigurationError``, not ``IndexError``.

    Earlier shapes inferred the model from ``fields[0].model``; when
    ``Meta.exclude`` covered every concrete + relation field the resulting
    empty ``fields`` tuple ``IndexError``'d before the consumer could see a
    typed error. The fix threads ``meta.model`` through explicitly so the
    selected-relation gate fires with a normal ``ConfigurationError``.
    """
    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                exclude = (
                    "id",
                    "name",
                    "description",
                    "is_private",
                    "created_date",
                    "updated_date",
                    "items",
                )
                optimizer_hints = {"items": OptimizerHint.prefetch_related()}


# ---------------------------------------------------------------------------
# Slice 2 - Meta.primary recognition
# ---------------------------------------------------------------------------


def test_meta_primary_true_registers_type_as_primary():
    """``Meta.primary = True`` makes ``registry.primary_for(model)`` return the type."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.primary_for(Item) is ItemType


def test_meta_primary_false_does_not_register_primary():
    """An explicit ``Meta.primary = False`` is treated identically to absent."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = False

    assert registry.primary_for(Item) is None
    # Single-type backward-compat: ``get()`` still returns the lone type even
    # without an explicit primary flag (Slice 1 Decision 4).
    assert registry.get(Item) is ItemType


def test_meta_primary_absent_does_not_register_primary():
    """No ``Meta.primary`` key is the default ``False`` path."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.primary_for(Item) is None
    assert registry.get(Item) is ItemType


@pytest.mark.parametrize(
    "bad",
    [
        "yes",
        1,
        0,
        [],
        None,
        1.0,
    ],
)
def test_meta_primary_non_bool_raises_configuration_error(bad):
    """``Meta.primary`` must be a ``bool``; any other shape raises.

    ``isinstance(1, bool)`` is ``False`` (``bool`` is a subclass of ``int``,
    not the other way around) so the guard correctly rejects the ``1``/``0``
    integer trap that would otherwise pass a duck-typed bool check.
    """
    with pytest.raises(ConfigurationError, match="must be a bool"):

        class T(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")
                primary = bad


def test_meta_primary_propagates_to_definition():
    """The ``primary`` flag is stored on ``DjangoTypeDefinition`` for introspection."""

    class ItemTypePrimary(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.get_definition(ItemTypePrimary).primary is True


def test_meta_primary_absent_definition_primary_defaults_false():
    """Absent ``Meta.primary`` lands ``False`` on the dataclass default."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get_definition(ItemType).primary is False


def test_two_types_same_model_one_primary_both_register_successfully():
    """Two ``DjangoType`` subclasses on one model, exactly one primary, both register."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.types_for(Item) == (ItemType, AdminItemType)
    assert registry.primary_for(Item) is AdminItemType
    # ``get()`` returns the declared primary even though ``ItemType`` registered
    # first (Slice 1 Decision 4: primary wins over registration order).
    assert registry.get(Item) is AdminItemType


def test_two_primary_types_same_model_raises():
    """Two ``Meta.primary = True`` declarations for the same model raise at class creation."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    with pytest.raises(
        ConfigurationError,
        match=r"Cannot register AdminItemType as primary for Item;.*ItemType is already the primary type",
    ):

        class AdminItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")
                primary = True


# ---------------------------------------------------------------------------
# Slice 2 - scalar synthesis
# ---------------------------------------------------------------------------


def test_scalar_mapping_against_category_textfields_booleanfields_datetimefields():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    a = CategoryType.__annotations__
    assert a["id"] is int
    assert a["name"] is str
    assert a["description"] is str
    assert a["is_private"] is bool
    assert a["created_date"] is datetime.datetime
    assert a["updated_date"] is datetime.datetime


def test_meta_fields_explicit_list_filters_concrete_fields():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert set(CategoryType.__annotations__) == {"id", "name"}


def test_meta_exclude_filters_concrete_fields():
    """Excluding scalars + reverse rels yields a clean scalar-only annotation set."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            # Exclude scalars under test plus the reverse rels (Item /
            # Property are unregistered in this test, so leaving them
            # selected would trip ``convert_relation``).
            exclude = (
                "description",
                "updated_date",
                "items",
                "properties",
            )

    a = CategoryType.__annotations__
    assert "description" not in a
    assert "updated_date" not in a
    assert {
        "id",
        "name",
        "is_private",
        "created_date",
    } <= set(a)


# ---------------------------------------------------------------------------
# Slice 2 - Strawberry finalization
# ---------------------------------------------------------------------------


def test_category_type_is_a_strawberry_type():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    finalize_django_types()
    assert hasattr(CategoryType, "__strawberry_definition__")
    assert CategoryType.__strawberry_definition__.name == "CategoryType"


def test_meta_name_overrides_graphql_type_name():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            name = "Category"

    finalize_django_types()

    assert CategoryType.__strawberry_definition__.name == "Category"


def test_meta_description_threads_through_to_strawberry():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            description = "A Faker provider."

    finalize_django_types()

    assert CategoryType.__strawberry_definition__.description == "A Faker provider."


# ---------------------------------------------------------------------------
# Slice 2 - default get_queryset is identity
# ---------------------------------------------------------------------------


def test_get_queryset_default_returns_input_unchanged():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    qs = Category.objects.all()
    assert CategoryType.get_queryset(qs, info=None) is qs


def test_has_custom_get_queryset_false_when_using_default():
    """A subclass that does not override ``get_queryset`` reports False."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert CategoryType._is_default_get_queryset is True
    assert CategoryType.has_custom_get_queryset() is False


def test_has_custom_get_queryset_true_when_overridden():
    """A subclass that overrides ``get_queryset`` flips the sentinel and reports True."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    assert CategoryType._is_default_get_queryset is False
    assert CategoryType.has_custom_get_queryset() is True


def test_has_custom_get_queryset_inherits_through_intermediate_base():
    """A subclass without its own ``get_queryset`` whose parent overrides one still reports True.

    The sentinel sits on the class itself - Python's normal attribute
    lookup walks the MRO, so a child that does not redeclare
    ``get_queryset`` inherits the parent's ``False`` flag through the
    class hierarchy without us writing any MRO-walking code.
    """

    class BaseCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    # Drop the registry collision so we can subclass cleanly.
    registry.clear()

    class ChildCategoryType(BaseCategoryType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert ChildCategoryType.has_custom_get_queryset() is True


def test_has_custom_get_queryset_inherits_through_abstract_base_without_meta():
    """A concrete subclass inherits override-detection from an abstract base that has no ``Meta``.

    The abstract-shared-base pattern is documented as supported - the
    ``__init_subclass__`` ``meta is None`` early return notes
    "intermediate abstract subclasses without Meta are allowed". For
    that pattern to work end-to-end with the optimizer's
    downgrade-to-Prefetch rule, the sentinel flip must run regardless
    of whether the abstract base declares its own ``Meta``. Used to be
    a P1 bug: the flip sat after the ``meta is None`` early return, so
    an abstract base that overrode ``get_queryset`` without Meta never
    flipped the flag, and concrete subclasses inheriting from it
    silently reported ``has_custom_get_queryset() is False``.
    """

    class TenantScopedType(DjangoType):
        """Abstract base - no Meta, but defines ``get_queryset``."""

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    # The abstract base flipped its own sentinel even without Meta.
    assert TenantScopedType._is_default_get_queryset is False

    class CategoryType(TenantScopedType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    # Concrete subclass does not redefine ``get_queryset`` itself, but
    # inherits the flipped sentinel via normal attribute lookup.
    assert "get_queryset" not in CategoryType.__dict__
    assert CategoryType.has_custom_get_queryset() is True


# ---------------------------------------------------------------------------
# Slice 2 - convert_scalar direct unit coverage
# ---------------------------------------------------------------------------


def test_convert_scalar_raises_on_unsupported_field_type(monkeypatch):
    """Unsupported field types fail loudly with a message naming the field."""
    monkeypatch.delitem(converters.SCALAR_MAP, models.TextField)
    name_field = Category._meta.get_field("name")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(name_field, "CategoryType")


# ---------------------------------------------------------------------------
# Slice 3 - relation conversion via _build_annotations
# ---------------------------------------------------------------------------


def test_relation_fk_to_target_djangotype():
    """Forward FK on Item maps to the registered ``CategoryType`` post-finalize."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    class ItemType(DjangoType):
        class Meta:
            model = Item
            # Skip ``entries`` reverse rel - Entry is unregistered in this test.
            fields = ("id", "name", "category")

    finalize_django_types()
    assert ItemType.__annotations__["category"] is CategoryType


def test_relation_reverse_fk_returns_list():
    """Reverse FK on Category maps to ``list[ItemType]`` and ``list[PropertyType]``."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = (
                "id",
                "name",
                "items",
                "properties",
            )

    finalize_django_types()
    a = CategoryType.__annotations__
    assert a["items"] == list[ItemType]
    assert a["properties"] == list[PropertyType]


def test_relation_meta_default_when_neither_fields_nor_exclude_set():
    """Omitting ``fields``/``exclude`` defaults to ``__all__`` and includes relations."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category

    finalize_django_types()
    a = CategoryType.__annotations__
    assert {
        "id",
        "name",
        "items",
        "properties",
    } <= set(a)
    assert a["items"] == list[ItemType]
    assert a["properties"] == list[PropertyType]


def test_relation_unregistered_target_raises():
    """Referencing an unregistered relation target raises during finalization."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    assert ItemType.__annotations__["category"] is PendingRelationAnnotation
    assert "finalize_django_types()" in repr(PendingRelationAnnotation)
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Cannot finalize Django types" in msg
    assert "Item.category -> Category" in msg
    assert "no registered DjangoType" in msg


def test_relation_full_chain_when_all_targets_registered():
    """Every fakeshop relation resolves cleanly when types are declared in order."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            # Exclude reverse rels; Item / Property come next.
            fields = CATEGORY_SCALAR_FIELDS

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            # category FK + scalars; entries reverse rel waits for EntryType.
            fields = ("id", "name", "category")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = (
                "id",
                "value",
                "property",
                "item",
            )

    finalize_django_types()
    assert PropertyType.__annotations__["category"] is CategoryType
    assert ItemType.__annotations__["category"] is CategoryType
    assert EntryType.__annotations__["property"] is PropertyType
    assert EntryType.__annotations__["item"] is ItemType


def test_resolved_relation_annotation_nullable_fk_widens_to_optional(monkeypatch):
    """Nullable forward FK widens to ``T | None``.

    No fakeshop FK declares ``null=True``, so monkeypatch the Item.category
    field for the duration of this test. ``resolved_relation_annotation``
    reads ``field.null`` via ``FieldMeta.from_django_field``; the widening
    branch is exercised without the rest of the pipeline.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    item_category = Item._meta.get_field("category")
    monkeypatch.setattr(item_category, "null", True)
    annotation = resolved_relation_annotation(item_category, CategoryType)
    assert annotation == (CategoryType | None)


# ---------------------------------------------------------------------------
# spec-029 Slice 3 - Meta.nullable_overrides / Meta.required_overrides
#
# Synthetic ``managed=False`` models give clean control over per-field
# ``null`` (and a relation field) for the override-applies and validation
# cases. ``text_value`` is a non-null column, ``note`` a nullable one (the
# two directions the spec test plan names); ``partner`` is a relation field
# for the scalar-only-scope reject. ``_unique_override_app_label`` namespaces
# each synthetic model so Django's app registry does not collide across tests.
# ---------------------------------------------------------------------------

_override_app_label_counter = itertools.count(1)


def _unique_override_app_label() -> str:
    """Return a unique ``app_label`` per call for synthetic override models."""
    return f"test_overrides__{next(_override_app_label_counter)}"


def _make_override_model():
    """Return a synthetic model with a non-null + a nullable scalar and a relation."""

    class _OverrideOwner(models.Model):
        text_value = models.TextField()
        note = models.TextField(null=True)
        partner = models.ForeignKey(
            "self",
            null=True,
            on_delete=models.SET_NULL,
            related_name="+",
        )

        class Meta:
            managed = False
            app_label = _unique_override_app_label()

    return _OverrideOwner


def _make_override_type(model, *, namespace=None, **meta_attrs):
    """Build an ``OverrideType`` subclass for ``model`` with the given Meta attrs.

    Uses ``type(...)`` construction (mirroring ``test_meta_rejects_each_deferred_key``)
    so the synthetic ``model`` local is passed by value rather than referenced from
    a nested ``class Meta`` body (class bodies do not close over function locals).
    ``namespace`` carries consumer-authored annotations / assignments onto the type.
    """
    meta_cls = type("Meta", (), {"model": model, **meta_attrs})
    return type("OverrideType", (DjangoType,), {"Meta": meta_cls, **(namespace or {})})


def test_nullable_overrides_in_allowed_meta_keys():
    """Both override keys are net-new ALLOWED keys, NOT deferred (Decision 6)."""
    from django_strawberry_framework.types.base import ALLOWED_META_KEYS, DEFERRED_META_KEYS

    assert "nullable_overrides" in ALLOWED_META_KEYS
    assert "required_overrides" in ALLOWED_META_KEYS
    assert "nullable_overrides" not in DEFERRED_META_KEYS
    assert "required_overrides" not in DEFERRED_META_KEYS


def test_nullable_override_flips_annotation():
    """``nullable_overrides`` widens a non-null column; ``required_overrides`` narrows a nullable one."""
    override_type = _make_override_type(
        _make_override_model(),
        fields=("id", "text_value", "note"),
        nullable_overrides=("text_value",),
        required_overrides=("note",),
    )

    # text_value is NOT NULL natively (str); the override widens it to str | None.
    assert override_type.__annotations__["text_value"] == (str | None)
    # note is null=True natively (str | None); the override narrows it to bare str.
    assert override_type.__annotations__["note"] is str


def test_override_unknown_field_raises():
    """A name not on the model raises ``ConfigurationError`` (unknown-field path)."""
    with pytest.raises(ConfigurationError, match="unknown fields"):
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            nullable_overrides=("does_not_exist",),
        )


def test_override_excluded_field_raises():
    """A name excluded from the selected set raises - distinct from unknown (Decision 8 rule 2)."""
    with pytest.raises(ConfigurationError, match="not in the selected set"):
        # ``note`` exists on the model but is excluded from the type.
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            required_overrides=("note",),
        )


def test_override_consumer_authored_field_raises():
    """A name with a consumer annotation raises (the annotation already controls nullability)."""
    with pytest.raises(ConfigurationError, match="consumer-authored"):
        _make_override_type(
            _make_override_model(),
            namespace={"__annotations__": {"text_value": int}},
            fields=("id", "text_value"),
            nullable_overrides=("text_value",),
        )


def test_override_relation_field_raises():
    """A relation field name raises - scalar-only scope (Decision 10)."""
    with pytest.raises(ConfigurationError, match="relation field"):
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value", "partner"),
            nullable_overrides=("partner",),
        )


def test_override_relay_suppressed_pk_raises():
    """Naming the Relay-Node-suppressed pk in an override set raises (Decision 8 rule e)."""
    from strawberry import relay

    with pytest.raises(ConfigurationError, match="Relay-Node-suppressed pk"):

        class CategoryNodeOverride(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)
                required_overrides = ("id",)


def test_override_both_sets_collision_raises():
    """The same name in both sets raises at the shape stage, naming the field."""
    with pytest.raises(ConfigurationError, match="both"):
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            nullable_overrides=("text_value",),
            required_overrides=("text_value",),
        )


def test_override_non_sequence_raises():
    """A bare-string override is rejected by the non-string-sequence shape guard."""
    with pytest.raises(ConfigurationError, match="non-string sequence"):
        # A bare string is an iterable of characters, not a field-name list.
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            nullable_overrides="text_value",
        )


def test_override_redundant_is_no_op():
    """A redundant override (already in the target direction) is accepted, not raised.

    ``nullable_overrides`` on an already-nullable column and
    ``required_overrides`` on an already-non-null column are legitimate
    (if redundant) declarations - pinned as a passing case (Edge cases).
    """
    # note is already nullable; text_value is already non-null.
    override_type = _make_override_type(
        _make_override_model(),
        fields=("id", "text_value", "note"),
        nullable_overrides=("note",),
        required_overrides=("text_value",),
    )

    assert override_type.__annotations__["note"] == (str | None)
    assert override_type.__annotations__["text_value"] is str
