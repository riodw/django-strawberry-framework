"""Tests for ``django_strawberry_framework.utils.typing``."""

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


def test_unwrap_return_type_returns_direct_class_when_unwrapped():
    """A bare class with no wrapper passes through unchanged."""

    class Inner:
        pass

    assert unwrap_return_type(Inner) is Inner
