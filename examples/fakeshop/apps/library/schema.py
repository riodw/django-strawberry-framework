"""GraphQL schema for library acceptance coverage."""

from typing import Any

import strawberry
from strawberry import relay
from strawberry.types import Info

from apps.library import filters, filters_genre, forms, models, orders, orders_genre
from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoNodeField,
    DjangoNodesField,
    DjangoType,
    OptimizerHint,
)
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.orders import order_input_type

# Consumer ``resolver=`` helper exercising the shared field-wrapper
# ``Manager`` coercion line at
# ``django_strawberry_framework/utils/querysets.py::normalize_query_source #"source = source.all()"``.
# The README rule at ``examples/fakeshop/test_query/README.md #"Coverage rule"`` requires
# coverage lines reachable from a live ``/graphql/`` query to land here. Returns
# ``models.Branch.objects`` (a ``Manager``) - NOT ``.all()`` - so the field-
# wrapper's coercion fires per rev4 M1. The async equivalent
# (the same ``normalize_query_source`` line reached via
# ``django_strawberry_framework/utils/querysets.py::post_process_queryset_result_async``) is genuinely unreachable from the sync ``GraphQLView``
# mounted at ``/graphql/`` (Strawberry's sync execution rejects async resolvers
# with ``RuntimeError: GraphQL execution failed to complete synchronously``),
# so the async ``Manager`` coercion stays in ``tests/test_list_field.py`` per
# the README's "genuinely unreachable" fallback.


def _branches_manager_resolver(root: Any, info: Info) -> Any:
    return models.Branch.objects


def _user_is_staff(info: Info) -> bool:
    """Unwrap ``info.context`` -> request -> user and report ``is_staff``.

    The shared staff-bypass predicate for every library ``get_queryset``
    visibility hook (Shelf / Branch / Book); hoisted so the
    context-unwrap dance lives in exactly one place.
    """
    context = getattr(info, "context", None)
    request = getattr(context, "request", None) or context
    user = getattr(request, "user", None)
    return user is not None and getattr(user, "is_staff", False)


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
    """Book declared before Shelf and Genre to exercise finalization.

    Relay-Node-shaped AND ``get_queryset``-filtered: the live hidden-row
    ``null`` eligible type (spec-032 Decision 12).
    """

    @classmethod
    def get_queryset(cls, queryset: Any, info: Info) -> Any:
        """Hide ``circulation_status="repair"`` books from non-staff requests.

        The ``ShelfType`` ``topic="secret"`` pattern, staff bypass included
        (spec-032 Decision 12).
        """
        if _user_is_staff(info):
            return queryset
        return queryset.exclude(circulation_status=models.Book.CirculationStatus.REPAIR)

    class Meta:
        model = models.Book
        # ``primary = True`` makes ``BookType`` the relation-resolution target
        # for ``library.Book`` so the acceptance-only ``NullabilityOverrideBookType``
        # secondary below can register on the same model without ambiguity
        # (spec-029 Decision 5 / Edge cases - exactly one type per model is primary).
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
        interfaces = (relay.Node,)
        filterset_class = filters.BookFilter
        orderset_class = orders.BookOrder


