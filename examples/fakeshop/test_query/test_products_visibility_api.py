"""Live GraphQL proof that generated relations enforce target visibility themselves.

Which half of the framework enforces it depends on whether the optimizer PLANNED
the relation - which is NOT the same question as whether the optimizer ran, nor
as whether it armed strictness. Unplanned - no optimizer mounted, a
consumer-populated prefetch cache, a selection the walker declined, a root handed
back as a plain list under armed ``strictness`` - and the generated resolver
applies the hook per parent. Planned, and the resolver stands down
(``django_strawberry_framework/types/resolvers.py::_optimizer_scoped_relation``)
because the plan already applied it to the child queryset, which makes the plan
the sole authority for those rows. Both halves are covered here, each against the
staff branch that must NOT be scoped.

Authority over WHICH ROWS is not authority over WHICH CONNECTION: the last two
rows pin the planned child's hook to the connection the walker seeded it on, so a
hook that pins an alias of its own fails the relation closed while a hook that only
narrows still serves its scoped page. A list-returning root with the optimizer
installed still pays ``1 + N`` for a nested connection.
"""

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import assert_graphql_success, post_graphql
from strategy_schemas import make_django_type
from strawberry import relay
from strawberry.django.views import GraphQLView

from django_strawberry_framework import finalize_django_types, strawberry_config
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import AsyncDjangoGraphQLView

_CURRENT: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return GraphQLView.as_view(schema=schema)(request)


async def _async_graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view), path("graphql-async/", _async_graphql_view)]


