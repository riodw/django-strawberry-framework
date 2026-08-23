"""Live GraphQL proof that generated relations lazy-load from an async context.

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

Two constraints govern every case in this module, and both are load-bearing:

* **The targets must have no custom visibility.** Each new arm is gated on
  ``visibility_type is None``, so the relation target type must not declare
  ``get_queryset``. ``LoanType``, ``PatronType`` and ``MembershipCardType``
  qualify; ``BookType``, ``ShelfType``, ``BranchType`` and ``IssueType`` do
  not, and neither does the products app's ``CategoryType`` -- routing a case
  through any of those lands on the visibility arm instead and silently stops
  covering the intended line while still passing.
* **No optimizer.** Each schema below is built WITHOUT
  ``DjangoOptimizerExtension`` on purpose. An installed optimizer plans the
  relation, the row arrives already fetched, ``_will_lazy_load_single`` is
  False, and the async arms never execute.

The shipped fakeshop mount at ``examples/fakeshop/config/urls.py`` is the SYNC
view, so -- exactly as ``test_products_visibility_api.py`` does -- this module
supplies its own ``AsyncDjangoGraphQLView`` mount over the app's registered
types rather than inventing throwaway ones.
"""

import json

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.test import AsyncClient, override_settings
from django.urls import clear_url_caches, path

from django_strawberry_framework import strawberry_config
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
            response = await AsyncClient().post(
                "/graphql-async/",
                data=json.dumps({"query": query}),
                content_type="application/json",
            )
        assert response.status_code == 200
        return response.json()
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
