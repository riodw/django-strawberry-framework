"""Schema-build tests for definition-order-independent DjangoType finalization."""

import pytest
import strawberry
from apps.products.models import Item

from django_strawberry_framework import DjangoType
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def test_manual_strawberry_type_before_finalization_surfaces_sentinel_repr():
    """If Strawberry sees an unresolved relation sentinel, the error names the finalizer."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    strawberry.type(ItemType)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    with pytest.raises(TypeError) as exc_info:
        strawberry.Schema(query=Query)

    msg = str(exc_info.value)
    assert "Unexpected type" in msg
    assert "finalize_django_types()" in msg
