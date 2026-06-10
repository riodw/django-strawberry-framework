"""Tests for ``django_strawberry_framework.utils.typing``."""

import typing
from typing import Any

import pytest

from django_strawberry_framework.utils import unwrap_graphql_type
from django_strawberry_framework.utils.typing import (
    _MAX_TYPE_WRAPPER_DEPTH,
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