def test_unoptimized_relation_hides_private_child_over_http(db):
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None
    item = Item.objects.filter(category=category).first()
    assert item is not None
    Item.objects.filter(pk=item.pk).update(is_private=True)

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return Category.objects.filter(pk=category.pk)

    _CURRENT["schema"] = strawberry.Schema(query=Query)
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            response = post_graphql(
                "{ categories { items { name } } }",
                url="/graphql/",
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("errors") is None, payload
        assert payload["data"] == {"categories": [{"items": []}]}
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


def _build_async_visibility_schema():
    category = Category.objects.first()
    assert category is not None
    item = Item.objects.filter(category=category).first()
    assert item is not None
    Item.objects.filter(pk=item.pk).update(is_private=True)

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        async def categories(self) -> list[CategoryType]:
            return await sync_to_async(list)(
                Category.objects.filter(pk=category.pk),
            )

    return strawberry.Schema(query=Query)


async def _post_async_visibility_query():
    schema = await sync_to_async(_build_async_visibility_schema)()
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            res = await AsyncTestClient().query(
                "{ categories { items { name } } }",
                assert_no_errors=False,
                url="/graphql-async/",
            )
            return res.response
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


@pytest.mark.django_db(transaction=True)
async def test_async_unoptimized_relation_hides_private_child_over_http():
    await sync_to_async(services.seed_data)(1)
    response = await _post_async_visibility_query()
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors") is None, payload
    assert payload["data"] == {"categories": [{"items": []}]}


def _post_visibility_query(schema, query, *, client=None):
    """POST ``query`` against ``schema`` over live HTTP and return the JSON payload.

    ``client`` carries a logged-in session when the row's subject is which viewer
    the target hook answers for; omitting it posts anonymously.
    """
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            response = post_graphql(query, client=client, url="/graphql/")
        assert response.status_code == 200
        return response.json()
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


def test_consumer_prefetch_cache_is_rescoped_with_the_optimizer_installed(db):
    """A cache the CONSUMER prefetched is unscoped even while the optimizer runs.

    ``prefetch_related`` on a consumer-owned root queryset never passes through
    the target type's ``get_queryset``, and an installed optimizer says nothing
    about a relation it did not plan. Trusting the request-wide presence of an
    optimizer served the private row here; the per-relation planned-key check
    re-reads it through the visibility boundary. Asserted as parity against the
    same schema with no optimizer, which is the reference behavior.
    """
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None
    item = Item.objects.filter(category=category).first()
    assert item is not None
    Item.objects.filter(pk=item.pk).update(is_private=True)

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return list(Category.objects.filter(pk=category.pk).prefetch_related("items"))

    query = "{ categories { items { name isPrivate } } }"
    optimizer = DjangoOptimizerExtension()
    optimized = _post_visibility_query(
        strawberry.Schema(query=Query, extensions=[lambda: optimizer]),
        query,
    )
    unoptimized = _post_visibility_query(strawberry.Schema(query=Query), query)
    assert optimized.get("errors") is None, optimized
    assert optimized["data"] == {"categories": [{"items": []}]}
    assert optimized["data"] == unoptimized["data"]


def test_forward_fk_target_visibility_holds_with_the_optimizer_installed(db):
    """A hidden forward-FK target stays hidden for a relation the walker never planned.

    The optimizer cannot plan a root that hands back a plain list, so the FK
    below lazy-loads unscoped. The non-null ``category`` field then fails loudly
    rather than emitting a row ``CategoryType.get_queryset`` excludes - the same
    outcome the no-optimizer schema produces.
    """
    services.seed_data(1)
    item = Item.objects.first()
    assert item is not None
    Category.objects.filter(pk=item.category_id).update(is_private=True)

    from apps.products.schema import ItemType

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> list[ItemType]:
            return list(Item.objects.filter(pk=item.pk))

    query = "{ items { name category { name } } }"
    optimizer = DjangoOptimizerExtension()
    optimized = _post_visibility_query(
        strawberry.Schema(query=Query, extensions=[lambda: optimizer]),
        query,
    )
    unoptimized = _post_visibility_query(strawberry.Schema(query=Query), query)
    assert optimized["data"] is None
    assert [error["message"] for error in optimized["errors"]] == [
        "Cannot return null for non-nullable field ItemType.category.",
    ]
    assert optimized["errors"] == unoptimized["errors"]


def _build_async_forward_fk_schema():
    """Schema whose async root select_relateds the FK, so it loads WITHOUT a query.

    The visibility re-check needs the related object in hand, and a forward-FK
    lazy load is a ``SynchronousOnlyOperation`` inside an async execution - so a
    consumer ``select_related`` is what puts an UNSCOPED target on this path:
    the JOIN never consulted ``CategoryType.get_queryset``.
    """
    item = Item.objects.first()
    assert item is not None
    Category.objects.filter(pk=item.category_id).update(is_private=True)

    from apps.products.schema import ItemType

    @strawberry.type
    class Query:
        @strawberry.field
        async def items(self) -> list[ItemType]:
            return await sync_to_async(list)(
                Item.objects.filter(pk=item.pk).select_related("category"),
            )

    return strawberry.Schema(query=Query)


@pytest.mark.django_db(transaction=True)
async def test_async_forward_fk_target_visibility_hides_a_private_target_over_http():
    """The async single-object visibility re-check runs on a real async request.

    ``_visible_related_object`` takes its ``await``-ing branch here, and a hidden
    non-null ``category`` fails loudly rather than resolving the excluded row a
    consumer JOIN pulled in.
    """
    await sync_to_async(services.seed_data)(1)
    schema = await sync_to_async(_build_async_forward_fk_schema)()
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            res = await AsyncTestClient().query(
                "{ items { name category { name } } }",
                assert_no_errors=False,
                url="/graphql-async/",
            )
            response = res.response
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None
    assert [error["message"] for error in payload["errors"]] == [
        "Cannot return null for non-nullable field ItemType.category.",
    ]


#: Forward-FK document posted against the strictness-armed holder below.
_STRICT_LOADED_FK_QUERY = "{ items { name category { name } } }"


def _strictness_armed_loaded_fk_schema(item_pk):
    """Holder arming ``strictness="raise"`` over a root the walker cannot plan.

    Three things have to hold at once for the forward resolver's SLOW-path sync
    arm to reach the visibility re-check, and this schema is what makes them
    coincide. ``DjangoOptimizerExtension(strictness="raise")`` arms strictness on
    the execution frame before any planning runs, so the resolver leaves its
    sentinel-free fast path even though the plain-list root leaves the walker
    with nothing to plan. Nothing planned means nothing published to the
    optimizer's scoped-relation set, so the relation is NOT optimizer-scoped -
    "planned" and "scoped" are separate predicates and this is the gap between
    them. And the consumer's own ``select_related`` loads the FK, which is what
    keeps the armed N+1 guard silent: a lazy load here would be refused by
    ``strictness="raise"`` before any row was served.

    What arrives at the resolver is therefore a related object a consumer JOIN
    pulled in, which never passed through ``CategoryType.get_queryset``, on an
    execution that carries the optimizer's sentinels. The resolver owns the
    permission decision on it.
    """
    from apps.products.schema import ItemType

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> list[ItemType]:
            return list(Item.objects.filter(pk=item_pk).select_related("category"))

    optimizer = DjangoOptimizerExtension(strictness="raise")
    return strawberry.Schema(query=Query, extensions=[lambda: optimizer])


def _hide_the_seeded_items_category():
    """Hide the seeded item's FK target; return the item's pk and the hidden name."""
    item = Item.objects.first()
    assert item is not None
    Category.objects.filter(pk=item.category_id).update(is_private=True)
    return item.pk, Category.objects.get(pk=item.category_id).name


def test_anonymous_is_refused_a_joined_forward_fk_target_the_hook_hides(db):
    """A JOINed hidden target is hidden from an anonymous viewer under armed strictness.

    Neither sibling row reaches this arm. The sync
    ``..._holds_with_the_optimizer_installed`` row mounts the DEFAULT strictness,
    so the resolver answers on its fast path; the async row mounts no optimizer at
    all and answers in the coroutine. This one is the sync slow-path arm: armed
    strictness, an unplanned relation, and an already-loaded target.

    ``ItemType.category`` is non-null, so hiding the row is a loud failure rather
    than a silent null: ``data`` is null outright, and the excluded category's
    name reaches the wire nowhere.
    """
    services.seed_data(1)
    item_pk, _hidden_name = _hide_the_seeded_items_category()

    payload = _post_visibility_query(
        _strictness_armed_loaded_fk_schema(item_pk),
        _STRICT_LOADED_FK_QUERY,
    )

    assert payload["data"] is None
    assert [error["message"] for error in payload["errors"]] == [
        "Cannot return null for non-nullable field ItemType.category.",
    ]


def test_staff_is_served_the_same_joined_forward_fk_target(db):
    """The control: the same row is served once the viewer is one the hook admits.

    Without it the row above would be satisfied by a resolver that hid every
    target, which is not the claim - the re-check is a permission decision, and
    ``CategoryType.get_queryset`` returns everything to staff.
    """
    services.seed_data(1)
    item_pk, hidden_name = _hide_the_seeded_items_category()
    services.create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    payload = _post_visibility_query(
        _strictness_armed_loaded_fk_schema(item_pk),
        _STRICT_LOADED_FK_QUERY,
        client=client,
    )

    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "items": [
            {"name": Item.objects.get(pk=item_pk).name, "category": {"name": hidden_name}},
        ],
    }


