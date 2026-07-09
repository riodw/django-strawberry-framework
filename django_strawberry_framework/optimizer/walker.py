"""Selection-tree walker that converts GraphQL selections into an ``OptimizationPlan``."""

from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

from django.db import models
from django.db.models import Prefetch
from graphql import OperationType
from strawberry import relay

from ..exceptions import ConfigurationError
from ..registry import registry
from ..utils.connections import (
    UnwindowableConnection,
    derive_connection_window_bounds,
    has_connection_sidecar_kwargs,
    window_range_plan,
)
from ..utils.querysets import apply_type_visibility_sync
from ..utils.relations import instance_accessor, is_many_side_relation_kind, relation_kind
from ..utils.strings import snake_case
from . import logger
from .field_meta import FieldMeta
from .hints import OptimizerHint, hint_is_skip
from .join_taxonomy import classify_relation_join
from .nested_fetch import (
    NestedConnectionRequest,
    active_strategy,
    unwindowable_child_queryset_reason,
)
from .plans import (
    OptimizationPlan,
    append_prefetch_unique,
    append_unique,
    append_unique_many,
    deterministic_order,
    order_entry_name_and_direction,
    resolver_key,
    runtime_path_from_info,
)
from .selections import (
    connection_has_next_page_selected,
    connection_total_count_selected,
    included_field_selections,
    is_fragment,
    named_children,
    node_children_with_runtime_prefix,
    response_key,
    response_keys,
    should_include,
    with_runtime_prefix,
)

# The selection-traversal primitives moved to ``optimizer/selections.py`` in the
# 0.0.9 DRY pass (``docs/feedback.md`` Major 2) so the walker and the AST seam in
# ``extension.py`` share ONE fragment/directive/response-key implementation. The
# underscore aliases keep this module's bodies - and the tests that import these
# names from ``optimizer.walker`` - working unchanged; the walker-specific merge
# / runtime-prefix / argument helpers below consume them.
_should_include = should_include
_is_fragment = is_fragment
_response_key = response_key
_response_keys = response_keys
_included_field_selections = included_field_selections
_named_children = named_children
_node_children_with_runtime_prefix = node_children_with_runtime_prefix
_with_runtime_prefix = with_runtime_prefix


def _enable_only_for_operation(info: Any | None) -> bool:
    """Return whether ``.only(...)`` projection is enabled for ``info``'s operation.

    The G2 gate (spec-035 Decision 4): only a ``QUERY`` operation projects
    ``only_fields`` / applies ``.only(...)``. ``MUTATION`` and
    ``SUBSCRIPTION`` suppress projection across the whole plan tree so a
    mutation-resolver-returned queryset never carries a deferred-field set
    (the deferred-refetch / deferred-``save()`` hazard).

    Defensive by design (the package's ``getattr`` posture, mirroring
    ``runtime_path_from_info`` and ``_relay_max_results_from_info``): a
    ``None`` ``info`` *or* a partial test-double whose ``operation`` (or
    ``operation.operation``) is absent falls to the enabled default rather
    than raising. During real execution ``info.operation`` is always present
    (``extension.py::_build_cache_key`` reads it directly), so the defensive
    arm exists only for direct / test callers of ``plan_optimizations``.
    """
    operation = getattr(getattr(info, "operation", None), "operation", None)
    return operation is None or operation is OperationType.QUERY


def plan_optimizations(
    selected_fields: list[Any],
    model: type[models.Model],
    info: Any | None = None,
    *,
    runtime_prefixes: tuple[tuple[str, ...], ...] | None = None,
    source_type: type | None = None,
) -> OptimizationPlan:
    """Walk the selection tree and produce an ``OptimizationPlan``.

    ``source_type`` is the resolver's actual Strawberry return type
    (``origin``). Threaded into the root ``_walk_selections`` call so the
    root ``_resolve_field_map(...)`` uses that type's ``field_map`` /
    ``optimizer_hints`` instead of ``registry.get(model)`` (which
    returns the primary). Nested relation traversal stays unchanged -
    nested ``_walk_selections`` calls leave ``source_type`` ``None`` so
    nested targets continue to route through the primary.
    """
    # Derive the operation-wide projection gate ONCE here (spec-035 Decision 4)
    # and thread the single ``enable_only`` bool through every walk recursion so
    # the root plan, generated ``Prefetch`` child plans, and scalar-only
    # connection windows share ONE operation decision - rather than each
    # projection writer re-reading ``info.operation`` independently.
    enable_only = _enable_only_for_operation(info)
    plan = OptimizationPlan()
    _walk_selections(
        selected_fields,
        model,
        plan,
        info=info,
        runtime_prefixes=(
            runtime_prefixes if runtime_prefixes is not None else (runtime_path_from_info(info),)
        ),
        source_type=source_type,
        enable_only=enable_only,
    )
    # Finalise at handoff: list fields become tuples so post-walker
    # mutation (by callers, the plan cache, or downstream resolvers)
    # raises ``AttributeError`` instead of silently corrupting the
    # cached plan for subsequent requests.
    return plan.finalize()


def plan_relation(field: Any, target_type: type | None, info: Any | None) -> tuple[str, str]:  # noqa: ARG001
    """Return relation traversal kind without constructing querysets.

    ``info`` is unused by this default planner but kept to mirror the
    ``DjangoOptimizerExtension.plan_relation`` override seam, whose subclasses
    may plan on ``info`` - hence the ARG001 noqa rather than dropping the param.
    """
    if _target_has_custom_get_queryset(target_type):
        logger.debug(
            "Optimizer: will downgrade %s to Prefetch because %s overrides get_queryset.",
            field.name,
            target_type.__name__,
        )
        return ("prefetch", "custom_get_queryset")
    if is_many_side_relation_kind(relation_kind(field)):
        return ("prefetch", "default")
    return ("select", "default")


def _target_has_custom_get_queryset(target_type: type | None) -> bool:
    return target_type is not None and target_type.has_custom_get_queryset()


def _resolve_field_map(
    model: type[models.Model],
    *,
    source_type: type | None = None,
) -> tuple[type | None, Any | None, dict[str, Any]]:
    """Return ``(registered DjangoType, definition, field_map)`` for ``model``.

    Prefers the canonical ``DjangoTypeDefinition.field_map`` registered
    for the ``DjangoType`` subclass; falls back to a fresh
    ``model._meta.get_fields()`` walk when the model has no registered
    definition. Centralizes the brittle Django-private ``_meta`` access
    used by the walker.

    ``source_type`` carries the root resolver's actual return type when
    the call comes from ``plan_optimizations`` - that type's field_map /
    optimizer_hints are used so a secondary-return resolver plans
    against the secondary's metadata rather than the primary's.
    Nested ``_walk_selections`` calls leave ``source_type`` ``None``,
    which routes through ``registry.get(model)`` and resolves nested
    relation targets to the primary (the spec-018 nested contract).

    DUAL CONTRACT (read before consuming the returned map): the values
    are ``FieldMeta`` when the model has a registered ``DjangoType``, but
    raw Django field objects (from ``model._meta.get_fields()``) on the
    fallback path when it does not. Both shapes are read via
    ``getattr(..., default)`` downstream -- that defensive access is the
    ONLY reason the two coexist safely, so never read a ``FieldMeta``-only
    attribute without a ``getattr`` default. Treat the values as
    ``FieldMeta | Any`` until the registry-coverage gate lands. The same
    divergence (and the same ``getattr``-defensive fallback) lives in
    ``optimizer/resolvers.py::_field_meta_for_resolver``; keep the two in
    sync.
    """
    type_cls = source_type if source_type is not None else registry.get(model)
    definition = registry.get_definition(type_cls) if type_cls is not None else None
    field_map = (
        definition.field_map
        if definition is not None
        else {f.name: f for f in model._meta.get_fields()}
    )
    return type_cls, definition, field_map


