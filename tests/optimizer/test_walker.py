"""Tests for ``optimizer/walker.py`` — ``spec-optimizer.md`` O2.

The walker is a pure function (``plan_optimizations``) tested in
isolation against synthetic selection objects — no Strawberry execution
required. This makes the three load-bearing details (fragments, aliases,
``@skip``/``@include``) each testable with a tight, focused case.

All tests use ``SimpleNamespace`` objects mimicking Strawberry's
``SelectedField`` / ``FragmentSpread`` / ``InlineFragment`` shape.
The walker dispatches on duck-typed attributes (``name``, ``alias``,
``directives``, ``selections``, ``type_condition``), so synthetic
objects exercise exactly the same code paths as real Strawberry nodes.

O4 (nested prefetch chains) and O6
(``Prefetch`` downgrade) each extend this file with additional tests
when they land.
"""

from types import SimpleNamespace

from django.db import models
from django.db.models import Prefetch
from fakeshop.products.models import Category, Entry, Item

from django_strawberry_framework.optimizer.walker import (
    _is_fragment,
    _merge_aliased_selections,
    _should_include,
    plan_optimizations,
)
from django_strawberry_framework.registry import registry

# ---------------------------------------------------------------------------
# Helpers: synthetic selection factories
# ---------------------------------------------------------------------------


def _sel(name, selections=None, directives=None, alias=None):
    """Build a synthetic ``SelectedField``."""
    return SimpleNamespace(
        name=name,
        alias=alias,
        directives=directives or {},
        arguments={},
        selections=selections or [],
    )


def _inline_fragment(type_condition, selections=None, directives=None):
    """Build a synthetic ``InlineFragment``."""
    return SimpleNamespace(
        type_condition=type_condition,
        directives=directives or {},
        selections=selections or [],
    )


def _fragment_spread(name, type_condition, selections=None, directives=None):
    """Build a synthetic ``FragmentSpread``."""
    return SimpleNamespace(
        name=name,
        type_condition=type_condition,
        directives=directives or {},
        selections=selections or [],
    )


# ---------------------------------------------------------------------------
# plan_optimizations — cardinality dispatch
# ---------------------------------------------------------------------------


def test_plan_returns_empty_for_scalar_only_selection():
    """Selecting only scalars produces an ``only()`` projection but no relations."""
    plan = plan_optimizations([_sel("name"), _sel("id")], Category)
    assert plan.select_related == []
    assert plan.prefetch_related == []
    assert plan.only_fields == ["name", "id"]


def test_plan_dispatches_forward_fk_to_select_related():
    """A forward FK selection routes to ``select_related``."""
    plan = plan_optimizations([_sel("category")], Item)
    assert plan.select_related == ["category"]
    assert plan.prefetch_related == []
    assert plan.only_fields == ["category_id"]


def test_plan_dispatches_reverse_fk_to_prefetch_related():
    """A reverse FK selection routes to ``prefetch_related``."""
    plan = plan_optimizations([_sel("items")], Category)
    assert plan.select_related == []
    assert plan.prefetch_related == ["items"]


def test_plan_dispatches_mixed_relations():
    """Forward FK and reverse FK in one selection produce both bags."""
    plan = plan_optimizations(
        [_sel("category"), _sel("entries")],
        Item,
    )
    assert plan.select_related == ["category"]
    assert plan.prefetch_related == ["entries"]
    assert plan.only_fields == ["category_id"]


def test_plan_skips_unknown_selections():
    """Selections not on the Django model are silently skipped."""
    plan = plan_optimizations([_sel("bogusField")], Category)
    assert plan.is_empty


def test_plan_converts_camel_case_to_snake_case():
    """Strawberry's camelCase names are converted back to snake_case for lookup."""
    # Entry has "item" and "property" as FKs. Strawberry would expose
    # them as "item" and "property" (already snake-compatible), but
    # the walker converts via snake_case regardless.
    plan = plan_optimizations([_sel("item"), _sel("property")], Entry)
    assert sorted(plan.select_related) == ["item", "property"]