def _strictness_armed_nullable_fk_schema():
    """The same armed-but-unplanned mount over a NULLABLE forward key.

    ``ItemType.category`` is non-null, so a hidden target there is a loud
    refusal. The other wire outcome of the same decision is a field that
    collapses to ``null`` while its siblings are served, and no shipped type
    pairs a nullable forward key with a custom-visibility target - the example's
    one nullable forward key (``PatronProfile.favorite_genre``) points at
    ``GenreType``, which declares no hook, and adding one there would change
    every genre traversal in the library suite. Rung 3 holder.
    """
    from apps.library.models import Genre, PatronProfile

    registry.clear()
    make_django_type(
        "HolderFavoriteGenreType",
        Genre,
        ("id", "name"),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                lambda cls, queryset, info: queryset.exclude(name__startswith="HIDDEN"),
            ),
        },
    )
    profile_type = make_django_type(
        "HolderProfileType",
        PatronProfile,
        ("postal_code", "favorite_genre"),
        node=False,
    )
    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def profiles(self) -> list[profile_type]:
            return list(
                PatronProfile.objects.select_related("favorite_genre").order_by("postal_code"),
            )

    optimizer = DjangoOptimizerExtension(strictness="raise")
    return strawberry.Schema(query=Query, extensions=[lambda: optimizer])


def test_a_nullable_joined_forward_fk_collapses_to_null_only_for_the_hidden_target(db):
    """The hidden target nulls its own field; the admitted one on the next row is served.

    Same armed-but-unplanned slow path as the two rows above, over a nullable
    key, so the re-check's verdict is readable as data rather than as a
    non-null failure - and both verdicts sit in one payload, which is what
    stops "hides everything" from satisfying the claim.
    """
    from apps.library.models import Genre, Patron, PatronProfile

    hidden_genre = Genre.objects.create(name="HIDDEN-Noir")
    open_genre = Genre.objects.create(name="OPEN-Verse")
    PatronProfile.objects.create(
        patron=Patron.objects.create(name="Profile Holder A"),
        postal_code="AA-1",
        favorite_genre=hidden_genre,
    )
    PatronProfile.objects.create(
        patron=Patron.objects.create(name="Profile Holder B"),
        postal_code="BB-2",
        favorite_genre=open_genre,
    )

    payload = _post_visibility_query(
        _strictness_armed_nullable_fk_schema(),
        "{ profiles { postalCode favoriteGenre { name } } }",
    )

    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "profiles": [
            {"postalCode": "AA-1", "favoriteGenre": None},
            {"postalCode": "BB-2", "favoriteGenre": {"name": "OPEN-Verse"}},
        ],
    }


