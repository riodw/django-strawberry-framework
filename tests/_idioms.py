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
"""

from types import ModuleType
from typing import TypeVar

_ClassT = TypeVar("_ClassT", bound=type)


def definition_raises(cls: _ClassT) -> _ClassT:
    """Mark a class statement that must raise before its name is bound."""
    raise AssertionError(f"class statement for {cls.__qualname__} did not raise")


def module_binding(module: ModuleType, name: str) -> object:
    """Return ``module``'s own binding for ``name`` (its ``__dict__`` entry)."""
    return vars(module)[name]