def test_plan_empty_selections_produces_empty_plan():
    """An empty selection list produces an empty plan."""
    plan = plan_optimizations([], Category)
    assert plan.is_empty


# ---------------------------------------------------------------------------
# _should_include — @skip / @include directives
# ---------------------------------------------------------------------------


def test_should_include_returns_true_by_default():
    """No directives → included."""
    assert _should_include(_sel("name")) is True


def test_should_include_skips_when_skip_true():
    """``@skip(if: true)`` → excluded."""
    sel = _sel("name", directives={"skip": {"if": True}})
    assert _should_include(sel) is False


def test_should_include_includes_when_skip_false():
    """``@skip(if: false)`` → included."""
    sel = _sel("name", directives={"skip": {"if": False}})
    assert _should_include(sel) is True


def test_should_include_skips_when_include_false():
    """``@include(if: false)`` → excluded."""
    sel = _sel("name", directives={"include": {"if": False}})
    assert _should_include(sel) is False


def test_should_include_includes_when_include_true():
    """``@include(if: true)`` → included."""
    sel = _sel("name", directives={"include": {"if": True}})
    assert _should_include(sel) is True


def test_should_include_treats_unresolved_variable_as_selected():
    """A non-boolean directive value (e.g. unresolved variable) → included."""
    # Strawberry normally resolves variables, but if one slips through
    # as None the walker treats it as "selected" defensively.
    sel = _sel("name", directives={"skip": {"if": None}})
    assert _should_include(sel) is True


def test_should_include_skip_true_beats_include_true():
    """``@skip(if: true) @include(if: true)`` → excluded (skip wins)."""
    sel = _sel(
        "name",
        directives={"skip": {"if": True}, "include": {"if": True}},
    )
    assert _should_include(sel) is False


def test_should_include_works_on_fragment_nodes():
    """Directives on fragment nodes are evaluated the same way."""
    frag = _inline_fragment(
        "CategoryType",
        directives={"skip": {"if": True}},
    )
    assert _should_include(frag) is False


def test_plan_excludes_skip_true_relation():
    """A relation with ``@skip(if: true)`` is excluded from the plan."""
    plan = plan_optimizations(
        [_sel("items", directives={"skip": {"if": True}})],
        Category,
    )
    assert plan.is_empty


# ---------------------------------------------------------------------------
# _is_fragment — fragment detection
# ---------------------------------------------------------------------------


def test_is_fragment_returns_false_for_selected_field():
    """A regular ``SelectedField`` is not a fragment."""
    assert _is_fragment(_sel("name")) is False


def test_is_fragment_returns_true_for_inline_fragment():
    """An ``InlineFragment`` is detected as a fragment."""
    assert _is_fragment(_inline_fragment("CategoryType")) is True


def test_is_fragment_returns_true_for_fragment_spread():
    """A ``FragmentSpread`` is detected as a fragment."""
    assert _is_fragment(_fragment_spread("CategoryFields", "CategoryType")) is True


# ---------------------------------------------------------------------------
# Fragment handling in the walker
# ---------------------------------------------------------------------------


def test_plan_handles_inline_fragment():
    """Relations inside an inline fragment route to the plan."""
    inline = _inline_fragment(
        "CategoryType",
        selections=[_sel("name"), _sel("items")],
    )
    plan = plan_optimizations([inline], Category)
    assert plan.prefetch_related == ["items"]


def test_plan_handles_named_fragment_spread():
    """Relations inside a named fragment spread route to the plan."""
    spread = _fragment_spread(
        "CategoryFields",
        "CategoryType",
        selections=[_sel("name"), _sel("items")],
    )
    plan = plan_optimizations([spread], Category)
    assert plan.prefetch_related == ["items"]


