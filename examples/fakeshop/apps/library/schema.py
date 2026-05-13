"""GraphQL schema for library acceptance coverage."""

import strawberry
from strawberry import relay

from apps.library import models
from django_strawberry_framework import DjangoType, OptimizerHint

# The DjangoType declaration order is intentionally awkward. Several
# relation targets are declared after their consumers so the example schema
# keeps exercising pending-relation resolution through the real app import
# path. Do not reorder these classes unless the tests that pin this contract
# are updated at the same time.


class LoanType(DjangoType):
    """Loan declared before Book and Patron to exercise finalization."""

    class Meta:
        model = models.Loan
        fields = ("id", "note", "book", "patron")
        optimizer_hints = {
            "book": OptimizerHint.prefetch_related(),
            "patron": OptimizerHint.SKIP,
        }


class BookType(DjangoType):
    """Book declared before Shelf and Genre to exercise finalization."""

    class Meta:
        model = models.Book
        fields = ("id", "title", "subtitle", "circulation_status", "shelf", "genres", "loans")


class ShelfType(DjangoType):
    """Shelf declared before Branch to exercise FK finalization."""

    class Meta:
        model = models.Shelf
        fields = ("id", "code", "topic", "branch", "books")


class MembershipCardType(DjangoType):
    """Card declared before Patron to exercise OneToOne finalization."""

    class Meta:
        model = models.MembershipCard
        fields = ("id", "barcode", "patron")


class GenreType(DjangoType):
    """Genre with reverse M2M books."""

    class Meta:
        model = models.Genre
        fields = ("id", "name", "books")
        interfaces = (relay.Node,)


class BranchType(DjangoType):
    """Branch parent with reverse FK shelves."""

    @strawberry.field
    def shelves(self) -> list[ShelfType]:
        """Consumer-authored relation resolver used by HTTP override tests."""
        return list(self.shelves.order_by("-code"))

    class Meta:
        model = models.Branch
        fields = ("id", "name", "city", "shelves")


class PatronType(DjangoType):
    """Patron with nullable reverse OneToOne card and reverse FK loans."""

    class Meta:
        model = models.Patron
        fields = ("id", "name", "card", "loans")


@strawberry.type
class Query:
    """Library acceptance root fields."""

    @strawberry.field
    def all_library_branches(self) -> list[BranchType]:
        return models.Branch.objects.order_by("id")

    @strawberry.field
    def all_library_shelves(self) -> list[ShelfType]:
        return models.Shelf.objects.order_by("id")

    @strawberry.field
    def all_library_books(self) -> list[BookType]:
        return models.Book.objects.order_by("id")

    @strawberry.field
    def all_library_prefetched_books(self) -> list[BookType]:
        return models.Book.objects.select_related("shelf").prefetch_related("genres").order_by("id")

    @strawberry.field
    def all_library_genres(self) -> list[GenreType]:
        return models.Genre.objects.order_by("id")

    @strawberry.field
    def all_library_patrons(self) -> list[PatronType]:
        return models.Patron.objects.order_by("id")

    @strawberry.field
    def all_library_membership_cards(self) -> list[MembershipCardType]:
        return models.MembershipCard.objects.order_by("id")

    @strawberry.field
    def all_library_loans(self) -> list[LoanType]:
        return models.Loan.objects.order_by("id")


__all__ = ("Query",)
