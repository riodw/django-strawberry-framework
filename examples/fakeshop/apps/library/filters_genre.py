"""Cross-module fixture for the absolute-import-path ``RelatedFilter``.

``GenreFilter`` lives in its own module so the
``BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")``
declaration in ``filters.py`` exercises Layer-2 absolute-import-path
resolution per spec-027. The single same-module unqualified-name branch is
exercised by every other ``RelatedFilter("XFilter")`` declaration in
``filters.py``.
"""

from __future__ import annotations

from django_filters import CharFilter

from apps.library import models
from django_strawberry_framework.filters import FilterSet, RelatedFilter


class GenreFilter(FilterSet):
    """Genre filterset bound to ``GenreType`` at finalize phase 2.5.

    ``GenreType`` declares ``Meta.interfaces = (relay.Node,)`` so the
    spec-027 Decision 4 own-PK branch fires for ``id`` here: the resulting filter
    is ``GlobalIDFilter`` (not the scalar default), and the wire shape is
    a Strawberry Relay GlobalID string.

    ``without_book_titled`` is a declared ``exclude=True`` filter whose
    ``field_name`` walks the declared ``books`` hop: it drops a genre holding a
    book with that title among the books ``BookType.get_queryset`` lets the
    viewer see, so a book hidden from the viewer never drops its genre.
    """

    books = RelatedFilter("apps.library.filters.BookFilter", field_name="books")
    without_book_titled = CharFilter(field_name="books__title", exclude=True)

    class Meta:
        model = models.Genre
        fields = {"id": ["exact", "in"], "name": ["exact", "icontains"]}


__all__ = ("GenreFilter",)
