"""OptimizationPlan tests for plan structure, keys, paths, and select/prefetch state.

The plan is a simple dataclass, so the test surface is small and focused
on the ``is_empty`` property and the ``apply`` method. The walker tests
in ``test_walker.py`` exercise construction; these tests verify that the
plan's own methods work correctly in isolation.
"""

import sys
from types import SimpleNamespace

import pytest
from apps.products.models import Category, Entry, Item, Property
from django.db.models import Prefetch

from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.optimizer.plans import (
    _MAX_PATH_DEPTH,
    WINDOW_ROW_NUMBER,
    WINDOW_ROW_NUMBER_REVERSED,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
    _consumer_only_fields,
    _flatten_select_related,
    _reverse_order_by,
    apply_window_pagination,
    deterministic_order,
    diff_plan_for_queryset,
    ends_in_unique_column,
    lookup_paths,
    resolver_key,
    runtime_path_from_path,
    window_partition_for_prefetch,
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

    def test_uses_finalized_lookup_paths_after_finalize(self):
        """After ``finalize()``, ``lookup_paths`` reuses the frozen path set."""
        plan = OptimizationPlan(
            select_related=["category"],
            prefetch_related=["items"],
        ).finalize()
        # The frozen set is populated and is what ``lookup_paths`` returns.
        assert plan.finalized_lookup_paths == frozenset({"category", "items"})
        result = lookup_paths(plan)
        assert result == {"category", "items"}
        # A fresh ``set`` copy, not the frozenset itself.
        assert isinstance(result, set) and not isinstance(result, frozenset)


def test_resolver_key_includes_parent_type_and_runtime_path():
    class ItemType:
        pass

    assert (
        resolver_key(ItemType, "category", ("allItems", "category"))
        == "ItemType.category@allItems.category"
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
        # Use a model that has a FK - Item.category.
        from apps.products.models import Item

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


class TestOptimizationPlanFinalize:
    """``finalize`` swaps mutable list fields for tuples so post-handoff mutation raises."""

    def test_finalize_returns_tuples_for_list_fields(self):
        plan = OptimizationPlan(
            select_related=["category"],
            prefetch_related=["items"],
            only_fields=["name"],
            fk_id_elisions=["ItemType.category@x"],
            planned_resolver_keys=["ItemType.entries@x"],
        )
        finalized = plan.finalize()
        assert isinstance(finalized.select_related, tuple)
        assert isinstance(finalized.prefetch_related, tuple)
        assert isinstance(finalized.only_fields, tuple)
        assert isinstance(finalized.fk_id_elisions, tuple)
        assert isinstance(finalized.planned_resolver_keys, tuple)

    def test_finalize_precomputes_context_metadata_frozensets(self):
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(
            select_related=["category"],
            prefetch_related=[outer],
            fk_id_elisions=["ItemType.category@allItems.category"],
            planned_resolver_keys=["ItemType.items@allItems.items"],
        )

        finalized = plan.finalize()

        assert finalized.finalized_fk_id_elisions == frozenset(
            {"ItemType.category@allItems.category"},
        )
        assert finalized.finalized_planned_resolver_keys == frozenset(
            {"ItemType.items@allItems.items"},
        )
        assert finalized.finalized_lookup_paths == frozenset(
            {"category", "items", "items__entries"},
        )

    def test_finalize_preserves_values_and_cacheable_flag(self):
        plan = OptimizationPlan(select_related=["a", "b"], cacheable=False)
        finalized = plan.finalize()
        assert finalized.select_related == ("a", "b")
        assert finalized.cacheable is False

    def test_finalize_blocks_post_handoff_append_on_cache_isolation(self):
        plan = OptimizationPlan(prefetch_related=["items"]).finalize()
        # Tuple has no ``append``; mutation attempts raise AttributeError
        # rather than silently poisoning the plan-cache entry for the
        # next request.
        import pytest

        with pytest.raises(AttributeError):
            plan.prefetch_related.append("new")  # type: ignore[attr-defined]

    def test_finalize_is_idempotent(self):
        plan = OptimizationPlan(select_related=["a"]).finalize()
        again = plan.finalize()
        assert again.select_related == ("a",)
        assert isinstance(again.select_related, tuple)

    def test_apply_works_on_finalized_plan(self):
        plan = OptimizationPlan(select_related=["category"]).finalize()
        qs = Item.objects.all()
        result = plan.apply(qs)
        assert "category" in result.query.select_related


class TestPlanHelperRelocations:
    """``append_unique`` / ``append_unique_many`` / ``append_prefetch_unique`` live with the plan shape."""

    def test_append_unique_skips_existing_value(self):
        from django_strawberry_framework.optimizer.plans import append_unique

        values: list[str] = ["a"]
        append_unique(values, "a")
        append_unique(values, "b")
        assert values == ["a", "b"]

    def test_append_unique_many_iterates_tuple(self):
        from django_strawberry_framework.optimizer.plans import append_unique_many

        values: list[str] = []
        append_unique_many(
            values,
            ("a", "b", "a"),
        )
        assert values == ["a", "b"]

    def test_append_prefetch_unique_dedupes_by_lookup_path(self):
        from django_strawberry_framework.optimizer.plans import append_prefetch_unique

        first = Prefetch("items", queryset=Item.objects.all())
        second = Prefetch("items", queryset=Item.objects.filter(pk__gt=0))
        values: list = []
        append_prefetch_unique(values, first)
        append_prefetch_unique(values, second)
        assert values == [first]

    def test_plan_default_lists_use_indexed_append_unique(self):
        from django_strawberry_framework.optimizer.plans import _IndexedList, append_unique

        plan = OptimizationPlan()

        append_unique(plan.only_fields, "name")
        append_unique(plan.only_fields, "name")
        append_unique(plan.only_fields, "id")

        assert isinstance(plan.only_fields, _IndexedList)
        assert plan.only_fields == ["name", "id"]

    def test_plan_default_prefetch_list_indexes_by_lookup_path(self):
        from django_strawberry_framework.optimizer.plans import (
            _IndexedList,
            append_prefetch_unique,
        )

        first = Prefetch("items", queryset=Item.objects.all())
        second = Prefetch("items", queryset=Item.objects.filter(pk__gt=0))
        plan = OptimizationPlan()

        append_prefetch_unique(plan.prefetch_related, first)
        append_prefetch_unique(plan.prefetch_related, second)

        assert isinstance(plan.prefetch_related, _IndexedList)
        assert plan.prefetch_related == [first]


class TestIndexedList:
    """Direct coverage of ``_IndexedList`` mutators and the unhashable fallback."""

    def test_constructor_dedupes_initial_values(self):
        from django_strawberry_framework.optimizer.plans import _IndexedList

        indexed = _IndexedList(["a", "b", "a"])
        assert indexed == ["a", "b"]

    def test_append_and_extend_keep_index_for_later_append_unique(self):
        from django_strawberry_framework.optimizer.plans import _IndexedList

        indexed = _IndexedList()
        indexed.append("a")
        indexed.extend(["b", "c"])
        assert indexed == ["a", "b", "c"]
        # The sidecar index was maintained, so a later ``append_unique`` of an
        # already-present value is a no-op.
        indexed.append_unique("b")
        assert indexed == ["a", "b", "c"]

    def test_append_unique_falls_back_to_membership_for_unhashable_values(self):
        from django_strawberry_framework.optimizer.plans import _IndexedList

        indexed = _IndexedList()
        unhashable = ["nested"]
        # Unhashable key: the ``_seen`` probe raises ``TypeError`` and the
        # helper falls back to an ``in self`` membership scan. First insert
        # appends; the second is recognised as a duplicate and skipped.
        indexed.append_unique(unhashable)
        indexed.append_unique(unhashable)
        assert indexed == [["nested"]]


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


class TestConsumerOnlyFields:
    """``_consumer_only_fields`` defends Django's private ``deferred_loading`` contract.

    The function is fed real ``QuerySet`` objects from ``diff_plan_for_queryset``,
    but the contract it reads (``query.deferred_loading`` - a private 2-tuple
    of ``(field_set, defer_flag)``) is volatile across Django versions, so
    the function defends against missing-attribute, wrong-shape, defer-mode,
    and wildcard-``.only()`` inputs by returning ``None``. These pins cover
    each defensive branch directly so the guards cannot rot silently.
    """

    def test_returns_none_for_non_queryset_without_deferred_loading(self):
        """Pins the missing-attribute branch.

        A ``getattr(query, "deferred_loading", None)`` lookup returns ``None``
        when ``queryset.query`` is absent or has no ``deferred_loading`` -
        e.g. when the optimizer is fed a plain ``Manager`` or a test double.
        """
        assert _consumer_only_fields(object()) is None
        assert _consumer_only_fields(SimpleNamespace(query=SimpleNamespace())) is None

    def test_returns_none_for_malformed_deferred_loading_shape(self):
        """Pins the ``except (TypeError, ValueError)`` guard.

        Django's contract is ``(field_set, defer_flag)``; a future Django
        version (or a test double) returning a non-iterable, a non-2-tuple,
        a non-iterable field set, or any other malformed value falls through
        to ``None`` instead of crashing the optimizer.
        """
        bad_three_tuple = SimpleNamespace(
            query=SimpleNamespace(
                deferred_loading=(set(), False, "extra"),
            ),
        )
        bad_scalar = SimpleNamespace(query=SimpleNamespace(deferred_loading=42))
        bad_field_set = SimpleNamespace(query=SimpleNamespace(deferred_loading=(None, False)))
        assert _consumer_only_fields(bad_three_tuple) is None
        assert _consumer_only_fields(bad_scalar) is None
        assert _consumer_only_fields(bad_field_set) is None

    def test_returns_none_for_wildcard_only_with_empty_field_set(self):
        """Pins the ``not field_set`` branch.

        ``(set(), False)`` is not a meaningful consumer projection - Django's
        wildcard ``.only()`` collapses to the defer-mode default
        ``(set(), True)``, so this shape is mostly synthetic, but the guard
        keeps the contract symmetric with the wildcard explanation in the
        docstring.
        """
        empty_only = SimpleNamespace(query=SimpleNamespace(deferred_loading=(set(), False)))
        assert _consumer_only_fields(empty_only) is None


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
        assert delta_plan.select_related == ()
        assert delta_qs is qs
        # Original plan is untouched - B1 caches it across requests.
        assert plan.select_related == ["category"]

    def test_drops_chained_select_related(self):
        plan = OptimizationPlan(select_related=["item__category"])
        qs = Entry.objects.select_related("item__category")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.select_related == ()

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
        assert delta_plan.prefetch_related == ()
        assert plan.prefetch_related == ["items"]

    def test_consumer_prefetch_object_suppresses_plan_string(self):
        plan = OptimizationPlan(prefetch_related=["items"])
        qs = Category.objects.prefetch_related(Prefetch("items", queryset=Item.objects.all()))
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()

    def test_partial_overlap_keeps_remaining_entries(self):
        plan = OptimizationPlan(select_related=["item", "property"])
        qs = Entry.objects.select_related("item")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.select_related == ("property",)
        assert plan.select_related == ["item", "property"]

    def test_carries_over_metadata_fields(self):
        plan = OptimizationPlan(
            select_related=["category"],
            only_fields=["name"],
            fk_id_elisions=["ItemType.category@allItems.category"],
            planned_resolver_keys=["ItemType.category@allItems.category"],
            cacheable=False,
        ).finalize()
        qs = Item.objects.select_related("category")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.only_fields == ("name",)
        assert delta_plan.fk_id_elisions == ("ItemType.category@allItems.category",)
        assert delta_plan.planned_resolver_keys == ("ItemType.category@allItems.category",)
        assert delta_plan.finalized_lookup_paths == frozenset()
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
        assert delta_plan.prefetch_related == (outer,)
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
        assert delta_plan.prefetch_related == (outer,)
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
        assert delta_plan.prefetch_related == ()
        assert delta_qs is qs
        assert {getattr(e, "prefetch_to", e) for e in delta_qs._prefetch_related_lookups} == {
            "items__entries",
        }

    def test_optimizer_can_absorb_consumer_path_only_when_covered(self):
        # Variant: consumer has both a covered descendant and an
        # uncovered descendant. The uncovered one tips the decision -
        # we drop the optimizer to keep the consumer's full subtree.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items__entries", "items__properties")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()
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
        assert delta_plan.prefetch_related == ()
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
        assert delta_plan.prefetch_related == (outer,)
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
        assert delta_plan.prefetch_related == (outer,)
        assert delta_qs is not qs
        assert delta_qs._prefetch_related_lookups == (unrelated,)

    def test_drops_only_fields_when_consumer_applied_only(self):
        # M1: Django's ``QuerySet.only(...).only(...)`` replaces (not
        # merges) the deferred-field set. If the consumer already
        # restricted columns via ``.only()`` (e.g., to enforce a
        # column-level permission boundary), the optimizer must drop
        # its own ``only_fields`` rather than silently overwriting the
        # consumer projection. The diff result has ``only_fields=()``
        # so ``apply()`` does not call ``.only()`` again.
        plan = OptimizationPlan(select_related=["category"], only_fields=["id"])
        qs = Item.objects.only("name")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is not plan
        assert delta_plan.only_fields == ()
        # The consumer's projection survives untouched.
        fields, is_deferred = delta_qs.query.deferred_loading
        assert fields == {"name"}
        assert is_deferred is False
        # Original plan untouched (B1 cache invariant).
        assert plan.only_fields == ["id"]

    def test_keeps_only_fields_when_consumer_did_not_apply_only(self):
        # Counterpart to the drop case: without a consumer ``.only()``,
        # the optimizer's ``only_fields`` passes through unchanged and
        # ``apply()`` applies it.
        plan = OptimizationPlan(only_fields=["id"])
        qs = Item.objects.all()
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_plan.only_fields == ["id"]
        applied = delta_plan.apply(delta_qs)
        fields, is_deferred = applied.query.deferred_loading
        assert fields == {"id"}
        assert is_deferred is False

    def test_keeps_only_fields_when_consumer_used_defer(self):
        # ``.defer()`` is not a consumer projection in the
        # ``.only()`` sense - Django composes ``.only()`` after
        # ``.defer()`` cleanly. The optimizer keeps its ``only_fields``.
        plan = OptimizationPlan(only_fields=["id"])
        qs = Item.objects.defer("name")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_plan.only_fields == ["id"]

    def test_drops_only_fields_when_consumer_chained_only(self):
        # Django's chained ``.only().only()`` collapses to the most
        # recent argument; the consumer's effective ``.only()`` still
        # triggers the drop because ``deferred_loading`` is still
        # ``(<non-empty set>, False)``.
        plan = OptimizationPlan(only_fields=["id"])
        qs = Item.objects.only("name").only("category_id")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.only_fields == ()

    def test_consumer_prefetch_with_queryset_keeps_consumer_drops_optimizer(self):
        # When the consumer passes their own ``Prefetch`` with a custom
        # queryset, we cannot losslessly replace it.  Consumer wins,
        # optimizer is dropped (any nested optimizer work is sacrificed
        # - the consumer chose to manage this branch explicitly).
        consumer_pf = Prefetch("items", queryset=Item.objects.all())
        opt_pf = Prefetch("items", queryset=Item.objects.prefetch_related("entries"))
        plan = OptimizationPlan(prefetch_related=[opt_pf])
        qs = Category.objects.prefetch_related(consumer_pf)
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()
        assert delta_qs is qs
        assert delta_qs._prefetch_related_lookups == (consumer_pf,)


def _linked_path(*keys):
    """Build a graphql-core-style ``key``/``prev`` linked response path."""
    node = None
    for key in keys:
        node = SimpleNamespace(key=key, prev=node)
    return node


class TestRuntimePathFromPath:
    """``runtime_path_from_path`` walks ``prev`` under a fixed, fail-loud bound."""

    def test_walks_a_deep_but_finite_path(self):
        """A path of (ceiling - 1) nodes resolves fully - the boundary that just fits."""
        # _linked_path builds root-first; the output is that same root-first order.
        keys = tuple(f"f{i}" for i in range(_MAX_PATH_DEPTH - 1))
        path = _linked_path(*keys)
        assert runtime_path_from_path(path) == keys

    def test_strips_list_indexes(self):
        """Integer (list-index) keys are skipped; string keys/aliases kept."""
        path = _linked_path("allItems", 0, "cat")
        assert runtime_path_from_path(path) == ("allItems", "cat")

    def test_raises_on_cyclic_path(self):
        """A self-referential ``prev`` chain hits the bound and fails loud."""
        node = SimpleNamespace(key="loop", prev=None)
        node.prev = node  # never bottoms out
        with pytest.raises(RuntimeError, match="cyclic or corrupt"):
            runtime_path_from_path(node)


class TestApplyWindowPagination:
    """``apply_window_pagination`` annotation + range-filter mechanism (spec-033 Decision 4)."""

    def _windowed(self, **kwargs):
        return apply_window_pagination(
            Item.objects.all(),
            partition_by="category_id",
            order_by=["name", "pk"],
            **kwargs,
        )

    def test_annotates_row_number_and_total_count(self):
        """Both window annotations land under the ``_dst_*`` reserved names."""
        qs = self._windowed(offset=0, limit=3)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT in annotations
        sql = str(qs.query).upper()
        assert "ROW_NUMBER()" in sql
        assert "COUNT(" in sql

    def test_ambiguous_shapes_keep_partition_marker_row(self):
        """``offset > 0`` / ``limit == 0`` windows keep each partition's row 1.

        The marker-row disambiguation (connection window rigor, workstream C):
        the historically-ambiguous empty shapes OR the range filter with
        ``row_number == 1`` so an empty prefetch list proves zero children and
        a marker-only list carries the real count. The SQL shape pin: the
        row-number predicate appears with BOTH the range bound and the
        ``= 1`` alternative.
        """
        overshot = self._windowed(offset=5, limit=2)
        sql = str(overshot.query).upper()
        assert "> 5" in sql
        assert "<= 7" in sql
        assert "= 1" in sql  # the marker alternative
        assert " OR " in sql

        first_zero = self._windowed(offset=0, limit=0)
        sql = str(first_zero.query).upper()
        assert "= 1" in sql

        # Unbounded overshoot (offset without a finite limit) still markers.
        unbounded = self._windowed(offset=3, limit=None)
        sql = str(unbounded.query).upper()
        assert "> 3" in sql
        assert "= 1" in sql

    def test_unambiguous_shapes_plan_no_marker(self):
        """Plain ``first: N`` (offset 0, positive bound) and reverse windows add no marker."""
        plain = self._windowed(offset=0, limit=3)
        sql = str(plain.query).upper()
        assert "<= 3" in sql
        assert " OR " not in sql

        # The reversed (last-only) window never markers - ``last: 0`` falls
        # back per-parent for upstream's ``edges[-0:]`` serve-all quirk.
        reverse_zero = self._windowed(offset=0, limit=0, reverse=True)
        sql = str(reverse_zero.query).upper()
        assert WINDOW_ROW_NUMBER_REVERSED.upper() in sql
        assert " OR " not in sql

    def test_with_total_count_false_omits_count_annotation(self):
        """``with_total_count=False`` drops the count window, keeping the row filters.

        The conditional-count contract (connection window rigor, workstream B):
        the walker passes ``False`` when nothing in the selection observes the
        count; the row-number annotation and its range filters are untouched.
        """
        qs = self._windowed(offset=2, limit=3, with_total_count=False)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT not in annotations
        sql = str(qs.query).upper()
        assert "ROW_NUMBER()" in sql
        assert WINDOW_TOTAL_COUNT.upper() not in sql
        # The range filters still apply without the count annotation.
        assert ">" in sql
        assert "<=" in sql

    def test_next_page_probe_overfetches_one_row_without_the_count(self):
        """``next_page_probe=True`` bounds to ``limit + 1`` and drops the count.

        The count-free ``hasNextPage`` render: the plain first page fetches ONE
        sentinel row past the page (``<= 4`` for ``first: 3``, not ``<= 3``) and
        omits ``_dst_total_count`` entirely - the resolver derives ``hasNextPage``
        from the sentinel's presence. The renderer reads ``fetch_upper_bound``
        and never mentions the probe itself.
        """
        qs = self._windowed(offset=0, limit=3, with_total_count=False, next_page_probe=True)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT not in annotations
        sql = str(qs.query).upper()
        assert "<= 4" in sql  # the n+1 sentinel bound
        assert "<= 3" not in sql  # NOT the plain page bound
        assert " OR " not in sql  # a probe is not a marker shape

    def test_next_page_probe_ignored_off_the_plain_first_page_shape(self):
        """The probe flag is inert on non-plain shapes (bound stays the page bound).

        ``window_range_plan`` normalizes ``next_page_probe`` to the
        ``plain_first_page`` shape, so an ``after``-offset window passed the flag
        keeps its plain ``<= offset + limit`` bound - no accidental overfetch.
        """
        qs = self._windowed(offset=2, limit=3, next_page_probe=True)
        sql = str(qs.query).upper()
        assert "<= 5" in sql  # offset 2 + limit 3, no +1
        assert "<= 6" not in sql

    def test_engaged_probe_with_count_is_rejected(self):
        """An engaged-probe window that also annotates the count fails loudly.

        The probe/count mutual-exclusion contract at the ORM window entry point
        (``utils/connections.py::assert_window_fetch_mode``): a ``plain_first_page``
        window (offset 0, ``limit`` > 0) with ``next_page_probe=True`` engages the
        overfetch, so ``with_total_count=True`` is a planner bug - the sentinel
        would leak as a real edge. The off-shape case is inert and stays allowed
        (``test_next_page_probe_ignored_off_the_plain_first_page_shape`` above).
        """
        with pytest.raises(OptimizerError, match="mutually exclusive"):
            self._windowed(offset=0, limit=3, with_total_count=True, next_page_probe=True)

    def test_with_total_count_false_reverse_branch_still_bounds(self):
        """The reverse (last-only) branch honors ``with_total_count=False`` too."""
        qs = self._windowed(offset=0, limit=2, reverse=True, with_total_count=False)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER_REVERSED in annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT not in annotations
        assert "<= 2" in str(qs.query).upper()

    def test_applies_order_by_to_queryset_not_just_the_window(self):
        """The deterministic order is applied to the queryset's own ``ORDER BY``.

        The SQL window orders the ROW-NUMBER values, but Django hands prefetched
        instances to ``to_attr`` in the queryset's own return order; the fast path
        consumes ``rows`` as forward-ordered. So the same ``order_by`` tuple must
        drive ``queryset.order_by`` too, or the fast path can diverge from the
        fallback pipeline when DB return order != connection order (spec-033
        Decision 11, cursor-parity). Forward order applies in BOTH branches.
        """
        forward = self._windowed(offset=0, limit=3)
        assert tuple(forward.query.order_by) == ("name", "pk")
        reverse = self._windowed(offset=0, limit=2, reverse=True)
        assert tuple(reverse.query.order_by) == ("name", "pk")

    def test_forward_window_filters_offset_and_upper_bound(self):
        """A forward window with offset+limit filters ``__gt`` offset and ``__lte`` offset+limit."""
        qs = self._windowed(offset=2, limit=3)
        where = str(qs.query).upper()
        # Window-function filters wrap the queryset in a subquery with the
        # row-number predicates; both bounds must appear.
        assert WINDOW_ROW_NUMBER.upper() in where
        # offset filter (> 2) and upper-bound filter (<= 5) both present.
        assert ">" in where
        assert "<=" in where

    def test_no_offset_skips_lower_filter(self):
        """``offset == 0`` applies only the upper-bound filter."""
        qs = self._windowed(offset=0, limit=3)
        # The annotations are present; only the upper-bound filter applies.
        assert WINDOW_ROW_NUMBER in qs.query.annotations

    def test_reverse_branch_uses_reversed_row_number(self):
        """The reverse (last-only) branch annotates ``_dst_row_number_reversed`` and bounds it."""
        qs = self._windowed(offset=0, limit=2, reverse=True)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER_REVERSED in annotations
        # The reversed window still annotates the forward row number + total count.
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT in annotations
        # The reversed window MUST be bounded to ``limit`` rows (annotation alone
        # over-fetches every child row - the spec-033 last-only over-fetch bug).
        sql = str(qs.query).upper()
        assert WINDOW_ROW_NUMBER_REVERSED.upper() in sql
        assert "<= 2" in sql

    def test_reverse_branch_applies_offset_filter_when_present(self):
        """``reverse=True`` with a non-zero ``offset`` still applies the forward gt-filter.

        The walker never plans this combination (``after`` + ``last`` raises
        ``UnwindowableConnection`` at bounds derivation), but the helper's
        contract is the full ``(offset, limit, reverse)`` surface for direct
        callers: the forward offset filter composes with the reversed bound
        rather than being silently dropped.
        """
        qs = self._windowed(offset=2, limit=3, reverse=True)
        sql = str(qs.query).upper()
        assert "> 2" in sql
        assert WINDOW_ROW_NUMBER_REVERSED.upper() in sql
        assert "<= 3" in sql

    def test_reverse_branch_with_none_limit_adds_no_upper_filter(self):
        """``reverse=True, limit=None`` annotates the reversed window but adds no bound.

        Guards that the limit-vs-``None`` decision lives in the caller
        (``_connection_window_slice`` passes the literal ``last`` for the reverse
        branch); ``apply_window_pagination`` itself still no-ops on ``None``.
        """
        qs = self._windowed(offset=0, limit=None, reverse=True)
        assert WINDOW_ROW_NUMBER_REVERSED in qs.query.annotations
        assert "<=" not in str(qs.query).upper()

    def test_unbounded_limit_skips_upper_filter(self):
        """``limit is None`` (no upper bound) annotates but adds no ``__lte`` row filter."""
        qs = self._windowed(offset=1, limit=None)
        # Annotation present; offset filter applies, but no finite upper bound.
        assert WINDOW_ROW_NUMBER in qs.query.annotations

    def test_maxsize_limit_skips_upper_filter(self):
        """``sys.maxsize`` (relay's no-limit sentinel) adds no upper-bound filter."""
        qs = self._windowed(offset=0, limit=sys.maxsize)
        assert WINDOW_ROW_NUMBER in qs.query.annotations

    def test_annotations_compose_with_only(self):
        """Window annotations survive a ``.only()`` projection (annotations, not columns)."""
        qs = apply_window_pagination(
            Item.objects.only("name", "category_id"),
            partition_by="category_id",
            order_by=["name", "pk"],
            offset=0,
            limit=3,
        )
        assert WINDOW_ROW_NUMBER in qs.query.annotations
        assert WINDOW_TOTAL_COUNT in qs.query.annotations


class TestWindowPartitionForPrefetch:
    """``window_partition_for_prefetch`` returns the parent-side attach key per kind."""

    def test_reverse_fk_partitions_by_child_fk_attname(self):
        """A reverse FK (``Category.items``) partitions by the child FK column."""
        field = Category._meta.get_field("items")
        assert window_partition_for_prefetch(field) == "category_id"

    def test_forward_m2m_partitions_by_reverse_query_name(self):
        """A forward M2M partitions by the target's reverse query name, not the accessor.

        ``Book.genres`` has reverse query name ``"books"`` (the ``related_name``);
        partitioning the Genre child rows by ``"books"`` follows the reverse M2M
        back to each Book parent.
        """
        from apps.library.models import Book

        field = Book._meta.get_field("genres")
        assert window_partition_for_prefetch(field) == "books"

    def test_reverse_m2m_partitions_through_forward_field_name(self):
        """A reverse M2M (``Genre.books``) partitions through the child's forward M2M field."""
        from apps.library.models import Genre

        field = Genre._meta.get_field("books")
        assert window_partition_for_prefetch(field) == "genres"

    def test_forward_m2m_partition_diverges_from_accessor(self):
        """The forward-M2M partition is the reverse query name, NOT the accessor.

        ``Book.genres``'s instance accessor is ``"genres"`` but its windowable
        partition is the reverse query name ``"books"`` - the divergence the
        helper must resolve off ``remote_field`` rather than the accessor
        (spec-033 Decision 4; the reverse-no-``related_name`` shape the package
        special-cases everywhere).
        """
        from apps.library.models import Book

        field = Book._meta.get_field("genres")
        assert window_partition_for_prefetch(field) == "books"
        assert field.remote_field.name == "books"

    def test_forward_single_relation_raises(self):
        """A single-valued forward FK has no windowable partition - raises ``OptimizerError``."""
        field = Item._meta.get_field("category")
        with pytest.raises(OptimizerError, match="no windowable parent partition"):
            window_partition_for_prefetch(field)

    def test_windowable_kind_without_remote_field_keys_raises(self):
        """A windowable kind whose ``remote_field`` resolves neither attname nor name raises.

        Stock Django relation descriptors always carry a ``remote_field`` name, so
        this is a defensive guard: a malformed descriptor that classifies as a
        windowable kind but exposes no parent partition column falls back
        per-parent rather than partitioning by ``None`` (spec-033 Decision 4).
        """
        field = SimpleNamespace(many_to_many=True, remote_field=SimpleNamespace(), name="mock_rel")
        with pytest.raises(OptimizerError, match="could not resolve a parent partition"):
            window_partition_for_prefetch(field)


class TestDeterministicOrderHoistParity:
    """The hoisted order rule answers identically to the previous connection.py code."""

    def test_ends_in_unique_column_string_refs(self):
        """String order refs: pk / attname / unique field are unique; non-unique are not."""
        assert ends_in_unique_column(("id",), Category) is True
        assert ends_in_unique_column(("pk",), Category) is True
        assert ends_in_unique_column(("name",), Category) is True  # Category.name unique=True
        assert ends_in_unique_column(("-name",), Category) is True  # leading '-' stripped
        assert ends_in_unique_column(("name",), Item) is False  # Item.name unique=False
        assert ends_in_unique_column(("category__name",), Item) is False  # relation path
        assert ends_in_unique_column(("_dst_order_alias",), Category) is False  # annotation alias
        assert ends_in_unique_column((), Category) is False  # unordered

    def test_ends_in_unique_column_expression_refs(self):
        """``F`` expression terminals read the wrapped column name."""
        from django.db.models import F

        assert ends_in_unique_column((F("name").asc(),), Category) is True  # unique
        assert ends_in_unique_column((F("name").asc(),), Item) is False  # non-unique

    def test_ends_in_unique_column_unnameable_terminal(self):
        """A transform terminal (no readable column name) is treated as non-unique."""
        from django.db.models.functions import Lower

        assert ends_in_unique_column((Lower("name"),), Category) is False

    def test_deterministic_order_appends_pk_when_not_unique(self):
        """A non-unique terminal gets the pk appended; a unique one is returned unchanged."""
        assert deterministic_order(("name",), Item) == ("name", "id")
        # Already ends in a unique column -> unchanged.
        assert deterministic_order(("name",), Category) == ("name",)
        assert deterministic_order(("id",), Item) == ("id",)

    def test_deterministic_order_matches_connection_reexport(self):
        """``connection.py`` re-exports the same ``ends_in_unique_column`` (one source)."""
        from django_strawberry_framework.connection import _ends_in_unique_column

        assert _ends_in_unique_column is ends_in_unique_column


class TestReverseOrderBy:
    """``_reverse_order_by`` mirrors Django's ``queryset.reverse()`` (spec-033 Decision 4)."""

    def test_flips_string_direction(self):
        """String refs toggle the leading ``-``; the pk terminal stays total."""
        assert _reverse_order_by(["name", "id"]) == ["-name", "-id"]
        assert _reverse_order_by(["-name", "id"]) == ["name", "-id"]

    def test_flips_orderby_descending(self):
        """``OrderBy`` expressions flip ``.descending`` without re-running the compiler."""
        from django.db.models import F

        reversed_order = _reverse_order_by([F("name").asc()])
        assert reversed_order[0].descending is True

    def test_swaps_explicit_nulls_positioning(self):
        """Explicit ``nulls_first`` / ``nulls_last`` swap on reversal, like ``.reverse()``.

        Django inverts NULLS placement when reversing an ordering; mirror that so
        a consumer ``OrderSet`` with explicit NULLS positioning produces a reversed
        window matching the resolve-time ``.reverse()`` pipeline.
        """
        from django.db.models import F

        nulls_first = _reverse_order_by([F("name").asc(nulls_first=True)])[0]
        assert nulls_first.descending is True
        assert nulls_first.nulls_first is None
        assert nulls_first.nulls_last is True

        nulls_last = _reverse_order_by([F("name").desc(nulls_last=True)])[0]
        assert nulls_last.descending is False
        assert nulls_last.nulls_first is True
        assert nulls_last.nulls_last is None

    def test_bare_expression_without_descending_passes_through(self):
        """A non-string term with no ``.descending`` is reversed by passing it through.

        ``deterministic_order`` yields strings and ``OrderBy`` wrappers, but the
        guard handles a raw expression term defensively: with no ``.descending`` to
        flip, it is appended unchanged rather than mutated.
        """
        from django.db.models import F

        expr = F("name")
        assert _reverse_order_by([expr]) == [expr]


class TestPruneUnsupportableSelectRelated:
    """B8 relation-aware reconciliation: ``prune_unsupportable_select_related``.

    Django refuses ``select_related`` through a deferred relation field
    ("cannot be both deferred and traversed"), so a plan reconciled against
    a consumer-projected queryset must drop untraversable paths BEFORE
    apply - and drop the resolver keys those paths satisfied, so strictness
    sees the per-row fallback instead of a phantom plan. Every kept-path
    case COMPILES the applied queryset (``str(qs.query)``): the runtime
    behavior Django enforces, not just the plan shape.
    """

    @staticmethod
    def _reconcile(plan, queryset):
        """The extension's full B8 pipeline: prune, then diff, then apply."""
        from django_strawberry_framework.optimizer.plans import (
            prune_unsupportable_select_related,
        )

        pruned = prune_unsupportable_select_related(plan, queryset)
        delta, queryset = diff_plan_for_queryset(pruned, queryset)
        return pruned, delta.apply(queryset)

    def test_consumer_only_drops_blocked_path_and_its_resolver_keys(self):
        plan = OptimizationPlan(
            select_related=["category"],
            only_fields=["name", "category_id"],
            planned_resolver_keys=["category-key", "unrelated-key"],
            select_path_resolver_keys={"category": ("category-key",)},
        ).finalize()
        pruned, applied = self._reconcile(plan, Item.objects.only("name"))
        assert pruned is not plan
        assert pruned.select_related == ()
        assert pruned.planned_resolver_keys == ("unrelated-key",)
        assert "category-key" not in pruned.finalized_planned_resolver_keys
        # The review's runtime bar: the applied queryset COMPILES (the old
        # behavior raised FieldError at SQL generation).
        assert 'JOIN "products_category"' not in str(applied.query)
        # The original (cached) plan is untouched.
        assert plan.select_related == ("category",)
        assert "category-key" in plan.finalized_planned_resolver_keys

    def test_projection_loading_the_connector_keeps_the_path(self):
        plan = OptimizationPlan(
            select_related=["category"],
            planned_resolver_keys=["category-key"],
            select_path_resolver_keys={"category": ("category-key",)},
        ).finalize()
        # The attname form counts as loading the connector.
        pruned, applied = self._reconcile(plan, Item.objects.only("name", "category_id"))
        assert pruned is plan  # same object: nothing to prune.
        assert 'JOIN "products_category"' in str(applied.query)

    def test_dotted_projection_keeps_root_and_drops_deeper_path(self):
        from apps.library.models import Book

        plan = OptimizationPlan(
            select_related=["shelf", "shelf__branch"],
            planned_resolver_keys=["shelf-key", "branch-key"],
            select_path_resolver_keys={
                "shelf": ("shelf-key",),
                "shelf__branch": ("branch-key",),
            },
        ).finalize()
        # only("title", "shelf__code"): shelf traversable (dotted entry loads
        # the connector), but branch is deferred AT THE SHELF LEVEL.
        pruned, applied = self._reconcile(plan, Book.objects.only("title", "shelf__code"))
        assert pruned.select_related == ("shelf",)
        assert pruned.planned_resolver_keys == ("shelf-key",)
        compiled = str(applied.query)
        assert 'JOIN "library_shelf"' in compiled
        assert 'JOIN "library_branch"' not in compiled

    def test_consumer_defer_drops_path_keys_and_nested_only_fields(self):
        from apps.library.models import Book

        plan = OptimizationPlan(
            select_related=["shelf", "shelf__branch"],
            only_fields=["title", "shelf_id", "shelf__code"],
            planned_resolver_keys=["shelf-key", "branch-key"],
            select_path_resolver_keys={
                "shelf": ("shelf-key",),
                "shelf__branch": ("branch-key",),
            },
        ).finalize()
        pruned, applied = self._reconcile(plan, Book.objects.defer("shelf"))
        assert pruned.select_related == ()
        assert pruned.planned_resolver_keys == ()
        # The nested projection entry is only valid alongside the dropped
        # join; the plain root columns stay (defer composes with only()).
        assert pruned.only_fields == ("title", "shelf_id")
        assert 'JOIN "library_shelf"' not in str(applied.query)

    def test_defer_of_an_unrelated_column_prunes_nothing(self):
        from apps.library.models import Book

        plan = OptimizationPlan(
            select_related=["shelf"],
            select_path_resolver_keys={"shelf": ("shelf-key",)},
            planned_resolver_keys=["shelf-key"],
        ).finalize()
        pruned, applied = self._reconcile(plan, Book.objects.defer("subtitle"))
        assert pruned is plan
        assert 'JOIN "library_shelf"' in str(applied.query)

    def test_unresolvable_path_is_dropped_conservatively(self):
        # A path the model cannot resolve (planner drift, exotic doubles)
        # drops rather than gambles on a FieldError at compile time.
        from apps.library.models import Book

        plan = OptimizationPlan(select_related=["mystery"]).finalize()
        pruned, _ = self._reconcile(plan, Book.objects.only("title"))
        assert pruned.select_related == ()

    def test_no_consumer_projection_returns_the_same_plan(self):
        plan = OptimizationPlan(
            select_related=["category"],
            planned_resolver_keys=["category-key"],
        ).finalize()
        from django_strawberry_framework.optimizer.plans import (
            prune_unsupportable_select_related,
        )

        assert prune_unsupportable_select_related(plan, Item.objects.all()) is plan


def test_consumer_projection_and_traversal_defensive_shapes():
    """``_consumer_projection`` / ``_select_path_traversable`` defensive tails.

    Non-queryset inputs and malformed ``deferred_loading`` shapes report no
    projection (the prune then no-ops), and a scalar mid-path segment - no
    related model to resolve the next segment against - is conservatively
    untraversable. None of these shapes is producible by a real consumer
    queryset, so the tails are pinned directly in one sweep.
    """
    from apps.library.models import Book

    from django_strawberry_framework.optimizer.plans import (
        _consumer_projection,
        _select_path_traversable,
    )

    assert _consumer_projection(SimpleNamespace()) is None
    malformed = SimpleNamespace(query=SimpleNamespace(deferred_loading=("only-one",)))
    assert _consumer_projection(malformed) is None
    assert _select_path_traversable("title__upper", frozenset({"title"}), False, Book) is False
