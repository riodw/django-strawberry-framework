"""The async package view's ``as_view`` returns a coroutine view callback, or refuses.

``views.py::AsyncDjangoGraphQLView.as_view`` extends Strawberry's
``AsyncGraphQLView.as_view``, which marks the callback a coroutine function. An
``as_view`` placed between the two that drops the mark would have Django call the
async view synchronously, so the package view refuses it with a typed error.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest
from django.utils.decorators import classonlymethod
from strawberry.django.views import AsyncGraphQLView
from typing_extensions import override

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.views import AsyncDjangoGraphQLView

if TYPE_CHECKING:
    from django.http import HttpResponseBase


class _UnmarkedAsView(AsyncGraphQLView[object, object]):
    """An async Strawberry view whose ``as_view`` skips Strawberry's coroutine marking."""

    @classonlymethod
    @override
    # basedpyright: the stand-in returns Django's own ``View.as_view`` callback, typed as
    # django-stubs types it rather than as Strawberry's narrower override
    def as_view(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,  # noqa: N805 - Django's own signature
        **initkwargs: object,
    ) -> Callable[..., HttpResponseBase]:
        # The next ``as_view`` past Strawberry's is Django's ``View.as_view``, which marks nothing.
        return super(AsyncGraphQLView, cls).as_view(**initkwargs)


def test_async_view_callback_is_a_coroutine_function():
    """The stamped callback of the async view is a coroutine function."""
    assert inspect.iscoroutinefunction(AsyncDjangoGraphQLView.as_view())


def test_async_view_refuses_an_unmarked_upstream_callback():
    """An upstream ``as_view`` that drops the coroutine mark is refused."""

    # basedpyright: the two bases' ``as_view`` differ by design: the stand-in's is the one
    # the package view must refuse
    class _Unmarked(AsyncDjangoGraphQLView[object, object], _UnmarkedAsView):  # pyright: ignore[reportIncompatibleMethodOverride]
        pass

    with pytest.raises(ConfigurationError, match="needs a coroutine view callback"):
        _Unmarked.as_view()
