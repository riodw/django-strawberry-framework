"""Call-time cascade visibility: ``apply_cascade_permissions`` (sync + async).

A consumer calls ``apply_cascade_permissions(cls, queryset, info)`` inside its
``DjangoType.get_queryset`` to make every single-column concrete forward
relation of ``cls``'s model respect its target type's own visibility. The walk
is depth-1; transitive cascade (``Entry -> Item -> Category``) emerges because
each target's ``get_queryset`` may itself call the helper.

The traversal contract is fail-closed on every boundary the composed SQL
depends on:

- **Immutable traversal state.** A module-level ``ContextVar`` holds a frozen
  ``_TraversalState`` (root DB alias, active type tuple, edge-path frames).
  Every root, edge, and nested application installs a NEW state object with a
  token and resets it in a ``finally``, so state cannot leak across calls,
  tasks, threads, or exceptions -- request isolation holds under both WSGI and
  ASGI, and the async variant's ``sync_to_async`` worker sees a *copied*
  context whose install/reset never leaks back into the event-loop task.
- **Cycles fail closed.** Re-entry into a type already on the active tuple
  raises a path-rich ``ConfigurationError`` (``AType.b -> BType.a -> AType``).
  The previous re-entry contract returned the queryset un-narrowed, which let
  a recursive graph skip the re-entered type's *outgoing* visibility edges --
  a root row whose hidden relation was only reachable through the re-entry
  could survive. Recursive graphs are a consumer error; the recourse is
  ``fields=`` scoping on one participating hook. The one permitted re-entrant
  shape is an explicit zero-edge scope (``fields=[]``): it walks nothing and
  composes nothing, so a self-referential type's hook can cascade with
  ``fields=[]`` and the enclosing edge still binds the hook's direct
  narrowing.
- **Every registered target composes.** Each edge whose target model has a
  registered primary type contributes a subquery built from the target's
  ``_default_manager`` on the root alias and run through its ``get_queryset``
  -- *including* identity hooks. An identity-hook target used to be skipped as
  "nothing to narrow", which silently bypassed a registered proxy type whose
  filtered ``_default_manager`` IS its visibility policy. Only an edge whose
  target model has no registered type is outside the visibility contract.
- **Hook returns are validated, then normalized.** A target hook must return
  a ``QuerySet`` over the edge target's concrete table (proxy / concrete
  siblings are compatible; unrelated models and MTI child querysets are not),
  unsliced, uncombined (no ``union()`` etc.), ungrouped (no aggregate
  ``annotate`` / ``values()`` grouping), without field-specific
  ``distinct(...)``, without an ``extra(select=...)`` alias shadowing the
  target column, and on the root alias -- re-projection is only sound where
  ``.values(...)`` changes the selected column, not the query's semantics.
  The accepted queryset is re-projected to ``.values(target_field.attname)``
  so the ``__in`` comparison always binds the FK's actual target column --
  a consumer ``.values("name")`` / ``.values_list(...)`` projection (or a
  ``ForeignKey(to_field=...)`` edge fed a pk projection) can no longer compare
  the wrong column.
- **One database.** The root call pins ``queryset.db``; every nested cascade
  application and every hook return must stay on that alias, raising
  ``ConfigurationError`` before Django would attempt (or silently mis-compose)
  a cross-database subquery.
- **MTI parent links cascade.** The auto-generated ``<parent>_ptr``
  ``OneToOneField(parent_link=True)`` is a real single-column concrete forward
  edge; a child row whose MTI parent the parent type hides is dropped. (The
  previous contract excluded parent links, leaving a hidden parent reachable
  through its child type.)
- **Unsupported forward relations preflight.** A ``GenericForeignKey`` (or any
  future composite / multi-column forward relation) can neither be composed as
  a single-column subquery nor safely skipped, so a full walk (``fields=None``)
  over a model carrying one fails before any visibility hook runs, and naming
  one in ``fields=`` fails at validation. The GFK's *backing* ``content_type``
  FK is an ordinary single-column edge and may be selected explicitly;
  ``object_id`` is a scalar and never an edge. Reverse FK / reverse OneToOne,
  M2M, and ``GenericRelation`` stay outside parent-row cascade semantics and
  are skipped as before.
- **Nullable edges only get the ``__isnull`` disjunct.** ``| Q(<edge>__isnull
  =True)`` is added only when the Django field is nullable; a non-nullable
  edge composes the bare membership test.

The per-edge target-hook invocation is delegated to
``utils/querysets.py::apply_type_visibility_sync`` so the package has ONE place
that runs a sync ``get_queryset`` and rejects an async hook with
``SyncMisuseError`` (the coroutine is closed first) -- a visibility-hook-routing
mistake is a data-leak bug, so the routing is not re-decided here. The async
twin wraps the single sync walk in ``run_in_one_sync_boundary`` (the neutral
``sync_to_async(thread_sensitive=True)`` owner in ``utils/querysets.py``) so
blocking consumer-hook work (e.g. ``user.has_perm(...)`` permission-table
reads) stays off the event loop; there is no second async walk implementation.
An ``async def`` target hook therefore raises ``SyncMisuseError`` from both
variants -- inside the wrapped worker thread there is still no awaiting
context.
"""