def _resolve_relation_target(
    definition: Any | None,
    django_name: str,
    django_field: Any,
) -> type | None:
    """Return a relation target type, preferring finalized definition metadata."""
    if definition is not None:
        resolved = definition.related_target_for(django_name)
        if resolved is not None:
            target_definition, _model_field = resolved
            return target_definition.origin
    related_model = getattr(django_field, "related_model", None)
    if related_model is None:
        return None
    return registry.get(related_model)


def _resolve_optimizer_hints(definition: Any | None) -> dict[str, OptimizerHint]:
    """Return optimizer hints from the resolved ``DjangoTypeDefinition``."""
    if definition is None:
        return {}
    return definition.optimizer_hints or {}


def _build_child_queryset(
    field: Any,
    target_type: type | None,
    info: Any | None,
    has_custom_qs: bool,
) -> Any:
    """Build the queryset used inside a generated ``Prefetch`` object.

    ``has_custom_qs`` is the precomputed value of
    ``target_type.has_custom_get_queryset()`` from the caller, so the
    method does not need to be called twice on the prefetch path.

    The custom ``get_queryset`` visibility hook runs through the shared
    ``utils/querysets.py::apply_type_visibility_sync`` (the 0.0.9 DRY pass,
    ``docs/feedback.md`` Major 1) so plan-time prefetch visibility uses the SAME
    sync routing the resolver surfaces do: an async-only related ``get_queryset``
    surfaces a clean ``SyncMisuseError`` here (the optimizer walker is sync; a
    coroutine would otherwise leak into ``OptimizationPlan.apply``) - consistent
    with the connection field's documented "nested async ``get_queryset`` ->
    ``relation_shapes = list``" recourse. The base queryset stays the related
    model's own ``_default_manager.all()`` (NOT ``initial_queryset(target_type)``
    - the prefetch child is keyed on ``field.related_model``).
    """
    queryset = field.related_model._default_manager.all()
    if has_custom_qs:
        queryset = apply_type_visibility_sync(target_type, queryset, info)
    return queryset


def _resolver_identities_for(
    sel: Any,
    field_name: str,
    type_cls: type | None,
    runtime_prefixes: tuple[tuple[str, ...], ...],
) -> tuple[tuple[tuple[str, ...], ...], tuple[str, ...]]:
    """Return ``(runtime_paths, resolver_identities)`` for one selection.

    Shared by the list-relation walk (``_walk_selections``, keyed on the
    Django field name) and the nested-connection planner
    (``_plan_connection_relation``, keyed on ``relation_field_name`` - the
    underlying relation field, NOT the generated ``<field>_connection``
    accessor). ``field_name`` is the resolver-key vocabulary, so passing
    ``relation_field_name`` at the connection site keeps the walker's emitted
    key MATCHING the resolve-time key ``connection.py``'s
    ``_check_n1(kind="connection_to_attr")`` rebuilds via
    ``resolver_key(type_cls, relation_field_name, runtime_path)`` - the
    load-bearing "planned -> silent" parity (``connection.py`` resolver doc).

    A selection-specific ``_optimizer_runtime_prefixes`` (set by connection
    extraction) overrides the inherited ``runtime_prefixes``; the runtime path
    is the cartesian product over those prefixes and ``_response_keys(sel)``.
    """
    selection_runtime_prefixes = (
        tuple(sel._optimizer_runtime_prefixes)
        if getattr(sel, "_optimizer_runtime_prefixes", None) is not None
        else runtime_prefixes
    )
    runtime_paths = tuple(
        (*runtime_prefix, response_key)
        for runtime_prefix in selection_runtime_prefixes
        for response_key in _response_keys(sel)
    )
    resolver_identities = tuple(
        resolver_key(type_cls, field_name, runtime_path) for runtime_path in runtime_paths
    )
    return runtime_paths, resolver_identities


