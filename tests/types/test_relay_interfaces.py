"""Tests for the 0.0.5 Relay interfaces slice.

Slice 1 covers validation and storage: ``_validate_interfaces`` normalizes
and validates ``Meta.interfaces``, and the normalized tuple is threaded
through to ``DjangoTypeDefinition.interfaces``. End-to-end ``_validate_meta``
coverage with ``Meta.interfaces`` declared lands in Slice 5 once the key is
promoted out of ``DEFERRED_META_KEYS``; until then the deferred-key check
short-circuits before the interface validator runs, so Slice 1 calls
``_validate_interfaces`` directly.
"""

import pytest
import strawberry
from apps.products.models import Category
from strawberry import relay

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.base import _validate_interfaces
from django_strawberry_framework.types.definition import DjangoTypeDefinition


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _meta(**attrs):
    """Build a throw-away ``Meta`` class with ``model=Category`` plus extras."""
    attrs.setdefault("model", Category)
    return type("Meta", (), attrs)


# ---------------------------------------------------------------------------
# Slice 1 — validation + storage
# ---------------------------------------------------------------------------


def test_meta_interfaces_accepted():
    """``interfaces = (relay.Node,)`` is normalized to ``(relay.Node,)``."""
    meta = _meta(interfaces=(relay.Node,))
    assert _validate_interfaces(meta) == (relay.Node,)


@pytest.mark.parametrize(
    "raw",
    [
        relay.Node,
        (relay.Node,),
        # Missing-comma spec spelling: Python evaluates ``(relay.Node)`` to
        # the bare class identity (not a tuple), so this case is identical
        # to the first; included verbatim per spec lines 192-193 / 323.
        (relay.Node),
    ],
)
def test_meta_interfaces_accepts_single_interface_class(raw):
    """A single class, a one-tuple, and the missing-comma spelling all normalize."""
    meta = _meta(interfaces=raw)
    assert _validate_interfaces(meta) == (relay.Node,)


@pytest.mark.parametrize(
    "raw",
    [
        {relay.Node},
        (x for x in (relay.Node,)),
        {relay.Node: None},
        42,
    ],
)
def test_meta_interfaces_rejects_non_sequence(raw):
    meta = _meta(interfaces=raw)
    with pytest.raises(ConfigurationError, match="must be a tuple/list"):
        _validate_interfaces(meta)


def test_meta_interfaces_rejects_string_entries():
    """Both top-level strings and tuple-of-string entries are rejected."""
    meta_top = _meta(interfaces="Node")
    with pytest.raises(ConfigurationError, match="must be a tuple/list"):
        _validate_interfaces(meta_top)
    meta_entry = _meta(interfaces=("Node",))
    with pytest.raises(ConfigurationError, match="must contain interface classes"):
        _validate_interfaces(meta_entry)


def test_meta_interfaces_rejects_non_interface_classes():
    """Plain classes, builtin types, and ``@strawberry.type``-decorated classes are rejected."""

    @strawberry.type
    class NotAnInterface:
        name: str

    for entry in (object, int, NotAnInterface):
        meta = _meta(interfaces=(entry,))
        with pytest.raises(ConfigurationError, match="not a Strawberry interface"):
            _validate_interfaces(meta)


@pytest.mark.parametrize(
    "entry",
    [
        object(),
        42,
    ],
)
def test_meta_interfaces_rejects_non_class_entries(entry):
    """Non-class non-string entries (instances, ints) raise the must-contain-interface-classes error."""
    meta = _meta(interfaces=(entry,))
    with pytest.raises(ConfigurationError, match="must contain interface classes"):
        _validate_interfaces(meta)


def test_meta_interfaces_rejects_djangotype_self_reference():
    """``DjangoType`` itself and any subclass are rejected as interface entries."""
    meta_self = _meta(interfaces=(DjangoType,))
    with pytest.raises(ConfigurationError, match="may not contain DjangoType"):
        _validate_interfaces(meta_self)

    class SomeType(DjangoType):
        pass

    meta_sub = _meta(interfaces=(SomeType,))
    with pytest.raises(ConfigurationError, match="may not contain DjangoType"):
        _validate_interfaces(meta_sub)


def test_meta_interfaces_rejects_duplicates():
    meta = _meta(interfaces=(relay.Node, relay.Node))
    with pytest.raises(ConfigurationError, match="duplicate entries"):
        _validate_interfaces(meta)


def test_meta_interfaces_empty_tuple_treated_as_unset():
    """An empty tuple and an absent key both produce ``()`` (bit-for-bit identical)."""
    assert _validate_interfaces(_meta(interfaces=())) == ()
    assert _validate_interfaces(_meta()) == ()


def test_meta_interfaces_stored_on_definition():
    """The normalized tuple flows through to ``DjangoTypeDefinition.interfaces``."""
    meta = _meta(interfaces=(relay.Node,))
    normalized = _validate_interfaces(meta)
    definition = DjangoTypeDefinition(
        origin=object,
        model=Category,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
        interfaces=normalized,
    )
    assert definition.interfaces == (relay.Node,)


def test_class_already_inherits_relay_node_directly():
    """``_validate_interfaces`` accepts a Meta whose host class already inherits ``relay.Node``.

    Slice 1's contract is only that the validator accepts the tuple
    without raising. The structural no-op (skip bases already in
    ``cls.__mro__``) is Slice 4's job; this test deliberately does not
    inspect ``__bases__``.
    """

    class _Host(DjangoType, relay.Node):
        pass

    meta = _meta(interfaces=(relay.Node,))
    assert _validate_interfaces(meta) == (relay.Node,)
    # Reference _Host so ruff does not flag the host class as unused; the
    # class existing in the test module is the assertion shape per the plan.
    assert relay.Node in _Host.__mro__


@pytest.mark.skip(
    reason="composite-pk check lives in Slice 4 / Phase 2.5; see spec line 431",
)
def test_relay_node_with_composite_pk_raises():
    """Reserved for Slice 4 to unskip and implement."""
