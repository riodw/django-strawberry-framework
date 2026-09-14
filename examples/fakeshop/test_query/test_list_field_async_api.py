"""Live async-HTTP contract for ``DjangoListField`` arguments.

This suite is intentionally exempt from ``examples/fakeshop/graphql_client.py``:
that helper is synchronous by construction, while these cases cross a real
``AsyncClient`` -> ``AsyncDjangoGraphQLView`` -> graphql-core async-completion
boundary.

No case sets ``DJANGO_ALLOW_ASYNC_UNSAFE``. All tests carry
``@pytest.mark.django_db(transaction=True)``.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import pytest
import strawberry
from apps.library import models as library_models
from apps.library import schema as library_schema
from apps.library.orders import BranchOrder
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import EmptyResultSet
from django.db import models
from django.db.models.sql.compiler import SQLCompiler
from django.test import AsyncClient, override_settings
from django.urls import clear_url_caches, path

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    strawberry_config,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.orders import Ordering, OrderSet
from django_strawberry_framework.resource_policy import (
    DST_RESOURCE_DEADLINE,
    DST_RESOURCE_POLICY,
    RESOURCE_LIMIT_ERROR_CODE,
    ResourcePolicy,
)
from django_strawberry_framework.schema import DjangoSchema
from django_strawberry_framework.utils.context import stash_on_context
from django_strawberry_framework.views import AsyncDjangoGraphQLView

_CURRENT: dict[str, Any] = {"schema": None, "view_class": None}

_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}


async def _async_graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    view_class = _CURRENT["view_class"] or AsyncDjangoGraphQLView
    return await view_class.as_view(schema=schema)(request)


urlpatterns = [path("graphql-async/", _async_graphql_view)]


async def _post_async(
    schema: DjangoSchema | strawberry.Schema,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
    client: AsyncClient | None = None,
    extra_settings: dict[str, Any] | None = None,
    view_class: type[AsyncDjangoGraphQLView] | None = None,
) -> dict[str, Any]:
    _CURRENT["schema"] = schema
    _CURRENT["view_class"] = view_class
    override_dict: dict[str, Any] = {"ROOT_URLCONF": __name__}
    if extra_settings:
        override_dict.update(extra_settings)
    try:
        with override_settings(**override_dict):
            clear_url_caches()
            http_client = client or AsyncClient()
            body: dict[str, Any] = {"query": query}
            if variables is not None:
                body["variables"] = variables
            response = await http_client.post(
                "/graphql-async/",
                data=json.dumps(body),
                content_type="application/json",
            )
        assert response.status_code == 200
        return response.json()
    finally:
        _CURRENT["schema"] = None
        _CURRENT["view_class"] = None
        clear_url_caches()


class _ClosableAsyncIterator:
    """Async iterator that counts calls to __anext__ and aclose for lifecycle assertions."""

    def __init__(self, items: list[Any]) -> None:
        self.items = list(items)
        self.index = 0
        self.next_count = 0
        self.aclose_called = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.next_count += 1
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

    async def aclose(self):
        self.aclose_called += 1


# ---------------------------------------------------------------------------
# 1-4. Queryset completion: default, sync manager, sync qs, async def qs
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_queryset_completion_default_resolver():
    await sync_to_async(library_models.Branch.objects.create)(name="Alpha", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Bravo", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Charlie", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Delta", city="Boston")

    @strawberry.type
    class _DefaultQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    schema = DjangoSchema(query=_DefaultQuery, config=strawberry_config())
    query = """
    query {
      branches(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 1
        limit: 2
      ) {
        name
      }
    }
    """
    payload = await _post_async(schema, query)
    assert "errors" not in payload, payload
    names = [row["name"] for row in payload["data"]["branches"]]
    assert names == ["Bravo", "Charlie"]


@pytest.mark.django_db(transaction=True)
async def test_async_queryset_completion_sync_manager_resolver():
    await sync_to_async(library_models.Branch.objects.create)(name="Alpha", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Bravo", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Charlie", city="Boston")

    @strawberry.type
    class _ManagerQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: library_models.Branch.objects,
        )

    schema = DjangoSchema(query=_ManagerQuery, config=strawberry_config())
    query = """
    query {
      branches(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 1
        limit: 1
      ) {
        name
      }
    }
    """
    payload = await _post_async(schema, query)
    assert "errors" not in payload, payload
    assert payload["data"]["branches"] == [{"name": "Bravo"}]


@pytest.mark.django_db(transaction=True)
async def test_async_queryset_completion_sync_queryset_resolver():
    await sync_to_async(library_models.Branch.objects.create)(name="Alpha", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Bravo", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Charlie", city="Boston")

    @strawberry.type
    class _QsQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: library_models.Branch.objects.all(),
        )

    schema = DjangoSchema(query=_QsQuery, config=strawberry_config())
    query = """
    query {
      branches(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 1
        limit: 1
      ) {
        name
      }
    }
    """
    payload = await _post_async(schema, query)
    assert "errors" not in payload, payload
    assert payload["data"]["branches"] == [{"name": "Bravo"}]


@pytest.mark.django_db(transaction=True)
async def test_async_queryset_completion_async_def_queryset_resolver():
    await sync_to_async(library_models.Branch.objects.create)(name="Alpha", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Bravo", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Charlie", city="Boston")

    async def _resolve_branches(root, info):
        return library_models.Branch.objects.all()

    @strawberry.type
    class _AsyncQsQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_resolve_branches,
        )

    schema = DjangoSchema(query=_AsyncQsQuery, config=strawberry_config())
    query = """
    query {
      branches(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 1
        limit: 1
      ) {
        name
      }
    }
    """
    payload = await _post_async(schema, query)
    assert "errors" not in payload, payload
    assert payload["data"]["branches"] == [{"name": "Bravo"}]


# ---------------------------------------------------------------------------
# 5. Optimizer on vs off parity
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("with_optimizer", [False, True], ids=["plain", "optimized"])
async def test_async_queryset_completion_windows_the_same_rows(with_optimizer):
    """Each schema configuration owns a node, and both assert the SAME literal rows.

    Asserting the two payloads equal each other would go green whenever they are
    wrong together, and puts two configurations behind one node id. Naming the
    rows instead makes each configuration independently falsifiable.
    """
    await sync_to_async(library_models.Branch.objects.create)(name="Alpha", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Bravo", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Charlie", city="Boston")

    @strawberry.type
    class _BranchQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    # A factory over a singleton, never a constructing lambda: Strawberry runs a
    # non-instance entry once per operation, which would hand every request a
    # cold plan cache (spec-029 Decision 3).
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=_BranchQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer] if with_optimizer else None,
    )

    payload = await _post_async(
        schema,
        """
    query {
      branches(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 0
        limit: 2
      ) {
        name
      }
    }
    """,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["branches"] == [{"name": "Alpha"}, {"name": "Bravo"}]


# ---------------------------------------------------------------------------
# 6. Pipeline parity: visibility -> order -> window
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_pipeline_parity():
    # Visibility removes restricted city row BEFORE offset is counted
    await sync_to_async(library_models.Branch.objects.create)(name="Alpha", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Hidden", city="restricted")
    await sync_to_async(library_models.Branch.objects.create)(name="Bravo", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Charlie", city="Boston")

    @strawberry.type
    class _BranchQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    schema = DjangoSchema(query=_BranchQuery, config=strawberry_config())

    query_vis = """
    query {
      branches(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 1
        limit: 2
      ) {
        name
      }
    }
    """
    payload_vis = await _post_async(schema, query_vis)
    assert "errors" not in payload_vis, payload_vis
    names = [row["name"] for row in payload_vis["data"]["branches"]]
    assert names == ["Bravo", "Charlie"]

    # Anonymous user ordering by staff-gated 'name' hits permission denial before offset
    query_denied = """
    query {
      branches(
        orderBy: [{ name: ASC }]
        offset: 1
      ) {
        name
      }
    }
    """
    payload_denied = await _post_async(schema, query_denied)
    assert "errors" in payload_denied
    assert payload_denied["errors"][0]["extensions"]["code"] == "ORDER_PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# 7-9. Async iterables and cleanup
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_generator_cleanup_and_finally_witness():
    branches = [
        await sync_to_async(library_models.Branch.objects.create)(name=f"B{i}", city="Boston")
        for i in range(5)
    ]

    finally_entered = False

    async def _gen():
        nonlocal finally_entered
        try:
            for b in branches:
                yield b
        finally:
            finally_entered = True

    @strawberry.type
    class _GenQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: _gen(),
        )

    schema = DjangoSchema(query=_GenQuery, config=strawberry_config())
    payload = await _post_async(schema, "{ branches(limit: 2) { name } }")
    assert "errors" not in payload, payload
    assert len(payload["data"]["branches"]) == 2
    # Generator was advanced then stopped by limit ceiling; finally block witnessed
    assert finally_entered is True


@pytest.mark.django_db(transaction=True)
async def test_async_iterator_aclose_witness_on_limit_zero_and_rejection():
    branches = [
        await sync_to_async(library_models.Branch.objects.create)(name=f"B{i}", city="Boston")
        for i in range(3)
    ]

    holder: dict[str, _ClosableAsyncIterator | None] = {"it": None}

    def _resolver(root, info):
        it = _ClosableAsyncIterator(branches)
        holder["it"] = it
        return it

    @strawberry.type
    class _ItQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_resolver,
        )

    schema = DjangoSchema(query=_ItQuery, config=strawberry_config())

    # 1. limit: 0 short-circuit invokes aclose with 0 next calls
    p_lim0 = await _post_async(schema, "{ branches(limit: 0) { name } }")
    assert "errors" not in p_lim0, p_lim0
    assert p_lim0["data"]["branches"] == []
    assert holder["it"] is not None
    assert holder["it"].aclose_called == 1
    assert holder["it"].next_count == 0

    # 2. Nonzero offset rejection invokes aclose with 0 next calls
    p_off = await _post_async(schema, "{ branches(offset: 1) { name } }")
    assert p_off["errors"][0]["extensions"]["reason"] == "order_required"
    assert holder["it"].aclose_called == 1
    assert holder["it"].next_count == 0

    # 3. Non-null orderBy rejection invokes aclose with 0 next calls
    p_ord = await _post_async(schema, "{ branches(orderBy: [{ city: ASC }]) { name } }")
    assert p_ord["errors"][0]["extensions"]["reason"] == "queryset_required"
    assert holder["it"].aclose_called == 1
    assert holder["it"].next_count == 0


@pytest.mark.django_db(transaction=True)
async def test_async_generator_natural_exhaustion_does_not_call_aclose():
    branches = [
        await sync_to_async(library_models.Branch.objects.create)(name=f"B{i}", city="Boston")
        for i in range(2)
    ]

    holder: dict[str, _ClosableAsyncIterator | None] = {"it": None}

    def _resolver(root, info):
        it = _ClosableAsyncIterator(branches)
        holder["it"] = it
        return it

    @strawberry.type
    class _ExhaustQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_resolver,
        )

    schema = DjangoSchema(query=_ExhaustQuery, config=strawberry_config())
    # Request limit: 5 on 2 items -> natural exhaustion
    payload = await _post_async(schema, "{ branches(limit: 5) { name } }")
    assert "errors" not in payload, payload
    assert len(payload["data"]["branches"]) == 2
    assert holder["it"] is not None
    # aclose must NOT be called on natural exhaustion
    assert holder["it"].aclose_called == 0


#: Wide enough that nothing in the request can reach it on its own, so the only
#: thing that can end this budget is the resolver's own handoff below.
_UNREACHABLE_DEADLINE_SECONDS = 30


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "arguments",
    ["", "(limit: 0)"],
    ids=["default-window", "limit-zero"],
)
async def test_async_deadline_rejection_closes_the_source_it_never_advanced(arguments):
    """A budget that ends while the resolver awaits still closes the source it returned.

    The resolver produces its source first and the bounding seam reads the clock
    second, so a deadline that ends between those two points lands holding an
    iterator nobody will ever see again. It has produced no item, but an async
    source can own an open external resource from the moment it is constructed,
    so the rejection owes it exactly one ``aclose`` and no advance.

    The budget is ended by the resolver, after it awaits across the async
    boundary the claim is about - not by a deadline small enough that the request
    is expected to outrun it. A configured budget nothing else can reach makes
    the verdict the pipeline's rather than the machine's, and the await is what
    puts the expiry on the far side of the handoff a synchronous return never
    crosses.

    ``limit: 0`` takes the same path: the empty-window short-circuit sits
    downstream of the clock, so the close it promises on a healthy request has to
    survive a rejected one too.
    """
    branches = [
        await sync_to_async(library_models.Branch.objects.create)(name=f"B{i}", city="Boston")
        for i in range(3)
    ]

    holder: dict[str, Any] = {"it": None, "awaited": False}

    async def _resolver(root, info):
        it = _ClosableAsyncIterator(branches)
        holder["it"] = it
        await asyncio.sleep(0)
        holder["awaited"] = True
        stash_on_context(info.context, DST_RESOURCE_DEADLINE, time.monotonic() - 1)
        return it

    @strawberry.type
    class _DeadlineQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_resolver,
        )

    schema = DjangoSchema(
        query=_DeadlineQuery,
        config=strawberry_config(),
        resource_policy={"execution_deadline_seconds": _UNREACHABLE_DEADLINE_SECONDS},
    )

    payload = await _post_async(schema, "{ branches%s { name } }" % arguments)

    assert holder["awaited"] is True, "the resolver never reached its await"
    assert payload["data"] is None, payload
    extensions = payload["errors"][0]["extensions"]
    assert extensions["code"] == RESOURCE_LIMIT_ERROR_CODE, extensions
    assert extensions["bound"] == "execution_deadline_seconds", extensions
    assert extensions["limit"] == _UNREACHABLE_DEADLINE_SECONDS, extensions
    assert extensions["charged"] == _UNREACHABLE_DEADLINE_SECONDS + 1, extensions
    assert holder["it"] is not None
    assert holder["it"].next_count == 0
    assert holder["it"].aclose_called == 1


#: Long enough that the request cannot reach it on its own, short enough that
#: the resolver's own sleep below clears it by a wide margin.
_SHORT_DEADLINE_SECONDS = 0.2


@pytest.mark.django_db(transaction=True)
async def test_async_a_resolver_cannot_widen_the_row_bound_through_the_context():
    """``info.context`` is the consumer's, so the bound cannot live there.

    Every resolver in the request can write ``DST_RESOURCE_POLICY``. If the
    bounding seam read the request's policy back from that key, a resolver would
    hand itself a wider ``max_list_rows`` - and the ``offset`` ceiling derived
    from the same field - for the rest of the operation, without ever passing
    ``ResourcePolicy.narrowed``. The write happens after a real ``await``, so
    the widening attempt is on the far side of the async boundary from the seam
    that answers it.
    """
    for i in range(5):
        await sync_to_async(library_models.Branch.objects.create)(name=f"B{i}", city="Boston")

    holder: dict[str, Any] = {"awaited": False}

    async def _resolver(root, info):
        await asyncio.sleep(0)
        holder["awaited"] = True
        stash_on_context(info.context, DST_RESOURCE_POLICY, ResourcePolicy(max_list_rows=5))
        return library_models.Branch.objects.order_by("name")

    @strawberry.type
    class _WideningQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_resolver,
        )

    schema = DjangoSchema(
        query=_WideningQuery,
        config=strawberry_config(),
        resource_policy={"max_list_rows": 2},
    )

    payload = await _post_async(schema, "{ branches { name } }")

    assert holder["awaited"] is True, "the resolver never reached its await"
    assert "errors" not in payload, payload
    assert [row["name"] for row in payload["data"]["branches"]] == ["B0", "B1"]


class _NarrowsThenNeverExpires(float):
    """A written deadline that orders as EARLIER than the armed one, then never as passed.

    Both answers come out of the same object: the ``<`` a narrowing rule admits
    it by, and the reflected ``__le__`` that decides whether the clock has
    reached it.
    """

    def __lt__(self, other):
        return True

    def __le__(self, other):
        return False


#: The two spellings of "give me more wall clock", written to the mirror key a
#: resolver owns: an instant plainly past the budget, and one that presents as a
#: narrowing and then answers every reading as time remaining.
_WIDENED_DEADLINES = [
    lambda: time.monotonic() + 3600,
    lambda: _NarrowsThenNeverExpires(time.monotonic() - 1),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "widened",
    _WIDENED_DEADLINES,
    ids=["far-future", "narrowing-subclass"],
)
async def test_async_a_resolver_cannot_buy_more_wall_clock_through_the_context(widened):
    """A budget that ended while the resolver awaited cannot be pushed back out.

    The resolver sleeps well past its own configured deadline and then writes a
    widened instant under ``DST_RESOURCE_DEADLINE``. The sleep is what makes the
    expiry the pipeline's verdict rather than the machine's: it is longer than
    the budget by a multiple, so the only way a row goes green is if the seam
    trusted the key the resolver wrote.
    """
    for i in range(3):
        await sync_to_async(library_models.Branch.objects.create)(name=f"B{i}", city="Boston")

    holder: dict[str, Any] = {"awaited": False}

    async def _resolver(root, info):
        await asyncio.sleep(_SHORT_DEADLINE_SECONDS * 3)
        holder["awaited"] = True
        stash_on_context(info.context, DST_RESOURCE_DEADLINE, widened())
        return library_models.Branch.objects.order_by("name")

    @strawberry.type
    class _ReprieveQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_resolver,
        )

    schema = DjangoSchema(
        query=_ReprieveQuery,
        config=strawberry_config(),
        resource_policy={"execution_deadline_seconds": _SHORT_DEADLINE_SECONDS},
    )

    payload = await _post_async(schema, "{ branches { name } }")

    assert holder["awaited"] is True, "the resolver never reached its await"
    assert payload["data"] is None, payload
    extensions = payload["errors"][0]["extensions"]
    assert extensions["code"] == RESOURCE_LIMIT_ERROR_CODE, extensions
    assert extensions["bound"] == "execution_deadline_seconds", extensions
    assert extensions["limit"] == 1, extensions


# ---------------------------------------------------------------------------
# 10. Async error transport and naming
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_a_rejection_names_the_argument_in_the_schema_spelling():
    """Under ``auto_camel_case=False`` the error must name ``offset``, not a camel form."""

    @strawberry.type
    class _SnakeQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    payload = await _post_async(
        DjangoSchema(query=_SnakeQuery, config=strawberry_config(auto_camel_case=False)),
        "{ branches(order_by: [{ id: null }], offset: 1) { name } }",
    )

    assert payload["errors"][0]["extensions"]["argument"] == "offset"
    assert payload["errors"][0]["extensions"]["reason"] == "order_required"


@pytest.mark.django_db(transaction=True)
async def test_async_a_failing_aclose_does_not_displace_the_argument_rejection():
    """The rejection the client can act on stays primary when cleanup also fails."""

    class _FailingAcloseIterator(_ClosableAsyncIterator):
        async def aclose(self):
            await super().aclose()
            raise RuntimeError("simulated cleanup failure")

    branches = [
        await sync_to_async(library_models.Branch.objects.create)(name="B0", city="Boston"),
    ]

    @strawberry.type
    class _CleanupFailQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: _FailingAcloseIterator(branches),
        )

    payload = await _post_async(
        DjangoSchema(query=_CleanupFailQuery, config=strawberry_config()),
        "{ branches(offset: 1) { name } }",
    )

    assert "errors" in payload
    error = payload["errors"][0]
    assert error["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert error["extensions"]["reason"] == "order_required"


_ASYNC_OFFSET_WITH_ACTIVE_ORDER = (
    "{ branches(orderBy: [{ city: ASC }], offset: 1, limit: 1) { name } }"
)

#: Django spells a random order ``RAND()`` on SQLite and MySQL and ``RANDOM()`` on
#: PostgreSQL (``django/db/models/functions/math.py::Random``), so the prefix is
#: what an emitted-order assertion can read on every tier this suite runs under.
#: Neither the table nor a column here contains it.
_RANDOM_ORDER_SQL = "RAND"


async def _seed_three_branches_async():
    for name in ("Alpha", "Bravo", "Charlie"):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city="Boston")


def _offset_guard_schema():
    @strawberry.type
    class _OffsetGuardQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    return DjangoSchema(query=_OffsetGuardQuery, config=strawberry_config())


def _record_branch_sql(monkeypatch) -> list[str]:
    """Record every branch statement the request compiles, whichever thread runs it.

    ``CaptureQueriesContext`` watches one connection object, and the async
    pipeline hands its ORM work to a ``sync_to_async`` executor thread holding a
    different one - so the sync suite's instrument reads empty here for reasons
    that have nothing to do with the ordering under test. Recording at the
    compiler is the same observable taken one layer in: the statement is captured
    where it is built, which is inside whichever thread ends up building it.

    A query Django compiles to "no rows possible" never reaches the database and
    carries no ordering, so it is skipped rather than recorded. Only the plain
    SELECT compiler is read: compiling a write compiler a second time re-runs its
    pre-SQL setup, which for a multi-table update executes a SELECT and rewrites
    the query's own filter, so an instrument must not ask one for its SQL.
    """
    recorded: list[str] = []
    original_execute_sql = SQLCompiler.execute_sql

    def _recording_execute_sql(self, *args, **kwargs):
        if type(self) is SQLCompiler:
            try:
                sql = self.as_sql()[0]
            except EmptyResultSet:
                sql = ""
            if "library_branch" in sql:
                recorded.append(sql)
        return original_execute_sql(self, *args, **kwargs)

    monkeypatch.setattr(SQLCompiler, "execute_sql", _recording_execute_sql)
    return recorded


@pytest.mark.django_db(transaction=True)
async def test_async_offset_rejects_a_random_model_default(monkeypatch):
    """The async coloring reads the same effective order the sync one does.

    Both pipelines hand the sealed queryset to one guard, so the order the
    request will run under - here the model's own ``"?"``, left standing by an
    override that returns what it was given - has to reject the offset on either
    side. A guard that answered from ``query.order_by`` alone would see two empty
    collections and serve a re-shuffled page.
    """
    await _seed_three_branches_async()
    monkeypatch.setattr(library_models.Branch._meta, "ordering", ("?",))

    async def _apply_unchanged(cls, order_input, queryset, info, **kwargs):
        return queryset

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_apply_unchanged))
    branch_sql = _record_branch_sql(monkeypatch)

    payload = await _post_async(_offset_guard_schema(), _ASYNC_OFFSET_WITH_ACTIVE_ORDER)

    err = payload["errors"][0]
    assert err["extensions"]["reason"] == "order_required"
    assert err["extensions"]["argument"] == "offset"
    assert branch_sql == [], branch_sql


@pytest.mark.django_db(transaction=True)
async def test_async_offset_accepts_extra_ordering_over_a_dormant_random_order(monkeypatch):
    """The async twin of the acceptance half: a superseded ``"?"`` cannot reject the offset.

    ``extra`` ordering wins over ``query.order_by`` in the compiler, so the page
    comes back in id order and the dormant random term never reaches SQL. The
    returned row alone cannot say that: three rows in a re-shuffled result set
    put ``Bravo`` at the requested offset often enough to keep a broken guard
    green, so the emitted statement is what carries the claim - it has to order
    by ``id`` and mention no randomness at all.
    """
    await _seed_three_branches_async()

    async def _extra_supersedes_random(cls, order_input, queryset, info, **kwargs):
        return queryset.order_by("?").extra(order_by=["id"])

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_extra_supersedes_random))
    branch_sql = _record_branch_sql(monkeypatch)

    payload = await _post_async(_offset_guard_schema(), _ASYNC_OFFSET_WITH_ACTIVE_ORDER)

    assert "errors" not in payload, payload
    assert payload["data"]["branches"] == [{"name": "Bravo"}]
    assert len(branch_sql) == 1, branch_sql
    statement = branch_sql[0].upper()
    assert "OFFSET 1" in statement, statement
    assert _RANDOM_ORDER_SQL not in statement, statement
    assert "ORDER BY" in statement, statement
    assert '"ID"' in statement or "(ID)" in statement, statement


@pytest.mark.django_db(transaction=True)
async def test_async_offset_rejects_extra_random_ordering_over_a_stable_order(monkeypatch):
    """The control for the acceptance above: the same precedence, opposite verdict.

    ``extra`` ordering supersedes an explicit ``order_by`` whichever way the two
    are spelled, so a stable order standing behind a random ``extra`` term is the
    dormant one. Without this row an acceptance could be produced by a guard that
    stopped reading ``extra_order_by`` altogether and simply trusted the explicit
    collection.
    """
    await _seed_three_branches_async()

    async def _random_extra_supersedes_stable(cls, order_input, queryset, info, **kwargs):
        return queryset.order_by("name").extra(order_by=["?"])

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_random_extra_supersedes_stable))
    branch_sql = _record_branch_sql(monkeypatch)

    payload = await _post_async(_offset_guard_schema(), _ASYNC_OFFSET_WITH_ACTIVE_ORDER)

    err = payload["errors"][0]
    assert err["extensions"]["reason"] == "order_required"
    assert err["extensions"]["argument"] == "offset"
    assert branch_sql == [], branch_sql


# ---------------------------------------------------------------------------
# 11. Async post-OrderSet seals
# ---------------------------------------------------------------------------


_BRANCH_ORDER_ASYNC_SHAPE_PREFIX = (
    "BranchOrder.apply_async must return an unevaluated, unsliced, uncombined "
    "QuerySet of Branch rows; got "
)


class _AsyncDeferredFilterQuerySet(models.QuerySet):
    """A queryset SUBCLASS, which is what makes an unresolved deferred filter untrusted."""


class _ResidualAwaitable:
    """An awaitable returned by an already-awaited seam, which nothing will await."""

    def __await__(self):
        return iter(())


async def _async_combined(cls, order_input, queryset, info, **kwargs):
    return queryset.filter(name="A").union(queryset.filter(name="B"))


async def _async_evaluated(cls, order_input, queryset, info, **kwargs):
    async for _row in queryset:
        pass
    return queryset


async def _async_materialized(cls, order_input, queryset, info, **kwargs):
    return [branch async for branch in queryset]


async def _async_projection(cls, order_input, queryset, info, **kwargs):
    return queryset.values("name")


async def _async_wrong_model(cls, order_input, queryset, info, **kwargs):
    return library_models.Book.objects.all()


async def _async_sliced(cls, order_input, queryset, info, **kwargs):
    return queryset.order_by("name")[:1]


async def _async_in_place_routing(cls, order_input, queryset, info, **kwargs):
    queryset._hints = {"tenant": 2}
    return queryset


async def _async_untrusted(cls, order_input, queryset, info, **kwargs):
    candidate = _AsyncDeferredFilterQuerySet(model=library_models.Branch)
    candidate._deferred_filter = (False, (), {"name": "A"})
    return candidate


def _async_non_awaitable(cls, order_input, queryset, info, **kwargs):
    return queryset


async def _async_residual(cls, order_input, queryset, info, **kwargs):
    return _ResidualAwaitable()


#: One row per defect class the post-``OrderSet`` seal names over the async view:
#: ``(override, expected message start, required substrings)``. The last two
#: rows are the async protocol itself rather than the result shape - a sync
#: override of an async seam, and a seam that hands back a second awaitable.
_MALFORMED_APPLY_ASYNC_ROWS = (
    (
        "combined",
        _async_combined,
        _BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "combined defect",
        (),
    ),
    (
        "evaluated",
        _async_evaluated,
        _BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "evaluated defect",
        (),
    ),
    (
        "materialized-list",
        _async_materialized,
        _BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "type defect",
        (),
    ),
    (
        "projection",
        _async_projection,
        _BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "projection defect",
        (),
    ),
    (
        "wrong-model",
        _async_wrong_model,
        _BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "table defect",
        (),
    ),
    (
        "sliced",
        _async_sliced,
        _BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "sliced defect",
        (),
    ),
    (
        "routing-rewritten-in-place",
        _async_in_place_routing,
        "BranchOrder.apply_async changed database routing intent",
        ("got db=None, hints={'tenant': 2}",),
    ),
    (
        "unresolved-deferred-filter",
        _async_untrusted,
        _BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "untrusted defect",
        ("carries an unresolved deferred filter",),
    ),
    (
        "sync-override-of-an-async-seam",
        _async_non_awaitable,
        "BranchOrder.apply_async",
        ("returned a non-awaitable value",),
    ),
    (
        "residual-awaitable",
        _async_residual,
        "BranchOrder.apply_async",
        ("returned a residual awaitable value",),
    ),
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("override", "message_start", "substrings"),
    [row[1:] for row in _MALFORMED_APPLY_ASYNC_ROWS],
    ids=[row[0] for row in _MALFORMED_APPLY_ASYNC_ROWS],
)
async def test_async_holder_branches_a_malformed_apply_async_result_names_its_own_defect(
    monkeypatch,
    override,
    message_start,
    substrings,
):
    """Every malformed ``apply_async`` result names its exact defect, on its own node.

    ``apply_async`` is a distinct executable seam from ``apply_sync``, so each
    defect class owes a proof on this colour too - and, being independent
    boundaries, each owes its own node id rather than a place in a matrix where
    an early failure stops the rest from running.
    """
    await sync_to_async(library_models.Branch.objects.create)(name="A", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="B", city="Boston")

    @strawberry.type
    class _BranchQuery:
        all_library_branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
        )

    schema = DjangoSchema(query=_BranchQuery, config=strawberry_config())
    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(override))

    payload = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )

    assert payload["data"] is None
    message = payload["errors"][0]["message"]
    assert message.startswith(message_start), message
    for substring in substrings:
        assert substring in message, message


class _NestedTenantRouter:
    """Routes by state INSIDE the tenant hint object - ordinary, legal router code."""

    def db_for_read(self, model, **hints):
        token = hints.get("tenant")
        return token["alias"] if type(token) is dict else None

    def db_for_write(self, model, **hints):
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None


@pytest.mark.django_db(transaction=True)
async def test_async_mutable_hint_cannot_reroute_the_completed_read(monkeypatch):
    """The async override's accepted result is pinned to the alias frozen before it ran.

    ``apply_async`` is a distinct executable seam from ``apply_sync``, so the
    routing attestation owes a proof on this colour too. The source carries a
    mutable tenant token the router reads into; the override edits it to name an
    alias this project does not configure and returns an ordinary ordered clone,
    so every hint object the seal compares is still the same object. Resolving
    the effective alias before the override ran, and pinning the result to it, is
    the only reason the read completes at all - a late resolution would reach for
    a connection that does not exist.
    """
    await sync_to_async(library_models.Branch.objects.create)(name="A", city="Boston")

    token = {"alias": "default"}

    async def _hint_mutating_apply_async(cls, order_input, queryset, info, **kwargs):
        token["alias"] = "no_such_alias"
        return queryset.order_by("name")

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_hint_mutating_apply_async))

    # The token rides the visibility hook's return, so the source the async
    # pipeline snapshots carries it; the default field is what commits this
    # field to the async coloring, so it takes no ``resolver=``.
    original_get_queryset = library_schema.BranchType.get_queryset

    def _hinted_get_queryset(cls, queryset, info, **kwargs):
        hinted = original_get_queryset(queryset, info, **kwargs)
        hinted._hints = {"tenant": token}
        return hinted

    monkeypatch.setattr(
        library_schema.BranchType,
        "get_queryset",
        classmethod(_hinted_get_queryset),
    )

    @strawberry.type
    class _TenantQuery:
        branches_tenant: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
        )

    schema = DjangoSchema(query=_TenantQuery, config=strawberry_config())
    payload = await _post_async(
        schema,
        "{ branchesTenant(orderBy: [{ city: ASC }]) { name } }",
        extra_settings={**_ERROR_POLICY_PASS_THROUGH, "DATABASE_ROUTERS": [_NestedTenantRouter()]},
    )

    assert "errors" not in payload, payload
    assert payload["data"]["branchesTenant"] == [{"name": "A"}]
    assert token["alias"] == "no_such_alias"


# ---------------------------------------------------------------------------
# 12. Naming and context isolation over the async view
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_rejection_reports_the_published_name_without_extra_converter_calls():
    """An async rejection names the PUBLISHED argument and adds no converter calls.

    Strawberry maps arguments through the converter on every execution; the
    framework's error path reads the executable schema instead of running it
    again, so a rejected request costs exactly as many converter calls as a
    successful one.
    """
    from strawberry.schema.name_converter import NameConverter

    class _CountingConverter(NameConverter):
        calls = 0

        def from_argument(self, argument):
            type(self).calls += 1
            return super().from_argument(argument).upper()

    @strawberry.type
    class _CountingQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    schema = DjangoSchema(
        query=_CountingQuery,
        config=strawberry_config(name_converter=_CountingConverter()),
    )

    before = _CountingConverter.calls
    p_ok = await _post_async(schema, "{ branches(LIMIT: 1) { name } }")
    assert "errors" not in p_ok, p_ok
    per_success = _CountingConverter.calls - before

    before = _CountingConverter.calls
    p_rejected = await _post_async(schema, "{ branches(OFFSET: -1) { name } }")
    assert p_rejected["errors"][0]["extensions"]["argument"] == "OFFSET"
    assert _CountingConverter.calls - before == per_success


_CONTEXT_CAPTURE: dict[str, Any] = {}


class _CapturingAsyncContextView(AsyncDjangoGraphQLView):
    async def get_context(self, request, response):
        context = await super().get_context(request, response)
        context.consumer_marker = _CONTEXT_CAPTURE["marker"]
        _CONTEXT_CAPTURE["context"] = context
        return context


class _FrozenContext:
    """A context that refuses every attribute write or delete after construction."""

    def __init__(self, request, response):
        object.__setattr__(self, "request", request)
        object.__setattr__(self, "response", response)

    def __setattr__(self, name, value):
        raise AttributeError(f"frozen context refuses write to {name!r}")

    def __delattr__(self, name):
        raise AttributeError(f"frozen context refuses delete of {name!r}")


class _FrozenAsyncContextView(AsyncDjangoGraphQLView):
    async def get_context(self, request, response):
        return _FrozenContext(request, response)


def _build_context_schema() -> DjangoSchema:
    @strawberry.type
    class _ContextQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)
        genres: DjangoConnection[library_schema.GenreType] = DjangoConnectionField(
            library_schema.GenreType,
        )

    return DjangoSchema(query=_ContextQuery, config=strawberry_config())


#: ``(id, control query, ordered query)`` - one entry per collection surface
#: whose ordering could leave a trace on the consumer's context.
_ORDERED_CONTEXT_REQUESTS: tuple[tuple[str, str, str], ...] = (
    (
        "list",
        "{ branches(limit: 1) { name } }",
        "{ branches(orderBy: [{ city: ASC }], offset: 1, limit: 1) { name } }",
    ),
    (
        "connection",
        "{ genres { edges { node { name } } } }",
        "{ genres(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
    ),
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("control_query", "ordered_query"),
    [row[1:] for row in _ORDERED_CONTEXT_REQUESTS],
    ids=[row[0] for row in _ORDERED_CONTEXT_REQUESTS],
)
async def test_async_ordering_leaves_the_consumer_context_exactly_as_found(
    control_query,
    ordered_query,
):
    """An async ordered surface adds nothing to ``info.context`` its control does not.

    The list and the connection reach the order-normalization handoff by
    different paths, so each owns a node: a leak on one must not be masked by the
    other's arm failing first.
    """
    for name in ("Alpha", "Bravo"):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city="Boston")
    await sync_to_async(library_models.Genre.objects.create)(name="Fiction")
    schema = _build_context_schema()

    observed: dict[str, Any] = {}
    for label, query in (("control", control_query), ("ordered", ordered_query)):
        marker = object()
        _CONTEXT_CAPTURE.clear()
        _CONTEXT_CAPTURE["marker"] = marker
        payload = await _post_async(schema, query, view_class=_CapturingAsyncContextView)
        assert "errors" not in payload, (label, payload)
        context = _CONTEXT_CAPTURE["context"]
        assert context.consumer_marker is marker
        observed[label] = set(vars(context))
    assert observed["ordered"] == observed["control"], observed


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "ordered_query",
    [row[2] for row in _ORDERED_CONTEXT_REQUESTS],
    ids=[row[0] for row in _ORDERED_CONTEXT_REQUESTS],
)
async def test_async_ordering_succeeds_on_a_context_that_forbids_writes(ordered_query):
    """A write-refusing context still serves each async ordered surface."""
    for name in ("Alpha", "Bravo"):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city="Boston")
    await sync_to_async(library_models.Genre.objects.create)(name="Fiction")
    schema = _build_context_schema()

    payload = await _post_async(schema, ordered_query, view_class=_FrozenAsyncContextView)

    assert "errors" not in payload, payload


@pytest.mark.django_db(transaction=True)
async def test_async_a_frozen_context_still_returns_the_windowed_rows():
    """The positive control: refusing the stash must not quietly empty the window."""
    for name in ("Alpha", "Bravo"):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city="Boston")
    schema = _build_context_schema()

    payload = await _post_async(
        schema,
        "{ branches(orderBy: [{ city: ASC }], offset: 1, limit: 1) { name } }",
        view_class=_FrozenAsyncContextView,
    )

    assert payload["data"]["branches"] == [{"name": "Bravo"}]


# ---------------------------------------------------------------------------
# Child-delegated ordering: the applied normalization reaches the offset guard
# ---------------------------------------------------------------------------


def _build_child_delegating_schema() -> DjangoSchema:
    @strawberry.type
    class _DelegatingQuery:
        all_library_branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
        )

    return DjangoSchema(query=_DelegatingQuery, config=strawberry_config())


async def _child_delegating_apply_async(
    cls,
    order_input,
    queryset,
    info,
):
    """A supported public override that hands the application to a child task."""
    return await asyncio.create_task(
        OrderSet.apply_async.__func__(cls, order_input, queryset, info),
    )


@pytest.mark.django_db(transaction=True)
async def test_async_child_delegated_ordering_still_orders_and_pages(monkeypatch):
    """An ``apply_async`` override that applies in a child task serves a correct page.

    The rejection row below only proves the guard SEES the child's work; this row
    proves the override stays usable - the ordering the client asked for is the
    ordering the page is cut from, with a positive offset riding it.
    """
    for name, city in (("Alpha", "Denver"), ("Bravo", "Boston"), ("Charlie", "Austin")):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city=city)
    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_child_delegating_apply_async))
    schema = _build_child_delegating_schema()

    payload = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }], offset: 1, limit: 1) { name city } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert "errors" not in payload, payload
    # city ASC is Austin / Boston / Denver, so offset 1 limit 1 is Bravo.
    assert payload["data"]["allLibraryBranches"] == [{"name": "Bravo", "city": "Boston"}]


@pytest.mark.django_db(transaction=True)
async def test_async_child_delegated_impure_ordering_is_rejected(monkeypatch):
    """A/B/B across a child-task delegation raises the typed purity rejection.

    The ordering the client receives is built inside the child task from the
    FIRST normalization. A handoff that could not carry that attestation back
    would leave the offset guard comparing the second and third normalizations
    to each other, agreeing, and blessing a page cut from terms it never saw.
    """
    for name, city in (("Alpha", "Denver"), ("Bravo", "Boston")):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city=city)

    sequence = [[("city", Ordering.ASC)], [("name", Ordering.DESC)], [("name", Ordering.DESC)]]
    calls = {"n": 0}

    def _impure_normalize(cls, order_input):
        result = sequence[min(calls["n"], len(sequence) - 1)]
        calls["n"] += 1
        return result

    monkeypatch.setattr(BranchOrder, "_normalize_input", classmethod(_impure_normalize))
    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_child_delegating_apply_async))
    schema = _build_child_delegating_schema()

    payload = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }], offset: 1) { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert payload["data"] is None
    assert "BranchOrder._normalize_input is not pure" in payload["errors"][0]["message"]
    assert calls["n"] == 2
