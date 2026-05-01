"""Selection-tree walker — ``spec-optimizer.md`` O2.

Pure function ``plan_optimizations(selected_fields, model)`` that walks
the GraphQL selection tree once, mapping each relation selection to an
optimizer directive (``select_related`` or ``prefetch_related``) and
each scalar selection to an ``only()`` column. The output is an
``OptimizationPlan`` consumed by ``DjangoOptimizerExtension`` in
``optimizer/extension.py``.

Design notes (from the spec):

- **Top-level walk, not per-resolver.** The walker runs once at
  ``on_executing_start`` (O3) and produces a complete plan for the
  entire selection tree. Per-resolver hooks cannot emit nested prefetch
  chains because the outer queryset is already evaluated by the time
  inner resolvers fire.
- **Pure function.** The walker is stateless — it takes a selection list
  and a Django model, returns a plan. This keeps it unit-testable with
  synthetic selection objects, no Strawberry execution required.
- **Recursive.** Nested selections descend through relation fields;
  each level contributes to the plan's prefetch chain. O4 extends the
  base O2 walker to emit ``Prefetch("items", queryset=...)`` style
  nested chains.

Three load-bearing details (see spec-optimizer.md O2 section):

1. **Fragments** — named (``...FragmentName``) and inline
   (``... on TypeName``). The walker descends into fragment selections
   recursively and merges them as if they were direct children.
2. **Aliases** — normalize on ``selection.name`` (the underlying field
   name), not the alias. Merge selection sets for aliased duplicates.
3. **``@skip`` / ``@include`` directives** — skip-marked selections are
   excluded; unresolved variables are treated as "selected" to avoid
   silently dropping prefetches.

Strawberry's ``info.selected_fields`` exposes three node types
(defined in ``strawberry.types.nodes``):

- ``SelectedField`` — ``name``, ``alias``, ``directives``, ``arguments``,
  ``selections``. Directives are a ``dict[str, dict[str, Any]]`` where
  values are already resolved (variables substituted at build time).
- ``FragmentSpread`` — ``name``, ``type_condition``, ``directives``,
  ``selections``. No ``alias``.
- ``InlineFragment`` — ``type_condition``, ``selections``, ``directives``.
  No ``name``, no ``alias``.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db import models
from django.db.models import Prefetch

from ..registry import registry
from ..utils.strings import snake_case
from .hints import OptimizerHint
from .plans import OptimizationPlan

logger = logging.getLogger("django_strawberry_framework")


def plan_optimizations(
    selected_fields: list[Any],
    model: type[models.Model],
    info: Any | None = None,
) -> OptimizationPlan:
    """Walk the selection tree and produce an ``OptimizationPlan``.

    Args:
        selected_fields: The root selections from ``info.selected_fields``.
            Typically ``info.selected_fields[0].selections`` when called
            from the extension (the ``[0]`` peels the root query field).
        model: The Django model backing the root queryset.

    Returns:
        An ``OptimizationPlan`` ready to be applied to the root queryset
        via ``plan.apply(queryset)``.
    """
    plan = OptimizationPlan()
    _walk_selections(selected_fields, model, plan, info=info)
    return plan


def plan_relation(
    field: Any,
    target_type: type | None,
    info: Any | None,
) -> tuple[str, Any]:
    """Plan one relation traversal.

    Returns ``("select", field_name)`` for a normal single-valued join
    or ``("prefetch", lookup)`` for many-side relations and O6
    visibility-aware downgrades. When the registered target
    ``DjangoType`` overrides ``get_queryset``, the lookup is a
    ``Prefetch`` object whose queryset has passed through that hook.
    """
    if target_type is not None and target_type.has_custom_get_queryset():
        target_qs = field.related_model._default_manager.all()
        target_qs = target_type.get_queryset(target_qs, info)
        logger.debug(
            "Optimizer: downgraded %s to Prefetch because %s overrides get_queryset.",
            field.name,
            target_type.__name__,
        )
        return ("prefetch", Prefetch(field.name, queryset=target_qs))
    if field.many_to_many or field.one_to_many:
        return ("prefetch", field.name)
    return ("select", field.name)


def _walk_selections(
    selections: list[Any],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
    info: Any | None = None,
) -> None:
    """Recursive workhorse: descend one level of the selection tree.

    Args:
        selections: The selections at this level (children of the
            parent field or fragment).
        model: The Django model at this level.
        plan: The mutable plan being accumulated.
        prefix: The dotted path prefix for nested chains (e.g.
            ``"items__"`` when walking ``Category > items > ...``).
            Empty at the root level.
    """
    # B7: read precomputed _optimizer_field_map when available;
    # fall back to _meta.get_fields() for unregistered models.
    type_cls = registry.get(model)
    cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
    field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
    merged = _merge_aliased_selections(selections)
    for sel in merged:
        if not _should_include(sel):
            continue
        if _is_fragment(sel):
            _walk_selections(sel.selections, model, plan, prefix, info)
            continue
        django_name = snake_case(sel.name)
        django_field = field_map.get(django_name)
        if django_field is None:
            continue
        if not django_field.is_relation:
            _append_unique(plan.only_fields, f"{prefix}{django_name}")
            continue
        # B4: consult optimizer_hints before cardinality dispatch.
        hint = getattr(type_cls, "_optimizer_hints", {}).get(django_name) if type_cls is not None else None
        if hint is not None:
            if hint is OptimizerHint.SKIP or hint.skip:
                continue
            full_path = f"{prefix}{django_name}"
            if hint.prefetch_obj is not None:
                if django_field.attname is not None:
                    _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
                plan.prefetch_related.append(hint.prefetch_obj)
                continue
            if hint.force_select:
                if django_field.attname is not None:
                    _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
                if django_field.related_model is not None:
                    _collect_scalar_only_fields(
                        sel.selections,
                        django_field.related_model,
                        plan,
                        prefix=f"{full_path}__",
                    )
                plan.select_related.append(full_path)
                continue
            if hint.force_prefetch:
                if django_field.attname is not None:
                    _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
                plan.prefetch_related.append(full_path)
                continue
        # Relation dispatch by cardinality.
        full_path = f"{prefix}{django_name}"
        target_type = (
            registry.get(django_field.related_model) if django_field.related_model is not None else None
        )
        relation_kind, relation_lookup = plan_relation(django_field, target_type, info)
        if relation_kind == "prefetch":
            if django_field.attname is not None:
                _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
            if target_type is not None and target_type.has_custom_get_queryset():
                plan.cacheable = False
            plan.prefetch_related.append(
                full_path if relation_lookup == django_name else relation_lookup,
            )
        else:
            if django_field.attname is not None:
                _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
            target_pk_name = _target_pk_name(django_field)
            if (
                _can_elide_fk_id(django_field)
                and not (target_type is not None and target_type.has_custom_get_queryset())
                and not _has_custom_id_resolver(target_type, target_pk_name)
                and _selected_scalar_names(sel.selections, django_field.related_model) == {target_pk_name}
            ):
                _append_unique(plan.fk_id_elisions, full_path)
                continue
            if django_field.related_model is not None:
                _collect_scalar_only_fields(
                    sel.selections,
                    django_field.related_model,
                    plan,
                    prefix=f"{full_path}__",
                )
            plan.select_related.append(full_path)
        # TODO(spec-optimizer.md O4): recurse into sel.selections to
        # build nested Prefetch chains for depth > 1.


def _collect_scalar_only_fields(
    selections: list[Any],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
) -> None:
    """Collect scalar child selections for ``only()`` without planning relations.

    O5 is allowed to project columns across ``select_related`` joins
    using Django's ``relation__column`` syntax. This helper walks only
    scalar selections under a single-valued relation and leaves nested
    relation planning to O4.
    """
    type_cls = registry.get(model)
    cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
    field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
    merged = _merge_aliased_selections(selections)
    for sel in merged:
        if not _should_include(sel):
            continue
        if _is_fragment(sel):
            _collect_scalar_only_fields(sel.selections, model, plan, prefix)
            continue
        django_name = snake_case(sel.name)
        django_field = field_map.get(django_name)
        if django_field is not None and not django_field.is_relation:
            _append_unique(plan.only_fields, f"{prefix}{django_name}")


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
    for sel in _merge_aliased_selections(selections):
        if not _should_include(sel):
            continue
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


def _append_unique(values: list[str], value: str) -> None:
    """Append ``value`` to ``values`` if it is not already present."""
    if value not in values:
        values.append(value)


def _should_include(selection: Any) -> bool:
    """Evaluate ``@skip`` / ``@include`` directives on a selection.

    Returns ``False`` when the selection should be excluded from the
    plan. Treats unresolved or non-boolean values as "selected" to
    avoid silently dropping prefetches the consumer needed.

    Strawberry resolves directive arguments (including variable
    substitution) at ``convert_directives`` time, so ``directives``
    is a ``dict[str, dict[str, Any]]`` with concrete values by the
    time the walker sees it.
    """
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
    """Merge selections that alias the same underlying field.

    A query like ``{ first: items { id } second: items { name } }``
    produces two ``SelectedField`` nodes both with ``name="items"``
    but different ``alias`` values. The walker normalizes on
    ``snake_case(sel.name)`` (the Django field name) and merges their
    child selection lists so the plan emits one optimizer directive per
    field, not one per alias.

    Fragment nodes (``FragmentSpread``, ``InlineFragment``) do not have
    aliases and pass through unchanged.

    Returns a deduplicated list where aliased duplicates have their
    ``selections`` children merged.
    """
    seen: dict[str, Any] = {}
    result: list[Any] = []
    for sel in selections:
        if _is_fragment(sel):
            result.append(sel)
            continue
        key = snake_case(sel.name)
        if key in seen:
            # Merge child selections into the first occurrence.
            seen[key].selections = list(seen[key].selections) + list(sel.selections)
        else:
            seen[key] = sel
            result.append(sel)
    return result


def _is_fragment(selection: Any) -> bool:
    """Return ``True`` if the selection is a fragment spread or inline fragment.

    Detection: Strawberry's ``SelectedField`` always carries an
    ``arguments`` attribute. Both ``FragmentSpread`` and
    ``InlineFragment`` carry ``type_condition`` instead. Checking for
    ``type_condition`` cleanly separates the two families.
    """
    return hasattr(selection, "type_condition")
