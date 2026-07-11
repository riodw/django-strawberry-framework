"""GraphQL schema for library acceptance coverage."""

from typing import Any

import strawberry
from strawberry import relay
from strawberry.types import Info

from apps.library import filters, filters_genre, forms, models, orders, orders_genre, serializers

# ``SerializerMutation`` is imported BY NAME (never via star import): the root ``__all__``
# omits it while DRF is a soft dependency (F1), so the root ``__getattr__`` resolves it on
# demand. DRF is present in the test context, so this import succeeds.
from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoFormMutation,
    DjangoListField,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoNodeField,
    DjangoNodesField,
    DjangoType,
    NestedSerializerConfig,
    OptimizerHint,
    SerializerMutation,
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


@strawberry.interface
class Named:
    """Consumer-defined non-Relay ``@strawberry.interface`` (spec-015 demonstration).

    ``Meta.interfaces`` accepts ANY Strawberry interface, not only ``relay.Node``.
    ``Branch`` / ``Genre`` / ``Patron`` each carry a unique ``name`` column, so
    ``BranchType`` / ``GenreType`` / ``PatronType`` list ``Named`` in ``Meta.interfaces``
    (``GenreType`` alongside ``relay.Node``): the package injects ``Named`` into each
    type's MRO with NO Relay resolver wiring (it is not ``relay.Node``), the SDL renders
    ``implements ... & Named``, and ``name`` resolves from the model column through the
    normal auto-conversion. The ``namedLibraryRecords`` root field returns a polymorphic
    ``list[Named]`` mixing all three so a client selects the shared ``name`` across them,
    with ``__typename`` discriminating the concrete type.
    """

    name: str


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
        interfaces = (relay.Node, Named)
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
        interfaces = (Named,)
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
        interfaces = (Named,)
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

    This is also the example's ``Meta.name`` / ``Meta.description`` demonstration:
    a public-facing secondary view is exactly where renaming the GraphQL type
    (``name = "PublicPatron"``, decoupled from the ``PublicPatronType`` class name)
    and attaching a schema-visible ``description`` is natural. Both surface through
    introspection; renaming a secondary is safe because a non-Relay type carries no
    model-anchored ``GlobalID`` to invalidate.
    """

    class Meta:
        model = models.Patron
        primary = False
        exclude = ("email", "lifetime_fines_cents")
        name = "PublicPatron"
        description = (
            "A patron projection with PII (email) and financial (lifetime fines) columns removed."
        )


class IssueType(DjangoType):
    """The keyset-cursor (``Meta.cursor_field``) acceptance type.

    ``cursor_field = ("-number", "id")`` makes every connection over issues
    KEYSET-MODE: newest-number-first ordering (the canonical feed shape and
    the mixed-direction seek arm - DESC ordering column, ASC pk tiebreak),
    value-encoded signed cursors that survive inserts/deletes, offset
    cursors rejected. ``get_queryset`` hides embargoed issues from
    non-staff viewers - the permission-aware cursor-decode substrate: a
    cursor minted under staff visibility replays for anonymous viewers over
    ONLY the rows they can see.
    """

    @classmethod
    def get_queryset(cls, queryset: Any, info: Info) -> Any:
        """Hide ``embargoed=True`` issues from non-staff requests."""
        if _user_is_staff(info):
            return queryset
        return queryset.exclude(embargoed=True)

    class Meta:
        model = models.Issue
        fields = (
            "id",
            "number",
            "title",
            "embargoed",
            "periodical",
        )
        interfaces = (relay.Node,)
        cursor_field = ("-number", "id")
        connection = {"total_count": True}
        orderset_class = orders.IssueOrder


class PeriodicalType(DjangoType):
    """Parent of the keyset acceptance type - its ``issuesConnection`` nested
    connection windows with keyset value seeks (uniform value-position across
    every parent partition)."""

    class Meta:
        model = models.Periodical
        fields = ("id", "name", "issues")
        interfaces = (relay.Node,)
        relation_shapes = {"issues": "connection"}
        orderset_class = orders.PeriodicalOrder


@strawberry.type
class Query:
    """Library acceptance root fields."""

    # Keyset-cursor (Meta.cursor_field) acceptance surface: the root
    # connection mints/decodes value cursors through the framework slicer;
    # the periodicals root reaches the NESTED issuesConnection windows.
    all_library_issues_connection: DjangoConnection[IssueType] = DjangoConnectionField(IssueType)
    all_library_periodicals_connection: DjangoConnection[PeriodicalType] = DjangoConnectionField(
        PeriodicalType,
    )

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
    def named_library_records(self, info: strawberry.Info) -> list[Named]:
        """Polymorphic ``list[Named]`` mixing Branch / Genre / Patron rows (spec-015).

        The custom-interface demonstration: the field's declared type is the consumer
        ``Named`` interface, and the resolver returns a materialized mix of all three
        implementing models. ``is_type_of`` (installed on every ``DjangoType``)
        discriminates the concrete type per row, so a client selects the shared ``name``
        directly and narrows with ``__typename`` / inline fragments. Returns a plain list
        (already materialized), so it is outside the optimizer's queryset fast path.

        Each model's rows are routed through its primary type's ``get_queryset``
        visibility hook before materializing (feedback #3) - the SAME hook every other
        Branch resolver applies (e.g. ``all_library_branches``). A materialized list has
        no downstream queryset re-execution, so reading ``Branch.objects`` directly here
        would leak ``city="restricted"`` rows ``BranchType.get_queryset`` hides from
        non-staff callers. Genre / Patron route through the (default, no-op) hook too, so
        the field stays correct if either later gains a visibility rule.
        """
        records: list[Any] = []
        records.extend(BranchType.get_queryset(models.Branch.objects.order_by("id"), info))
        records.extend(GenreType.get_queryset(models.Genre.objects.order_by("id"), info))
        records.extend(PatronType.get_queryset(models.Patron.objects.order_by("id"), info))
        return records

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
    def all_library_cards_projected(self) -> list[MembershipCardType]:
        """B8 dogfood: consumer ``.only()`` vs a planned ``select_related``.

        ``PatronType`` has NO visibility hook, so selecting ``patron`` under
        this field plans a real ``select_related("patron")`` - which Django
        refuses to apply over the ``.only("barcode")`` projection (a field
        cannot be both deferred and traversed). B8's relation-aware prune
        must drop the path (and its strictness metadata) live. Pinned in
        ``test_query/test_library_api.py``
        (``test_library_card_projection_survives_select_related_relation``).
        """
        return models.MembershipCard.objects.order_by("id").only("barcode")

    @strawberry.field
    def all_library_cards_deferred(self) -> list[MembershipCardType]:
        """B8 dogfood, defer flavor: ``.defer("patron")`` blocks the same join.

        Django raises the same deferred-and-traversed ``FieldError`` for a
        ``defer()`` projection, and the prune's defer-mode rules (exact
        entries defer; everything else stays loaded) must drop the planned
        ``select_related("patron")`` live. Pinned in
        ``test_query/test_library_api.py``
        (``test_library_card_deferred_projection_survives_select_related``).
        """
        return models.MembershipCard.objects.order_by("id").defer("patron")

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


# --------------------------------------------------------------------------- #
# Custom mutation-input overrides (spec-036 Meta.input_class / partial_input_class)
# over the Relay-Node ``Book`` (which carries no other model-backed mutation, so the
# merged inputs keep the canonical ``BookInput`` / ``BookPartialInput`` names).
# --------------------------------------------------------------------------- #


@strawberry.input
class BookCreateFieldOverrides:
    """Consumer ``Meta.input_class`` override merged into the generated ``BookInput``.

    Declares ONLY the customized field, using the generated naming scheme.
    ``Book.subtitle`` is ``blank=True, null=True``, so the generated ``BookInput`` makes
    ``subtitle`` optional; this consumer requires it. The package merges this field with
    the generated remainder (``title`` / ``circulationStatus`` / ``shelfId`` / ``genres``)
    by class inheritance under the canonical ``BookInput`` name, so the live ``BookInput``
    carries a required ``subtitle: String!`` alongside every other generated column. Only
    a scalar is overridden, so the relation-id type-lock (which pins ``shelfId`` /
    ``genres`` to their generated id shapes) does not apply.
    """

    subtitle: str


@strawberry.input
class BookUpdateFieldOverrides:
    """Consumer ``Meta.partial_input_class`` override merged into ``BookPartialInput``.

    The generated ``BookPartialInput`` makes every field optional; this consumer pins
    ``title`` as always-required on update. The merged ``BookPartialInput`` carries
    ``title: String!`` while ``subtitle`` / ``circulationStatus`` / ``shelfId`` / ``genres``
    stay optional.
    """

    title: str


class CreateBookViaCustomInput(DjangoMutation):
    """Create a ``Book`` through a consumer ``Meta.input_class`` merge override.

    ``Book`` carries no other model-backed mutation (``updateBookViaForm`` is form-backed
    with its own form-derived input name), so the merged create input keeps the canonical
    ``BookInput`` name. ``permission_classes = []`` (the allow-any opt-out) keeps the path
    under test the input shape, not write-auth.
    """

    class Meta:
        model = models.Book
        operation = "create"
        input_class = BookCreateFieldOverrides
        permission_classes = []


class UpdateBookViaCustomInput(DjangoMutation):
    """Update a ``Book`` through a consumer ``Meta.partial_input_class`` merge override.

    ``BookType`` is Relay-Node, so the update ``id`` is a decodable ``GlobalID``; the row
    is located through ``BookType.get_queryset`` (which hides ``circulation_status=repair``
    from non-staff) before the optimizer re-fetch.
    """

    class Meta:
        model = models.Book
        operation = "update"
        partial_input_class = BookUpdateFieldOverrides
        permission_classes = []


class CreateBranchWithShelf(DjangoFormMutation):
    """A plain ``DjangoFormMutation`` whose ``perform_mutate`` runs a custom multi-row write.

    The plain-form write-hook demonstration (spec-038): a model-less ``forms.Form`` has no
    ``form.save()``, so the default ``perform_mutate`` is a no-op. This override creates a
    ``Branch`` plus a starter ``Shelf`` under it from the validated form data - the
    model-less, multi-row write the hook exists for, which a single ``ModelForm.save()``
    cannot express - inside the mutation's ``transaction.atomic()`` boundary, then returns
    the pinned ``{ ok, errors }`` payload. ``permission_classes = []`` (the allow-any
    opt-out) opens the success path so the live test needs no login.
    """

    class Meta:
        form_class = forms.BranchWithShelfForm
        permission_classes = []

    def perform_mutate(self, form, info):
        branch = models.Branch.objects.create(name=form.cleaned_data["branch_name"])
        models.Shelf.objects.create(
            code=form.cleaned_data["shelf_code"],
            branch=branch,
        )


# --------------------------------------------------------------------------- #
# Serializer-mutation surface (spec-039): the get_serializer_for_schema() schema
# hook + subclass validation, earned live over /graphql/ per the README live-first
# mandate. Each opens the write to any caller via ``permission_classes = []`` (the
# allow-any opt-out) so these isolate the hook / subclass behavior, not write-auth.
# --------------------------------------------------------------------------- #


class CreateShelfViaSchemaHookSerializer(SerializerMutation):
    """Create a ``Shelf`` through a construction-kwarg-requiring serializer via the schema hook (spec-039 Decision 7).

    ``TenantShelfSerializer`` requires a ``tenant`` constructor kwarg, so DRF's default
    no-arg schema discovery fails. The consumer overrides ``get_serializer_for_schema()``
    to supply a stable, request-independent schema-time field map (spec-039 Critical-2) and
    overrides ``get_serializer_kwargs`` to inject the runtime ``tenant`` (the actor's
    username). The live test proves the schema-time hook and the runtime serializer
    construction AGREE end to end over ``/graphql/``. The generated input takes a
    deterministic descriptor-derived name (the canonical ``<Serializer>Input`` is reserved
    for the DEFAULT full shape, which this discovery-failing serializer has none of).
    """

    class Meta:
        serializer_class = serializers.TenantShelfSerializer
        operation = "create"
        permission_classes = []

    @classmethod
    def get_serializer_for_schema(cls):
        # The stable, request-independent schema-time field map: construct WITH a
        # placeholder tenant (the field SET does not depend on the tenant value).
        return dict(serializers.TenantShelfSerializer(tenant="__schema__").fields)

    def get_serializer_kwargs(
        self,
        info,
        *,
        data,
        instance=None,
    ):
        # Inject the runtime tenant so construction succeeds (and waive the create-required
        # guard - the override is trusted to supply what schema-time discovery cannot).
        kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
        user = getattr(getattr(info.context, "request", None), "user", None)
        kwargs["tenant"] = getattr(user, "username", "") or "anonymous"
        return kwargs


class CreateShelfViaSerializer(SerializerMutation):
    """Create a ``Shelf`` through ``ShelfSerializer`` - the subclass-mutation PARENT (spec-039)."""

    class Meta:
        serializer_class = serializers.ShelfSerializer
        operation = "create"
        permission_classes = []


class CreateShelfViaOptionalCodeStrictSerializer(SerializerMutation):
    """Create a ``Shelf`` through ``OptionalCodeShelfSerializer`` with its natural required ``code``."""

    class Meta:
        serializer_class = serializers.OptionalCodeShelfSerializer
        operation = "create"
        permission_classes = []


class CreateShelfViaOptionalCodeSerializer(SerializerMutation):
    """Create a ``Shelf`` while mutation ``Meta.optional_fields`` makes required ``code`` omittable.

    ``OptionalCodeShelfSerializer`` itself declares no custom ``Meta.optional_fields``; the
    public API is the mutation's ``Meta.optional_fields``. The strict sibling above shares the
    same serializer and field set but does not set ``optional_fields``, so the two generated
    inputs must remain distinct and retain different ``code`` requiredness.
    """

    class Meta:
        serializer_class = serializers.OptionalCodeShelfSerializer
        operation = "create"
        optional_fields = ("code",)
        permission_classes = []


class CreateShelfViaSubclassedSerializer(CreateShelfViaSerializer):
    """A ``SerializerMutation`` SUBCLASS that REDEFINES ``Meta.serializer_class`` (spec-039 subclass validation).

    Subclasses the concrete ``CreateShelfViaSerializer`` (``serializer_class=ShelfSerializer``)
    but redefines ``serializer_class`` to ``RenamedShelfSerializer`` and narrows to its OWN
    field ``shelf_code`` (renamed from ``code``), which ``ShelfSerializer`` does NOT declare.
    The default ``get_serializer_for_schema`` reads the mutation's OWN ``_mutation_meta`` (via
    ``cls.__dict__``, never an inherited parent snapshot), so the child validates against ITS
    serializer; were the inherited parent snapshot read, ``shelf_code`` would be rejected as
    unknown at this class's creation (the schema import / reload would fail). The live test
    writes through the renamed wire name ``shelfCode``.
    """

    class Meta:
        serializer_class = serializers.RenamedShelfSerializer
        operation = "create"
        fields = ("shelf_code", "branch")
        permission_classes = []


class CreateShelfRejectingViaSerializer(SerializerMutation):
    """Create a ``Shelf`` whose serializer ``save()`` raises a bare DRF ``ValidationError`` (spec-039).

    ``RejectingShelfSerializer.save()`` raises a whole-object, save-time
    ``serializers.ValidationError`` with a BARE (non-dict) detail; the recursive error
    flattener normalizes the empty error path to the ``"__all__"`` sentinel, so the live
    test proves that save-time bare-detail path surfaces as ``{ field: "__all__" }`` over
    HTTP with no row written.
    """

    class Meta:
        serializer_class = serializers.RejectingShelfSerializer
        operation = "create"
        permission_classes = []


class CreateShelfViaHookTargetingPatron(SerializerMutation):
    """One half of a same-serializer hook-collision pair: a shared ``target`` relation pointed at ``Patron`` (spec-039 High).

    Shares ``TargetedShelfSerializer`` with ``CreateShelfViaHookTargetingLoan``; both override
    ``get_serializer_for_schema()`` (the schema-time field map) AND ``get_serializer_kwargs``
    (the runtime construction) to point a shared write-only ``target`` relation at a DIFFERENT
    model, differing ONLY in ``target``'s model. The two generated inputs (``code`` /
    ``branchId`` / ``targetId``) differ ONLY in ``target``'s ``related_model``, so each takes a
    distinct descriptor-derived name (the canonical name is reserved for the unused DEFAULT
    ``code`` + ``branch`` shape) - the pair finalizes to DISTINCT input types instead of
    colliding on one canonical name. ``target`` is a REAL runtime field: posting ``targetId``
    decodes it against ``Patron`` (this half's model) BEFORE the serializer is constructed and
    DRF re-validates it, so a ``Patron``-only pk succeeds here but is a ``targetId`` relation
    error for the ``Loan`` half - proving the differentiating relation DECODE, not just the
    name. ``target`` is ``required=False`` and popped before the write (``Shelf`` has no
    ``target`` column).
    """

    class Meta:
        serializer_class = serializers.TargetedShelfSerializer
        operation = "create"
        permission_classes = []

    @classmethod
    def get_serializer_for_schema(cls):
        return serializers.shelf_collision_schema_field_map(models.Patron)

    def get_serializer_kwargs(
        self,
        info,
        *,
        data,
        instance=None,
    ):
        # Construct the runtime serializer with the SAME target_model the schema hook used,
        # so the schema-time ``target`` shape and the runtime ``target`` decode agree.
        kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
        kwargs["target_model"] = models.Patron
        return kwargs


class CreateShelfViaHookTargetingLoan(SerializerMutation):
    """The collision pair's twin: the shared ``target`` relation pointed at ``Loan`` (spec-039 High).

    Same shared ``TargetedShelfSerializer`` and same ``code`` + ``branch`` + ``target`` shape
    as ``CreateShelfViaHookTargetingPatron``, with ``target`` pointed at ``Loan`` (a different
    non-Relay model with a registered primary ``DjangoType``) via both
    ``get_serializer_for_schema()`` and ``get_serializer_kwargs``. The two generated inputs
    differ ONLY in ``target``'s ``related_model`` - identical ``targetId`` annotations, distinct
    descriptor-derived names - so the materialize ledger no longer collides on one canonical
    name. At runtime ``targetId`` decodes against ``Loan``, so a ``Patron``-only pk is a
    ``targetId`` relation error here (the wrong-model assertion proving each half decodes
    against its OWN target model).
    """

    class Meta:
        serializer_class = serializers.TargetedShelfSerializer
        operation = "create"
        permission_classes = []

    @classmethod
    def get_serializer_for_schema(cls):
        return serializers.shelf_collision_schema_field_map(models.Loan)

    def get_serializer_kwargs(
        self,
        info,
        *,
        data,
        instance=None,
    ):
        kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
        kwargs["target_model"] = models.Loan
        return kwargs


class CreateShelfViaHookNarrowedSerializer(SerializerMutation):
    """Create a ``Shelf`` via a serializer whose UNSUPPORTED default field a hook narrows away (spec-039 High - unsupported-default-field recovery).

    ``HookNarrowedShelfSerializer``'s default ``.fields`` include an unsupported
    ``SlugRelatedField(many=True)`` ``alt_branches``: default discovery succeeds but its WALK
    raises, so the canonical name is not reserved (``_default_full_shape_identity`` swallows
    the walk error) and the supported hook map is NOT rejected. The hook narrows the
    schema-time map to the supported subset (``code`` + ``branch``); the live write proves the
    hook map drives BOTH the schema (a ``branchId`` raw-pk input, not the ``altBranches`` slug
    list) and the runtime decode, and ``alt_branches`` (``required=False``) is omitted.
    """

    class Meta:
        serializer_class = serializers.HookNarrowedShelfSerializer
        operation = "create"
        permission_classes = []

    @classmethod
    def get_serializer_for_schema(cls):
        # Default no-arg discovery succeeds, so construct once and DROP the unsupported
        # alt_branches from its bound .fields - leaving the supported (code + branch) subset.
        fields = dict(serializers.HookNarrowedShelfSerializer().fields)
        del fields["alt_branches"]
        return fields


class CreateShelfViaHookNonNullNote(SerializerMutation):
    """One half of a same-serializer pair whose hooks differ ONLY in a field's ``allow_null`` (spec-039 High / M2 + rev6 #1).

    Shares ``NoteShelfSerializer`` with ``CreateShelfViaHookNullableNote``; both override
    ``get_serializer_for_schema()`` (the schema-time field map) AND ``get_serializer_kwargs``
    (the per-request construction) to build the SAME serializer with a different
    ``note_allow_null``, so the schema-time ``note`` shape and the runtime ``note`` field AGREE
    (rev6 #1 - the agreement guard now forbids a schema-only decode-then-drop field). This half
    is ``allow_null=False``, so ``note`` is a non-null ``String!`` in the generated input; the
    twin's is a nullable, omittable ``String``. Before the descriptor-identity fix both shapes
    compared EQUAL (the descriptor recorded the base annotation, NOT the emitted nullability),
    so the second declaration silently reused the first's cached input class - giving one
    mutation the other's nullability. The fix records the EMITTED annotation, so the two take
    DISTINCT descriptor-derived names with the correct per-field nullability. ``note`` is a
    serializer-only write-only field (decoded + validated then dropped by ``create()``).
    """

    class Meta:
        serializer_class = serializers.NoteShelfSerializer
        operation = "create"
        permission_classes = []

    @classmethod
    def get_serializer_for_schema(cls):
        return serializers.nullability_schema_field_map(allow_null=False)

    def get_serializer_kwargs(
        self,
        info,
        *,
        data,
        instance=None,
    ):
        # Construct the runtime serializer with the SAME note_allow_null the schema hook used,
        # so the schema-time ``note`` shape and the runtime ``note`` field agree (rev6 #1).
        kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
        kwargs["note_allow_null"] = False
        return kwargs


class CreateShelfViaHookNullableNote(SerializerMutation):
    """The nullability pair's twin: the same ``note`` field but ``allow_null=True`` (spec-039 High / M2 + rev6 #1).

    Same shared ``NoteShelfSerializer`` and same ``code`` + ``branch`` + ``note`` hook shape as
    ``CreateShelfViaHookNonNullNote``, with ``note`` ``allow_null=True`` - so ``note`` is a
    nullable, OMITTABLE, null-ACCEPTING ``String`` (M2 - GraphQL cannot express
    required-AND-nullable, so the key is omittable and an explicit ``null`` is a valid value).
    Its generated input must take a name DISTINCT from the non-null twin's (the
    emitted-annotation descriptor identity), not silently reuse it. Its ``get_serializer_kwargs``
    constructs the runtime serializer with ``note_allow_null=True`` so schema + runtime agree.
    """

    class Meta:
        serializer_class = serializers.NoteShelfSerializer
        operation = "create"
        permission_classes = []

    @classmethod
    def get_serializer_for_schema(cls):
        return serializers.nullability_schema_field_map(allow_null=True)

    def get_serializer_kwargs(
        self,
        info,
        *,
        data,
        instance=None,
    ):
        kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
        kwargs["note_allow_null"] = True
        return kwargs


class CreateShelfViaBlankCodeSerializer(SerializerMutation):
    """Create a ``Shelf`` whose ``code`` is an ``allow_blank=True`` required ``CharField`` (spec-039 M2 - allow_blank pinned).

    ``BlankCodeShelfSerializer`` constructs no-arg (default discovery works), so its input is
    the canonical ``BlankCodeShelfSerializerInput``. ``allow_blank`` is absent from the SDL:
    ``code`` is still a non-null ``String!`` (a required ``CharField``), and the empty-string
    acceptance is enforced by the serializer at runtime. The live test introspects ``code`` as
    a non-null ``String`` and posts ``code: ""`` to prove the serializer accepts + writes the
    blank (a plain required ``CharField`` would reject it with a field error).
    """

    class Meta:
        serializer_class = serializers.BlankCodeShelfSerializer
        operation = "create"
        permission_classes = []


class UpdateBookViaSerializerWithLock(SerializerMutation):
    """Update a ``Book`` with an opt-in ``SELECT ... FOR UPDATE`` row lock (spec-039 rev6 #14).

    ``BookType`` is Relay-Node, so the update ``id`` is a decodable ``GlobalID`` (payload slot
    ``node``). ``Meta.select_for_update = True`` locks the located row inside the pipeline
    transaction, AFTER visibility filtering. On sqlite (the test backend) Django silently skips
    the ``FOR UPDATE`` clause, so the live test proves the update path integrates cleanly with
    the lock enabled; on a supporting backend the row is genuinely locked.
    """

    class Meta:
        serializer_class = serializers.BookSerializer
        operation = "update"
        select_for_update = True
        permission_classes = []


class CreateShelfWithSaveKwargs(SerializerMutation):
    """Create a ``Shelf`` injecting server-side data at ``serializer.save(**kwargs)`` (spec-039 rev6 #12).

    ``ShelfSerializer`` accepts ``code`` + ``branch``; ``get_serializer_save_kwargs`` supplies a
    server-side ``topic`` at SAVE time (NOT a client input, NOT a constructor kwarg) - the
    DRF-native ``serializer.save(owner=...)`` pattern. ``topic`` is not a serializer input field,
    so it does not shadow one. The live test posts ``{code, branchId}`` and reads the
    save-time-stamped ``topic`` back off the written ``Shelf``.
    """

    class Meta:
        serializer_class = serializers.ShelfSerializer
        operation = "create"
        permission_classes = []

    def get_serializer_save_kwargs(
        self,
        info,
        data,
        instance=None,
    ):
        return {"topic": "stamped-at-save"}


class CreateShelfViaAltBranchesSerializer(SerializerMutation):
    """Create a ``Shelf`` with a raw-pk M2M ``alt_branches`` input - the batched multi-relation visibility path (spec-039 rev6 #3).

    ``alt_branches`` targets the non-Relay ``BranchType``, so the input is a raw-pk list; the
    serializer decode confirms the whole list's visibility in ONE batched ``pk__in`` query
    (through ``BranchType.get_queryset``, hiding ``city="restricted"`` from the anonymous
    caller), and DRF's own re-validation runs against the SAME visibility-scoped queryset. The
    live test proves the M2M writes for visible branches and that a hidden branch is an
    ``altBranches`` relation error over ``/graphql/``.
    """

    class Meta:
        serializer_class = serializers.AltBranchesShelfSerializer
        operation = "create"
        permission_classes = []


class CreateShelfWithInjectedTopic(SerializerMutation):
    """Create a ``Shelf`` narrowing away a REQUIRED ``topic`` and INJECTING it via ``Meta.injected_fields`` (spec-039 rev6 #2).

    ``OwnerStampShelfSerializer`` declares ``topic`` ``required=True``; this mutation narrows
    the input to ``("code", "branch")`` (dropping ``topic``) and declares
    ``Meta.injected_fields = ("topic",)`` + a ``get_serializer_kwargs`` override that supplies
    ``topic`` into ``data``. The create-required guard SUBTRACTS the declared injected field
    (so the narrowing does not raise), and the resolver VERIFIES the override supplied it - the
    auditable, per-field replacement for the old blanket ``get_serializer_kwargs`` waiver. The
    live test posts ``{code, branchId}`` (no ``topic`` input) and reads the injected
    ``topic`` back off the written ``Shelf``.
    """

    class Meta:
        serializer_class = serializers.OwnerStampShelfSerializer
        operation = "create"
        fields = ("code", "branch")
        injected_fields = ("topic",)
        permission_classes = []

    def get_serializer_kwargs(
        self,
        info,
        *,
        data,
        instance=None,
    ):
        # Supply the narrowed-away required ``topic`` into the serializer data (the injection
        # contract Meta.injected_fields declares).
        kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
        kwargs["data"] = {**kwargs["data"], "topic": "stamped-by-injection"}
        return kwargs


class CreateBranchWithNestedShelves(SerializerMutation):
    """Create a ``Branch`` with an EXPLICIT opt-in nested writable ``shelves`` list (spec-039 rev6 #17).

    ``BranchWithShelvesSerializer`` declares a nested ``shelves = NestedShelfSerializer(many=True)``;
    the mutation opts it in with ``Meta.nested_fields = {"shelves": NestedSerializerConfig()}`` and
    the serializer implements ``create()`` for the nested write. The generated input carries a
    ``shelves: [<NestedShelfSerializerInput>!]`` field, each nested item exposing ``code`` /
    ``topic`` / a raw-pk ``altBranches`` list. The live test proves, over ``/graphql/``:

    * the nested create writes the branch + every nested shelf (through the serializer's OWN
      ``create()`` - the framework never auto-saves the nested relation);
    * a nested ``altBranches`` id is visibility-decoded (a ``city="restricted"`` branch is hidden),
      surfacing as a structured ``shelves.<i>.altBranches`` relation error with NO partial write;
    * a nested DRF validation error (``code == "BANNED"``) flattens to the structured
      ``shelves.<i>.code`` path.

    Opens to any caller via ``permission_classes = []`` so it isolates the nested behavior, not
    write-auth. ``BranchType`` is non-Relay, so the payload slot is ``result``.
    """

    class Meta:
        serializer_class = serializers.BranchWithShelvesSerializer
        operation = "create"
        nested_fields = {"shelves": NestedSerializerConfig()}
        permission_classes = []


class CreateShelfViaMetadataSerializer(SerializerMutation):
    """Create a ``Shelf`` via ``ShelfMetadataSerializer`` - the live type-system matrix (spec-039 rev6 #6 / #7 / #11).

    The input carries a serializer-only ``ChoiceField`` -> a GENERATED enum (``priority``), a
    ``DictField`` -> ``JSON`` (``attributes``), and a custom ``HexColorField`` mapped via the
    public converter registry -> ``String`` (``accentColor``). The live test introspects each
    input field's type (ENUM / JSON / String) and posts a create through them, proving the
    expanded input type system - serializer-only enums, the expanded DRF scalar matrix, and the
    sanctioned converter registry - end to end over ``/graphql/``. The resolved ``priority`` is
    stamped into ``topic`` so the test can read the write effect.
    """

    class Meta:
        serializer_class = serializers.ShelfMetadataSerializer
        operation = "create"
        permission_classes = []


@strawberry.type
class Mutation:
    """Library write surface (live raw-pk relation visibility + ``to_field_name``).

    The serializer-mutation fields (spec-039) add ``createShelfViaSchemaHookSerializer`` (the
    ``get_serializer_for_schema()`` schema hook + ``get_serializer_kwargs`` runtime injection
    over HTTP) and ``createShelfViaSubclassedSerializer`` (a subclass redefining
    ``Meta.serializer_class`` - subclass validation reads the mutation's own snapshot, not an
    inherited parent). ``createShelfViaSerializer`` is the plain parent the subclass extends.
    ``createShelfViaHookTargetingPatron`` / ``createShelfViaHookTargetingLoan`` are the
    same-serializer hook-shape collision pair (one serializer, two hooks pointing a shared
    write-only ``target`` relation at different models - distinct descriptor-derived input
    names AND a differentiating runtime relation decode), and
    ``createShelfViaHookNarrowedSerializer`` is the unsupported-default-field recovery case (a
    hook narrows away an unsupported default field so the supported map still builds + writes).
    ``createShelfViaHookNonNullNote`` / ``createShelfViaHookNullableNote`` are a same-serializer
    pair whose hooks differ ONLY in a field's ``allow_null`` (proving the EMITTED nullability is
    part of the descriptor identity - distinct input types, not a silent reuse), and
    ``createShelfViaBlankCodeSerializer`` pins ``allow_blank=True`` (a non-null ``String!`` in
    the SDL, empty string accepted at runtime). ``createShelfViaOptionalCodeStrictSerializer``
    and ``createShelfViaOptionalCodeSerializer`` share one serializer and prove mutation-level
    ``Meta.optional_fields`` produces a distinct input with weaker GraphQL requiredness while
    leaving DRF to enforce the omitted required field in-band.
    """

    create_shelf_via_form = DjangoMutationField(CreateShelfViaForm)
    create_shelf = DjangoMutationField(CreateShelf)
    update_book_via_form = DjangoMutationField(UpdateBookViaForm)
    create_book_via_custom_input = DjangoMutationField(CreateBookViaCustomInput)
    update_book_via_custom_input = DjangoMutationField(UpdateBookViaCustomInput)
    create_branch_with_shelf = DjangoMutationField(CreateBranchWithShelf)
    create_shelf_via_serializer = DjangoMutationField(CreateShelfViaSerializer)
    create_shelf_rejecting_via_serializer = DjangoMutationField(CreateShelfRejectingViaSerializer)
    create_shelf_via_optional_code_strict_serializer = DjangoMutationField(
        CreateShelfViaOptionalCodeStrictSerializer,
    )
    create_shelf_via_optional_code_serializer = DjangoMutationField(
        CreateShelfViaOptionalCodeSerializer,
    )
    create_shelf_via_schema_hook_serializer = DjangoMutationField(
        CreateShelfViaSchemaHookSerializer,
    )
    create_shelf_via_subclassed_serializer = DjangoMutationField(
        CreateShelfViaSubclassedSerializer,
    )
    create_shelf_via_hook_targeting_patron = DjangoMutationField(
        CreateShelfViaHookTargetingPatron,
    )
    create_shelf_via_hook_targeting_loan = DjangoMutationField(
        CreateShelfViaHookTargetingLoan,
    )
    create_shelf_via_hook_narrowed_serializer = DjangoMutationField(
        CreateShelfViaHookNarrowedSerializer,
    )
    create_shelf_via_hook_non_null_note = DjangoMutationField(
        CreateShelfViaHookNonNullNote,
    )
    create_shelf_via_hook_nullable_note = DjangoMutationField(
        CreateShelfViaHookNullableNote,
    )
    create_shelf_via_blank_code_serializer = DjangoMutationField(
        CreateShelfViaBlankCodeSerializer,
    )
    create_shelf_via_metadata_serializer = DjangoMutationField(
        CreateShelfViaMetadataSerializer,
    )
    create_shelf_with_injected_topic = DjangoMutationField(
        CreateShelfWithInjectedTopic,
    )
    create_shelf_via_alt_branches_serializer = DjangoMutationField(
        CreateShelfViaAltBranchesSerializer,
    )
    create_shelf_with_save_kwargs = DjangoMutationField(
        CreateShelfWithSaveKwargs,
    )
    update_book_via_serializer_with_lock = DjangoMutationField(
        UpdateBookViaSerializerWithLock,
    )
    create_branch_with_nested_shelves = DjangoMutationField(
        CreateBranchWithNestedShelves,
    )


__all__ = ("Mutation", "Query")
