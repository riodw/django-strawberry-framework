"""Finalizer tests for order binding, Meta.orderset_class promotion, and orphan validation.

Covers:

- ``Meta.orderset_class`` promotion and validation (positive + negative + local-import).
- Four-subpass ordering: bind owners -> expand fields -> orphan-validate ->
  materialize. Subpass 1 completes across all owners before subpass 2 runs;
  subpass 3 runs BEFORE subpass 4 so an orphan failure leaves no partial
  state.
- First-bind model compatibility per spec-028 (rejects orderset
  wired to unrelated owner model; message names all four entities).
- Multi-owner reuse: identical-target accepted; diverging-target rejected;
  idempotent re-bind of the same ``(orderset, definition)`` pair accepted;
  a second owner refused when either owner has a custom ``get_queryset``, or
  when the two owners read different tables (a multi-table-inheritance parent
  and child), in both declaration orders.
- Per Decision 6 the order side does NOT enforce the filter side's own-PK
  Relay-identity check.
- Unresolved ``RelatedOrder`` propagates as ``ConfigurationError`` with the
  underlying ``ImportError`` preserved on ``__cause__``; non-import
  expansion failure rewraps uniformly.
- Materialization writes input classes to ``orders.inputs.__dict__``;
  idempotent ``finalize_django_types()``.
- Partial-failure recovery (the partially-materialized state stays consistent
  with the ledger).

Finalize-time bind / orphan / collision have no request. Shipped
``Meta.orderset_class`` wiring is exercised live by
``examples/fakeshop/test_query/test_library_api.py``.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, LendingDesk, ProxyBranch, Shelf, Venue
from django.db import models
from django.db.models import QuerySet
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import (
    OrderInput,
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
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.types.finalizer import _bind_orderset_owner
from django_strawberry_framework.types.relay import apply_interfaces
from tests._idioms import definition_raises


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
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

        @definition_raises
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

    Pins the spec-028 contract: the import lives
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
    def instrumented_get_fields(cls: type[OrderSet]):
        observations.append(cls._owner_definition is not None)
        return original_get_fields(cls)

    # basedpyright: the classmethod spy installed on the class is the probe under test; the
    # checker compares the descriptor against the bound hook signature
    ShelfOrder.get_fields = instrumented_get_fields  # pyright: ignore[reportAttributeAccessIssue]
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title", "shelf")
                orderset_class = BookOrder

        assert registry.get(Book) is BookType

        class ShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "code")
                orderset_class = ShelfOrder

        assert registry.get(Shelf) is ShelfType

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

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

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

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookOrder" in msg
    assert "raised during expansion" in msg
    assert "ValueError" in msg
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_phase_2_5_non_order_set_related_target_raises_uniform_error():
    """A ``RelatedOrder`` resolving to a non-``OrderSet`` class surfaces typed at finalize.

    The target-type gate on ``RelatedOrder.orderset`` raises
    ``ConfigurationError`` at the subpass-2 Layer-2 walk (``_expand_orderset``
    forces ``related.orderset``), which propagates BY IDENTITY (the
    ``except ConfigurationError: raise`` pass-through) -- the mis-wiring can
    no longer survive until subpass 4's BFS materialization, where it used to
    leak a raw ``AttributeError`` (``type_name_for`` missing on the target)
    outside the uniform rewrap.
    """

    class NotAnOrderSet:
        pass

    class BookOrder(OrderSet):
        # basedpyright: the non-OrderSet target is the hostile input under test; RelatedOrder types
        # the parameter as _OrderSetTarget
        shelf = RelatedOrder(NotAnOrderSet, field_name="shelf")  # pyright: ignore[reportArgumentType]

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    # The typed gate's message, propagated by identity (no subpass-2 rewrap).
    assert "BookOrder" in msg
    assert "NotAnOrderSet" in msg
    assert "OrderSet subclass" in msg
    assert "raised during expansion" not in msg


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

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

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

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "StandaloneOrder" in msg
    assert "is referenced via OrderInput[...] / order_input_type(...) but never" in msg
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

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = WiredOrder

    assert registry.get(Book) is BookType

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

    # One orphan per helper spelling: both feed the one ledger the check reads.
    OrderInput[OrphanA]
    order_input_type(OrphanB)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert (
        "OrderSets referenced via OrderInput[...] / order_input_type(...) but not wired to "
        "any DjangoType:" in msg
    )
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

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    finalize_django_types()

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookOrderInputType")
    assert "BookOrderInputType" in _materialized_names


# ---------------------------------------------------------------------------
# Decision 6 -- first-bind model compatibility
# ---------------------------------------------------------------------------


def test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model():
    """Rejects an orderset wired to an unrelated model.

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

    assert registry.get(Branch) is BranchType

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


