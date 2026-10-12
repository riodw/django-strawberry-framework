"""Narrowing predicates and typed base slots for values whose type is only ``object``.

The package reads consumer-controlled values (input payloads, ``Meta`` options,
context objects, stored queryset state) that arrive typed ``object``. A bare
``isinstance(value, dict)`` on such a value narrows to ``dict[Unknown, Unknown]``
because ``dict``'s slots are invariant, and a bare unbound slot call
(``dict.items(value)``, ``list.__iter__(value)``) specializes the class with
``Unknown`` the same way. Each predicate here runs exactly the check its call
sites spell and states the element types as ``object``, so the narrowed value is
a container of ``object`` the caller then checks member by member.

Two families of check, kept apart because they answer different questions:

* ``is_dict`` / ``is_list`` / ... are ``isinstance`` checks (subclasses pass) and
  ``TypeIs`` predicates. At runtime each name IS the class's own
  ``__instancecheck__`` bound to it, so a check costs no extra Python frame on the
  input walks that make one per value.
* ``is_exact_*`` are ``type(value) is C`` checks (subclasses fail) and
  ``TypeGuard`` predicates, since a negative answer says nothing about a subclass.

The typed slots (``dict_items``, ``list_iter``, ...) are the builtin base
methods themselves at runtime, so a subclass override of ``items`` /
``__iter__`` still cannot decide what a walk sees; under the checker they are
declared generic over the container they read.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING, TypeGuard

if TYPE_CHECKING:
    from collections.abc import ItemsView, Iterator
    from typing import TypeVar

    from typing_extensions import TypeIs

    _KeyT = TypeVar("_KeyT")
    _ValueT = TypeVar("_ValueT")

    def is_dict(value: object, /) -> TypeIs[dict[object, object]]:
        """Return whether ``value`` is a ``dict`` (subclasses included)."""
        ...

    def is_list(value: object, /) -> TypeIs[list[object]]:
        """Return whether ``value`` is a ``list`` (subclasses included)."""
        ...

    def is_tuple(value: object, /) -> TypeIs[tuple[object, ...]]:
        """Return whether ``value`` is a ``tuple`` (subclasses included)."""
        ...

    def is_set(value: object, /) -> TypeIs[set[object]]:
        """Return whether ``value`` is a ``set`` (subclasses included)."""
        ...

    def is_frozenset(value: object, /) -> TypeIs[frozenset[object]]:
        """Return whether ``value`` is a ``frozenset`` (subclasses included)."""
        ...

    def is_abstract_set(value: object, /) -> TypeIs[AbstractSet[object]]:
        """Return whether ``value`` is a ``collections.abc.Set`` (registered virtual subclasses included)."""
        ...

    def is_memoryview(value: object, /) -> TypeIs[memoryview]:
        """Return whether ``value`` is a ``memoryview`` (subclasses included)."""
        ...

    def is_iterable(value: object, /) -> TypeIs[Iterable[object]]:
        """Return whether ``value`` is a ``collections.abc.Iterable`` (declares ``__iter__``)."""
        ...

    def is_mapping(value: object, /) -> TypeIs[Mapping[object, object]]:
        """Return whether ``value`` is a ``Mapping`` (registered virtual subclasses included)."""
        ...

    def dict_items(value: dict[_KeyT, _ValueT], /) -> ItemsView[_KeyT, _ValueT]:
        """``dict.items`` read through the base slot."""
        ...

    def dict_get(value: dict[_KeyT, _ValueT], key: _KeyT, /) -> _ValueT | None:
        """``dict.get`` read through the base slot."""
        ...

    def list_iter(value: list[_ValueT], /) -> Iterator[_ValueT]:
        """``list.__iter__`` read through the base slot."""
        ...

    def tuple_iter(value: tuple[_ValueT, ...], /) -> Iterator[_ValueT]:
        """``tuple.__iter__`` read through the base slot."""
        ...

    def set_iter(value: set[_ValueT], /) -> Iterator[_ValueT]:
        """``set.__iter__`` read through the base slot."""
        ...

    def frozenset_iter(value: frozenset[_ValueT], /) -> Iterator[_ValueT]:
        """``frozenset.__iter__`` read through the base slot."""
        ...

    def mapping_get(value: Mapping[_KeyT, _ValueT], key: _KeyT, /) -> _ValueT | None:
        """``Mapping.get`` read through the ABC's own method."""
        ...