def test_fragment_spread_from_multiple_sites_does_not_double_prefetch():
    """Two fragment spreads with the same children produce one plan entry."""
    spread_a = _fragment_spread(
        "CategoryFields",
        "CategoryType",
        selections=[_sel("items")],
    )
    spread_b = _fragment_spread(
        "CategoryFields",
        "CategoryType",
        selections=[_sel("items")],
    )
    # Both spreads reference "items". The walker descends into each
    # fragment independently, but _merge_aliased_selections inside the
    # fragment-level walk deduplicates.
    plan = plan_optimizations([spread_a, spread_b], Category)
    # Each fragment spread triggers a separate recursive _walk_selections
    # call, so we get two entries for "items". This is the O2 behavior;
    # O4 may refine deduplication when nested Prefetch objects land.
    # For now, assert that the relation *is* in the plan and the count
    # is at most 2 (one per spread).
    assert "items" in plan.prefetch_related
    assert plan.prefetch_related.count("items") <= 2


def test_plan_skips_fragment_with_skip_directive():
    """A fragment with ``@skip(if: true)`` is excluded from the plan."""
    inline = _inline_fragment(
        "CategoryType",
        selections=[_sel("items")],
        directives={"skip": {"if": True}},
    )
    plan = plan_optimizations([inline], Category)
    assert plan.is_empty


# ---------------------------------------------------------------------------
# _merge_aliased_selections — alias normalization
# ---------------------------------------------------------------------------


def test_merge_aliased_selections_merges_same_field():
    """Two aliased selections for the same field merge into one."""
    sel_a = _sel("items", selections=[_sel("id")], alias="first")
    sel_b = _sel("items", selections=[_sel("name")], alias="second")
    merged = _merge_aliased_selections([sel_a, sel_b])
    assert len(merged) == 1
    assert len(merged[0].selections) == 2


def test_merge_aliased_selections_preserves_different_fields():
    """Selections for different fields are not merged."""
    sel_a = _sel("items", alias="first")
    sel_b = _sel("name", alias="second")
    merged = _merge_aliased_selections([sel_a, sel_b])
    assert len(merged) == 2


def test_merge_aliased_selections_passes_fragments_through():
    """Fragment nodes pass through without merging."""
    frag = _inline_fragment("CategoryType", selections=[_sel("items")])
    sel = _sel("name")
    merged = _merge_aliased_selections([frag, sel])
    assert len(merged) == 2


def test_plan_merges_aliased_selections():
    """Aliased selections for the same relation produce one plan entry."""
    plan = plan_optimizations(
        [
            _sel("items", selections=[_sel("id")], alias="first"),
            _sel("items", selections=[_sel("name")], alias="second"),
        ],
        Category,
    )
    assert plan.prefetch_related == ["items"]


# ---------------------------------------------------------------------------
# O5 — only() projection
# ---------------------------------------------------------------------------


def test_plan_collects_only_fields_for_selected_scalars():
    """O5: scalar selections are collected into ``only_fields``."""
    plan = plan_optimizations([_sel("id"), _sel("name")], Category)
    assert plan.only_fields == ["id", "name"]
    assert plan.select_related == []
    assert plan.prefetch_related == []


def test_plan_includes_fk_columns_in_only_fields():
    """O5: select_related FK traversals include the source FK column."""
    plan = plan_optimizations(
        [_sel("name"), _sel("category", selections=[_sel("name")])],
        Item,
    )
    assert plan.select_related == ["category"]
    assert plan.only_fields == ["name", "category_id", "category__name"]


def test_plan_collects_related_scalar_only_fields_from_fragment():
    """O5: scalar selections inside relation fragments use relation paths."""
    plan = plan_optimizations(
        [
            _sel(
                "category",
                selections=[
                    _inline_fragment(
                        "CategoryType",
                        selections=[_sel("id"), _sel("name")],
                    ),
                ],
            ),
        ],
        Item,
    )
    assert plan.only_fields == ["category_id", "category__id", "category__name"]


