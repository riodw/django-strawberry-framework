"""OrderArgumentsFactory tests for BFS generation, annotations, caching, idempotency, and validation.

Covers ``OrderArgumentsFactory``'s BFS walk, per-class collision check,
idempotency, subclass rejection, the leaf / related-branch annotation
shape produced by ``_build_class_type``, and set-shaped ``Meta.fields``
expansion order.

Factory construction and collision guards have no wire shape. Published
``orderBy`` argument types live in
``examples/fakeshop/test_query/test_library_api.py`` and
``examples/fakeshop/test_query/test_list_field_api.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import get_args

import pytest
import strawberry
from apps.library import models as library_models
from strawberry.types.base import get_object_definition

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import (
    OrderSet,
    RelatedOrder,
)
from django_strawberry_framework.orders.factories import OrderArgumentsFactory
from django_strawberry_framework.orders.inputs import (
    Ordering,
    _field_specs,
    _materialized_names,
)


@pytest.fixture(autouse=True)
def _isolate_state() -> Iterator[None]:
    """Clear per-test state so cross-test class-level caches don't leak."""
    _materialized_names.clear()
    _field_specs.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    yield
    _materialized_names.clear()
    _field_specs.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()


# ---------------------------------------------------------------------------
# OrderArgumentsFactory BFS
# ---------------------------------------------------------------------------


def test_factory_visits_every_reachable_relatedorder_target_via_bfs():
    """A ``Book -> Shelf`` + ``Book -> Genre`` graph -> all three classes built."""

    class ShelfOrderBfs(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class GenreOrderBfs(OrderSet):
        class Meta:
            model = library_models.Genre
            fields = ["name"]

    class BookOrderBfs(OrderSet):
        shelf = RelatedOrder(ShelfOrderBfs, field_name="shelf")
        genres = RelatedOrder(GenreOrderBfs, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderBfs)
    factory.arguments  # trigger build
    for name in ("BookOrderBfsInputType", "ShelfOrderBfsInputType", "GenreOrderBfsInputType"):
        assert name in OrderArgumentsFactory.input_object_types
        assert name in OrderArgumentsFactory._type_orderset_registry


def test_factory_handles_cycles_via_seen_set():
    """Mutual ``A -> B -> A`` ``RelatedOrder``s do not blow the BFS stack."""

    class AOrderCycle(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class BOrderCycle(OrderSet):
        a = RelatedOrder(AOrderCycle, field_name="a")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    # Close the cycle by attaching A -> B post-declaration. Direct class
    # attribute assignment bypasses the metaclass; manually bind via the
    # ``related_orders`` dict + ``RelatedOrder.bind_orderset``.
    rel = RelatedOrder(BOrderCycle, field_name="b")
    rel.bind_orderset(AOrderCycle)
    AOrderCycle.related_orders["b"] = rel

    factory = OrderArgumentsFactory(AOrderCycle)
    factory.arguments  # must not recurse forever
    assert "AOrderCycleInputType" in OrderArgumentsFactory.input_object_types
    assert "BOrderCycleInputType" in OrderArgumentsFactory.input_object_types
    # Each class is built exactly once (no duplicate-build).
    assert OrderArgumentsFactory._type_orderset_registry["AOrderCycleInputType"] is AOrderCycle
    assert OrderArgumentsFactory._type_orderset_registry["BOrderCycleInputType"] is BOrderCycle


def test_factory_builds_leaf_fields_with_ordering_or_none_annotation():
    """Leaf fields land typed as ``Ordering | None``."""

    class BookOrderLeaf(OrderSet):
        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderLeaf)
    input_cls = factory.arguments
    fields = {f.python_name: f for f in get_object_definition(input_cls, strict=True).fields}
    title_field = fields["title"]
    assert title_field.type_annotation is not None
    annotation = title_field.type_annotation.annotation
    # ``Ordering | None`` produces a ``Union[Ordering, NoneType]`` shape.
    args = get_args(annotation)
    assert Ordering in args
    assert type(None) in args


def test_factory_builds_relatedorder_fields_with_annotated_strawberry_lazy_forward_reference():
    """``RelatedOrder`` fields produce ``Annotated[ForwardRef, strawberry.lazy(...)] | None``."""

    class ShelfOrderRel(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class BookOrderRel(OrderSet):
        shelf = RelatedOrder(ShelfOrderRel, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderRel)
    input_cls = factory.arguments
    fields = {f.python_name: f for f in get_object_definition(input_cls, strict=True).fields}
    shelf_field = fields["shelf"]
    assert shelf_field.type_annotation is not None
    annotation = shelf_field.type_annotation.annotation
    non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
    assert non_none, annotation
    inner = non_none[0]
    if hasattr(inner, "__metadata__"):
        forward = inner.__args__[0]
        forward_name = getattr(forward, "__forward_arg__", forward)
    else:
        # ``LazyType`` carries ``.type_name`` after Strawberry resolves.
        forward_name = inner.type_name
    assert forward_name == "ShelfOrderRelInputType"


def test_factory_raises_on_two_distinct_ordersets_sharing_classname():
    """Two distinct ``OrderSet`` classes with the same ``__name__`` -> ``ConfigurationError``."""

    class DupOrder(OrderSet):
        class Meta:
            model = library_models.Branch
            fields = ["name"]

    factory = OrderArgumentsFactory(DupOrder)
    factory.arguments  # build the first one

    # Synthesize a second class with the same ``__name__``.
    DupOrder2 = type(
        "DupOrder",
        (OrderSet,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Shelf, "fields": ["code"]},
            ),
        },
    )
    factory2 = OrderArgumentsFactory(DupOrder2)
    with pytest.raises(ConfigurationError) as excinfo:
        factory2.arguments
    message = str(excinfo.value)
    assert "DupOrderInputType" in message
    # The shared BFS substrate keeps family-specific wording: the message
    # still names OrderArgumentsFactory / OrderSet (not the filter twin).
    assert "OrderArgumentsFactory" in message
    assert "OrderSet" in message


