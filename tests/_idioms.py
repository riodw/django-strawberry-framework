"""Shared test idioms written so the type checker can follow them.

``definition_raises`` decorates a class statement that a test wraps in ``pytest.raises``
because declaring the class is the call under test. The metaclass raises before the class
object exists, so the decorator never runs and the name is never bound; the decorator is
the read that keeps basedpyright from reporting the never-used local class
(``reportUnusedClass``), so such sites carry no per-site suppression. If the statement
unexpectedly succeeds, the decorator fails the test with a message naming the class, ahead
of ``pytest.raises``'s generic ``DID NOT RAISE``.

``module_binding`` reads a name out of a module's own namespace. A single-source check
asserts that a consumer module holds the SAME object as its owner, so it reads the
consumer's binding rather than importing the owner again; basedpyright flags that attribute
read as use of a private local import (``reportPrivateLocalImportUsage``). ``vars()`` reads
the ``__dict__`` entry, which a package ``__getattr__`` cannot satisfy, so the check is at
least as strict as the attribute read it replaces.

``websocket_scope`` builds a complete ASGI WebSocket handshake scope, so a row that cares
about only the headers and the ``server`` pair still hands a typed scope to code that
declares asgiref's ``WebSocketScope``.

``relay_hooks`` / ``async_relay_hooks`` read the Relay resolvers ``finalize_django_types()``
installs on a Relay ``DjangoType``. The declared class gains ``relay.Node`` only when the
finalizer injects it, so its static type carries none of them; and ``relay.Node``'s own
signatures type the rows as the node class, not the model rows the installed defaults
return. The accessor asserts the type really is a ``relay.Node`` over ``model`` and hands
it back as a protocol naming the call shapes the tests use: rows typed as ``model``, and
``info`` as ``object`` because the paths under test never read it. ``relay_hooks`` is the
sync executor's shape; ``async_relay_hooks`` is the async one, where ``resolve_node`` and
``resolve_nodes`` return the coroutine the caller awaits.
"""

import inspect
from collections.abc import Iterable
from types import ModuleType
from typing import TYPE_CHECKING, Literal, Protocol, TypeGuard, TypeVar, overload

from django.db.models import Model, QuerySet
from django.test.testcases import SimpleTestCase
from strawberry import relay

from django_strawberry_framework import DjangoType
from django_strawberry_framework.utils.querysets import model_for

if TYPE_CHECKING:
    from asgiref.typing import WebSocketScope

    from django_strawberry_framework.rest_framework.serializer_converter import DRFField

_ClassT = TypeVar("_ClassT", bound=type)
_ModelT = TypeVar("_ModelT", bound=Model)
_DRFFieldT = TypeVar("_DRFFieldT", bound="DRFField")


def definition_raises(cls: _ClassT) -> _ClassT:
    """Mark a class statement that must raise before its name is bound."""
    raise AssertionError(f"class statement for {cls.__qualname__} did not raise")


def module_binding(module: ModuleType, name: str) -> object:
    """Return ``module``'s own binding for ``name`` (its ``__dict__`` entry)."""
    return vars(module)[name]


def stub_module(name: str, **attributes: object) -> ModuleType:
    """Build a run-time module called ``name`` whose namespace holds ``attributes``."""
    module = ModuleType(name)
    vars(module).update(attributes)
    return module


def _remove_databases_failures_descriptor(
    cls: type[SimpleTestCase],
) -> "classmethod[SimpleTestCase, ..., object]":
    """``cls``'s ``_remove_databases_failures`` descriptor, found along the MRO unbound.

    django-stubs omits this private classmethod, so a test cannot name it on the class.
    ``inspect.getattr_static`` fetches the descriptor without binding it and the
    ``isinstance`` check makes the read assert the shape the callers use.
    """
    descriptor = inspect.getattr_static(cls, "_remove_databases_failures")
    assert isinstance(descriptor, classmethod)
    return descriptor


def remove_databases_failures_function(cls: type[SimpleTestCase]) -> object:
    """The function behind ``cls._remove_databases_failures`` (``classmethod.__func__``)."""
    return _remove_databases_failures_descriptor(cls).__func__


