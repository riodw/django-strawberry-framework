"""FilterSet declarations for the library acceptance app.

Twenty-four filtersets mirror the relation shape ``apps.library.schema`` exposes
through the live ``/graphql/`` endpoint. Inter-filterset references use
the same-module unqualified-name form (e.g. ``RelatedFilter("ShelfFilter")``)
so the lazy-resolution Layer-2 prefix-with-owner branch is exercised end
to end; the ``BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")``
declaration deliberately uses the absolute-import-path form so the
Layer-2 ``import_string`` first-attempt branch is also exercised
(spec-027).

``GenreFilter`` lives in the sibling ``filters_genre.py`` module so the
absolute-import-path resolution path has a real cross-module target;
both branches of the Layer-2 fallback are visible from the fakeshop
filter graph.
"""

from __future__ import annotations

from typing import Any

from django import forms
from django_filters import CharFilter

from apps.library import models
from django_strawberry_framework.filters import FilterSet, RelatedFilter


def _validate_email_must_have_at_sign(value: str) -> None:
    """Reject email strings without an ``@`` sign.

    A plain ``String!`` declared filter whose custom validator raises
    ``forms.ValidationError("missing @", code="missing_at_sign")``. Used by
    ``PatronFilter.email_must_have_at_sign``
    so the filter input bypasses GraphQL enum coercion and reaches
    ``_validate_form_or_raise``'s ``FILTER_INVALID`` path.
    """
    if "@" not in value:
        raise forms.ValidationError("missing @", code="missing_at_sign")


class BranchFilter(FilterSet):
    """Branch filterset bound to ``BranchType`` at finalize phase 2.5."""

    shelves = RelatedFilter(
        "ShelfFilter",
        field_name="shelves",
        queryset=models.Shelf.objects.filter(topic="permanent collection"),
    )

    class Meta:
        model = models.Branch
        fields = {
            "id": ["exact", "in"],
            "name": ["exact", "icontains"],
            "city": ["exact", "icontains"],
        }


class ShelfFilter(FilterSet):
    """Shelf filterset bound to ``ShelfType`` at finalize phase 2.5."""

    branch = RelatedFilter("BranchFilter", field_name="branch")
    books = RelatedFilter("BookFilter", field_name="books")

    class Meta:
        model = models.Shelf
        fields = {
            "id": ["exact", "in"],
            "code": ["exact", "icontains"],
            "topic": ["exact", "icontains"],
        }


class BookFilter(FilterSet):
    """Book filterset bound to ``BookType`` at finalize phase 2.5.

    ``BookFilter.genres`` uses the absolute-import-path form
    ``"apps.library.filters_genre.GenreFilter"`` so the Layer-2
    ``import_string`` first-attempt branch resolves cross-module per
    spec-027.
    """

    shelf = RelatedFilter("ShelfFilter", field_name="shelf")
    genres = RelatedFilter(
        "apps.library.filters_genre.GenreFilter",
        field_name="genres",
    )
    loans = RelatedFilter("LoanFilter", field_name="loans")

    class Meta:
        model = models.Book
        fields = {
            "id": ["exact", "in"],
            "title": ["exact", "icontains"],
            "subtitle": ["exact", "icontains", "isnull"],
            "circulation_status": ["exact", "in"],
        }


class LoanFilter(FilterSet):
    """Loan filterset bound to ``LoanType`` at finalize phase 2.5."""

    book = RelatedFilter("BookFilter", field_name="book")
    patron = RelatedFilter("PatronFilter", field_name="patron")

    class Meta:
        model = models.Loan
        fields = {
            "id": ["exact", "in"],
            "note": ["exact", "icontains"],
            "book__loans__patron__email": ["icontains"],
        }


