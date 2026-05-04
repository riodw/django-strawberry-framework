"""Tests for ``optimizer/plans.py`` — ``OptimizationPlan`` data structure.

The plan is a simple dataclass, so the test surface is small and focused
on the ``is_empty`` property and the ``apply`` method. The walker tests
in ``test_walker.py`` exercise construction; these tests verify that the
plan's own methods work correctly in isolation.
"""

from django.db.models import Prefetch
from fakeshop.products.models import Category, Entry, Item, Property

from django_strawberry_framework.optimizer.plans import (
    OptimizationPlan,
    _flatten_select_related,
    diff_plan_for_queryset,
    lookup_paths,
    resolver_key,
)


class TestOptimizationPlanIsEmpty:
    """``is_empty`` returns ``True`` only when all plan directives are empty."""

    def test_empty_plan(self):
        plan = OptimizationPlan()
        assert plan.is_empty is True

    def test_non_empty_select_related(self):
        plan = OptimizationPlan(select_related=["category"])
        assert plan.is_empty is False

    def test_non_empty_prefetch_related(self):
        plan = OptimizationPlan(prefetch_related=["items"])
        assert plan.is_empty is False

    def test_non_empty_only_fields(self):
        plan = OptimizationPlan(only_fields=["name"])
        assert plan.is_empty is False

    def test_non_empty_fk_id_elisions(self):
        plan = OptimizationPlan(fk_id_elisions=["ItemType.category@allItems.category"])
        assert plan.is_empty is False

    def test_non_empty_planned_resolver_keys(self):
        plan = OptimizationPlan(planned_resolver_keys=["ItemType.category@allItems.category"])
        assert plan.is_empty is False

    def test_cacheable_flag_does_not_affect_empty_state(self):
        plan = OptimizationPlan(cacheable=False)
        assert plan.is_empty is True


class TestLookupPaths:
    """``lookup_paths`` flattens Django lookup paths for debugging/B8."""

    def test_flatten_select_related_paths(self):
        plan = OptimizationPlan(select_related=["item", "item__category"])
        assert lookup_paths(plan) == {"item", "item__category"}

    def test_flatten_plain_prefetch_string(self):
        plan = OptimizationPlan(prefetch_related=["items"])
        assert lookup_paths(plan) == {"items"}

    def test_flatten_nested_prefetch_objects_recursively(self):
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        assert lookup_paths(plan) == {"items", "items__entries"}

    def test_does_not_include_resolver_keys(self):
        plan = OptimizationPlan(
            select_related=["category"],
            planned_resolver_keys=["ItemType.category@allItems.category"],
            fk_id_elisions=["ItemType.owner@allItems.owner"],
        )
        assert lookup_paths(plan) == {"category"}

    def test_ignores_unknown_prefetch_like_entries(self):
        # Deliberately impossible for generated plans; covers defensive flattening.
        plan = OptimizationPlan(prefetch_related=[object()])
        assert lookup_paths(plan) == set()


def test_resolver_key_includes_parent_type_and_runtime_path():
    class ItemType:
        pass

    assert (
        resolver_key(ItemType, "category", ("allItems", "category")) == "ItemType.category@allItems.category"
    )


class TestOptimizationPlanApply:
    """``apply`` mutates a queryset with the collected directives."""

    def test_apply_empty_plan_returns_queryset_unchanged(self):
        plan = OptimizationPlan()
        qs = Category.objects.all()
        result = plan.apply(qs)
        # An empty plan should not add select_related or prefetch_related.
        assert result.query.select_related is False
        assert result._prefetch_related_lookups == ()

    def test_apply_select_related(self):
        plan = OptimizationPlan(select_related=["category"])
        # Use a model that has a FK — Item.category.
        from fakeshop.products.models import Item

        qs = Item.objects.all()
        result = plan.apply(qs)
        assert "category" in result.query.select_related

    def test_apply_prefetch_related(self):
        plan = OptimizationPlan(prefetch_related=["items"])
        qs = Category.objects.all()
        result = plan.apply(qs)
        assert "items" in result._prefetch_related_lookups

    def test_apply_only_fields(self):
        plan = OptimizationPlan(only_fields=["name"])
        qs = Category.objects.all()
        result = plan.apply(qs)
        fields, is_deferred = result.query.deferred_loading
        assert fields == {"name"}
        assert is_deferred is False