from __future__ import annotations

import dataclasses
from contextvars import ContextVar
from functools import lru_cache
from typing import Any, NamedTuple

from django.db import models
from django.db.models import Q
from django.db.models.fields.reverse_related import ForeignObjectRel

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
from .utils.querysets import apply_type_visibility_sync, model_for, run_in_one_sync_boundary

_ASYNC_RECOURSE = (
    "apply_cascade_permissions walks target hooks synchronously and "
    "aapply_cascade_permissions wraps that same sync walk, so neither "
    "can await an async target hook; make this target type's "
    "get_queryset sync, or pass fields= to skip the async-hooked edge."
)


@dataclasses.dataclass(frozen=True)
class _TraversalState:
    """Immutable per-walk traversal state carried by the ``ContextVar``.

    ``alias`` is the root call's resolved DB alias (``queryset.db``) -- every
    nested application and hook return is validated against it. ``active`` is
    the ordered tuple of in-flight ``DjangoType`` classes; re-entry into a
    member raises the fail-closed cycle error. ``path`` is the ordered
    ``"TypeName.edge"`` frame tuple rendering the path-rich cycle message.
    Frozen so a frame can only *replace* the state through a token-scoped
    ``set``/``reset`` pair -- no in-place mutation can survive an exception or
    leak into a sibling frame.
    """

    alias: str
    active: tuple[type, ...]
    path: tuple[str, ...]


# ``None`` means "no walk in flight" -- the next call is the root and installs a
# fresh state; a ``_TraversalState`` means "walk in flight". Every install is
# token-based and reset in a ``finally``, so a consumer-hook exception cannot
# leak stale state into the next request sharing the context. A ``ContextVar``
# (not a plain global) so isolation holds under both WSGI and ASGI, and so the
# async variant's ``sync_to_async`` worker thread sees a *copied* context
# (asgiref runs ``contextvars.copy_context()`` into the thread): its
# install/reset is scoped to that copy and never leaks back into the event-loop
# task.
_cascade_state: ContextVar[_TraversalState | None] = ContextVar("_cascade_state", default=None)


class _EdgePlan(NamedTuple):
    """One model's cached relation-descriptor classification.

    ``cascadable`` is the tuple of single-column concrete forward FK / OneToOne
    fields (MTI parent links included) the walk composes. ``unsupported`` is
    the tuple of forward-relation *names* the cascade can neither compose nor
    safely skip (``GenericForeignKey``, composite / multi-column forward
    relations): a full walk over a model carrying one fails closed before any
    hook runs, and ``fields=`` naming one fails at validation.
    """

    cascadable: tuple[Any, ...]
    unsupported: tuple[str, ...]