def test_factory_arguments_is_idempotent():
    """Repeated reads of ``.arguments`` return the same input class instance."""

    class IdempotentOrder(OrderSet):
        class Meta:
            model = library_models.Branch
            fields = ["name"]

    factory = OrderArgumentsFactory(IdempotentOrder)
    first = factory.arguments
    second = factory.arguments
    assert first is second


def test_factory_input_object_types_shared_across_factory_instances():
    """``input_object_types`` is a class-level dict shared across instances."""

    class SharedOrderA(OrderSet):
        class Meta:
            model = library_models.Branch
            fields = ["name"]

    class SharedOrderB(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    factory_a = OrderArgumentsFactory(SharedOrderA)
    factory_a.arguments
    factory_b = OrderArgumentsFactory(SharedOrderB)
    factory_b.arguments
    assert "SharedOrderAInputType" in OrderArgumentsFactory.input_object_types
    assert "SharedOrderBInputType" in OrderArgumentsFactory.input_object_types


def test_factory_subclass_rejected_at_class_creation_time():
    """Subclassing ``OrderArgumentsFactory`` raises ``TypeError`` immediately."""
    with pytest.raises(TypeError) as excinfo:
        # basedpyright: the class statement is the call under test and raises, so the name is never bound
        class _SubFactory(OrderArgumentsFactory):  # pyright: ignore[reportUnusedClass]
            pass

    assert "does not support subclassing" in str(excinfo.value)


def test_factory_skips_related_order_with_none_target():
    """``RelatedOrder(None, ...)`` placeholders are skipped silently in the BFS."""

    class BookOrderNone(OrderSet):
        # ``None`` target is the cookbook's placeholder shape per
        # cookbook lines 124-130 (factory skips the target enqueue).
        ghost = RelatedOrder(None, field_name="ghost")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderNone)
    factory.arguments  # must not raise on the None target
    assert "BookOrderNoneInputType" in OrderArgumentsFactory.input_object_types