#: One nested-connection document, posted against holder schemas that differ only
#: in how many parent rows their root resolver hands back.
_NESTED_CONNECTION_QUERY = (
    "{ categories { itemsConnection(first: 2) { edges { node { name } } } } }"
)


def _nested_connection_item_queries(parent_count):
    """Post ``_NESTED_CONNECTION_QUERY`` at ``parent_count`` parents; return the item SQL.

    The holder schema installs NO ``DjangoOptimizerExtension``, so the nested
    connection runs off the relation manager rather than a planned window.
    """
    parent_pks = list(
        Category.objects.order_by("pk").values_list("pk", flat=True)[:parent_count],
    )
    assert len(parent_pks) == parent_count

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return list(Category.objects.filter(pk__in=parent_pks).order_by("pk"))

    with CaptureQueriesContext(connection) as captured:
        payload = _post_visibility_query(strawberry.Schema(query=Query), _NESTED_CONNECTION_QUERY)
    assert payload.get("errors") is None, payload
    assert len(payload["data"]["categories"]) == parent_count
    return [entry["sql"] for entry in captured.captured_queries if "products_item" in entry["sql"]]


def test_nested_connection_costs_one_query_per_parent_without_the_optimizer(db):
    """With no optimizer installed a nested connection costs one window query per parent.

    A relation-seeded connection is served from each parent's own relation
    manager, so the cost grows with the parent count: N parents pay N window
    queries. A schema that mounts no ``DjangoOptimizerExtension`` is a supported
    consumer configuration, and this is what it pays there - measured at two
    cardinalities so a fixed count cannot satisfy it, and so a regression toward
    per-EDGE loading (which would overshoot N) is visible.
    """
    services.seed_data(1)

    assert len(_nested_connection_item_queries(2)) == 2
    assert len(_nested_connection_item_queries(5)) == 5


def _nested_connection_item_queries_with_optimizer_on_a_list(parent_count):
    """Same document as ``_nested_connection_item_queries``, optimizer installed, list root.

    A materialized list is not a ``QuerySet``, so the installed optimizer cannot
    plan the nested window and each parent still pays its own child query.

    Returns the child SQL and the root SQL, so a caller can pin both that the
    per-parent cost is real and that the optimizer left the materialized root
    alone instead of re-deriving a queryset from it and running it again.
    """
    parent_pks = list(
        Category.objects.order_by("pk").values_list("pk", flat=True)[:parent_count],
    )
    assert len(parent_pks) == parent_count

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return list(Category.objects.filter(pk__in=parent_pks).order_by("pk"))

    optimizer = DjangoOptimizerExtension()
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: optimizer],
        config=strawberry_config(),
    )
    with CaptureQueriesContext(connection) as captured:
        payload = _post_visibility_query(schema, _NESTED_CONNECTION_QUERY)
    assert payload.get("errors") is None, payload
    assert len(payload["data"]["categories"]) == parent_count
    item_sql = [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "products_item"' in entry["sql"]
    ]
    root_sql = [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "products_category"' in entry["sql"]
        and 'FROM "products_item"' not in entry["sql"]
    ]
    return item_sql, root_sql


def test_nested_connection_still_costs_one_query_per_parent_when_the_optimizer_gets_a_list(
    db,
):
    """An installed optimizer does not plan a list-returning root: cost still grows with N.

    The root itself is read exactly once at both cardinalities: an optimizer that
    re-ran the materialized list would show a second category statement.
    """
    services.seed_data(1)

    item_sql_two, root_sql_two = _nested_connection_item_queries_with_optimizer_on_a_list(2)
    assert len(root_sql_two) == 1, root_sql_two
    assert len(item_sql_two) == 2

    item_sql_five, root_sql_five = _nested_connection_item_queries_with_optimizer_on_a_list(5)
    assert len(root_sql_five) == 1, root_sql_five
    assert len(item_sql_five) == 5