def _is_cascadable_edge(field: Any) -> bool:
    """Return whether ``field`` is a single-column concrete forward FK / OneToOne edge.

    The single definition of "cascadable edge" -- the full walk, the
    ``fields=`` validator, and the preflight all key off the cached
    ``_edge_plan`` built from this predicate, so scope cannot drift.
    ``isinstance(field, models.ForeignKey)`` is the forward-concrete test:
    ``OneToOneField`` subclasses ``ForeignKey`` (MTI ``<parent>_ptr`` parent
    links included -- a hidden MTI parent must hide its child row, so the
    parent link cascades like any other O2O edge), while reverse relations
    (``ForeignObjectRel``), M2M (join-table-backed), ``GenericForeignKey``
    (virtual, polymorphic), ``GenericRelation`` (a ``ForeignObject`` but not a
    ``ForeignKey``), and plain multi-column ``ForeignObject`` relations are
    all excluded by construction. The ``column`` check guards the
    single-column contract against a future ``ForeignKey`` shape whose value
    is not one concrete column.
    """
    return isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None


def _is_unsupported_forward_edge(field: Any) -> bool:
    """Return whether ``field`` is a forward relation the cascade must fail closed on.

    A forward relation that is not a single-column concrete FK / OneToOne --
    ``GenericForeignKey`` (polymorphic target, no single visibility policy to
    compose) or a composite / multi-column ``ForeignObject`` -- cannot be
    expressed as a one-column ``__in`` subquery, and silently *skipping* it
    would let a row pointing at a hidden target survive the cascade. Reverse
    relations (``ForeignObjectRel``), M2M, and one-to-many virtual relations
    (``GenericRelation``) are outside parent-row cascade semantics entirely
    (they do not select a parent row's single target) and stay skippable.
    """
    return (
        getattr(field, "is_relation", False)
        and not isinstance(field, ForeignObjectRel)
        and not field.many_to_many
        and not field.one_to_many
        and not _is_cascadable_edge(field)
    )


@lru_cache(maxsize=1024)
def _edge_plan(model: type[models.Model]) -> _EdgePlan:
    """Return ``model``'s cached relation-descriptor plan.

    Django model metadata is immutable after app loading, while cascade hooks
    run per request. Classify ``model._meta.get_fields()`` once per model so
    ``fields=`` validation, the preflight, and the walk share one metadata
    slice. The bounded cache keeps synthetic/dynamic test models from growing
    this process-wide helper without limit; eviction is correctness-neutral
    because the plan can always be recomputed.
    """
    cascadable = []
    unsupported = []
    for field in model._meta.get_fields():
        if _is_cascadable_edge(field):
            cascadable.append(field)
        elif _is_unsupported_forward_edge(field):
            unsupported.append(field.name)
    return _EdgePlan(cascadable=tuple(cascadable), unsupported=tuple(unsupported))


def _cascadable_edges(model: type[models.Model]) -> tuple[Any, ...]:
    """Return ``model``'s cascadable edge fields (the cached plan's tuple)."""
    return _edge_plan(model).cascadable


def _cascadable_edge_names(model: type[models.Model]) -> frozenset[str]:
    """Return the names of ``model``'s cascadable edges (Decision 5 step 1)."""
    return frozenset(field.name for field in _cascadable_edges(model))


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
    Otherwise every supplied name must be a cascadable edge. A name matching an
    *unsupported* forward relation (``GenericForeignKey`` / composite) raises
    the dedicated no-cascade-semantics error; other unknown or
    known-but-non-cascadable names raise ``ConfigurationError`` naming the
    offending entry, the model, and the cascadable set. A cascadable name whose
    target lacks a registered type validates clean here and is skipped by the
    walk's per-edge gate (Decision 9).
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
    plan = _edge_plan(model)
    unsupported = requested.intersection(plan.unsupported)
    if unsupported:
        raise ConfigurationError(
            f"apply_cascade_permissions fields={sorted(unsupported)!r} on "
            f"{model.__name__} have no single-column cascade semantics: a "
            f"GenericForeignKey or composite forward relation cannot be composed "
            f"as a visibility subquery. Select its real backing FK (for a GFK, "
            f"the content_type edge) or drop the entry.",
        )
    cascadable = frozenset(field.name for field in plan.cascadable)
    unknown = requested - cascadable
    if unknown:
        raise ConfigurationError(
            f"apply_cascade_permissions fields={sorted(unknown)!r} on "
            f"{model.__name__} are not cascadable; the cascadable edges are "
            f"{sorted(cascadable)!r}.",
        )
    return requested