def test_factory_rejects_related_orders_with_colliding_graphql_names():
    """The order family shares the generated GraphQL-name collision guard."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class BookCollisionOrder(OrderSet):
        foo_bar = RelatedOrder(ShelfOrder, field_name="shelf")
        fooBar = RelatedOrder(  # noqa: N815 - intentional camel-case collision fixture.
            ShelfOrder,
            field_name="shelf",
        )

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookCollisionOrder)
    with pytest.raises(ConfigurationError) as excinfo:
        factory.arguments
    message = str(excinfo.value)
    assert "'foo_bar'" in message
    assert "'fooBar'" in message
    assert "GraphQL input field name 'fooBar'" in message


# ---------------------------------------------------------------------------
# Empty-orderset guard -- a zero-field OrderSet must fail loud at the factory
# boundary (a ConfigurationError naming the set), never reach schema build as a
# raw Strawberry ``ValueError: Input Object type ... must define one or more
# fields``. The order family is the only set family that can be empty: filters
# always carry the ``and_`` / ``or_`` / ``not_`` operator bag, so their input is
# never zero-field. Mirrors the write-side empty-input guards in
# ``mutations`` / ``forms`` / ``rest_framework`` ``inputs.py``.
# ---------------------------------------------------------------------------


def test_factory_raises_on_orderset_with_no_orderable_fields():
    """An ``OrderSet`` whose expansion is empty raises ``ConfigurationError``.

    Pre-fix the factory built a zero-field ``@strawberry.input`` that only blew
    up later at ``strawberry.Schema(...)`` with a raw ``ValueError`` naming the
    GENERATED type (``EmptyOrderInputType``) rather than the consumer's class.
    The guard fails loud at the framework boundary instead.
    """

    class EmptyOrder(OrderSet):
        # Omitted ``Meta.fields`` and no ``RelatedOrder`` -> ``get_fields()``
        # expands to nothing -> zero input-field triples.
        class Meta:
            model = library_models.Book

    factory = OrderArgumentsFactory(EmptyOrder)
    with pytest.raises(ConfigurationError) as excinfo:
        factory.arguments
    message = str(excinfo.value)
    assert "EmptyOrderInputType" in message
    assert "no fields" in message
    # Family-specific wording is preserved through the shared BFS substrate.
    assert "OrderArgumentsFactory" in message
    assert "OrderSet" in message


def test_factory_raises_on_orderset_with_empty_fields_list():
    """``Meta.fields = []`` is also rejected at the factory boundary."""

    class EmptyListOrder(OrderSet):
        class Meta:
            model = library_models.Book
            fields = []

    factory = OrderArgumentsFactory(EmptyListOrder)
    with pytest.raises(ConfigurationError) as excinfo:
        factory.arguments
    assert "EmptyListOrderInputType" in str(excinfo.value)


def test_factory_raises_when_reachable_related_orderset_is_empty():
    """The BFS rejects an empty related target, not only an empty root."""

    class EmptyChildOrder(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = []

    class ParentOrder(OrderSet):
        shelf = RelatedOrder(EmptyChildOrder, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(ParentOrder)
    with pytest.raises(ConfigurationError) as excinfo:
        factory.arguments
    message = str(excinfo.value)
    assert "EmptyChildOrderInputType" in message
    assert "no fields" in message


# ---------------------------------------------------------------------------
# Pop-time ``if set_cls in seen: continue`` skip
# ---------------------------------------------------------------------------


def test_factory_dedupes_double_enqueued_target_via_seen_check():
    """Covers ``utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`` #"if set_cls in seen:".

    The existing ``test_factory_handles_cycles_via_seen_set`` pins the same
    helper's enqueue-time #"if target is not None and target not in seen:"
    gate; this test pins the pop-time one. To force a double-enqueue, declare an
    orderset with TWO ``RelatedOrder`` instances pointing to the SAME
    target -- both walk the ``related_orders.values()`` loop while the
    target is not yet in ``seen`` (the parent class is still in flight),
    so both enqueue. The first pop processes the target; the second pop
    hits the ``if set_cls in seen: continue`` skip.
    """

    class ChildOrderDedup(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class ParentOrderDedup(OrderSet):
        # Two RelatedOrders pointing to the SAME target -- the BFS walks
        # both at the same outer iteration, enqueueing ChildOrderDedup
        # twice before either is popped.
        child_a = RelatedOrder(ChildOrderDedup, field_name="shelf")
        child_b = RelatedOrder(ChildOrderDedup, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(ParentOrderDedup)
    factory.arguments  # must not raise; the pop-time guard fires.
    # The target was built exactly once (the registry has one entry).
    assert (
        OrderArgumentsFactory._type_orderset_registry["ChildOrderDedupInputType"]
        is ChildOrderDedup
    )


# ---------------------------------------------------------------------------
# Meta.fields expansion order
# ---------------------------------------------------------------------------


def test_orderset_set_shaped_meta_fields_expand_in_canonical_order():
    """Class-declared set-shaped ``Meta.fields`` expand in ``repr``-sorted order."""

    class BookOrderSetFields(OrderSet):
        class Meta:
            model = library_models.Book
            fields = {"title", "subtitle"}

    expected = sorted(["title", "subtitle"], key=repr)
    assert list(BookOrderSetFields.get_fields()) == expected
    assert BookOrderSetFields.Meta.fields == {"title", "subtitle"}


def test_factory_handles_diamond_dependency_graph():
    """A -> B -> D and A -> C -> D diamond graph builds D once and all 4 classes exist."""

    class DOrder(OrderSet):
        class Meta:
            model = library_models.Branch
            fields = ["name"]

    class BOrder(OrderSet):
        d = RelatedOrder(DOrder, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class COrder(OrderSet):
        d = RelatedOrder(DOrder, field_name="branch")

        class Meta:
            model = library_models.Genre
            fields = ["name"]

    class AOrder(OrderSet):
        b = RelatedOrder(BOrder, field_name="shelf")
        c = RelatedOrder(COrder, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(AOrder)
    input_cls = factory.arguments
    assert input_cls.__name__ == "AOrderInputType"
    for name in (
        "AOrderInputType",
        "BOrderInputType",
        "COrderInputType",
        "DOrderInputType",
    ):
        assert name in OrderArgumentsFactory.input_object_types
        assert name in OrderArgumentsFactory._type_orderset_registry
    assert OrderArgumentsFactory._type_orderset_registry["DOrderInputType"] is DOrder


def test_factory_handles_4_tier_deep_chain():
    """Book -> Shelf -> Branch -> TaggedItem chain builds all 4 input classes in BFS order."""

    class DOrder(OrderSet):
        class Meta:
            model = library_models.TaggedItem
            fields = ["tag"]

    class COrder(OrderSet):
        d = RelatedOrder(DOrder, field_name="tags")

        class Meta:
            model = library_models.Branch
            fields = ["name"]

    class BOrder(OrderSet):
        c = RelatedOrder(COrder, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class AOrder(OrderSet):
        b = RelatedOrder(BOrder, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(AOrder)
    factory.arguments
    for name in (
        "AOrderInputType",
        "BOrderInputType",
        "COrderInputType",
        "DOrderInputType",
    ):
        assert name in OrderArgumentsFactory.input_object_types


def test_factory_handles_related_order_targeting_callable_factory():
    """RelatedOrder targeting a callable factory is resolved and enqueued properly in BFS."""

    class TargetOrder(OrderSet):
        class Meta:
            model = library_models.Shelf
            fields = ["code"]

    class RootOrder(OrderSet):
        shelf = RelatedOrder(lambda: TargetOrder, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(RootOrder)
    factory.arguments
    assert "RootOrderInputType" in OrderArgumentsFactory.input_object_types
    assert "TargetOrderInputType" in OrderArgumentsFactory.input_object_types


# Keep ``strawberry`` import alive for re-exported lazy types under
# the Annotated forward-references.
assert strawberry is not None
