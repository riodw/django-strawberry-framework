"""Tests for ``django_strawberry_framework.utils.typing``."""

from django_strawberry_framework.utils import unwrap_graphql_type
from django_strawberry_framework.utils.typing import unwrap_return_type


def test_unwrap_return_type_handles_typing_list():
    """``list[T]`` annotation unwraps to ``T``."""

    class Inner:
        pass

    assert unwrap_return_type(list[Inner]) is Inner


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