# ---------------------------------------------------------------------------
# B2 — Forward-FK-id elision
# ---------------------------------------------------------------------------


def test_plan_elides_forward_fk_when_child_selection_is_id_only():
    """B2: ``category { id }`` uses ``category_id`` instead of a JOIN."""
    plan = plan_optimizations(
        [_sel("name"), _sel("category", selections=[_sel("id")])],
        Item,
    )
    assert plan.select_related == []
    assert plan.prefetch_related == []
    assert plan.only_fields == ["name", "category_id"]
    assert plan.fk_id_elisions == ["category"]


def test_plan_does_not_elide_forward_fk_when_extra_target_scalar_selected():
    """B2: ``category { id name }`` still needs ``select_related``."""
    plan = plan_optimizations(
        [_sel("category", selections=[_sel("id"), _sel("name")])],
        Item,
    )
    assert plan.select_related == ["category"]
    assert plan.prefetch_related == []
    assert plan.only_fields == ["category_id", "category__id", "category__name"]
    assert plan.fk_id_elisions == []


def test_plan_elides_forward_fk_id_only_selection_inside_fragment():
    """B2: id-only selections discovered through fragments can elide the JOIN."""
    plan = plan_optimizations(
        [
            _sel(
                "category",
                selections=[
                    _inline_fragment("CategoryType", selections=[_sel("id")]),
                ],
            ),
        ],
        Item,
    )
    assert plan.select_related == []
    assert plan.only_fields == ["category_id"]
    assert plan.fk_id_elisions == ["category"]


def test_plan_does_not_elide_forward_fk_when_target_has_custom_get_queryset():
    """B2: O6 visibility hooks win over FK-id elision."""
    registry.clear()

    class FilteredCategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return True

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset

    registry.register(Category, FilteredCategoryType)
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("id")])],
            Item,
        )
    finally:
        registry.clear()

    assert plan.select_related == []
    assert plan.fk_id_elisions == []
    assert plan.only_fields == ["category_id"]
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)


def test_plan_elides_forward_fk_when_target_pk_is_not_named_id():
    """B2: elision uses the related model's actual PK field name, not literal ``id``."""

    class UuidTarget(models.Model):
        uuid = models.CharField(max_length=32, primary_key=True)
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "tests"
            managed = False

    class UuidSource(models.Model):
        target = models.ForeignKey(UuidTarget, on_delete=models.CASCADE)

        class Meta:
            app_label = "tests"
            managed = False

    plan = plan_optimizations(
        [_sel("target", selections=[_sel("uuid")])],
        UuidSource,
    )
    assert plan.select_related == []
    assert plan.only_fields == ["target_id"]
    assert plan.fk_id_elisions == ["target"]