def _walk_selections(
    selections: list[Any],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
    info: Any | None = None,
    runtime_prefixes: tuple[tuple[str, ...], ...] = ((),),
    *,
    source_type: type | None = None,
    enable_only: bool = True,
) -> None:
    """Recursive workhorse: descend one normalized level of the selection tree.

    ``source_type`` is set only on the root invocation from
    ``plan_optimizations`` so the resolver's actual Strawberry return
    type drives the root ``_resolve_field_map`` lookup. Recursive
    nested calls (``_plan_select_relation`` and
    ``_build_prefetch_child_queryset`` below) intentionally omit it so
    nested relation targets keep routing through ``registry.get(model)``
    and resolve to the primary type.

    The default ``runtime_prefixes=((),)`` encodes "one empty-path
    prefix" for direct or test-only callers without ``info``;
    ``plan_optimizations`` always passes an explicit single-tuple via
    ``runtime_path_from_info(info)``.

    ``enable_only`` is the operation-wide G2 projection gate (spec-035
    Decision 4) derived once in ``plan_optimizations``. It defaults to
    ``True`` so every existing direct / test caller keeps QUERY behavior;
    the two nested recursions forward the same bool so root and child plans
    share one operation decision. When closed (a non-``QUERY`` operation),
    the scalar-leaf / Relay-pk appends below are skipped and the relation
    writers it threads into apply no ``.only(...)`` projection.
    """
    type_cls, definition, field_map = _resolve_field_map(model, source_type=source_type)
    hints_map = _resolve_optimizer_hints(definition)
    # TODO(spec-035 Slice 3): supply a registry-only type-condition classifier
    # to ``included_field_selections`` at this planning seam.
    # Pseudocode: accept the planning type's GraphQL name plus declared and
    # MRO-inherited interface names; skip known sibling concrete types; recurse
    # fragments-only for unknown composite/union names; never accept the model
    # primary type merely because the Django model matches. The classifier must
    # not call into graphql-core schema introspection.
    merged = _merge_aliased_selections(_included_field_selections(selections))
    relation_connections = getattr(definition, "relation_connections", None) or {}
    for sel in merged:
        django_name = snake_case(sel.name)
        # Recognize a synthesized nested connection BEFORE the unknown-name
        # guard below: ``books_connection`` matches no model field, so without
        # this branch the unknown-name guard silently ``continue``s and the
        # nested connection is never planned (the gap spec-033 closes). The
        # ``relation_connections`` slot (Phase-2.5 synthesis metadata) maps the
        # generated attr name to the underlying relation field name; recognition
        # is metadata-driven, never name-pattern guessing (Decision 3). The
        # ``definition`` resolved above is the model's PRIMARY type, so a
        # divergent secondary type's connection is out of scope for windowed
        # planning and falls through to per-parent (Decision 3 primary contract).
        if django_name in relation_connections:
            _plan_connection_relation(
                sel,
                definition,
                relation_field_name=relation_connections[django_name],
                field_map=field_map,
                plan=plan,
                prefix=prefix,
                info=info,
                runtime_prefixes=runtime_prefixes,
                type_cls=type_cls,
                model=model,
                enable_only=enable_only,
            )
            continue
        django_field = field_map.get(django_name)
        if django_field is None:
            # Decision 7 ("no avoidable lazy loads on ``resolve_id``"):
            # when a Relay-declared ``DjangoType`` uses a custom pk
            # attname (e.g. ``uuid = UUIDField(primary_key=True)``),
            # ``snake_case("id") == "id"`` does not match the field-map
            # key (``"uuid"``). Resolve the configured ``id_attr`` and
            # project that real column so ``_resolve_id_default`` reads
            # the loaded value from ``root.__dict__`` instead of falling
            # back to ``getattr`` and triggering an N+1 lazy load.
            #
            # The verification scans the ``FieldMeta`` values by both
            # ``name`` and ``attname`` rather than ``id_attr in
            # field_map``: ``field_map`` is keyed by the Django field's
            # ``name``, but ``model._meta.pk.attname`` carries the
            # column ``attname`` which differs for relation primary
            # keys (e.g. ``OneToOneField(primary_key=True)`` named
            # ``user`` has ``name="user"`` but ``attname="user_id"``).
            # A naive ``in`` check would skip projection on those shapes
            # and reintroduce the lazy-load. Django's ``.only(attname)``
            # accepts the FK column directly, which avoids dragging the
            # related row in along with it.
            if django_name == "id" and type_cls is not None and issubclass(type_cls, relay.Node):
                id_attr = type_cls.resolve_id_attr()
                if id_attr == "pk":
                    id_attr = model._meta.pk.attname
                db_field = next(
                    (
                        f
                        for f in field_map.values()
                        if f.name == id_attr or getattr(f, "attname", None) == id_attr
                    ),
                    None,
                )
                # ``enable_only`` is the G2 gate (spec-035 Decision 4): under a
                # non-``QUERY`` operation the full row is loaded, so the
                # id-column projection is skipped - resolver reads stay safe
                # without a column mask. Combined with the ``db_field``
                # presence check so the projection is the single guarded action.
                if db_field is not None and enable_only:
                    # Project via ``attname`` so a consumer-declared
                    # ``NodeID`` targeting the relation's ``name`` (e.g.
                    # ``user`` on ``OneToOneField(primary_key=True)``)
                    # still lands on the FK column ``user_id`` instead of
                    # the relation name, which would drag the related row
                    # back via ``.only("user")``.
                    column = getattr(db_field, "attname", None) or id_attr
                    append_unique(plan.only_fields, f"{prefix}{column}")
            continue
        if not django_field.is_relation:
            # Scalar projection. When ``django_name == "id"`` and the
            # type is a Relay-declared ``DjangoType``, this is the
            # default-pk path (the model's pk attname IS ``"id"``); the
            # custom-pk path is handled above.
            # G2 gate (spec-035 Decision 4): QUERY appends as today;
            # MUTATION / SUBSCRIPTION leave ``plan.only_fields`` untouched.
            # The ``continue`` stays unconditional - the scalar field is
            # accounted for whether or not it is projected.
            if enable_only:
                append_unique(plan.only_fields, f"{prefix}{django_name}")
            continue

        # Consumer-assigned relation fields are FULLY unplanned without an
        # explicit hint (connection window rigor, workstream D - the
        # strawberry-django #697 bug class). The consumer replaced the
        # generated relation resolver (``finalizer.py::finalize_django_types``
        # skips attaching one via this same frozenset), so the walker cannot
        # know what their resolver fetches: a speculative model-shaped
        # ``Prefetch`` may pay a query nobody consumes, and - worse -
        # recording ``planned_resolver_keys`` for the walked subtree would
        # short-circuit ``types/resolvers.py::_check_n1`` for every generated
        # resolver under the consumer's OWN returned instances, silencing a
        # real N+1 under strictness. Leaving the selection unplanned (no
        # ``Prefetch``, no resolver keys, no connector column) is the
        # Decision-6 fallback discipline: strictness SEES the per-parent
        # accesses, and a delegating resolver opts back in with an explicit
        # ``OptimizerHint`` (``force_select`` / ``force_prefetch`` /
        # ``prefetch(...)``) - the hint dispatch below runs when one is
        # declared. Consumer-assigned SCALAR shadows are unaffected (the
        # scalar branch above projects columns, which is harmless).
        consumer_assigned = (
            definition is not None and django_name in definition.consumer_assigned_relation_fields
        )
        if consumer_assigned and hints_map.get(django_name) is None:
            continue

        full_path = f"{prefix}{django_name}"
        runtime_paths, resolver_identities = _resolver_identities_for(
            sel,
            django_name,
            type_cls,
            runtime_prefixes,
        )
        target_type = _resolve_relation_target(definition, django_name, django_field)

        hint = hints_map.get(django_name)
        if hint is not None and _apply_hint(
            hint,
            sel=sel,
            django_field=django_field,
            django_name=django_name,
            type_cls=type_cls,
            target_type=target_type,
            plan=plan,
            prefix=prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
            enable_only=enable_only,
            consumer_assigned=consumer_assigned,
        ):
            continue

        relation_plan_kind, _ = plan_relation(django_field, target_type, info)
        _dispatch_single_relation(
            prefer_prefetch=relation_plan_kind == "prefetch",
            sel=sel,
            django_field=django_field,
            target_type=target_type,
            plan=plan,
            prefix=prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
            enable_only=enable_only,
        )


def _dispatch_single_relation(
    *,
    prefer_prefetch: bool,
    sel: Any,
    django_field: Any,
    target_type: type | None,
    plan: OptimizationPlan,
    prefix: str,
    full_path: str,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    enable_only: bool = True,
) -> None:
    """Route one relation selection to the prefetch or the select planner.

    The single owner of the ``_plan_prefetch_relation`` /
    ``_plan_select_relation`` argument threading its three deciders share:
    the cardinality dispatch in ``_walk_selections`` (``plan_relation``'s
    verdict), and the two hint branches in ``_apply_hint`` (``force_select``'s
    custom-``get_queryset`` downgrade and ``force_prefetch``). Only the
    DECISION (``prefer_prefetch``) differs per site; ``full_path`` is a
    select-only concern (``select_related`` resolves query paths).
    """
    if prefer_prefetch:
        _plan_prefetch_relation(
            sel,
            django_field,
            target_type,
            plan,
            prefix,
            info,
            runtime_paths,
            resolver_identities,
            enable_only=enable_only,
        )
    else:
        _plan_select_relation(
            sel,
            django_field,
            target_type,
            plan,
            prefix,
            full_path,
            info,
            runtime_paths,
            resolver_identities,
            enable_only=enable_only,
        )


