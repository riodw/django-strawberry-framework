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

    # TODO(spec-016, Slice 4 — Decision 9 add-only posture, rev2 M1 + rev4 H3):
    # add a NEW sibling root field exercising the ``DjangoListField``
    # default-resolver code path. Do NOT replace ``all_library_branches``
    # below — its ``order_by("id")`` is depended on by
    # ``test_library_relation_override_shapes_http_response_data``. The
    # add-only posture is an intentional departure from the KANBAN card's
    # "replacing one of the hand-rolled ``all_library_*`` resolvers" wording
    # (rev4 H3); the past-tense card body is rewritten on Done.
    #
    #     all_library_branches_via_list_field: list[BranchType] = DjangoListField(
    #         BranchType,
    #     )
    #
    # The Slice 4 HTTP test
    # ``test_library_branches_via_djangolistfield_optimized_nested_selection``
    # in ``examples/fakeshop/test_query/test_library_api.py`` queries
    # ``{ allLibraryBranchesViaListField { id name shelves { id code } } }``
    # against ``/graphql/`` and asserts ``prefetch_related("shelves")`` was
    # planned (via ``assertNumQueries`` / SQL-sniffer).

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
