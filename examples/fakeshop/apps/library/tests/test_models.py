"""Library model tests for __str__ output and computed field behavior.

Mirrors the products model tests so the library app carries its own coverage:
__str__ rendering, forward/reverse relation traversal, and a uniqueness rule.
"""

import pytest
from django.db import IntegrityError, transaction

from apps.library.models import Book, Branch, Genre, Loan, MembershipCard, Patron, Shelf


@pytest.mark.django_db
def test_str_representations_and_relations():
    branch = Branch.objects.create(name="Central", city="Metropolis")
    shelf = Shelf.objects.create(code="A-1", branch=branch, topic="scifi")
    genre = Genre.objects.create(name="Speculative")
    book = Book.objects.create(title="Kindred", shelf=shelf)
    book.genres.add(genre)
    patron = Patron.objects.create(name="Ada", email="ada@example.com")
    card = MembershipCard.objects.create(patron=patron, barcode="BC-001")
    loan = Loan.objects.create(book=book, patron=patron)

    assert str(branch) == "Central"
    assert str(shelf) == "A-1"
    assert str(genre) == "Speculative"
    assert str(book) == "Kindred"
    assert str(patron) == "Ada"
    assert str(card) == "BC-001"
    assert str(loan) == "Kindred to Ada"

    # Relations resolve in both directions.
    assert list(branch.shelves.all()) == [shelf]
    assert list(shelf.books.all()) == [book]
    assert list(book.genres.all()) == [genre]
    assert list(genre.books.all()) == [book]
    assert patron.card == card
    assert list(book.loans.all()) == [loan]
    assert list(patron.loans.all()) == [loan]


@pytest.mark.django_db
def test_book_title_unique_per_shelf():
    branch = Branch.objects.create(name="B1")
    shelf = Shelf.objects.create(code="X", branch=branch)
    Book.objects.create(title="Dune", shelf=shelf)
    with pytest.raises(IntegrityError), transaction.atomic():
        Book.objects.create(title="Dune", shelf=shelf)