else:
    is_dict = dict.__instancecheck__
    is_list = list.__instancecheck__
    is_tuple = tuple.__instancecheck__
    is_set = set.__instancecheck__
    is_frozenset = frozenset.__instancecheck__
    is_mapping = Mapping.__instancecheck__
    is_iterable = Iterable.__instancecheck__
    is_abstract_set = AbstractSet.__instancecheck__
    is_memoryview = memoryview.__instancecheck__
    dict_items = dict.items
    dict_get = dict.get
    list_iter = list.__iter__
    tuple_iter = tuple.__iter__
    set_iter = set.__iter__
    frozenset_iter = frozenset.__iter__
    mapping_get = Mapping.get

__all__ = (
    "dict_get",
    "dict_items",
    "frozenset_iter",
    "is_abstract_set",
    "is_class",
    "is_dict",
    "is_exact_dict",
    "is_exact_list",
    "is_exact_list_or_tuple",
    "is_exact_set_or_frozenset",
    "is_exact_tuple",
    "is_exact_tuple_or_list",
    "is_frozenset",
    "is_iterable",
    "is_list",
    "is_list_or_tuple",
    "is_mapping",
    "is_memoryview",
    "is_set",
    "is_set_or_frozenset",
    "is_text_or_bytes",
    "is_tuple",
    "list_iter",
    "mapping_get",
    "set_iter",
    "tuple_iter",
)


def is_list_or_tuple(value: object) -> TypeIs[list[object] | tuple[object, ...]]:
    """Return whether ``value`` is a ``list`` or a ``tuple`` (subclasses included)."""
    return isinstance(value, (list, tuple))


def is_set_or_frozenset(value: object) -> TypeIs[set[object] | frozenset[object]]:
    """Return whether ``value`` is a ``set`` or a ``frozenset`` (subclasses included)."""
    return isinstance(value, (set, frozenset))


def is_text_or_bytes(value: object) -> TypeIs[str | bytes | bytearray | memoryview]:
    """Return whether ``value`` is text or a bytes-like atom (subclasses included).

    The values that iterate character by character (or byte by byte), so a caller
    expecting a sequence of items must refuse them before iterating.
    """
    return isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
            memoryview,
        ),
    )


def is_class(value: object) -> TypeIs[type[object]]:
    """Return whether ``value`` IS a class, asked of its real type.

    ``issubclass(type(value), type)`` rather than ``isinstance(value, type)``: the real
    type cannot be restated by a ``__class__`` property on the value.
    """
    return issubclass(type(value), type)


def is_exact_dict(value: object) -> TypeGuard[dict[object, object]]:
    """Return whether ``value`` is EXACTLY a builtin ``dict`` (never a subclass)."""
    return type(value) is dict


def is_exact_list(value: object) -> TypeGuard[list[object]]:
    """Return whether ``value`` is EXACTLY a builtin ``list`` (never a subclass)."""
    return type(value) is list


def is_exact_tuple(value: object) -> TypeGuard[tuple[object, ...]]:
    """Return whether ``value`` is EXACTLY a builtin ``tuple`` (never a subclass)."""
    return type(value) is tuple


def is_exact_list_or_tuple(value: object) -> TypeGuard[list[object] | tuple[object, ...]]:
    """Return whether ``value`` is EXACTLY a builtin ``list`` or ``tuple``."""
    return type(value) in (list, tuple)


def is_exact_tuple_or_list(value: object) -> TypeGuard[list[object] | tuple[object, ...]]:
    """``is_exact_list_or_tuple`` comparing ``tuple`` first, for the sites that test in that order.

    ``in`` compares by equality, so the order decides which class a metaclass ``__eq__``
    is asked about first; each site keeps its own.
    """
    return type(value) in (tuple, list)


def is_exact_set_or_frozenset(value: object) -> TypeGuard[set[object] | frozenset[object]]:
    """Return whether ``value`` is EXACTLY a builtin ``set`` or ``frozenset``."""
    return type(value) in (set, frozenset)
