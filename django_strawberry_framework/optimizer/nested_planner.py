"""Transactional planner for nested Relay connection selections.

The general walker normalizes selections and resolves model/type metadata, then
delegates one recognized nested connection here. This component owns pagination
normalization, fallback classification, child-queryset construction, fetch
strategy dispatch, and acceptance bookkeeping. It builds a private result plan
and returns it only after orchestration completes, so refusal or an exception
cannot leak partial directives into the walker's parent plan.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from django.db import models
from graphql import GraphQLError

from ..keyset import (
    KeysetSeek,
    cursor_columns_for,
    decode_keyset_cursor,
    order_fingerprint,
)
from ..utils.connections import (
    UnwindowableConnection,
    derive_connection_window_bounds,
    derive_keyset_window_bounds,
    has_connection_sidecar_kwargs,
    window_range_plan,
)
from ..utils.relations import instance_accessor
from ..utils.typing import schema_config_from_info
from . import logger
from .hints import hint_is_skip
from .join_taxonomy import classify_relation_join
from .nested_fetch import (
    NestedConnectionRequest,
    active_strategy,
    unwindowable_child_queryset_reason,
)
from .plans import (
    OptimizationPlan,
    append_unique,
    append_unique_many,
    deferred_loading_of,
    deterministic_order,
    order_entry_name_and_direction,
)
from .selections import (
    connection_has_next_page_selected,
    connection_total_count_selected,
)
from .selections import (
    named_children as _named_children,
)
from .selections import (
    node_children_with_runtime_prefix as _node_children_with_runtime_prefix,
)
from .selections import (
    response_key as _response_key,
)
from .selections import (
    response_keys as _response_keys,
)


@dataclass(frozen=True)
class NestedConnectionPlanResult:
    """An isolated nested-connection plan and the windows a strategy accepted."""

    plan: OptimizationPlan
    accepted_response_keys: tuple[str | None, ...] = ()

    @property
    def accepted(self) -> bool:
        """Return whether at least one fetch window was accepted."""
        return bool(self.accepted_response_keys)


def _connector_only_field(parent_field: Any) -> str | None:
    """Return the column Django needs to attach prefetched rows to parents.

    The relation-kind-specific connector: the child FK attname for a reverse FK /
    reverse one-to-one, the target field's attname for a forward single-valued
    relation, and the related model's pk attname for an M2M (the join table owns
    the attach, so the child only needs its pk). Returns ``None`` when no column
    resolves. Shared by ``_ensure_connector_only_fields`` (the list-prefetch
    projection) and the scalar-only connection-window projection.

    A thin shim over ``optimizer/join_taxonomy.py::classify_relation_join``
    (which carries the moved-verbatim connector derivation as
    ``parent_join_column``), kept under the historical name for its two
    callers and the direct test-double pins.
    """
    return classify_relation_join(parent_field).parent_join_column


def _order_entry_field_name(entry: Any) -> str | None:
    """Return the field name an ``order_by`` entry references, or ``None``.

    A thin shim over the shared entry parser
    (``plans.py::order_entry_name_and_direction`` - one dash rule, one
    expression unwrap for every consumer of the ``deterministic_order``
    entry vocabulary), kept under the historical name for its caller and
    test pins; this projection needs only the name half.
    """
    parsed = order_entry_name_and_direction(entry)
    return parsed[0] if parsed is not None else None


def _concrete_order_columns(order_by: Sequence[Any], model: type[models.Model]) -> list[str]:
    """Return the LOCAL concrete column attnames referenced by ``order_by``.

    Related-span lookups (``author__name``) and unresolvable expressions are
    skipped: the window's ``OVER (ORDER BY ...)`` and the queryset ``ORDER BY``
    reference those columns in SQL regardless of the ``.only()`` projection, so a
    skipped column only forgoes loading an attribute a scalar-only selection
    never reads. Used to keep the scalar-only window projection minimal yet
    order-complete (spec-033 Decision 4 scalar-only bullet: the
    "pk/connector/order-only child projection").
    """
    by_name = {field.name: field.attname for field in model._meta.concrete_fields}
    attnames = set(by_name.values())
    columns: list[str] = []
    for entry in order_by:
        name = _order_entry_field_name(entry)
        if name is None or "__" in name:
            continue
        if name in by_name:
            append_unique(columns, by_name[name])
        elif name in attnames:
            append_unique(columns, name)
    return columns


def _project_scalar_only_window(
    child_queryset: Any,
    django_field: Any,
    order_by: Sequence[Any],
    *,
    enable_only: bool = True,
) -> Any:
    """Restrict a scalar-only connection window to pk / connector / order columns.

    A ``pageInfo``-only or ``totalCount``-only selection unwraps to ``[]`` node
    children, so the child plan adds no ``.only()`` and the window would fetch
    full model rows even though the page needs only the target pk (Relay edge
    identity), the relation connector column (Django's prefetch attach), and the
    concrete ordering columns the deterministic window order references
    (spec-033 Decision 4 / Decision 6 scalar-only contract). The ``_dst_*`` window annotations
    compose with ``.only()`` (annotations, not deferred columns).

    The G2 gate (spec-035 Decision 4): under a non-``QUERY`` operation this
    direct ``.only(...)`` is the projection-writer that never touches
    ``OptimizationPlan.only_fields``, so it must consult the gate itself -
    when closed it returns the child queryset unchanged (no column mask) and
    the window annotations are applied afterwards in ``_plan_connection_relation``.
    """
    if not enable_only:
        return child_queryset
    related_model = django_field.related_model
    fields: list[str] = []
    append_unique(fields, related_model._meta.pk.attname)
    connector = _connector_only_field(django_field)
    if connector is not None:
        append_unique(fields, connector)
    for column in _concrete_order_columns(order_by, related_model):
        append_unique(fields, column)
    return child_queryset.only(*fields)


def _extend_only_projection(child_queryset: Any, attnames: tuple[str, ...]) -> Any:
    """Ensure ``attnames`` load under an existing ``.only()`` / ``.defer()`` projection.

    The keyset cursor-column loader: a keyset page mints edge cursors from
    the rows' ordering-column VALUES, so those columns must survive the
    ``.only()`` mask even when the query never selects them as GraphQL
    fields. Django's ``.only()`` chaining REPLACES the load-only set, so the
    extension re-applies the UNION read through the shared
    ``deferred_loading_of`` unpack. A ``.defer()`` mask needs the inverse:
    clear it, then re-apply every deferred field EXCEPT the cursor columns.
    Otherwise cursor minting lazy-loads once per edge in sync execution and
    raises ``SynchronousOnlyOperation`` in async execution.
    """
    loading = deferred_loading_of(child_queryset)
    if loading is None:
        return child_queryset
    names, defer_flag = loading
    if defer_flag:
        remaining = sorted(set(names) - set(attnames))
        if len(remaining) == len(names):
            return child_queryset
        cleared = child_queryset.defer(None)
        return cleared.defer(*remaining) if remaining else cleared
    if not names:
        return child_queryset
    missing = [attname for attname in attnames if attname not in names]
    if not missing:
        return child_queryset
    return child_queryset.only(*names, *missing)


def _relation_connection_to_attr(relation_field_name: str) -> str:
    """Return the package-reserved ``to_attr`` for a relation connection window.

    ``_dst_<field>_connection``, keyed on the relation FIELD NAME (not the
    accessor). The single source for this literal across the walker (plan
    site), the finalizer (resolver precompute, Slice 2), and the connection
    resolver probe (Slice 2), so the ``_dst_`` namespace string is never
    duplicated as a scattered f-string (Decision 4 / Decision 5).
    """
    return f"_dst_{relation_field_name}_connection"


def _relation_connection_to_attr_for_key(relation_field_name: str, response_key: str) -> str:
    """Return the per-RESPONSE-KEY ``to_attr`` for a divergent-alias window.

    ``_dst_<field>$<key>_connection`` - the namespaced twin of
    ``_relation_connection_to_attr`` used when aliases of one relation carry
    DIVERGENT argument payloads and each response key gets its own windowed
    prefetch (one ``Prefetch`` per key on the same lookup; Django's
    ``prefetch_to`` is ``to_attr``-aware, so they coexist).

    The ``$`` delimiter (graph-node's ``g$parent_id`` move) is load-bearing
    twice over. Collision-safety: ``$`` is illegal in BOTH vocabularies
    (Django field names must be Python identifiers; GraphQL response keys
    match ``[_A-Za-z][_0-9A-Za-z]*``), so the first ``$`` unambiguously ends
    the field name - no ``(field, key)`` pair can alias another or the shared
    attr - and graphql-core's field-merging validation forbids one response
    key carrying two different argument payloads. Django-safety: a ``to_attr``
    must not contain ``__`` anywhere (``prefetch_to`` is split on
    ``LOOKUP_SEP`` to traverse prefetch levels; an embedded ``__`` silently
    breaks the descent), and a response key MAY contain ``__``/trailing
    ``_``, so every ``_`` in the key is escaped to ``$`` - injective, since
    ``$`` cannot occur in a raw key. ``setattr``/``getattr`` accept the
    non-identifier attr just fine (the ``_dst_`` namespace is
    package-reserved either way). The single source for the per-key namespace
    string shared with the resolve-side probe
    (``connection.py::_build_relation_connection_resolver``).
    """
    return f"_dst_{relation_field_name}${response_key.replace('_', '$')}_connection"


def _connection_node_selections(sel: Any, runtime_paths: tuple[tuple[str, ...], ...]) -> list[Any]:
    """Unwrap a nested connection's ``edges { node { ... } }`` child selections.

    Reuses the consolidated ``edges { node }`` helpers (Decision 9) so the
    nested-connection unwrap matches the root seam's fragment-aware,
    directive-aware, runtime-prefix-carrying semantics. Returns the node-level
    child selections carrying the connection-aware runtime prefixes; an empty
    list for a scalar-only (``pageInfo`` / ``totalCount``) selection with no
    ``edges { node }`` - those are still PLANNED with a connector/ordering-only
    projection (Decision 6), not a fallback.
    """
    node_children: list[Any] = []
    for edge_selection in _named_children(sel, "edges"):
        edge_path_prefixes = tuple((*rp, _response_key(edge_selection)) for rp in runtime_paths)
        for node_selection in _named_children(edge_selection, "node"):
            node_path_prefixes = tuple(
                (*ep, _response_key(node_selection)) for ep in edge_path_prefixes
            )
            node_children.extend(
                _node_children_with_runtime_prefix(
                    node_selection,
                    runtime_prefixes=node_path_prefixes,
                ),
            )
    return node_children


def _relay_max_results_from_info(info: Any) -> int | None:
    """Resolve ``relay_max_results`` from the planner's graphql-core ``info``.

    The walker runs at the optimizer extension's middleware layer, where ``info``
    is the raw graphql-core ``GraphQLResolveInfo`` whose ``.schema`` is a bare
    ``GraphQLSchema`` with NO ``.config`` (unlike the resolve-time Strawberry
    ``Info`` ``SliceMetadata.from_arguments`` expects). The config dig lives in
    ``utils/typing.py::schema_config_from_info`` (shared with the walker's name
    converter and ``resolve_relay_max_results``) so this helper never
    dereferences ``info.schema.config`` itself. Returns ``None`` when no config
    is reachable so the engine default applies downstream - deliberately distinct
    from ``resolve_relay_max_results``'s terminal ``100``.
    """
    return getattr(schema_config_from_info(info), "relay_max_results", None)


def _coerce_pagination_int(value: Any) -> Any:
    """Coerce a pagination ``first`` / ``last`` argument to ``int`` when int-like.

    An inline Int literal arrives as the raw token string; a resolved variable is
    already an ``int``. Coerce an ``int``-castable string to ``int`` so the slice
    arithmetic fires; pass ``None`` and anything non-int-castable through
    untouched so ``SliceMetadata.from_arguments`` reaches its own
    ``isinstance(..., int)`` gate (skipping the bound, the shipped behavior for a
    malformed value) rather than the walker pre-judging it.
    """
    if value is None or isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _connection_window_slice(sel: Any, info: Any) -> tuple[int, int | None, bool] | None:
    """Resolve the window ``(offset, limit, reverse)`` from a connection selection.

    The planner-side adapter over the shared
    ``utils/connections.py::derive_connection_window_bounds`` contract (so the
    plan-time and resolve-time windows can never drift): it reads the RESOLVED
    ``first`` / ``last`` / ``before`` / ``after`` values off ``sel.arguments``
    (converted selections already resolved variable references through
    ``info.variable_values``), applies the walker-only int coercion, resolves
    ``max_results`` from the Strawberry schema config via
    ``_relay_max_results_from_info`` (the walker's graphql-core ``info.schema``
    has no ``.config`` the engine could read), and hands those to the shared
    helper, which owns the ``reverse`` / ``limit`` rule.

    Returns ``None`` when the shared helper raises ``ValueError`` (negative /
    over-max ``first`` / ``last``) or ``TypeError`` (malformed cursor) so
    ``plan_connection_relation`` leaves the selection UNPLANNED and the shipped
    nested field path raises at its own error locality (Decision 4 step f). The
    resolver calls the same helper directly with already-coerced Strawberry
    arguments and lets the pagination error propagate instead.

    ``UnwindowableConnection`` (an offset-bearing backward or inverted interval)
    is deliberately NOT caught here: it is a VALID query that resolves correctly
    per-parent, so ``plan_connection_relation`` must treat it as a fully-unplanned
    Decision-6 fallback (no ``planned_resolver_keys`` entry, like the sidecar /
    distinct shapes) rather than the malformed-pagination ``None`` path that
    records the field as accounted-for (spec-033 Decision 5).
    """
    return _connection_window_slice_from_arguments(
        getattr(sel, "arguments", None) or {},
        info,
    )


def _connection_window_slice_from_arguments(
    arguments: dict[str, Any],
    info: Any,
) -> tuple[int, int | None, bool] | None:
    """``_connection_window_slice`` over one raw argument payload.

    The per-payload entry point the divergent-alias scheme iterates: each
    response key's recorded argument payload
    (``_optimizer_response_key_arguments``) resolves its OWN window through
    the same shared-contract adapter, so per-key windows can never drift from
    the merged-selection window the single-window scheme derives. Same
    coercion, same error contract (``None`` on malformed pagination;
    ``UnwindowableConnection`` propagates).
    """
    # ``first`` / ``last`` from an inline GraphQL Int LITERAL arrive as the raw
    # token STRING (``convert_value`` returns ``node.value`` and graphql-core
    # stores an ``IntValueNode.value`` as ``"2"``); a variable
    # (``first: $n``) is already coerced to ``int`` by the engine. Coerce to int
    # so the shared helper's ``SliceMetadata.from_arguments`` - which gates the
    # slice on ``isinstance(first, int)`` - applies the window bound instead of
    # silently leaving the page uncapped at ``relay_max_results`` (the
    # literal-vs-variable divergence the resolve-time ``ConnectionExtension``
    # argument coercion hides at the field boundary). This coercion is
    # plan-time-only and deliberately NOT folded into the shared helper, whose
    # resolver caller already receives ``int`` arguments from Strawberry.
    first = _coerce_pagination_int(arguments.get("first"))
    last = _coerce_pagination_int(arguments.get("last"))
    try:
        bounds = derive_connection_window_bounds(
            info,
            before=arguments.get("before"),
            after=arguments.get("after"),
            first=first,
            last=last,
            max_results=_relay_max_results_from_info(info),
        )
    except (ValueError, TypeError):
        return None
    return bounds.offset, bounds.limit, bounds.reverse


def _keyset_cursor_context(
    target_type: type | None,
) -> tuple[tuple[Any, ...], str] | None:
    """Resolve a relation target's keyset context: ``(cursor columns, fingerprint)``.

    ``None`` when the target type is absent or does not declare
    ``Meta.cursor_field`` - the offset-window vocabulary applies. For a
    keyset target the connection's effective order IS the declared
    ``cursor_field`` (the BACKLOG "enforced matching order" contract), so
    the fingerprint every nested cursor embeds is derived from it directly.
    """
    definition = getattr(target_type, "__django_strawberry_definition__", None)
    cursor_field = getattr(definition, "cursor_field", None)
    if cursor_field is None:
        return None
    return (cursor_columns_for(definition.model, cursor_field), order_fingerprint(cursor_field))


def _keyset_window_slice_from_arguments(
    arguments: dict[str, Any],
    info: Any,
    *,
    columns: tuple[Any, ...],
    fingerprint: str,
) -> tuple[tuple[int, int | None, bool], KeysetSeek | None] | None:
    """Resolve one keyset window ``((offset, limit, reverse), seek)`` per payload.

    The keyset twin of ``_connection_window_slice_from_arguments``, forking
    BEFORE the offset engine (``SliceMetadata`` cannot parse a value cursor):
    bounds come from the shared ``derive_keyset_window_bounds`` (the same
    helper the resolve side consumes, so the two windows agree by
    construction) and the ``after:`` cursor decodes through the canonical
    codec. Error contract mirrors the offset adapter:

    - ``None`` for malformed pagination - a negative / over-cap ``first``
      (``ValueError``) or an invalid / tampered / wrong-order cursor (the
      codec's ``GraphQLError``). The caller records the field as
      accounted-for and the per-parent pipeline raises the SAME error at
      the field's own locality.
    - ``UnwindowableConnection`` propagates for the valid backward shapes
      (``last`` / ``before:``) the v1 keyset window does not plan - a real
      per-parent access that must stay strictness-visible.
    """
    first = _coerce_pagination_int(arguments.get("first"))
    last = _coerce_pagination_int(arguments.get("last"))
    after = arguments.get("after")
    before = arguments.get("before")
    seek: KeysetSeek | None = None
    try:
        # Validate both cursors before classifying a valid backward shape as
        # unwindowable. Otherwise strictness can mask malformed ``before:``
        # (or ``after:`` + ``last``) input as an unplanned N+1.
        if after is not None:
            cursor = decode_keyset_cursor(
                after,
                columns,
                fingerprint=fingerprint,
                argument="after",
            )
            seek = KeysetSeek(columns=columns, cursor=cursor)
        if before is not None:
            decode_keyset_cursor(
                before,
                columns,
                fingerprint=fingerprint,
                argument="before",
            )
        bounds = derive_keyset_window_bounds(
            info,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=_relay_max_results_from_info(info),
        )
    except (GraphQLError, ValueError, TypeError):
        return None
    return (bounds.offset, bounds.limit, bounds.reverse), seek


def _divergent_key_windows(
    sel: Any,
    info: Any,
    keyset_context: tuple[tuple[Any, ...], str] | None = None,
) -> tuple[
    list[tuple[str, tuple[int, int | None, bool], KeysetSeek | None]],
    list[str],
    list[tuple[str, str]],
]:
    """Resolve one window per response key for a divergent-alias connection.

    The divergent scheme's pure window pass: iterate the merged selection's
    per-response-key argument payloads (``_optimizer_response_key_arguments``)
    and run the ARGUMENTS-DERIVED fallback gates per key - each alias is its
    own windowed fetch (the graph-node model: one batched children query per
    response key), so one alias's fallback shape must not drag its siblings
    per-parent:

    - sidecar input (``filter:`` / ``orderBy:``) -> that key stays UNPLANNED
      (per-parent, strictness-visible), siblings unaffected;
    - ``UnwindowableConnection`` (``after`` + ``last``; inverted offset interval;
      every backward keyset shape) and the reversed ``last: 0`` quirk -> likewise
      that key alone falls back per-parent;
    - malformed pagination -> that key is returned in ``malformed`` so the
      caller records ONLY its identities (per-key error locality: the
      per-parent pipeline raises that alias's own validation error);
    - otherwise the key's ``(offset, limit, reverse)`` window joins
      ``planned``.

    ``keyset_context`` routes every key through the keyset window adapter
    instead (each alias decodes its OWN ``after:`` cursor into its own
    seek); the entry shape gains that seek (``None`` under the offset
    vocabulary and for keyset first pages alike).

    Returns ``(planned, malformed, fallbacks)``; each fallback carries its
    stable reason for the caller's debug log. Relation-level gates (hint
    SKIP, join windowability, child-queryset safety) stay whole-relation in
    ``_plan_connection_relation``.
    """
    planned: list[tuple[str, tuple[int, int | None, bool], KeysetSeek | None]] = []
    malformed: list[str] = []
    fallbacks: list[tuple[str, str]] = []
    for resp_key, key_arguments in sel._optimizer_response_key_arguments.items():
        if has_connection_sidecar_kwargs(key_arguments):
            fallbacks.append((resp_key, "sidecar arguments"))
            continue
        seek: KeysetSeek | None = None
        try:
            if keyset_context is not None:
                columns, fingerprint = keyset_context
                keyed = _keyset_window_slice_from_arguments(
                    key_arguments,
                    info,
                    columns=columns,
                    fingerprint=fingerprint,
                )
                window = keyed[0] if keyed is not None else None
                seek = keyed[1] if keyed is not None else None
            else:
                window = _connection_window_slice_from_arguments(key_arguments, info)
        except UnwindowableConnection:
            fallbacks.append((resp_key, "unsupported pagination window"))
            continue
        if window is None:
            malformed.append(resp_key)
            continue
        _offset, limit, reverse = window
        if reverse and limit == 0:
            fallbacks.append((resp_key, "last: 0"))
            continue
        planned.append((resp_key, window, seek))
    return planned, malformed, fallbacks


def _log_connection_fallback(
    relation_field_name: str,
    response_keys: Sequence[str],
    reason: str,
) -> None:
    """Log each response key that will use the per-parent connection pipeline."""
    for resp_key in dict.fromkeys(response_keys):
        logger.debug(
            "Optimizer: nested connection %s response key %r falls back "
            "to per-parent resolution (%s).",
            relation_field_name,
            resp_key,
            reason,
        )


def _identities_for_response_keys(
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    response_keys: list[str | None],
) -> tuple[str, ...]:
    """Filter parallel ``(runtime_paths, resolver_identities)`` to given keys.

    ``_resolver_identities_for`` already builds identities per response key
    (the cartesian ``runtime_prefixes x _response_keys(sel)``; each runtime
    path ENDS in its response key), so per-key selection is a filter over the
    parallel tuples, never a re-derivation. Used by the divergent-alias scheme
    to record identities only for the keys actually planned (or, for
    malformed keys, accounted-for).
    """
    wanted = set(response_keys)
    return tuple(
        identity
        for runtime_path, identity in zip(runtime_paths, resolver_identities, strict=True)
        if runtime_path[-1] in wanted
    )


def _raw_relation_field(model: type[models.Model], relation_field_name: str) -> Any:
    """Return the raw Django relation field for ``relation_field_name`` on ``model``.

    The window partition derivation needs the raw descriptor's
    ``remote_field`` (the forward-M2M reverse query name lives only there and is
    not carried on ``FieldMeta``); ``field_map`` holds ``FieldMeta``, so resolve
    the live field from ``_meta`` (spec-033 Decision 4 partition derivation).
    """
    return model._meta.get_field(relation_field_name)


def plan_connection_relation(
    sel: Any,
    definition: Any,
    *,
    relation_field_name: str,
    field_map: dict[str, Any],
    prefix: str,
    info: Any | None,
    runtime_prefixes: tuple[tuple[str, ...], ...],
    type_cls: type | None,
    model: type[models.Model],
    enable_only: bool = True,
    resolve_optimizer_hints: Callable[[Any], dict[str, Any]],
    resolve_relation_target: Callable[[Any, str, Any], type | None],
    response_key_arguments_conflict: Callable[[Any], bool],
    aliased_arguments_diverge: Callable[[Any], bool],
    target_has_custom_get_queryset: Callable[[type | None], bool],
    resolver_identities_for: Callable[..., tuple[tuple[tuple[str, ...], ...], tuple[str, ...]]],
    build_child_queryset: Callable[..., Any],
    build_prefetch_child_queryset_from_base: Callable[..., Any],
) -> NestedConnectionPlanResult:
    """Plan one recognized nested connection as a windowed ``Prefetch``.

    Orchestrates the windowed-prefetch plan (spec-033 Decision 4); leaves the
    selection UNPLANNED (no ``Prefetch``, no ``planned_resolver_keys`` entry) for
    each Decision-6 fallback shape so Slice 4's strictness contract still sees
    the per-parent access. Delegates child-queryset construction to the same
    helpers the list path uses (``_build_prefetch_child_queryset`` /
    ``_build_child_queryset``); the only addition is the window applied after
    ``child_plan.apply``.
    """
    plan = OptimizationPlan()
    django_field = field_map.get(relation_field_name)
    if django_field is None:
        return NestedConnectionPlanResult(plan=plan)
    # (b) Fallback shapes detectable before any queryset is built -> UNPLANNED.
    if response_key_arguments_conflict(sel):
        _log_connection_fallback(
            relation_field_name,
            _response_keys(sel),
            "conflicting arguments for one response key",
        )
        # ONE response key carries two different argument payloads - reachable
        # only when different parent-alias subtrees were union-merged (their
        # same-named children land in one merged selection). Neither scheme
        # can serve it: the shared window has one payload slot, and the
        # per-key scheme routes by response key, which is the very thing that
        # collides. Stay FULLY unplanned (no window, no resolver identities)
        # so each alias subtree's per-parent resolution applies its OWN
        # arguments and the access stays strictness-visible, like the sidecar
        # shapes. A silent first-payload-wins window here served the sibling
        # alias a wrong page (idea-#2 review P0).
        return NestedConnectionPlanResult(plan=plan)
    # Divergent aliased arguments select the PER-KEY scheme (one window per
    # response key, idea #2); its arguments-derived gates - the sidecar check
    # included - run per key inside ``_divergent_key_windows``, so the merged
    # primary-payload sidecar gate below applies only to the single-window
    # scheme (where every alias shares one payload by definition).
    arguments = getattr(sel, "arguments", None) or {}
    divergent = aliased_arguments_diverge(sel)
    if not divergent and has_connection_sidecar_kwargs(arguments):
        _log_connection_fallback(
            relation_field_name,
            _response_keys(sel),
            "sidecar arguments",
        )
        return NestedConnectionPlanResult(plan=plan)
    hints_map = resolve_optimizer_hints(definition)
    if hint_is_skip(hints_map.get(relation_field_name)):
        return NestedConnectionPlanResult(plan=plan)

    target_type = resolve_relation_target(definition, relation_field_name, django_field)
    has_custom_get_queryset = target_has_custom_get_queryset(target_type)

    runtime_paths, resolver_identities = resolver_identities_for(
        sel,
        relation_field_name,
        type_cls,
        runtime_prefixes,
    )

    if django_field.related_model is None:
        return NestedConnectionPlanResult(plan=plan)

    # Keyset context (the ``cursor_field`` opt-in): when the relation target
    # is keyset-mode, every window below derives through the keyset adapter
    # (value-cursor decode + forward-only bounds) instead of the offset
    # engine, and the connection order is the DECLARED ``cursor_field``
    # rather than the child queryset / model ``Meta.ordering`` (the BACKLOG
    # "enforced matching order" contract - the cursor columns ARE the order).
    keyset_context = _keyset_cursor_context(target_type)

    # (e/f) Slice window(s) from the selection's resolved pagination arguments.
    # Pure (mutates nothing), so resolve BEFORE the child build - a malformed
    # slice must not leave child resolver keys / cacheable flips on the parent
    # plan. ``keyed_windows`` is the scheme-agnostic hand-off: the divergent
    # scheme yields one ``(response_key, window, seek)`` per plannable alias
    # (each gets its own per-key ``to_attr``); the single-window scheme yields
    # one ``(None, window, seek)`` entry (the legacy shared ``to_attr``,
    # byte-identical to the pre-idea-#2 path by construction). ``seek`` is the
    # decoded keyset value seek, ``None`` under the offset vocabulary and for
    # keyset first pages alike.
    keyed_windows: list[tuple[str | None, tuple[int, int | None, bool], Any]]
    if divergent:
        planned_windows, malformed_keys, fallback_keys = _divergent_key_windows(
            sel,
            info,
            keyset_context,
        )
        keyed_windows = list(planned_windows)
        for fallback_key, reason in fallback_keys:
            _log_connection_fallback(relation_field_name, [fallback_key], reason)
        if malformed_keys:
            _log_connection_fallback(
                relation_field_name,
                malformed_keys,
                "malformed pagination",
            )
            # Malformed pagination, per key (Decision 4 step f): that alias
            # resolves per-parent and raises its OWN cursor/pagination
            # validation error, so record ONLY its identities as accounted-for
            # (strictness must not preempt the error under ``"raise"``;
            # spec-033 Decision 8). Sibling keys plan independently below.
            append_unique_many(
                plan.planned_resolver_keys,
                _identities_for_response_keys(
                    runtime_paths,
                    resolver_identities,
                    malformed_keys,
                ),
            )
        if not keyed_windows:
            return NestedConnectionPlanResult(plan=plan)
    else:
        try:
            if keyset_context is not None:
                columns, fingerprint = keyset_context
                keyed = _keyset_window_slice_from_arguments(
                    arguments,
                    info,
                    columns=columns,
                    fingerprint=fingerprint,
                )
                window = keyed[0] if keyed is not None else None
                seek = keyed[1] if keyed is not None else None
            else:
                window = _connection_window_slice(sel, info)
                seek = None
        except UnwindowableConnection:
            _log_connection_fallback(
                relation_field_name,
                _response_keys(sel),
                "unsupported pagination window",
            )
            # (b) A valid offset interval the SQL window cannot represent
            # (``after`` + ``last`` or inverted ``after`` + ``before``) - and,
            # for a keyset target, EVERY backward shape (``last`` / ``before:``;
            # the v1 keyset window is forward-only). Fall back per-parent like
            # the other Decision-6 shapes (sidecar, distinct). Stay FULLY
            # unplanned so the per-parent access remains strictness-visible;
            # unlike malformed pagination, this query resolves normally there.
            return NestedConnectionPlanResult(plan=plan)
        if window is None:
            _log_connection_fallback(
                relation_field_name,
                _response_keys(sel),
                "malformed pagination",
            )
            # Malformed pagination (Decision 4 step f): emit NO window prefetch so the
            # connection pipeline runs per-parent and raises its OWN cursor/pagination
            # validation error at the field. But RECORD the resolver identities so the
            # Slice-4 strictness contract treats the field as accounted-for and does
            # NOT preempt that error with a spurious "Unplanned N+1" OptimizerError
            # under `"raise"` (spec-033 Decision 8 - error locality wins here). The
            # other Decision-6 fallback shapes (sidecar, hint SKIP,
            # distinct, unwindowable partition) stay fully unplanned on purpose so
            # strictness CAN see them as real per-parent accesses. A keyset
            # target reaches this path for an invalid / tampered / wrong-order
            # cursor too - the codec raises the SAME GraphQLError per-parent.
            append_unique_many(plan.planned_resolver_keys, resolver_identities)
            return NestedConnectionPlanResult(plan=plan)
        offset, limit, reverse = window
        if reverse and limit == 0:
            _log_connection_fallback(
                relation_field_name,
                _response_keys(sel),
                "last: 0",
            )
            # (b) ``last: 0``: upstream ``ListConnection`` slices ``edges[-0:]``,
            # which is the WHOLE list - only the per-parent pipeline reproduces
            # that quirk, so a planned reversed window would always come back
            # empty and be discarded by ``_resolve_from_window``'s fallback
            # return. Plan nothing (feedback2 P0-3 follow-through): no dead
            # window query riding every request, and no resolver keys - the
            # per-parent fallback stays strictness-visible like the other
            # Decision-6 fallback shapes. ``_resolve_from_window`` keeps its own
            # ``last: 0`` guard as the defensive tail for direct callers.
            return NestedConnectionPlanResult(plan=plan)
        keyed_windows = [(None, window, seek)]

    # (g, partition) also pure; classify the join before the child build so an
    # unsupported relation kind (single-valued forward, or a shape with no
    # resolvable parent partition) falls back without leaking child metadata.
    # The RAW field (not the ``FieldMeta``) also rides the strategy request:
    # the lateral backend reads ``remote_field`` / through metadata that only
    # the raw descriptor carries.
    raw_relation_field = _raw_relation_field(model, relation_field_name)
    join = classify_relation_join(raw_relation_field)
    if not join.windowable:
        return NestedConnectionPlanResult(plan=plan)

    # (a) Unwrap edges { node }; scalar-only selections plan with [] node children.
    # ``runtime_paths`` spans ALL response keys (per-key child selections are
    # not preserved by the merge), so under the divergent scheme the child
    # plan records nested identities under an UNPLANNED sibling key's paths
    # too. Deliberate conservatism: that sibling's per-parent pipeline plans
    # its own subtree, so those nested accesses never lazy-load - the
    # imprecision can only mask a strictness flag, never serve wrong data.
    node_selections = _connection_node_selections(sel, runtime_paths)
    scalar_only = not node_selections
    node_sel = SimpleNamespace(selections=node_selections)

    # (c, pre-build safety gate) the base child queryset comes from consumer
    # code even without a target ``get_queryset``: a custom default manager's
    # ``.all()`` can still return distinct/sliced/combined/values/locking
    # shapes no fetch strategy can window. Build that base exactly once,
    # classify it unconditionally, and feed the same value into child-plan
    # application on the success path.
    base_queryset = build_child_queryset(
        django_field,
        target_type,
        info,
        has_custom_qs=has_custom_get_queryset,
    )
    if unwindowable_child_queryset_reason(base_queryset) is not None:
        return NestedConnectionPlanResult(plan=plan)

    # (c) Build the child plan/queryset exactly like the list prefetch path, but
    # against a THROWAWAY sub-plan so a strategy refusal below can fall back
    # without leaking the child's resolver keys / fk-id elisions / cacheable flip
    # into the parent (Decision 6 / DoD-4 "no planned_resolver_keys entry"). The
    # parent plan absorbs the child metadata only on the success path.
    sub_plan = OptimizationPlan()
    if has_custom_get_queryset:
        sub_plan.cacheable = False
    child_queryset = build_prefetch_child_queryset_from_base(
        node_sel,
        django_field,
        sub_plan,
        info,
        runtime_paths,
        base_queryset=base_queryset,
        enable_only=enable_only,
    )
    # No post-build re-check: the classified base queryset is the single
    # strategy-independent gate; later child-plan application only adds the
    # package's optimizer directives.

    # (d) Deterministic total order shared with the resolve-time pipeline. A
    # keyset target's connection order IS its declared ``cursor_field`` (the
    # unique-terminal contract is finalization-validated, so
    # ``deterministic_order`` returns it unchanged); everything else keeps
    # the child-queryset / model ``Meta.ordering`` derivation.
    if keyset_context is not None:
        effective = target_type.__django_strawberry_definition__.cursor_field
    else:
        effective = tuple(child_queryset.query.order_by) or tuple(
            django_field.related_model._meta.ordering,
        )
    order_by = list(deterministic_order(effective, django_field.related_model))

    # A scalar-only (pageInfo/totalCount) selection unwrapped to [] node children,
    # so the child plan added no `.only()` projection; restrict it to the minimal
    # pk/connector/order columns now that the deterministic order is known
    # (spec-033 Decision 4 / Decision 6 scalar-only contract) rather than fetching full child rows.
    if scalar_only:
        child_queryset = _project_scalar_only_window(
            child_queryset,
            django_field,
            order_by,
            enable_only=enable_only,
        )
    elif keyset_context is not None:
        # Keyset edges mint cursors from the rows' ORDERING-COLUMN VALUES
        # (not the row-number annotation), so the cursor columns must be
        # loaded on every page row - extend a node-selection ``.only()``
        # projection that did not select them as GraphQL fields (the
        # scalar-only branch above already carries its order columns).
        child_queryset = _extend_only_projection(
            child_queryset,
            tuple(column.field.attname for column in keyset_context[0]),
        )

    # Conditional total count (workstream B) + count-free ``hasNextPage``
    # (the n+1 overfetch probe): annotate the per-partition ``Count(1) OVER``
    # only when something needs it. The two selection observers come from the
    # shared per-selection walks (``selections.py``), computed ONCE here and
    # reused for both the count decision and the probe decision (their OR is
    # what ``connection_count_required`` returns; splitting them avoids
    # re-walking the selection). ``totalCount`` selected or the window SHAPE
    # needing the count (``requires_total_count``: the ambiguous-empty marker
    # shapes serve counts from it, workstream C; an unbounded limit keeps it
    # conservatively) forces the annotation. A plain ``first: N`` page
    # selecting ``pageInfo.hasNextPage`` but NOT ``totalCount`` takes the probe
    # instead: overfetch one sentinel row (``fetch_*`` bounds) so the row's
    # presence answers ``hasNextPage`` without a partition scan. The probe
    # decision is ``WindowRangePlan.wants_next_page_probe``, made HERE only:
    # ``sel`` is the merged (union) selection when aliases share this relation,
    # so the resolver must not re-derive the probe per response
    # key - it reads the decision back off the window's physical shape (count
    # annotation absent on a plain first page), which stays truthful only
    # while ``next_page_probe`` and ``with_total_count`` below remain mutually
    # exclusive (``_resolve_from_window`` documents that invariant; the
    # ``NestedConnectionRequest`` seam enforces it per window). Under the
    # divergent scheme the observers stay UNION-conservative on purpose: a
    # sibling alias selecting ``totalCount`` keeps every per-key window on the
    # count (no probe) - correct for each window, one shared decision input.
    total_selected = connection_total_count_selected(sel)
    has_next_selected = connection_has_next_page_selected(sel)
    # (g) Hand one fully-resolved fetch request PER WINDOW to the active
    # strategy (the nested_fetch.py seam): the single-window scheme sends the
    # legacy shared-``to_attr`` request; the divergent scheme sends one
    # request per response key under that key's namespaced ``to_attr`` (the
    # graph-node model - O(aliases) batched queries instead of
    # O(parents x aliases) per-parent fallbacks). A strategy returning
    # ``False`` leaves that window unplanned, keeping the Decision-6
    # strictness contract (no resolver identities recorded for it).
    planned_keys: list[str | None] = []
    for resp_key, (offset, limit, reverse), window_seek in keyed_windows:
        range_plan = window_range_plan(offset=offset, limit=limit, reverse=reverse)
        next_page_probe = range_plan.wants_next_page_probe(
            has_next_selected=has_next_selected,
            total_selected=total_selected,
        )
        with_total_count = (
            range_plan.requires_total_count
            or total_selected
            or (has_next_selected and not next_page_probe)
        )
        request = NestedConnectionRequest(
            django_field=raw_relation_field,
            relation_field_name=relation_field_name,
            prefix=prefix,
            child_queryset=child_queryset,
            join=join,
            order_by=tuple(order_by),
            offset=offset,
            limit=limit,
            reverse=reverse,
            with_total_count=with_total_count,
            next_page_probe=next_page_probe,
            keyset_seek=window_seek,
            to_attr=(
                _relation_connection_to_attr(relation_field_name)
                if resp_key is None
                else _relation_connection_to_attr_for_key(relation_field_name, resp_key)
            ),
            lookup=f"{prefix}{instance_accessor(django_field)}",
        )
        strategy = active_strategy()
        strategy_plan = OptimizationPlan()
        if strategy.plan(request, strategy_plan):
            plan.merge_from(strategy_plan)
            planned_keys.append(resp_key)
        else:
            _log_connection_fallback(
                relation_field_name,
                [resp_key] if resp_key is not None else _response_keys(sel),
                f"strategy {getattr(strategy, 'name', type(strategy).__name__)!r} "
                "refused the window",
            )
    if not planned_keys:
        return NestedConnectionPlanResult(plan=plan)
    # Success path: absorb the child metadata the sub-plan collected into the
    # parent only now - a strategy that refused every window (like each earlier
    # fallback shape) must leak no child resolver keys / fk-id elisions /
    # cacheable flip into the parent plan (the Decision-6 no-leakage contract).
    # The child queryset / node selections / order were built ONCE from the
    # merged UNION children and are shared by every per-key window, so one
    # absorb covers all planned keys.
    plan.merge_metadata_from(sub_plan)
    # (h) Record resolver identities so strictness (Slice 4) sees the field as
    # planned - all identities for the shared window; only the planned keys'
    # identities under the divergent scheme (an unplanned sibling alias stays
    # strictness-visible as a real per-parent access).
    if divergent:
        append_unique_many(
            plan.planned_resolver_keys,
            _identities_for_response_keys(runtime_paths, resolver_identities, planned_keys),
        )
    else:
        append_unique_many(plan.planned_resolver_keys, resolver_identities)
    return NestedConnectionPlanResult(
        plan=plan,
        accepted_response_keys=tuple(planned_keys),
    )