def _plan_select_relation(
    sel: Any,
    django_field: Any,
    target_type: type | None,
    plan: OptimizationPlan,
    prefix: str,
    full_path: str,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    *,
    enable_only: bool = True,
) -> None:
    """Plan a same-query single-valued relation traversal.

    ``full_path`` (field-name vocabulary) is correct here: Django's
    ``select_related`` resolves QUERY paths, and single-valued forward
    relations have no name/accessor split anyway - the accessor swap is
    a ``_plan_prefetch_relation`` concern only.

    ``enable_only`` (G2 gate, spec-035 Decision 4) gates only the
    connector-column projection in ``_record_relation_access`` and the
    nested scalar appends; ``select_related`` and ``fk_id_elisions`` stay
    intact under a non-``QUERY`` operation.
    """
    _record_relation_access(
        plan,
        django_field,
        prefix,
        resolver_identities,
        enable_only=enable_only,
    )
    target_pk_name = _target_pk_name(django_field)
    if (
        _can_elide_fk_id(django_field)
        and not _target_has_custom_get_queryset(target_type)
        and not _has_custom_id_resolver(target_type, target_pk_name)
        and _selected_scalar_names(sel.selections, django_field.related_model) == {target_pk_name}
    ):
        append_unique_many(plan.fk_id_elisions, resolver_identities)
        return
    append_unique(plan.select_related, full_path)
    # Couple the directive to the resolver metadata it satisfies (B8): if
    # reconciliation later drops this path because a consumer projection
    # cannot traverse it (``plans.py::prune_unsupportable_select_related``),
    # these keys leave ``planned_resolver_keys`` with it.
    recorded = plan.select_path_resolver_keys.get(full_path, ())
    plan.select_path_resolver_keys[full_path] = recorded + tuple(
        key for key in resolver_identities if key not in recorded
    )
    if django_field.related_model is not None:
        _walk_selections(
            sel.selections,
            django_field.related_model,
            plan,
            prefix=f"{full_path}__",
            info=info,
            runtime_prefixes=runtime_paths,
            enable_only=enable_only,
        )


def _plan_prefetch_relation(
    sel: Any,
    django_field: Any,
    target_type: type | None,
    plan: OptimizationPlan,
    prefix: str,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    *,
    enable_only: bool = True,
) -> None:
    """Plan a queryset-boundary relation traversal with optional child optimization.

    The prefetch LOOKUP segment is the relation's instance accessor
    (``utils.relations.instance_accessor``), not ``field.name``: Django's
    ``prefetch_related`` resolves lookups via ``getattr`` on the instance,
    and for a reverse relation without ``related_name`` the field name is
    the related QUERY name (``"book"``) while the accessor is ``"book_set"``
    - planning the query name made every optimized query over such a
    relation fail with ``AttributeError: ... invalid parameter to
    prefetch_related()`` (Round-4 S3 follow-up). Plan keys and resolver
    identities stay in field-name vocabulary; only the lookup string
    Django consumes uses the accessor.

    ``enable_only`` (G2 gate, spec-035 Decision 4) gates only the connector
    columns and the child plan's projection; the ``Prefetch`` itself is
    always emitted so a non-``QUERY`` operation keeps ``prefetch_related``.
    """
    _record_relation_access(
        plan,
        django_field,
        prefix,
        resolver_identities,
        enable_only=enable_only,
    )
    lookup_path = f"{prefix}{instance_accessor(django_field)}"
    has_custom_get_queryset = _target_has_custom_get_queryset(target_type)
    if has_custom_get_queryset:
        plan.cacheable = False
    if django_field.related_model is None:
        append_unique(plan.prefetch_related, lookup_path)
        return

    child_queryset = _build_prefetch_child_queryset(
        sel,
        django_field,
        target_type,
        plan,
        info,
        runtime_paths,
        has_custom_get_queryset=has_custom_get_queryset,
        enable_only=enable_only,
    )
    append_prefetch_unique(plan.prefetch_related, Prefetch(lookup_path, queryset=child_queryset))


def _record_relation_access(
    plan: OptimizationPlan,
    django_field: Any,
    prefix: str,
    resolver_identities: tuple[str, ...],
    *,
    enable_only: bool = True,
) -> None:
    """Record the shared connector and resolver metadata for a relation.

    MUST run before ``_can_elide_fk_id`` fires in ``_plan_select_relation``:
    the FK ``attname`` appended to ``plan.only_fields`` here is the column
    Django still needs to materialise the relation when the JOIN is elided
    (``_resolve_id_default`` reads ``obj.<fk>_id`` directly instead of
    triggering a lazy load through ``obj.<fk>.pk``). Moving this call
    after the elision check would silently drop the FK column on the
    elided path and reintroduce the N+1.

    The G2 gate (spec-035 Decision 4) gates ONLY the connector-column
    append: under a non-``QUERY`` operation the source row is fully loaded,
    so the FK column need not be masked. The ``planned_resolver_keys``
    append stays unconditional so strictness still sees the planned
    relation regardless of operation (Decision 4 / edge case line 315).
    """
    attname = getattr(django_field, "attname", None)
    if enable_only and attname is not None:
        append_unique(plan.only_fields, f"{prefix}{attname}")
    append_unique_many(plan.planned_resolver_keys, resolver_identities)


def _build_prefetch_child_queryset(
    sel: Any,
    django_field: Any,
    target_type: type | None,
    parent_plan: OptimizationPlan,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    *,
    has_custom_get_queryset: bool,
    enable_only: bool = True,
) -> Any:
    """Build and optimize the child queryset for a generated ``Prefetch``.

    ``enable_only`` (G2 gate, spec-035 Decision 4) is forwarded so a child
    plan inherits the root operation's projection decision: under a
    non-``QUERY`` operation the ``Prefetch`` is still built but its child
    queryset carries no deferred-loading mask.
    """
    base_queryset = _build_child_queryset(
        django_field,
        target_type,
        info,
        has_custom_qs=has_custom_get_queryset,
    )
    return _build_prefetch_child_queryset_from_base(
        sel,
        django_field,
        parent_plan,
        info,
        runtime_paths,
        base_queryset=base_queryset,
        enable_only=enable_only,
    )


def _build_prefetch_child_queryset_from_base(
    sel: Any,
    django_field: Any,
    parent_plan: OptimizationPlan,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    *,
    base_queryset: Any,
    enable_only: bool = True,
) -> Any:
    """Apply the child optimization plan to an already-built base queryset.

    This is the queryset-boundary abstraction: the visibility/default-manager
    base queryset is built once by the caller, then every child-plan writer
    operates on that single value. Nested connections classify that base before
    this helper runs so unsafe manager or hook shapes fall back before
    projection or window planning can touch them.
    """
    child_plan = OptimizationPlan()
    _walk_selections(
        sel.selections,
        django_field.related_model,
        child_plan,
        prefix="",
        info=info,
        runtime_prefixes=runtime_paths,
        enable_only=enable_only,
    )
    _ensure_connector_only_fields(child_plan, django_field, enable_only=enable_only)
    _absorb_child_plan(parent_plan, child_plan)
    return child_plan.apply(base_queryset)