def _structural_defect(queryset: Any, model: type[models.Model]) -> tuple[str, str] | None:
    """Return the first structural defect shared by root and hook-return validation.

    Both validation sites reject the same four composability-breaking shapes --
    non-``QuerySet``, wrong concrete table, sliced, combined -- but with
    site-specific error prose. Single-sourcing the *checks* here (each site owns
    only its messages) keeps the two batteries from drifting apart; the missing
    sliced/combined root checks in the first cut were exactly that drift.
    Returns ``(code, detail)`` -- ``code`` in ``{"type", "table", "sliced",
    "combined"}`` -- or ``None`` when the queryset is structurally composable.
    """
    if not isinstance(queryset, models.QuerySet):
        return ("type", type(queryset).__name__)
    if queryset.model._meta.concrete_model is not model._meta.concrete_model:
        return ("table", queryset.model.__name__)
    if queryset.query.is_sliced:
        return ("sliced", "")
    if queryset.query.combinator:
        return ("combined", queryset.query.combinator)
    return None


def _validate_root_queryset(cls: type, queryset: Any, model: type[models.Model]) -> None:
    """Reject a root/nested ``queryset`` that is not this type's model rows.

    The composed constraints are only sound over a real ``QuerySet`` of
    ``cls``'s model rows: a list or ``Manager`` has no lazy query to compose
    into, and a queryset over an unrelated model (or an MTI sibling on a
    different concrete table) would attach the edge filters to the wrong
    table. Proxy / concrete siblings share the concrete table and are
    accepted. Sliced and combined (``union()`` / ``intersection()`` /
    ``difference()``) roots are rejected up front: the walk narrows by
    ``.filter(...)``, which Django refuses on both shapes, so accepting one
    would leak a raw ``TypeError`` / ``NotSupportedError`` mid-walk instead of
    the fail-closed configuration error.
    """
    defect = _structural_defect(queryset, model)
    if defect is None:
        return
    code, detail = defect
    if code == "type":
        raise ConfigurationError(
            f"apply_cascade_permissions requires a QuerySet of {model.__name__} "
            f"rows for {cls.__name__}; got {detail}. Pass the "
            f"get_queryset hook's queryset (a Manager needs .all(); a list has "
            f"no lazy query to compose into).",
        )
    if code == "table":
        raise ConfigurationError(
            f"apply_cascade_permissions for {cls.__name__} requires a QuerySet "
            f"over {model.__name__}'s concrete table; got a {detail} queryset.",
        )
    if code == "sliced":
        raise ConfigurationError(
            f"apply_cascade_permissions for {cls.__name__} got a sliced "
            f"queryset; the cascade narrows by .filter(...), which cannot be "
            f"applied after a slice. Cascade first, slice after.",
        )
    # ``code == "combined"`` -- the only remaining defect the shared checker
    # emits; an unhandled future code would fall through silently, so this
    # last branch is unconditional.
    raise ConfigurationError(
        f"apply_cascade_permissions for {cls.__name__} got a {detail}() "
        f"combined queryset; the cascade narrows by .filter(...), which Django "
        f"does not support after a combinator. Cascade each branch before "
        f"combining.",
    )


