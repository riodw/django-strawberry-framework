"""Cross-cutting utility helpers.

Subpackage structure mirrors the convention both `graphene_django/utils/`
and `strawberry_django/utils/` converge on: focused submodules per
concern rather than a single 500-line `utils.py`. Currently:

- ``strings`` — case conversion (``snake_case``, ``pascal_case``).
- ``typing`` — Strawberry / Python type unwrapping (``unwrap_return_type``).

A ``queryset`` submodule will land when queryset-introspection helpers
become cross-cutting (currently each subsystem keeps its own).
"""

from .strings import pascal_case, snake_case
from .typing import unwrap_return_type

__all__ = ("pascal_case", "snake_case", "unwrap_return_type")