def _owner(model: type[models.Model]) -> DjangoTypeDefinition:
    """Declare a plain real ``DjangoType`` over ``model`` and return its definition."""
    owner_model = model

    class OwnerType(DjangoType):
        class Meta:
            model = owner_model
            fields = ("id",)

    return OwnerType.__django_strawberry_definition__


def _resolves_nothing(_field_name: object) -> None:
    """A ``related_target_for`` that resolves no relation."""


def test_bind_orderset_owner_idempotent_for_same_definition():
    """Re-binding the SAME ``(orderset, definition)`` pair is a no-op."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    definition = _owner(Shelf)
    _bind_orderset_owner(ShelfOrder, definition)  # previous None -> bind
    _bind_orderset_owner(ShelfOrder, definition)  # previous IS definition -> no-op
    assert ShelfOrder._owner_definition is definition


def test_bind_orderset_owner_rejects_diverging_related_targets(monkeypatch: pytest.MonkeyPatch):
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

    class PrevTargetType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id",)

    class NewTargetType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id",)

    prev_target = PrevTargetType.__django_strawberry_definition__
    new_target = NewTargetType.__django_strawberry_definition__
    shelf_field = Book._meta.get_field("shelf")
    first = _owner(Book)
    second = _owner(Book)

    # Two live owners resolve ``shelf`` through the one registry and so always agree; each
    # owner's lookup is forced to its own target to reach the defensive divergence check.
    def prev_lookup(_field_name: object):
        return (prev_target, shelf_field)

    def new_lookup(_field_name: object):
        return (new_target, shelf_field)

    monkeypatch.setattr(first, "related_target_for", prev_lookup)
    monkeypatch.setattr(second, "related_target_for", new_lookup)
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

    # No ``Shelf`` type is registered, so neither owner resolves ``shelf``.
    first = _owner(Book)
    second = _owner(Book)
    _bind_orderset_owner(BookOrder, first)
    _bind_orderset_owner(BookOrder, second)
    # First binding preserved.
    assert BookOrder._owner_definition is first


def test_bind_orderset_owner_raises_when_one_owner_resolves_and_other_does_not(
    monkeypatch: pytest.MonkeyPatch,
):
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

    _owner(Shelf)
    first = _owner(Book)
    second = _owner(Book)
    # Two live owners resolve ``shelf`` through the one registry and so always agree; the
    # second owner's lookup is forced to resolve nothing to reach the defensive divergence check.
    monkeypatch.setattr(second, "related_target_for", _resolves_nothing)
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
    class RelayShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    class PlainShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    apply_interfaces(RelayShelfType, RelayShelfType.__django_strawberry_definition__)
    relay_def = RelayShelfType.__django_strawberry_definition__

    _bind_orderset_owner(ShelfOrder, relay_def)
    # Second distinct owner -- no raise, even though the owners diverge on
    # Relay-node-ness; the order side simply does not care about own-PK Relay
    # identity.
    _bind_orderset_owner(ShelfOrder, PlainShelfType.__django_strawberry_definition__)
    assert ShelfOrder._owner_definition is relay_def


def _declare_shared_shelf_order_owners(*, hooked_first: bool) -> list[type[DjangoType]]:
    """Declare one ``ShelfOrder`` on a hiding and a plain ``Shelf`` type, a ``RelatedOrder`` target.

    ``hooked_first`` picks which owner registers, and so binds, first; the two
    owners return in declaration order.
    """

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    def hiding() -> type[DjangoType]:
        class HidingShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = True
                orderset_class = ShelfOrder

            @classmethod
            @override
            def get_queryset(cls, queryset: QuerySet[Shelf], info: object, **kwargs: object):
                return queryset.exclude(topic="secret")

        return HidingShelfType

    def plain() -> type[DjangoType]:
        class PlainShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = False
                orderset_class = ShelfOrder

        return PlainShelfType

    owners = [declare() for declare in ((hiding, plain) if hooked_first else (plain, hiding))]

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = BookOrder

    assert BookType.__django_strawberry_definition__.orderset_class is BookOrder
    return owners


@pytest.mark.parametrize("hooked_first", [True, False], ids=["hiding-first", "plain-first"])
def test_phase_2_5_rejects_shared_orderset_when_an_owner_scopes_get_queryset(hooked_first: bool):
    """One ``OrderSet`` on a hiding and a plain owner is refused in both declaration orders.

    ``orderBy: [{shelf: {topic: ...}}]`` reads the ``shelf`` hop through the type
    ``ShelfOrder`` is bound to (``OrderSet._scoped_hops``), and only the first
    binding is stored: bound to ``PlainShelfType`` a hidden shelf's topic would
    position its book, bound to ``HidingShelfType`` it would sort as a missing
    shelf. Finalize refuses the pairing instead of letting declaration order
    pick the visibility.
    """
    owners = _declare_shared_shelf_order_owners(hooked_first=hooked_first)
    expected = ["HidingShelfType", "PlainShelfType"]
    assert [owner.__name__ for owner in owners] == (expected if hooked_first else expected[::-1])
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert msg.startswith("OrderSet ")
    assert "get_queryset visibility" in msg
    assert "RelatedOrder target" in msg
    assert "ShelfOrder" in msg
    assert "HidingShelfType" in msg
    assert "PlainShelfType" in msg
    assert "Declare separate OrderSet subclasses per owner." in msg


def test_phase_2_5_rejects_shared_orderset_whose_owners_share_one_custom_get_queryset():
    """Two owners inheriting ONE custom ``get_queryset`` are refused: function identity is not visibility.

    The hook runs with each owner's own ``cls``, so a ``cls``-parameterized body
    can hide different rows per owner while both owners share its function.
    """

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class _HidingShelfBase(DjangoType):
        # No ``Meta``: an unregistered base both owners inherit the hook from.
        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Shelf], info: object, **kwargs: object):
            return queryset.exclude(topic="secret")

    class PrimaryShelfType(_HidingShelfBase):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            primary = True
            orderset_class = ShelfOrder

    class SecondaryShelfType(_HidingShelfBase):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            orderset_class = ShelfOrder

    assert registry.get(Shelf) is PrimaryShelfType
    assert registry.model_for_type(SecondaryShelfType) is Shelf
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "get_queryset visibility" in msg
    assert "PrimaryShelfType" in msg
    assert "SecondaryShelfType" in msg


def test_phase_2_5_accepts_shared_orderset_whose_owners_keep_the_identity_get_queryset():
    """Two owners of one model that both keep the default hook hide nothing, so they share a set."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class PrimaryShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            primary = True
            orderset_class = ShelfOrder

    class SecondaryShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            orderset_class = ShelfOrder

    finalize_django_types()
    assert ShelfOrder._owner_definition is PrimaryShelfType.__django_strawberry_definition__
    assert SecondaryShelfType.__django_strawberry_definition__.orderset_class is ShelfOrder