def _validated_target_subquery(
    target_type: type,
    target_qs: Any,
    field: Any,
    alias: str,
) -> models.QuerySet:
    """Validate a target hook's return and normalize it to the edge's target column.

    The hook return becomes the RHS of ``Q(<edge>__in=...)`` -- a row-visibility
    predicate -- so every shape that would compare the wrong column or the
    wrong database fails closed here, before composition. The accepted
    queryset is re-projected to ``.values(field.target_field.attname)`` so the
    membership test always binds the FK's actual target column: a consumer
    ``.values(...)`` / ``.values_list(...)`` projection is overridden rather
    than trusted, and a ``ForeignKey(to_field=...)`` edge compares its
    ``to_field`` column, never a stray pk projection.

    Re-projection is only sound where ``.values(...)`` merely changes the
    selected column. Shapes where it changes *semantics* are rejected instead
    of "repaired": a grouped queryset (aggregate ``annotate`` / ``values()``
    grouping) would gain a different ``GROUP BY``, silently widening the
    visible set; a combined queryset (``union()`` etc.) only rewrites the
    outer projection while each branch keeps selecting its original column;
    an ``extra(select={...})`` alias shadowing the target column would make
    ``.values(...)`` select the raw-SQL expression, not the model column.
    """
    defect = _structural_defect(target_qs, field.related_model)
    if defect is not None:
        code, detail = defect
        if code == "type":
            raise ConfigurationError(
                f"{target_type.__name__}.get_queryset must return a QuerySet for "
                f"the cascade subquery on {field.model.__name__}.{field.name}; "
                f"got {detail}.",
            )
        if code == "table":
            raise ConfigurationError(
                f"{target_type.__name__}.get_queryset returned a {detail} "
                f"queryset for the cascade subquery on "
                f"{field.model.__name__}.{field.name}, which targets "
                f"{field.related_model.__name__}; the subquery must stay on the "
                f"target's concrete table (proxy siblings are compatible, MTI "
                f"children are not).",
            )
        if code == "sliced":
            raise ConfigurationError(
                f"{target_type.__name__}.get_queryset returned a sliced queryset "
                f"for the cascade subquery on "
                f"{field.model.__name__}.{field.name}; a LIMIT/OFFSET visibility "
                f"predicate is row-order-dependent and cannot compose as an __in "
                f"subquery.",
            )
        # ``code == "combined"`` (see _validate_root_queryset for the
        # fall-through rationale).
        raise ConfigurationError(
            f"{target_type.__name__}.get_queryset returned a {detail}() combined "
            f"queryset for the cascade subquery on "
            f"{field.model.__name__}.{field.name}; re-projecting a combined "
            f"queryset only rewrites the outer projection while each branch "
            f"keeps its original column, so it cannot be safely bound to the "
            f"edge's target column.",
        )
    if target_qs.query.distinct_fields:
        raise ConfigurationError(
            f"{target_type.__name__}.get_queryset returned a queryset with "
            f"field-specific distinct({', '.join(map(repr, target_qs.query.distinct_fields))}) "
            f"for the cascade subquery on {field.model.__name__}.{field.name}; "
            f"the cascade re-projects the subquery to the edge's target column, "
            f"which would change which rows DISTINCT ON keeps.",
        )
    if target_qs.query.group_by is not None:
        raise ConfigurationError(
            f"{target_type.__name__}.get_queryset returned a grouped "
            f"(aggregate-annotated) queryset for the cascade subquery on "
            f"{field.model.__name__}.{field.name}; re-projecting a grouped "
            f"queryset changes its GROUP BY and can widen the visible set. "
            f"Return plain rows and let the cascade project the edge's target "
            f"column.",
        )
    attname = field.target_field.attname
    if attname in target_qs.query.extra:
        raise ConfigurationError(
            f"{target_type.__name__}.get_queryset returned a queryset whose "
            f"extra(select=...) alias shadows {attname!r} for the cascade "
            f"subquery on {field.model.__name__}.{field.name}; the cascade "
            f"must project the model column, not a raw-SQL alias of the same "
            f"name.",
        )
    if target_qs.db != alias:
        raise ConfigurationError(
            f"{target_type.__name__}.get_queryset returned a queryset on alias "
            f"{target_qs.db!r} for the cascade subquery on "
            f"{field.model.__name__}.{field.name}, but the cascade is pinned to "
            f"{alias!r}; a cascade cannot compose cross-database subqueries.",
        )
    return target_qs.values(attname)


