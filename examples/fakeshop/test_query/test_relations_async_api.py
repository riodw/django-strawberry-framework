"""Live GraphQL proof that generated relations lazy-load and read prefetches in async.

``django_strawberry_framework/types/resolvers.py`` grew three async arms that
lazy-load a relation through ``sync_to_async(getattr, thread_sensitive=True)``
when the row arrives unfetched inside a running event loop --
``types/resolvers.py::forward_resolver``,
``types/resolvers.py::reverse_one_to_one_resolver`` and
``types/resolvers.py::many_resolver`` (the last through its
``bounded_rows_async`` no-visibility branch). Before those arms existed the
relation read raised ``SynchronousOnlyOperation`` and surfaced as a top-level
error, so ``errors is None`` plus an exact ``data`` match IS the regression
assertion here; weakening either half to a bare status check discards the
point of the suite.

Two constraints govern every lazy-load case in this module, and both are
load-bearing:

* **The targets must have no custom visibility.** Each new arm is gated on
  ``visibility_type is None``, so the relation target type must not declare
  ``get_queryset``. ``LoanType``, ``PatronType`` and ``MembershipCardType``
  qualify; ``BookType``, ``ShelfType``, ``BranchType`` and ``IssueType`` do
  not, and neither does the products app's ``CategoryType`` -- routing a case
  through any of those lands on the visibility arm instead and silently stops
  covering the intended line while still passing.
* **No optimizer.** Each lazy-load schema below is built WITHOUT
  ``DjangoOptimizerExtension`` on purpose. An installed optimizer plans the
  relation, the row arrives already fetched, ``_will_lazy_load_single`` is
  False, and the async arms never execute.

The prefetched cases invert both constraints on purpose. Their many-side rows
arrive already in Django's prefetch cache - planned by the composed schema's
optimizer, or prefetched by the consumer's own root resolver - and
``many_resolver`` must read each relation kind under the key Django stored it
under. The reverse side of ``VenueSponsor.venues``, declared without
``related_name``, is keyed by its query name ``venuesponsor`` rather than its
``venuesponsor_set`` accessor; a miss there hands ``bounded_rows_async`` the
evaluated prefetch queryset, whose slice is a ``list`` no ``async for`` can
iterate. The reverse-FK ``repairticket`` targets ``RepairTicketType``, so its
unplanned consumer prefetch also crosses the visibility arm.

The shipped fakeshop mount at ``examples/fakeshop/config/urls.py`` is the SYNC
view, so -- exactly as ``test_products_visibility_api.py`` does -- this module
supplies its own ``AsyncDjangoGraphQLView`` mount over the app's registered
types rather than inventing throwaway ones.
"""

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.test import override_settings
from django.urls import clear_url_caches, path

from django_strawberry_framework import strawberry_config
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView

_CURRENT: dict[str, object | None] = {"schema": None}


async def _async_graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-async/", _async_graphql_view)]


def _seed_loan_graph():
    """Create a patron holding two loans, plus the branch/shelf/book chain they need.

    Inline ``Model.objects.create(...)`` rather than a seed helper: the library
    acceptance app has no ``services.py``, so this is the idiom AGENTS.md
    prescribes for the library tier.
    """
    branch = models.Branch.objects.create(name="Async Branch")
    shelf = models.Shelf.objects.create(code="ASYNC-1", branch=branch)
    first = models.Book.objects.create(title="Async First", shelf=shelf)
    second = models.Book.objects.create(title="Async Second", shelf=shelf)
    patron = models.Patron.objects.create(name="Async Patron")
    models.Loan.objects.create(book=first, patron=patron, note="first-note")
    models.Loan.objects.create(book=second, patron=patron, note="second-note")
    return patron


def _seed_card_graph():
    """Create one patron holding a card and one holding none.

    The absent-card row is what drives ``reverse_one_to_one_resolver``'s
    ``except related_does_not_exist: return None`` arm; without it the test
    would only cover the present half.
    """
    with_card = models.Patron.objects.create(name="Patron With Card")
    models.MembershipCard.objects.create(patron=with_card, barcode="CARD-ASYNC-1")
    without_card = models.Patron.objects.create(name="Patron Without Card")
    return with_card, without_card