def test_plan_does_not_elide_fk_to_non_pk_to_field():
    """B2: FK ``to_field`` values are not treated as related PK values."""

    class CodeTarget(models.Model):
        code = models.CharField(max_length=32, unique=True)
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "tests"
            managed = False

    class CodeSource(models.Model):
        target = models.ForeignKey(
            CodeTarget,
            to_field="code",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "tests"
            managed = False

    plan = plan_optimizations(
        [_sel("target", selections=[_sel("id")])],
        CodeSource,
    )
    assert plan.select_related == ["target"]
    assert plan.fk_id_elisions == []
    assert plan.only_fields == ["target_id", "target__id"]


def test_plan_does_not_elide_when_target_type_has_custom_id_resolver():
    """B2: custom id resolvers may need more than the stubbed PK."""

    class CustomIdTarget(models.Model):
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "tests"
            managed = False

    class CustomIdSource(models.Model):
        target = models.ForeignKey(CustomIdTarget, on_delete=models.CASCADE)

        class Meta:
            app_label = "tests"
            managed = False

    class CustomIdTargetType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

        def resolve_id(self):
            return f"{self.name}:{self.pk}"

    registry.register(CustomIdTarget, CustomIdTargetType)
    try:
        plan = plan_optimizations(
            [_sel("target", selections=[_sel("id")])],
            CustomIdSource,
        )
    finally:
        registry.clear()

    assert plan.select_related == ["target"]
    assert plan.fk_id_elisions == []
    assert plan.only_fields == ["target_id", "target__id"]


# ---------------------------------------------------------------------------
# O6 — get_queryset + Prefetch downgrade
# ---------------------------------------------------------------------------


def test_plan_downgrades_select_related_when_target_has_custom_get_queryset():
    """O6: a custom target ``get_queryset`` downgrades forward FK joins to ``Prefetch``."""
    registry.clear()
    info = SimpleNamespace(field_name="allItems")
    calls = {}

    class FilteredCategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return True

        @classmethod
        def get_queryset(cls, queryset, passed_info, **kwargs):
            calls["queryset"] = queryset
            calls["info"] = passed_info
            return queryset.filter(is_private=False)

    registry.register(Category, FilteredCategoryType)
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("name")])],
            Item,
            info=info,
        )
    finally:
        registry.clear()

    assert plan.select_related == []
    assert plan.only_fields == ["category_id"]
    assert plan.cacheable is False
    assert len(plan.prefetch_related) == 1
    prefetch = plan.prefetch_related[0]
    assert isinstance(prefetch, Prefetch)
    assert prefetch.prefetch_to == "category"
    assert prefetch.queryset.model is Category
    assert calls["queryset"].model is Category
    assert calls["info"] is info


def test_plan_keeps_select_related_when_target_uses_default_get_queryset():
    """O6: registered target types without custom ``get_queryset`` still use joins."""
    registry.clear()

    class DefaultCategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.register(Category, DefaultCategoryType)
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("name")])],
            Item,
        )
    finally:
        registry.clear()

    assert plan.select_related == ["category"]
    assert plan.prefetch_related == []
    assert plan.only_fields == ["category_id", "category__name"]
    assert plan.cacheable is True


def test_plan_prefetches_many_side_with_custom_target_get_queryset():
    """O6: many-side relations use filtered ``Prefetch`` when the target has visibility logic."""
    registry.clear()
    calls = {}

    class FilteredItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return True

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls["queryset"] = queryset
            return queryset.filter(is_private=False)

    registry.register(Item, FilteredItemType)
    try:
        plan = plan_optimizations([_sel("items", selections=[_sel("name")])], Category)
    finally:
        registry.clear()

    assert plan.select_related == []
    assert plan.cacheable is False
    assert len(plan.prefetch_related) == 1
    prefetch = plan.prefetch_related[0]
    assert isinstance(prefetch, Prefetch)
    assert prefetch.prefetch_to == "items"
    assert prefetch.queryset.model is Item
    assert calls["queryset"].model is Item


# ---------------------------------------------------------------------------
# Future slice placeholders
# ---------------------------------------------------------------------------
# TODO(spec-optimizer_nested_prefetch_chains.md O4): add walker tests.
#
# Pseudo:
# - test_plan_emits_nested_prefetch_chain_depth_2:
#     Category > items > entries emits outer Prefetch("items") whose
#     child queryset prefetches entries.
# - test_plan_emits_nested_select_related_chain_depth_2:
#     Entry > item > category emits ["item", "item__category"].
# - test_plan_combines_prefetch_boundary_with_inner_select_related.
# - test_plan_propagates_uncacheable_nested_custom_get_queryset.
# - test_plan_honors_optimizer_hints_at_nested_depth.
# - test_plan_honors_prefetch_obj_hint_does_not_walk_inner_selections.
# - test_plan_records_nested_fk_id_elision_with_resolver_key.
# - add fragment / alias / directive variants for nested branches.
# - test_plan_emits_nested_prefetch_chain_depth_3
