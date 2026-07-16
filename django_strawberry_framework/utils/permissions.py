"""Shared permission traversal and Django/Channels request-context decoding.

FilterSet and OrderSet independently grew the SAME active-input permission
contract: resolve the request from ``info``, walk only supplied input fields,
dedupe ``check_<field>_permission`` calls by class, recurse into active related
branches, and fire both child gates and parent branch gates. A divergence
between the two copies is a real authorization-bug class -- a fix to one side is
easy to miss on the other -- so the neutral mechanics are single-sited here (the
0.0.9 DRY pass, ``docs/feedback.md`` Major 3).

This module owns mechanics only; the family-specific shape stays at the call
sites as configuration:

* the filter side passes ``unset_sentinel=strawberry.UNSET`` (its inputs default
  unsupplied fields to ``UNSET``); the order side leaves it ``None``;
* the filter side's logical ``and`` / ``or`` / ``not`` recursion and depth cap
  stay in ``FilterSet._run_permission_checks`` (wrapped around
  ``run_active_input_permission_checks``); the order side handles a top-level
  list of order-input dataclasses via ``handle_top_level_list=True``.

It depends on neither family package (it operates on a duck-typed ``cls`` that
exposes the per-family permission methods), so both can import it without a
cycle -- same contract as ``utils/connections.py`` / ``utils/inputs.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import lru_cache
from typing import Any

from django.db.models.constants import LOOKUP_SEP
from django.http import HttpRequest

from ..exceptions import ConfigurationError
from .input_values import (
    LEAF,
    RELATED,
    SetInputTraversal,
    input_field_value,
    is_inactive_value,
    iter_active_fields,
    iter_input_items,
)
from .querysets import reject_async_in_sync_context
from .strings import flatten_lookup_path

# Recourse text shared by every ``check_<field>_permission`` async-guard raise. A
# filter / order permission gate is fired synchronously (on the async surface it
# runs on the single ``sync_to_async`` worker that ``_apply_common_finalize``
# wraps), so it can never await; an ``async def`` gate returns a TRUTHY, orphaned
# coroutine and a naive call would treat that as a silent success -- an
# authorization BYPASS. Mirrors ``mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE``.
_GATE_ASYNC_RECOURSE = (
    "A FilterSet / OrderSet permission gate runs synchronously, so it cannot await "
    "an async hook; redefine check_<field>_permission as a sync method (def, not "
    "async def)."
)

# Fallback cap on the RELATED-branch recursion when a set defines no
# ``_MAX_LOGIC_DEPTH`` of its own (``OrderSet`` -- ordering has no logical
# operator-bag, so it never grew the filter side's cap). A self-referential
# ``RelatedFilter`` / ``RelatedOrder`` (e.g. ``CardFilter.dependencies`` pointing
# back at ``CardFilter``) lets a client nest the same branch to arbitrary depth;
# without a cap the input-driven recursion here bottoms out in a raw
# ``RecursionError`` (a 500) instead of a typed, catchable ``ConfigurationError``.
# Mirrors ``FilterSet._MAX_LOGIC_DEPTH`` so the two sides share one budget.
_MAX_RELATED_RECURSION_DEPTH = 8


@lru_cache(maxsize=2048)
def _check_method_name(field_path: str) -> str:
    """Map a field path to its ``check_<field>_permission`` method name.

    The transform is request-independent (it depends only on the declared field
    path), so it is memoized over the bounded set of declared paths; only the
    bound-instance ``getattr`` / ``callable`` probe in
    ``invoke_permission_method`` stays per-request (feedback L5). The lookup
    flatten itself is the shared ``flatten_lookup_path`` (DRY review A9).
    """
    return f"check_{flatten_lookup_path(field_path)}_permission"


# ``iter_input_items`` is single-sited in ``utils/input_values.py`` (the 0.0.9
# DRY pass, ``docs/feedback.md`` Major 1). Re-exported here so the existing
# ``from ..utils.permissions import iter_input_items`` consumers (``filters/sets.py``,
# the permission test suite) keep their import path.
__all__ = [
    "ChannelsRequestAdapter",
    "active_permission_field_paths",
    "active_permission_targets",
    "active_related_branches",
    "extract_branch_value",
    "invoke_permission_method",
    "iter_input_items",
    "request_from_info",
    "run_active_input_permission_checks",
    "verbatim_path",
]


class ChannelsRequestAdapter:
    """Request-like wrapper for Strawberry's Channels context values.

    The HTTP consumer supplies a ``ChannelsRequest`` whose scope lives at
    ``request.consumer.scope``. The WebSocket consumer supplies itself, with the
    scope directly at ``request.scope``. This adapter exposes ``user``,
    ``session``, and ``scope`` consistently for both shapes and delegates every
    other attribute to the original context value.

    The contract is deliberately duck-typed so importing this module does not
    require the optional ``channels`` dependency (spec-041 Decision 11).
    """

    def __init__(self, request: Any, scope: Mapping[str, Any]) -> None:
        self._request = request
        self._scope = scope

    @property
    def scope(self) -> Mapping[str, Any]:
        """Return the resolved Channels connection scope."""
        return self._scope

    @property
    def user(self) -> Any:
        """The scope's ``user`` (``AuthMiddlewareStack``-populated); ``None`` when absent."""
        return self._scope.get("user")

    @property
    def session(self) -> Any:
        """The scope's ``session`` (``SessionMiddleware``-populated); ``None`` when absent."""
        return self._scope.get("session")

    def __getattr__(self, name: str) -> Any:
        """Delegate every non-scope attribute to the original context value."""
        return getattr(self._request, name)


