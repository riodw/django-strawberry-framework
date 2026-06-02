"""Cross-module fixture for the absolute-import-path ``RelatedOrder`` (Slice 4).

``GenreOrder`` lives in its own module so the
``BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")``
declaration in ``orders.py`` exercises Layer-2 absolute-import-path
resolution per spec-028 Slice 4 Test 5. The single same-module
unqualified-name branch is exercised by every other
``RelatedOrder("XOrder")`` declaration in ``orders.py``.
"""

from __future__ import annotations

from apps.library import models
from django_strawberry_framework.orders import OrderSet, RelatedOrder


class GenreOrder(OrderSet):
    """Genre orderset bound to ``GenreType`` at finalize phase 2.5.

    ``GenreType`` declares ``Meta.interfaces = (relay.Node,)`` -- per
    spec-028 Decision 8 + Edge case ``Meta.orderset_class`` on a
    ``DjangoType`` that also declares ``Meta.interfaces = (relay.Node,)``,
    the ``Ordering`` enum's leaf type does NOT depend on Relay shape;
    ``id`` orders by the column, not the GraphQL ID. The own-PK column-
    ordering path is exercised by ordering on ``GenreOrder`` via the
    absolute-import-path resolution from ``BookOrder.genres``.
    """

    books = RelatedOrder("apps.library.orders.BookOrder", field_name="books")

    class Meta:
        model = models.Genre
        fields = ["id", "name"]


__all__ = ("GenreOrder",)
