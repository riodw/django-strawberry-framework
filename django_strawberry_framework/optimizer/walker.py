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

from typing import Any

from django.db import models

from ..registry import registry
from ..utils.strings import snake_case
from .hints import OptimizerHint
from .plans import OptimizationPlan


def plan_optimizations(
    selected_fields: list[Any],
    model: type[models.Model],
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
    _walk_selections(selected_fields, model, plan)
    return plan


def _walk_selections(
    selections: list[Any],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
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
            _walk_selections(sel.selections, model, plan, prefix)
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
        if django_field.many_to_many or django_field.one_to_many:
            plan.prefetch_related.append(full_path)
        else:
            if django_field.attname is not None:
                _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
            if django_field.related_model is not None:
                _collect_scalar_only_fields(
                    sel.selections,
                    django_field.related_model,
                    plan,
                    prefix=f"{full_path}__",
                )
            # TODO(spec-optimizer_beyond.md B2): before emitting
            # ``select_related``, check whether the only child
            # selections on the FK target are columns already
            # available on the source row (e.g. ``{"id"}`` maps to
            # ``field.attname``). If so, elide the JOIN and add
            # ``field.attname`` to ``plan.only_fields`` instead.
            # Guard: skip elision when the target type has a custom
            # ``get_queryset`` (needs the JOIN for visibility).
            # Applies to forward FK (many_to_one) and forward
            # OneToOne (non-auto-created one_to_one).
            #
            # Pseudo:
            #   child_scalars = {snake_case(c.name)
            #                   for c in sel.selections
            #                   if not _is_fragment(c)}
            #   target_type = registry.get(
            #       django_field.related_model)
            #   if (child_scalars == {"id"}
            #           and not (target_type
            #                    and target_type
            #                    .has_custom_get_queryset())):
            #       plan.only_fields.append(
            #           django_field.attname)
            #       continue
            # TODO(spec-optimizer.md O6): check whether the target type
            # overrides get_queryset and downgrade select_related to
            # Prefetch when it does.
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
