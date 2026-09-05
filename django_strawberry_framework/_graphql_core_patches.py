"""Defensive patch for graphql-core async-iterable list completion.

``graphql-core``'s ``ExecutionContext.complete_list_value`` materializes an
``AsyncIterable`` and recursively completes the resulting list, but the installed
upstream implementation does not await a residual completion awaitable. Awaitable
child fields can therefore escape as an unawaited coroutine. The delegating wrapper
below awaits that residual value and otherwise preserves upstream behavior.

The patch has its own ``APPLY_UPSTREAM_PATCHES`` dependency key,
``"graphql_core"``. It can be retired independently when the captured upstream
implementation no longer exhibits the bug pinned by
``tests/test_graphql_core_patches.py``.
"""

import inspect
from collections.abc import AsyncIterable
from typing import Any

from .conf import upstream_patches_enabled

try:
    from graphql.execution.execute import ExecutionContext
    from graphql.pyutils import is_iterable
except ImportError:  # pragma: no cover - exercised through patched imports in tests.
    ExecutionContext = None  # type: ignore[assignment,misc]
    is_iterable = None  # type: ignore[assignment,misc]


_PATCH_OWNER_ATTRIBUTE = "_django_strawberry_framework_patch_owner"
_PATCH_ORIGINAL_ATTRIBUTE = "_django_strawberry_framework_original"
_PATCH_OWNER = "django_strawberry_framework._graphql_core_patches"


def _captured_upstream_method(owner: Any | None, name: str) -> Any:
    if owner is None:
        return None
    method = owner.__dict__.get(name)
    patch_owner = getattr(method, _PATCH_OWNER_ATTRIBUTE, None)
    if patch_owner == _PATCH_OWNER or (
        isinstance(patch_owner, str) and patch_owner.startswith("django_strawberry_framework.")
    ):
        return getattr(method, _PATCH_ORIGINAL_ATTRIBUTE, None)
    return method


_original_complete_list_value = _captured_upstream_method(
    ExecutionContext,
    "complete_list_value",
)


def _validate_upstream_shape() -> None:
    if (
        ExecutionContext is None
        or not callable(is_iterable)
        or not callable(_original_complete_list_value)
    ):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's graphql-core patch: expected "
            "ExecutionContext.complete_list_value and graphql.pyutils.is_iterable. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"graphql_core": False} '
            "or use a supported graphql-core version.",
        )
    parameters = tuple(inspect.signature(_original_complete_list_value).parameters.values())
    if len(parameters) != 6 or any(
        parameter.kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters
    ):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's graphql-core patch: "
            "ExecutionContext.complete_list_value no longer has the expected "
            "(self, return_type, field_nodes, info, path, result) signature. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"graphql_core": False} '
            "or use a supported graphql-core version.",
        )


def _patched_complete_list_value(
    self: Any,
    return_type: Any,
    field_nodes: Any,
    info: Any,
    path: Any,
    result: Any,
) -> Any:
    res = _original_complete_list_value(
        self,
        return_type,
        field_nodes,
        info,
        path,
        result,
    )
    if not is_iterable(result) and isinstance(result, AsyncIterable) and self.is_awaitable(res):

        async def _await_residual(awaitable: Any) -> Any:
            completed = await awaitable
            if self.is_awaitable(completed):
                return await completed
            return completed

        return _await_residual(res)
    return res


setattr(_patched_complete_list_value, _PATCH_OWNER_ATTRIBUTE, _PATCH_OWNER)
setattr(
    _patched_complete_list_value,
    _PATCH_ORIGINAL_ATTRIBUTE,
    _original_complete_list_value,
)


def _patch_is_installed() -> bool:
    return (
        ExecutionContext is not None
        and ExecutionContext.__dict__.get("complete_list_value") is _patched_complete_list_value
    )


def apply() -> None:
    """Install the graphql-core workaround when its independent gate is enabled."""
    if not upstream_patches_enabled("graphql_core"):
        return
    _validate_upstream_shape()
    if _patch_is_installed():
        return
    ExecutionContext.complete_list_value = _patched_complete_list_value