def _list_relation_item_queries(parent_count):
    """Post a raw-list ``items`` selection at ``parent_count`` parents; return item SQL.

    Holder installs no optimizer. The root returns a queryset so an installed
    optimizer could plan the reverse FK; this helper omits the extension so
    each parent lazy-loads.
    """
    parent_pks = list(
        Category.objects.order_by("pk").values_list("pk", flat=True)[:parent_count],
    )
    assert len(parent_pks) == parent_count

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return Category.objects.filter(pk__in=parent_pks).order_by("pk")

    with CaptureQueriesContext(connection) as captured:
        payload = _post_visibility_query(
            strawberry.Schema(query=Query),
            "{ categories { items { name } } }",
        )
    assert payload.get("errors") is None, payload
    assert len(payload["data"]["categories"]) == parent_count
    return [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "products_item"' in entry["sql"]
    ]


def test_unoptimized_list_relation_costs_one_query_per_parent(db):
    """With no optimizer a many-side list selection costs one item query per parent.

    Measured at two cardinalities so a fixed count cannot satisfy it.
    """
    services.seed_data(1)

    assert len(_list_relation_item_queries(2)) == 2
    assert len(_list_relation_item_queries(5)) == 5


def _holder_patron_card_schema(*, optimizer):
    """Throwaway reverse-O2O types: card hook hides ``HIDDEN*`` barcodes.

    Shipped ``MembershipCardType`` has no ``get_queryset``; adding one there
    would change every ``patron { card }`` traversal. Rung 3 holder.
    """
    from apps.library.models import MembershipCard, Patron

    from django_strawberry_framework import DjangoType

    registry.clear()

    class HolderCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode")
            name = "HolderCardType"

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(barcode__startswith="HIDDEN")

    class HolderPatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")
            name = "HolderPatronType"

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def patrons(self) -> list[HolderPatronType]:
            return list(Patron.objects.filter(name__endswith="Holder").order_by("name"))

    extensions = []
    if optimizer:
        installed = DjangoOptimizerExtension()
        extensions = [lambda: installed]
    return strawberry.Schema(query=Query, extensions=extensions)


def test_reverse_one_to_one_custom_visibility_matches_with_and_without_optimizer(db):
    """Hidden reverse-O2O cards collapse to ``null`` whether or not the relation was planned.

    The optimizer leg also pins its statement count. The root hands back a
    materialized list, so nothing is planned and each patron pays exactly two
    card statements: the descriptor load and the hook's re-check. Four in total
    at two patrons - a third statement per patron fails this row.
    """
    from apps.library.models import MembershipCard, Patron

    hidden = Patron.objects.create(name="Hidden Holder")
    MembershipCard.objects.create(patron=hidden, barcode="HIDDEN-1")
    visible = Patron.objects.create(name="Visible Holder")
    MembershipCard.objects.create(patron=visible, barcode="OPEN-1")

    query = "{ patrons { name card { barcode } } }"
    expected = {
        "patrons": [
            {"name": "Hidden Holder", "card": None},
            {"name": "Visible Holder", "card": {"barcode": "OPEN-1"}},
        ],
    }
    unplanned = _post_visibility_query(_holder_patron_card_schema(optimizer=False), query)
    planned_schema = _holder_patron_card_schema(optimizer=True)
    with CaptureQueriesContext(connection) as captured:
        planned = _post_visibility_query(planned_schema, query)
    assert unplanned.get("errors") is None, unplanned
    assert planned.get("errors") is None, planned
    assert unplanned["data"] == expected
    assert planned["data"] == expected
    card_sql = [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "library_membershipcard"' in entry["sql"]
    ]
    assert len(card_sql) == 4, card_sql


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_reverse_one_to_one_custom_visibility_over_http():
    """Async reverse-O2O re-checks the card hook and nulls a hidden barcode."""
    from apps.library.models import MembershipCard, Patron

    await sync_to_async(Patron.objects.create)(name="Hidden Patron")
    hidden = await sync_to_async(Patron.objects.get)(name="Hidden Patron")
    await sync_to_async(MembershipCard.objects.create)(patron=hidden, barcode="HIDDEN-99")
    await sync_to_async(Patron.objects.create)(name="Visible Patron")
    visible = await sync_to_async(Patron.objects.get)(name="Visible Patron")
    await sync_to_async(MembershipCard.objects.create)(patron=visible, barcode="OPEN-99")

    from django_strawberry_framework import DjangoType

    registry.clear()

    class HolderCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode")
            name = "AsyncHolderCardType"

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(barcode__startswith="HIDDEN")

    class HolderPatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")
            name = "AsyncHolderPatronType"

    await sync_to_async(finalize_django_types)()

    @strawberry.type
    class Query:
        @strawberry.field
        async def patrons(self) -> list[HolderPatronType]:
            return await sync_to_async(list)(
                Patron.objects.filter(pk__in=[hidden.pk, visible.pk]).order_by("pk"),
            )

    schema = strawberry.Schema(query=Query)
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            res = await AsyncTestClient().query(
                "{ patrons { name card { barcode } } }",
                assert_no_errors=False,
                url="/graphql-async/",
            )
            response = res.response
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "patrons": [
            {"name": "Hidden Patron", "card": None},
            {"name": "Visible Patron", "card": {"barcode": "OPEN-99"}},
        ],
    }