def _channels_scope(request: Any) -> Mapping[str, Any] | None:
    """Resolve Strawberry's HTTP or WebSocket Channels scope shape."""
    consumer = getattr(request, "consumer", None)
    scope = getattr(consumer, "scope", None)
    if isinstance(scope, Mapping):
        return scope
    scope = getattr(request, "scope", None)
    if isinstance(scope, Mapping):
        return scope
    return None


def _channels_request_adapter(context: Any) -> ChannelsRequestAdapter | None:
    """Resolve a mapping context to the Channels adapter; ``None`` for every other shape.

    The recognized value carries a mapping scope through ``consumer.scope``
    (HTTP) or directly through ``scope`` (WebSocket). Keeping this recognition
    here preserves the single request-decoder boundary from spec-041 D-P2.
    """
    if not isinstance(context, Mapping):
        return None
    request = context.get("request")
    if request is None:
        return None
    scope = _channels_scope(request)
    if scope is None:
        return None
    return ChannelsRequestAdapter(request, scope)


def _request_from_context(context: Any) -> Any | None:
    """Resolve every supported Django or Channels request context shape."""
    request = getattr(context, "request", None)
    if request is not None:
        return request
    if isinstance(context, HttpRequest):
        return context
    return _channels_request_adapter(context)


def request_from_info(info: Any, *, family_label: str) -> Any:
    """Resolve the Django request from ``info.context``.

    Canonical Strawberry-Django shape: ``info.context.request``. The
    wrapper-less alternative (``info.context`` *is* a bare ``HttpRequest`` -- the
    Django test-client default) is also accepted so consumers work without
    bespoke wiring. Strawberry's Channels mapping context is also accepted: its
    ``"request"`` carries the ASGI scope through ``consumer.scope`` for HTTP or
    directly through ``scope`` for WebSockets and is wrapped in a
    ``ChannelsRequestAdapter`` (spec-041 Decision 11). Any other shape raises
    ``ConfigurationError`` naming ``family_label`` (``FilterSet`` / ``OrderSet``
    / ``DjangoMutation``) so the consumer sees which surface failed. The message
    is **family-neutral** (no ``.apply`` suffix): the helper is shared by the
    filter / order ``apply`` seam AND the mutation ``check_permission`` seam,
    which has no ``.apply`` method, so hard-coding ``.apply`` would mis-describe
    the mutation caller (feedback CR-5).
    """
    context = getattr(info, "context", None)
    if context is None:
        raise ConfigurationError(
            f"{family_label} requires `info.context`; received `info` without a context.",
        )
    request = _request_from_context(context)
    if request is not None:
        return request
    raise ConfigurationError(
        f"{family_label} could not resolve a Django HttpRequest from `info.context` "
        f"(got {type(context).__name__}). Expected `info.context.request`, a bare "
        "HttpRequest, or a Strawberry Channels mapping context whose `request` "
        'carries an ASGI scope (`context["request"].consumer.scope` for the HTTP '
        'consumer, `context["request"].scope` for the WebSocket consumer).',
    )