class PatronFilter(FilterSet):
    """Patron filterset bound to ``PatronType`` at finalize phase 2.5.

    ``email_must_have_at_sign`` is the declared custom filter. The underlying
    form field carries ``_validate_email_must_have_at_sign`` as a validator so
    an input
    without ``@`` raises ``forms.ValidationError("missing @",
    code="missing_at_sign")``; ``_validate_form_or_raise`` in
    ``sets.py::FilterSet`` then translates that into the
    ``GraphQLError("Invalid filter input", extensions={"code":
    "FILTER_INVALID", "errors": ...})`` payload the test asserts on.
    """

    loans = RelatedFilter("LoanFilter", field_name="loans")
    email_must_have_at_sign = CharFilter(
        field_name="email",
        method="filter_email_must_have_at_sign",
    )

    class Meta:
        model = models.Patron
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"]}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Wire the validator on the underlying ``forms.CharField`` so
        # ``form.is_valid()`` fires the "missing @" gate on inputs without
        # an ``@`` sign per spec-027.
        email_filter = self.filters.get("email_must_have_at_sign")
        if email_filter is not None:
            email_filter.field.validators.append(_validate_email_must_have_at_sign)

    def filter_email_must_have_at_sign(
        self,
        queryset: Any,
        name: str,
        value: str,
    ) -> Any:
        """Apply the declared filter once the validator has accepted the value."""
        return queryset.filter(email=value)


class PublisherFilter(FilterSet):
    """Publisher filterset bound to ``PublisherType`` at finalize phase 2.5."""

    editions = RelatedFilter("EditionFilter", field_name="editions")

    class Meta:
        model = models.Publisher
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"], "house_code": ["exact"]}


class EditionFilter(FilterSet):
    """Edition filterset bound to ``EditionType`` at finalize phase 2.5."""

    publisher = RelatedFilter("PublisherFilter", field_name="publisher")

    class Meta:
        model = models.Edition
        fields = {
            "isbn_13": ["exact", "in"],
            "isbn_10": ["exact"],
            "imprint": ["exact", "icontains"],
        }


class PrintingFilter(FilterSet):
    """Printing filterset bound to ``PrintingType`` at finalize phase 2.5."""

    edition = RelatedFilter("EditionFilter", field_name="edition")

    class Meta:
        model = models.Printing
        fields = {"id": ["exact", "in"], "run_size": ["exact", "gt"]}


class PatronProfileFilter(FilterSet):
    """Patron-profile filterset bound to ``PatronProfileType`` at finalize phase 2.5.

    The model's primary key is its one-to-one key, so the declared scalars are
    the profile's own address columns; the patron itself is reached through
    the ``patron`` related filter.
    """

    patron = RelatedFilter("PatronFilter", field_name="patron")

    class Meta:
        model = models.PatronProfile
        fields = {"postal_code": ["exact", "icontains"]}


class AnnotationFilter(FilterSet):
    """Annotation filterset bound to ``AnnotationType`` at finalize phase 2.5."""

    profile = RelatedFilter("PatronProfileFilter", field_name="profile")

    class Meta:
        model = models.Annotation
        fields = {"id": ["exact", "in"], "body": ["icontains"]}


class DistributorFilter(FilterSet):
    """Distributor filterset bound to ``DistributorType`` at finalize phase 2.5."""

    class Meta:
        model = models.Distributor
        fields = {"id": ["exact", "in"]}


class ConsignmentFilter(FilterSet):
    """Consignment filterset bound to ``ConsignmentType`` at finalize phase 2.5."""

    class Meta:
        model = models.Consignment
        fields = {"id": ["exact", "in"], "label": ["exact", "icontains"]}


class VenueFilter(FilterSet):
    """Venue filterset bound to ``VenueType`` at finalize phase 2.5."""

    class Meta:
        model = models.Venue
        fields = {
            "id": ["exact", "in"],
            "name": ["exact", "icontains"],
            "opened_on": ["exact", "gt"],
        }


class LendingDeskFilter(FilterSet):
    """Lending-desk filterset bound to ``LendingDeskType`` at finalize phase 2.5.

    ``name`` and ``opened_on`` are inherited from ``Venue``, so their lookups
    resolve through the ``venue_ptr`` join; ``window_count`` is the child's own.
    """

    class Meta:
        model = models.LendingDesk
        fields = {
            "id": ["exact", "in"],
            "name": ["exact", "icontains"],
            "opened_on": ["exact", "gt"],
            "window_count": ["exact", "gt"],
        }


