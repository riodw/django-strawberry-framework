"""Tests for ``optimizer/walker.py``.

The walker is a pure function (``plan_optimizations``) tested in
isolation against synthetic selection objects — no Strawberry execution
required. This makes the three load-bearing details (fragments, aliases,
``@skip``/``@include``) each testable with a tight, focused case.

All tests use ``SimpleNamespace`` objects mimicking Strawberry's
``SelectedField`` / ``FragmentSpread`` / ``InlineFragment`` shape.
The walker dispatches on duck-typed attributes (``name``, ``alias``,
``directives``, ``selections``, ``type_condition``), so synthetic
objects exercise exactly the same code paths as real Strawberry nodes.

Nested prefetch chains, FK-id elision, optimizer hints, and ``Prefetch``
downgrades extend this same walker surface.
"""

from types import SimpleNamespace

import pytest
from apps.products.models import Category, Entry, Item
from django.db import models
from django.db.models import Prefetch

from django_strawberry_framework import OptimizerHint
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.optimizer.field_meta import FieldMeta
from django_strawberry_framework.optimizer.walker import (
    _ensure_connector_only_fields,
    _is_fragment,
    _merge_aliased_selections,
    _prefetch_hint_for_path,
    _selected_scalar_names,
    _should_include,
    plan_optimizations,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.utils.strings import snake_case

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


def _register_type_definition(model, type_cls, *, optimizer_hints=None, field_map=None, primary=False):
    """Register a minimal definition for walker-only synthetic type classes."""
    selected_fields = tuple(model._meta.get_fields())
    registry.register(model, type_cls, primary=primary)
    registry.register_definition(
        type_cls,
        DjangoTypeDefinition(
            origin=type_cls,
            model=model,
            name=None,
            description=None,
            fields_spec=None,
            exclude_spec=None,
            selected_fields=selected_fields,
            field_map=field_map
            if field_map is not None
            else {snake_case(field.name): FieldMeta.from_django_field(field) for field in selected_fields},
            optimizer_hints=optimizer_hints or {},
            has_custom_get_queryset=type_cls.has_custom_get_queryset(),
        ),
    )


# ---------------------------------------------------------------------------
# plan_optimizations — cardinality dispatch
# ---------------------------------------------------------------------------


def test_plan_returns_empty_for_scalar_only_selection():
    """Selecting only scalars produces an ``only()`` projection but no relations."""
    plan = plan_optimizations([_sel("name"), _sel("id")], Category)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("name", "id")


def test_plan_dispatches_forward_fk_to_select_related():
    """A forward FK selection routes to ``select_related``."""
    plan = plan_optimizations([_sel("category")], Item)
    assert plan.select_related == ("category",)
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("category_id",)


def test_plan_dispatches_reverse_fk_to_prefetch_related():
    """A reverse FK selection routes to ``prefetch_related``."""
    plan = plan_optimizations([_sel("items")], Category)
    assert plan.select_related == ()
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "items"


def test_plan_dispatches_mixed_relations():
    """Forward FK and reverse FK in one selection produce both bags."""
    plan = plan_optimizations(
        [_sel("category"), _sel("entries")],
        Item,
    )
    assert plan.select_related == ("category",)
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "entries"
    assert plan.only_fields == ("category_id",)


def test_plan_skips_unknown_selections():
    """Selections not on the Django model are silently skipped."""
    plan = plan_optimizations([_sel("bogusField")], Category)
    assert plan.is_empty


def test_plan_relay_id_projects_real_pk_attname_when_not_id(monkeypatch):
    """Regression for ``docs/feedback.md`` § custom-pk Relay projection.

    When a Relay-declared ``DjangoType`` is backed by a model whose pk
    attname is not ``"id"``, ``snake_case("id")`` does not match the
    field-map's real key. The walker must resolve the configured
    ``id_attr`` (via ``type_cls.resolve_id_attr()``) and project that
    column into ``only()`` so ``_resolve_id_default`` reads the loaded
    value from ``root.__dict__`` instead of falling back to ``getattr``
    and triggering a lazy load (Decision 7).

    Simulates the custom-pk shape without adding a new fakeshop model:
    monkey-patches ``Category._meta.pk.attname`` and the registered
    definition field map to drop the ``"id"`` key while keeping
    ``"name"`` as the stand-in pk projection.
    """
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class CategoryNode(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)

        finalize_django_types()
        definition = registry.get_definition(CategoryNode)
        fake_field_map = {k: v for k, v in definition.field_map.items() if k != "id"}
        monkeypatch.setattr(definition, "field_map", fake_field_map)
        monkeypatch.setattr(Category._meta.pk, "attname", "name")

        plan = plan_optimizations([_sel("id")], Category)

        assert "name" in plan.only_fields
        assert "id" not in plan.only_fields
    finally:
        registry.clear()


def test_plan_relay_id_projects_attname_when_pk_is_relation():
    """Regression for ``docs/feedback.md`` § walker ``id_attr in field_map`` mismatch.

    When a Relay-declared ``DjangoType`` is backed by a model whose
    primary key is a relation (e.g. ``OneToOneField(primary_key=True)``
    or ``ForeignKey(primary_key=True)``), the pk's ``name`` and
    ``attname`` differ: ``name="user"`` vs. ``attname="user_id"``. The
    walker's projection branch resolves ``id_attr`` to the attname
    (``"user_id"``), but ``field_map`` is keyed by the field's ``name``
    (``"user"``). A naive ``id_attr in field_map`` check would skip
    projection and re-introduce the lazy-load N+1 the fix was meant to
    close. The walker must scan the ``FieldMeta`` values by both
    ``name`` and ``attname``.
    """
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    class UserTarget(models.Model):
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "tests"
            managed = False

    class ProfileSource(models.Model):
        user = models.OneToOneField(
            UserTarget,
            on_delete=models.CASCADE,
            primary_key=True,
            related_name="profile_for_test",
        )
        bio = models.CharField(max_length=32)

        class Meta:
            app_label = "tests"
            managed = False

    registry.clear()
    try:

        class UserTargetNode(DjangoType):
            class Meta:
                model = UserTarget
                fields = ("name",)

        class ProfileNode(DjangoType):
            class Meta:
                model = ProfileSource
                fields = ("user", "bio")
                interfaces = (relay.Node,)

        finalize_django_types()
        plan = plan_optimizations([_sel("id")], ProfileSource)

        # ``id_attr`` resolves to ``"user_id"`` (the pk's attname). The
        # walker must locate the matching ``FieldMeta`` via its
        # ``attname`` (the ``"user"`` FieldMeta has ``name="user"``,
        # ``attname="user_id"``) and project ``"user_id"`` so Django's
        # ``.only("user_id")`` loads the FK column without dragging in
        # the related ``UserTarget`` row.
        assert "user_id" in plan.only_fields
    finally:
        registry.clear()


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

    assert plan.prefetch_related == ("generic",)
    assert plan.planned_resolver_keys == ("generic@generic",)


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

    assert plan.select_related == ("relation",)
    assert plan.only_fields == ("relation_id",)
    assert plan.fk_id_elisions == ()


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


def test_merge_aliased_selections_logs_when_arguments_diverge(caplog):
    """Aliased selections with different ``arguments`` emit a DEBUG signal.

    Today's walker ignores ``arguments``, so divergence is harmless and
    merge proceeds.  The DEBUG line exists so the future optimizer slice
    that begins planning per-argument has an immediate trace pointing
    at this branch.
    """
    sel_a = SimpleNamespace(
        name="items",
        alias="first",
        directives={},
        arguments={"active": True},
        selections=[_sel("id")],
    )
    sel_b = SimpleNamespace(
        name="items",
        alias="second",
        directives={},
        arguments={"active": False},
        selections=[_sel("name")],
    )

    with caplog.at_level("DEBUG", logger="django_strawberry_framework"):
        merged = _merge_aliased_selections([sel_a, sel_b])

    # Merge still proceeds; the first occurrence's ``arguments`` are kept.
    assert len(merged) == 1
    assert merged[0].arguments == {"active": True}
    assert merged[0]._optimizer_response_keys == ["first", "second"]
    assert any("different arguments" in record.message for record in caplog.records)


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
    assert plan.planned_resolver_keys == ("items@first", "items@second")


# ---------------------------------------------------------------------------
# O5 — only() projection
# ---------------------------------------------------------------------------


def test_plan_collects_only_fields_for_selected_scalars():
    """O5: scalar selections are collected into ``only_fields``."""
    plan = plan_optimizations([_sel("id"), _sel("name")], Category)
    assert plan.only_fields == ("id", "name")
    assert plan.select_related == ()
    assert plan.prefetch_related == ()


def test_plan_includes_fk_columns_in_only_fields():
    """O5: select_related FK traversals include the source FK column."""
    plan = plan_optimizations(
        [_sel("name"), _sel("category", selections=[_sel("name")])],
        Item,
    )
    assert plan.select_related == ("category",)
    assert plan.only_fields == ("name", "category_id", "category__name")


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
    assert plan.only_fields == ("category_id", "category__id", "category__name")


# ---------------------------------------------------------------------------
# B2 — Forward-FK-id elision
# ---------------------------------------------------------------------------


def test_plan_elides_forward_fk_when_child_selection_is_id_only():
    """B2: ``category { id }`` uses ``category_id`` instead of a JOIN."""
    plan = plan_optimizations(
        [_sel("name"), _sel("category", selections=[_sel("id")])],
        Item,
    )
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("name", "category_id")
    assert plan.fk_id_elisions == ("category@category",)
    assert plan.planned_resolver_keys == ("category@category",)


def test_plan_elides_forward_fk_id_only_selection_for_each_alias():
    """B2/O4: duplicate aliases keep distinct resolver keys for FK-id elision."""
    plan = plan_optimizations(
        [
            _sel("category", selections=[_sel("id")], alias="first"),
            _sel("category", selections=[_sel("id")], alias="second"),
        ],
        Item,
    )
    assert plan.select_related == ()
    assert plan.only_fields == ("category_id",)
    assert plan.fk_id_elisions == ("category@first", "category@second")
    assert plan.planned_resolver_keys == ("category@first", "category@second")


def test_plan_does_not_elide_forward_fk_when_extra_target_scalar_selected():
    """B2: ``category { id name }`` still needs ``select_related``."""
    plan = plan_optimizations(
        [_sel("category", selections=[_sel("id"), _sel("name")])],
        Item,
    )
    assert plan.select_related == ("category",)
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("category_id", "category__id", "category__name")
    assert plan.fk_id_elisions == ()


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
    assert plan.select_related == ()
    assert plan.only_fields == ("category_id",)
    assert plan.fk_id_elisions == ("category@category",)


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
    assert plan.select_related == ("category",)
    assert plan.only_fields == ("category_id",)
    assert plan.fk_id_elisions == ()


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

    assert plan.select_related == ()
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("category_id",)
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
    assert plan.select_related == ()
    assert plan.only_fields == ("target_id",)
    assert plan.fk_id_elisions == ("target@target",)


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
    assert plan.select_related == ("target",)
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("target_id", "target__id")


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

    assert plan.select_related == ("target",)
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("target_id", "target__id")


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

    assert plan.select_related == ()
    assert plan.only_fields == ("category_id",)
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

    assert plan.select_related == ("category",)
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("category_id", "category__name")
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

    assert plan.select_related == ()
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

    assert plan.select_related == ("item", "item__category")
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("item_id", "item__category_id", "item__category__name")


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
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(Item, ItemType, optimizer_hints={"entries": OptimizerHint.SKIP})
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
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(
        Category,
        CategoryType,
        optimizer_hints={"items": OptimizerHint.prefetch(explicit)},
    )
    try:
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("entries", selections=[_sel("value")])])],
            Category,
        )
    finally:
        registry.clear()

    assert plan.prefetch_related == (explicit,)


