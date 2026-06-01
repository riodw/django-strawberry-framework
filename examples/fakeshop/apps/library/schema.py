"""GraphQL schema for library acceptance coverage."""

from typing import Any

import strawberry
from strawberry import relay
from strawberry.types import Info

from apps.library import filters, filters_genre, models
from django_strawberry_framework import DjangoListField, DjangoType, OptimizerHint
from django_strawberry_framework.filters import filter_input_type

# TODO(spec-028-orders-0_0_8 Slice 4): Import ``orders`` / ``orders_genre`` and
# ``order_input_type`` once the order subsystem ships.
# Pseudocode:
#   - wire each ``DjangoType.Meta`` to the matching ``Meta.orderset_class``:
#     LoanType -> LoanOrder, BookType -> BookOrder, ShelfType -> ShelfOrder,
#     GenreType -> GenreOrder, BranchType -> BranchOrder, PatronType -> PatronOrder.
#   - keep ``MembershipCardType`` unwired unless a live order test needs it.
#   - root resolvers call ``get_queryset`` first, optional ``Filter.apply_sync``
#     second, and optional ``Order.apply_sync`` third.

# Consumer ``resolver=`` helper exercising the ``_post_process_consumer_sync``
# ``Manager`` coercion line at
# ``django_strawberry_framework/list_field.py::_post_process_consumer_sync #"result = result.all()"``.
# The README rule at ``examples/fakeshop/test_query/README.md #"Coverage rule"`` requires
# coverage lines reachable from a live ``/graphql/`` query to land here. Returns
# ``models.Branch.objects`` (a ``Manager``) — NOT ``.all()`` — so the field-
# wrapper's coercion fires per rev4 M1. The async equivalent
# (``django_strawberry_framework/list_field.py::_post_process_consumer_async #"result = result.all()"``) is genuinely unreachable from the sync ``GraphQLView``
# mounted at ``/graphql/`` (Strawberry's sync execution rejects async resolvers
# with ``RuntimeError: GraphQL execution failed to complete synchronously``),
# so the async ``Manager`` coercion stays in ``tests/test_list_field.py`` per
# the README's "genuinely unreachable" fallback.


def _branches_manager_resolver(root: Any, info: Info) -> Any:  # noqa: ARG001
    return models.Branch.objects


# The DjangoType declaration order is intentionally awkward. Several
# relation targets are declared after their consumers so the example schema
# keeps exercising pending-relation resolution through the real app import
# path. Do not reorder these classes unless the tests that pin this contract
# are updated at the same time.


class LoanType(DjangoType):
    """Loan declared before Book and Patron to exercise finalization."""

    class Meta:
        model = models.Loan
        fields = (
            "id",
            "note",
            "book",
            "patron",
        )
        filterset_class = filters.LoanFilter
        optimizer_hints = {"book": OptimizerHint.prefetch_related(), "patron": OptimizerHint.SKIP}


class BookType(DjangoType):
    """Book declared before Shelf and Genre to exercise finalization."""

    class Meta:
        model = models.Book
        fields = (
            "id",
            "title",
            "subtitle",
            "circulation_status",
            "shelf",
            "genres",
            "loans",
        )
        filterset_class = filters.BookFilter


class ShelfType(DjangoType):
    """Shelf declared before Branch to exercise FK finalization."""

    @classmethod
    def get_queryset(cls, queryset: Any, info: Info) -> Any:  # noqa: ARG003
        """Hide ``topic="secret"`` shelves from non-staff requests (H1-rev4).

        Spec-021 L1053: the nested-``RelatedFilter`` visibility-scoping
        contract relies on the target type's ``get_queryset`` hiding
        sensitive rows before the filter clause sees them. Staff requests
        bypass the gate.
        """
        context = getattr(info, "context", None)
        request = getattr(context, "request", None) or context
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_staff", False):
            return queryset
        return queryset.exclude(topic="secret")

    class Meta:
        model = models.Shelf
        fields = (
            "id",
            "code",
            "topic",
            "branch",
            "books",
        )
        filterset_class = filters.ShelfFilter


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
        filterset_class = filters_genre.GenreFilter


