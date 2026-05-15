"""Selection-tree walker for ORM optimization plans."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from django.db import models
from django.db.models import Prefetch
from strawberry import relay

from ..exceptions import ConfigurationError
from ..registry import registry
from ..utils.relations import is_many_side_relation_kind, relation_kind
from ..utils.strings import snake_case
from . import logger
from .hints import OptimizerHint, hint_is_skip
from .plans import (
    OptimizationPlan,
    append_prefetch_unique,
    append_unique,
    append_unique_many,
    resolver_key,
    runtime_path_from_info,
)


def plan_optimizations(
    selected_fields: list[Any],
    model: type[models.Model],
    info: Any | None = None,
) -> OptimizationPlan:
    """Walk the selection tree and produce an ``OptimizationPlan``."""
    plan = OptimizationPlan()
    _walk_selections(
        selected_fields,
        model,
        plan,
        info=info,
        runtime_prefixes=(runtime_path_from_info(info),),
    )
    # Finalise at handoff: list fields become tuples so post-walker
    # mutation (by callers, the plan cache, or downstream resolvers)
    # raises ``AttributeError`` instead of silently corrupting the
    # cached plan for subsequent requests.
    return plan.finalize()


def plan_relation(
    field: Any,
    target_type: type | None,
    info: Any | None,
) -> tuple[str, str]:
    """Return relation traversal kind without constructing querysets."""
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


def _resolve_field_map(model: type[models.Model]) -> tuple[type | None, dict[str, Any]]:
    """Return ``(registered DjangoType, field_map)`` for ``model``.

    Prefers the precomputed ``_optimizer_field_map`` cached on the
    ``DjangoType`` subclass; falls back to a fresh
    ``model._meta.get_fields()`` walk when the model has no registered
    type.  Centralizes the brittle Django-private ``_meta`` access used
    by the walker.
    """
    type_cls = registry.get(model)
    # TODO(spec-fieldmeta-mirror-retirement): once the one-minor compatibility
    # mirror from ``DjangoTypeDefinition.field_map`` to
    # ``type_cls._optimizer_field_map`` is removed, read through
    # ``registry.get_definition(type_cls)`` here instead of the legacy class
    # attribute.
    cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
    field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
    return type_cls, field_map


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
    """
    queryset = field.related_model._default_manager.all()
    if has_custom_qs:
        queryset = target_type.get_queryset(queryset, info)
    return queryset


def _walk_selections(
    selections: list[Any],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
    info: Any | None = None,
    runtime_prefixes: tuple[tuple[str, ...], ...] = ((),),
) -> None:
    """Recursive workhorse: descend one normalized level of the selection tree."""
    type_cls, field_map = _resolve_field_map(model)
    merged = _merge_aliased_selections(_included_field_selections(selections))
    for sel in merged:
        django_name = snake_case(sel.name)
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
                if db_field is not None:
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
            append_unique(plan.only_fields, f"{prefix}{django_name}")
            continue

        full_path = f"{prefix}{django_name}"
        runtime_paths = tuple(
            (*runtime_prefix, response_key)
            for runtime_prefix in runtime_prefixes
            for response_key in _response_keys(sel)
        )
        resolver_identities = tuple(
            resolver_key(type_cls, django_name, runtime_path) for runtime_path in runtime_paths
        )
        target_type = (
            registry.get(django_field.related_model) if django_field.related_model is not None else None
        )

        # TODO(spec-fieldmeta-mirror-retirement): after the compatibility
        # mirror is removed, read optimizer hints from
        # ``registry.get_definition(type_cls)`` instead of the legacy
        # ``_optimizer_hints`` class attribute.
        hints_map = getattr(type_cls, "_optimizer_hints", None) or {} if type_cls is not None else {}
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
        ):
            continue

        relation_plan_kind, _ = plan_relation(django_field, target_type, info)
        if relation_plan_kind == "prefetch":
            _plan_prefetch_relation(
                sel,
                django_field,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )
        else:
            _plan_select_relation(
                sel,
                django_field,
                django_name,
                type_cls,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )


def _plan_select_relation(
    sel: Any,
    django_field: Any,
    django_name: str,
    parent_type: type | None,
    target_type: type | None,
    plan: OptimizationPlan,
    prefix: str,
    full_path: str,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
) -> None:
    """Plan a same-query single-valued relation traversal."""
    _record_relation_access(plan, django_field, prefix, resolver_identities)
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
    if django_field.related_model is not None:
        _walk_selections(
            sel.selections,
            django_field.related_model,
            plan,
            prefix=f"{full_path}__",
            info=info,
            runtime_prefixes=runtime_paths,
        )


def _plan_prefetch_relation(
    sel: Any,
    django_field: Any,
    target_type: type | None,
    plan: OptimizationPlan,
    prefix: str,
    full_path: str,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
) -> None:
    """Plan a queryset-boundary relation traversal with optional child optimization."""
    _record_relation_access(plan, django_field, prefix, resolver_identities)
    has_custom_get_queryset = _target_has_custom_get_queryset(target_type)
    if has_custom_get_queryset:
        plan.cacheable = False
    if django_field.related_model is None:
        append_unique(plan.prefetch_related, full_path)
        return

    child_queryset = _build_prefetch_child_queryset(
        sel,
        django_field,
        target_type,
        plan,
        info,
        runtime_paths,
        has_custom_get_queryset=has_custom_get_queryset,
    )
    append_prefetch_unique(plan.prefetch_related, Prefetch(full_path, queryset=child_queryset))


def _record_relation_access(
    plan: OptimizationPlan,
    django_field: Any,
    prefix: str,
    resolver_identities: tuple[str, ...],
) -> None:
    """Record the shared connector and resolver metadata for a relation."""
    attname = getattr(django_field, "attname", None)
    if attname is not None:
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
) -> Any:
    """Build and optimize the child queryset for a generated ``Prefetch``."""
    child_plan = OptimizationPlan()
    _walk_selections(
        sel.selections,
        django_field.related_model,
        child_plan,
        prefix="",
        info=info,
        runtime_prefixes=runtime_paths,
    )
    _ensure_connector_only_fields(child_plan, django_field)
    _merge_child_plan_metadata(parent_plan, child_plan)
    if not child_plan.cacheable:
        parent_plan.cacheable = False
    child_queryset = child_plan.apply(
        _build_child_queryset(django_field, target_type, info, has_custom_qs=has_custom_get_queryset),
    )
    return child_queryset


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
) -> bool:
    """Apply a Meta-level ``OptimizerHint`` to ``plan``; return ``True`` when handled.

    Dispatches the four documented hint shapes (``SKIP``, ``prefetch_obj``,
    ``force_select``, ``force_prefetch``) and returns ``True`` after the
    matching action has been taken.  Returns ``False`` for hints that
    set no flag — the caller falls back to the default cardinality
    dispatch in that case.  ``OptimizerHint.__post_init__`` already
    rejects conflicting flag combinations, so the priority order here
    is documentation, not collision arbitration.
    """
    if hint_is_skip(hint):
        return True
    if hint.prefetch_obj is not None:
        _record_relation_access(plan, django_field, prefix, resolver_identities)
        # Consumer-supplied Prefetch objects commonly close over a queryset
        # built with request- or user-scoped filters; matching the
        # has_custom_get_queryset discipline in _plan_prefetch_relation, mark
        # the plan non-cacheable so the plan cache cannot serve one
        # request's queryset to the next.
        plan.cacheable = False
        append_prefetch_unique(
            plan.prefetch_related,
            _prefetch_hint_for_path(hint.prefetch_obj, django_name=django_name, full_path=full_path),
        )
        return True
    if hint.force_select:
        if _target_has_custom_get_queryset(target_type):
            _plan_prefetch_relation(
                sel,
                django_field,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )
        else:
            _plan_select_relation(
                sel,
                django_field,
                django_name,
                type_cls,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )
        return True
    if hint.force_prefetch:
        _plan_prefetch_relation(
            sel,
            django_field,
            target_type,
            plan,
            prefix,
            full_path,
            info,
            runtime_paths,
            resolver_identities,
        )
        return True
    return False