def _cycle_error(state: _TraversalState, cls: type) -> ConfigurationError:
    """Build the path-rich fail-closed cycle error for re-entry into ``cls``."""
    path = " -> ".join((*state.path, cls.__name__))
    return ConfigurationError(
        f"apply_cascade_permissions detected a cascade visibility cycle: {path}. "
        f"A recursive cascade graph fails closed (a silently broken cycle would "
        f"skip the re-entered type's outgoing visibility edges); pass fields= in "
        f"one participating hook to break the cycle explicitly.",
    )


def apply_cascade_permissions(
    cls: type,
    queryset: models.QuerySet,
    info: Any,
    fields: Any = None,
) -> models.QuerySet:
    """Narrow ``queryset`` so each forward relation respects its target visibility.

    Call from inside a ``DjangoType.get_queryset`` (Decision 5). Walks ``cls``'s
    model single-column concrete forward FK / OneToOne edges (MTI parent links
    included), resolves each edge's target type through the registry primary
    lookup, runs that type's ``get_queryset`` against the target model's
    ``_default_manager`` rows (pinned to the root call's resolved DB alias --
    identity hooks included, so a filtered default manager still narrows), and
    intersects ``Q(<edge>__in=<visible>)`` (plus ``| Q(<edge>__isnull=True)``
    when the edge is nullable) into ``queryset``. Edges whose target model has
    no registered type are skipped -- there is no visibility policy to apply.
    Returns a narrowed queryset; never evaluates, reorders, or projects the
    caller's queryset -- pure ``.filter(...)`` composition, so the ``__in``
    subqueries compile into the caller's single ``SELECT`` and add zero query
    round-trips (Decision 7).

    Args:
        cls: the owning ``DjangoType`` (its ``.model`` is the walk root).
        queryset: the caller's already-visibility-filtered queryset (a real
            ``QuerySet`` over the model's concrete table).
        info: the Strawberry resolver ``info`` (threaded into each target hook).
        fields: optional iterable of model field names scoping the walk to those
            edges; ``None`` walks every cascadable edge, ``[]`` cascades nothing.
            A bare string raises (Decision 9).

    Raises:
        ConfigurationError: a malformed ``queryset`` (non-``QuerySet`` /
            wrong concrete table / sliced / combined -- the walk narrows by
            ``.filter(...)``, which supports neither); a bare-string ``fields=``
            or a ``fields=``
            name that is unknown, non-cascadable, or an unsupported forward
            relation; a full walk over a model carrying an unsupported forward
            relation (``GenericForeignKey`` / composite -- preflighted before
            any hook runs); a cascade cycle (fail-closed, path-rich); a nested
            application or hook return that leaves the root DB alias; a hook
            return that is not an unsliced, uncombined, ungrouped,
            non-``distinct(...)``, non-column-shadowing queryset over the edge
            target's concrete table.
        SyncMisuseError: a target type's ``get_queryset`` is ``async def``. The
            async twin ``aapply_cascade_permissions`` wraps this same sync walk, so
            it raises identically -- the recourse is to make the target hook sync,
            or pass ``fields=`` to skip the async-hooked edge (Decision 10).
    """
    model = model_for(cls)
    _validate_root_queryset(cls, queryset, model)
    names_to_walk = _validate_fields(model, fields)
    plan = _edge_plan(model)
    if names_to_walk is None and plan.unsupported:
        # Preflight: fail before any visibility hook runs. A full walk cannot
        # compose these edges and must not silently skip them.
        raise ConfigurationError(
            f"apply_cascade_permissions cannot walk every edge of {model.__name__}: "
            f"forward relation(s) {sorted(plan.unsupported)!r} have no "
            f"single-column cascade semantics (a GenericForeignKey or composite "
            f"forward relation cannot be composed as a visibility subquery, and "
            f"skipping one would leak rows pointing at hidden targets); pass "
            f"fields= naming the edges to walk explicitly.",
        )

    state = _cascade_state.get()
    if state is None:
        state = _TraversalState(alias=queryset.db, active=(cls,), path=())
    else:
        if queryset.db != state.alias:
            raise ConfigurationError(
                f"apply_cascade_permissions nested walk for {cls.__name__} runs on "
                f"alias {queryset.db!r} but the root cascade is pinned to "
                f"{state.alias!r}; a cascade cannot compose cross-database "
                f"subqueries.",
            )
        if cls in state.active:
            if names_to_walk == set():
                # The documented cycle-breaking recourse: an explicit zero-edge
                # scope (``fields=[]``) walks nothing and composes nothing, so
                # a re-entrant application of it is provably non-recursive --
                # the enclosing edge's subquery carries exactly the hook's own
                # direct narrowing. Any re-entry that would walk an edge (a
                # full walk or a non-empty subset) stays fail-closed below.
                return queryset
            raise _cycle_error(state, cls)
        state = dataclasses.replace(state, active=(*state.active, cls))
    token = _cascade_state.set(state)
    try:
        return _walk(cls, model, queryset, info, names_to_walk, state)
    finally:
        _cascade_state.reset(token)


