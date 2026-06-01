"""Planned ``OrderSet`` declarations for the library acceptance app."""

# TODO(spec-028-orders-0_0_8 Slice 4): Add library ordersets used by live HTTP
# acceptance coverage.
# Pseudocode:
#   - define ``BranchOrder`` with ``Meta.model = Branch`` and orderable
#     ``id``, ``name``, ``city`` plus ``shelves = RelatedOrder("ShelfOrder")``.
#   - define ``ShelfOrder`` with ``branch`` / ``books`` related branches and
#     orderable ``id``, ``code``, ``topic``.
#   - define ``BookOrder`` with ``shelf = RelatedOrder("ShelfOrder")``,
#     ``genres = RelatedOrder("apps.library.orders_genre.GenreOrder")``,
#     ``loans = RelatedOrder("LoanOrder")``, and fields including ``title``,
#     ``subtitle``, ``circulation_status``, and flat shorthand ``shelf__code``.
#   - define ``LoanOrder`` and ``PatronOrder`` for the schema wiring mirrors.
#   - declare permission hooks for the live denial tests:
#     ``BranchOrder.check_name_permission`` and
#     ``BranchOrder.check_shelves_permission``.
#   - export the five same-module ordersets through ``__all__``.
