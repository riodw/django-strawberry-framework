"""Tests for ``optimizer/plans.py`` — ``OptimizationPlan`` data structure.

The plan is a simple dataclass, so the test surface is small and focused
on the ``is_empty`` property and the ``apply`` method. The walker tests
in ``test_walker.py`` exercise construction; these tests verify that the
plan's own methods work correctly in isolation.
"""

from django.db.models import Prefetch
from fakeshop.products.models import Category, Entry, Item

from django_strawberry_framework.optimizer.plans import OptimizationPlan, lookup_paths, resolver_key


class TestOptimizationPlanIsEmpty:
    """``is_empty`` returns ``True`` only when all three bags are empty."""

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