@pytest.mark.django_db
def test_relay_id_only_connection_page_costs_one_query_and_emits_decodable_ids():
    """An id-only connection page reads the table once and every id decodes to its row.

    ``{ allCategories(first: 5) { edges { node { id } } } }`` selects nothing but
    the Relay ``id``, so the optimizer's projection must still carry the concrete
    pk column: if it did not, each edge would pay a lazy pk fetch and the single
    ``products_category`` query would become one per row. Staff is the viewer so
    ``CategoryType.get_queryset`` narrows nothing and the page is the raw table
    order. Each emitted id is checked against the one the package's own helper
    mints for that row, and decoded back to its ``products.category`` payload.
    """
    services.create_users(1)
    services.seed_data(1)
    from apps.products.schema import CategoryType

    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))
    expected_rows = list(Category.objects.order_by("pk")[:5])
    assert len(expected_rows) == 5

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allCategories(first: 5) { edges { node { id } } } }",
            client=client,
        )

    emitted = [edge["node"]["id"] for edge in data["allCategories"]["edges"]]
    assert emitted == [global_id_for(CategoryType, row.pk) for row in expected_rows]
    decoded = [relay.GlobalID.from_id(node_id) for node_id in emitted]
    assert [global_id.type_name for global_id in decoded] == ["products.category"] * 5
    assert [global_id.node_id for global_id in decoded] == [str(row.pk) for row in expected_rows]
    category_queries = [
        entry["sql"] for entry in captured.captured_queries if "products_category" in entry["sql"]
    ]
    assert len(category_queries) == 1, category_queries


@pytest.mark.django_db
def test_relay_id_and_name_selection_is_clean_under_strictness_raise_over_http():
    """Selecting ``id`` and ``name`` on shipped ``CategoryType`` does not lazy-load under ``raise``.

    Holder mount with ``DjangoOptimizerExtension(strictness="raise")``. The root
    returns a queryset so the walker plans the page; if Relay ``id`` failed to
    project the loaded pk, ``strictness="raise"`` would refuse the unplanned
    fetch. Payload names are derived from the ORM, not memorized.
    """
    services.seed_data(1)
    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return Category.objects.order_by("pk")

    optimizer = DjangoOptimizerExtension(strictness="raise")
    payload = _post_visibility_query(
        strawberry.Schema(
            query=Query,
            extensions=[lambda: optimizer],
            config=strawberry_config(),
        ),
        "{ categories { id name } }",
    )
    assert payload.get("errors") is None, payload
    expected = list(Category.objects.order_by("pk").values_list("name", flat=True))
    assert [row["name"] for row in payload["data"]["categories"]] == expected
    decoded = [relay.GlobalID.from_id(row["id"]) for row in payload["data"]["categories"]]
    assert [int(g.node_id) for g in decoded] == list(
        Category.objects.order_by("pk").values_list("pk", flat=True),
    )
    assert all(g.type_name == Category._meta.label_lower for g in decoded)


@pytest.mark.django_db
def test_cascading_target_hook_blocks_fk_id_elision_over_http():
    """A cascading target hook costs a second query rather than eliding the FK read.

    An id-only forward-FK selection would normally round-trip the source row's FK
    column with no relation read at all. ``ItemType``'s target here is
    ``CategoryType``, whose ``get_queryset`` cascades, and a target hook must run
    over real rows - so the elision is off and the relation is fetched by a
    separate query instead. The root item read therefore carries no join to
    ``products_category``, and the category read is a second query.
    """
    services.seed_data(1)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allItems { edges { node { category { id } } } } }",
        )

    edges = data["allItems"]["edges"]
    assert edges, data
    assert all(edge["node"]["category"]["id"] for edge in edges)
    item_queries = [
        entry["sql"] for entry in captured.captured_queries if "products_item" in entry["sql"]
    ]
    assert len(item_queries) == 1, item_queries
    # No elision, but no join either: the target hook's rows arrive on their own
    # query, so the count is 2 and never 1 + one-per-row.
    assert " JOIN " not in item_queries[0].upper()
    assert len(captured.captured_queries) == 2, [
        entry["sql"] for entry in captured.captured_queries
    ]


