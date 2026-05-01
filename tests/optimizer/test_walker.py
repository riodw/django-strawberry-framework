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

from django_strawberry_framework import OptimizerHint
from django_strawberry_framework.optimizer.walker import (
    _ensure_connector_only_fields,
    _is_fragment,
    _merge_aliased_selections,
    _selected_scalar_names,
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


def _prefetch_entry(plan, index=0):
    """Return a prefetch entry and assert it is a ``Prefetch`` object."""
    entry = plan.prefetch_related[index]
    assert isinstance(entry, Prefetch)
    return entry


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
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "items"


def test_plan_dispatches_mixed_relations():
    """Forward FK and reverse FK in one selection produce both bags."""
    plan = plan_optimizations(
        [_sel("category"), _sel("entries")],
        Item,
    )
    assert plan.select_related == ["category"]
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "entries"
    assert plan.only_fields == ["category_id"]


def test_plan_skips_unknown_selections():
    """Selections not on the Django model are silently skipped."""
    plan = plan_optimizations([_sel("bogusField")], Category)
    assert plan.is_empty


def test_plan_prefetches_relation_with_missing_related_model_defensively():
    """Defensive branch: relation fields without related_model become string prefetches."""

    class FakeModel:
        pass

    # Deliberately impossible in real Django; covers the defensive branch.
    fake_field = SimpleNamespace(
        name="generic",
        is_relation=True,
        related_model=None,
        attname=None,
        many_to_many=True,
        one_to_many=False,
    )
    FakeModel._meta = SimpleNamespace(get_fields=lambda: [fake_field])

    plan = plan_optimizations([_sel("generic")], FakeModel)

    assert plan.prefetch_related == ["generic"]
    assert plan.planned_resolver_keys == ["generic@generic"]


def test_plan_select_relation_with_missing_related_model_is_not_elided():
    """Defensive branch: FK-id elision is unsafe when related_model is missing."""

    class FakeModel:
        pass

    fake_field = SimpleNamespace(
        name="relation",
        is_relation=True,
        related_model=None,
        attname="relation_id",
        many_to_many=False,
        one_to_many=False,
        auto_created=False,
    )
    FakeModel._meta = SimpleNamespace(get_fields=lambda: [fake_field])

    plan = plan_optimizations([_sel("relation", selections=[_sel("id")])], FakeModel)

    assert plan.select_related == ["relation"]
    assert plan.only_fields == ["relation_id"]
    assert plan.fk_id_elisions == []


def test_selected_scalar_names_returns_none_without_model():
    """Defensive branch: FK-id elision is unsafe without a concrete model."""
    # Deliberately impossible in normal walker flow; covers the helper guard.
    assert _selected_scalar_names([_sel("id")], None) is None


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
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "items"


def test_plan_handles_named_fragment_spread():
    """Relations inside a named fragment spread route to the plan."""
    spread = _fragment_spread(
        "CategoryFields",
        "CategoryType",
        selections=[_sel("name"), _sel("items")],
    )
    plan = plan_optimizations([spread], Category)
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "items"


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
    assert [prefetch.prefetch_to for prefetch in plan.prefetch_related] == ["items"]


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
    assert merged[0]._optimizer_response_keys == ["first", "second"]


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
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "items"
    assert plan.planned_resolver_keys == ["items@first", "items@second"]


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
    assert plan.fk_id_elisions == ["category@category"]
    assert plan.planned_resolver_keys == ["category@category"]


def test_plan_elides_forward_fk_id_only_selection_for_each_alias():
    """B2/O4: duplicate aliases keep distinct resolver keys for FK-id elision."""
    plan = plan_optimizations(
        [
            _sel("category", selections=[_sel("id")], alias="first"),
            _sel("category", selections=[_sel("id")], alias="second"),
        ],
        Item,
    )
    assert plan.select_related == []
    assert plan.only_fields == ["category_id"]
    assert plan.fk_id_elisions == ["category@first", "category@second"]
    assert plan.planned_resolver_keys == ["category@first", "category@second"]


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
    assert plan.fk_id_elisions == ["category@category"]


def test_plan_does_not_elide_when_fragment_contains_relation_selection():
    """B2: relation selections inside fragments make FK-id elision unsafe."""
    plan = plan_optimizations(
        [
            _sel(
                "category",
                selections=[
                    _inline_fragment("CategoryType", selections=[_sel("items")]),
                ],
            ),
        ],
        Item,
    )
    assert plan.select_related == ["category"]
    assert plan.only_fields == ["category_id"]
    assert plan.fk_id_elisions == []


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
    assert plan.fk_id_elisions == ["target@target"]


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
# O4 — nested prefetch chains
# ---------------------------------------------------------------------------


def test_plan_emits_nested_prefetch_chain_depth_2():
    """O4: ``Category > items > entries`` emits nested ``Prefetch`` objects."""
    plan = plan_optimizations(
        [_sel("items", selections=[_sel("entries", selections=[_sel("value")])])],
        Category,
    )

    outer = _prefetch_entry(plan)
    assert outer.prefetch_to == "items"
    inner = outer.queryset._prefetch_related_lookups[0]
    assert isinstance(inner, Prefetch)
    assert inner.prefetch_to == "entries"
    assert inner.queryset.model is Entry
    fields, is_deferred = inner.queryset.query.deferred_loading
    assert fields == {"value", "item_id"}
    assert is_deferred is False


def test_plan_emits_nested_prefetch_chain_depth_3_with_inner_select():
    """O4: ``Category > items > entries > property`` keeps connector columns."""
    plan = plan_optimizations(
        [
            _sel(
                "items",
                selections=[
                    _sel(
                        "entries",
                        selections=[_sel("property", selections=[_sel("name")])],
                    ),
                ],
            ),
        ],
        Category,
    )

    outer = _prefetch_entry(plan)
    assert outer.prefetch_to == "items"
    inner = outer.queryset._prefetch_related_lookups[0]
    assert isinstance(inner, Prefetch)
    assert inner.prefetch_to == "entries"
    assert inner.queryset.model is Entry
    assert inner.queryset.query.select_related == {"property": {}}
    fields, is_deferred = inner.queryset.query.deferred_loading
    assert fields == {"item_id", "property_id", "property__name"}
    assert is_deferred is False


def test_plan_emits_nested_select_related_chain_depth_2():
    """O4: ``Entry > item > category`` stays in one joined queryset."""
    plan = plan_optimizations(
        [_sel("item", selections=[_sel("category", selections=[_sel("name")])])],
        Entry,
    )

    assert plan.select_related == ["item", "item__category"]
    assert plan.prefetch_related == []
    assert plan.only_fields == ["item_id", "item__category_id", "item__category__name"]


def test_plan_combines_prefetch_boundary_with_inner_select_related():
    """O4: a prefetched child queryset can carry its own ``select_related``."""
    plan = plan_optimizations(
        [_sel("items", selections=[_sel("category", selections=[_sel("name")])])],
        Category,
    )

    outer = _prefetch_entry(plan)
    assert outer.prefetch_to == "items"
    assert outer.queryset.query.select_related == {"category": {}}
    fields, is_deferred = outer.queryset.query.deferred_loading
    assert fields == {"category_id", "category__name"}
    assert is_deferred is False


def test_plan_propagates_uncacheable_nested_custom_get_queryset():
    """O4+O6: a nested custom ``get_queryset`` makes the root plan uncacheable."""
    registry.clear()

    class FilteredEntryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return True

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    registry.register(Entry, FilteredEntryType)
    try:
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("entries", selections=[_sel("value")])])],
            Category,
        )
    finally:
        registry.clear()

    assert plan.cacheable is False
    outer = _prefetch_entry(plan)
    inner = outer.queryset._prefetch_related_lookups[0]
    assert isinstance(inner, Prefetch)
    assert inner.prefetch_to == "entries"


