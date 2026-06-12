"""Tests for ``optimizer/plans.py`` - ``OptimizationPlan`` data structure.

The plan is a simple dataclass, so the test surface is small and focused
on the ``is_empty`` property and the ``apply`` method. The walker tests
in ``test_walker.py`` exercise construction; these tests verify that the
plan's own methods work correctly in isolation.
"""

from types import SimpleNamespace

import pytest
from apps.products.models import Category, Entry, Item, Property
from django.db.models import Prefetch

from django_strawberry_framework.optimizer.plans import (
    _MAX_PATH_DEPTH,
    OptimizationPlan,
    _consumer_only_fields,
    _flatten_select_related,
    diff_plan_for_queryset,
    lookup_paths,
    resolver_key,
    runtime_path_from_path,
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
        or any other unpacking-incompatible value falls through to ``None``
        instead of crashing the optimizer.
        """
        bad_three_tuple = SimpleNamespace(
            query=SimpleNamespace(
                deferred_loading=(set(), False, "extra"),
            ),
        )
        bad_scalar = SimpleNamespace(query=SimpleNamespace(deferred_loading=42))
        assert _consumer_only_fields(bad_three_tuple) is None
        assert _consumer_only_fields(bad_scalar) is None

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
