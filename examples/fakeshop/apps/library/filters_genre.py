"""Cross-module fixture for the absolute-import-path ``RelatedFilter`` (Slice 4).

``GenreFilter`` lives in its own module so the
``BookFilter.genres = RelatedFilter("apps.library.filters_genre.GenreFilter")``
declaration in ``filters.py`` exercises Layer-2 absolute-import-path
resolution per spec-021 L988 + L1052. The single same-module unqualified-
name branch is exercised by every other ``RelatedFilter("XFilter")``
declaration in ``filters.py``.
"""

from __future__ import annotations

from apps.library import models
from django_strawberry_framework.filters import FilterSet, RelatedFilter


class GenreFilter(FilterSet):
    """Genre filterset bound to ``GenreType`` at finalize phase 2.5.

    ``GenreType`` declares ``Meta.interfaces = (relay.Node,)`` so the
    Decision-4 own-PK branch fires for ``id`` here: the resulting filter
    is ``GlobalIDFilter`` (not the scalar default), and the wire shape is
    a Strawberry Relay GlobalID string.
    """

    books = RelatedFilter("apps.library.filters.BookFilter", field_name="books")

    class Meta:
        model = models.Genre
        fields = {
            "id": ["exact", "in"],
            "name": ["exact", "icontains"],
        }


__all__ = ("GenreFilter",)