#: The two vocabularies one PLANNED nested relation is selected through. Both ride
#: the shipped ``allCategories`` root, which the composed schema optimizes, so the
#: walker plans the relation and records its resolver key - and the generated
#: relation resolver stands down over rows it trusts the plan to have scoped
#: (``django_strawberry_framework/types/resolvers.py::_optimizer_scoped_relation``).
_PLANNED_LIST_QUERY = "{ allCategories(first: 3) { edges { node { name items { name } } } } }"
_PLANNED_CONNECTION_QUERY = (
    "{ allCategories(first: 3) { edges { node { name "
    "itemsConnection(first: 5) { edges { node { name } } } } } } }"
)


def _hide_one_parents_items():
    """Pin three public parents, hide every item under ONE of them by name.

    Arranges privacy over rows the test has already seeded; returns
    ``(hidden_parent, hidden_names)``. Seeded privacy is arbitrary, so all three
    parents and their items are pinned public first and the hidden rows are the
    only ones this helper hides.
    """
    parent_pks = list(Category.objects.order_by("pk").values_list("pk", flat=True)[:3])
    assert len(parent_pks) == 3
    Category.objects.filter(pk__in=parent_pks).update(is_private=False)
    Item.objects.filter(category_id__in=parent_pks).update(is_private=False)
    hidden_parent = Category.objects.get(pk=parent_pks[0]).name
    hidden_names = sorted(
        Item.objects.filter(category_id=parent_pks[0]).values_list("name", flat=True),
    )
    assert hidden_names, "the hidden parent must own items for their absence to mean anything"
    Item.objects.filter(category_id=parent_pks[0]).update(is_private=True)
    return hidden_parent, hidden_names


def _expected_item_names(*, include_private):
    """Derive the expected page per parent from the ORM (products rows are Faker-seeded)."""
    rows = Item.objects.all() if include_private else Item.objects.filter(is_private=False)
    parents = Category.objects.order_by("pk")[:3]
    return {
        parent.name: sorted(rows.filter(category_id=parent.pk).values_list("name", flat=True))
        for parent in parents
    }


def _planned_item_names(query, *, reader, client=None):
    """POST ``query``, assert the relation was PLANNED, return ``{parent: sorted names}``.

    ONE ``products_item`` query for the whole page is what "planned" means here: a
    relation the walker declined costs one read per parent, and its rows are then
    scoped by the resolver rather than by the plan - the opposite of what these
    rows measure.

    Pages come back sorted rather than carrying an ``orderBy:``. A generated
    relation promises WHICH rows, not their order, so sorting is what makes the
    payload comparison exact without pinning an order the field never offered.
    """
    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(query, client=client)
    item_queries = [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "products_item"' in entry["sql"]
    ]
    assert len(item_queries) == 1, item_queries
    return {
        edge["node"]["name"]: sorted(reader(edge["node"]))
        for edge in data["allCategories"]["edges"]
    }


def _list_page(node):
    return [row["name"] for row in node["items"]]


def _connection_page(node):
    return [edge["node"]["name"] for edge in node["itemsConnection"]["edges"]]


@pytest.mark.django_db
def test_anonymous_planned_list_relation_omits_the_targets_private_rows():
    """A planned ``items`` prefetch carries the target's visibility scope into its own query.

    The plan is the only thing scoping a planned relation: its resolver stands
    down, so ``ItemType.get_queryset`` runs exactly once, inside the plan, over the
    child queryset the walker built - and the walker decides whether to run it at
    all from the definition it resolved the relation through. A planner that
    answered that question from a second read and got ``False`` would build the
    child from the unscoped default manager and serve these rows.
    """
    services.seed_data(2)
    hidden_parent, hidden_names = _hide_one_parents_items()

    pages = _planned_item_names(_PLANNED_LIST_QUERY, reader=_list_page)

    assert pages == _expected_item_names(include_private=False)
    assert pages[hidden_parent] == []
    assert not set(hidden_names) & {name for page in pages.values() for name in page}


