"""Call-time cascade visibility: ``apply_cascade_permissions`` (sync + async).

A consumer calls ``apply_cascade_permissions(cls, queryset, info)`` inside its
``DjangoType.get_queryset`` to make every single-column forward relation of
``cls``'s model respect its target type's own visibility hook. The walk is
depth-1; transitive cascade (``Entry -> Item -> Category``) emerges because each
target's ``get_queryset`` may itself call the helper. A module-level
``ContextVar`` seen-set breaks cycles (mutual / self-referential cascade), and
the root call resets it in a ``finally`` so request isolation holds under both
WSGI and ASGI.

Four upstream invariants are ported verbatim from
``django_graphene_filters/permissions.py`` (the working reference): the
``ContextVar`` cycle guard (re-entry partial-narrows, never raises), the
single-column forward-relation scope (the ``related_model``-plus-non-``None``-
``column`` test), nullable-FK preservation (the ``__isnull=True`` disjunct), and
caller-alias pinning (``queryset.db``). Two package adaptations tighten
semantics without changing the contract: each edge's target type is resolved
through the registry primary lookup (``Meta.primary`` semantics, which graphene
has no equivalent of), and a target whose ``has_custom_get_queryset()`` is
``False`` is skipped (the identity default would emit a dead ``__in (SELECT ...)``
clause). One package tightening beyond upstream excludes the multi-table-
inheritance ``<parent>_ptr`` edge, which otherwise passes the two-predicate
scope test.

The per-edge target-hook invocation is delegated to
``utils/querysets.py::apply_type_visibility_sync`` so the package has ONE place
that runs a sync ``get_queryset`` and rejects an async hook with
``SyncMisuseError`` (the coroutine is closed first) -- a visibility-hook-routing
mistake is a data-leak bug, so the routing is not re-decided here. The async
twin wraps the single sync walk in ``sync_to_async(thread_sensitive=True)`` (the
``filters/sets.py`` precedent) so blocking consumer-hook work (e.g.
``user.has_perm(...)`` permission-table reads) stays off the event loop; there
is no second async walk implementation. An ``async def`` target hook therefore
raises ``SyncMisuseError`` from both variants -- inside the wrapped worker
thread there is still no awaiting context.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from asgiref.sync import sync_to_async
from django.db import models
from django.db.models import Q

from .exceptions import ConfigurationError
from .registry import registry

# ``SyncMisuseError`` is re-exported (redundant-alias form, the established
# ``types/relay.py`` convention) so the cascade's own error surface is importable
# from this module (``from django_strawberry_framework.permissions import
# SyncMisuseError``) without reaching into the private ``utils`` package. It is
# already in the package-root ``__all__`` via ``types``, so this re-export adds no
# new public name.
from .utils.querysets import SyncMisuseError as SyncMisuseError

# ``apply_type_visibility_sync`` runs a target's ``get_queryset`` and rejects an
# async hook with ``SyncMisuseError`` (the coroutine closed first); the cascade
# reuses it as the per-edge probe so the package keeps ONE sync-misuse site
# (Decision 10).
from .utils.querysets import apply_type_visibility_sync

# Module-level cycle-guard seen-set (the upstream ``_cascade_seen`` shape
# verbatim). ``None`` means "no walk in flight" -- the next call is the root and
# installs a fresh set; a ``set`` of in-flight ``DjangoType`` classes means "walk
# in flight" so a re-entrant call on a class already present partial-narrows
# instead of recursing. The root call resets the var in a ``finally`` so a
# request-handler exception cannot leak a stale seen-set into the next request
# sharing the context. A ``ContextVar`` (not a plain global) so isolation holds
# under both WSGI and ASGI, and so the async variant's ``sync_to_async`` worker
# thread sees a *copied* context (asgiref runs ``contextvars.copy_context()``
# into the thread): its install/reset is scoped to that copy and never leaks back
# into the event-loop task.
_cascade_seen: ContextVar[set | None] = ContextVar("_cascade_seen", default=None)


def _is_cascadable_edge(field: Any) -> bool:
    """Return whether ``field`` is a single-column forward FK / OneToOne edge.

    The single definition of "cascadable edge" -- both the ``fields=None`` full
    walk and the ``fields=`` validator key off this predicate, so scope cannot
    drift between them. Two predicates ported from upstream (``related_model``
    present AND a non-``None`` single-column ``column``) plus one package
    tightening (NOT a join-table-backed many-to-many edge and NOT the MTI
    ``<parent>_ptr`` parent link). The ``column`` test is
    ``getattr(field, "column", None) is not None`` rather than a bare
    ``hasattr``: under Django 6.0 both ``ManyToManyField`` and ``GenericRelation``
    expose a ``column`` *attribute* whose value is ``None``, so a presence-only
    ``hasattr`` test would over-include them. Under Django 5.2, however,
    ``ManyToManyField.column`` can be non-``None`` despite the relation still being
    join-table-backed, so the explicit ``not many_to_many`` guard is part of the
    contract too. Without these guards, the cascade would compose wrong-shape
    ``__in`` constraints on join-table / virtual relations (a scope-leak bug on a
    row-visibility surface). M2M (join-table-backed), reverse FK / reverse OneToOne
    (``ForeignObjectRel``, no ``column``),
    ``GenericForeignKey`` (``related_model`` absent), ``GenericRelation``
    (virtual, ``column`` is ``None``), and composite-PK / composite-FK targets
    (no single ``column``) are excluded; the MTI ``<parent>_ptr``
    ``OneToOneField(parent_link=True)`` carries both a ``related_model`` and a
    real ``column`` so it passes the two-predicate test and must be excluded by
    the explicit ``parent_link`` guard (otherwise a child row would be silently
    narrowed by its MTI-parent type's hook).
    """
    return (
        getattr(field, "related_model", None) is not None
        and getattr(field, "column", None) is not None
        and not getattr(field, "many_to_many", False)
        and not getattr(field.remote_field, "parent_link", False)
    )


def _cascadable_edge_names(model: type[models.Model]) -> set[str]:
    """Return the names of ``model``'s cascadable edges (Decision 5 step 1)."""
    return {field.name for field in model._meta.get_fields() if _is_cascadable_edge(field)}


def _validate_fields(model: type[models.Model], fields: Any) -> set[str] | None:
    """Resolve ``fields`` to the set of edge names to walk, validating loudly.

    ``None`` returns ``None`` (a sentinel meaning "walk every cascadable edge",
    distinct from ``fields=[]`` which returns an empty set -- a defined no-op). A
    bare string is rejected up front: a string iterates as its characters, so
    ``fields="item"`` would otherwise validate ``'i'``, ``'t'``, ``'e'``,
    ``'m'`` and surface a misleading per-character error that hides the missing
    brackets. A non-iterable value (``fields=1``) or a non-string entry
    (``fields=[1]`` / ``fields=[["item"]]``) likewise raises ``ConfigurationError``
    naming the field-name-iterable contract rather than escaping as a raw
    ``TypeError`` from ``set(...)`` (feedback M2).
    Otherwise every supplied name must be a cascadable edge; unknown or
    known-but-non-cascadable names raise ``ConfigurationError`` naming the
    offending entry, the model, and the cascadable set. A cascadable name whose
    target lacks a registered type or custom hook validates clean here and is
    skipped by the walk's per-edge gate (Decision 9).
    """
    if fields is None:
        return None
    if isinstance(fields, str):
        raise ConfigurationError(
            f"apply_cascade_permissions fields= must be a non-string iterable of "
            f"field names, not the bare string {fields!r}; wrap it in a list "
            f"(fields=[{fields!r}]).",
        )
    try:
        # ``list`` (not ``set``) first: a non-iterable (``fields=1``) raises here,
        # while an iterable with unhashable entries (``fields=[["item"]]``) iterates
        # fine and is caught by the string check below -- so a malformed shape never
        # escapes as a raw ``TypeError`` from ``set(...)`` (feedback M2).
        requested = list(fields)
    except TypeError as exc:
        raise ConfigurationError(
            f"apply_cascade_permissions fields= must be a non-string iterable of "
            f"field names; got {fields!r}.",
        ) from exc
    non_strings = [entry for entry in requested if not isinstance(entry, str)]
    if non_strings:
        raise ConfigurationError(
            f"apply_cascade_permissions fields= entries must be field-name strings; "
            f"got non-string entries {non_strings!r}.",
        )
    requested = set(requested)
    cascadable = _cascadable_edge_names(model)
    unknown = requested - cascadable
    if unknown:
        raise ConfigurationError(
            f"apply_cascade_permissions fields={sorted(unknown)!r} on "
            f"{model.__name__} are not cascadable; the cascadable edges are "
            f"{sorted(cascadable)!r}.",
        )
    return requested


def apply_cascade_permissions(
    cls: type,
    queryset: models.QuerySet,
    info: Any,
    fields: Any = None,
) -> models.QuerySet:
    """Narrow ``queryset`` so each forward relation respects its target visibility.

    Call from inside a ``DjangoType.get_queryset`` (Decision 5). Walks ``cls``'s
    model single-column forward FK / OneToOne edges, resolves each edge's target
    type through the registry primary lookup, runs that type's ``get_queryset``
    against the target model's rows (pinned to the caller's resolved DB alias),
    and intersects ``Q(<edge>__in=<visible>) | Q(<edge>__isnull=True)`` into
    ``queryset``. Edges whose target has no registered type or no custom hook are
    skipped (nothing to narrow, no dead SQL). Returns a narrowed queryset; never
    evaluates, reorders, or projects -- pure ``.filter(...)`` composition, so the
    ``__in`` subqueries compile into the caller's single ``SELECT`` and add zero
    query round-trips (Decision 7).

    Args:
        cls: the owning ``DjangoType`` (its ``.model`` is the walk root).
        queryset: the caller's already-visibility-filtered queryset.
        info: the Strawberry resolver ``info`` (threaded into each target hook).
        fields: optional iterable of model field names scoping the walk to those
            edges; ``None`` walks every cascadable edge, ``[]`` cascades nothing.
            A bare string raises (Decision 9).

    Raises:
        ConfigurationError: a bare-string ``fields=`` or a ``fields=`` name that
            is unknown / non-cascadable (Decision 9).
        SyncMisuseError: a target type's ``get_queryset`` is ``async def``. The
            async twin ``aapply_cascade_permissions`` wraps this same sync walk, so
            it raises identically -- the recourse is to make the target hook sync,
            or pass ``fields=`` to skip the async-hooked edge (Decision 10).
    """
    model = cls.__django_strawberry_definition__.model
    names_to_walk = _validate_fields(model, fields)

    seen = _cascade_seen.get()
    if seen is None:
        seen = {cls}
        token = _cascade_seen.set(seen)
        try:
            return _walk(model, queryset, info, names_to_walk)
        finally:
            _cascade_seen.reset(token)
    if cls in seen:
        return queryset
    seen.add(cls)
    try:
        return _walk(model, queryset, info, names_to_walk)
    finally:
        seen.discard(cls)


def _walk(
    model: type[models.Model],
    queryset: models.QuerySet,
    info: Any,
    names_to_walk: set[str] | None,
) -> models.QuerySet:
    """Intersect one visibility constraint per qualifying edge of ``model``.

    The caller owns the cycle-guard lifecycle (seen-set install / re-entry break /
    frame-exit discard); this function only composes the per-edge subqueries.
    ``names_to_walk`` is ``None`` for the full walk or a validated edge-name set
    for the ``fields=`` scoped walk.
    """
    for field in model._meta.get_fields():
        if not _is_cascadable_edge(field):
            continue
        if names_to_walk is not None and field.name not in names_to_walk:
            continue
        target_type = registry.get(field.related_model)
        if target_type is None:
            continue
        if not target_type.has_custom_get_queryset():
            continue
        base = field.related_model._default_manager.using(queryset.db).all()
        target_qs = apply_type_visibility_sync(
            target_type,
            base,
            info,
            async_recourse=(
                "apply_cascade_permissions walks target hooks synchronously and "
                "aapply_cascade_permissions wraps that same sync walk, so neither "
                "can await an async target hook in 0.0.10; make this target type's "
                "get_queryset sync, or pass fields= to skip the async-hooked edge."
            ),
        )
        queryset = queryset.filter(
            Q(**{f"{field.name}__in": target_qs}) | Q(**{f"{field.name}__isnull": True}),
        )
    return queryset


async def aapply_cascade_permissions(
    cls: type,
    queryset: models.QuerySet,
    info: Any,
    fields: Any = None,
) -> models.QuerySet:
    """Async twin of ``apply_cascade_permissions`` -- the same walk, off the event loop.

    Wraps the single sync walk in ``sync_to_async(thread_sensitive=True)`` (the
    ``filters/sets.py`` precedent) so blocking consumer-hook work (permission-
    table reads inside a target type's ``get_queryset``) never runs on the event
    loop. The ``ContextVar`` install/reset happens inside the worker thread on
    the asgiref-copied context, so it never leaks back into the calling async
    task. An ``async def`` target hook still raises ``SyncMisuseError`` (no
    awaiting context inside the thread); narrow with ``fields=`` to skip an
    async-hooked edge (Decision 10).
    """
    return await sync_to_async(apply_cascade_permissions, thread_sensitive=True)(
        cls,
        queryset,
        info,
        fields,
    )