def _walk(
    cls: type,
    model: type[models.Model],
    queryset: models.QuerySet,
    info: Any,
    names_to_walk: set[str] | None,
    state: _TraversalState,
) -> models.QuerySet:
    """Intersect one visibility constraint per qualifying edge of ``model``.

    The caller owns the walk-frame lifecycle (state install / cycle raise /
    token reset); this function composes the per-edge subqueries and owns the
    per-edge frame: each target-hook invocation runs under a token-scoped state
    carrying the ``"TypeName.edge"`` path frame, so a nested cascade inside the
    hook renders the full path on a cycle and the frame unwinds on any
    exception. ``names_to_walk`` is ``None`` for the full walk or a validated
    edge-name set for the ``fields=`` scoped walk.
    """
    for field in _edge_plan(model).cascadable:
        if names_to_walk is not None and field.name not in names_to_walk:
            continue
        target_type = registry.get(field.related_model)
        if target_type is None:
            continue
        base = field.related_model._default_manager.using(state.alias).all()
        edge_state = dataclasses.replace(
            state,
            path=(*state.path, f"{cls.__name__}.{field.name}"),
        )
        edge_token = _cascade_state.set(edge_state)
        try:
            target_qs = apply_type_visibility_sync(
                target_type,
                base,
                info,
                async_recourse=_ASYNC_RECOURSE,
            )
        finally:
            _cascade_state.reset(edge_token)
        subquery = _validated_target_subquery(target_type, target_qs, field, state.alias)
        condition = Q(**{f"{field.name}__in": subquery})
        if field.null:
            condition |= Q(**{f"{field.name}__isnull": True})
        queryset = queryset.filter(condition)
    return queryset


async def aapply_cascade_permissions(
    cls: type,
    queryset: models.QuerySet,
    info: Any,
    fields: Any = None,
) -> models.QuerySet:
    """Async twin of ``apply_cascade_permissions`` -- the same walk, off the event loop.

    Wraps the single sync walk in ``run_in_one_sync_boundary`` so blocking
    consumer-hook work (permission-table reads inside a target type's
    ``get_queryset``) never runs on the event loop. The ``ContextVar``
    install/reset happens inside the worker thread on the asgiref-copied
    context, so it never leaks back into the calling async task. An
    ``async def`` target hook still raises ``SyncMisuseError`` (no awaiting
    context inside the thread); narrow with ``fields=`` to skip an
    async-hooked edge (Decision 10).
    """
    return await run_in_one_sync_boundary(
        apply_cascade_permissions,
        cls,
        queryset,
        info,
        fields,
    )
