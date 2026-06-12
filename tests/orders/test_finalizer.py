"""Finalizer tests for order binding, Meta.orderset_class promotion, and orphan validation.

Covers:

- ``Meta.orderset_class`` promotion and validation (positive + negative + local-import).
- Four-subpass ordering: bind owners -> expand fields -> orphan-validate ->
  materialize. Subpass 1 completes across all owners before subpass 2 runs;
  subpass 3 runs BEFORE subpass 4 so an orphan failure leaves no partial
  state.
- First-bind model compatibility per spec-028 Revision 4 H2 (rejects orderset
  wired to unrelated owner model; message names all four entities).
- Multi-owner reuse: identical-target accepted; diverging-target rejected;
  idempotent re-bind of the same ``(orderset, definition)`` pair accepted.
- Per Decision 6 second paragraph the order side does NOT enforce the
  filter side's own-PK Relay-identity check.
- Unresolved ``RelatedOrder`` propagates as ``ConfigurationError`` with the
  underlying ``ImportError`` preserved on ``__cause__``; non-import
  expansion failure rewraps uniformly.
- Materialization writes input classes to ``orders.inputs.__dict__``;
  idempotent ``finalize_django_types()``.
- Partial-failure recovery (the partially-materialized state stays consistent
  with the ledger).
"""

from __future__ import annotations

import sys

import pytest
from apps.library.models import Book, Branch, Genre, Shelf
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import (
    OrderSet,
    RelatedOrder,
    _helper_referenced_ordersets,
    order_input_type,
)
from django_strawberry_framework.orders.factories import OrderArgumentsFactory
from django_strawberry_framework.orders.inputs import (
    INPUTS_MODULE_PATH,
    _field_specs,
    _materialized_names,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.finalizer import _bind_orderset_owner


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    _field_specs.clear()
    _helper_referenced_ordersets.clear()
    _materialized_names.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    yield
    registry.clear()
    _field_specs.clear()
    _helper_referenced_ordersets.clear()
    _materialized_names.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()


# ---------------------------------------------------------------------------
# Meta.orderset_class promotion + validation
# ---------------------------------------------------------------------------


def test_meta_orderset_class_accepts_order_set_subclass():
    """``Meta.orderset_class`` promotes onto the definition."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = BookOrder

    assert BookType.__django_strawberry_definition__.orderset_class is BookOrder


def test_meta_orderset_class_rejects_non_order_set():
    """A non-``OrderSet`` value at class-creation time raises ``ConfigurationError``."""

    class NotAnOrderSet:
        pass

    with pytest.raises(ConfigurationError) as exc_info:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                orderset_class = NotAnOrderSet

    msg = str(exc_info.value)
    assert "OrderSet subclass" in msg
    assert "NotAnOrderSet" in msg


def test_validate_orderset_class_uses_local_import():
    """``_validate_orderset_class`` keeps ``OrderSet`` out of ``types.base`` module globals.

    Pins the spec-028 N3-of-rev1 / DoD item 9 contract: the import lives
    inside the function so the ``types -> orders -> types`` module-load
    cycle stays inert.
    """
    import inspect

    import django_strawberry_framework.types.base as base_mod

    # Module-top namespace must NOT carry ``OrderSet`` -- the validator
    # imports it locally.
    assert "OrderSet" not in vars(base_mod)
    # The function source carries the local import line.
    src = inspect.getsource(base_mod._validate_orderset_class)
    assert "from ..orders.sets import OrderSet" in src


# ---------------------------------------------------------------------------
# Subpass 1 -> Subpass 2 ordering
# ---------------------------------------------------------------------------


def test_phase_2_5_binds_all_owners_before_expansion():
    """Every owner binds before any ``get_fields()`` runs (subpass 1 before subpass 2)."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    observations: list[bool] = []
    original_get_fields = ShelfOrder.get_fields.__func__

    @classmethod
    def instrumented_get_fields(cls):  # type: ignore[no-redef]
        observations.append(cls._owner_definition is not None)
        return original_get_fields(cls)

    ShelfOrder.get_fields = instrumented_get_fields  # type: ignore[method-assign]
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title", "shelf")
                orderset_class = BookOrder

        class ShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "code")
                orderset_class = ShelfOrder

        finalize_django_types()

        assert observations, "ShelfOrder.get_fields was never called"
        assert all(observations), (
            "ShelfOrder._owner_definition was unset during get_fields; "
            "subpass 1 did not complete across all owners before subpass 2 ran."
        )
    finally:
        del ShelfOrder.get_fields