def _apply_hint(
    hint: OptimizerHint,
    *,
    sel: Any,
    django_field: Any,
    django_name: str,
    type_cls: type | None,
    target_type: type | None,
    plan: OptimizationPlan,
    prefix: str,
    full_path: str,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    enable_only: bool = True,
    consumer_assigned: bool = False,
) -> bool:
    """Apply a Meta-level ``OptimizerHint`` to ``plan``; return ``True`` when handled.

    Dispatches the four configurable hint shapes (``SKIP``,
    ``prefetch_obj``, ``force_select``, ``force_prefetch``) plus the
    no-op empty form. Returns ``True`` when one of the configurable
    shapes is matched. Returns ``False`` for an ``OptimizerHint()`` with
    no flag set - the caller falls back to the default cardinality
    dispatch in that case. ``OptimizerHint.__post_init__`` already
    rejects conflicting flag combinations, so the priority order here
    is documentation, not collision arbitration.

    ``consumer_assigned`` marks a relation whose resolver the consumer
    supplied (``definition.consumer_assigned_relation_fields``) - the one
    shape allowed to hint a ``Prefetch(..., to_attr=...)``, because only the
    consumer's own resolver can honor the attribute contract.
    """
    if hint_is_skip(hint):
        return True
    if hint.prefetch_obj is not None:
        hinted_to_attr = getattr(hint.prefetch_obj, "to_attr", None)
        if hinted_to_attr and not consumer_assigned:
            # feedback2 P0-4: Django lands ``to_attr`` rows on that attribute
            # instead of ``_prefetched_objects_cache[accessor]`` - which is
            # what the GENERATED relation resolver reads. Accepting the hint
            # would record the relation as planned (silencing strictness)
            # while every row still lazy-loads. Only a consumer-assigned
            # resolver can consume the attribute, so anything else fails
            # loud at plan time with the fix spelled out.
            raise ConfigurationError(
                f"OptimizerHint.prefetch(Prefetch(..., to_attr={hinted_to_attr!r})) on "
                f"{type_cls.__name__}.{django_name}: the generated relation resolver "
                "reads Django's prefetch cache by accessor name and would ignore rows "
                "landed on the to_attr (per-row lazy loads behind a plan strictness "
                "trusts). Drop to_attr from the hinted Prefetch, or assign your own "
                "resolver for the field (consumer-assigned relations may hint with "
                "to_attr because their resolver owns the attribute contract).",
            )
        # ``_apply_hint`` is only entered when ``_resolve_optimizer_hints``
        # returned a non-empty hints map, which it cannot do for
        # ``type_cls is None`` (it short-circuits to ``{}``). The hint
        # error attribution can therefore read ``type_cls.__name__``
        # unguarded; a future direct caller with ``type_cls=None`` will
        # ``AttributeError`` loudly rather than rotting behind a silent
        # ``"UnknownType"`` literal.
        #
        # Validate the consumer-supplied Prefetch BEFORE mutating ``plan``:
        # ``_prefetch_hint_for_path`` may raise ``ConfigurationError`` for
        # a missing lookup path or a lookup that does not target the
        # hinted relation. Recording the resolver identity / non-cacheable
        # flip before validation would leave the plan with phantom
        # connector columns and resolver keys for a relation that was
        # never actually planned, which any future caller catching
        # ``ConfigurationError`` at this layer would consume. Compute the
        # rebased Prefetch first, mutate only on success.
        # The rebase TARGET is the accessor path (what Django's
        # prefetch_related resolves via getattr); the consumer-facing
        # lookup vocabulary in the match below stays ``django_name``.
        rebased_prefetch = _prefetch_hint_for_path(
            hint.prefetch_obj,
            django_name=django_name,
            full_path=f"{prefix}{instance_accessor(django_field)}",
            type_name=type_cls.__name__,
        )
        _record_relation_access(
            plan,
            django_field,
            prefix,
            resolver_identities,
            enable_only=enable_only,
        )
        # Consumer-supplied Prefetch objects commonly close over a queryset
        # built with request- or user-scoped filters; matching the
        # has_custom_get_queryset discipline in _plan_prefetch_relation, mark
        # the plan non-cacheable so the plan cache cannot serve one
        # request's queryset to the next.
        plan.cacheable = False
        append_prefetch_unique(plan.prefetch_related, rebased_prefetch)
        return True
    if hint.force_select:
        kind = relation_kind(django_field)
        if is_many_side_relation_kind(kind):
            raise ConfigurationError(
                f"OptimizerHint.select_related() on {type_cls.__name__}.{django_name}: "
                f"Django requires prefetch_related for {kind} relations; "
                "use OptimizerHint.prefetch_related() or OptimizerHint.prefetch(obj) instead.",
            )
        _dispatch_single_relation(
            prefer_prefetch=_target_has_custom_get_queryset(target_type),
            sel=sel,
            django_field=django_field,
            target_type=target_type,
            plan=plan,
            prefix=prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
            enable_only=enable_only,
        )
        return True
    if hint.force_prefetch:
        _dispatch_single_relation(
            prefer_prefetch=True,
            sel=sel,
            django_field=django_field,
            target_type=target_type,
            plan=plan,
            prefix=prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
            enable_only=enable_only,
        )
        return True
    return False


def _prefetch_hint_for_path(
    prefetch: Prefetch,
    *,
    django_name: str,
    full_path: str,
    type_name: str,
) -> Prefetch:
    """Return ``prefetch`` adapted from a type-relative lookup to ``full_path``."""
    lookup = getattr(prefetch, "prefetch_through", None)
    if lookup is None:
        raise ConfigurationError(
            f"OptimizerHint.prefetch(obj) on {type_name}.{django_name} "
            "requires a Prefetch with a lookup path.",
        )
    if lookup == full_path or lookup.startswith(f"{full_path}__"):
        return prefetch
    if lookup == django_name:
        adjusted_lookup = full_path
    elif lookup.startswith(f"{django_name}__"):
        adjusted_lookup = f"{full_path}{lookup.removeprefix(django_name)}"
    else:
        raise ConfigurationError(
            f"OptimizerHint.prefetch(obj) lookup on {type_name}.{django_name} "
            f"must target the hinted relation {django_name!r}; got {lookup!r}.",
        )
    return Prefetch(
        adjusted_lookup,
        queryset=prefetch.queryset,
        to_attr=getattr(prefetch, "to_attr", None),
    )


def _absorb_child_plan(parent_plan: OptimizationPlan, child_plan: OptimizationPlan) -> None:
    """Absorb an ACCEPTED child queryset plan's metadata into the parent plan.

    Resolver metadata (``fk_id_elisions`` / ``planned_resolver_keys``) plus
    the ``cacheable`` propagation: a non-cacheable child (request-scoped
    consumer queryset, custom hook) must poison the parent's cacheability, or
    the plan cache could serve one request's child queryset to the next.
    Folded in here - rather than a separate line at each absorb site - so a
    future third site cannot forget it (the cache-poisoning hazard the plan
    docstring warns about).
    """
    for key in child_plan.fk_id_elisions:
        append_unique(parent_plan.fk_id_elisions, key)
    for key in child_plan.planned_resolver_keys:
        append_unique(parent_plan.planned_resolver_keys, key)
    if not child_plan.cacheable:
        parent_plan.cacheable = False