async def _post_async(schema, query):
    """POST ``query`` against ``schema`` over the live async mount, returning the payload."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            res = await AsyncTestClient().query(
                query,
                assert_no_errors=False,
                url="/graphql-async/",
            )
        assert res.response.status_code == 200
        return res.response.json()
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


@pytest.mark.django_db(transaction=True)
async def test_async_forward_fk_lazy_loads_over_http():
    """A forward FK on an unfetched row lazy-loads inside the event loop.

    ``Loan.patron`` targets ``PatronType``, which declares no ``get_queryset``,
    so ``forward_resolver`` takes its ``visibility_type is None`` async arm.
    """
    await sync_to_async(_seed_loan_graph)()

    def _build():
        from apps.library.schema import LoanType

        @strawberry.type
        class Query:
            @strawberry.field
            async def loans(self) -> list[LoanType]:
                return await sync_to_async(list)(models.Loan.objects.order_by("note"))

        return strawberry.Schema(query=Query, config=strawberry_config())

    schema = await sync_to_async(_build)()
    payload = await _post_async(schema, "{ loans { note patron { name } } }")

    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "loans": [
            {"note": "first-note", "patron": {"name": "Async Patron"}},
            {"note": "second-note", "patron": {"name": "Async Patron"}},
        ],
    }


@pytest.mark.django_db(transaction=True)
async def test_async_many_side_lazy_loads_over_http():
    """A reverse-FK many side on an unfetched row lazy-loads inside the event loop.

    ``Patron.loans`` targets ``LoanType``, which declares no ``get_queryset``,
    so ``many_resolver`` reaches its ``bounded_rows_async`` branch rather than
    the ``_visible_many_rows`` one -- the arm no other live case touches.
    """
    await sync_to_async(_seed_loan_graph)()

    def _build():
        from apps.library.schema import PatronType

        @strawberry.type
        class Query:
            @strawberry.field
            async def patrons(self) -> list[PatronType]:
                return await sync_to_async(list)(models.Patron.objects.order_by("name"))

        return strawberry.Schema(query=Query, config=strawberry_config())

    schema = await sync_to_async(_build)()
    payload = await _post_async(schema, "{ patrons { name loans { note } } }")

    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "patrons": [
            {"name": "Async Patron", "loans": [{"note": "first-note"}, {"note": "second-note"}]},
        ],
    }


@pytest.mark.django_db(transaction=True)
async def test_async_reverse_one_to_one_lazy_loads_over_http():
    """A reverse OneToOne lazy-loads inside the event loop, present and absent alike.

    ``Patron.card`` targets ``MembershipCardType``, which declares no
    ``get_queryset``, so ``reverse_one_to_one_resolver`` takes its
    ``visibility_type is None`` async arm. The second row carries no card and
    pins the ``DoesNotExist -> None`` half of that arm.
    """
    await sync_to_async(_seed_card_graph)()

    def _build():
        from apps.library.schema import PatronType

        @strawberry.type
        class Query:
            @strawberry.field
            async def patrons(self) -> list[PatronType]:
                return await sync_to_async(list)(models.Patron.objects.order_by("pk"))

        return strawberry.Schema(query=Query, config=strawberry_config())

    schema = await sync_to_async(_build)()
    payload = await _post_async(schema, "{ patrons { name card { barcode } } }")

    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "patrons": [
            {"name": "Patron With Card", "card": {"barcode": "CARD-ASYNC-1"}},
            {"name": "Patron Without Card", "card": None},
        ],
    }


def _seed_sponsor_graph():
    """Two venues, two sponsors over the no-``related_name`` M2M, and three tickets.

    ``VenueSponsor.venues`` declares no ``related_name``: a venue reaches its
    sponsors through the ``venuesponsor_set`` accessor while Django keys the
    prefetched rows under the query name ``venuesponsor``. ``RepairTicket.venue``
    is the reverse-FK control, whose prefetch key IS its accessor; the
    withdrawn ``VOID-`` ticket is hidden by ``RepairTicketType.get_queryset``.
    """
    annex = models.Venue.objects.create(name="Annex")
    depot = models.Venue.objects.create(name="Depot")
    models.RepairTicket.objects.create(code="T-1", venue=annex)
    models.RepairTicket.objects.create(code="VOID-2", venue=annex)
    models.RepairTicket.objects.create(code="T-3", venue=depot)
    acme = models.VenueSponsor.objects.create(name="Acme")
    acme.venues.add(annex, depot)
    models.VenueSponsor.objects.create(name="Globex").venues.add(annex)


_SPONSOR_GRAPH_DATA = {
    "venues": [
        {
            "name": "Annex",
            "venuesponsor": [{"name": "Acme"}, {"name": "Globex"}],
            "repairticket": [{"code": "T-1"}],
        },
        {"name": "Depot", "venuesponsor": [{"name": "Acme"}], "repairticket": [{"code": "T-3"}]},
    ],
    "sponsors": [
        {"name": "Acme", "venues": [{"name": "Annex"}, {"name": "Depot"}]},
        {"name": "Globex", "venues": [{"name": "Annex"}]},
    ],
}


@pytest.mark.django_db(transaction=True)
async def test_async_planned_many_side_prefetches_resolve_over_http():
    """Optimizer-planned prefetches of every many-side kind resolve inside the event loop.

    The composed fakeshop schema (``DjangoOptimizerExtension`` installed) plans
    ``venuesponsor`` (reverse M2M without ``related_name``), ``venues`` (its
    forward side) and ``repairticket`` (reverse FK) as prefetches, so
    ``many_resolver`` must find each one in ``_prefetched_objects_cache`` under
    the key Django stored it under. Reading the reverse M2M under its accessor
    ``venuesponsor_set`` misses, and the manager fall-through then hands
    ``bounded_rows_async`` the prefetched, already-evaluated queryset, whose
    slice is a ``list`` the ``async for`` cannot iterate.
    """
    await sync_to_async(_seed_sponsor_graph)()

    def _build():
        from config.schema import schema

        return schema

    schema = await sync_to_async(_build)()
    payload = await _post_async(
        schema,
        """
        {
          venues: allLibraryVenues { name venuesponsor { name } repairticket { code } }
          sponsors: allLibraryVenueSponsors { name venues { name } }
        }
        """,
    )

    assert payload.get("errors") is None, payload
    assert payload["data"] == _SPONSOR_GRAPH_DATA


@pytest.mark.django_db(transaction=True)
async def test_async_consumer_prefetched_many_side_resolves_over_http():
    """A consumer's own ``prefetch_related`` of every many-side kind resolves in the event loop.

    No optimizer: the root resolvers prefetch the relations themselves, so the
    rows reach ``many_resolver`` in Django's prefetch cache unplanned. The reverse
    M2M (``venuesponsor``, target without ``get_queryset``) and the forward M2M
    (``venues``) are served from that cache; the reverse FK ``repairticket``
    targets ``RepairTicketType``, whose custom ``get_queryset`` re-reads the
    unplanned cache through ``_visible_many_rows`` and keeps ``VOID-2`` hidden.
    """
    await sync_to_async(_seed_sponsor_graph)()

    def _build():
        from apps.library.schema import VenueSponsorType, VenueType

        @strawberry.type
        class Query:
            @strawberry.field
            async def venues(self) -> list[VenueType]:
                return await sync_to_async(list)(
                    models.Venue.objects.prefetch_related(
                        "venuesponsor_set",
                        "repairticket_set",
                    ).order_by("name"),
                )

            @strawberry.field
            async def sponsors(self) -> list[VenueSponsorType]:
                return await sync_to_async(list)(
                    models.VenueSponsor.objects.prefetch_related("venues").order_by("name"),
                )

        return strawberry.Schema(query=Query, config=strawberry_config())

    schema = await sync_to_async(_build)()
    payload = await _post_async(
        schema,
        """
        {
          venues { name venuesponsor { name } repairticket { code } }
          sponsors { name venues { name } }
        }
        """,
    )

    assert payload.get("errors") is None, payload
    assert payload["data"] == _SPONSOR_GRAPH_DATA