def test_plan_honors_optimizer_hints_at_nested_depth():
    """O4+B4: nested ``OptimizerHint.SKIP`` suppresses that branch."""
    registry.clear()

    class ItemType:
        _optimizer_hints = {"entries": OptimizerHint.SKIP}

        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.register(Item, ItemType)
    try:
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("entries", selections=[_sel("value")])])],
            Category,
        )
    finally:
        registry.clear()

    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "items"


def test_plan_honors_prefetch_obj_hint_does_not_walk_inner_selections():
    """O4+B4: explicit ``Prefetch`` hints are leaf operations."""
    registry.clear()
    explicit = Prefetch("items", queryset=Item.objects.only("name"))

    class CategoryType:
        _optimizer_hints = {"items": OptimizerHint.prefetch(explicit)}

        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.register(Category, CategoryType)
    try:
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("entries", selections=[_sel("value")])])],
            Category,
        )
    finally:
        registry.clear()

    assert plan.prefetch_related == [explicit]


def test_plan_prefetch_obj_hint_on_forward_fk_adds_connector_column():
    """B4: explicit ``Prefetch`` hints on forward FKs keep the source FK column."""
    registry.clear()
    explicit = Prefetch("category", queryset=Category.objects.only("name"))

    class ItemType:
        _optimizer_hints = {"category": OptimizerHint.prefetch(explicit)}

        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.register(Item, ItemType)
    try:
        plan = plan_optimizations([_sel("category", selections=[_sel("name")])], Item)
    finally:
        registry.clear()

    assert plan.prefetch_related == [explicit]
    assert plan.only_fields == ["category_id"]
    assert plan.planned_resolver_keys == ["ItemType.category@category"]


