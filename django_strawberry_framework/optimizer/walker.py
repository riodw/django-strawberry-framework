"""Selection walker that delegates nested Relay connections to their private planner."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from django.db import models
from django.db.models import Prefetch
from graphql import OperationType
from strawberry import relay
from strawberry.utils.str_converters import to_camel_case

from ..exceptions import ConfigurationError
from ..registry import registry
from ..utils.querysets import apply_type_visibility_sync
from ..utils.relations import instance_accessor, is_many_side_relation_kind, relation_kind
from ..utils.strings import snake_case
from ..utils.typing import schema_config_from_info
from . import logger
from . import nested_planner as _nested_planner
from .field_meta import FieldMeta
from .hints import OptimizerHint, hint_is_skip
from .nested_planner import (
    _coerce_pagination_int,
    _connector_only_field,
)
from .nested_planner import (
    plan_connection_relation as _plan_nested_connection_relation,
)
from .plans import (
    OptimizationPlan,
    append_prefetch_unique,
    append_unique,
    append_unique_many,
    resolver_key,
    runtime_path_from_info,
)
from .selections import (
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
# Compatibility aliases for private imports that predate the connection
# planner extraction. The implementations now live with their owner.
_concrete_order_columns = _nested_planner._concrete_order_columns
_connection_window_slice = _nested_planner._connection_window_slice
_connection_window_slice_from_arguments = _nested_planner._connection_window_slice_from_arguments
_extend_only_projection = _nested_planner._extend_only_projection
_keyset_cursor_context = _nested_planner._keyset_cursor_context
_keyset_window_slice_from_arguments = _nested_planner._keyset_window_slice_from_arguments
_order_entry_field_name = _nested_planner._order_entry_field_name
_project_scalar_only_window = _nested_planner._project_scalar_only_window
_relation_connection_to_attr = _nested_planner._relation_connection_to_attr
_relation_connection_to_attr_for_key = _nested_planner._relation_connection_to_attr_for_key
_relay_max_results_from_info = _nested_planner._relay_max_results_from_info


def _record_prefetch_path_keys(
    plan: OptimizationPlan,
    lookup_path: str,
    keys: tuple[str, ...],
) -> None:
    """Attribute resolver / FK-id keys to a ``prefetch_related`` lookup path (B8)."""
    if not keys:
        return
    recorded = plan.prefetch_path_resolver_keys.get(lookup_path, ())
    plan.prefetch_path_resolver_keys[lookup_path] = recorded + tuple(
        key for key in keys if key not in recorded
    )


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


def _schema_name_converter(info: Any | None) -> Any | None:
    """Return the active Strawberry name converter from planner or resolver ``info``."""
    return getattr(schema_config_from_info(info), "name_converter", None)


def _graphql_names_by_python_name(type_cls: type | None, info: Any | None) -> dict[str, str]:
    """Return authoritative GraphQL names for the Strawberry fields on ``type_cls``."""
    definition = getattr(type_cls, "__strawberry_definition__", None)
    converter = _schema_name_converter(info)
    names: dict[str, str] = {}
    for field in getattr(definition, "fields", ()):
        python_name = getattr(field, "python_name", None)
        if python_name is None:
            continue
        if converter is not None:
            names[python_name] = converter.get_graphql_name(field)
        else:
            names[python_name] = getattr(field, "graphql_name", None) or to_camel_case(
                python_name,
            )
    return names


def _field_by_graphql_name(
    graphql_name: str,
    field_map: dict[str, Any],
    *,
    type_cls: type | None = None,
    info: Any | None = None,
    graphql_names: dict[str, str] | None = None,
) -> tuple[str, Any] | None:
    """Forward-resolve a GraphQL name to its real Django field after a reverse miss.

    Strawberry's default camelizer is lossy at digit boundaries
    (``address_2`` -> ``address2``), and explicit field names or custom schema
    converters need not be reversible at all. Compare the selection against the
    authoritative Strawberry field name when available, falling back to the
    default converter for unregistered models and synthetic planner calls.
    """
    if graphql_names is None:
        graphql_names = _graphql_names_by_python_name(type_cls, info)
    for field in field_map.values():
        django_name = getattr(field, "name", None)
        if django_name is None:
            continue
        candidate = graphql_names.get(django_name)
        if candidate is None:
            candidate = to_camel_case(django_name)
        if candidate == graphql_name:
            return django_name, field
    return None


def _resolve_selection_target(
    graphql_name: str,
    field_map: dict[str, Any],
    relation_connections: dict[str, str],
    *,
    type_cls: type | None,
    info: Any | None,
) -> tuple[str, str, Any | None] | None:
    """Resolve a selection across model-field and synthesized-connection namespaces."""
    snake = snake_case(graphql_name)
    relation_field_name = relation_connections.get(snake)
    if relation_field_name is not None:
        return "connection", relation_field_name, None
    field = field_map.get(snake)
    if field is not None:
        return "field", snake, field
    graphql_names = _graphql_names_by_python_name(type_cls, info)
    for generated, relation_name in relation_connections.items():
        candidate = graphql_names.get(generated)
        if candidate is None:
            candidate = to_camel_case(generated)
        if candidate == graphql_name:
            return "connection", relation_name, None
    resolved = _field_by_graphql_name(
        graphql_name,
        field_map,
        type_cls=type_cls,
        info=info,
        graphql_names=graphql_names,
    )
    if resolved is not None:
        real, real_field = resolved
        return "field", real, real_field
    return None


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
        # Resolve the selection name through the ONE consolidated resolver
        # (fast-path exact reversal, forward-camelization scan on a miss). It
        # recognizes a synthesized nested connection BEFORE the field namespace
        # and BEFORE the unknown-name guard below: ``booksConnection`` /
        # ``line2Connection`` match no model field, so without this branch the
        # unknown-name guard silently ``continue``s and the nested connection
        # is never planned (the gap spec-033 closes, extended to digit-boundary
        # relation names here). The ``relation_connections`` slot (Phase-2.5
        # synthesis metadata) maps the generated attr name to the underlying
        # relation field name; recognition is metadata-driven, never
        # name-pattern guessing (Decision 3). The ``definition`` resolved above
        # is the model's PRIMARY type, so a divergent secondary type's
        # connection is out of scope for windowed planning and falls through to
        # per-parent (Decision 3 primary contract).
        resolved = _resolve_selection_target(
            sel.name,
            field_map,
            relation_connections,
            type_cls=type_cls,
            info=info,
        )
        if resolved is not None and resolved[0] == "connection":
            _plan_connection_relation(
                sel,
                definition,
                relation_field_name=resolved[1],
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
        if resolved is not None:
            _kind, django_name, django_field = resolved
        else:
            # Neither namespace matched: keep the reversed name so the Relay
            # custom-pk ``id`` branch below can still fire, and leave the field
            # unresolved for the unknown-name handling.
            django_name, django_field = snake_case(sel.name), None
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
        and _selected_scalar_names(sel.selections, django_field.related_model, info=info)
        == {target_pk_name}
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
        _record_prefetch_path_keys(plan, lookup_path, resolver_identities)
        append_unique(plan.prefetch_related, lookup_path)
        return

    # Snapshot before the child absorb so nested PLANNED keys that land on
    # the parent are attributed to THIS prefetch lookup (B8 consumer-wins
    # must strip them with the dropped Prefetch, so strictness re-sees the
    # now-lazy relation). Nested FK-id elisions are deliberately NOT recorded
    # here: an elision reads a column already on the parent row (``obj.<fk>_id``)
    # and adds no query whether or not this prefetch survives, so it must
    # never be stripped - mirroring the select-related path, whose elision
    # branch returns before recording into ``select_path_resolver_keys``.
    prior_planned = frozenset(plan.planned_resolver_keys)
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
    nested_keys = tuple(k for k in plan.planned_resolver_keys if k not in prior_planned)
    _record_prefetch_path_keys(plan, lookup_path, (*resolver_identities, *nested_keys))
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
        # B8 coupling: attribute the relation's resolver keys to the rebased
        # lookup so a later consumer-wins drop strips them from strictness.
        hinted_lookup = getattr(rebased_prefetch, "prefetch_to", None) or getattr(
            rebased_prefetch,
            "prefetch_through",
            "",
        )
        _record_prefetch_path_keys(plan, hinted_lookup, resolver_identities)
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
    parent_plan.merge_metadata_from(child_plan)


def _selected_scalar_names(
    selections: list[Any],
    model: type[models.Model] | None,
    *,
    info: Any | None = None,
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
    type_cls, _definition, field_map = _resolve_field_map(model)
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
        if django_field is None:
            # Same lossy-reversal miss as ``_walk_selections`` (site 1): a
            # digit-boundary scalar (``address_2`` -> schema ``address2``)
            # reverses to ``"address2"`` and misses the real ``"address_2"``
            # field-map key. Forward-resolve through the shared primitive so a
            # digit-boundary target pk (e.g. ``code_2``) is recognized and the
            # FK-id elision can fire instead of falling back to a redundant
            # ``select_related`` JOIN. No connection form is possible here - the
            # helper walks a single-valued relation's child scalar selections
            # for elision, and any relation/connection child returns ``None``
            # below regardless.
            resolved = _field_by_graphql_name(
                sel.name,
                field_map,
                type_cls=type_cls,
                info=info,
            )
            if resolved is not None:
                django_name, django_field = resolved
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

    Fast path: when no two selections share an exact GraphQL field name (the
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
        key = sel.name
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
        key = sel.name
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
            # arguments across aliases are window-planned together (one shared
            # ``to_attr``), while divergent aliases (``a: books(first:2)`` +
            # ``b: books(first:5)``, or differing filter/orderBy) plan ONE
            # WINDOW PER RESPONSE KEY under per-key ``to_attr``s (idea #2 -
            # O(aliases) batched queries). The first occurrence's
            # ``arguments`` stays the merged selection's primary value (the
            # pre-033 first-args-win contract for non-connection fields); the
            # per-response-key map is the side-channel ``_plan_connection_relation``
            # reads to select the scheme and derive each key's window.
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

    ONE response key arriving twice with DIFFERENT payloads is flagged as a
    conflict (``_optimizer_response_key_argument_conflict``). graphql-core's
    field-merging validation forbids that within one selection set, but the
    walker also merges the same-named CHILDREN of different parent-alias
    subtrees (``a: books(first: 1) { loans(first: 1) }`` + ``b: books(first:
    3) { loans(first: 2) }`` union their node children), where two payloads
    under one key are legal - and unservable by any single child plan, since
    the resolve side routes by response key alone (a silent overwrite here
    planned ONE nested window from the first payload and served the other
    alias a wrong page). ``_plan_connection_relation`` treats the flag as a
    fully-unplanned fallback. Payloads compare pagination-NORMALIZED
    (``_normalized_alias_payload``) so an inline literal and an equal
    resolved variable do not conflict.
    """
    response_key = _response_key(selection)
    payload = getattr(selection, "arguments", None) or {}
    per_key = merged._optimizer_response_key_arguments
    if response_key in per_key and _normalized_alias_payload(
        per_key[response_key],
    ) != _normalized_alias_payload(payload):
        merged._optimizer_response_key_argument_conflict = True
    per_key[response_key] = payload


