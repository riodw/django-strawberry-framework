"""Public Relay helper tests for global_id_for and decode_global_id.

Mirrors ``django_strawberry_framework/testing/relay.py`` per the
``docs/TREE.md`` one-to-one rule (``docs/spec-032-full_relay-0_0_9.md``
Decision 11 - no card conflict for this pair).
"""

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types, strawberry_config
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import relay as testing_relay
from django_strawberry_framework.testing.relay import decode_global_id, global_id_for
from django_strawberry_framework.types import finalizer as types_finalizer
from django_strawberry_framework.types import relay as types_relay


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _make_node_type(
    name,
    *,
    model=Category,
    strategy=None,
    interfaces=(relay.Node,),
    primary=False,
):
    """Build a (by default Relay-Node-shaped) ``DjangoType`` over ``model``."""
    meta_attrs = {"model": model, "fields": ("id", "name"), "name": name}
    if interfaces:
        meta_attrs["interfaces"] = interfaces
    if strategy is not None:
        meta_attrs["globalid_strategy"] = strategy
    if primary:
        meta_attrs["primary"] = True
    return type(name, (DjangoType,), {"Meta": type("Meta", (), meta_attrs)})


def _schema_with_row(node_type, model) -> strawberry.Schema:
    """Finalize, then build a schema exposing ``row`` -> the lowest-pk instance."""

    def row() -> node_type:
        return model._default_manager.order_by("pk").first()

    query_cls = strawberry.type(type("Query", (), {"row": strawberry.field(resolver=row)}))
    finalize_django_types()
    return strawberry.Schema(query=query_cls, config=strawberry_config())


def _emitted_typename(type_cls):
    """Return the GlobalID type-name slot the installed live closure emits.

    Framework closures for ``model`` / ``type+model`` ignore ``root`` / ``info``
    content, so a synthetic root faithfully exercises the live emit path.
    """

    class _FakeRoot:
        pass

    _FakeRoot._meta = type_cls.__django_strawberry_definition__.model._meta
    _FakeRoot.id = "1"
    return type_cls.resolve_typename(_FakeRoot(), None)


_ROW_ID_QUERY = "{ row { id } }"


# ---------------------------------------------------------------------------
# global_id_for - the three deterministically encodable strategies
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_global_id_for_model_strategy():
    """Default (``model``) strategy: helper output equals the live emitted id."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with_row(category_node, Category)
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(_ROW_ID_QUERY)
    assert result.errors is None
    live_id = result.data["row"]["id"]
    assert live_id == global_id_for(category_node, row.pk)
    decoded = relay.GlobalID.from_id(live_id)
    assert decoded.type_name == "products.category"
    assert decoded.node_id == str(row.pk)


@pytest.mark.django_db
def test_global_id_for_type_strategy():
    """``type`` strategy: live id equals helper output; payload is the Meta name."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode", strategy="type")
    schema = _schema_with_row(category_node, Category)
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(_ROW_ID_QUERY)
    assert result.errors is None
    live_id = result.data["row"]["id"]
    assert live_id == global_id_for(category_node, row.pk)
    # The payload slot is the graphql_type_name (the honored ``Meta.name``).
    assert relay.GlobalID.from_id(live_id).type_name == "CategoryNode"


@pytest.mark.django_db
def test_global_id_for_type_plus_model_strategy():
    """``type+model`` strategy: live id equals helper output; payload is the model label."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode", strategy="type+model")
    schema = _schema_with_row(category_node, Category)
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(_ROW_ID_QUERY)
    assert result.errors is None
    live_id = result.data["row"]["id"]
    assert live_id == global_id_for(category_node, row.pk)
    assert relay.GlobalID.from_id(live_id).type_name == "products.category"


# ---------------------------------------------------------------------------
# global_id_for - the four raise branches
# ---------------------------------------------------------------------------


def _callable_strategy_type():
    """A Relay type whose ``Meta.globalid_strategy`` is a consumer callable."""

    def _encoder(
        type_cls,
        model,
        root,
        info,
    ):
        return "products.category"

    return _make_node_type("CategoryNode", strategy=_encoder)


def _custom_override_type():
    """A Relay type with a consumer ``resolve_typename`` override (stamped ``custom``)."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_typename(cls, root, info):
            return "ConsumerOwned"

    return CategoryNode


