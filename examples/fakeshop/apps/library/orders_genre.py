"""Planned cross-module ``GenreOrder`` fixture."""

# TODO(spec-028-orders-0_0_8 Slice 4): Add ``GenreOrder`` in a separate module
# so ``BookOrder.genres`` exercises the absolute-import-path lazy resolution
# branch.
# Pseudocode:
#   - import ``OrderSet`` and ``RelatedOrder`` from
#     ``django_strawberry_framework.orders``.
#   - define ``GenreOrder.Meta.model = models.Genre`` with ``id`` and ``name``.
#   - add ``books = RelatedOrder("apps.library.orders.BookOrder", field_name="books")``
#     to keep the cross-module relation graph cyclic.
#   - export ``GenreOrder`` through ``__all__``.