def test_plan_prefetch_obj_hint_on_forward_fk_adds_connector_column():
    """B4: explicit ``Prefetch`` hints on forward FKs keep the source FK column."""
    registry.clear()
    explicit = Prefetch("category", queryset=Category.objects.only("name"))

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(Item, ItemType, optimizer_hints={"category": OptimizerHint.prefetch(explicit)})
    try:
        plan = plan_optimizations([_sel("category", selections=[_sel("name")])], Item)
    finally:
        registry.clear()

    assert plan.prefetch_related == (explicit,)
    assert plan.only_fields == ("category_id",)
    assert plan.planned_resolver_keys == ("ItemType.category@category",)


def test_plan_prefetch_obj_hint_adapts_nested_selected_parent_prefix():
    """B4: type-relative explicit ``Prefetch`` hints are rooted at the current path."""
    registry.clear()
    explicit = Prefetch("items", queryset=Item.objects.only("name"))

    class CategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(
        Category,
        CategoryType,
        optimizer_hints={"items": OptimizerHint.prefetch(explicit)},
    )
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("items", selections=[_sel("name")])])],
            Item,
        )
    finally:
        registry.clear()

    assert plan.select_related == ("category",)
    assert plan.only_fields == ("category_id",)
    prefetch = _prefetch_entry(plan)
    assert prefetch is not explicit
    assert prefetch.prefetch_to == "category__items"
    assert prefetch.queryset.model is Item
    fields, is_deferred = prefetch.queryset.query.deferred_loading
    assert fields == {"name"}
    assert is_deferred is False