def _selected_scalar_names(
    selections: list[Any],
    model: type[models.Model] | None,
) -> set[str] | None:
    """Return selected scalar Django field names, or ``None`` when elision is unsafe."""
    if model is None:
        return None
    # Nested-only: do NOT thread source_type here. The only caller is
    # _plan_select_relation for FK-id elision; the model argument is
    # django_field.related_model, never the resolver's root return type.
    # Nested relation targets correctly route through the primary via
    # registry.get(model), which is what the default _resolve_field_map(model)
    # call already does. The scalar-only secondary-type regression is
    # exercised through the root _walk_selections path, not through this
    # helper. (spec-018 rev6 M1 audit invariant.)
    _type_cls, _definition, field_map = _resolve_field_map(model)
    # TODO(spec-035 Slice 3): audit this FK-id-elision helper as the walker's
    # second ``included_field_selections`` consumer. Pseudocode: either share
    # the same type-condition classifier used by ``_walk_selections`` or prove
    # the helper only receives concretely typed relation child selections where
    # sibling fragments are GraphQL-invalid.
    #
    # No ``_merge_aliased_selections`` here (unlike ``_walk_selections``): this
    # helper only builds a SET of scalar field names, and merging aliased
    # duplicates before set insertion cannot change that set - two aliases of one
    # field collapse to a single name either way, and merging never turns a
    # scalar into a relation. Skipping the merge avoids a redundant second pass
    # over the same child selections the caller re-walks when elision does not
    # fire (the common case: any non-pk scalar selected).
    scalar_names: set[str] = set()
    for sel in _included_field_selections(selections):
        django_name = snake_case(sel.name)
        django_field = field_map.get(django_name)
        if django_field is None or django_field.is_relation:
            return None
        scalar_names.add(django_name)
    return scalar_names


def _can_elide_fk_id(field: Any) -> bool:
    """Return ``True`` when ``field`` stores the related object's id on the source row.

    ``field`` is ``FieldMeta | Any`` per the ``_resolve_field_map`` dual
    contract. A registered model yields a ``FieldMeta`` carrying the
    precomputed ``fk_id_elision_eligible`` slot, returned directly. A raw
    Django field (the unregistered-model fallback) is run through the
    canonical ``FieldMeta._from_field_shape`` so the walker and ``FieldMeta``
    share ONE elision predicate - including the composite-PK exclusion (a
    single-column source ``attname`` cannot satisfy a tuple-shaped target
    pk, so eliding would surface wrong data) - and cannot drift.
    """
    stamped = getattr(field, "fk_id_elision_eligible", None)
    if stamped is not None:
        return stamped
    return FieldMeta._from_field_shape(field, is_relation=True).fk_id_elision_eligible


def _target_pk_name(field: Any) -> str | None:
    """Return the related model's concrete primary-key field name."""
    stamped = getattr(field, "target_pk_name", None)
    if stamped is not None:
        return stamped
    related_model = getattr(field, "related_model", None)
    if related_model is None:
        return None
    return related_model._meta.pk.name


def _has_custom_id_resolver(target_type: type | None, target_pk_name: str | None) -> bool:
    """Return ``True`` when target type customizes the selected id field.

    Routes through the registered definition's memoized check when one exists,
    and otherwise delegates to the *same* free function
    (``definition.origin_has_custom_id_resolver``) so the registered and
    definition-less paths cannot answer the same type differently.
    """
    if target_type is None or target_pk_name is None:
        return False
    definition = registry.get_definition(target_type)
    if definition is not None:
        return definition.has_custom_id_resolver_for(target_pk_name)
    # Lazy import: ``types.definition`` pulls in ``optimizer.field_meta`` at
    # module load, so importing it at the top of the walker risks an
    # import-time cycle through the optimizer package init.
    from ..types.definition import origin_has_custom_id_resolver

    return origin_has_custom_id_resolver(target_type, target_pk_name)


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


def _ensure_connector_only_fields(
    plan: OptimizationPlan,
    parent_field: Any,
    *,
    enable_only: bool = True,
) -> None:
    """Inject columns Django needs to attach prefetched rows to parents.

    The G2 gate (spec-035 Decision 4) short-circuits before the
    empty-``only_fields`` guard: under a non-``QUERY`` operation the child
    plan appended nothing to ``only_fields``, so the connector append must
    also be skipped. The early return makes that explicit rather than
    relying on the empty-set no-op, which is insufficient because
    ``_project_scalar_only_window`` and ``_record_relation_access`` populate
    independently of the scalar path.
    """
    if not enable_only:
        return
    if not plan.only_fields:
        return
    attname = _connector_only_field(parent_field)
    if attname is not None:
        append_unique(plan.only_fields, attname)
        return
    logger.debug(
        "Optimizer: could not resolve connector column for Prefetch %s; only() may be less precise.",
        getattr(parent_field, "name", parent_field),
    )


def _merge_aliased_selections(selections: list[Any]) -> list[Any]:
    """Merge same-field selections while preserving all represented response keys.

    The main walker path passes fragment-inlined field selections here, so
    duplicate relation branches are combined before planning. The fragment
    passthrough below is retained for defensive direct helper use.

    Fast path: when no two selections share a snake-cased field name (the
    overwhelmingly common query shape - each field selected once), there is
    nothing to merge, so the input list is returned unchanged instead of
    rebuilding it into per-selection ``SimpleNamespace`` clones. Downstream
    readers (``_response_keys`` / ``_selection_runtime_prefixes`` /
    ``_aliased_arguments_diverge``) all ``getattr``-default the ``_optimizer_*``
    markers a raw selection lacks, so the passthrough is shape-compatible. Any
    fragment defensively forces the slow path (fragments cannot be deduped by
    name and are passed through by the merge loop below unchanged).
    """
    seen_names: set[str] = set()
    for sel in selections:
        if _is_fragment(sel):
            break
        key = snake_case(sel.name)
        if key in seen_names:
            break
        seen_names.add(key)
    else:
        return selections
    seen: dict[str, Any] = {}
    result: list[Any] = []
    for sel in selections:
        if _is_fragment(sel):
            result.append(sel)
            continue
        key = snake_case(sel.name)
        if key in seen:
            merged = seen[key]
            # Keep duplicate selections as defensive as the first-seen
            # construction below; Strawberry currently provides a list here,
            # but some tests and future integration shims may omit it.
            merged.selections = list(merged.selections) + list(
                getattr(sel, "selections", None) or [],
            )
            response_key = _response_key(sel)
            if response_key not in merged._optimizer_response_keys:
                merged._optimizer_response_keys.append(response_key)
            _merge_runtime_prefixes(merged, sel)
            # Preserve per-response-key argument payloads so a synthesized
            # connection sibling's pagination/sidecar arguments stay
            # comparable AFTER the merge (spec-033 Decision 6): identical
            # arguments across aliases are window-planned together, while
            # divergent aliases (``a: books(first:2)`` + ``b: books(first:5)``,
            # or differing filter/orderBy) must fall back per-parent because one
            # ``to_attr`` cannot serve two windows. The first occurrence's
            # ``arguments`` stays the merged selection's primary value (the
            # pre-033 first-args-win contract for non-connection fields); the
            # per-response-key map is the side-channel ``_plan_connection_relation``
            # reads to detect divergence.
            _record_response_key_arguments(merged, sel)
        else:
            merged = SimpleNamespace(
                name=sel.name,
                alias=getattr(sel, "alias", None),
                directives=getattr(sel, "directives", None) or {},
                arguments=getattr(sel, "arguments", None) or {},
                selections=list(getattr(sel, "selections", None) or []),
                _optimizer_response_keys=[_response_key(sel)],
                _optimizer_runtime_prefixes=_selection_runtime_prefixes(sel),
                # Per-response-key argument payloads (spec-033 Decision 6); see
                # the merge branch above and ``_aliased_arguments_diverge``.
                _optimizer_response_key_arguments={
                    _response_key(sel): getattr(sel, "arguments", None) or {},
                },
            )
            seen[key] = merged
            result.append(merged)
    return result


