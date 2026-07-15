"""Typing utility tests for async-callable detection and Strawberry, Python, and GraphQL unwrapping."""

import functools
import typing
from typing import Any

import pytest

from django_strawberry_framework.utils import unwrap_graphql_type
from django_strawberry_framework.utils.typing import (
    _MAX_TYPE_WRAPPER_DEPTH,
    is_async_callable,
    unwrap_container_type,
    unwrap_return_type,
)


def test_unwrap_return_type_handles_typing_list():
    """``list[T]`` annotation unwraps to ``T``."""

    class Inner:
        pass

    assert unwrap_return_type(list[Inner]) is Inner


def test_unwrap_return_type_handles_bare_typing_list():
    """``typing.List`` (no parameter) returns ``Any``.

    ``get_origin(typing.List) is list`` so the list branch fires, but
    ``get_args(typing.List)`` returns ``()``. The earlier shape indexed
    ``get_args(rt)[0]`` and ``IndexError``'d here; the fix returns ``Any``
    as the "unknown element type" sentinel.
    """
    assert unwrap_return_type(typing.List) is Any  # noqa: UP006


def test_unwrap_return_type_handles_bare_builtin_list():
    """A bare ``list`` (no parameter) returns ``Any``.

    ``get_origin(list)`` is ``None`` (a bare builtin is not a generic
    alias), so the list-origin branch does not fire and the dedicated
    ``rt is list`` branch returns the same ``Any`` sentinel as
    ``typing.List``.
    """
    assert unwrap_return_type(list) is Any


def test_unwrap_return_type_handles_strawberry_of_type():
    """A Strawberry-style wrapper exposing ``of_type`` unwraps to the inner type."""

    class Inner:
        pass

    class FakeStrawberryList:
        of_type = Inner

    assert unwrap_return_type(FakeStrawberryList()) is Inner


def test_unwrap_return_type_peels_only_one_layer():
    """The annotation helper keeps nested wrappers for callers to inspect."""

    class Inner:
        pass

    class Outer:
        of_type = list[Inner]

    assert unwrap_return_type(Outer()) == list[Inner]


def test_unwrap_graphql_type_peels_all_of_type_layers():
    """The GraphQL helper recursively unwraps wrapper stacks to the leaf type."""

    class Inner:
        pass

    class NonNull:
        def __init__(self, of_type):
            self.of_type = of_type

    class List:
        def __init__(self, of_type):
            self.of_type = of_type

    wrapped = NonNull(List(NonNull(Inner)))

    assert unwrap_graphql_type(wrapped) is Inner


def test_unwrap_graphql_type_peels_a_deep_but_finite_stack():
    """A stack just under the ceiling still peels to the leaf (no false overrun)."""

    class Inner:
        pass

    class Wrap:
        def __init__(self, of_type):
            self.of_type = of_type

    wrapped = Inner
    for _ in range(_MAX_TYPE_WRAPPER_DEPTH - 1):
        wrapped = Wrap(wrapped)

    assert unwrap_graphql_type(wrapped) is Inner


def test_unwrap_graphql_type_raises_on_cyclic_of_type_stack():
    """A cyclic ``of_type`` chain hits the bound and fails loud instead of spinning."""

    class Cyclic:
        @property
        def of_type(self):
            return self  # never bottoms out

    with pytest.raises(RuntimeError, match="cyclic or corrupt"):
        unwrap_graphql_type(Cyclic())


def test_unwrap_container_type_peels_containers_but_not_a_leaf_with_of_type():
    """Only ``StrawberryContainer`` layers peel; a leaf exposing ``of_type`` is NOT descended.

    The load-bearing distinction from ``unwrap_graphql_type``'s bare-``hasattr``
    contract (DRY review B3): an ``Edge`` subclass that happens to carry an
    ``of_type`` attribute must be returned as the leaf, not peeled into.
    """
    from strawberry.types.base import StrawberryList

    class Edge:
        of_type = "not a wrapper"

    assert unwrap_container_type(StrawberryList(of_type=Edge)) is Edge
    assert unwrap_container_type(Edge) is Edge


def test_unwrap_container_type_raises_on_cyclic_container_stack():
    """A cyclic container chain hits the Power-of-Ten bound and fails loud."""
    from strawberry.types.base import StrawberryList

    cyclic = StrawberryList(of_type=None)
    cyclic.of_type = cyclic  # never bottoms out

    with pytest.raises(RuntimeError, match="cyclic or corrupt"):
        unwrap_container_type(cyclic)


def test_unwrap_return_type_returns_direct_class_when_unwrapped():
    """A bare class with no wrapper passes through unchanged."""

    class Inner:
        pass

    assert unwrap_return_type(Inner) is Inner


def test_unwrap_graphql_type_passes_through_none():
    """``None`` carries no ``of_type`` attribute and passes through unchanged.

    The optimizer's ``_walk_gql_type`` recursion at
    ``optimizer/extension.py`` feeds ``getattr(field_obj, "type", None)``
    into this helper; the post-peel ``type_name is None`` gate downstream
    relies on the passthrough holding so the recursion terminates cleanly.
    """

    assert unwrap_graphql_type(None) is None


# ---------------------------------------------------------------------------
# is_async_callable -- shared by the field factories + GlobalID-callable validator
# ---------------------------------------------------------------------------


# These callables are never invoked; ``is_async_callable`` only reads their
# coroutine-function flags. (Test code is outside the coverage source.)
async def _async_fn(): ...


def _sync_fn(): ...


class _AsyncCallable:
    async def __call__(self): ...


class _SyncCallable:
    def __call__(self): ...


class _MethodHolder:
    @staticmethod
    async def async_static(): ...

    @staticmethod
    def sync_static(): ...

    @classmethod
    async def async_cls(cls): ...


# The RAW descriptor objects (as seen when a ``@staticmethod async def`` resolver
# is referenced by name INSIDE its own class body, e.g. ``resolver=async_static``);
# attribute access via the class would unwrap these to the underlying function.
_async_static_obj = _MethodHolder.__dict__["async_static"]
_sync_static_obj = _MethodHolder.__dict__["sync_static"]
_async_cls_obj = _MethodHolder.__dict__["async_cls"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (_async_fn, True),
        (_sync_fn, False),
        (_AsyncCallable(), True),  # async ``__call__`` instance
        (_SyncCallable(), False),
        (functools.partial(_async_fn), True),  # partial around an async function
        (functools.partial(_AsyncCallable()), True),  # partial around an async instance
        (functools.partial(_sync_fn), False),
        (_async_static_obj, True),  # raw ``staticmethod`` descriptor around an async def
        (_sync_static_obj, False),
        (_async_cls_obj, False),  # raw ``classmethod`` descriptors are not callable
        (functools.partial(_async_static_obj), True),  # partial around a staticmethod descriptor
    ],
)
def test_is_async_callable_sees_through_supported_wrappers(value, expected):
    """The predicate sees through supported async callable wrappers.

    These are the shapes ``inspect.iscoroutinefunction`` alone misses; both the
    public field factories and the GlobalID-callable validator depend on the
    shared predicate catching them at construction time. The raw ``staticmethod``
    case is reachable when a class-body resolver references the decorated method
    by name. The classmethod case pins the opposite boundary: its raw descriptor
    is not callable, even when its underlying function is async.
    """
    assert is_async_callable(value) is expected
