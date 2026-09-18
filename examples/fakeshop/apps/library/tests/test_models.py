"""Library model tests for string rendering, relation traversal, and per-shelf title uniqueness.

Mirrors the products model tests so the library app carries its own coverage:
__str__ rendering, forward/reverse relation traversal, and a uniqueness rule.
"""

import pytest
from django.db import IntegrityError, transaction

from apps.library.models import (
    Book,
    Branch,
    BranchNote,
    Genre,
    Loan,
    MembershipCard,
    Patron,
    ProxyBranch,
    Shelf,
)


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


@pytest.mark.django_db
def test_branch_note_str_and_proxy_targeted_relation():
    """``BranchNote.branch`` is declared to the ``ProxyBranch`` proxy, not ``Branch``.

    The forward side resolves to a proxy instance and the reverse ``notes``
    accessor hangs off the proxy, while the rows live in the concrete
    ``Branch`` table - the table identity the prefetch-child seal proves a
    relation by.
    """
    branch = ProxyBranch.objects.create(name="Proxy Central", city="Boston")
    note = BranchNote.objects.create(branch=branch, body="shelving audit")

    assert str(note) == "shelving audit"
    assert BranchNote._meta.get_field("branch").related_model is ProxyBranch
    assert note.branch == branch
    assert list(branch.notes.all()) == [note]
    # The proxy reads the concrete parent's table, so the same row is a Branch.
    assert Branch.objects.get(pk=branch.pk).name == "Proxy Central"