def _safe_get_model(app_label: str, model_name: str) -> type | None:
    """Return the named model, or ``None`` when the app / model is not installed."""
    from django.apps import apps

    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


def resolve_auth_aliases() -> frozenset[str]:
    """The database aliases the auth machinery reads from (for the authorization phase).

    The write pipeline's dedicated authorization phase permits READ-ONLY SQL on
    exactly these aliases while it resolves the request user + permission set, so
    a divergent read/write router that keeps auth OFF the write alias is not
    rejected as a cross-alias read. Derived from the router's own read answer for
    the auth models actually queried during permission evaluation - the user
    model, ``auth.Permission`` / ``auth.Group``, and
    ``contenttypes.ContentType`` - so it tracks whatever alias each deployment
    routes auth to (``default`` in the common single-database case). A model the
    deployment does not install is skipped; an empty result grants nothing. This
    replaces the old pre-guard permission-cache warming: the authorization phase
    now does its real work on the auth alias directly, which fills the same
    per-user cache as a side effect, so later ``has_perm`` reads stay cache-only.
    """
    from django.conf import settings
    from django.db import router

    # ``AUTH_USER_MODEL`` is ``"app_label.ModelName"``; resolving it through the
    # same ``_safe_get_model`` as the other auth models keeps ONE code path (an
    # uninstalled / misconfigured model is skipped, never an error).
    user_app_label, _, user_model_name = settings.AUTH_USER_MODEL.partition(".")
    candidates = [
        _safe_get_model(user_app_label, user_model_name),
        _safe_get_model("auth", "Permission"),
        _safe_get_model("auth", "Group"),
        _safe_get_model("contenttypes", "ContentType"),
    ]
    aliases = {router.db_for_read(model) for model in candidates if model is not None}
    aliases.discard(None)
    return frozenset(aliases)


def extract_branch_value(input_value: Any, field_name: str, *, unset_sentinel: Any = None) -> Any:
    """Return the value at ``field_name`` on a dataclass-or-dict input.

    Collapses ``None`` (and ``unset_sentinel``, when the family supplies one) to
    "branch not supplied" so the active-branch caller treats absent branches
    uniformly. The filter side passes ``unset_sentinel=strawberry.UNSET`` because
    Strawberry input dataclasses default unsupplied fields to ``UNSET``; the
    order side leaves it ``None`` (its inputs default to ``None``), which makes
    the sentinel check a harmless ``value is None`` no-op.

    Shares the active-value rule with every traversal surface via
    ``input_values.is_inactive_value`` (the 0.0.9 DRY pass, ``docs/feedback.md``
    Major 1). Used by the filter side's logical-branch pre-walk
    (``_collect_nested_visibility_querysets_async``) to read ``and_`` / ``or_`` /
    ``not_`` arms off the raw input. The dict-vs-dataclass single-field read is
    ``input_values.input_field_value`` (DRY review C6), so the shape sniff stays
    single-sited in the traversal-primitives module.
    """
    if input_value is None:
        return None
    value = input_field_value(input_value, field_name)
    return None if is_inactive_value(value, unset_sentinel=unset_sentinel) else value