def _record_response_key_arguments(merged: Any, selection: Any) -> None:
    """Record a duplicate selection's arguments under its response key.

    The merged selection carries ``_optimizer_response_key_arguments``: a map
    from response key to that occurrence's resolved argument payload. Kept off
    the inline merge branch so ``_merge_aliased_selections`` (a control-flow
    hotspot) does not grow another branch (spec-033 Decision 6).
    """
    merged._optimizer_response_key_arguments[_response_key(selection)] = (
        getattr(selection, "arguments", None) or {}
    )


def _aliased_arguments_diverge(selection: Any) -> bool:
    """Return whether a merged selection's aliases carry divergent arguments.

    ``True`` when two response keys of the same field were selected with
    different argument payloads (e.g. ``a: books(first: 2)`` +
    ``b: books(first: 5)``). A synthesized connection with divergent aliases is
    left unplanned (one ``to_attr`` cannot serve two windows; spec-033
    Decision 6). Selections built outside ``_merge_aliased_selections`` (direct
    test/helper callers) carry no per-response-key map and never diverge.
    """
    per_key = getattr(selection, "_optimizer_response_key_arguments", None)
    if not per_key:
        return False
    payloads = list(per_key.values())
    first = payloads[0]
    return any(payload != first for payload in payloads[1:])


def _selection_runtime_prefixes(selection: Any) -> list[tuple[str, ...]] | None:
    """Return selection-specific runtime prefixes carried by connection extraction."""
    prefixes = getattr(selection, "_optimizer_runtime_prefixes", None)
    if prefixes is None:
        return None
    return list(prefixes)


def _merge_runtime_prefixes(merged: Any, selection: Any) -> None:
    """Union connection-carried runtime prefixes while preserving order."""
    incoming = _selection_runtime_prefixes(selection)
    if incoming is None:
        return
    if merged._optimizer_runtime_prefixes is None:
        merged._optimizer_runtime_prefixes = incoming
        return
    for prefix in incoming:
        if prefix not in merged._optimizer_runtime_prefixes:
            merged._optimizer_runtime_prefixes.append(prefix)


# ---------------------------------------------------------------------------
# ``edges { node }`` selection-unwrap orchestration (spec-033 Decision 9).
#
# The fragment-aware / directive-aware / runtime-prefix-carrying PRIMITIVES
# (``named_children`` / ``node_children_with_runtime_prefix`` /
# ``with_runtime_prefix`` / ``should_include`` / ``is_fragment``) live in
# ``optimizer/selections.py`` (the 0.0.9 DRY pass, ``docs/feedback.md`` Major 2)
# so the root-connection seam (``extension._connection_node_child_selections``)
# and the walker's nested ``_plan_connection_relation`` unwrap an
# ``edges { node { ... } }`` wrapper with ONE implementation. The walker reaches
# them through the underscore aliases bound at module top; the per-caller
# orchestration (``_connection_node_selections`` below) stays here.
# ---------------------------------------------------------------------------


