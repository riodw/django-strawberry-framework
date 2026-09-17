"""Install-lifecycle tests for the graphql-core ``complete_list_value`` residual-awaitable patch.

System-under-test: :mod:`django_strawberry_framework._graphql_core_patches`,
applied at app-load by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

What stays here, and why a live request cannot express it:

- ``apply()`` lifecycle: installed at AppConfig load, idempotence, self-heal
  after a reverted executor method, missing-symbol / signature-drift
  ``RuntimeError``, and the ``APPLY_UPSTREAM_PATCHES`` global and per-dependency
  (``graphql_core`` vs ``strawberry``) toggles. A GraphQL document cannot show
  that ``apply()`` was the caller or that a missing capture refused to install.
- The captured upstream method still yielding a residual awaitable after one
  ``await``: that is the retirement sentinel (spec-050 Decision 13). With the
  patch installed a live request sees completed list data, never the residual
  coroutine.
- ``_captured_upstream_method(None, ...)`` returning ``None`` rather than
  raising: a graphql-core build that omits ``ExecutionContext`` never reaches a
  schema.

Wire-observable async list completion lives in
``examples/fakeshop/test_query/test_list_field_async_api.py`` (queryset
completion with synchronous children, and an async-iterable list whose child
fields are awaitable).
"""

import inspect
from unittest import mock

import pytest
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
    """The captured upstream method still yields a residual awaitable after one ``await``."""

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


def test_captured_upstream_method_returns_none_without_an_owner():
    """A missing owner class yields no captured method rather than an attribute error.

    ``_captured_upstream_method`` is called with whatever
    ``graphql.execution.execute`` exposes; a graphql-core build that does not
    ship ``ExecutionContext`` hands the helper ``None``, and the reinstall path
    has to treat that as "nothing captured".
    """
    assert patches._captured_upstream_method(None, "complete_list_value") is None