@pytest.mark.parametrize("parent_first", [True, False], ids=["parent-first", "child-first"])
def test_phase_2_5_rejects_shared_orderset_whose_owners_read_different_tables(parent_first: bool):
    """A ``Venue`` owner and a ``LendingDesk`` owner of one ``OrderSet`` are refused in both orders.

    A path re-entering the set's table reads the type it is bound to, and
    multi-table-inheritance parent and child are different tables: bound to the
    parent owner a re-entered ``Venue`` row reads that owner, bound to the child
    it reads ``Venue``'s primary. Both owners keep the identity hook, so only the
    table axis refuses them.
    """

    class VenueOrder(OrderSet):
        class Meta:
            model = Venue
            fields = ["name"]

    def parent() -> type[DjangoType]:
        class VenueOwnerType(DjangoType):
            class Meta:
                model = Venue
                fields = ("id", "name")
                orderset_class = VenueOrder

        return VenueOwnerType

    def child() -> type[DjangoType]:
        class DeskOwnerType(DjangoType):
            class Meta:
                model = LendingDesk
                fields = ("name",)
                orderset_class = VenueOrder

        return DeskOwnerType

    for declare in (parent, child) if parent_first else (child, parent):
        declare()
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert msg.startswith("OrderSet ")
    assert "cannot bind to multiple owners over different tables" in msg
    assert "VenueOwnerType (model Venue)" in msg
    assert "DeskOwnerType (model LendingDesk)" in msg
    assert "Declare separate OrderSet subclasses per owner." in msg


@pytest.mark.parametrize("proxy_first", [True, False], ids=["proxy-first", "concrete-first"])
def test_phase_2_5_accepts_shared_orderset_whose_owners_read_one_table(proxy_first: bool):
    """A plain ``Branch`` owner and a plain ``ProxyBranch`` owner read one table, so they share a set."""

    class BranchOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["name"]

    def concrete() -> type[DjangoType]:
        class BranchOwnerType(DjangoType):
            class Meta:
                model = Branch
                fields = ("id", "name")
                orderset_class = BranchOrder

        return BranchOwnerType

    def proxy() -> type[DjangoType]:
        class ProxyOwnerType(DjangoType):
            class Meta:
                model = ProxyBranch
                fields = ("id", "name")
                orderset_class = BranchOrder

        return ProxyOwnerType

    owners = [declare() for declare in ((proxy, concrete) if proxy_first else (concrete, proxy))]
    finalize_django_types()
    assert BranchOrder._owner_definition is owners[0].__django_strawberry_definition__
    assert owners[1].__django_strawberry_definition__.orderset_class is BranchOrder