def _normalized_alias_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return ``payload`` with pagination bounds coerced for equality checks.

    Alias-payload comparison (the divergence selector and the same-key
    conflict detector) must not be fooled by the argument VOCABULARY: an
    inline Int literal arrives as the raw token string (``{"first": "2"}``)
    while a resolved variable arrives engine-coerced (``{"first": 2}``) - the
    same window either way (``_connection_window_slice_from_arguments``
    applies the identical coercion). Without this, ``a: books(first: 2)`` +
    ``b: books(first: $n)`` with ``n = 2`` would spuriously classify as
    divergent and pay a second identical window query. Only ``first`` /
    ``last`` are coerced; every other argument compares verbatim.
    """
    if "first" not in payload and "last" not in payload:
        return payload
    normalized = dict(payload)
    for bound in ("first", "last"):
        if bound in normalized:
            normalized[bound] = _coerce_pagination_int(normalized[bound])
    return normalized


def _response_key_arguments_conflict(selection: Any) -> bool:
    """Return whether one response key carries two DIFFERENT argument payloads.

    Set by ``_record_response_key_arguments`` when parent-alias subtrees were
    union-merged (the only reachable source - graphql-core validation rules
    the shape out within one selection set). Selections built outside
    ``_merge_aliased_selections`` never carry the flag.
    """
    return getattr(selection, "_optimizer_response_key_argument_conflict", False)


def _aliased_arguments_diverge(selection: Any) -> bool:
    """Return whether a merged selection's aliases carry divergent arguments.

    ``True`` when two response keys of the same field were selected with
    different argument payloads (e.g. ``a: books(first: 2)`` +
    ``b: books(first: 5)``). The scheme selector for
    ``_plan_connection_relation``: divergent aliases plan one window PER
    RESPONSE KEY (each under its own ``to_attr``; idea #2), while agreeing
    aliases share the single legacy window. Payloads compare
    pagination-normalized (``_normalized_alias_payload``) so the literal
    ``first: 2`` and a variable resolving to ``2`` agree. Selections built
    outside ``_merge_aliased_selections`` (direct test/helper callers) carry
    no per-response-key map and never diverge.
    """
    per_key = getattr(selection, "_optimizer_response_key_arguments", None)
    if not per_key:
        return False
    payloads = [_normalized_alias_payload(payload) for payload in per_key.values()]
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
    """Delegate one normalized nested connection and atomically merge its result."""
    result = _plan_nested_connection_relation(
        sel,
        definition,
        relation_field_name=relation_field_name,
        field_map=field_map,
        prefix=prefix,
        info=info,
        runtime_prefixes=runtime_prefixes,
        type_cls=type_cls,
        model=model,
        enable_only=enable_only,
        resolve_optimizer_hints=_resolve_optimizer_hints,
        resolve_relation_target=_resolve_relation_target,
        response_key_arguments_conflict=_response_key_arguments_conflict,
        aliased_arguments_diverge=_aliased_arguments_diverge,
        target_has_custom_get_queryset=_target_has_custom_get_queryset,
        resolver_identities_for=_resolver_identities_for,
        build_child_queryset=_build_child_queryset,
        build_prefetch_child_queryset_from_base=_build_prefetch_child_queryset_from_base,
    )
    plan.merge_from(result.plan)