def test_plan_force_select_hint_uses_select_recursion():
    """B4: ``select_related`` hints flow through same-query recursion."""
    registry.clear()

    class ItemType:
        _optimizer_hints = {"category": OptimizerHint.select_related()}

        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.register(Item, ItemType)
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("name"), _sel("items", selections=[_sel("name")])])],
            Item,
        )
    finally:
        registry.clear()

    assert plan.select_related == ["category"]
    assert plan.only_fields == ["category_id", "category__name"]
    assert plan.planned_resolver_keys == ["ItemType.category@category", "items@category.items"]
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "category__items"
    fields, is_deferred = prefetch.queryset.query.deferred_loading
    assert fields == {"name", "category_id"}
    assert is_deferred is False


def test_plan_records_nested_fk_id_elision_with_resolver_key():
    """O4+B2: FK-id elision inside a child plan uses the nested resolver key."""
    plan = plan_optimizations(
        [_sel("items", selections=[_sel("category", selections=[_sel("id")])])],
        Category,
    )

    outer = _prefetch_entry(plan)
    assert outer.prefetch_to == "items"
    assert plan.fk_id_elisions == ["category@items.category"]
    assert "category@items.category" in plan.planned_resolver_keys


def test_plan_nested_prefetch_respects_fragment_alias_and_directive_shapes():
    """O4: nested branches still honor existing fragment/alias/directive behavior."""
    plan = plan_optimizations(
        [
            _sel(
                "items",
                alias="things",
                selections=[
                    _inline_fragment(
                        "ItemType",
                        selections=[
                            _sel(
                                "entries",
                                selections=[_sel("value")],
                                directives={"include": {"if": True}},
                            ),
                            _sel(
                                "category",
                                selections=[_sel("name")],
                                directives={"skip": {"if": True}},
                            ),
                        ],
                    ),
                ],
            ),
        ],
        Category,
    )

    outer = _prefetch_entry(plan)
    assert outer.prefetch_to == "items"
    inner = outer.queryset._prefetch_related_lookups[0]
    assert isinstance(inner, Prefetch)
    assert inner.prefetch_to == "entries"
    select_related = outer.queryset.query.select_related
    assert select_related is False or "category" not in select_related


def test_ensure_connector_only_fields_adds_m2m_target_pk():
    """Connector injection supports M2M-style relation metadata."""
    plan = plan_optimizations([_sel("name")], Category)
    fake_related_model = SimpleNamespace(
        _meta=SimpleNamespace(pk=SimpleNamespace(attname="id")),
    )
    fake_parent_field = SimpleNamespace(
        one_to_many=False,
        many_to_many=True,
        related_model=fake_related_model,
    )

    _ensure_connector_only_fields(plan, fake_parent_field)

    assert plan.only_fields == ["name", "id"]


def test_ensure_connector_only_fields_logs_when_connector_unknown(caplog):
    """Connector injection logs when a relation lacks connector metadata."""
    from django_strawberry_framework.optimizer.walker import logger

    plan = plan_optimizations([_sel("name")], Category)
    fake_parent_field = SimpleNamespace(
        name="generic",
        one_to_many=True,
        many_to_many=False,
    )

    caplog.set_level("DEBUG", logger=logger.name)
    _ensure_connector_only_fields(plan, fake_parent_field)

    assert plan.only_fields == ["name"]
    assert any("could not resolve connector column" in r.message for r in caplog.records)
