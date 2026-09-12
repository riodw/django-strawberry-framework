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
from typing import Any

import pytest
import strawberry
from apps.library import models as library_models
from apps.library import schema as library_schema
from apps.library.orders import BranchOrder
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import models
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
from django_strawberry_framework.schema import DjangoSchema
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
async def test_async_queryset_completion_optimizer_on_and_off():
    await sync_to_async(library_models.Branch.objects.create)(name="Alpha", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Bravo", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="Charlie", city="Boston")

    @strawberry.type
    class _BranchQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    schema_plain = DjangoSchema(query=_BranchQuery, config=strawberry_config())
    optimizer = DjangoOptimizerExtension()
    schema_opt = DjangoSchema(
        query=_BranchQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )

    query = """
    query {
      branches(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 0
        limit: 2
      ) {
        name
      }
    }
    """
    payload_plain = await _post_async(schema_plain, query)
    payload_opt = await _post_async(schema_opt, query)

    assert "errors" not in payload_plain, payload_plain
    assert "errors" not in payload_opt, payload_opt
    assert payload_plain["data"] == payload_opt["data"]


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


# ---------------------------------------------------------------------------
# 10. Async error transport and naming
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_error_transport_and_naming():
    # 1. auto_camel_case=False
    @strawberry.type
    class _SnakeQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    snake_schema = DjangoSchema(
        query=_SnakeQuery,
        config=strawberry_config(auto_camel_case=False),
    )
    p_snake = await _post_async(
        snake_schema,
        "{ branches(order_by: [{ id: null }], offset: 1) { name } }",
    )
    assert p_snake["errors"][0]["extensions"]["argument"] == "offset"
    assert p_snake["errors"][0]["extensions"]["reason"] == "order_required"

    # 2. Cleanup failure in aclose does not displace the primary error
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

    schema_clean = DjangoSchema(query=_CleanupFailQuery, config=strawberry_config())
    p_fail = await _post_async(schema_clean, "{ branches(offset: 1) { name } }")
    # Primary LIST_ARGUMENT_INVALID error must be preserved
    assert "errors" in p_fail
    err = p_fail["errors"][0]
    assert err["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err["extensions"]["reason"] == "order_required"


# ---------------------------------------------------------------------------
# 11. Async post-OrderSet seals
# ---------------------------------------------------------------------------


_BRANCH_ORDER_ASYNC_SHAPE_PREFIX = (
    "BranchOrder.apply_async must return an unevaluated, unsliced, uncombined "
    "QuerySet of Branch rows; got "
)


@pytest.mark.django_db(transaction=True)
async def test_async_holder_branches_post_orderset_seals(monkeypatch):
    """Every malformed ``apply_async`` result names its exact defect over the async view."""
    await sync_to_async(library_models.Branch.objects.create)(name="A", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="B", city="Boston")

    @strawberry.type
    class _BranchQuery:
        all_library_branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
        )

    schema = DjangoSchema(query=_BranchQuery, config=strawberry_config())
    query = "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }"

    async def _run(override) -> str:
        monkeypatch.setattr(BranchOrder, "apply_async", classmethod(override))
        payload = await _post_async(schema, query, extra_settings=_ERROR_POLICY_PASS_THROUGH)
        assert payload["data"] is None
        return payload["errors"][0]["message"]

    # 1. Combined return (union)
    async def _malicious_apply_combined(cls, order_input, queryset, info, **kwargs):
        return queryset.filter(name="A").union(queryset.filter(name="B"))

    message = await _run(_malicious_apply_combined)
    assert message.startswith(_BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "combined defect")

    # 2. Evaluated: the override iterated the queryset and returned the SAME cached object.
    async def _malicious_apply_evaluated(cls, order_input, queryset, info, **kwargs):
        async for _row in queryset:
            pass
        return queryset

    message = await _run(_malicious_apply_evaluated)
    assert message.startswith(_BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "evaluated defect")

    # 3. A materialized list is a non-queryset ``type`` defect, distinct from row 2.
    async def _malicious_apply_list(cls, order_input, queryset, info, **kwargs):
        return [b async for b in queryset]

    message = await _run(_malicious_apply_list)
    assert message.startswith(_BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "type defect")

    # 4. Projection return (values)
    async def _malicious_apply_proj(cls, order_input, queryset, info, **kwargs):
        return queryset.values("name")

    message = await _run(_malicious_apply_proj)
    assert message.startswith(_BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "projection defect")

    # 4b. Wrong model return (Book queryset instead of Branch)
    async def _malicious_apply_model(cls, order_input, queryset, info, **kwargs):
        return library_models.Book.objects.all()

    message = await _run(_malicious_apply_model)
    assert message.startswith(_BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "table defect")

    # 4c. Sliced after ordering.
    async def _malicious_apply_sliced(cls, order_input, queryset, info, **kwargs):
        return queryset.order_by("name")[:1]

    message = await _run(_malicious_apply_sliced)
    assert message.startswith(_BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "sliced defect")

    # 4d. Routing rewritten in place on the received queryset, compared against the
    #     pre-call snapshot rather than the mutated object.
    async def _malicious_apply_in_place_routing(cls, order_input, queryset, info, **kwargs):
        queryset._hints = {"tenant": 2}
        return queryset

    message = await _run(_malicious_apply_in_place_routing)
    assert message.startswith("BranchOrder.apply_async changed database routing intent")
    assert "got db=None, hints={'tenant': 2}" in message

    # 4e. A queryset SUBCLASS carrying an unresolved deferred filter - a predicate
    #     not yet baked into the query. Django leaves one only on an EXACT plain
    #     queryset, so a subclass holding one cannot be rebuilt and fails closed.
    class _DeferredFilterQuerySet(models.QuerySet):
        pass

    async def _malicious_apply_untrusted(cls, order_input, queryset, info, **kwargs):
        candidate = _DeferredFilterQuerySet(model=library_models.Branch)
        candidate._deferred_filter = (False, (), {"name": "A"})
        return candidate

    message = await _run(_malicious_apply_untrusted)
    assert message.startswith(_BRANCH_ORDER_ASYNC_SHAPE_PREFIX + "untrusted defect")
    assert "carries an unresolved deferred filter" in message

    # 5. A sync override of apply_async violates the public async protocol.
    def _malicious_apply_non_awaitable(cls, order_input, queryset, info, **kwargs):
        return queryset

    monkeypatch.setattr(
        BranchOrder,
        "apply_async",
        classmethod(_malicious_apply_non_awaitable),
    )
    p_non_awaitable = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert "returned a non-awaitable value" in p_non_awaitable["errors"][0]["message"]

    # 6. Awaiting apply_async once must not leave a second awaitable behind.
    class _ResidualAwaitable:
        def __await__(self):
            return iter(())

    async def _malicious_apply_residual(cls, order_input, queryset, info, **kwargs):
        return _ResidualAwaitable()

    monkeypatch.setattr(
        BranchOrder,
        "apply_async",
        classmethod(_malicious_apply_residual),
    )
    p_residual = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert "returned a residual awaitable value" in p_residual["errors"][0]["message"]


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


_ORDERED_CONTEXT_REQUESTS: tuple[tuple[str, str], ...] = (
    (
        "{ branches(limit: 1) { name } }",
        "{ branches(orderBy: [{ city: ASC }], offset: 1, limit: 1) { name } }",
    ),
    (
        "{ genres { edges { node { name } } } }",
        "{ genres(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
    ),
)


@pytest.mark.django_db(transaction=True)
async def test_async_ordering_leaves_the_consumer_context_exactly_as_found():
    """Async ordered lists and connections add nothing to ``info.context`` a control does not."""
    for name in ("Alpha", "Bravo"):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city="Boston")
    await sync_to_async(library_models.Genre.objects.create)(name="Fiction")
    schema = _build_context_schema()

    for control_query, ordered_query in _ORDERED_CONTEXT_REQUESTS:
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
async def test_async_ordering_succeeds_on_a_context_that_forbids_writes():
    """A write-refusing context still serves async ordered lists and connections."""
    for name in ("Alpha", "Bravo"):
        await sync_to_async(library_models.Branch.objects.create)(name=name, city="Boston")
    await sync_to_async(library_models.Genre.objects.create)(name="Fiction")
    schema = _build_context_schema()

    for _control_query, ordered_query in _ORDERED_CONTEXT_REQUESTS:
        payload = await _post_async(schema, ordered_query, view_class=_FrozenAsyncContextView)
        assert "errors" not in payload, payload
    p_list = await _post_async(
        schema,
        "{ branches(orderBy: [{ city: ASC }], offset: 1, limit: 1) { name } }",
        view_class=_FrozenAsyncContextView,
    )
    assert p_list["data"]["branches"] == [{"name": "Bravo"}]


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
