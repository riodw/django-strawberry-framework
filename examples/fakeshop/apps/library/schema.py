"""GraphQL schema for library acceptance coverage."""

from typing import Any

import strawberry
from strawberry import relay
from strawberry.types import Info

from apps.library import filters, filters_genre, models, orders, orders_genre
from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    DjangoType,
    OptimizerHint,
)
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.orders import order_input_type

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
        orderset_class = orders.LoanOrder
        optimizer_hints = {"book": OptimizerHint.prefetch_related(), "patron": OptimizerHint.SKIP}


class BookType(DjangoType):
    """Book declared before Shelf and Genre to exercise finalization."""

    class Meta:
        model = models.Book
        # ``primary = True`` makes ``BookType`` the relation-resolution target
        # for ``library.Book`` so the acceptance-only ``NullabilityOverrideBookType``
        # secondary below can register on the same model without ambiguity
        # (spec-029 Decision 5 / Edge cases — exactly one type per model is primary).
        primary = True
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
        orderset_class = orders.BookOrder


class NullabilityOverrideBookType(DjangoType):
    """Acceptance-only secondary ``Book`` type proving the nullability overrides.

    ``nullable_overrides = ("title",)`` flips the ``NOT NULL`` ``title`` column
    from its native ``String!`` to ``String``; ``required_overrides = ("subtitle",)``
    flips the ``null=True`` ``subtitle`` column from its native ``String`` to
    ``String!`` — both without touching the Django column (spec-029 Slice 3).
    ``Meta.primary = False`` keeps ``BookType`` the relation target; this type
    stays reverse-discoverable via the registry. The dedicated root resolver
    (``Query.all_library_nullability_override_books``) returns only rows with a
    non-null ``subtitle`` so the forced ``subtitle = String!`` contract holds at
    the query boundary (``required_overrides`` changes the GraphQL contract, not
    the data).
    """

    class Meta:
        model = models.Book
        primary = False
        fields = ("id", "title", "subtitle")
        nullable_overrides = ("title",)
        required_overrides = ("subtitle",)


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
        orderset_class = orders.ShelfOrder


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
        orderset_class = orders_genre.GenreOrder
        connection = {"total_count": True}


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
        orderset_class = orders.BranchOrder


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
        orderset_class = orders.PatronOrder


@strawberry.type
class Query:
    """Library acceptance root fields."""

    all_library_branches_via_list_field: list[BranchType] = DjangoListField(
        BranchType,
    )

    # Nullable-outer variant: the consumer ``list[BranchType] | None`` class
    # annotation (NOT a constructor argument) drives the rendered GraphQL type
    # to ``[BranchType!]`` — a nullable list of non-null items. ``DjangoListField``
    # itself has no outer-nullability branch; Strawberry reads the annotation, so
    # this pins that the field factory leaves the consumer's annotation intact.
    all_library_branches_via_list_field_nullable: list[BranchType] | None = DjangoListField(
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
        order_by: list[order_input_type(orders.BranchOrder)] | None = None,
    ) -> list[BranchType]:
        queryset = BranchType.get_queryset(models.Branch.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.BranchFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.BranchOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_library_shelves(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.ShelfFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.ShelfOrder)] | None = None,
    ) -> list[ShelfType]:
        queryset = ShelfType.get_queryset(models.Shelf.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.ShelfFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ShelfOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_library_books(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.BookFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.BookOrder)] | None = None,
    ) -> list[BookType]:
        queryset = BookType.get_queryset(models.Book.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.BookFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.BookOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_library_prefetched_books(self) -> list[BookType]:
        return (
            models.Book.objects.select_related("shelf").prefetch_related("genres").order_by("id")
        )

    @strawberry.field
    def all_library_nullability_override_books(self) -> list[NullabilityOverrideBookType]:
        # ``required_overrides = ("subtitle",)`` declares ``subtitle`` as
        # ``String!`` on this type, but the column is ``null=True`` and fakeshop
        # seeds ``subtitle=None`` rows — so exclude null-subtitle rows to keep
        # the non-null GraphQL contract true at the boundary, ordered by id for
        # deterministic responses (spec-029 Slice 3 / Edge cases).
        return models.Book.objects.exclude(subtitle__isnull=True).order_by("id")

    @strawberry.field
    def all_library_genres(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters_genre.GenreFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders_genre.GenreOrder)] | None = None,
    ) -> list[GenreType]:
        queryset = GenreType.get_queryset(models.Genre.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters_genre.GenreFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders_genre.GenreOrder.apply_sync(order_by, queryset, info)
        return queryset

    # Relay connection field over the Relay-Node-shaped ``GenreType`` (spec-030
    # Slice 4 / Decision 14). Additive alongside the ``all_library_genres`` list
    # resolver above so both surfaces stay tested; ``filter:`` / ``orderBy:`` and
    # the opt-in ``totalCount`` are all Meta-derived (Decision 5) from
    # ``GenreType.Meta`` (``filterset_class`` / ``orderset_class`` /
    # ``connection = {"total_count": True}``). Imported from the public surface.
    all_library_genres_connection: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)

    @strawberry.field
    def all_library_patrons(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.PatronFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.PatronOrder)] | None = None,
    ) -> list[PatronType]:
        queryset = PatronType.get_queryset(models.Patron.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.PatronFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.PatronOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_library_membership_cards(self) -> list[MembershipCardType]:
        return models.MembershipCard.objects.order_by("id")

    @strawberry.field
    def all_library_loans(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.LoanFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.LoanOrder)] | None = None,
    ) -> list[LoanType]:
        queryset = LoanType.get_queryset(models.Loan.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.LoanFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.LoanOrder.apply_sync(order_by, queryset, info)
        return queryset


__all__ = ("Query",)