def test_plan_force_select_hint_uses_select_recursion():
    """B4: ``select_related`` hints flow through same-query recursion."""
    registry.clear()

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(Item, ItemType, optimizer_hints={"category": OptimizerHint.select_related()})
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("name"), _sel("items", selections=[_sel("name")])])],
            Item,
        )
    finally:
        registry.clear()

    assert plan.select_related == ("category",)
    assert plan.only_fields == ("category_id", "category__name")
    assert plan.planned_resolver_keys == ("ItemType.category@category", "items@category.items")
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "category__items"
    fields, is_deferred = prefetch.queryset.query.deferred_loading
    assert fields == {"name", "category_id"}
    assert is_deferred is False


def test_plan_force_select_hint_downgrades_for_custom_target_get_queryset():
    """B4+O6: ``force_select`` cannot override target visibility hooks."""
    registry.clear()
    calls = []

    class CategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return True

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset.filter(is_private=False)

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.register(Category, CategoryType)
    _register_type_definition(Item, ItemType, optimizer_hints={"category": OptimizerHint.select_related()})
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("name")])],
            Item,
        )
    finally:
        registry.clear()

    assert calls == [None]
    assert plan.select_related == ()
    assert plan.cacheable is False
    assert plan.only_fields == ("category_id",)
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "category"
    assert prefetch.queryset.model is Category
    assert prefetch.queryset.query.where


