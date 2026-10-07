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

from collections.abc import Iterable
from types import ModuleType
from typing import Literal, Protocol, TypeGuard, TypeVar, overload

from django.db.models import Model, QuerySet
from strawberry import relay

from django_strawberry_framework import DjangoType
from django_strawberry_framework.utils.querysets import model_for

_ClassT = TypeVar("_ClassT", bound=type)
_ModelT = TypeVar("_ModelT", bound=Model)


def definition_raises(cls: _ClassT) -> _ClassT:
    """Mark a class statement that must raise before its name is bound."""
    raise AssertionError(f"class statement for {cls.__qualname__} did not raise")


def module_binding(module: ModuleType, name: str) -> object:
    """Return ``module``'s own binding for ``name`` (its ``__dict__`` entry)."""
    return vars(module)[name]


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