def invoke_permission_method(
    bare_instance: Any,
    field_path: str,
    request: Any,
    *,
    fired: set[str] | None = None,
) -> None:
    """Call ``check_<field_path>_permission(request)`` if defined on ``bare_instance``.

    When ``fired`` is supplied, the method name is recorded after a successful
    fire and subsequent calls with the same name skip the attribute lookup
    entirely. The dedup is scoped to the supplied set -- the caller passes the
    per-class set keyed out of its shared ``_fired`` map.

    The gate result runs through ``reject_async_in_sync_context``: an
    ``async def check_<field>_permission`` returns a truthy, un-awaited coroutine
    whose ``raise`` never executes, so an intended DENIAL would silently become a
    no-op -- an authorization BYPASS. This is the same guard every sibling
    authorization seam already applies (``mutations/permissions.py`` /
    ``mutations/resolvers.py`` write hooks, ``utils/querysets.py`` ``get_queryset``
    visibility); the filter / order gate is fired the same synchronous way (on the
    async surface it runs on the ``sync_to_async`` worker ``_apply_common_finalize``
    wraps), so an async gate is rejected loudly with ``SyncMisuseError`` on both
    surfaces rather than passed through as a silent allow.
    """
    method_name = _check_method_name(field_path)
    if fired is not None and method_name in fired:
        return
    method = getattr(bare_instance, method_name, None)
    if callable(method):
        reject_async_in_sync_context(
            method(request),
            owner=type(bare_instance).__name__,
            method=method_name,
            context="permission-check",
            recourse=_GATE_ASYNC_RECOURSE,
        )
        if fired is not None:
            fired.add(method_name)


def verbatim_path(python_attr: str) -> str:
    """Shared identity ``fallback_path``: the python attr IS its own source path.

    Used wherever a caller has no lookup-to-source remapping to apply -- the
    related-only ``active_related_branches`` discard caller and the order side's
    ``OrderSet._active_permission_targets`` (whose order attrs map verbatim). The
    filter side passes its own real remap instead. Module-level (not a per-call
    lambda) so order-side traversals do not allocate a fresh closure each walk.
    """
    return python_attr


def active_permission_targets(
    cls: type,
    input_value: Any,
    *,
    field_specs: Mapping[Any, Any],
    related_attr: str,
    logic_keys: frozenset[str],
    fallback_path: Callable[[str], str],
    unset_sentinel: Any = None,
    handle_top_level_list: bool = False,
) -> tuple[list[str], list[tuple[str, Any, Any]]]:
    """Partition active top-level fields into ``(leaf_paths, related_branches)`` in ONE walk.

    ``run_active_input_permission_checks`` needs both the per-field gate paths
    (``LEAF``) and the related branches (``RELATED``) at the same nesting level.
    Running ``iter_active_fields`` once and partitioning by ``.kind`` removes the
    second full traversal + re-classification + config rebuild the two separate
    walkers otherwise pay per level (feedback H3). ``LOGIC`` records are dropped
    (the logical-branch recursion owns them).

    The single config is the superset of the two callers': ``field_specs`` and
    ``logic_keys`` are populated. ``RELATED`` classification keys only off
    ``related_attr`` membership (logic and related names are disjoint, and the
    branch tuple reads ``related_obj`` / ``raw_value``, never ``spec``), so the
    ``RELATED`` half is byte-identical to ``active_related_branches``'s
    field-spec-less, logic-key-less config; the ``LEAF`` half matches
    ``active_permission_field_paths`` exactly. Both are kept as thin wrappers
    over this so the classification rule stays single-sited.
    """
    config = SetInputTraversal(
        field_specs=field_specs,
        related_attr=related_attr,
        logic_keys=logic_keys,
        unset_sentinel=unset_sentinel,
        handle_top_level_list=handle_top_level_list,
    )
    leaf_paths: list[str] = []
    branches: list[tuple[str, Any, Any]] = []
    for field in iter_active_fields(cls, input_value, config):
        if field.kind == LEAF:
            leaf_paths.append(
                field.spec.django_source_path
                if field.spec is not None
                else fallback_path(field.python_attr),
            )
        elif field.kind == RELATED:
            branches.append((field.python_attr, field.related_obj, field.raw_value))
    return leaf_paths, branches