def _prefetch_hint_for_path(prefetch: Prefetch, *, django_name: str, full_path: str) -> Prefetch:
    """Return ``prefetch`` adapted from a type-relative lookup to ``full_path``."""
    lookup = getattr(prefetch, "prefetch_through", None)
    if lookup is None:
        raise ConfigurationError("OptimizerHint.prefetch(obj) requires a Prefetch with a lookup path.")
    if lookup == full_path or lookup.startswith(f"{full_path}__"):
        return prefetch
    if lookup == django_name:
        adjusted_lookup = full_path
    elif lookup.startswith(f"{django_name}__"):
        adjusted_lookup = f"{full_path}{lookup.removeprefix(django_name)}"
    else:
        raise ConfigurationError(
            "OptimizerHint.prefetch(obj) lookup must target the hinted relation "
            f"{django_name!r}; got {lookup!r}.",
        )
    return Prefetch(
        adjusted_lookup,
        queryset=prefetch.queryset,
        to_attr=getattr(prefetch, "to_attr", None),
    )


def _merge_child_plan_metadata(parent_plan: OptimizationPlan, child_plan: OptimizationPlan) -> None:
    """Propagate resolver metadata from a child queryset plan to the root plan."""
    for key in child_plan.fk_id_elisions:
        append_unique(parent_plan.fk_id_elisions, key)
    for key in child_plan.planned_resolver_keys:
        append_unique(parent_plan.planned_resolver_keys, key)


def _selected_scalar_names(
    selections: list[Any],
    model: type[models.Model] | None,
) -> set[str] | None:
    """Return selected scalar Django field names, or ``None`` when elision is unsafe."""
    if model is None:
        return None
    _type_cls, field_map = _resolve_field_map(model)
    scalar_names: set[str] = set()
    for sel in _merge_aliased_selections(_included_field_selections(selections)):
        django_name = snake_case(sel.name)
        django_field = field_map.get(django_name)
        if django_field is None or django_field.is_relation:
            return None
        scalar_names.add(django_name)
    return scalar_names


def _can_elide_fk_id(field: Any) -> bool:
    """Return ``True`` when ``field`` stores the related object's id on the source row.

    Composite primary keys (Django 5.2+) are excluded: the source-row
    ``attname`` carries a single column id, but the target's ``pk`` is
    a tuple, so eliding would compare the wrong shapes and surface
    wrong data.
    """
    related_model = getattr(field, "related_model", None)
    target_pk_name = _target_pk_name(field)
    target_field = getattr(field, "target_field", None)
    target_field_name = (
        getattr(target_field, "name", None)
        if target_field is not None
        else getattr(field, "target_field_name", None)
    )
    pk_fields = getattr(related_model._meta, "pk_fields", None) if related_model is not None else None
    if pk_fields is not None and len(pk_fields) > 1:  # pragma: no cover
        # Composite primary key (Django 5.2+).  Test fixtures do not
        # define one; the guard exists so the elision branch fails
        # closed if a consumer adopts composite PKs.
        return False
    return (
        field.attname is not None
        and related_model is not None
        and target_pk_name is not None
        and target_field_name == target_pk_name
        and not field.many_to_many
        and not field.one_to_many
        and not getattr(field, "auto_created", False)
    )


def _target_pk_name(field: Any) -> str | None:
    """Return the related model's concrete primary-key field name."""
    related_model = getattr(field, "related_model", None)
    if related_model is None:
        return None
    return related_model._meta.pk.name


def _has_custom_id_resolver(target_type: type | None, target_pk_name: str | None) -> bool:
    """Return ``True`` when target type customizes the selected id field."""
    if target_type is None or target_pk_name is None:
        return False
    resolver_names = (target_pk_name, f"resolve_{target_pk_name}")
    return any(
        name in getattr(cls, "__dict__", {})
        for cls in getattr(target_type, "__mro__", ())
        for name in resolver_names
    )