def test_plan_force_select_hint_raises_for_many_side_relation():
    """B4: ``force_select`` on a reverse-FK relation raises ``ConfigurationError`` at plan time.

    Django's ``select_related`` rejects reverse-FK / M2M paths at queryset execution.
    The walker catches the cardinality mismatch before dispatch so the consumer sees
    a typed error naming ``OptimizerHint.select_related()`` and the offending field
    instead of a deep Django ``FieldError`` stack trace.
    """
    registry.clear()

    class CategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(
        Category,
        CategoryType,
        optimizer_hints={"items": OptimizerHint.select_related()},
    )
    try:
        with pytest.raises(
            ConfigurationError,
            match=r"OptimizerHint\.select_related\(\) on CategoryType\.items",
        ):
            plan_optimizations([_sel("items", selections=[_sel("name")])], Category)
    finally:
        registry.clear()


def test_plan_no_flag_hint_falls_through_to_default_dispatch():
    """``OptimizerHint()`` with no flag set is a no-op: the walker falls back to default cardinality dispatch.

    Pins the ``_apply_hint`` ``return False`` branch.  The four documented
    factories (``SKIP``, ``select_related()``, ``prefetch_related()``,
    ``prefetch(...)``) all set exactly one flag, but a consumer who
    constructs ``OptimizerHint()`` with no args lands here.  The walker
    must treat it as if no hint were present, not silently skip the
    field or do something unexpected.
    """
    registry.clear()

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(Item, ItemType, optimizer_hints={"category": OptimizerHint()})
    try:
        plan = plan_optimizations([_sel("category", selections=[_sel("name")])], Item)
    finally:
        registry.clear()

    # Forward FK with non-id-only child → default dispatch picks select_related.
    assert plan.select_related == ("category",)
    assert plan.only_fields == ("category_id", "category__name")