class TestFlattenSelectRelated:
    """``_flatten_select_related`` normalizes Django's three select_related shapes."""

    def test_false_returns_empty_set(self):
        assert _flatten_select_related(False) == set()

    def test_true_returns_empty_set_for_wildcard(self):
        # P2: wildcard ``select_related()`` cannot safely justify
        # dropping explicit optimizer entries because the wildcard only
        # follows non-null FKs.  Treat as no overlap.
        assert _flatten_select_related(True) == set()

    def test_dict_flattens_to_top_level_paths(self):
        assert _flatten_select_related({"category": {}}) == {"category"}

    def test_dict_flattens_nested_chains(self):
        assert _flatten_select_related({"category": {"parent": {}}}) == {
            "category",
            "category__parent",
        }


class TestDiffPlanForQueryset:
    """``diff_plan_for_queryset`` reconciles plan vs. queryset without mutating the plan."""

    def test_returns_same_instances_when_nothing_to_drop(self):
        plan = OptimizationPlan(select_related=["category"], prefetch_related=["items"])
        qs = Category.objects.all()
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_qs is qs

    def test_drops_select_related_already_on_queryset(self):
        plan = OptimizationPlan(select_related=["category"])
        qs = Item.objects.select_related("category")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is not plan
        assert delta_plan.select_related == []
        assert delta_qs is qs
        # Original plan is untouched — B1 caches it across requests.
        assert plan.select_related == ["category"]

    def test_drops_chained_select_related(self):
        plan = OptimizationPlan(select_related=["item__category"])
        qs = Entry.objects.select_related("item__category")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.select_related == []

    def test_wildcard_select_related_does_not_drop_explicit_entries(self):
        # P2: ``select_related()`` follows only non-null FKs; the
        # optimizer may name nullable FKs explicitly.  Treat the
        # wildcard as no overlap and pass entries through unchanged.
        plan = OptimizationPlan(select_related=["item", "property"])
        qs = Entry.objects.select_related()
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_plan.select_related == ["item", "property"]

    def test_drops_string_prefetch_already_on_queryset(self):
        plan = OptimizationPlan(prefetch_related=["items"])
        qs = Category.objects.prefetch_related("items")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == []
        assert plan.prefetch_related == ["items"]

    def test_consumer_prefetch_object_suppresses_plan_string(self):
        plan = OptimizationPlan(prefetch_related=["items"])
        qs = Category.objects.prefetch_related(Prefetch("items", queryset=Item.objects.all()))
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == []

    def test_partial_overlap_keeps_remaining_entries(self):
        plan = OptimizationPlan(select_related=["item", "property"])
        qs = Entry.objects.select_related("item")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.select_related == ["property"]
        assert plan.select_related == ["item", "property"]

    def test_carries_over_metadata_fields(self):
        plan = OptimizationPlan(
            select_related=["category"],
            only_fields=["name"],
            fk_id_elisions=["ItemType.category@allItems.category"],
            planned_resolver_keys=["ItemType.category@allItems.category"],
            cacheable=False,
        )
        qs = Item.objects.select_related("category")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.only_fields == ["name"]
        assert delta_plan.fk_id_elisions == ["ItemType.category@allItems.category"]
        assert delta_plan.planned_resolver_keys == ["ItemType.category@allItems.category"]
        assert delta_plan.cacheable is False

    def test_consumer_descendant_string_absorbed_by_optimizer_prefetch(self):
        # P1 case 1: consumer ``"items__entries"`` carries no info the
        # optimizer's nested ``Prefetch`` lacks.  The plain string is
        # stripped from the queryset and the optimizer entry is kept;
        # this avoids the ``'items' lookup was already seen with a
        # different queryset`` ValueError without sacrificing
        # projection.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items__entries")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == [outer]
        assert delta_qs is not qs
        assert delta_qs._prefetch_related_lookups == ()

    def test_consumer_exact_plus_descendant_strings_both_absorbed(self):
        # P1 follow-up: ``prefetch_related("items", "items__entries")``
        # combined.  Both plain strings are absorbed by the optimizer's
        # ``Prefetch("items", queryset=...)`` so Django does not see
        # the implicit ``items`` from ``items__entries`` colliding with
        # the explicit ``Prefetch("items", ...)``.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items", "items__entries")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == [outer]
        assert delta_qs is not qs
        assert delta_qs._prefetch_related_lookups == ()

    def test_optimizer_does_not_strip_consumer_descendants_it_does_not_cover(self):
        # P1 follow-up: when the optimizer's own subtree does not cover
        # every consumer descendant on the same subtree, absorbing
        # would silently drop data. Drop the optimizer entry instead;
        # the consumer's deeper prefetch is preserved.
        outer = Prefetch("items", queryset=Item.objects.only("name"))  # no nested chain
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items__entries")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == []
        assert delta_qs is qs
        assert {getattr(e, "prefetch_to", e) for e in delta_qs._prefetch_related_lookups} == {
            "items__entries",
        }

    def test_optimizer_can_absorb_consumer_path_only_when_covered(self):
        # Variant: consumer has both a covered descendant and an
        # uncovered descendant. The uncovered one tips the decision —
        # we drop the optimizer to keep the consumer's full subtree.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items__entries", "items__properties")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == []
        assert delta_qs is qs

    def test_consumer_descendant_with_custom_prefetch_drops_optimizer(self):
        # When any consumer entry on the subtree is a custom
        # ``Prefetch`` (not just a bare string), we cannot losslessly
        # absorb it; drop the optimizer entry to preserve the
        # consumer's explicit subtree.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        consumer_descendant = Prefetch("items__entries", queryset=Entry.objects.all())
        qs = Category.objects.prefetch_related(consumer_descendant)
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == []
        assert delta_qs is qs
        assert delta_qs._prefetch_related_lookups == (consumer_descendant,)

    def test_consumer_plain_string_replaced_by_optimizer_nested_prefetch(self):
        # P1 case 2: consumer ``prefetch_related("items")`` plain
        # string vs. optimizer ``Prefetch("items", queryset=...)``
        # carrying nested chains.  The plain string carries no info
        # the optimizer's Prefetch lacks, so the optimizer wins and
        # the consumer's bare entry is stripped from the queryset.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == [outer]
        assert delta_qs is not qs
        assert delta_qs._prefetch_related_lookups == ()

    def test_upgrade_preserves_other_consumer_prefetches(self):
        # When upgrading a single consumer plain string to the
        # optimizer's ``Prefetch``, any unrelated consumer prefetches
        # must survive the queryset rewrite.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        unrelated = Prefetch("properties", queryset=Property.objects.all())
        qs = Category.objects.prefetch_related("items", unrelated)
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == [outer]
        assert delta_qs is not qs
        assert delta_qs._prefetch_related_lookups == (unrelated,)

    def test_consumer_prefetch_with_queryset_keeps_consumer_drops_optimizer(self):
        # When the consumer passes their own ``Prefetch`` with a custom
        # queryset, we cannot losslessly replace it.  Consumer wins,
        # optimizer is dropped (any nested optimizer work is sacrificed
        # — the consumer chose to manage this branch explicitly).
        consumer_pf = Prefetch("items", queryset=Item.objects.all())
        opt_pf = Prefetch("items", queryset=Item.objects.prefetch_related("entries"))
        plan = OptimizationPlan(prefetch_related=[opt_pf])
        qs = Category.objects.prefetch_related(consumer_pf)
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == []
        assert delta_qs is qs
        assert delta_qs._prefetch_related_lookups == (consumer_pf,)