def active_related_branches(
    cls: type,
    input_value: Any,
    *,
    related_attr: str,
    unset_sentinel: Any = None,
    handle_top_level_list: bool = False,
) -> list[tuple[str, Any, Any]]:
    """List ``(field_name, related_obj, child_input)`` for present related branches.

    Active-branch scoping: a related branch is "active" when its key is present
    in the input, regardless of the inner value's emptiness. Inactive branches
    are skipped end-to-end so an empty branch does not exercise the child's
    gates. ``related_attr`` names the per-class related-collection
    (``related_filters`` / ``related_orders``).

    ``handle_top_level_list`` (order side) walks each dataclass element of a
    top-level list separately so the parent gate fires once per active branch
    occurrence (the caller's ``_fired`` dedup collapses repeats per class).

    Consumes the shared ``iter_active_fields`` classifier (the 0.0.9 DRY pass,
    ``docs/feedback.md`` Major 1), keeping the ``RELATED`` records; the yield
    order is the input-iteration order rather than the declared-collection order,
    which is immaterial here (the per-class ``_fired`` dedup, the AND-commutative
    ``_apply_related_constraints`` narrowing, and the field-name-keyed visibility
    map are all order-independent).

    Thin wrapper over ``active_permission_targets`` (keeps the single-pass
    classification single-sited, feedback H3): ``RELATED`` records are
    independent of ``field_specs`` / ``logic_keys``, so the empty/identity values
    here yield the same branch tuples this always returned.
    """
    _leaf_paths, branches = active_permission_targets(
        cls,
        input_value,
        field_specs={},
        related_attr=related_attr,
        logic_keys=frozenset(),
        fallback_path=verbatim_path,
        unset_sentinel=unset_sentinel,
        handle_top_level_list=handle_top_level_list,
    )
    return branches


def active_permission_field_paths(
    cls: type,
    input_value: Any,
    *,
    field_specs: Mapping[Any, Any],
    related_attr: str,
    logic_keys: frozenset[str],
    fallback_path: Callable[[str], str],
    unset_sentinel: Any = None,
    handle_top_level_list: bool = False,
) -> list[str]:
    """Return the base Django source path for each active top-level field.

    Drives the per-field gate dispatch: one entry per supplied top-level LEAF
    field, keyed on its ``django_source_path`` (the lookup-free source field)
    from ``field_specs[(cls, python_attr)]`` so ``check_<field>_permission``
    fires once for a field no matter which lookups the consumer populated. Fields
    with no field-spec entry fall back to ``fallback_path(python_attr)`` (the
    filter side maps lookup attrs back to form keys; the order side uses the attr
    verbatim).

    Logical operators (``logic_keys`` -- filter ``and_`` / ``or_`` / ``not_``)
    and related branches (recognized off ``related_attr`` on ``cls``) are
    excluded -- the former are walked by the logical-branch recursion, the latter
    by the related-branch loop -- because the shared ``iter_active_fields``
    classifier marks them ``LOGIC`` / ``RELATED`` and only the ``LEAF`` records
    are kept. ``None`` / ``unset_sentinel`` values are skipped (active-input-only)
    and ``handle_top_level_list`` (order side) aggregates across the elements of
    a top-level list input -- both handled inside the classifier (the 0.0.9 DRY
    pass, ``docs/feedback.md`` Major 1).

    Thin wrapper over ``active_permission_targets`` (single-sited classification,
    feedback H3): returns only the ``LEAF`` half.
    """
    leaf_paths, _branches = active_permission_targets(
        cls,
        input_value,
        field_specs=field_specs,
        related_attr=related_attr,
        logic_keys=logic_keys,
        fallback_path=fallback_path,
        unset_sentinel=unset_sentinel,
        handle_top_level_list=handle_top_level_list,
    )
    return leaf_paths


