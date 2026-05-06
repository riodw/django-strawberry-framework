"""Relation-shape helpers shared by converters, resolvers, and the optimizer."""

from __future__ import annotations

from typing import Any, Literal, TypeAlias

RelationKind: TypeAlias = Literal["many", "reverse_one_to_one", "forward_single"]


def relation_kind(field: Any) -> RelationKind:
    """Classify a Django relation field by GraphQL/runtime cardinality."""
    if getattr(field, "many_to_many", False) or getattr(field, "one_to_many", False):
        return "many"
    if getattr(field, "one_to_one", False) and getattr(field, "auto_created", False):
        return "reverse_one_to_one"
    return "forward_single"
