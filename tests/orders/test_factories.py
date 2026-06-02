"""Tests for ``django_strawberry_framework/orders/factories.py`` (Slice 2).

Covers ``OrderArgumentsFactory``'s BFS walk, per-class collision check,
idempotency, subclass rejection, and the leaf / related-branch
annotation shape produced by ``_build_class_type``.
"""

from __future__ import annotations

from typing import get_args

import pytest
import strawberry
from apps.library import models as library_models

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
def _isolate_state():
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
    fields = {f.python_name: f for f in input_cls.__strawberry_definition__.fields}
    title_field = fields["title"]
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
    fields = {f.python_name: f for f in input_cls.__strawberry_definition__.fields}
    shelf_field = fields["shelf"]
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
    assert "OrderArgumentsFactory" in message


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

        class _SubFactory(OrderArgumentsFactory):
            pass

    assert "does not support subclassing" in str(excinfo.value)


def test_factory_skips_related_order_with_none_target():
    """``RelatedOrder(None, ...)`` placeholders are skipped silently in the BFS."""

    class BookOrderNone(OrderSet):
        # ``None`` target is the cookbook's placeholder shape per
        # cookbook lines 124-130 (factory skips the target enqueue).
        ghost = RelatedOrder(None, field_name="ghost")  # type: ignore[arg-type]

        class Meta:
            model = library_models.Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderNone)
    factory.arguments  # must not raise on the None target
    assert "BookOrderNoneInputType" in OrderArgumentsFactory.input_object_types


# Keep ``strawberry`` import alive for re-exported lazy types under
# the Annotated forward-references.
assert strawberry is not None
