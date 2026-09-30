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
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from .conf import upstream_patches_enabled

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from collections.abc import Callable, Iterable

    from graphql import FieldNode, GraphQLList, GraphQLOutputType, GraphQLResolveInfo
    from graphql.execution.execute import ExecutionContext as _ExecutionContext
    from graphql.pyutils import AwaitableOrValue, Path

    _CompleteListValue = Callable[
        [
            _ExecutionContext,
            GraphQLList[GraphQLOutputType],
            list[FieldNode],
            GraphQLResolveInfo,
            Path,
            AsyncIterable[object] | Iterable[object],
        ],
        AwaitableOrValue[list[object]],
    ]

# Every graphql-core release the ``graphql-core<3.3`` pin in ``pyproject.toml`` admits
# defines both names here; ``None`` stands in for a release that moves one, and
# ``_upstream_captures`` refuses it before anything is patched or called.
ExecutionContext: "type[_ExecutionContext] | None"
is_iterable: "Callable[[object], bool] | None"
try:
    from graphql.execution.execute import ExecutionContext
    from graphql.pyutils import is_iterable
except ImportError:  # pragma: no cover - exercised through patched imports in tests.
    ExecutionContext = None
    is_iterable = None


_PATCH_OWNER_ATTRIBUTE = "_django_strawberry_framework_patch_owner"
_PATCH_ORIGINAL_ATTRIBUTE = "_django_strawberry_framework_original"
_PATCH_OWNER = "django_strawberry_framework._graphql_core_patches"


def _captured_upstream_method(owner: type | None, name: str) -> object:
    if owner is None:
        return None
    method = owner.__dict__.get(name)
    patch_owner = getattr(method, _PATCH_OWNER_ATTRIBUTE, None)
    if patch_owner == _PATCH_OWNER or (
        isinstance(patch_owner, str) and patch_owner.startswith("django_strawberry_framework.")
    ):
        return getattr(method, _PATCH_ORIGINAL_ATTRIBUTE, None)
    return method


# ``None`` or a reshaped value until ``_validate_upstream_shape`` refuses it; the
# wrapper reads it only through ``_upstream_captures``, which refuses ``None``.
_original_complete_list_value = cast(
    "_CompleteListValue | None",
    _captured_upstream_method(ExecutionContext, "complete_list_value"),
)


class _UpstreamCaptures(NamedTuple):
    """The module's upstream captures, each proven present by ``_upstream_captures``."""

    execution_context: "type[_ExecutionContext]"
    is_iterable: "Callable[[object], bool]"
    complete_list_value: "_CompleteListValue"


def _upstream_captures() -> _UpstreamCaptures:
    """Return the current captures, refusing any that is a ``None`` drift sentinel.

    Reads the module globals on every call, so the install step and the wrapper
    both see the same captures ``_validate_upstream_shape`` pinned.
    """
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
    return _UpstreamCaptures(ExecutionContext, is_iterable, _original_complete_list_value)


def _validate_upstream_shape() -> _UpstreamCaptures:
    upstream = _upstream_captures()
    parameters = tuple(inspect.signature(upstream.complete_list_value).parameters.values())
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
    return upstream


def _patched_complete_list_value(
    self: "_ExecutionContext",
    return_type: "GraphQLList[GraphQLOutputType]",
    field_nodes: "list[FieldNode]",
    info: "GraphQLResolveInfo",
    path: "Path",
    result: "AsyncIterable[object] | Iterable[object]",
) -> "AwaitableOrValue[list[object]]":
    upstream = _upstream_captures()
    res = upstream.complete_list_value(
        self,
        return_type,
        field_nodes,
        info,
        path,
        result,
    )
    if (
        not upstream.is_iterable(result)
        and isinstance(result, AsyncIterable)
        and self.is_awaitable(res)
    ):

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
    upstream = _validate_upstream_shape()
    if _patch_is_installed():
        return
    # mypy: the patch itself, assigned over the executor class's method
    upstream.execution_context.complete_list_value = _patched_complete_list_value  # type: ignore[method-assign]
