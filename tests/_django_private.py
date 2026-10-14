"""Typed views of Django's private attributes that django-stubs omits.

Tests read (and, for hostile-input rows, plant) a few attributes Django defines but its
stubs never declare, so a plain read reports an unknown attribute
(``reportAttributeAccessIssue``). Each ``has_*`` accessor narrows the object to a
declaration-only subclass of the real class that adds the one attribute; the subclasses
exist for the checker alone (they sit under ``TYPE_CHECKING`` and are never instantiated).
The narrowing is a real run-time check that the attribute exists, so a Django release that
drops it fails at the ``assert has_x(obj)`` line rather than as a bare ``AttributeError``
deeper in the test. ``TypeIs`` over a ``Protocol`` that does not subclass the real class is
rejected, so every view subclasses the class it narrows.

``Query._filtered_relations`` is typed as holding arbitrary objects: the rows that read it
compare identity and the rows that write it plant non-Django values.
``FilteredRelation.resolved_condition`` is typed ``object``: the rows that read it compare
identity and the rows that write it plant ``None``. A row that walks or mutates the
resolved ``WhereNode`` tree reads it through its own typed handle instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from django.db.models import (
    FilteredRelation,
    Manager,
    Model,
    QuerySet,
)
from django.db.models.expressions import BaseExpression
from django.db.models.sql import Query
from django.http import HttpRequest

if TYPE_CHECKING:
    from typing_extensions import Self, TypeIs

_M = TypeVar("_M", bound=Model)
_R = TypeVar("_R")
_QuerySetT = TypeVar("_QuerySetT", bound="QuerySet[Model, object]")

if TYPE_CHECKING:

    class QueryWithFilteredRelations(Query):
        """A ``Query`` carrying Django's ``_filtered_relations`` mapping."""

        _filtered_relations: dict[str, object]

    class FilteredRelationWithCondition(FilteredRelation):
        """A ``FilteredRelation`` carrying the condition Django resolves onto it."""

        resolved_condition: object

    class HttpRequestWithReadState(HttpRequest):
        """An ``HttpRequest`` carrying the flag ``HttpRequest.read`` sets on first read."""

        _read_started: bool

    class ModelWithPrefetchCache(Model):
        """A model row carrying the cache ``prefetch_related_objects`` fills."""

        _prefetched_objects_cache: dict[str, QuerySet[Model, object]]

    class QuerySetWithValues(QuerySet[_M, _R]):
        """A queryset carrying the ``_values`` method ``QuerySet.values`` delegates to."""

        def _values(self, *_fields: str, **_expressions: object) -> Self: ...

    class ManagerWithRelFilters(Manager[_M]):
        """A related manager carrying the ``_apply_rel_filters`` method Django binds on it."""

        def _apply_rel_filters(self, _queryset: _QuerySetT) -> _QuerySetT: ...

    class DeconstructibleExpression(BaseExpression):
        """An expression carrying the arguments ``@deconstructible`` records at construction."""

        _constructor_args: tuple[tuple[object, ...], dict[object, object]]


def has_filtered_relations(query: Query) -> TypeIs[QueryWithFilteredRelations]:
    """Return whether ``query`` carries ``_filtered_relations``."""
    return hasattr(query, "_filtered_relations")


def has_resolved_condition(
    relation: FilteredRelation | None,
) -> TypeIs[FilteredRelationWithCondition]:
    """Return whether ``relation`` is a ``FilteredRelation`` carrying ``resolved_condition``."""
    return relation is not None and hasattr(relation, "resolved_condition")


def has_read_started(request: HttpRequest) -> TypeIs[HttpRequestWithReadState]:
    """Return whether ``request`` carries ``_read_started``."""
    return hasattr(request, "_read_started")


def has_prefetched_objects_cache(row: Model) -> TypeIs[ModelWithPrefetchCache]:
    """Return whether ``row`` carries ``_prefetched_objects_cache``."""
    return hasattr(row, "_prefetched_objects_cache")


def has_values_method(queryset: QuerySet[_M, _R]) -> TypeIs[QuerySetWithValues[_M, _R]]:
    """Return whether ``queryset`` carries the ``_values`` method."""
    return hasattr(queryset, "_values")


def has_apply_rel_filters(manager: Manager[_M]) -> TypeIs[ManagerWithRelFilters[_M]]:
    """Return whether ``manager`` carries the ``_apply_rel_filters`` method."""
    return hasattr(manager, "_apply_rel_filters")


def has_constructor_args(expression: BaseExpression) -> TypeIs[DeconstructibleExpression]:
    """Return whether ``expression`` carries the ``_constructor_args`` ``@deconstructible`` sets."""
    return hasattr(expression, "_constructor_args")
