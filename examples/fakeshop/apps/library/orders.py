"""OrderSet declarations for library relation-graph and keyset-cursor acceptance coverage.

Twenty-six ordersets mirror the relation shape ``apps.library.schema`` exposes
through the live ``/graphql/`` endpoint; ``PeriodicalOrder`` and
``IssueOrder`` are the keyset-cursor ``orderBy:`` substrate: a root
``orderBy: {title: ASC}`` page over ``IssueOrder`` mints value cursors
fingerprinted to THAT order, and ``PeriodicalOrder`` is the related target
``IssueOrder.periodical`` reaches. Inter-orderset references use the
same-module unqualified-name form (e.g. ``RelatedOrder("ShelfOrder")``) so
the lazy-resolution Layer-2 prefix-with-owner branch is exercised end to end; the
``BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")``
declaration deliberately uses the absolute-import-path form so the
Layer-2 ``import_string`` first-attempt branch is also exercised
(spec-028 Decision 3 Layer 2).

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
    active-input-only / active-related-branch coverage tests
    (spec-028 test plan). The gates raise ``GraphQLError`` with the explicit
    ``code="ORDER_PERMISSION_DENIED"`` extension code so the live HTTP
    tests can assert the extension-code value verbatim.
    """

    shelves = RelatedOrder("ShelfOrder", field_name="shelves")

    class Meta:
        model = models.Branch
        fields = ["id", "name", "city"]

    @classmethod
    def check_name_permission(cls, request: Any) -> None:
        """Active-input-only scalar gate: denies an anonymous order by ``name``.

        The gate fires ONLY when the consumer's input names ``name``
        (``orderBy: [{ name: ASC }]``); an input naming another scalar
        (``orderBy: [{ city: ASC }]``) leaves it quiet. Both halves are
        pinned live by
        ``test_library_api.py::test_order_check_permission_denies_for_active_field``
        and
        ``test_library_api.py::test_order_check_permission_quiet_for_inactive_field``.
        """
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_staff", False):
            raise GraphQLError(
                "staff only",
                extensions={"code": "ORDER_PERMISSION_DENIED"},
            )

    @classmethod
    def check_shelves_permission(cls, request: Any) -> None:
        """Active-related-branch gate: denies an anonymous order through ``shelves``.

        Active-branch dispatch: the gate fires ONLY when the consumer's
        input names the ``shelves`` RelatedOrder branch
        (``orderBy: [{ shelves: { code: ASC } }]``); an input naming the
        unguarded ``city`` scalar fires neither this gate nor
        ``check_name_permission``. Both halves are pinned live by
        ``test_library_api.py::test_order_check_permission_denies_active_related_branch``.
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
    spec-028 test plan (M2M absolute-import-path).

    ``BookOrder.Meta.fields`` carries the path-shorthand ``"shelf__code"``
    which renders as ``shelfCode: Ordering`` on the input type per
    spec-028 test plan (flat-shorthand path), pinned live by
    ``test_library_api.py::test_library_books_order_by_flat_shorthand_path``.
    The explicit ``shelf = RelatedOrder("ShelfOrder", field_name="shelf")``
    declaration produces the nested-shape ``shelf: ShelfOrderInputType``
    surface, pinned live by
    ``test_library_api.py::test_library_books_order_by_forward_fk_relation``
    and
    ``test_library_api.py::test_library_books_order_by_multi_field_priority``.
    Both surfaces coexist on the same input type.
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


class PublisherOrder(OrderSet):
    """Publisher orderset bound to ``PublisherType`` at finalize phase 2.5."""

    editions = RelatedOrder("EditionOrder", field_name="editions")

    class Meta:
        model = models.Publisher
        fields = ["id", "name", "house_code"]


class EditionOrder(OrderSet):
    """Edition orderset bound to ``EditionType`` at finalize phase 2.5."""

    publisher = RelatedOrder("PublisherOrder", field_name="publisher")

    class Meta:
        model = models.Edition
        fields = ["isbn_13", "imprint"]


class PrintingOrder(OrderSet):
    """Printing orderset bound to ``PrintingType`` at finalize phase 2.5."""

    edition = RelatedOrder("EditionOrder", field_name="edition")

    class Meta:
        model = models.Printing
        fields = ["id", "run_size"]


class PatronProfileOrder(OrderSet):
    """Patron-profile orderset bound to ``PatronProfileType`` at finalize phase 2.5.

    The model's primary key is its one-to-one key, so the declared scalars are
    the profile's own address columns and the patron is ordered through the
    ``patron`` related order.
    """

    patron = RelatedOrder("PatronOrder", field_name="patron")

    class Meta:
        model = models.PatronProfile
        fields = ["postal_code"]


class AnnotationOrder(OrderSet):
    """Annotation orderset bound to ``AnnotationType`` at finalize phase 2.5."""

    profile = RelatedOrder("PatronProfileOrder", field_name="profile")

    class Meta:
        model = models.Annotation
        fields = ["id", "body"]


class DistributorOrder(OrderSet):
    """Distributor orderset bound to ``DistributorType`` at finalize phase 2.5."""

    class Meta:
        model = models.Distributor
        fields = ["id"]


class ConsignmentOrder(OrderSet):
    """Consignment orderset bound to ``ConsignmentType`` at finalize phase 2.5."""

    class Meta:
        model = models.Consignment
        fields = ["id", "label"]


class VenueOrder(OrderSet):
    """Venue orderset bound to ``VenueType`` at finalize phase 2.5."""

    class Meta:
        model = models.Venue
        fields = ["id", "name", "opened_on"]


class LendingDeskOrder(OrderSet):
    """Lending-desk orderset bound to ``LendingDeskType`` at finalize phase 2.5.

    ``opened_on`` is the inherited parent column a desk page is sorted by, and
    ``window_count`` the child's local one.
    """

    class Meta:
        model = models.LendingDesk
        fields = [
            "id",
            "name",
            "opened_on",
            "window_count",
        ]


class SelfServeDeskOrder(OrderSet):
    """Self-serve-desk orderset bound to ``SelfServeDeskType`` at finalize phase 2.5."""

    class Meta:
        model = models.SelfServeDesk
        fields = [
            "id",
            "name",
            "opened_on",
            "window_count",
            "kiosk_code",
        ]


class OpenVenueOrder(OrderSet):
    """Open-venue orderset bound to ``OpenVenueType`` at finalize phase 2.5."""

    class Meta:
        model = models.OpenVenue
        fields = ["id", "name", "opened_on"]


class RepairTicketOrder(OrderSet):
    """Repair-ticket orderset bound to ``RepairTicketType`` at finalize phase 2.5."""

    venue = RelatedOrder("VenueOrder", field_name="venue")

    class Meta:
        model = models.RepairTicket
        fields = ["id", "code"]


class VenueBadgeOrder(OrderSet):
    """Venue-badge orderset bound to ``VenueBadgeType`` at finalize phase 2.5."""

    class Meta:
        model = models.VenueBadge
        fields = ["id", "code"]


class VenueSponsorOrder(OrderSet):
    """Venue-sponsor orderset bound to ``VenueSponsorType`` at finalize phase 2.5."""

    class Meta:
        model = models.VenueSponsor
        fields = ["id", "name"]


class VisibleBranchOrder(OrderSet):
    """Visible-branch orderset bound to ``VisibleBranchType`` at finalize phase 2.5."""

    class Meta:
        model = models.VisibleBranch
        fields = ["id", "name", "city"]


class BranchSignageOrder(OrderSet):
    """Branch-signage orderset bound to ``BranchSignageType`` at finalize phase 2.5."""

    branch = RelatedOrder("VisibleBranchOrder", field_name="branch")

    class Meta:
        model = models.BranchSignage
        fields = ["id", "code"]


class CirculationDeskOrder(OrderSet):
    """Circulation-desk orderset bound to ``CirculationDeskType`` at finalize phase 2.5."""

    class Meta:
        model = models.CirculationDesk
        fields = ["id", "name"]


class DeskShiftOrder(OrderSet):
    """Desk-shift orderset bound to ``DeskShiftType`` at finalize phase 2.5."""

    desk = RelatedOrder("CirculationDeskOrder", field_name="desk")

    class Meta:
        model = models.DeskShift
        fields = ["id", "name"]


class DeskProfileOrder(OrderSet):
    """Desk-profile orderset bound to ``DeskProfileType`` at finalize phase 2.5."""

    class Meta:
        model = models.DeskProfile
        fields = ["id", "code"]


__all__ = (
    "AnnotationOrder",
    "BookOrder",
    "BranchOrder",
    "BranchSignageOrder",
    "CirculationDeskOrder",
    "ConsignmentOrder",
    "DeskProfileOrder",
    "DeskShiftOrder",
    "DistributorOrder",
    "EditionOrder",
    "IssueOrder",
    "LendingDeskOrder",
    "LoanOrder",
    "OpenVenueOrder",
    "PatronOrder",
    "PatronProfileOrder",
    "PeriodicalOrder",
    "PrintingOrder",
    "PublisherOrder",
    "RepairTicketOrder",
    "SelfServeDeskOrder",
    "ShelfOrder",
    "VenueBadgeOrder",
    "VenueOrder",
    "VenueSponsorOrder",
    "VisibleBranchOrder",
)
