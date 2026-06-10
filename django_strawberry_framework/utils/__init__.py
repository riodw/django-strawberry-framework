"""Cross-cutting utility helpers.

Subpackage structure mirrors the convention both `graphene_django/utils/`
and `strawberry_django/utils/` converge on: focused submodules per
concern rather than a single 500-line `utils.py`. Currently:

- ``relations`` - Django relation-shape classification
  (``relation_kind``, ``RelationKind``, ``is_many_side_relation_kind``).
- ``strings`` - case conversion (``snake_case``, ``pascal_case``).
- ``typing`` - Strawberry / Python / GraphQL type unwrapping
  (``unwrap_graphql_type``, ``unwrap_return_type``).
  ``unwrap_return_type`` is the Strawberry-list-peel sibling of
  ``unwrap_graphql_type``, exported for the upcoming schema-factory
  consumer (mirrors the ``queryset`` future-extension framing below).

A ``queryset`` submodule will land when queryset-introspection helpers
become cross-cutting (currently each subsystem keeps its own).
"""

from .relations import RelationKind, is_many_side_relation_kind, relation_kind
from .strings import pascal_case, snake_case
from .typing import unwrap_graphql_type, unwrap_return_type

__all__ = (
    "RelationKind",
    "is_many_side_relation_kind",
    "pascal_case",
    "relation_kind",
    "snake_case",
    "unwrap_graphql_type",
    "unwrap_return_type",
)