def _fire_gate_on_class(
    gate_cls: type,
    field_path: str,
    request: Any,
    *,
    fired: dict[type, set[str]],
) -> None:
    """Fire ``check_<field_path>_permission`` on a fresh bare instance of ``gate_cls``.

    Deduped via the per-class set inside the shared ``fired`` map -- matching the
    ``object.__new__(cls)`` bare-instance contract the family
    ``_run_permission_checks`` already uses (the gate is a
    ``check_X_permission(self, request)`` method that needs no constructed set).
    """
    class_fired = fired.setdefault(gate_cls, set())
    invoke_permission_method(object.__new__(gate_cls), field_path, request, fired=class_fired)


def _fire_flat_relation_path_gates(
    owning_cls: type,
    source_path: str,
    request: Any,
    *,
    fired: dict[type, set[str]],
    related_attr: str,
    target_attr: str,
) -> None:
    """Fire the target-set gate chain a flat relation-traversal leaf would otherwise bypass.

    A generated flat leaf (``categoryName`` -> source path ``category__name``, or
    a deep ``entriesPropertyCategoryName`` -> ``entries__property__category__name``)
    constrains the SAME column as the equivalent nested branch
    (``category: {name: ...}``) but its owning-class gate name
    (``check_category_name_permission`` on the owner) never consults the TARGET
    filterset's ``check_name_permission``. Left alone, a client bypasses a target
    gate merely by spelling the predicate flat. This walks the flat path and fires
    the SAME gates the nested form fires: each parent relation branch gate plus the
    terminal target set's field gate. The owner's flat-path gate is fired
    separately by the caller and is preserved.

    Hops are resolved against each set's declared related collection
    (``related_filters`` / ``related_orders``) by matching a related object's
    ``field_name`` -- the ORM accessor, NOT its public attribute name -- so a
    renamed branch (``visible_shelves = RelatedFilter(ShelfFilter,
    field_name="shelves")``) still resolves; the branch gate fired is keyed on the
    PUBLIC attr so it matches the gate the nested form fires. If any relation hop
    has no matching declared related object, the walk stops without firing target
    gates: the owner's flat-path gate stays the authorization point and no target
    set is guessed. Dedup rides the shared per-class ``fired`` map, so a flat leaf
    and its nested twin fire each gate at most once per request.
    """
    hops = source_path.split(LOOKUP_SEP)
    if len(hops) < 2:
        # Not a relation traversal -- the owner's own field gate is authoritative.
        return
    current_cls = owning_cls
    last_index = len(hops) - 1
    for index, hop in enumerate(hops):
        if index == last_index:
            # Terminal scalar field on the deepest resolved target set -- fire its
            # field gate (the gate the nested form's child recursion fires).
            _fire_gate_on_class(current_cls, hop, request, fired=fired)
            return
        related = getattr(current_cls, related_attr, {}) or {}
        match = next(
            (
                (declared_attr, related_obj)
                for declared_attr, related_obj in related.items()
                if getattr(related_obj, "field_name", None) == hop
            ),
            None,
        )
        if match is None:
            # No declared RelatedFilter/RelatedOrder for this hop -- do not guess a
            # target set; the owner's flat-path gate (fired by the caller) stands.
            return
        declared_attr, related_obj = match
        # Parent relation branch gate on the current set, keyed on the PUBLIC attr
        # so it matches the ``check_<branch>_permission`` the nested form fires.
        _fire_gate_on_class(current_cls, declared_attr, request, fired=fired)
        child_set = getattr(related_obj, target_attr, None)
        if child_set is None:
            return
        current_cls = child_set