def _relation_connection_to_attr(relation_field_name: str) -> str:
    """Return the package-reserved ``to_attr`` for a relation connection window.

    ``_dst_<field>_connection``, keyed on the relation FIELD NAME (not the
    accessor). The single source for this literal across the walker (plan
    site), the finalizer (resolver precompute, Slice 2), and the connection
    resolver probe (Slice 2), so the ``_dst_`` namespace string is never
    duplicated as a scattered f-string (Decision 4 / Decision 5).
    """
    return f"_dst_{relation_field_name}_connection"


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
    """Resolve ``relay_max_results`` from the walker's (graphql-core) ``info``.

    The walker runs at the optimizer extension's middleware layer, where ``info``
    is the raw graphql-core ``GraphQLResolveInfo`` whose ``.schema`` is a bare
    ``GraphQLSchema`` with NO ``.config`` (unlike the resolve-time Strawberry
    ``Info`` ``SliceMetadata.from_arguments`` expects). The config lives on the
    Strawberry schema wrapper Strawberry stashes at ``schema._strawberry_schema``
    (the same brittle-private contract ``extension._strawberry_schema_from_info``
    centralizes; the walker cannot import that helper without a cycle - extension
    imports walker). Resolve the cap explicitly here and pass it to
    ``SliceMetadata.from_arguments`` so the helper never dereferences
    ``info.schema.config`` itself. Falls back to a ``schema.config`` shape (the
    ``_fake_info`` test stub) and finally ``None`` (the engine default applies).
    """
    schema = getattr(info, "schema", None)
    config = getattr(getattr(schema, "_strawberry_schema", None), "config", None)
    if config is None:
        config = getattr(schema, "config", None)
    return getattr(config, "relay_max_results", None)


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

    The walker-side adapter over the shared
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
    ``_plan_connection_relation`` leaves the selection UNPLANNED and the shipped
    nested field path raises at its own error locality (Decision 4 step f). The
    resolver calls the same helper directly with already-coerced Strawberry
    arguments and lets the pagination error propagate instead.

    ``UnwindowableConnection`` (the offset-bearing backward shape, ``after`` +
    ``last``) is deliberately NOT caught here: it is a VALID query that resolves
    correctly per-parent, so ``_plan_connection_relation`` must treat it as a
    fully-unplanned Decision-6 fallback (no ``planned_resolver_keys`` entry, like
    the sidecar / divergent-alias / distinct shapes) rather than the
    malformed-pagination ``None`` path that records the field as accounted-for
    (spec-033 Decision 5).
    """
    arguments = getattr(sel, "arguments", None) or {}
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


def _plan_connection_relation(
    sel: Any,
    definition: Any,
    *,
    relation_field_name: str,
    field_map: dict[str, Any],
    plan: OptimizationPlan,
    prefix: str,
    info: Any | None,
    runtime_prefixes: tuple[tuple[str, ...], ...],
    type_cls: type | None,
    model: type[models.Model],
    enable_only: bool = True,
) -> None:
    """Plan one recognized nested connection as a windowed ``Prefetch``.

    Orchestrates the windowed-prefetch plan (spec-033 Decision 4); leaves the
    selection UNPLANNED (no ``Prefetch``, no ``planned_resolver_keys`` entry) for
    each Decision-6 fallback shape so Slice 4's strictness contract still sees
    the per-parent access. Delegates child-queryset construction to the same
    helpers the list path uses (``_build_prefetch_child_queryset`` /
    ``_build_child_queryset``); the only addition is the window applied after
    ``child_plan.apply``.
    """
    django_field = field_map.get(relation_field_name)
    if django_field is None:
        return
    # (b) Fallback shapes detectable before any queryset is built -> UNPLANNED.
    arguments = getattr(sel, "arguments", None) or {}
    if has_connection_sidecar_kwargs(arguments):
        return  # sidecar input (filter:/orderBy:) - per-parent fallback.
    if _aliased_arguments_diverge(sel):
        return  # divergent aliased pagination/sidecar args - one to_attr cannot serve two.
    hints_map = _resolve_optimizer_hints(definition)
    if hint_is_skip(hints_map.get(relation_field_name)):
        return  # OptimizerHint.SKIP extends to the connection sibling.

    target_type = _resolve_relation_target(definition, relation_field_name, django_field)
    has_custom_get_queryset = _target_has_custom_get_queryset(target_type)

    runtime_paths, resolver_identities = _resolver_identities_for(
        sel,
        relation_field_name,
        type_cls,
        runtime_prefixes,
    )

    if django_field.related_model is None:
        return

    # (e/f) Slice window from the selection's resolved pagination arguments. Pure
    # (mutates nothing), so resolve it BEFORE the child build - a malformed slice
    # must not leave child resolver keys / cacheable flips on the parent plan.
    try:
        window = _connection_window_slice(sel, info)
    except UnwindowableConnection:
        # (b) Offset-bearing backward window (after + last): the reversed window's
        # whole-partition row numbering cannot honor the after offset, so it falls
        # back per-parent like the other Decision-6 fallback shapes (sidecar,
        # divergent alias, distinct). Stay FULLY unplanned - record NO resolver
        # identities - so the per-parent access stays visible to the Slice-4
        # strictness contract (spec-033 Decision 5; unlike the malformed-pagination
        # `window is None` path below, this query resolves correctly per-parent
        # and never raises its own error, so it is a real per-parent access).
        return
    if window is None:
        # Malformed pagination (Decision 4 step f): emit NO window prefetch so the
        # connection pipeline runs per-parent and raises its OWN cursor/pagination
        # validation error at the field. But RECORD the resolver identities so the
        # Slice-4 strictness contract treats the field as accounted-for and does
        # NOT preempt that error with a spurious "Unplanned N+1" OptimizerError
        # under `"raise"` (spec-033 Decision 8 - error locality wins here). The
        # other Decision-6 fallback shapes (sidecar, divergent alias, hint SKIP,
        # distinct, unwindowable partition) stay fully unplanned on purpose so
        # strictness CAN see them as real per-parent accesses.
        append_unique_many(plan.planned_resolver_keys, resolver_identities)
        return
    offset, limit, reverse = window
    if reverse and limit == 0:
        # (b) ``last: 0``: upstream ``ListConnection`` slices ``edges[-0:]``,
        # which is the WHOLE list - only the per-parent pipeline reproduces
        # that quirk, so a planned reversed window would always come back
        # empty and be discarded by ``_resolve_from_window``'s fallback
        # return. Plan nothing (feedback2 P0-3 follow-through): no dead
        # window query riding every request, and no resolver keys - the
        # per-parent fallback stays strictness-visible like the other
        # Decision-6 fallback shapes. ``_resolve_from_window`` keeps its own
        # ``last: 0`` guard as the defensive tail for direct callers.
        return

    # (g, partition) also pure; classify the join before the child build so an
    # unsupported relation kind (single-valued forward, or a shape with no
    # resolvable parent partition) falls back without leaking child metadata.
    # The RAW field (not the ``FieldMeta``) also rides the strategy request:
    # the lateral backend reads ``remote_field`` / through metadata that only
    # the raw descriptor carries.
    raw_relation_field = _raw_relation_field(model, relation_field_name)
    join = classify_relation_join(raw_relation_field)
    if not join.windowable:
        return

    # (a) Unwrap edges { node }; scalar-only selections plan with [] node children.
    node_selections = _connection_node_selections(sel, runtime_paths)
    scalar_only = not node_selections
    node_sel = SimpleNamespace(selections=node_selections)

    # (c, pre-build safety gate) the base child queryset comes from consumer
    # code even without a target ``get_queryset``: a custom default manager's
    # ``.all()`` can still return distinct/sliced/combined/values/locking
    # shapes no fetch strategy can window. Build that base exactly once,
    # classify it unconditionally, and feed the same value into child-plan
    # application on the success path.
    base_queryset = _build_child_queryset(
        django_field,
        target_type,
        info,
        has_custom_qs=has_custom_get_queryset,
    )
    if unwindowable_child_queryset_reason(base_queryset) is not None:
        return

    # (c) Build the child plan/queryset exactly like the list prefetch path, but
    # against a THROWAWAY sub-plan so a strategy refusal below can fall back
    # without leaking the child's resolver keys / fk-id elisions / cacheable flip
    # into the parent (Decision 6 / DoD-4 "no planned_resolver_keys entry"). The
    # parent plan absorbs the child metadata only on the success path.
    sub_plan = OptimizationPlan()
    if has_custom_get_queryset:
        sub_plan.cacheable = False
    child_queryset = _build_prefetch_child_queryset_from_base(
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

    # (d) Deterministic total order shared with the resolve-time pipeline.
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
    # ``sel`` is the merged (union) selection when same-argument aliases share
    # this window, so the resolver must not re-derive the probe per response
    # key - it reads the decision back off the window's physical shape (count
    # annotation absent on a plain first page), which stays truthful only
    # while ``next_page_probe`` and ``with_total_count`` below remain mutually
    # exclusive (``_resolve_from_window`` documents that invariant).
    range_plan = window_range_plan(offset=offset, limit=limit, reverse=reverse)
    total_selected = connection_total_count_selected(sel)
    has_next_selected = connection_has_next_page_selected(sel)
    next_page_probe = range_plan.wants_next_page_probe(
        has_next_selected=has_next_selected,
        total_selected=total_selected,
    )
    with_total_count = (
        range_plan.requires_total_count
        or total_selected
        or (has_next_selected and not next_page_probe)
    )
    # (g) Hand the fully-resolved fetch request to the active strategy (the
    # nested_fetch.py seam): the windowed prefetch is the default backend; a
    # strategy returning ``False`` leaves the selection unplanned, keeping the
    # Decision-6 strictness contract (no resolver identities recorded).
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
        to_attr=_relation_connection_to_attr(relation_field_name),
        lookup=f"{prefix}{instance_accessor(django_field)}",
    )
    if not active_strategy().plan(request, plan):
        return
    # Success path: absorb the child metadata the sub-plan collected into the
    # parent only now - a strategy that refused (like every earlier fallback
    # shape) must leak no child resolver keys / fk-id elisions / cacheable
    # flip into the parent plan (the Decision-6 no-leakage contract).
    _absorb_child_plan(plan, sub_plan)
    # (h) Record resolver identities so strictness (Slice 4) sees the field as planned.
    append_unique_many(plan.planned_resolver_keys, resolver_identities)


def _raw_relation_field(model: type[models.Model], relation_field_name: str) -> Any:
    """Return the raw Django relation field for ``relation_field_name`` on ``model``.

    The window partition derivation needs the raw descriptor's
    ``remote_field`` (the forward-M2M reverse query name lives only there and is
    not carried on ``FieldMeta``); ``field_map`` holds ``FieldMeta``, so resolve
    the live field from ``_meta`` (spec-033 Decision 4 partition derivation).
    """
    return model._meta.get_field(relation_field_name)
