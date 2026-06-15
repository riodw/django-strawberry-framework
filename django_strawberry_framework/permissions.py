"""Cascade permission visibility — ``apply_cascade_permissions`` (sync + async).

STAGED SEAM (spec-034 Slice 1). This module is the cascade foundation described
by ``docs/spec-034-permissions-0_0_10.md``. The public surface and the private
walk are laid out here as pseudo-code; every call path raises
``NotImplementedError`` until Slice 1 fills it in (the AGENTS.md design-doc anchor
discipline: a ``TODO(spec-034 Slice N)`` comment + pseudo-code paired with a
loud ``NotImplementedError``, removed in the change that ships the slice).

What this ships (Decision 4 / Decision 5):

    ``apply_cascade_permissions(cls, queryset, info, fields=None)`` — a call-time
    walk of ``cls``'s single-column forward FK / OneToOne edges that intersects
    each target type's ``get_queryset`` visibility into ``queryset``, so a parent
    row whose FK points at a row the target type hides is dropped. Called from
    inside a consumer's ``get_queryset``; transitive cascade emerges because each
    target's hook may itself call the helper (the walk is depth-1, the
    ``ContextVar`` seen-set breaks cycles).

    ``aapply_cascade_permissions(...)`` — the async twin: the same walk wrapped in
    ``sync_to_async(thread_sensitive=True)`` so blocking consumer-hook work (e.g.
    ``user.has_perm(...)`` permission-table reads) stays off the event loop
    (Decision 10).

The four upstream invariants (ported verbatim from
``django-graphene-filters``'s ``permissions.py::apply_cascade_permissions``):
``ContextVar`` cycle guard (partial-narrow on re-entry, never a raise),
single-column forward scope, nullable-FK preservation
(``Q(fk__in=...) | Q(fk__isnull=True)``), and caller-alias pinning
(``.using(queryset.db)``). Two deliberate deviations from upstream: the registry
*primary* lookup (Meta.primary semantics) and the ``has_custom_get_queryset()``
gate (skip identity hooks so no dead ``__in`` SQL is emitted).
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async

# The sync-misuse probe + its error live in utils/querysets.py since the 0.0.9
# DRY pass (spec-034 feedback H1). ``apply_type_visibility_sync(target_type, qs,
# info)`` runs the target's ``get_queryset`` and raises ``SyncMisuseError`` if it
# returns a coroutine (closing it first) — exactly the per-edge probe Decision 10
# / Decision 5 step 4 need, so the cascade reuses it rather than re-spelling it.
from .utils.querysets import (  # noqa: F401  (apply_type_visibility_sync used once Slice 1 lands)
    SyncMisuseError,
    apply_type_visibility_sync,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from strawberry.types import Info


# Module-level cycle-guard seen-set (Decision 5 step 5; upstream ``_cascade_seen``
# shape verbatim). ``None`` outside any cascade; a ``set`` of in-flight
# ``DjangoType`` classes while a root call is on the stack. A ``ContextVar`` (not a
# plain global) so request isolation holds under both WSGI and ASGI — and so the
# async variant's ``sync_to_async`` thread sees a *copied* context (asgiref runs
# ``contextvars.copy_context()`` into the worker thread), containing its mutations
# to that copy and never leaking back into the event-loop task (Decision 10).
_cascade_seen: ContextVar[set[type] | None] = ContextVar("_cascade_seen", default=None)


def apply_cascade_permissions(
    cls: type,
    queryset: QuerySet,
    info: Info,
    fields: list[str] | tuple[str, ...] | None = None,
) -> QuerySet:
    """Intersect each forward-FK target type's visibility into ``queryset``.

    Call from inside a ``DjangoType.get_queryset`` (Decision 5). Returns a
    narrowed queryset; never evaluates, reorders, or projects — pure
    ``.filter(...)`` composition, so it composes with ``only()`` / ordering
    downstream and adds zero query round-trips (the ``__in`` subqueries compile
    into the caller's single ``SELECT`` — Decision 7).

    Args:
        cls: the owning ``DjangoType`` (its ``.model`` is the walk root).
        queryset: the caller's already-visibility-filtered queryset.
        info: the Strawberry resolver ``info`` (threaded into each target hook).
        fields: optional iterable of model field names scoping the walk to those
            edges; ``None`` walks every cascadable edge. A bare string raises
            (Decision 9).

    Raises:
        ConfigurationError: a bare-string ``fields=`` or a ``fields=`` name that
            is unknown / non-cascadable (Decision 9).
        SyncMisuseError: a target type's ``get_queryset`` is ``async def`` (use
            ``aapply_cascade_permissions`` or rewrite the hook sync — Decision 10).
    """
    # TODO(spec-034 Slice 1): implement the walk below and delete the raise.
    #
    # 1. fields= validation (Decision 9) — bare-string guard FIRST, then names:
    #        if isinstance(fields, str):
    #            raise ConfigurationError(
    #                "apply_cascade_permissions: fields= must be a non-string "
    #                f"iterable of field names, got the string {fields!r} (did you "
    #                "mean [{fields!r}]?)."
    #            )
    #        cascadable = {f.name for f in _cascade_edges(cls.model)}
    #        if fields is not None:
    #            unknown = set(fields) - cascadable
    #            if unknown:
    #                raise ConfigurationError(
    #                    f"apply_cascade_permissions: {sorted(unknown)} on "
    #                    f"{cls.model.__name__} are not cascadable. Cascadable "
    #                    f"fields: {sorted(cascadable)}."
    #                )
    #
    # 2. Cycle guard (Decision 5 step 5) — install at root, break on re-entry,
    #    discard own class on exit, reset the var at the root in ``finally``:
    #        seen = _cascade_seen.get()
    #        is_root = seen is None
    #        if is_root:
    #            seen = set()
    #            _cascade_seen.set(seen)
    #        if cls in seen:
    #            return queryset                     # partial narrow, never raise
    #        seen.add(cls)
    #        try:
    #            ... walk (steps 3-4) ...
    #            return queryset
    #        finally:
    #            seen.discard(cls)                   # siblings may re-visit
    #            if is_root:
    #                _cascade_seen.set(None)         # request isolation
    #
    # 3. Edge scope (Decision 5 step 1) — single-column forward FK / O2O only:
    #        for field in _cascade_edges(cls.model):
    #            if fields is not None and field.name not in fields:
    #                continue
    #
    # 4. Per edge: resolve target via the registry PRIMARY lookup, gate on a
    #    custom hook, build the visible-target subquery pinned to the caller's
    #    alias, intersect with the nullable-FK-preserving Q-shape:
    #        target_type = registry.get(field.related_model)
    #        if target_type is None:
    #            continue                            # unexposed model, no contract
    #        if not target_type.has_custom_get_queryset():
    #            continue                            # identity hook → no dead SQL
    #        base = field.related_model._default_manager.using(queryset.db).all()
    #        target_qs = apply_type_visibility_sync(target_type, base, info)  # SyncMisuse-probed
    #        queryset = queryset.filter(
    #            Q(**{f"{field.name}__in": target_qs})
    #            | Q(**{f"{field.name}__isnull": True})
    #        )
    raise NotImplementedError(
        "TODO(spec-034 Slice 1): apply_cascade_permissions cascade walk "
        "(Decision 5) is not implemented yet.",
    )


# Async twin (Decision 10): the SAME sync walk run in a thread-sensitive worker so
# blocking hook I/O stays off the event loop. One implementation, no sync/async
# fork to drift. Inside the thread the walk still uses the sync probe, so an async
# target hook raises ``SyncMisuseError`` from this variant too (documented; the
# recourse is a sync hook or ``fields=`` to skip the async-hooked edge). Until
# Slice 1 fills ``apply_cascade_permissions``, awaiting this raises its
# ``NotImplementedError`` through the wrapper.
#   TODO(spec-034 Slice 1): keep this wrap; confirm the ContextVar seen-set is
#   clean inside the worker thread (asgiref copy_context) — pinned by
#   ``test_aapply_runs_walk_off_event_loop``.
aapply_cascade_permissions = sync_to_async(thread_sensitive=True)(apply_cascade_permissions)


def _cascade_edges(model: type) -> list[Any]:
    """Return ``model``'s single-column forward FK / OneToOne fields (Decision 5 step 1).

    The upstream scope test, ported verbatim: ``model._meta.get_fields()`` entries
    with ``related_model`` present AND ``hasattr(field, "column")``. This excludes,
    *by construction*, M2M (join-table-backed, no ``column``), reverse FK / reverse
    OneToOne (``ForeignObjectRel``, no ``column``), ``GenericForeignKey``
    (``related_model`` absent), ``GenericRelation`` (virtual, no ``column``), and
    composite-PK / composite-FK targets (no single ``column``).
    """
    # TODO(spec-034 Slice 1): implement and delete the raise.
    #   return [
    #       f
    #       for f in model._meta.get_fields()
    #       if getattr(f, "related_model", None) is not None and hasattr(f, "column")
    #   ]
    raise NotImplementedError(
        "TODO(spec-034 Slice 1): _cascade_edges single-column-forward-relation "
        "scope (Decision 5 step 1) is not implemented yet.",
    )
