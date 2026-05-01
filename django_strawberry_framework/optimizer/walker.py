"""Selection-tree walker — ``spec-optimizer.md`` O2/O4."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

from django.db import models
from django.db.models import Prefetch

from ..registry import registry
from ..utils.strings import snake_case
from .hints import OptimizerHint
from .plans import OptimizationPlan, resolver_key, runtime_path_from_info

logger = logging.getLogger("django_strawberry_framework")


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
    return plan


def plan_relation(
    field: Any,
    target_type: type | None,
    info: Any | None,
) -> tuple[str, str]:
    """Return relation traversal kind without constructing querysets."""
    if target_type is not None and target_type.has_custom_get_queryset():
        logger.debug(
            "Optimizer: will downgrade %s to Prefetch because %s overrides get_queryset.",
            field.name,
            target_type.__name__,
        )
        return ("prefetch", "custom_get_queryset")
    if field.many_to_many or field.one_to_many:
        return ("prefetch", "default")
    return ("select", "default")


def _build_child_queryset(field: Any, target_type: type | None, info: Any | None) -> Any:
    """Build the queryset used inside a generated ``Prefetch`` object."""
    queryset = field.related_model._default_manager.all()
    if target_type is not None and target_type.has_custom_get_queryset():
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
    """Recursive workhorse: descend one level of the selection tree."""
    type_cls = registry.get(model)
    cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
    field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
    merged = _merge_aliased_selections([sel for sel in selections if _should_include(sel)])
    for sel in merged:
        if _is_fragment(sel):
            _walk_selections(
                sel.selections,
                model,
                plan,
                prefix=prefix,
                info=info,
                runtime_prefixes=runtime_prefixes,
            )
            continue
        django_name = snake_case(sel.name)
        django_field = field_map.get(django_name)
        if django_field is None:
            continue
        if not django_field.is_relation:
            _append_unique(plan.only_fields, f"{prefix}{django_name}")
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

        hint = getattr(type_cls, "_optimizer_hints", {}).get(django_name) if type_cls is not None else None
        if hint is not None:
            if hint is OptimizerHint.SKIP or hint.skip:
                continue
            if hint.prefetch_obj is not None:
                attname = getattr(django_field, "attname", None)
                if attname is not None:
                    _append_unique(plan.only_fields, f"{prefix}{attname}")
                _append_unique_many(plan.planned_resolver_keys, resolver_identities)
                plan.prefetch_related.append(hint.prefetch_obj)
                continue
            if hint.force_select:
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
                continue
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
                continue

        relation_kind, _reason = plan_relation(django_field, target_type, info)
        if relation_kind == "prefetch":
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
    attname = getattr(django_field, "attname", None)
    if attname is not None:
        _append_unique(plan.only_fields, f"{prefix}{attname}")
    target_pk_name = _target_pk_name(django_field)
    if (
        _can_elide_fk_id(django_field)
        and not (target_type is not None and target_type.has_custom_get_queryset())
        and not _has_custom_id_resolver(target_type, target_pk_name)
        and _selected_scalar_names(sel.selections, django_field.related_model) == {target_pk_name}
    ):
        _append_unique_many(plan.fk_id_elisions, resolver_identities)
        _append_unique_many(plan.planned_resolver_keys, resolver_identities)
        return
    _append_unique_many(plan.planned_resolver_keys, resolver_identities)
    _append_unique(plan.select_related, full_path)
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
    attname = getattr(django_field, "attname", None)
    if attname is not None:
        _append_unique(plan.only_fields, f"{prefix}{attname}")
    _append_unique_many(plan.planned_resolver_keys, resolver_identities)
    has_custom_get_queryset = target_type is not None and target_type.has_custom_get_queryset()
    if has_custom_get_queryset:
        plan.cacheable = False
    if django_field.related_model is None:
        _append_unique(plan.prefetch_related, full_path)
        return

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
    _merge_child_plan_metadata(plan, child_plan)
    if not child_plan.cacheable:
        plan.cacheable = False
    if child_plan.is_empty and not has_custom_get_queryset:
        _append_unique(plan.prefetch_related, full_path)
        return
    child_queryset = child_plan.apply(_build_child_queryset(django_field, target_type, info))
    plan.prefetch_related.append(Prefetch(full_path, queryset=child_queryset))


def _merge_child_plan_metadata(parent_plan: OptimizationPlan, child_plan: OptimizationPlan) -> None:
    """Propagate resolver metadata from a child queryset plan to the root plan."""
    for key in child_plan.fk_id_elisions:
        _append_unique(parent_plan.fk_id_elisions, key)
    for key in child_plan.planned_resolver_keys:
        _append_unique(parent_plan.planned_resolver_keys, key)


def _selected_scalar_names(
    selections: list[Any],
    model: type[models.Model] | None,
) -> set[str] | None:
    """Return selected scalar Django field names, or ``None`` when elision is unsafe."""
    if model is None:
        return None
    type_cls = registry.get(model)
    cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
    field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
    scalar_names: set[str] = set()
    for sel in _merge_aliased_selections([sel for sel in selections if _should_include(sel)]):
        if _is_fragment(sel):
            nested = _selected_scalar_names(sel.selections, model)
            if nested is None:
                return None
            scalar_names.update(nested)
            continue
        django_name = snake_case(sel.name)
        django_field = field_map.get(django_name)
        if django_field is None or django_field.is_relation:
            return None
        scalar_names.add(django_name)
    return scalar_names


def _can_elide_fk_id(field: Any) -> bool:
    """Return ``True`` when ``field`` stores the related object's id on the source row."""
    related_model = getattr(field, "related_model", None)
    target_pk_name = _target_pk_name(field)
    target_field = getattr(field, "target_field", None)
    target_field_name = (
        getattr(target_field, "name", None)
        if target_field is not None
        else getattr(field, "target_field_name", None)
    )
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
    if parent_field.one_to_many:
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
        _append_unique(plan.only_fields, attname)
        return
    logger.debug(
        "Optimizer: could not resolve connector column for Prefetch %s; only() may be less precise.",
        getattr(parent_field, "name", parent_field),
    )


def _append_unique(values: list[Any], value: Any) -> None:
    """Append ``value`` to ``values`` if it is not already present."""
    if value not in values:
        values.append(value)


def _append_unique_many(values: list[Any], new_values: tuple[Any, ...]) -> None:
    """Append each value in ``new_values`` if it is not already present."""
    for value in new_values:
        _append_unique(values, value)


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


def _merge_aliased_selections(selections: list[Any]) -> list[Any]:
    """Merge selections that alias the same underlying field while preserving response keys."""
    seen: dict[str, Any] = {}
    result: list[Any] = []
    for sel in selections:
        if _is_fragment(sel):
            result.append(sel)
            continue
        key = snake_case(sel.name)
        if key in seen:
            merged = seen[key]
            merged.selections = list(merged.selections) + list(sel.selections)
            response_key = _response_key(sel)
            if response_key not in merged._optimizer_response_keys:
                merged._optimizer_response_keys.append(response_key)
        else:
            merged = SimpleNamespace(
                name=sel.name,
                alias=getattr(sel, "alias", None),
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
