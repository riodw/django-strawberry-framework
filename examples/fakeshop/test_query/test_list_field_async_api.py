"""Live async-HTTP contract for ``DjangoListField`` (spec-050 Slice 4).

This suite is intentionally exempt from ``examples/fakeshop/graphql_client.py``:
that helper is synchronous by construction, while these cases cross a real
``AsyncClient`` -> ``AsyncDjangoGraphQLView`` -> graphql-core async-completion
boundary.

No case sets ``DJANGO_ALLOW_ASYNC_UNSAFE``. All tests carry
``@pytest.mark.django_db(transaction=True)``.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
import strawberry
from apps.library import models as library_models
from apps.library import schema as library_schema
from apps.library.orders import BranchOrder
from asgiref.sync import sync_to_async
from django.conf import settings
from django.test import AsyncClient, override_settings
from django.urls import clear_url_caches, path

from django_strawberry_framework import (
    DjangoListField,
    strawberry_config,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.schema import DjangoSchema
from django_strawberry_framework.views import AsyncDjangoGraphQLView

_CURRENT: dict[str, object | None] = {"schema": None}

_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}


async def _async_graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-async/", _async_graphql_view)]


async def _post_async(
    schema: DjangoSchema | strawberry.Schema,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
    client: AsyncClient | None = None,
    extra_settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _CURRENT["schema"] = schema
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


@pytest.mark.django_db(transaction=True)
async def test_async_holder_branches_post_orderset_seals(monkeypatch):
    await sync_to_async(library_models.Branch.objects.create)(name="A", city="Boston")
    await sync_to_async(library_models.Branch.objects.create)(name="B", city="Boston")

    @strawberry.type
    class _BranchQuery:
        all_library_branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
        )

    schema = DjangoSchema(query=_BranchQuery, config=strawberry_config())

    # 1. Combined return (union)
    async def _malicious_apply_combined(cls, order_input, queryset, info, **kwargs):
        return queryset.filter(name="A").union(queryset.filter(name="B"))

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_malicious_apply_combined))
    p_comb = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }",
    )
    assert "errors" in p_comb
    assert p_comb["data"] is None

    # 2. Evaluated return (list)
    async def _malicious_apply_eval(cls, order_input, queryset, info, **kwargs):
        return [b async for b in queryset]

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_malicious_apply_eval))
    p_eval = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }",
    )
    assert "errors" in p_eval
    assert p_eval["data"] is None

    # 3. Projection return (values)
    async def _malicious_apply_proj(cls, order_input, queryset, info, **kwargs):
        return queryset.values("name")

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_malicious_apply_proj))
    p_proj = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }",
    )
    assert "errors" in p_proj
    assert p_proj["data"] is None

    # 4. Wrong model return (Book queryset instead of Branch)
    async def _malicious_apply_model(cls, order_input, queryset, info, **kwargs):
        return library_models.Book.objects.all()

    monkeypatch.setattr(BranchOrder, "apply_async", classmethod(_malicious_apply_model))
    p_model = await _post_async(
        schema,
        "{ allLibraryBranches(orderBy: [{ city: ASC }]) { name } }",
    )
    assert "errors" in p_model
    assert p_model["data"] is None

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