@pytest.mark.parametrize(
    ("build_type", "expected_classification"),
    [(_callable_strategy_type, "callable"), (_custom_override_type, "custom")],
    ids=["callable", "custom"],
)
def test_global_id_for_callable_or_custom_raises(build_type, expected_classification):
    """``callable`` / ``custom`` encoders need a live (root, info) pair -> raise."""
    type_cls = build_type()
    finalize_django_types()
    definition = type_cls.__django_strawberry_definition__
    assert definition.effective_globalid_strategy == expected_classification
    with pytest.raises(ConfigurationError) as excinfo:
        global_id_for(type_cls, 1)
    message = str(excinfo.value)
    assert "global_id_for" in message
    assert "(root, info)" in message
    assert repr(expected_classification) in message


def test_global_id_for_unfinalized_raises():
    """A Relay-shaped type defined but never finalized raises finalize-first."""
    type_cls = _make_node_type("CategoryNode")
    with pytest.raises(ConfigurationError) as excinfo:
        global_id_for(type_cls, 1)
    message = str(excinfo.value)
    assert "CategoryNode" in message
    assert "finalize_django_types()" in message


def test_global_id_for_non_node_raises():
    """A finalized non-Relay DjangoType raises the Relay gate; a plain class is rejected too."""
    type_cls = _make_node_type("CategoryType", interfaces=())
    finalize_django_types()
    assert type_cls.__django_strawberry_definition__.finalized is True
    with pytest.raises(ConfigurationError) as excinfo:
        global_id_for(type_cls, 1)
    message = str(excinfo.value)
    assert "CategoryType" in message
    assert "requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces`" in message
    # Step-1a branch: an input that is not a DjangoType subclass at all.
    with pytest.raises(ConfigurationError) as excinfo:
        global_id_for(object, 1)
    assert "not a registered DjangoType subclass" in str(excinfo.value)


def test_global_id_for_strategy_stamped_but_unfinalized_raises(monkeypatch):
    """A Phase-3 failure leaves the strategy stamped but ``finalized=False`` -> raise.

    ``install_globalid_typename_resolver`` stamps ``effective_globalid_strategy``
    in Phase 2.5, BEFORE Phase 3 flips ``finalized``. If Phase 3
    (``strawberry.type``) raises, the type carries a non-None strategy yet is
    not finalized; ``global_id_for`` must gate on ``finalized`` and still raise
    the finalize-first error rather than mint an id (spec-032 feedback P2).
    """
    category_node = _make_node_type("CategoryNode")

    def _boom(*args, **kwargs):
        raise RuntimeError("phase-3 boom")

    monkeypatch.setattr(types_finalizer.strawberry, "type", _boom)
    with pytest.raises(RuntimeError, match="phase-3 boom"):
        finalize_django_types()

    definition = category_node.__django_strawberry_definition__
    # The stamp landed in Phase 2.5; Phase 3 never completed.
    assert definition.effective_globalid_strategy == "model"
    assert definition.finalized is False

    with pytest.raises(ConfigurationError) as excinfo:
        global_id_for(category_node, 1)
    message = str(excinfo.value)
    assert "CategoryNode" in message
    assert "finalize_django_types()" in message


# ---------------------------------------------------------------------------
# decode_global_id re-export + the round-trip / asymmetry contract
# ---------------------------------------------------------------------------


def test_public_decode_round_trip_primary_and_type_name():
    """Round-trip identity for a lone model-label type and a ``type``-strategy type."""
    model_type = _make_node_type("CategoryNode")
    type_type = _make_node_type("ItemNode", model=Item, strategy="type")
    finalize_django_types()
    assert decode_global_id(global_id_for(model_type, 7)) == (model_type, "7")
    assert decode_global_id(global_id_for(type_type, 7)) == (type_type, "7")
    # The public name IS the internal dispatch (re-export, not a wrapper).
    assert testing_relay.decode_global_id is types_relay.decode_global_id


def test_secondary_model_label_emitter_decodes_to_primary():
    """A secondary mints the model-label payload it emits; decode routes to the primary."""
    primary = _make_node_type("PrimaryItem", model=Item, primary=True)
    secondary = _make_node_type("SecondaryItem", model=Item)
    finalize_django_types()
    minted = global_id_for(secondary, 3)
    # The helper mints exactly the payload the secondary's live closure emits.
    assert relay.GlobalID.from_id(minted).type_name == "products.item"
    assert _emitted_typename(secondary) == "products.item"
    # ... and decode routes the model-label payload to the model's PRIMARY
    # via registry.get(model) - the documented asymmetry (Revision 2 P2).
    assert decode_global_id(minted) == (primary, "3")