def run_active_input_permission_checks(
    cls: type,
    input_value: Any,
    request: Any,
    *,
    fired: dict[type, set[str]],
    bare: Any,
    target_attr: str,
    related_attr: str,
    depth: int = 0,
) -> None:
    """Fire the per-field and per-branch gates for one input level.

    The shared core of ``FilterSet`` / ``OrderSet`` ``_run_permission_checks``:
    it owns the per-class dedup set, the active-field gate loop, and the
    active-related-branch loop (recurse into the child set's own
    ``_run_permission_checks`` then fire the parent's per-branch gate). The
    family wrappers own the prologue (None / ``UNSET`` guard, depth cap, bare
    allocation) and -- filter only -- the logical ``and`` / ``or`` / ``not``
    recursion that re-enters with the same ``bare`` and shared ``fired`` map.

    ``depth`` is the shared traversal budget: it counts BOTH the logical and the
    related recursion (the family wrapper hands its own ``_depth`` in, and the
    related recursion below re-enters the child's ``_run_permission_checks`` with
    ``depth + 1``). A self-referential related branch would otherwise recurse
    input-deep and blow the stack; the cap converts that into a typed
    ``ConfigurationError`` at the source. The per-set cap is ``_MAX_LOGIC_DEPTH``
    when the set defines one (``FilterSet``) and ``_MAX_RELATED_RECURSION_DEPTH``
    otherwise (``OrderSet``), so both sides share one budget.

    ``target_attr`` names the attribute on each related object that resolves the
    child set (``filterset`` / ``orderset``); ``related_attr`` names each set's
    declared related collection (``related_filters`` / ``related_orders``). Both
    the child-set recursion and the parent branch gate live in DIFFERENT per-class
    dedup sets, so both fire once -- the intentional parent-vs-child double
    dispatch.

    Flat relation-traversal leaves are gated the same as their nested twins: for
    each active leaf whose source path crosses a relation (``category__name``),
    ``_fire_flat_relation_path_gates`` fires the target set's gate chain so a
    client cannot bypass a target gate by spelling the predicate flat.
    """
    class_fired = fired.setdefault(cls, set())

    # ONE active-input traversal yields both the per-field gate paths and the
    # related branches for this level (feedback H3); the two used to be separate
    # full walks of the same input. Gates key on the SOURCE FIELD (one fire per
    # field across all its lookups).
    field_paths, related_branches = cls._active_permission_targets(input_value)
    for field_path in field_paths:
        cls._invoke_permission_method(bare, field_path, request, fired=class_fired)
        # A flat relation-traversal leaf (``category__name``) must ALSO fire the
        # target set's gate chain its nested twin (``category: {name}``) fires, or
        # the flat spelling silently bypasses the target gate.
        _fire_flat_relation_path_gates(
            cls,
            field_path,
            request,
            fired=fired,
            related_attr=related_attr,
            target_attr=target_attr,
        )

    for field_name, related_obj, child_input in related_branches:
        child_set = getattr(related_obj, target_attr)
        if child_set is not None and hasattr(child_set, "_run_permission_checks"):
            # Child set is (usually) a different class; it keys its own per-class
            # set inside the shared ``fired`` map and allocates its own bare.
            # Thread the shared depth budget so a self-referential related branch
            # (``CardFilter.dependencies`` -> ``CardFilter``) is capped with a
            # typed error rather than recursing input-deep into a ``RecursionError``.
            next_depth = depth + 1
            cap = getattr(child_set, "_MAX_LOGIC_DEPTH", _MAX_RELATED_RECURSION_DEPTH)
            if next_depth > cap:
                label = getattr(child_set, "__qualname__", repr(child_set))
                raise ConfigurationError(
                    f"{label}: related-branch nesting exceeded the maximum traversal "
                    f"depth ({cap}). Flatten the related input or split into multiple "
                    "queries.",
                )
            child_set._run_permission_checks(
                child_input,
                request,
                _fired=fired,
                _depth=next_depth,
            )
        # Per-branch gate on the parent (e.g. ``check_shelves_permission`` when
        # the ``shelves`` branch is active), deduped against the parent's set.
        cls._invoke_permission_method(bare, field_name, request, fired=class_fired)
