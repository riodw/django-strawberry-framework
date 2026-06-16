"""Active-input permission traversal shared by the FilterSet and OrderSet families.

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

from django.http import HttpRequest

from ..exceptions import ConfigurationError
from .input_values import (
    LEAF,
    RELATED,
    SetInputTraversal,
    is_inactive_value,
    iter_active_fields,
    iter_input_items,
)


@lru_cache(maxsize=2048)
def _check_method_name(field_path: str) -> str:
    """Map a field path to its ``check_<field>_permission`` method name.

    The transform is request-independent (it depends only on the declared field
    path), so it is memoized over the bounded set of declared paths; only the
    bound-instance ``getattr`` / ``callable`` probe in
    ``invoke_permission_method`` stays per-request (feedback L5).
    """
    return f"check_{field_path.replace('__', '_')}_permission"


# ``iter_input_items`` is single-sited in ``utils/input_values.py`` (the 0.0.9
# DRY pass, ``docs/feedback.md`` Major 1). Re-exported here so the existing
# ``from ..utils.permissions import iter_input_items`` consumers (``filters/sets.py``,
# the permission test suite) keep their import path.
__all__ = [
    "active_permission_field_paths",
    "active_permission_targets",
    "active_related_branches",
    "extract_branch_value",
    "invoke_permission_method",
    "iter_input_items",
    "request_from_info",
    "run_active_input_permission_checks",
]


def request_from_info(info: Any, *, family_label: str) -> Any:
    """Resolve the Django request from ``info.context``.

    Canonical Strawberry-Django shape: ``info.context.request``. The
    wrapper-less alternative (``info.context`` *is* a bare ``HttpRequest`` -- the
    Django test-client default) is also accepted so consumers work without
    bespoke wiring. Any other shape raises ``ConfigurationError`` naming
    ``family_label`` (``FilterSet`` / ``OrderSet``) so the consumer sees which
    sidecar's ``apply`` failed.
    """
    context = getattr(info, "context", None)
    if context is None:
        raise ConfigurationError(
            f"{family_label}.apply requires `info.context`; received `info` without a context.",
        )
    request = getattr(context, "request", None)
    if request is not None:
        return request
    if isinstance(context, HttpRequest):
        return context
    raise ConfigurationError(
        f"{family_label}.apply could not resolve a Django HttpRequest from `info.context` "
        f"(got {type(context).__name__}). Expected `info.context.request` or a bare HttpRequest.",
    )


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
    ``not_`` arms off the raw input.
    """
    if input_value is None:
        return None
    if isinstance(input_value, dict):
        value = input_value.get(field_name)
    else:
        value = getattr(input_value, field_name, None)
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
    """
    method_name = _check_method_name(field_path)
    if fired is not None and method_name in fired:
        return
    method = getattr(bare_instance, method_name, None)
    if callable(method):
        method(request)
        if fired is not None:
            fired.add(method_name)


def _verbatim_path(python_attr: str) -> str:
    """Fallback path that returns the attr unchanged (the related-only callers)."""
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
        fallback_path=_verbatim_path,
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


def run_active_input_permission_checks(
    cls: type,
    input_value: Any,
    request: Any,
    *,
    fired: dict[type, set[str]],
    bare: Any,
    target_attr: str,
) -> None:
    """Fire the per-field and per-branch gates for one input level.

    The shared core of ``FilterSet`` / ``OrderSet`` ``_run_permission_checks``:
    it owns the per-class dedup set, the active-field gate loop, and the
    active-related-branch loop (recurse into the child set's own
    ``_run_permission_checks`` then fire the parent's per-branch gate). The
    family wrappers own the prologue (None / ``UNSET`` guard, depth cap, bare
    allocation) and -- filter only -- the logical ``and`` / ``or`` / ``not``
    recursion that re-enters with the same ``bare`` and shared ``fired`` map.

    ``target_attr`` names the attribute on each related object that resolves the
    child set (``filterset`` / ``orderset``). Both the child-set recursion and
    the parent branch gate live in DIFFERENT per-class dedup sets, so both fire
    once -- the intentional parent-vs-child double dispatch.
    """
    class_fired = fired.setdefault(cls, set())

    # ONE active-input traversal yields both the per-field gate paths and the
    # related branches for this level (feedback H3); the two used to be separate
    # full walks of the same input. Gates key on the SOURCE FIELD (one fire per
    # field across all its lookups).
    field_paths, related_branches = cls._active_permission_targets(input_value)
    for field_path in field_paths:
        cls._invoke_permission_method(bare, field_path, request, fired=class_fired)

    for field_name, related_obj, child_input in related_branches:
        child_set = getattr(related_obj, target_attr)
        if child_set is not None and hasattr(child_set, "_run_permission_checks"):
            # Child set is (usually) a different class; it keys its own per-class
            # set inside the shared ``fired`` map and allocates its own bare.
            child_set._run_permission_checks(child_input, request, _fired=fired)
        # Per-branch gate on the parent (e.g. ``check_shelves_permission`` when
        # the ``shelves`` branch is active), deduped against the parent's set.
        cls._invoke_permission_method(bare, field_name, request, fired=class_fired)