class SelfServeDeskFilter(FilterSet):
    """Self-serve-desk filterset bound to ``SelfServeDeskType`` at finalize phase 2.5."""

    class Meta:
        model = models.SelfServeDesk
        fields = {
            "id": ["exact", "in"],
            "name": ["exact", "icontains"],
            "opened_on": ["exact"],
            "window_count": ["exact"],
            "kiosk_code": ["exact"],
        }


class OpenVenueFilter(FilterSet):
    """Open-venue filterset bound to ``OpenVenueType`` at finalize phase 2.5."""

    class Meta:
        model = models.OpenVenue
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"]}


class RepairTicketFilter(FilterSet):
    """Repair-ticket filterset bound to ``RepairTicketType`` at finalize phase 2.5."""

    venue = RelatedFilter("VenueFilter", field_name="venue")

    class Meta:
        model = models.RepairTicket
        fields = {"id": ["exact", "in"], "code": ["exact", "icontains"]}


class VenueBadgeFilter(FilterSet):
    """Venue-badge filterset bound to ``VenueBadgeType`` at finalize phase 2.5."""

    venue = RelatedFilter("VenueFilter", field_name="venue")

    class Meta:
        model = models.VenueBadge
        fields = {"id": ["exact", "in"], "code": ["exact"]}


class VenueSponsorFilter(FilterSet):
    """Venue-sponsor filterset bound to ``VenueSponsorType`` at finalize phase 2.5."""

    venues = RelatedFilter("VenueFilter", field_name="venues")

    class Meta:
        model = models.VenueSponsor
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"]}


class VisibleBranchFilter(FilterSet):
    """Visible-branch filterset bound to ``VisibleBranchType`` at finalize phase 2.5."""

    class Meta:
        model = models.VisibleBranch
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"], "city": ["exact"]}


class BranchSignageFilter(FilterSet):
    """Branch-signage filterset bound to ``BranchSignageType`` at finalize phase 2.5."""

    branch = RelatedFilter("VisibleBranchFilter", field_name="branch")

    class Meta:
        model = models.BranchSignage
        fields = {"id": ["exact", "in"], "code": ["exact", "icontains"]}


class CirculationDeskFilter(FilterSet):
    """Circulation-desk filterset bound to ``CirculationDeskType`` at finalize phase 2.5."""

    branch = RelatedFilter("BranchFilter", field_name="branch")

    class Meta:
        model = models.CirculationDesk
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"]}


class DeskShiftFilter(FilterSet):
    """Desk-shift filterset bound to ``DeskShiftType`` at finalize phase 2.5."""

    desk = RelatedFilter("CirculationDeskFilter", field_name="desk")

    class Meta:
        model = models.DeskShift
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"]}


class DeskProfileFilter(FilterSet):
    """Desk-profile filterset bound to ``DeskProfileType`` at finalize phase 2.5."""

    desk = RelatedFilter("CirculationDeskFilter", field_name="desk")

    class Meta:
        model = models.DeskProfile
        fields = {"id": ["exact", "in"], "code": ["exact"]}


__all__ = (
    "AnnotationFilter",
    "BookFilter",
    "BranchFilter",
    "BranchSignageFilter",
    "CirculationDeskFilter",
    "ConsignmentFilter",
    "DeskProfileFilter",
    "DeskShiftFilter",
    "DistributorFilter",
    "EditionFilter",
    "LendingDeskFilter",
    "LoanFilter",
    "OpenVenueFilter",
    "PatronFilter",
    "PatronProfileFilter",
    "PrintingFilter",
    "PublisherFilter",
    "RepairTicketFilter",
    "SelfServeDeskFilter",
    "ShelfFilter",
    "VenueBadgeFilter",
    "VenueFilter",
    "VenueSponsorFilter",
    "VisibleBranchFilter",
)
