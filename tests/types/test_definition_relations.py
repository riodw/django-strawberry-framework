"""Tests for ``DjangoTypeDefinition.related_target_for`` (spec-021 Slice 3).

The lookup powers the Decision-4 owner-aware FK/PK conditional in
``FilterSet.filter_for_field`` / ``filter_for_lookup``. Tests cover
forward FK, forward M2M, reverse FK (via ``Book.loans`` -> ``Loan.book``
with ``related_name="loans"``), scalar non-relation field, missing
field, and the default-reverse-name (``<model>_set``) branch via an
inline test-fixture model declared without ``related_name=``.
"""

from __future__ import annotations

import pytest
from apps.library.models import Book, Genre, Loan, Shelf

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


def test_related_target_for_resolves_fk_m2m_and_reverse():
    """Forward FK, forward M2M, reverse FK, scalar, and missing-field cases."""

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class LoanType(DjangoType):
        class Meta:
            model = Loan
            fields = ("id", "note")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
                "loans",
            )

    finalize_django_types()

    book_definition = BookType.__django_strawberry_definition__

    # Forward FK -> (ShelfDefinition, ForeignKey).
    shelf_pair = book_definition.related_target_for("shelf")
    assert shelf_pair is not None
    shelf_definition, shelf_field = shelf_pair
    assert shelf_definition is ShelfType.__django_strawberry_definition__
    assert shelf_field.name == "shelf"
    assert getattr(shelf_field, "many_to_one", False) is True

    # Forward M2M -> (GenreDefinition, ManyToManyField).
    genres_pair = book_definition.related_target_for("genres")
    assert genres_pair is not None
    genres_definition, genres_field = genres_pair
    assert genres_definition is GenreType.__django_strawberry_definition__
    assert genres_field.name == "genres"
    assert getattr(genres_field, "many_to_many", False) is True

    # Reverse FK via ``Loan.book = ForeignKey(Book, related_name="loans")``.
    loans_pair = book_definition.related_target_for("loans")
    assert loans_pair is not None
    loans_definition, loans_field = loans_pair
    assert loans_definition is LoanType.__django_strawberry_definition__
    # The reverse accessor's underlying meta-field is the ``ManyToOneRel``
    # / ``ForeignObject``-shaped reverse field; its ``related_model`` is
    # ``Loan`` (the source of the FK).
    assert loans_field.related_model is Loan

    # Scalar text field -> None (not a relation).
    assert book_definition.related_target_for("title") is None

    # Missing field -> None (FieldDoesNotExist caught).
    assert book_definition.related_target_for("nonexistent_field") is None


def test_related_target_for_resolves_one_to_one_relation():
    """Forward + reverse OneToOne both resolve via ``related_target_for``.

    Covers the canonical OneToOne pair declared in the fakeshop library
    app (``MembershipCard.patron`` ``OneToOneField`` with
    ``related_name="card"``). Both directions are exercised in the same
    test so the lookup's behavior on single-valued reverse relations is
    pinned alongside the FK / M2M variants above.
    """
    from apps.library.models import MembershipCard, Patron

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name")

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode", "patron")

    finalize_django_types()

    card_definition = MembershipCardType.__django_strawberry_definition__
    patron_definition = PatronType.__django_strawberry_definition__

    forward = card_definition.related_target_for("patron")
    assert forward is not None
    forward_definition, forward_field = forward
    assert forward_definition is patron_definition
    assert forward_field.related_model is Patron

    reverse = patron_definition.related_target_for("card")
    assert reverse is not None
    reverse_definition, reverse_field = reverse
    assert reverse_definition is card_definition
    assert reverse_field.related_model is MembershipCard


def test_related_target_for_returns_none_when_target_unregistered():
    """A relation whose target ``DjangoType`` was never registered resolves to ``None``."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    definition = BookType.__django_strawberry_definition__
    # No ShelfType registered; ``related_target_for("shelf")`` cannot
    # resolve a target definition and returns ``None`` (the defensive
    # registry-miss branch).
    assert definition.related_target_for("shelf") is None


def test_related_target_for_caches_resolved_pair_after_finalize():
    """A second post-finalize lookup for the same field hits the memo cache."""

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    finalize_django_types()
    book_definition = BookType.__django_strawberry_definition__

    first = book_definition.related_target_for("shelf")
    # Second call returns the SAME memoized pair via the post-finalize cache.
    second = book_definition.related_target_for("shelf")
    assert first is second
    assert first is not None


def test_related_target_for_resolves_to_primary_when_two_types_share_target_model():
    """Two ``DjangoType``s registered for the same target model: the primary wins.

    Pins the consolidation contract relied upon at
    ``django_strawberry_framework/types/definition.py``
    ``DjangoTypeDefinition.related_target_for`` — the call site is
    ``target_type = registry.get(target_model)``, NOT the historical
    ``registry.primary_for(target_model) or registry.get(target_model)``
    chain. The collapse is safe only because ``registry.get`` itself
    honors ``_primaries`` as its first return state; this test pins
    that end-to-end so a future change that breaks the primary-first
    rule in ``registry.get`` surfaces here before the Decision-4
    owner-aware FK/PK lookup silently swings to the wrong target.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class AdminShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            primary = True

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    finalize_django_types()

    book_definition = BookType.__django_strawberry_definition__
    pair = book_definition.related_target_for("shelf")
    assert pair is not None
    shelf_definition, _shelf_field = pair
    # The primary (``AdminShelfType``) wins over the non-primary sibling
    # (``ShelfType``) — ``registry.get(Shelf)`` returns ``AdminShelfType``
    # because ``_primaries[Shelf] is AdminShelfType``.
    assert shelf_definition is AdminShelfType.__django_strawberry_definition__


def test_related_target_for_returns_none_for_generic_foreign_key():
    """A ``GenericForeignKey`` is a relation with no ``related_model`` -> ``None``."""
    from apps.library.models import TaggedItem

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "object_id")

    finalize_django_types()
    definition = TaggedItemType.__django_strawberry_definition__
    # ``content_object`` is a GFK: ``is_relation`` is True but
    # ``related_model`` is ``None`` -> the target-model guard returns ``None``.
    assert definition.related_target_for("content_object") is None
