"""OrderSet declarations for the library acceptance app (Slice 4).

Five ordersets mirror the relation shape ``apps.library.schema`` exposes
through the live ``/graphql/`` endpoint. Inter-orderset references use
the same-module unqualified-name form (e.g. ``RelatedOrder("ShelfOrder")``)
so the lazy-resolution Layer-2 prefix-with-owner branch is exercised end
to end; the ``BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")``
declaration deliberately uses the absolute-import-path form so the
Layer-2 ``import_string`` first-attempt branch is also exercised
(spec-028 Slice 4 + Decision 11).

``GenreOrder`` lives in the sibling ``orders_genre.py`` module so the
absolute-import-path resolution path has a real cross-module target;
both branches of the Layer-2 fallback are visible from the fakeshop
order graph.
"""

from __future__ import annotations

from typing import Any

from graphql import GraphQLError

from apps.library import models
from django_strawberry_framework.orders import OrderSet, RelatedOrder


class BranchOrder(OrderSet):
    """Branch orderset bound to ``BranchType`` at finalize phase 2.5.

    Carries two ``check_*_permission`` gates load-bearing for the
    Slice-4 active-input-only / active-related-branch coverage tests
    (spec-028 Slice 4 Tests 9, 10, 11 per Spec test plan). The gates
    raise ``GraphQLError`` with the explicit
    ``code="ORDER_PERMISSION_DENIED"`` extension code so the live HTTP
    tests can assert the extension-code value verbatim.
    """

    shelves = RelatedOrder("ShelfOrder", field_name="shelves")

    class Meta:
        model = models.Branch
        fields = ["id", "name", "city"]

    @classmethod
    def check_name_permission(cls, request: Any) -> None:
        """Active-input-only scalar gate fired by Test 9 (denies) + quiet for Test 10.

        Spec-028 M6-rev1 split-pair: the gate fires ONLY when the
        consumer's input names ``name`` (Test 9's input is
        ``orderBy: [{ name: ASC }]``); the input ``orderBy: [{ city:
        ASC }]`` (Test 10) does NOT fire this gate.
        """
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_staff", False):
            raise GraphQLError(
                "staff only",
                extensions={"code": "ORDER_PERMISSION_DENIED"},
            )

    @classmethod
    def check_shelves_permission(cls, request: Any) -> None:
        """Active-related-branch gate fired by Test 11 (denies).

        Spec-028 H3-rev3 active-branch dispatch: the gate fires ONLY
        when the consumer's input names the ``shelves`` RelatedOrder
        branch (Test 11 first-half input ``orderBy: [{ shelves: { code:
        ASC } }]``). Test 11's second-half input uses ``city`` (an
        unguarded scalar) so it does NOT fire this gate or the
        ``check_name_permission`` gate -- per Worker 1's spec
        reconciliation note for Spec line 1041.
        """
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_staff", False):
            raise GraphQLError(
                "hidden shelves",
                extensions={"code": "ORDER_PERMISSION_DENIED"},
            )


class ShelfOrder(OrderSet):
    """Shelf orderset bound to ``ShelfType`` at finalize phase 2.5."""

    branch = RelatedOrder("BranchOrder", field_name="branch")
    books = RelatedOrder("BookOrder", field_name="books")

    class Meta:
        model = models.Shelf
        fields = ["id", "code", "topic"]


class BookOrder(OrderSet):
    """Book orderset bound to ``BookType`` at finalize phase 2.5.

    ``BookOrder.genres`` uses the absolute-import-path form
    ``"apps.library.orders_genre.GenreOrder"`` so the Layer-2
    ``import_string`` first-attempt branch resolves cross-module per
    spec-028 Slice 4 Test 5 (M2M absolute-import-path).

    ``BookOrder.Meta.fields`` carries the path-shorthand ``"shelf__code"``
    which renders as ``shelfCode: Ordering`` on the input type per
    spec-028 Slice 4 Test 13 (flat-shorthand path). The explicit
    ``shelf = RelatedOrder("ShelfOrder", field_name="shelf")``
    declaration produces the nested-shape ``shelf: ShelfOrderInputType``
    surface used by Tests 3, 7, 8, and 12. Both surfaces coexist on
    the same input type.
    """

    shelf = RelatedOrder("ShelfOrder", field_name="shelf")
    genres = RelatedOrder(
        "apps.library.orders_genre.GenreOrder",
        field_name="genres",
    )
    loans = RelatedOrder("LoanOrder", field_name="loans")

    class Meta:
        model = models.Book
        fields = [
            "id",
            "title",
            "subtitle",
            "circulation_status",
            "shelf__code",
        ]


class LoanOrder(OrderSet):
    """Loan orderset bound to ``LoanType`` at finalize phase 2.5."""

    book = RelatedOrder("BookOrder", field_name="book")
    patron = RelatedOrder("PatronOrder", field_name="patron")

    class Meta:
        model = models.Loan
        fields = ["id", "note"]


class PatronOrder(OrderSet):
    """Patron orderset bound to ``PatronType`` at finalize phase 2.5."""

    loans = RelatedOrder("LoanOrder", field_name="loans")

    class Meta:
        model = models.Patron
        fields = ["id", "name"]


class PeriodicalOrder(OrderSet):
    """Periodical orderset - the related target for ``IssueOrder.periodical``."""

    class Meta:
        model = models.Periodical
        fields = ["id", "name"]


class IssueOrder(OrderSet):
    """Issue orderset bound to ``IssueType`` at finalize phase 2.5.

    The keyset-cursor ``orderBy:`` substrate: ``title`` is a non-nullable
    column, so a root ``orderBy: {title: ASC}`` page mints value cursors
    fingerprinted to THAT order (replay under the default ``cursor_field``
    order is rejected at decode - the live order-fingerprint pin). The
    ``periodical`` related order reaches the keyset slicer's related-path
    branch live: ``orderBy: {periodical: {name: ASC}}`` seeks and mints
    through the ``periodical__name`` column via a row annotation.
    """

    periodical = RelatedOrder("PeriodicalOrder", field_name="periodical")

    class Meta:
        model = models.Issue
        fields = ["id", "number", "title"]


__all__ = (
    "BookOrder",
    "BranchOrder",
    "IssueOrder",
    "LoanOrder",
    "PatronOrder",
    "PeriodicalOrder",
    "ShelfOrder",
)