def test_plan_records_nested_fk_id_elision_with_resolver_key():
    """O4+B2: FK-id elision inside a child plan uses the nested resolver key."""
    plan = plan_optimizations(
        [_sel("items", selections=[_sel("category", selections=[_sel("id")])])],
        Category,
    )

    outer = _prefetch_entry(plan)
    assert outer.prefetch_to == "items"
    assert plan.fk_id_elisions == ("category@items.category",)
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


def test_plan_merges_fragment_branches_before_prefetch_queryset_creation():
    """Same-relation fragment branches contribute one combined child projection."""
    plan = plan_optimizations(
        [
            _inline_fragment(
                "CategoryType",
                selections=[_sel("items", selections=[_sel("name")])],
            ),
            _inline_fragment(
                "CategoryType",
                selections=[_sel("items", selections=[_sel("description")])],
            ),
        ],
        Category,
    )

    assert len(plan.prefetch_related) == 1
    outer = _prefetch_entry(plan)
    assert outer.prefetch_to == "items"
    fields, is_deferred = outer.queryset.query.deferred_loading
    assert fields == {"name", "description", "category_id"}
    assert is_deferred is False


def test_ensure_connector_only_fields_adds_m2m_target_pk():
    """Connector injection supports M2M-style relation metadata."""
    # ``_ensure_connector_only_fields`` runs during walker construction,
    # before ``plan_optimizations`` finalises the plan into tuples.
    # Build a fresh mutable plan to mirror the walker-internal call site.
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan(only_fields=["name"])
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

    assert plan.only_fields == ("name",)
    assert any("could not resolve connector column" in r.message for r in caplog.records)


def test_plan_prefetch_obj_hint_marks_plan_non_cacheable():
    """B4: consumer-supplied Prefetch may close over request-scoped state; plan must not be cacheable.

    The hint.prefetch_obj queryset commonly carries user-scoped filters; serving
    the cached Prefetch across requests would leak the first request's state.
    Mirrors the has_custom_get_queryset cache-safety flip in _plan_prefetch_relation.
    """
    registry.clear()
    explicit = Prefetch("items", queryset=Item.objects.only("name"))

    class CategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(
        Category,
        CategoryType,
        optimizer_hints={"items": OptimizerHint.prefetch(explicit)},
    )
    try:
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("name")])],
            Category,
        )
    finally:
        registry.clear()

    assert plan.cacheable is False
    assert plan.prefetch_related == (explicit,)


def test_plan_prefetch_obj_hint_dedupes_repeat_lookups():
    """B4: hint.prefetch_obj routes through append_prefetch_unique so the same lookup is not appended twice.

    Without the dedupe, a re-walk over the same selection (e.g. fragment spread
    expanding the same field, or duplicate selections) yields two Prefetch
    entries for the same lookup path; Django's later attach replaces the first
    and silently drops the consumer's queryset depending on order.
    """
    registry.clear()
    explicit = Prefetch("items", queryset=Item.objects.only("name"))

    class CategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(
        Category,
        CategoryType,
        optimizer_hints={"items": OptimizerHint.prefetch(explicit)},
    )
    try:
        # Two sibling selections of the same field; _merge_aliased_selections
        # collapses them, but the dedupe guard is the load-bearing invariant
        # here — assert there is exactly one prefetch entry on the plan.
        plan = plan_optimizations(
            [
                _sel("items", selections=[_sel("name")]),
                _sel("items", selections=[_sel("name")]),
            ],
            Category,
        )
    finally:
        registry.clear()

    assert plan.prefetch_related == (explicit,)


def test_plan_tolerates_optimizer_hints_set_to_none():
    """Shape guard: definition.optimizer_hints = None must not raise.

    The definition field is typed as a dict, but defending the
    intersection ``set to None`` keeps the reader robust against
    misbehaving writers and matches the ``... or {}`` pattern used
    elsewhere in the package.
    """
    registry.clear()

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(Item, ItemType)
    registry.get_definition(ItemType).optimizer_hints = None
    try:
        plan = plan_optimizations([_sel("category", selections=[_sel("name")])], Item)
    finally:
        registry.clear()

    # With no hints, default dispatch picks select_related for a forward FK
    # with a non-id-only child selection.
    assert plan.select_related == ("category",)


