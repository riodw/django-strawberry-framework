"""Typed reads and writes of the ``QuerySet`` state Django keeps in private attributes.

The visibility seal, the optimizer and the write pipeline read and rebuild a
queryset's routing (``_db``, ``_hints``), its projection (``_fields``), its
pending prefetches and its deferred filter. Django keeps all of these as private
``QuerySet`` attributes that django-stubs does not declare, so every direct
access is an unknown attribute to the type checker. Each one is spelled here
once, under the type Django stores, and every caller goes through these
functions instead of the attribute.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import TypeAlias

    from django.db import models
    from django.db.models import Prefetch
    from django.db.models.sql import Query

    #: One ``prefetch_related`` lookup as Django stores it: a lookup path or a ``Prefetch``.
    PrefetchLookup: TypeAlias = str | Prefetch[str]
    #: ``QuerySet._deferred_filter``: the ``(negate, args, kwargs)`` of a filter Django
    #: applies on the next ``query`` read, or ``None`` when none is pending.
    DeferredFilter: TypeAlias = tuple[bool, tuple[object, ...], dict[str, object]]

_QuerySetT = TypeVar("_QuerySetT", bound="models.QuerySet[models.Model, object]")


def queryset_db(queryset: models.QuerySet[models.Model, object]) -> str | None:
    """Return the alias ``using()`` pinned, or ``None`` when the router decides."""
    # basedpyright: django-stubs omits QuerySet._db, reported as an unknown attribute
    return queryset._db  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_db(queryset: models.QuerySet[models.Model, object], alias: str | None) -> None:
    """Pin ``queryset`` to ``alias`` without the clone ``using()`` makes."""
    # basedpyright: django-stubs omits QuerySet._db, reported as an unknown attribute
    queryset._db = alias  # pyright: ignore[reportAttributeAccessIssue]


def queryset_hints(queryset: models.QuerySet[models.Model, object]) -> dict[str, object]:
    """Return the router hints dict ``queryset`` holds (the object itself, not a copy)."""
    # basedpyright: django-stubs omits QuerySet._hints, reported as an unknown attribute
    return queryset._hints  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_hints(
    queryset: models.QuerySet[models.Model, object],
    hints: dict[str, object],
) -> None:
    """Replace the router hints dict ``queryset`` holds."""
    # basedpyright: django-stubs omits QuerySet._hints, reported as an unknown attribute
    queryset._hints = hints  # pyright: ignore[reportAttributeAccessIssue]


def queryset_fields(queryset: models.QuerySet[models.Model, object]) -> tuple[str, ...] | None:
    """Return the ``values()`` / ``values_list()`` field names, or ``None`` for model rows."""
    # basedpyright: django-stubs omits QuerySet._fields, reported as an unknown attribute
    return queryset._fields  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_fields(
    queryset: models.QuerySet[models.Model, object],
    fields: tuple[str, ...] | None,
) -> None:
    """Set the ``values()`` / ``values_list()`` field names ``queryset`` projects."""
    # basedpyright: django-stubs omits QuerySet._fields, reported as an unknown attribute
    queryset._fields = fields  # pyright: ignore[reportAttributeAccessIssue]


def queryset_prefetch_lookups(
    queryset: models.QuerySet[models.Model, object],
) -> tuple[PrefetchLookup, ...]:
    """Return the ``prefetch_related`` lookups ``queryset`` will run, in order."""
    # basedpyright: django-stubs omits QuerySet._prefetch_related_lookups, reported as an
    # unknown attribute
    return queryset._prefetch_related_lookups  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_prefetch_lookups(
    queryset: models.QuerySet[models.Model, object],
    lookups: tuple[PrefetchLookup, ...],
) -> None:
    """Replace the ``prefetch_related`` lookups ``queryset`` will run."""
    # basedpyright: django-stubs omits QuerySet._prefetch_related_lookups, reported as an
    # unknown attribute
    queryset._prefetch_related_lookups = lookups  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_deferred_filter(
    queryset: models.QuerySet[models.Model, object],
    deferred: DeferredFilter | None,
) -> None:
    """Set the filter Django applies to ``queryset`` on its next ``query`` read."""
    # basedpyright: django-stubs omits QuerySet._deferred_filter, reported as an unknown attribute
    queryset._deferred_filter = deferred  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_defer_next_filter(
    queryset: models.QuerySet[models.Model, object],
    defer: bool,
) -> None:
    """Set whether ``queryset``'s next ``filter()`` is deferred instead of applied."""
    # basedpyright: django-stubs omits QuerySet._defer_next_filter, reported as an unknown
    # attribute
    queryset._defer_next_filter = defer  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_sticky_filter(
    queryset: models.QuerySet[models.Model, object],
    sticky: bool,
) -> None:
    """Set whether ``queryset``'s next two ``filter()`` calls share their multi-valued joins."""
    # basedpyright: django-stubs omits QuerySet._sticky_filter, reported as an unknown attribute
    queryset._sticky_filter = sticky  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_for_write(
    queryset: models.QuerySet[models.Model, object],
    for_write: bool,
) -> None:
    """Set whether ``queryset`` routes through the router's write alias."""
    # basedpyright: django-stubs omits QuerySet._for_write, reported as an unknown attribute
    queryset._for_write = for_write  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_query(queryset: models.QuerySet[models.Model, object], query: Query) -> None:
    """Replace the ``Query`` ``queryset`` holds, past the ``query`` property's setter.

    The setter also switches ``_iterable_class`` for a ``values()`` query, and the
    getter applies a pending deferred filter; this write does neither.
    """
    # basedpyright: django-stubs omits QuerySet._query, reported as an unknown attribute
    queryset._query = query  # pyright: ignore[reportAttributeAccessIssue]


def chain_queryset(queryset: _QuerySetT) -> _QuerySetT:
    """Return Django's ``_chain()`` clone of ``queryset``: same class, same state."""
    # basedpyright: django-stubs omits QuerySet._chain, reported as an unknown attribute
    return queryset._chain()  # pyright: ignore[reportAttributeAccessIssue]
