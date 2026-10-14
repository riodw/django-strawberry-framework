"""The revalidating consumer factory proves its bases carry the hooks it overrides.

``consumers.py::build_revalidating_consumer_class`` derives the package consumer,
its two protocol handlers and its WebSocket adapter from classes read off the base
consumer at run time. Each is checked for the hooks its subclass extends before
anything derives from it, so a base that lacks one is refused with a typed error
naming the base instead of producing a consumer whose overrides delegate nowhere.
"""

from __future__ import annotations

import pytest

from django_strawberry_framework import consumers as cmod
from django_strawberry_framework.exceptions import ConfigurationError


class _TransportHandler:
    async def handle(self) -> None:
        return None

    async def handle_subscribe(self, _message: object) -> None:
        return None


class _LegacyHandler:
    async def handle(self) -> None:
        return None

    async def handle_start(self, _message: object) -> None:
        return None

    async def handle_stop(self, _message: object) -> None:
        return None


class _Adapter:
    async def send_json(self, _message: object) -> None:
        return None

    async def close(self, _code: int, _reason: str) -> None:
        return None


class _AdapterWithoutClose:
    async def send_json(self, _message: object) -> None:
        return None


class _BaseConsumer:
    graphql_transport_ws_handler_class: type[object] = _TransportHandler
    graphql_ws_handler_class: type[object] = _LegacyHandler
    websocket_adapter_class: type[object] = _Adapter

    @classmethod
    def as_asgi(cls, **_initkwargs: object) -> object:
        return cls

    async def disconnect(self, _code: int) -> None:
        return None


def test_base_with_every_hook_builds_the_consumer() -> None:
    """A base whose classes carry every overridden hook is derived from."""
    # basedpyright: a plain stand-in carrying exactly the hooks the factory checks;
    # build_revalidating_consumer_class types the parameter as type[GraphQLWSConsumer]
    consumer_class = cmod.build_revalidating_consumer_class(_BaseConsumer)  # pyright: ignore[reportArgumentType]

    assert issubclass(consumer_class, _BaseConsumer)


def test_base_whose_adapter_lacks_close_is_refused() -> None:
    """An adapter without ``close`` is refused before any class derives from it."""

    class _Base(_BaseConsumer):
        websocket_adapter_class: type[object] = _AdapterWithoutClose

    with pytest.raises(ConfigurationError, match="is not a Strawberry Channels GraphQLWSConsumer"):
        # basedpyright: a plain stand-in whose adapter lacks a hook the factory checks
        cmod.build_revalidating_consumer_class(_Base)  # pyright: ignore[reportArgumentType]
