"""Regression coverage for the dependency-owned graphql-core workaround."""

import inspect
from unittest import mock

import pytest
import strawberry
from graphql.execution.execute import ExecutionContext

from django_strawberry_framework import _graphql_core_patches as patches


class _SimpleAsyncIterable:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        async def gen():
            for item in self.items:
                yield item

        return gen()


def test_patch_is_installed_at_app_load_and_apply_is_idempotent():
    assert patches._patch_is_installed() is True
    patches.apply()
    patches.apply()
    assert patches._patch_is_installed() is True


def test_apply_reinstalls_a_reverted_executor_method():
    saved = ExecutionContext.__dict__["complete_list_value"]
    try:
        ExecutionContext.complete_list_value = patches._original_complete_list_value
        assert patches._patch_is_installed() is False
        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        ExecutionContext.complete_list_value = saved


def test_captured_upstream_still_returns_a_residual_awaitable():
    """Prove the installed upstream bug still exists before preserving its workaround."""

    class Context:
        is_awaitable = staticmethod(inspect.isawaitable)

        def complete_list_value(self, *_args):
            async def child_completion():
                return ["done"]

            return child_completion()

    first = patches._original_complete_list_value(
        Context(),
        object(),
        (),
        object(),
        object(),
        _SimpleAsyncIterable([object()]),
    )
    assert inspect.isawaitable(first)

    async def inspect_residual():
        residual = await first
        assert inspect.isawaitable(residual)
        residual.close()

    import asyncio

    asyncio.run(inspect_residual())


def test_apply_fails_loudly_when_upstream_shape_changes():
    with mock.patch.object(patches, "_original_complete_list_value", lambda self: None):
        with pytest.raises(RuntimeError, match="complete_list_value no longer"):
            patches.apply()


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("ExecutionContext", "ExecutionContext.complete_list_value"),
        ("is_iterable", "graphql.pyutils.is_iterable"),
        ("_original_complete_list_value", "ExecutionContext.complete_list_value"),
    ],
)
def test_apply_fails_loudly_when_required_upstream_symbols_are_missing(name, message):
    with mock.patch.object(patches, name, None):
        with pytest.raises(RuntimeError, match=message):
            patches.apply()


def test_apply_uses_independent_dependency_gate(settings):
    saved = ExecutionContext.__dict__["complete_list_value"]
    try:
        ExecutionContext.complete_list_value = patches._original_complete_list_value
        settings.DJANGO_STRAWBERRY_FRAMEWORK = {
            "APPLY_UPSTREAM_PATCHES": {"graphql_core": False},
        }
        patches.apply()
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {
            "APPLY_UPSTREAM_PATCHES": {"strawberry": False},
        }
        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        ExecutionContext.complete_list_value = saved


def test_apply_obeys_global_disable(settings):
    saved = ExecutionContext.__dict__["complete_list_value"]
    try:
        ExecutionContext.complete_list_value = patches._original_complete_list_value
        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
        patches.apply()
        assert patches._patch_is_installed() is False
    finally:
        ExecutionContext.complete_list_value = saved


async def test_patch_awaits_async_iterable_with_awaitable_children():
    @strawberry.type
    class Child:
        @strawberry.field
        async def name(self) -> str:
            return "resolved"

    @strawberry.type
    class Query:
        @strawberry.field
        def children(self) -> list[Child]:
            return _SimpleAsyncIterable([Child()])

    result = await strawberry.Schema(query=Query).execute("{ children { name } }")
    assert result.errors is None
    assert result.data == {"children": [{"name": "resolved"}]}


async def test_patch_preserves_async_iterable_with_synchronous_children():
    @strawberry.type
    class Child:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def children(self) -> list[Child]:
            return _SimpleAsyncIterable([Child(name="resolved")])

    result = await strawberry.Schema(query=Query).execute("{ children { name } }")
    assert result.errors is None
    assert result.data == {"children": [{"name": "resolved"}]}


def test_patch_delegates_synchronous_iterables():
    @strawberry.type
    class Query:
        @strawberry.field
        def values(self) -> list[str]:
            return ["resolved"]

    result = strawberry.Schema(query=Query).execute_sync("{ values }")
    assert result.errors is None
    assert result.data == {"values": ["resolved"]}