def call_remove_databases_failures(cls: type[SimpleTestCase]) -> None:
    """Run ``cls._remove_databases_failures()``: the descriptor's function called with ``cls``."""
    _remove_databases_failures_descriptor(cls).__func__(cls)


class RelayNodeHooks(Protocol[_ModelT]):
    """The installed Relay resolvers of a finalized type, called on the sync executor."""

    def resolve_id_attr(self) -> str: ...

    def resolve_id(self, root: object, *, info: object) -> str: ...

    @overload
    def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: Literal[True],
    ) -> _ModelT: ...

    @overload
    def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: bool = False,
    ) -> _ModelT | None: ...

    @overload
    def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: None = None,
        required: bool = False,
    ) -> QuerySet[_ModelT]: ...

    @overload
    def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: Iterable[object],
        required: bool = False,
    ) -> list[_ModelT | None]: ...

    def resolve_typename(self, root: object, info: object) -> str: ...


class AsyncRelayNodeHooks(Protocol[_ModelT]):
    """The installed Relay node lookups of a finalized type, called on the async executor."""

    @overload
    async def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: Literal[True],
    ) -> _ModelT: ...

    @overload
    async def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: bool = False,
    ) -> _ModelT | None: ...

    @overload
    async def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: None = None,
        required: bool = False,
    ) -> QuerySet[_ModelT]: ...

    @overload
    async def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: Iterable[object],
        required: bool = False,
    ) -> list[_ModelT | None]: ...


def _relay_type_over(type_cls: type[DjangoType], model: type[Model]) -> bool:
    """Return whether ``type_cls`` is a finalized ``relay.Node`` type over ``model``."""
    return issubclass(type_cls, relay.Node) and model_for(type_cls) is model


def _sync_hooks_over(
    type_cls: type[DjangoType],
    model: type[_ModelT],
) -> TypeGuard[RelayNodeHooks[_ModelT]]:
    return _relay_type_over(type_cls, model)


def _async_hooks_over(
    type_cls: type[DjangoType],
    model: type[_ModelT],
) -> TypeGuard[AsyncRelayNodeHooks[_ModelT]]:
    return _relay_type_over(type_cls, model)


def relay_hooks(type_cls: type[DjangoType], model: type[_ModelT]) -> RelayNodeHooks[_ModelT]:
    """Return finalized Relay type ``type_cls`` over ``model`` as its sync resolver hooks."""
    assert _sync_hooks_over(type_cls, model), f"{type_cls!r} is not a Relay type over {model!r}"
    return type_cls


def async_relay_hooks(
    type_cls: type[DjangoType],
    model: type[_ModelT],
) -> AsyncRelayNodeHooks[_ModelT]:
    """Return finalized Relay type ``type_cls`` over ``model`` as its async node lookups."""
    assert _async_hooks_over(type_cls, model), f"{type_cls!r} is not a Relay type over {model!r}"
    return type_cls


def websocket_scope(
    headers: Iterable[tuple[bytes, bytes]] = (),
    server: tuple[str, int | None] | None = None,
) -> "WebSocketScope":
    """Return a complete ASGI WebSocket handshake scope carrying ``headers`` and ``server``."""
    return {
        "type": "websocket",
        "asgi": {"spec_version": "2.3", "version": "3.0"},
        "http_version": "1.1",
        "scheme": "ws",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": list(headers),
        "client": None,
        "server": server,
        "subprotocols": [],
        "extensions": None,
    }


def bind_unparented(field: _DRFFieldT, name: str) -> _DRFFieldT:
    """Bind a serializer field to ``name`` with no parent serializer, and return it.

    DRF populates ``field_name`` / ``source`` / ``source_attrs`` at bind time, and the
    converters read bound fields, as the schema-time discovery hands them. The field a
    row holds directly has no serializer above it.
    """
    # basedpyright: drf-stubs types parent as BaseSerializer; the runtime accepts None (an
    # unparented bound field)
    field.bind(name, None)  # pyright: ignore[reportArgumentType]
    return field