# ---------------------------------------------------------------------------
# Subpass 2 -- ImportError / non-import rewrap
# ---------------------------------------------------------------------------


def test_phase_2_5_unresolved_related_order_raises_at_finalize():
    """``RelatedOrder("NonExistent")`` -> ``ConfigurationError`` with ``ImportError`` cause."""

    class BookOrder(OrderSet):
        shelf = RelatedOrder("NonExistentOrder", field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "Cannot finalize Django types: orderset" in msg
    assert "BookOrder" in msg
    assert "NonExistentOrder" in msg
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_phase_2_5_non_import_get_fields_failure_rewraps_as_configuration_error():
    """Non-``ImportError`` raised during ``get_fields()`` surfaces as ``ConfigurationError``."""

    def _broken_factory():
        raise ValueError("intentional factory failure")

    class BookOrder(OrderSet):
        broken = RelatedOrder(_broken_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookOrder" in msg
    assert "raised during expansion" in msg
    assert "ValueError" in msg
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_phase_2_5_configuration_error_during_expansion_propagates_by_identity():
    """A ``ConfigurationError`` from the subpass-2 expansion re-raises unchanged.

    The order twin of the filter side's ``finalizer.py`` ``except
    ConfigurationError: raise`` pass-through: if ``get_fields()`` / the
    ``related.orderset`` Layer-2 walk raises a ``ConfigurationError`` directly
    (as opposed to an ``ImportError`` or a generic ``Exception``), it must
    propagate by identity rather than being re-wrapped into a second
    ``ConfigurationError`` with the first on ``__cause__``.
    """
    sentinel = ConfigurationError("intentional config failure from related factory")

    def _config_error_factory():
        raise sentinel

    class BookOrder(OrderSet):
        broken = RelatedOrder(_config_error_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    # Propagated by identity -- NOT re-wrapped (no second ConfigurationError,
    # no ``raised during expansion`` prefix, the original is not on __cause__).
    assert exc_info.value is sentinel
    assert "raised during expansion" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# Subpass 3 -- orphan validation (runs BEFORE materialize)
# ---------------------------------------------------------------------------


def test_orphan_order_input_type_reference_raises_at_finalize():
    """A ``order_input_type(StandaloneOrder)`` without wiring raises."""

    class StandaloneOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    # Helper-reference the orderset without wiring it to any DjangoType.
    order_input_type(StandaloneOrder)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "StandaloneOrder" in msg
    assert "orderset_class = StandaloneOrder" in msg


def test_phase_2_5_orphan_check_runs_before_materialization():
    """Orphan failure leaves no partial state in the materialization ledgers."""

    class WiredOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class StandaloneOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    order_input_type(StandaloneOrder)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = WiredOrder

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    # No input class registered for either orderset; the wired one's
    # would-be input type stayed un-materialized because the orphan
    # check halted the pass before subpass 4 ran.
    wired_input_name = f"{WiredOrder.__name__}InputType"
    assert wired_input_name not in OrderArgumentsFactory.input_object_types
    assert wired_input_name not in _materialized_names


def test_phase_2_5_orphan_validation_lists_every_orphan_orderset():
    """Two orphans surface in one ``ConfigurationError`` with the multi-orphan lead-in."""

    class OrphanA(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class OrphanB(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    order_input_type(OrphanA)
    order_input_type(OrphanB)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "OrderSets referenced via order_input_type(...) but not wired to any DjangoType:" in msg
    assert "OrphanA" in msg
    assert "OrphanB" in msg
    assert "Add 'orderset_class = <Name>' to the relevant DjangoType's Meta" in msg
    # Sort key contract: offenders ordered by ``__module__.__qualname__``.
    idx_a = msg.index("OrphanA")
    idx_b = msg.index("OrphanB")
    assert idx_a < idx_b


# ---------------------------------------------------------------------------
# Subpass 4 -- materialize
# ---------------------------------------------------------------------------


def test_phase_2_5_subpass_4_materializes_input_classes_as_module_globals():
    """The materialize pass writes ``BookOrderInputType`` to the inputs module globals."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    finalize_django_types()

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookOrderInputType")
    assert "BookOrderInputType" in _materialized_names


# ---------------------------------------------------------------------------
# H2 of rev3 / Decision 6 -- first-bind model compatibility
# ---------------------------------------------------------------------------


def test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model():
    """Mandatory H2-of-rev3 test: rejects an orderset wired to an unrelated model.

    The error message names ALL FOUR entities: owner type, owner model,
    orderset class, and orderset model.
    """

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            orderset_class = BookOrder

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    # All four entity names appear in the message.
    assert "BookOrder" in msg
    assert "Book" in msg
    assert "BranchType" in msg
    assert "Branch" in msg


# ---------------------------------------------------------------------------
# Multi-owner reuse -- _bind_orderset_owner direct branches
# ---------------------------------------------------------------------------


def _owner_definition_stub(name, *, model=None, graphql_name=None):
    """Return a minimal owner-definition-shaped object for binding tests."""

    class _Stub:
        origin = type(name, (), {"__qualname__": name})
        graphql_type_name = graphql_name or name

        def __init__(self, resolver=None, *, m=model):
            self._resolver = resolver
            self.model = m

        def related_target_for(self, field_name):
            return self._resolver(field_name) if self._resolver is not None else None

    return _Stub


def test_bind_orderset_owner_idempotent_for_same_definition():
    """Re-binding the SAME ``(orderset, definition)`` pair is a no-op."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    Stub = _owner_definition_stub("OwnerType")
    definition = Stub()
    _bind_orderset_owner(ShelfOrder, definition)  # previous None -> bind
    _bind_orderset_owner(ShelfOrder, definition)  # previous IS definition -> no-op
    assert ShelfOrder._owner_definition is definition


def test_bind_orderset_owner_rejects_diverging_related_targets():
    """Two owners that resolve a shared ``RelatedOrder`` to different targets raise."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class _PrevTargetDefinition:
        origin = type("PrevTargetType", (), {"__qualname__": "PrevTargetType"})
        graphql_type_name = "PrevTargetType"

    class _NewTargetDefinition:
        origin = type("NewTargetType", (), {"__qualname__": "NewTargetType"})
        graphql_type_name = "NewTargetType"

    Stub = _owner_definition_stub("OwnerType")
    first = Stub(resolver=lambda f: (_PrevTargetDefinition, object()) if f == "shelf" else None)
    second = Stub(resolver=lambda f: (_NewTargetDefinition, object()) if f == "shelf" else None)
    _bind_orderset_owner(BookOrder, first)
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_orderset_owner(BookOrder, second)
    msg = str(exc_info.value)
    assert "diverging targets" in msg
    assert "shelf" in msg
    assert "PrevTargetType" in msg
    assert "NewTargetType" in msg


def test_bind_orderset_owner_continues_when_both_targets_unresolved():
    """A field neither owner can resolve is skipped (both-None continue)."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    Stub = _owner_definition_stub("OwnerType")
    first = Stub(resolver=lambda _f: None)
    second = Stub(resolver=lambda _f: None)
    _bind_orderset_owner(BookOrder, first)
    _bind_orderset_owner(BookOrder, second)
    # First binding preserved.
    assert BookOrder._owner_definition is first


def test_bind_orderset_owner_raises_when_one_owner_resolves_and_other_does_not():
    """A field resolved by one owner but not the other is a hard mismatch."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class _SomeTargetDefinition:
        origin = type("SomeTargetType", (), {"__qualname__": "SomeTargetType"})
        graphql_type_name = "SomeTargetType"

    Stub = _owner_definition_stub("OwnerType")
    first = Stub(resolver=lambda f: (_SomeTargetDefinition, object()) if f == "shelf" else None)
    second = Stub(resolver=lambda _f: None)
    _bind_orderset_owner(BookOrder, first)
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_orderset_owner(BookOrder, second)
    assert "diverging targets" in str(exc_info.value)


def test_bind_orderset_owner_does_not_check_axis_1_relay_identity():
    """Per spec-028 Decision 6 the order side does NOT enforce own-PK Relay identity.

    Two owners whose Relay-node-ness diverges still share one OrderSet
    successfully -- ``ORDER BY id`` uses the column, not the GraphQL ID
    type, so this is not an owner-dependent axis.
    """

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    # Both owners declare no ``RelatedOrder``s, so the Axis-2 walk is
    # vacuously satisfied. The filter-side equivalent test would FAIL here
    # because the filter side has Axis-1 (Relay-identity) check; the
    # order-side equivalent must succeed.
    class _RelayDefinition:
        origin = type("RelayShelfType", (), {"__qualname__": "RelayShelfType"})
        graphql_type_name = "RelayShelfType"
        model = Shelf

        @staticmethod
        def related_target_for(_field):
            return None

    class _PlainDefinition:
        origin = type("PlainShelfType", (), {"__qualname__": "PlainShelfType"})
        graphql_type_name = "PlainShelfType"
        model = Shelf

        @staticmethod
        def related_target_for(_field):
            return None

    _bind_orderset_owner(ShelfOrder, _RelayDefinition)
    # Second distinct owner -- no raise, even though the "owners" diverge
    # on shape; the order side simply does not care about own-PK Relay
    # identity.
    _bind_orderset_owner(ShelfOrder, _PlainDefinition)
    assert ShelfOrder._owner_definition is _RelayDefinition


def test_bind_orderset_owner_rejects_orderset_model_unrelated_to_owner():
    """A first bind whose orderset ``Meta.model`` is unrelated to the owner raises."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOwnerType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    book_def = BookOwnerType.__django_strawberry_definition__
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_orderset_owner(ShelfOrder, book_def)
    msg = str(exc_info.value)
    assert "ShelfOrder" in msg
    assert "Shelf" in msg  # orderset model
    assert "Book" in msg  # owner model
    # The rejected owner must NOT have been stored.
    assert getattr(ShelfOrder, "_owner_definition", None) is None


# ---------------------------------------------------------------------------
# Idempotent finalize after orderset wiring
# ---------------------------------------------------------------------------


def test_finalize_django_types_is_idempotent_after_orderset_wiring():
    """A second ``finalize_django_types()`` call is a no-op."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    finalize_django_types()
    bound = BookOrder._owner_definition
    assert bound is BookType.__django_strawberry_definition__

    # Second call short-circuits via the ``registry.is_finalized()`` guard.
    finalize_django_types()
    assert BookOrder._owner_definition is bound


# ---------------------------------------------------------------------------
# Cooperates with Relay-Node owners
# ---------------------------------------------------------------------------


def test_phase_2_5_runs_under_relay_node_interface():
    """Phase 2.5 order binding cooperates with Relay-Node interface injection."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            interfaces = (relay.Node,)
            orderset_class = BookOrder

    finalize_django_types()

    assert BookOrder._owner_definition is BookType.__django_strawberry_definition__
    assert issubclass(BookType, relay.Node)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookOrderInputType")