_SUBCLASS_OWNER_CASES = [
    pytest.param(hiding_first, base_on_hiding, id=f"{order}-{wiring}")
    for hiding_first, order in ((True, "hiding-declared-first"), (False, "plain-declared-first"))
    for base_on_hiding, wiring in ((True, "base-on-hiding"), (False, "subclass-on-hiding"))
]


@pytest.mark.django_db
@pytest.mark.parametrize(("hiding_first", "base_on_hiding"), _SUBCLASS_OWNER_CASES)
def test_an_orderset_subclass_binds_its_own_owner_apart_from_its_base(
    hiding_first: bool,
    base_on_hiding: bool,
):
    """``ShelfOrder`` and ``SubShelfOrder(ShelfOrder)`` on two owners each order by their own owner.

    The multi-owner refusal's remedy is a separate set subclass per owner, so a
    subclass binds its OWN owner and never sees its base's binding as a second
    owner, whichever type declares first and whichever class the hiding type
    wires. Each ``RelatedOrder`` branch then reads the type its target class is
    bound to: through the hiding owner a hidden shelf sorts as a missing one
    (last under ``ASC_NULLS_LAST``), through the plain owner by its topic.
    """
    from django.test import RequestFactory

    from django_strawberry_framework import DjangoListField

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class SubShelfOrder(ShelfOrder):
        pass

    hiding_set, plain_set = (
        (ShelfOrder, SubShelfOrder) if base_on_hiding else (SubShelfOrder, ShelfOrder)
    )

    def hiding() -> type[DjangoType]:
        class HidingShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = True
                orderset_class = hiding_set

            @classmethod
            @override
            def get_queryset(cls, queryset: QuerySet[Shelf], info: object, **kwargs: object):
                return queryset.exclude(topic="secret")

        return HidingShelfType

    def plain() -> type[DjangoType]:
        class PlainShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = False
                orderset_class = plain_set

        return PlainShelfType

    declared = [declare() for declare in ((hiding, plain) if hiding_first else (plain, hiding))]
    hiding_type, plain_type = declared if hiding_first else declared[::-1]

    class ViaHidingBookOrder(OrderSet):
        shelf = RelatedOrder(hiding_set, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ViaPlainBookOrder(OrderSet):
        shelf = RelatedOrder(plain_set, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ViaHidingBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            primary = True
            orderset_class = ViaHidingBookOrder

    class ViaPlainBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = ViaPlainBookOrder

    finalize_django_types()
    assert ShelfOrder.__dict__["_owner_definition"].origin is (
        hiding_type if base_on_hiding else plain_type
    )
    assert SubShelfOrder.__dict__["_owner_definition"].origin is (
        plain_type if base_on_hiding else hiding_type
    )

    # ``from __future__ import annotations`` leaves a class-body annotation a string
    # naming a function local, so the root type is built with resolved annotations.
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "via_hiding": list[ViaHidingBookType],
                    "via_plain": list[ViaPlainBookType],
                },
                "via_hiding": DjangoListField(ViaHidingBookType),
                "via_plain": DjangoListField(ViaPlainBookType),
            },
        ),
    )

    branch = Branch.objects.create(name="b")
    hidden = Shelf.objects.create(branch=branch, code="h", topic="secret")
    seen = Shelf.objects.create(branch=branch, code="s", topic="zzz")
    Book.objects.create(title="on-hidden", shelf=hidden)
    Book.objects.create(title="on-seen", shelf=seen)
    order = "(orderBy: [{shelf: {topic: ASC_NULLS_LAST}}]) { title }"
    result = strawberry.Schema(query=query).execute_sync(
        f"{{ viaHiding{order} viaPlain{order} }}",
        context_value={"request": RequestFactory().get("/")},
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    assert [row["title"] for row in result.data["viaHiding"]] == ["on-seen", "on-hidden"]
    assert [row["title"] for row in result.data["viaPlain"]] == ["on-hidden", "on-seen"]


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

    assert registry.get(Shelf) is ShelfType

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

    assert registry.get(Shelf) is ShelfType

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    assert registry.get(Genre) is GenreType

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