def test_plan_tolerates_registered_type_without_definition():
    """Shape guard: a stale registered type without definition metadata has no hints."""
    registry.clear()

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.register(Item, ItemType)
    try:
        plan = plan_optimizations([_sel("category", selections=[_sel("name")])], Item)
    finally:
        registry.clear()

    assert plan.select_related == ("category",)


def test_prefetch_hint_for_path_rejects_prefetch_without_lookup():
    """B4: ``_prefetch_hint_for_path`` raises when the Prefetch carries no lookup path.

    ``Prefetch`` always sets ``prefetch_through`` from its first positional arg,
    so the ``None`` branch is reachable only when a malformed surrogate is
    passed in.  A duck-typed object with ``prefetch_through is None`` surfaces
    the defensive guard so the consumer learns about a missing lookup at plan
    time, not as a silent missed prefetch downstream. The pin also covers the
    ``type_name.field_name`` attribution so a future cosmetic refactor cannot
    silently drop the type name from the error.
    """
    no_lookup = SimpleNamespace(prefetch_through=None, queryset=None, to_attr=None)

    with pytest.raises(
        ConfigurationError,
        match=r"OptimizerHint\.prefetch\(obj\) on CategoryType\.items "
        r"requires a Prefetch with a lookup path",
    ):
        _prefetch_hint_for_path(
            no_lookup,
            django_name="items",
            full_path="category__items",
            type_name="CategoryType",
        )


def test_prefetch_hint_for_path_adapts_nested_lookup_under_parent():
    """B4: a type-relative nested ``Prefetch`` lookup is rebased onto ``full_path``.

    When the hint is declared as ``Prefetch("items__entries", ...)`` on
    ``CategoryType.items`` and the walker reaches that relation through
    ``Item.category``, the planned lookup is ``"category__items__entries"``.
    The original queryset and ``to_attr`` survive the rebuild.
    """
    qs = Entry.objects.only("value")
    explicit = Prefetch("items__entries", queryset=qs, to_attr="bucket")

    rebased = _prefetch_hint_for_path(
        explicit,
        django_name="items",
        full_path="category__items",
        type_name="CategoryType",
    )

    assert rebased is not explicit
    assert rebased.prefetch_through == "category__items__entries"
    assert rebased.queryset is qs
    assert rebased.to_attr == "bucket"


def test_prefetch_hint_for_path_rejects_mismatched_lookup():
    """B4: a ``Prefetch`` lookup that does not target the hinted relation raises.

    The walker treats the hint as type-relative.  ``Prefetch("items", ...)`` on
    ``CategoryType.items`` is the simple case; ``Prefetch("items__entries", ...)``
    is the nested-adaptation case.  ``Prefetch("unrelated_relation", ...)``
    cannot be rebased onto the current ``full_path`` and is rejected so the
    consumer learns about the misconfiguration at plan time.
    """
    explicit = Prefetch("unrelated_relation", queryset=Entry.objects.all())

    with pytest.raises(
        ConfigurationError,
        match=r"OptimizerHint\.prefetch\(obj\) lookup on CategoryType\.items "
        r"must target the hinted relation 'items'",
    ):
        _prefetch_hint_for_path(
            explicit,
            django_name="items",
            full_path="category__items",
            type_name="CategoryType",
        )


def test_ensure_connector_only_fields_adds_reverse_o2o_connector():
    """A reverse ``OneToOneRel`` prefetch must project the forward FK column.

    When prefetching a reverse one-to-one relation, the child queryset
    needs the forward FK column so Django can bind each child row back
    to its parent. Without this projection, accessing the reverse
    attribute reintroduces a lazy load (matching the reverse-FK branch
    behavior in ``_ensure_connector_only_fields``).
    """
    from apps.library.models import Patron

    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan(only_fields=["id"])
    parent_field = Patron._meta.get_field("card")
    _ensure_connector_only_fields(plan, parent_field)

    assert "patron_id" in plan.only_fields


# ---------------------------------------------------------------------------
# Slice 4 — H2 root origin-type propagation
# ---------------------------------------------------------------------------