@pytest.mark.django_db
def test_staff_planned_list_relation_keeps_every_row():
    """The same planned prefetch returns the hidden rows once the viewer is staff.

    The scoping above is the hook's anonymous branch, not the plan refusing to
    fetch: the page is still one planned query and it carries every row.
    """
    services.seed_data(2)
    hidden_parent, hidden_names = _hide_one_parents_items()
    services.create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    pages = _planned_item_names(_PLANNED_LIST_QUERY, reader=_list_page, client=client)

    assert pages == _expected_item_names(include_private=True)
    assert pages[hidden_parent] == hidden_names


@pytest.mark.django_db
def test_anonymous_planned_relation_connection_window_omits_the_targets_private_rows():
    """The same proof over the connection vocabulary, whose page is one partitioned window.

    ``itemsConnection`` is a synthesized relation connection: every parent's page
    comes out of a single window over the child queryset the plan built, so the
    rows it partitions and the rows the hook scoped are one population, derived
    through one captured child definition.
    """
    services.seed_data(2)
    hidden_parent, hidden_names = _hide_one_parents_items()

    pages = _planned_item_names(_PLANNED_CONNECTION_QUERY, reader=_connection_page)

    assert pages == _expected_item_names(include_private=False)
    assert pages[hidden_parent] == []
    assert not set(hidden_names) & {name for page in pages.values() for name in page}


@pytest.mark.django_db
def test_staff_planned_relation_connection_window_keeps_every_row():
    """The window partitions over every row once the viewer is staff, still in one query."""
    services.seed_data(2)
    hidden_parent, hidden_names = _hide_one_parents_items()
    services.create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    pages = _planned_item_names(_PLANNED_CONNECTION_QUERY, reader=_connection_page, client=client)

    assert pages == _expected_item_names(include_private=True)
    assert pages[hidden_parent] == hidden_names


def _child_routing_schema(child_hook):
    """A live ``categories { items }`` schema whose CHILD type carries ``child_hook``.

    The root hands back a queryset under a mounted optimizer, so the walker plans
    ``items`` as a ``Prefetch`` and builds that child itself
    (``django_strawberry_framework/optimizer/walker.py::_build_child_queryset``).
    ``child_hook`` is then the only consumer code running inside the child's seal.
    """
    registry.clear()
    make_django_type(
        "RoutingItemType",
        Item,
        ("id", "name"),
        node=False,
        namespace_extra={"get_queryset": classmethod(child_hook)},
    )
    category_type = make_django_type(
        "RoutingCategoryType",
        Category,
        ("id", "name", "items"),
        node=False,
    )
    finalize_django_types()

    @strawberry.type
    class RoutingQuery:
        @strawberry.field
        def categories(self) -> list[category_type]:
            return Category.objects.all()

    optimizer = DjangoOptimizerExtension()
    return strawberry.Schema(
        query=RoutingQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


_CHILD_ROUTING_QUERY = "{ categories { name items { name } } }"


def test_planned_prefetch_child_may_not_pin_its_own_connection(db):
    """A child ``get_queryset`` calling ``.using(...)`` fails the planned relation closed.

    The walker seeds the prefetch child unrouted and never holds the parent the
    child will be attached to, so the child's effective alias is ``None`` and ANY
    explicit alias - the connection the request is already on included - is a
    divergence rather than a match. Refusing it is what keeps one resolution's
    parent rows and related rows on one connection; a second database is only
    what makes the consequence visible, not what makes the hook's alias explicit.
    """
    services.seed_data(1)

    payload = _post_visibility_query(
        _child_routing_schema(lambda cls, queryset, info: queryset.using("default")),
        _CHILD_ROUTING_QUERY,
    )

    assert payload["data"] is None
    assert len(payload["errors"]) == 1, payload
    message = payload["errors"][0]["message"]
    assert "RoutingItemType.get_queryset" in message
    assert "routed to alias 'default'" in message


def test_planned_prefetch_child_still_serves_rows_when_the_hook_only_narrows(db):
    """The control: an unrouted hook still scopes the planned child and serves its rows."""
    services.seed_data(1)
    Item.objects.update(is_private=False)
    hidden = Item.objects.order_by("pk").first()
    assert hidden is not None
    Item.objects.filter(pk=hidden.pk).update(is_private=True, name="hidden-from-planned-child")

    payload = _post_visibility_query(
        _child_routing_schema(lambda cls, queryset, info: queryset.filter(is_private=False)),
        _CHILD_ROUTING_QUERY,
    )

    assert payload.get("errors") is None, payload
    served = sorted(row["name"] for page in payload["data"]["categories"] for row in page["items"])
    assert served == sorted(
        Item.objects.filter(is_private=False).values_list("name", flat=True),
    )
    assert "hidden-from-planned-child" not in served