def _ensure_connector_only_fields(plan: OptimizationPlan, parent_field: Any) -> None:
    """Inject columns Django needs to attach prefetched rows to parents."""
    if not plan.only_fields:
        return
    kind = relation_kind(parent_field)
    if parent_field.one_to_many or kind == "reverse_one_to_one":
        attname = getattr(getattr(parent_field, "field", None), "attname", None) or getattr(
            parent_field,
            "reverse_connector_attname",
            None,
        )
    elif not parent_field.many_to_many:
        attname = getattr(getattr(parent_field, "target_field", None), "attname", None) or getattr(
            parent_field,
            "target_field_attname",
            None,
        )
    else:
        attname = parent_field.related_model._meta.pk.attname
    if attname is not None:
        append_unique(plan.only_fields, attname)
        return
    logger.debug(
        "Optimizer: could not resolve connector column for Prefetch %s; only() may be less precise.",
        getattr(parent_field, "name", parent_field),
    )


def _should_include(selection: Any) -> bool:
    """Evaluate ``@skip`` / ``@include`` directives on a selection."""
    directives = getattr(selection, "directives", None) or {}
    skip = directives.get("skip")
    if skip is not None:
        value = skip.get("if")
        if value is True:
            return False
    include = directives.get("include")
    if include is not None:
        value = include.get("if")
        if value is False:
            return False
    return True


def _included_field_selections(selections: list[Any]) -> list[Any]:
    """Return included fields with fragment bodies inlined before field merging.

    Directive filtering happens on both fragment nodes and their nested field
    selections. Returning a flat field list lets alias/relation merging combine
    duplicate relation branches before generated child ``Prefetch`` querysets
    are built.
    """
    result: list[Any] = []
    for selection in selections:
        if not _should_include(selection):
            continue
        if _is_fragment(selection):
            result.extend(_included_field_selections(list(getattr(selection, "selections", None) or [])))
            continue
        result.append(selection)
    return result


def _merge_aliased_selections(selections: list[Any]) -> list[Any]:
    """Merge same-field selections while preserving all represented response keys.

    The main walker path passes fragment-inlined field selections here, so
    duplicate relation branches are combined before planning. The fragment
    passthrough below is retained for defensive direct helper use.
    """
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
            merged.selections = list(merged.selections) + list(getattr(sel, "selections", None) or [])
            response_key = _response_key(sel)
            if response_key not in merged._optimizer_response_keys:
                merged._optimizer_response_keys.append(response_key)
            # Forward-compat signal: today's walker ignores ``arguments``,
            # so divergent arguments between aliased selections are
            # harmless.  When a future slice plans differently per
            # argument set this branch will need to plan per-response-key
            # instead of merging — emitting at DEBUG level here gives
            # that author a fast trace without changing current
            # behaviour.
            sel_arguments = getattr(sel, "arguments", None) or {}
            if sel_arguments != merged.arguments:
                logger.debug(
                    "Optimizer: aliased selections of %s carry different arguments; "
                    "merge keeps the first occurrence's values.",
                    sel.name,
                )
        else:
            merged = SimpleNamespace(
                name=sel.name,
                alias=getattr(sel, "alias", None),
                # The walker filters directives before merging and does not
                # inspect arguments. If future optimizer slices use arguments,
                # this merge must become per-response-key instead of keeping
                # only the first occurrence's values.
                directives=getattr(sel, "directives", None) or {},
                arguments=getattr(sel, "arguments", None) or {},
                selections=list(getattr(sel, "selections", None) or []),
                _optimizer_response_keys=[_response_key(sel)],
            )
            seen[key] = merged
            result.append(merged)
    return result


def _response_key(selection: Any) -> str:
    """Return the GraphQL response key for a field selection."""
    return getattr(selection, "alias", None) or selection.name


def _response_keys(selection: Any) -> tuple[str, ...]:
    """Return all response keys represented by a possibly merged selection."""
    return tuple(getattr(selection, "_optimizer_response_keys", None) or (_response_key(selection),))


def _is_fragment(selection: Any) -> bool:
    """Return ``True`` if the selection is a fragment spread or inline fragment."""
    return hasattr(selection, "type_condition")