class NullabilityOverrideBookType(DjangoType):
    """Acceptance-only secondary ``Book`` type proving the nullability overrides.

    ``nullable_overrides = ("title",)`` flips the ``NOT NULL`` ``title`` column
    from its native ``String!`` to ``String``; ``required_overrides = ("subtitle",)``
    flips the ``null=True`` ``subtitle`` column from its native ``String`` to
    ``String!`` - both without touching the Django column (spec-029 Slice 3).
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
    def get_queryset(cls, queryset: Any, info: Info) -> Any:
        """Hide ``topic="secret"`` shelves from non-staff requests (H1-rev4).

        Spec-021 L1053: the nested-``RelatedFilter`` visibility-scoping
        contract relies on the target type's ``get_queryset`` hiding
        sensitive rows before the filter clause sees them. Staff requests
        bypass the gate.
        """
        if _user_is_staff(info):
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
    def get_queryset(cls, queryset: Any, info: Info) -> Any:
        """Hide ``city="restricted"`` branches from anonymous requests (M1-rev8).

        Spec-021 L1056: the root-resolver ordering contract relies on
        ``BranchType.get_queryset(queryset, info)`` running BEFORE
        ``BranchFilter.apply_sync(...)``. Staff requests bypass the gate.
        """
        if _user_is_staff(info):
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
    """Patron with nullable reverse OneToOne card and reverse FK loans.

    Uses an allow-list ``Meta.fields`` tuple. ``primary = True`` keeps this type the
    relation-resolution target (``Loan.patron`` / ``MembershipCard.patron`` resolve
    here) now that ``PublicPatronType`` registers a second, ``Meta.exclude``-shaped
    view on the same model.
    """

    class Meta:
        model = models.Patron
        primary = True
        fields = (
            "id",
            "name",
            "lifetime_fines_cents",
            "card",
            "loans",
        )
        filterset_class = filters.PatronFilter
        orderset_class = orders.PatronOrder


class PublicPatronType(DjangoType):
    """Secondary ``primary=False`` Patron view selected via ``Meta.exclude``.

    Where ``PatronType`` uses an allow-list ``Meta.fields`` tuple, this type uses a
    deny-list ``Meta.exclude``: it starts from every Patron field and drops the
    sensitive ``email`` (PII) and ``lifetime_fines_cents`` (internal financial)
    columns. The two coexist on one model so the schema shows both selection
    mechanics side by side - ``fields`` (allow-list) vs ``exclude`` (deny-list).
    ``Meta.fields`` and ``Meta.exclude`` are mutually exclusive, so each mechanic
    needs its own type.

    ``exclude`` selects over ``model._meta.get_fields()``, so the kept set still
    includes the reverse relations (``card`` / ``loans``); only the two named
    scalar columns are removed from the GraphQL type. ``primary = False`` leaves
    ``PatronType`` the relation-resolution target.
    """

    class Meta:
        model = models.Patron
        primary = False
        exclude = ("email", "lifetime_fines_cents")


@strawberry.type
class Query:
    """Library acceptance root fields."""

    all_library_branches_via_list_field: list[BranchType] = DjangoListField(
        BranchType,
    )

    # Nullable-outer variant: the consumer ``list[BranchType] | None`` class
    # annotation (NOT a constructor argument) drives the rendered GraphQL type
    # to ``[BranchType!]`` - a nullable list of non-null items. ``DjangoListField``
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
    def all_library_branches_eager_eval(self, info: strawberry.Info) -> list[BranchType]:
        # G1 (spec-035): the evaluated-queryset guard, dogfooded. A consumer that
        # evaluates its queryset before returning it - here an ``if not queryset``
        # empty-guard whose ``bool(...)`` populates ``_result_cache`` - must NOT be
        # re-executed by the optimizer. ``DjangoOptimizerExtension._optimize`` sees
        # the populated cache and returns the queryset unchanged instead of cloning
        # it and applying ``.only(...)``, which would double the SQL (one logical
        # read -> two queries). Pinned live in ``test_query/test_library_api.py``
        # (``test_library_evaluated_queryset_not_re_executed_over_http``).
        queryset = BranchType.get_queryset(models.Branch.objects.order_by("id"), info)
        if not queryset:  # evaluates the queryset -> _result_cache populated
            return []
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
    def all_library_genres_consumer_descendant_prefetch(self) -> list[GenreType]:
        # B8 collision surface: a consumer descendant prefetch
        # (``books__loans``) overlaps the optimizer's own Genre -> books ->
        # loans prefetch plan. The optimizer must reconcile the two rather than
        # raise "'books' lookup was already seen with a different queryset".
        return models.Genre.objects.prefetch_related("books__loans").order_by("id")

    @strawberry.field
    def all_library_genres_consumer_exact_plus_descendant_prefetch(self) -> list[GenreType]:
        # B8 follow-up: the consumer declares BOTH the exact relation
        # (``books``) and a descendant (``books__loans``); both must reconcile
        # with the optimizer plan without colliding.
        return models.Genre.objects.prefetch_related("books", "books__loans").order_by("id")

    @strawberry.field
    def all_library_nullability_override_books(self) -> list[NullabilityOverrideBookType]:
        # ``required_overrides = ("subtitle",)`` declares ``subtitle`` as
        # ``String!`` on this type, but the column is ``null=True`` and fakeshop
        # seeds ``subtitle=None`` rows - so exclude null-subtitle rows to keep
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

    # Root Relay refetch fields (spec-032 Decision 12), imported from the
    # package public surface. The annotations are the supported
    # nullable-by-contract spellings (Decision 5: resolve_node dispatches
    # required=False unconditionally).
    node: relay.Node | None = DjangoNodeField()
    nodes: list[relay.Node | None] = DjangoNodesField()
    genre: GenreType | None = DjangoNodeField(GenreType)

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
    def all_library_public_patrons(self) -> list[PublicPatronType]:
        """Root field for the ``Meta.exclude`` deny-list view (see ``PublicPatronType``)."""
        return models.Patron.objects.order_by("id")

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


# --------------------------------------------------------------------------- #
# Write surface - earns the raw-pk relation visibility + ``to_field_name``
# framework branches over a LIVE ``/graphql`` request (the
# ``test_query/README.md`` discipline). ``Shelf`` relations target the non-Relay
# ``BranchType`` primary, so their inputs are raw pk (single FK + multi M2M); the
# decode resolves each through ``BranchType.get_queryset`` (which hides
# ``city="restricted"`` from non-staff). These writes isolate the relation DECODE,
# not the write-auth seam, so they open the write to any caller via the
# framework-native ``permission_classes = []`` allow-any opt-out (not a hand-rolled
# allow-all class): an anonymous caller can write but cannot attach a hidden branch.
# --------------------------------------------------------------------------- #


class CreateShelfViaForm(DjangoModelFormMutation):
    """Create a ``Shelf`` via ``ShelfRelationsForm`` - the FORM raw-pk relation path.

    ``branch`` (raw-pk FK) + ``alt_branches`` (raw-pk M2M) target the non-Relay
    ``BranchType``; the form decoder resolves each through
    ``apply_type_visibility_sync(BranchType.get_queryset(...))`` (single + multi
    visibility) and converts ``branch`` by ``to_field_name="name"``.
    """

    class Meta:
        form_class = forms.ShelfRelationsForm
        operation = "create"
        permission_classes = []


class CreateShelf(DjangoMutation):
    """Create a ``Shelf`` via the model pipeline - the MODEL raw-pk relation path.

    The ``branch`` / ``alt_branches`` raw-pk inputs route through
    ``mutations/resolvers.py::_raw_pk_relation_error`` - the model-path twin of the
    form decoder's visibility-on-the-raw-pk-branch fix.
    """

    class Meta:
        model = models.Shelf
        operation = "create"
        fields = ("code", "branch", "alt_branches")
        permission_classes = []


class UpdateBookViaForm(DjangoModelFormMutation):
    """Update a ``Book`` via ``BookGenresModelForm`` - the live FORM partial-update M2M path.

    ``BookType`` is Relay-Node, so the update ``id`` is a decodable ``GlobalID`` (a
    non-Relay type supports create only). A ``title``-only update OMITS the required
    ``genres`` M2M, so it is reconstructed from the located row
    (``forms/resolvers.py::_reconstruct_partial_data`` - the M2M branch, previously
    package-only) rather than cleared. ``permission_classes = []`` keeps write-auth out
    of the path under test; ``BookType.get_queryset`` still scopes the located row.
    """

    class Meta:
        form_class = forms.BookGenresModelForm
        operation = "update"
        permission_classes = []


@strawberry.type
class Mutation:
    """Library write surface (live raw-pk relation visibility + ``to_field_name``)."""

    create_shelf_via_form = DjangoMutationField(CreateShelfViaForm)
    create_shelf = DjangoMutationField(CreateShelf)
    update_book_via_form = DjangoMutationField(UpdateBookViaForm)


__all__ = ("Mutation", "Query")