def test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary():
    """H2: a root resolver returning a secondary plans from the secondary's hints.

    Register an ``ItemType`` primary with ``OptimizerHint.SKIP`` on
    ``category`` and an ``AdminItemType`` secondary with
    ``OptimizerHint.force_prefetch()`` on ``category``. With
    ``source_type=AdminItemType``, the planner must use the secondary's
    hint (force_prefetch), not the primary's SKIP. Without the H2
    threading, ``_resolve_field_map(Item)`` would route through
    ``registry.get(Item)`` -> ``ItemType``, and the SKIP would suppress
    the relation entirely.
    """
    registry.clear()

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    class AdminItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(
        Item,
        ItemType,
        optimizer_hints={"category": OptimizerHint.SKIP},
        primary=True,
    )
    _register_type_definition(
        Item,
        AdminItemType,
        optimizer_hints={"category": OptimizerHint.prefetch_related()},
    )
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("name")])],
            Item,
            source_type=AdminItemType,
        )
    finally:
        registry.clear()

    # AdminItemType's force_prefetch wins; the prefetch_related bag is populated
    # and select_related stays empty.
    assert plan.select_related == ()
    assert len(plan.prefetch_related) == 1


def test_scalar_only_secondary_resolver_uses_secondary_field_map():
    """H2 rev6 M1: a scalar-only selection routes through the root path.

    Register an ``ItemType`` primary with a field_map missing ``name``
    and an ``AdminItemType`` secondary with a field_map including
    ``name``. With ``source_type=AdminItemType`` the root planner uses
    the secondary's field_map; without it the primary's lookup would
    treat ``name`` as unknown and drop the only-field projection.
    """
    registry.clear()

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    class AdminItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    # Primary's field_map omits ``name``.
    primary_fields = tuple(f for f in Item._meta.get_fields() if f.name != "name")
    primary_field_map = {
        snake_case(field.name): FieldMeta.from_django_field(field) for field in primary_fields
    }
    _register_type_definition(Item, ItemType, field_map=primary_field_map, primary=True)
    # Secondary's field_map includes ``name``.
    _register_type_definition(Item, AdminItemType)
    try:
        plan = plan_optimizations(
            [_sel("name")],
            Item,
            source_type=AdminItemType,
        )
    finally:
        registry.clear()

    # Secondary's field_map includes ``name`` so the only-field projection lands.
    assert "name" in plan.only_fields


def test_optimizer_walker_uses_primary_for_nested_relation_target():
    """H2 nested contract: nested relation lookup still routes through the primary.

    Multi-type ``Item`` (``ItemType`` primary, ``AdminItemType``
    secondary) reached via a nested ``CategoryType.items`` relation.
    Even without ``source_type`` on the root call, the walker descends
    into the nested ``items`` step with ``source_type=None`` and routes
    through ``registry.get(Item)`` -> ``ItemType``. The primary's
    field_map (which omits ``name`` in this fixture) drives the nested
    only_fields projection, confirming the nested target picks the
    primary and not the secondary.
    """
    registry.clear()

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    class AdminItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    class CategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    # Primary ItemType field_map deliberately omits ``name`` so we can
    # detect which type's field_map was used for the nested step.
    primary_fields = tuple(f for f in Item._meta.get_fields() if f.name != "name")
    primary_field_map = {
        snake_case(field.name): FieldMeta.from_django_field(field) for field in primary_fields
    }
    _register_type_definition(Item, ItemType, field_map=primary_field_map, primary=True)
    _register_type_definition(Item, AdminItemType)
    _register_type_definition(Category, CategoryType)
    try:
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("name"), _sel("id")])],
            Category,
        )
    finally:
        registry.clear()

    # The nested step uses ItemType's field_map (primary), which omits
    # ``name``. So the prefetch's child queryset only_fields excludes
    # ``name`` even though the selection asked for it.
    prefetch = _prefetch_entry(plan)
    assert isinstance(prefetch, Prefetch)
    # The primary's field_map is what drove the nested resolution: the
    # child queryset's only-fields contain ``id`` (which IS in the
    # primary's field_map) but not ``name`` (which is NOT).
    child_qs = prefetch.queryset
    assert child_qs is not None
    only_clause = set(child_qs.query.deferred_loading[0])
    assert "id" in only_clause
    assert "name" not in only_clause
