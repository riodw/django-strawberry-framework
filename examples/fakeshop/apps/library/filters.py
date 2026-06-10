"""FilterSet declarations for the library acceptance app (Slice 4).

Five filtersets mirror the relation shape ``apps.library.schema`` exposes
through the live ``/graphql/`` endpoint. Inter-filterset references use
the same-module unqualified-name form (e.g. ``RelatedFilter("ShelfFilter")``)
so the lazy-resolution Layer-2 prefix-with-owner branch is exercised end
to end; the ``BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")``
declaration deliberately uses the absolute-import-path form so the
Layer-2 ``import_string`` first-attempt branch is also exercised (spec
L988 + L1052).

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

    Spec-021 L1054 (H4-rev8): a plain ``String!`` declared filter whose
    custom validator raises ``forms.ValidationError("missing @",
    code="missing_at_sign")``. Used by ``PatronFilter.email_must_have_at_sign``
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
    spec-021 L988 + L1052.
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
        fields = {"id": ["exact", "in"], "note": ["exact", "icontains"]}


class PatronFilter(FilterSet):
    """Patron filterset bound to ``PatronType`` at finalize phase 2.5.

    ``email_must_have_at_sign`` is the declared custom filter
    spec-021 H4-rev8 (L1054) names. The underlying form field carries
    ``_validate_email_must_have_at_sign`` as a validator so an input
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
        # an ``@`` sign per spec-021 L1054.
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


__all__ = (
    "BookFilter",
    "BranchFilter",
    "LoanFilter",
    "PatronFilter",
    "ShelfFilter",
)