class BranchType(DjangoType):
    """Branch parent with reverse FK shelves."""

    @strawberry.field
    def shelves(self) -> list["ShelfType"]:
        """Consumer-authored relation resolver used by HTTP override tests."""
        return list(self.shelves.order_by("-code"))

    @classmethod
    def get_queryset(cls, queryset: Any, info: Info) -> Any:  # noqa: ARG003
        """Hide ``city="restricted"`` branches from anonymous requests (M1-rev8).

        Spec-021 L1056: the root-resolver ordering contract relies on
        ``BranchType.get_queryset(queryset, info)`` running BEFORE
        ``BranchFilter.apply_sync(...)``. Staff requests bypass the gate.
        """
        context = getattr(info, "context", None)
        request = getattr(context, "request", None) or context
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_staff", False):
            return queryset
        return queryset.exclude(city="restricted")

    class Meta:
        model = models.Branch
        fields = (
            "id",
            "name",
            "city",
            "shelves",
        )
        filterset_class = filters.BranchFilter


class PatronType(DjangoType):
    """Patron with nullable reverse OneToOne card and reverse FK loans."""

    class Meta:
        model = models.Patron
        fields = (
            "id",
            "name",
            "lifetime_fines_cents",
            "card",
            "loans",
        )
        filterset_class = filters.PatronFilter


@strawberry.type
class Query:
    """Library acceptance root fields."""

    # TODO(spec-028-orders-0_0_8 Slice 4): Add ``order_by`` arguments to the
    # live root resolvers that participate in the 14 order acceptance tests.
    # Pseudocode:
    #   - annotate as ``order_by: list[order_input_type(orders.<Name>Order)] | None``.
    #   - preserve the existing ``filter: filter_input_type(...) | None`` argument.
    #   - apply in order: ``Type.get_queryset(...)``, optional filter, optional order.
    #   - leave ``DjangoListField`` ordering integration deferred to ``0.0.9``.

    all_library_branches_via_list_field: list[BranchType] = DjangoListField(
        BranchType,
    )

    all_library_branches_via_list_field_manager_resolver: list[BranchType] = DjangoListField(
        BranchType,
        resolver=_branches_manager_resolver,
    )

    @strawberry.field
    def all_library_branches(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.BranchFilter) | None = None,  # noqa: A002
    ) -> list[BranchType]:
        queryset = BranchType.get_queryset(models.Branch.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.BranchFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_library_shelves(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.ShelfFilter) | None = None,  # noqa: A002
    ) -> list[ShelfType]:
        queryset = ShelfType.get_queryset(models.Shelf.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.ShelfFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_library_books(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.BookFilter) | None = None,  # noqa: A002
    ) -> list[BookType]:
        queryset = BookType.get_queryset(models.Book.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.BookFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_library_prefetched_books(self) -> list[BookType]:
        return models.Book.objects.select_related("shelf").prefetch_related("genres").order_by("id")

    @strawberry.field
    def all_library_genres(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters_genre.GenreFilter) | None = None,  # noqa: A002
    ) -> list[GenreType]:
        queryset = GenreType.get_queryset(models.Genre.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters_genre.GenreFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_library_patrons(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.PatronFilter) | None = None,  # noqa: A002
    ) -> list[PatronType]:
        queryset = PatronType.get_queryset(models.Patron.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.PatronFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_library_membership_cards(self) -> list[MembershipCardType]:
        return models.MembershipCard.objects.order_by("id")

    @strawberry.field
    def all_library_loans(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.LoanFilter) | None = None,  # noqa: A002
    ) -> list[LoanType]:
        queryset = LoanType.get_queryset(models.Loan.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.LoanFilter.apply_sync(filter, queryset, info)
        return queryset


__all__ = ("Query",)
