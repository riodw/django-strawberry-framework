"""Tests for ``optimizer/plans.py`` — ``OptimizationPlan`` data structure.

The plan is a simple dataclass, so the test surface is small and focused
on the ``is_empty`` property and the ``apply`` method. The walker tests
in ``test_walker.py`` exercise construction; these tests verify that the
plan's own methods work correctly in isolation.
"""

from fakeshop.products.models import Category

from django_strawberry_framework.optimizer.plans import OptimizationPlan


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
        plan = OptimizationPlan(fk_id_elisions=["category"])
        assert plan.is_empty is False

    def test_cacheable_flag_does_not_affect_empty_state(self):
        plan = OptimizationPlan(cacheable=False)
        assert plan.is_empty is True


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
