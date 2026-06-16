"""Selection-walker tests for GraphQL selection to ORM OptimizationPlan conversion.

The walker is a pure function (``plan_optimizations``) tested in
isolation against synthetic selection objects - no Strawberry execution
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
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.optimizer.walker import (
    _apply_hint,
    _ensure_connector_only_fields,
    _has_custom_id_resolver,
    _is_fragment,
    _merge_aliased_selections,
    _merge_runtime_prefixes,
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


def _sel(
    name,
    selections=None,
    directives=None,
    alias=None,
    arguments=None,
):
    """Build a synthetic ``SelectedField``."""
    return SimpleNamespace(
        name=name,
        alias=alias,
        directives=directives or {},
        arguments=arguments or {},
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


def _fragment_spread(
    name,
    type_condition,
    selections=None,
    directives=None,
):
    """Build a synthetic ``FragmentSpread``."""
    return SimpleNamespace(
        name=name,
        type_condition=type_condition,
        directives=directives or {},
        selections=selections or [],
    )


def _register_type_definition(
    model,
    type_cls,
    *,
    optimizer_hints=None,
    field_map=None,
    primary=False,
):
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
            else {
                snake_case(field.name): FieldMeta.from_django_field(field)
                for field in selected_fields
            },
            optimizer_hints=optimizer_hints or {},
            has_custom_get_queryset=type_cls.has_custom_get_queryset(),
        ),
    )


# ---------------------------------------------------------------------------
# plan_optimizations - cardinality dispatch
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
    """Regression: custom-pk Relay projection (the model pk attname is not ``"id"``).

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
    """Regression: walker ``id_attr in field_map`` mismatch when the pk is a relation.

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
# _should_include - @skip / @include directives
# ---------------------------------------------------------------------------


def test_should_include_returns_true_by_default():
    """No directives -> included."""
    assert _should_include(_sel("name")) is True


def test_should_include_skips_when_skip_true():
    """``@skip(if: true)`` -> excluded."""
    sel = _sel("name", directives={"skip": {"if": True}})
    assert _should_include(sel) is False


def test_should_include_includes_when_skip_false():
    """``@skip(if: false)`` -> included."""
    sel = _sel("name", directives={"skip": {"if": False}})
    assert _should_include(sel) is True


def test_should_include_skips_when_include_false():
    """``@include(if: false)`` -> excluded."""
    sel = _sel("name", directives={"include": {"if": False}})
    assert _should_include(sel) is False


def test_should_include_includes_when_include_true():
    """``@include(if: true)`` -> included."""
    sel = _sel("name", directives={"include": {"if": True}})
    assert _should_include(sel) is True


def test_should_include_treats_unresolved_variable_as_selected():
    """A non-boolean directive value (e.g. unresolved variable) -> included."""
    # Strawberry normally resolves variables, but if one slips through
    # as None the walker treats it as "selected" defensively.
    sel = _sel("name", directives={"skip": {"if": None}})
    assert _should_include(sel) is True


def test_should_include_skip_true_beats_include_true():
    """``@skip(if: true) @include(if: true)`` -> excluded (skip wins)."""
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
# _is_fragment - fragment detection
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
# _merge_aliased_selections - alias normalization
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


def test_merge_runtime_prefixes_adopts_then_unions_connection_prefixes():
    """Connection-carried runtime prefixes are adopted, then order-preserving unioned.

    Pins the merge path used when aliased ``edges.node`` selections from
    ``_connection_node_child_selections`` collapse onto one merged selection.
    """
    merged = SimpleNamespace(_optimizer_runtime_prefixes=None)

    # First incoming with no existing prefixes -> adopt verbatim.
    _merge_runtime_prefixes(
        merged,
        SimpleNamespace(_optimizer_runtime_prefixes=[("conn", "edges", "node")]),
    )
    assert merged._optimizer_runtime_prefixes == [("conn", "edges", "node")]

    # Second incoming unions a new prefix while skipping the duplicate.
    _merge_runtime_prefixes(
        merged,
        SimpleNamespace(
            _optimizer_runtime_prefixes=[("conn", "edges", "node"), ("alias", "edges", "node")],
        ),
    )
    assert merged._optimizer_runtime_prefixes == [
        ("conn", "edges", "node"),
        ("alias", "edges", "node"),
    ]

    # Incoming ``None`` (a plain non-connection selection) is a no-op.
    _merge_runtime_prefixes(merged, SimpleNamespace(_optimizer_runtime_prefixes=None))
    assert merged._optimizer_runtime_prefixes == [
        ("conn", "edges", "node"),
        ("alias", "edges", "node"),
    ]


def test_merge_aliased_selections_preserves_per_response_key_arguments():
    """Aliased selections preserve each occurrence's ``arguments`` under its response key.

    Re-pinned for spec-033 Decision 6: the merge keeps the first occurrence's
    ``arguments`` as the merged selection's primary value (the pre-033
    first-args-win contract) AND records every occurrence's payload in
    ``_optimizer_response_key_arguments`` so a synthesized connection sibling's
    divergent pagination/sidecar arguments stay detectable
    (``_aliased_arguments_diverge``).
    """
    from django_strawberry_framework.optimizer.walker import _aliased_arguments_diverge

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

    merged = _merge_aliased_selections([sel_a, sel_b])

    # Merge still proceeds; the first occurrence's ``arguments`` are kept.
    assert len(merged) == 1
    assert merged[0].arguments == {"active": True}
    assert merged[0]._optimizer_response_keys == ["first", "second"]
    # Per-response-key payloads recorded for both aliases; divergence detected.
    assert merged[0]._optimizer_response_key_arguments == {
        "first": {"active": True},
        "second": {"active": False},
    }
    assert _aliased_arguments_diverge(merged[0]) is True


def test_aliased_arguments_diverge_false_without_per_key_map():
    """A selection carrying no per-response-key argument map cannot diverge.

    Selections built outside ``_merge_aliased_selections`` (direct test/helper
    callers, or a single non-aliased occurrence) carry no
    ``_optimizer_response_key_arguments``, so divergence detection returns
    ``False`` rather than raising (spec-033 Decision 6).
    """
    from django_strawberry_framework.optimizer.walker import _aliased_arguments_diverge

    assert _aliased_arguments_diverge(SimpleNamespace()) is False


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
# O5 - only() projection
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
# B2 - Forward-FK-id elision
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


def test_plan_uses_definition_custom_id_resolver_cache(monkeypatch):
    """B2: custom id resolver checks route through target definition metadata."""

    class CachedIdTarget(models.Model):
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "tests"
            managed = False

    class CachedIdSource(models.Model):
        target = models.ForeignKey(CachedIdTarget, on_delete=models.CASCADE)

        class Meta:
            app_label = "tests"
            managed = False

    class CachedIdTargetType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    registry.clear()
    _register_type_definition(CachedIdTarget, CachedIdTargetType)
    definition = registry.get_definition(CachedIdTargetType)
    assert definition is not None
    calls = []

    def has_custom_id_resolver_for(pk_name):
        calls.append(pk_name)
        return True

    monkeypatch.setattr(definition, "has_custom_id_resolver_for", has_custom_id_resolver_for)
    try:
        plan = plan_optimizations(
            [_sel("target", selections=[_sel("id")])],
            CachedIdSource,
        )
    finally:
        registry.clear()

    assert calls == ["id"]
    assert plan.select_related == ("target",)
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("target_id", "target__id")


def test_has_custom_id_resolver_fallback_matches_definition_path():
    """The definition-less fallback uses the same shared helper, so it agrees.

    Pins finding-2 (drift): when no ``DjangoTypeDefinition`` is registered for
    the target, ``_has_custom_id_resolver`` delegates to the same
    ``origin_has_custom_id_resolver`` free function the registered path uses.
    A plain consumer ``resolve_id`` counts as custom; the inherited
    Strawberry Relay default does not (the pre-fix raw ``__dict__`` fallback
    wrongly flagged the latter).
    """
    from strawberry import relay

    class PlainCustomTarget:
        def resolve_id(self):
            return "custom"

    class FrameworkDefaultTarget(relay.Node):
        pass

    registry.clear()
    assert registry.get_definition(PlainCustomTarget) is None
    assert registry.get_definition(FrameworkDefaultTarget) is None

    assert _has_custom_id_resolver(PlainCustomTarget, "id") is True
    assert _has_custom_id_resolver(FrameworkDefaultTarget, "id") is False
    # Guard rails: a ``None`` target / pk short-circuits to ``False``.
    assert _has_custom_id_resolver(None, "id") is False
    assert _has_custom_id_resolver(PlainCustomTarget, None) is False


# ---------------------------------------------------------------------------
# O6 - get_queryset + Prefetch downgrade
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
# O4 - nested prefetch chains
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

    _register_type_definition(
        Item,
        ItemType,
        optimizer_hints={"category": OptimizerHint.prefetch(explicit)},
    )
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

    _register_type_definition(
        Item,
        ItemType,
        optimizer_hints={"category": OptimizerHint.select_related()},
    )
    try:
        plan = plan_optimizations(
            [
                _sel(
                    "category",
                    selections=[_sel("name"), _sel("items", selections=[_sel("name")])],
                ),
            ],
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
    _register_type_definition(
        Item,
        ItemType,
        optimizer_hints={"category": OptimizerHint.select_related()},
    )
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

    # Forward FK with non-id-only child -> default dispatch picks select_related.
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
        # here - assert there is exactly one prefetch entry on the plan.
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("name")]), _sel("items", selections=[_sel("name")])],
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


def test_apply_hint_prefetch_obj_misconfigured_lookup_leaves_plan_clean():
    """B4: ``_apply_hint`` must NOT mutate ``plan`` when ``_prefetch_hint_for_path`` raises.

    The ``prefetch_obj`` branch validates the consumer-supplied Prefetch
    via ``_prefetch_hint_for_path`` before recording the resolver identity
    or flipping ``plan.cacheable``. The current call path raises
    ``ConfigurationError`` out of ``plan_optimizations`` and the
    partially-mutated plan is unreachable, but the invariant - "no plan
    mutation on a raised validator" - must hold so any future caller
    that catches ``ConfigurationError`` at this layer (e.g. a permissive
    mode toggle, a per-field ``try/except`` around ``_apply_hint``)
    cannot consume a plan with phantom ``planned_resolver_keys``,
    ``only_fields``, or ``cacheable=False`` for a relation that was
    never actually planned.
    """

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    plan = OptimizationPlan()
    baseline = (list(plan.only_fields), list(plan.planned_resolver_keys), plan.cacheable)

    explicit = Prefetch("unrelated_relation", queryset=Entry.objects.all())
    hint = OptimizerHint.prefetch(explicit)
    django_field = Item._meta.get_field("category")

    with pytest.raises(
        ConfigurationError,
        match=r"OptimizerHint\.prefetch\(obj\) lookup on ItemType\.category "
        r"must target the hinted relation 'category'",
    ):
        _apply_hint(
            hint,
            sel=_sel("category", selections=[_sel("name")]),
            django_field=django_field,
            django_name="category",
            type_cls=ItemType,
            target_type=None,
            plan=plan,
            prefix="",
            full_path="category",
            info=None,
            runtime_paths=((),),
            resolver_identities=("ItemType.category@category",),
        )

    assert (list(plan.only_fields), list(plan.planned_resolver_keys), plan.cacheable) == baseline


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
# Slice 4 - H2 root origin-type propagation
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


def test_walker_resolves_relation_targets_through_definition_metadata(monkeypatch):
    """Registered relation targets route through ``DjangoTypeDefinition.related_target_for``."""
    registry.clear()

    class CategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    class ItemType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    _register_type_definition(Category, CategoryType)
    _register_type_definition(Item, ItemType)
    definition = registry.get_definition(ItemType)
    assert definition is not None
    real_related_target_for = definition.related_target_for
    calls: list[str] = []

    def spy_related_target_for(field_name: str):
        calls.append(field_name)
        return real_related_target_for(field_name)

    monkeypatch.setattr(definition, "related_target_for", spy_related_target_for)
    try:
        plan = plan_optimizations(
            [_sel("category", selections=[_sel("name")])],
            Item,
            source_type=ItemType,
        )
    finally:
        registry.clear()

    assert calls == ["category"]
    assert plan.select_related == ("category",)


# ---------------------------------------------------------------------------
# spec-033 Slice 1 - nested connection recognition + windowed-Prefetch planning
# ---------------------------------------------------------------------------


def _fake_info(relay_max_results=100):
    """Build a minimal ``info`` exposing ``schema.config.relay_max_results`` and ``path``.

    ``SliceMetadata.from_arguments`` reads ``info.schema.config.relay_max_results``
    when ``max_results`` is left ``None``; the walker reads ``info.path`` for
    runtime-path identity. Nothing else on ``info`` is touched at plan time.
    """
    return SimpleNamespace(
        schema=SimpleNamespace(config=SimpleNamespace(relay_max_results=relay_max_results)),
        path=None,
        variable_values={},
    )


def _conn_sel(
    name,
    *,
    node_selections=None,
    arguments=None,
    alias=None,
    scalar_children=None,
):
    """Build a synthetic connection selection (``edges { node { ... } }`` wrapper)."""
    children = []
    if scalar_children is not None:
        children.extend(_sel(child) for child in scalar_children)
    if node_selections is not None:
        node = _sel("node", selections=list(node_selections))
        children.append(_sel("edges", selections=[node]))
    return _sel(name, selections=children, alias=alias, arguments=arguments or {})


def _connection_relay_types():
    """Register ``GenreType`` / ``BookType`` / ``ShelfType`` with synthesized connections.

    Uses the real library M2M (``Genre.books`` reverse, ``Book.genres`` forward)
    and reverse-FK (``Shelf.books``) graph so synthesized ``<field>_connection``
    siblings exist and the partition derivation is exercised against real fields.
    """
    from apps.library.models import Book, Genre, Shelf
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")
            interfaces = (relay.Node,)

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name", "books")
            interfaces = (relay.Node,)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code", "books")
            interfaces = (relay.Node,)

    finalize_django_types()
    return {"Book": (Book, BookType), "Genre": (Genre, GenreType), "Shelf": (Shelf, ShelfType)}


class _OrderedTag(models.Model):
    name = models.CharField(max_length=32)

    class Meta:
        app_label = "products"
        managed = False


class _OrderedPost(models.Model):
    title = models.CharField(max_length=32)
    tag = models.ForeignKey(_OrderedTag, related_name="posts", on_delete=models.CASCADE)

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["title"]


def _ordered_connection_types():
    """Register Relay ``DjangoType``s over a child model with a NON-pk ``Meta.ordering``.

    The library/products fixtures order by pk only, so their deterministic window
    order is the pk alone. This pair (``_OrderedPost`` ordered by ``title``, a
    reverse FK off ``_OrderedTag.posts``) lets the non-pk ordering path
    (``("title", "id")``) be pinned for the generated prefetch's ``ORDER BY`` and
    for the scalar-only projection so ``_concrete_order_columns`` is exercised
    against a real non-pk column. ``managed=False`` needs no table - planning
    builds the queryset lazily and never executes it.
    """
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    class OrderedPostType(DjangoType):
        class Meta:
            model = _OrderedPost
            fields = ("id", "title")
            interfaces = (relay.Node,)

    class OrderedTagType(DjangoType):
        class Meta:
            model = _OrderedTag
            fields = ("id", "name", "posts")
            interfaces = (relay.Node,)

    finalize_django_types()
    return {"Tag": (_OrderedTag, OrderedTagType), "Post": (_OrderedPost, OrderedPostType)}


def test_windowed_prefetch_queryset_carries_non_pk_deterministic_order():
    """The generated prefetch's ``ORDER BY`` is the non-pk ``(title, pk)`` tuple.

    The pk-only variant cannot catch a refactor that special-cases pk ordering;
    this pins that a real ``Meta.ordering`` column propagates to the queryset's
    own ``ORDER BY`` (spec-033 Decision 11, cursor-parity / Revision 3).
    """
    registry.clear()
    try:
        types = _ordered_connection_types()
        tag_model, tag_type = types["Tag"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "postsConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            tag_model,
            info=_fake_info(),
            source_type=tag_type,
        )
        prefetch = _prefetch_entry(plan)
        assert tuple(prefetch.queryset.query.order_by) == ("title", "id")
    finally:
        registry.clear()


def test_scalar_only_window_projects_non_pk_order_column():
    """A scalar-only window over a non-pk-ordered target projects the order column.

    Covers ``_concrete_order_columns`` against a real ``Meta.ordering`` column:
    the projection must carry pk + reverse-FK connector + the ``title`` order
    column, not the full row (spec-033 Decision 6 / Revision 3).
    """
    registry.clear()
    try:
        types = _ordered_connection_types()
        tag_model, tag_type = types["Tag"]
        plan = plan_optimizations(
            [_conn_sel("postsConnection", scalar_children=["totalCount"], arguments={"first": 3})],
            tag_model,
            info=_fake_info(),
            source_type=tag_type,
        )
        prefetch = _prefetch_entry(plan)
        only_fields, defer = prefetch.queryset.query.deferred_loading
        assert defer is False
        # pk + reverse-FK connector (tag_id) + the non-pk ORDER column (title).
        assert {"id", "tag_id", "title"} <= set(only_fields)
    finally:
        registry.clear()


def test_concrete_order_columns_resolves_expression_relspan_and_attname_entries():
    """``_concrete_order_columns`` handles all three order-entry shapes against a real model.

    One pass over ``Book`` exercises every branch: an ``OrderBy(F("title"))``
    resolves through ``_order_entry_field_name``'s expression arm to the local
    ``title`` column; a related-span ``"shelf__code"`` is skipped (its column is
    referenced in SQL regardless of the ``.only()`` projection, so a scalar-only
    selection never needs it loaded); and a raw FK attname ``"shelf_id"`` (an
    attname, not a field NAME) is accepted directly (spec-033 Decision 4
    scalar-only projection).
    """
    from apps.library.models import Book
    from django.db.models import F, OrderBy

    from django_strawberry_framework.optimizer.walker import _concrete_order_columns

    columns = _concrete_order_columns(
        [OrderBy(F("title")), "shelf__code", "shelf_id"],
        Book,
    )
    assert columns == ["title", "shelf_id"]


def test_plan_connection_relation_unknown_field_is_noop():
    """A recognized connection whose relation field is absent from the field map is a no-op.

    Defensive guard: ``field_map.get`` returns ``None``, so no window prefetch is
    planned and no resolver key recorded - the selection falls back per-parent.
    """
    from apps.library.models import Genre

    from django_strawberry_framework.optimizer.walker import _plan_connection_relation

    plan = OptimizationPlan()
    _plan_connection_relation(
        _conn_sel("booksConnection", node_selections=[_sel("id")], arguments={"first": 2}),
        None,
        relation_field_name="absent_relation",
        field_map={},
        plan=plan,
        prefix="",
        info=_fake_info(),
        runtime_prefixes=((),),
        type_cls=None,
        model=Genre,
    )
    assert not plan.prefetch_related
    assert not plan.planned_resolver_keys


def test_plan_connection_relation_field_without_related_model_is_noop():
    """A relation field whose ``related_model`` is ``None`` is left unplanned (defensive)."""
    from apps.library.models import Genre

    from django_strawberry_framework.optimizer.walker import _plan_connection_relation

    plan = OptimizationPlan()
    _plan_connection_relation(
        _conn_sel("booksConnection", node_selections=[_sel("id")], arguments={"first": 2}),
        None,
        relation_field_name="modelless",
        field_map={"modelless": SimpleNamespace(related_model=None)},
        plan=plan,
        prefix="",
        info=_fake_info(),
        runtime_prefixes=((),),
        type_cls=None,
        model=Genre,
    )
    assert not plan.prefetch_related
    assert not plan.planned_resolver_keys


def test_plan_connection_relation_non_windowable_partition_is_noop():
    """A relation with no windowable parent partition falls back per-parent (no window).

    Driving ``_plan_connection_relation`` against a forward FK (``Item.category``)
    reaches the partition step, where ``window_partition_for_prefetch`` raises
    ``OptimizerError`` for the non-windowable single-valued kind; the planner
    swallows it and leaves the selection unplanned (spec-033 Decision 6).
    """
    from django_strawberry_framework.optimizer.walker import _plan_connection_relation

    registry.clear()
    try:
        plan = OptimizationPlan()
        _plan_connection_relation(
            _conn_sel("categoryConnection", node_selections=[_sel("id")], arguments={"first": 2}),
            None,
            relation_field_name="category",
            field_map={"category": Item._meta.get_field("category")},
            plan=plan,
            prefix="",
            info=_fake_info(),
            runtime_prefixes=((),),
            type_cls=None,
            model=Item,
        )
        assert not plan.prefetch_related
        assert not plan.planned_resolver_keys
    finally:
        registry.clear()


def test_relation_connections_slot_recorded():
    """The synthesis records ``{generated: relation_field}`` for attached siblings only."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_def = registry.get_definition(types["Genre"][1])
        # Genre.books (reverse M2M) synthesizes booksConnection.
        assert genre_def.relation_connections == {"books_connection": "books"}
        shelf_def = registry.get_definition(types["Shelf"][1])
        assert shelf_def.relation_connections == {"books_connection": "books"}
    finally:
        registry.clear()


def test_relation_connections_slot_records_nothing_for_suppressed_shapes():
    """A ``"list"``-narrowed relation records no slot entry (suppressed shape)."""
    from apps.library.models import Book, Genre
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

        class GenreType(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)
                relation_shapes = {"books": "list"}

        finalize_django_types()
        genre_def = registry.get_definition(GenreType)
        # The "list" narrowing suppresses synthesis, so nothing is recorded.
        assert not (genre_def.relation_connections or {})
    finally:
        registry.clear()


def test_record_relation_connection_is_idempotent():
    """``_record_relation_connection`` lazily inits the slot and is idempotent.

    The re-entrancy branch (a partial-finalize rerun) and the first-attach
    branch share this writer; an idempotent dict assignment means the rerun
    records the same mapping the first attach did (spec-033 Decision 3).
    """
    from django_strawberry_framework.types.finalizer import _record_relation_connection

    definition = SimpleNamespace(relation_connections=None)
    _record_relation_connection(definition, "books_connection", "books")
    assert definition.relation_connections == {"books_connection": "books"}
    # Idempotent re-write (the marker-``continue`` branch path).
    _record_relation_connection(definition, "books_connection", "books")
    assert definition.relation_connections == {"books_connection": "books"}


def test_relation_connections_slot_recorded_on_partial_finalize_rerun(monkeypatch):
    """A partial finalize whose Phase 3 raised, then a re-run, still records the slot.

    Forces ``strawberry.type`` (Phase 3) to raise on the first
    ``finalize_django_types`` so the synthesis (Phase 2.5) has attached the
    marker-bearing connection field but ``finalized`` stays ``False``. The bare
    re-run takes the ``_SYNTHESIZED_RELATION_CONNECTION_MARKER`` early-``continue``
    branch, which must re-record the slot (spec-033 Decision 3 re-entrancy path).
    """
    from apps.library.models import Book, Genre
    from strawberry import relay

    import django_strawberry_framework.types.finalizer as finalizer_module
    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

        class GenreType(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)

        real_strawberry_type = finalizer_module.strawberry.type

        def boom(cls=None, *args, **kwargs):
            # Only the Phase-3 decoration of GenreType raises; synthesis
            # (Phase 2.5) internally calls ``strawberry.type`` to build the
            # connection class, which must still succeed.
            if cls is GenreType:
                raise RuntimeError("forced Phase 3 failure for re-entrancy test")
            return real_strawberry_type(cls, *args, **kwargs)

        # Synthesis (Phase 2.5) runs before Phase 3; make Phase 3 raise so the
        # marker is set but ``finalized`` stays False.
        monkeypatch.setattr(finalizer_module.strawberry, "type", boom)
        with pytest.raises(RuntimeError, match="forced Phase 3 failure"):
            finalize_django_types()
        genre_def = registry.get_definition(GenreType)
        # The first (raising) finalize already recorded the slot.
        assert genre_def.relation_connections == {"books_connection": "books"}
        # Wipe it and re-run with Phase 3 restored: the marker-``continue`` branch
        # must re-record the slot rather than skip it.
        genre_def.relation_connections = None
        monkeypatch.setattr(finalizer_module.strawberry, "type", real_strawberry_type)
        finalize_django_types()
        assert genre_def.relation_connections == {"books_connection": "books"}
    finally:
        registry.clear()


def test_nested_connection_planned_as_windowed_prefetch():
    """A nested connection plans a windowed ``Prefetch`` under the ``_dst_`` ``to_attr``."""
    from django_strawberry_framework.optimizer.plans import (
        WINDOW_ROW_NUMBER,
        WINDOW_TOTAL_COUNT,
    )

    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        prefetch = _prefetch_entry(plan)
        # The window lands on the reserved ``to_attr``, lookup stays the accessor.
        assert prefetch.to_attr == "_dst_books_connection"
        assert prefetch.prefetch_through == "books"
        annotations = prefetch.queryset.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT in annotations
        # Deterministic total order ends in the pk tiebreaker.
        assert prefetch.queryset.query.annotations  # window present
    finally:
        registry.clear()


def test_window_slice_from_first_after_literals():
    """Resolved ``first`` / ``after`` literals drive the window offset + limit.

    ``first`` arrives as the raw token STRING ``"3"`` from an inline Int literal
    (``convert_value`` returns ``IntValueNode.value``, a string); the walker
    coerces it so the window actually bounds to ``offset + first`` rather than
    silently leaving the page uncapped at ``relay_max_results``. The bound is
    asserted, not just annotation presence (the gap that hid the literal-string
    over-cap bug).
    """
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        # after cursor for offset 1 -> start 2; first 3 -> upper bound 5.
        from strawberry.relay.utils import to_base64

        after = to_base64("arrayconnection", "1")
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    # String values - exactly what ``convert_selections`` emits
                    # for inline Int literals (the real plan-time argument shape).
                    arguments={"first": "3", "after": after},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        prefetch = _prefetch_entry(plan)
        sql = str(prefetch.queryset.query).upper()
        assert "_DST_ROW_NUMBER" in sql
        # offset 2 (after "1") + first 3 -> the window is bounded to row 5, NOT
        # the relay_max_results cap of 100. Both the offset and the upper bound
        # must appear.
        assert "> 2" in sql
        assert "<= 5" in sql
    finally:
        registry.clear()


def test_window_slice_coerces_int_literal_strings():
    """``_coerce_pagination_int`` turns int-like strings to ints; passes others through.

    Guards the literal-vs-variable divergence: an inline Int literal arrives as
    a string (``"2"``), a resolved variable as an ``int`` (``2``); both must drive
    the slice. A non-int-castable value passes through so
    ``SliceMetadata.from_arguments`` reaches its own ``isinstance`` gate (the
    shipped malformed-value behavior) rather than the walker pre-judging it.
    """
    from django_strawberry_framework.optimizer.walker import _coerce_pagination_int

    assert _coerce_pagination_int("2") == 2
    assert _coerce_pagination_int(2) == 2
    assert _coerce_pagination_int(None) is None
    # Non-int-castable passes through untouched (SliceMetadata's isinstance gate
    # then skips the bound - the shipped behavior for a malformed value).
    assert _coerce_pagination_int("oops") == "oops"


def test_relay_max_results_from_optimizer_info_shapes():
    """``_relay_max_results_from_info`` reads the strawberry-wrapped schema config.

    The walker runs at the optimizer middleware layer where ``info.schema`` is a
    bare graphql-core ``GraphQLSchema`` with NO ``.config``; the config lives on
    ``schema._strawberry_schema.config``. The helper prefers that path, falls
    back to a bare ``schema.config`` (the ``_fake_info`` test stub), then ``None``.
    Without it ``SliceMetadata.from_arguments(max_results=None)`` would
    dereference ``info.schema.config`` and raise ``AttributeError`` in production.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer.walker import _relay_max_results_from_info

    # Production shape: bare GraphQLSchema-like with a wrapped strawberry schema.
    wrapped = SimpleNamespace(
        schema=SimpleNamespace(
            _strawberry_schema=SimpleNamespace(config=SimpleNamespace(relay_max_results=7)),
        ),
    )
    assert _relay_max_results_from_info(wrapped) == 7
    # Test-stub shape: ``schema.config`` directly (no ``_strawberry_schema``).
    assert _relay_max_results_from_info(_fake_info(relay_max_results=42)) == 42
    # No config anywhere -> None (engine default applies downstream).
    assert _relay_max_results_from_info(SimpleNamespace(schema=SimpleNamespace())) is None


def test_window_slice_from_variables():
    """Variable-supplied pagination resolves through the converted selection's values.

    Converted selections already carry resolved variable VALUES on
    ``sel.arguments`` (Strawberry resolves them during ``convert_selections``),
    so the walker reads the value the same way for a literal or a variable; the
    walker grows no second variable-resolution path (spec-033 Decision 3/4).

    The window BOUND is asserted (not just ``to_attr``) so this independently
    proves the resolved variable value drives the slice: a resolved variable
    arrives already as an ``int`` (``5``), distinct from the literals sibling's
    raw token STRING (``"3"``); both must bound the window. ``first: 5`` with no
    ``after`` bounds the window to row 5, NOT the ``relay_max_results`` cap of 100.
    """
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        # ``arguments`` carries the RESOLVED int value (5), as convert_selections
        # produces for a variable reference - NOT the raw token string a literal
        # arrives as.
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 5},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        prefetch = _prefetch_entry(plan)
        assert prefetch.to_attr == "_dst_books_connection"
        sql = str(prefetch.queryset.query).upper()
        assert "_DST_ROW_NUMBER" in sql
        # offset 0 + first 5 -> bounded to row 5, NOT the relay_max_results cap.
        assert "<= 5" in sql
        assert "<= 100" not in sql
    finally:
        registry.clear()


def test_window_last_only_uses_reversed_row_number():
    """A ``last``-only window annotates AND bounds the reversed row-number window.

    The annotation alone is insufficient: ``SliceMetadata`` sets
    ``end = sys.maxsize`` for a ``last``-only slice so ``expected is None``, and
    the bound must come from the literal ``last`` value. Without the
    ``_dst_row_number_reversed__lte`` filter the window would over-fetch every
    child row per parent (spec-033 Decision 4 reversed-row-number branch).
    """
    from django_strawberry_framework.optimizer.plans import WINDOW_ROW_NUMBER_REVERSED

    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [_conn_sel("booksConnection", node_selections=[_sel("title")], arguments={"last": 2})],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        prefetch = _prefetch_entry(plan)
        query = prefetch.queryset.query
        assert WINDOW_ROW_NUMBER_REVERSED in query.annotations
        # The reversed window MUST be bounded to ``last`` rows; assert the
        # ``__lte`` filter is present (the annotation without the bound is the
        # over-fetch bug this test guards against).
        sql = str(query).upper()
        assert WINDOW_ROW_NUMBER_REVERSED.upper() in sql
        assert "<= 2" in sql
    finally:
        registry.clear()


def test_window_respects_relay_max_results():
    """An over-cap ``first`` (> ``relay_max_results``) emits no window but records the key."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        # relay_max_results=5; first=10 raises ValueError in SliceMetadata ->
        # the malformed-slice fallback emits no window (error locality: the
        # pipeline raises the cap error) but records the resolver key so
        # strictness does not preempt it with a spurious "Unplanned N+1".
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 10},
                ),
            ],
            genre_model,
            info=_fake_info(relay_max_results=5),
            source_type=genre_type,
        )
        assert plan.prefetch_related == ()
        assert len(plan.planned_resolver_keys) >= 1
    finally:
        registry.clear()


def test_m2m_shared_child_partitions_per_parent():
    """A forward/reverse M2M window partitions by the parent key, not the child pk."""
    from apps.library.models import Book, Genre

    from django_strawberry_framework.optimizer.plans import window_partition_for_prefetch

    # Reverse M2M (Genre.books) partitions through the child's forward M2M field.
    assert window_partition_for_prefetch(Genre._meta.get_field("books")) == "genres"
    # Forward M2M (Book.genres) partitions by the reverse query name.
    assert window_partition_for_prefetch(Book._meta.get_field("genres")) == "books"


def test_nested_connection_two_level_recursion():
    """A window inside a window (the cookbook shape) plans both levels."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        # Genre { booksConnection { edges { node { genresConnection { edges { node { name } } } } } } }
        inner = _conn_sel(
            "genresConnection",
            node_selections=[_sel("name")],
            arguments={"first": 2},
        )
        plan = plan_optimizations(
            [_conn_sel("booksConnection", node_selections=[inner], arguments={"first": 3})],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        outer = _prefetch_entry(plan)
        assert outer.to_attr == "_dst_books_connection"
        # The outer window's child queryset carries the inner window prefetch.
        inner_prefetches = list(outer.queryset._prefetch_related_lookups)
        inner_to_attrs = [getattr(pf, "to_attr", None) for pf in inner_prefetches]
        assert "_dst_genres_connection" in inner_to_attrs
    finally:
        registry.clear()


def test_child_plan_projections_include_connector_and_ordering_columns():
    """The windowed child ``.only()`` includes the connector column from the edge selection."""
    registry.clear()
    try:
        types = _connection_relay_types()
        shelf_model, shelf_type = types["Shelf"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            shelf_model,
            info=_fake_info(),
            source_type=shelf_type,
        )
        prefetch = _prefetch_entry(plan)
        only_clause = set(prefetch.queryset.query.deferred_loading[0])
        # Reverse FK connector column (shelf_id) is force-included for attach.
        assert "shelf_id" in only_clause
    finally:
        registry.clear()


def test_scalar_only_pageinfo_and_total_count_are_window_planned():
    """``totalCount``-only / ``pageInfo``-only selections ARE planned (not fallbacks)."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [_conn_sel("booksConnection", scalar_children=["totalCount"], arguments={"first": 3})],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        prefetch = _prefetch_entry(plan)
        assert prefetch.to_attr == "_dst_books_connection"
        # Planned: resolver identity recorded so strictness stays silent.
        assert len(plan.planned_resolver_keys) >= 1
    finally:
        registry.clear()


def test_scalar_only_window_projects_pk_connector_and_order_columns():
    """A scalar-only window applies a minimal ``.only()`` instead of fetching full rows.

    Regression for the scalar-only over-fetch: ``pageInfo``/``totalCount``-only
    selections unwrap to ``[]`` node children, so historically no ``.only()`` was
    applied and the window fetched every model column. The page needs only the
    target pk, the relation connector column (here the reverse-FK ``shelf_id``),
    and the concrete ordering columns (spec-033 Decision 4 / Decision 6 scalar-only contract).
    """
    registry.clear()
    try:
        types = _connection_relay_types()
        shelf_model, shelf_type = types["Shelf"]
        plan = plan_optimizations(
            [_conn_sel("booksConnection", scalar_children=["totalCount"], arguments={"first": 3})],
            shelf_model,
            info=_fake_info(),
            source_type=shelf_type,
        )
        prefetch = _prefetch_entry(plan)
        only_fields, defer = prefetch.queryset.query.deferred_loading
        # An `.only()` projection (defer=False), not full-row loading or `.defer()`.
        assert defer is False
        # pk + reverse-FK connector both projected; Book is pk-ordered ("id").
        assert {"id", "shelf_id"} <= set(only_fields)
    finally:
        registry.clear()


def test_windowed_prefetch_queryset_carries_deterministic_order():
    """The generated ``Prefetch.queryset`` applies the deterministic ORDER BY.

    Regression for the windowed-ordering bug: the window expression alone orders
    only the row-number VALUES, so the queryset's own ``ORDER BY`` must carry the
    same deterministic tuple or the prefetched rows arrive in DB-natural order and
    the fast path diverges from the pipeline (spec-033 Decision 11, cursor-parity).
    ``Book`` has no ``Meta.ordering``, so the deterministic order is the pk alone.
    """
    registry.clear()
    try:
        types = _connection_relay_types()
        shelf_model, shelf_type = types["Shelf"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            shelf_model,
            info=_fake_info(),
            source_type=shelf_type,
        )
        prefetch = _prefetch_entry(plan)
        assert tuple(prefetch.queryset.query.order_by) == ("id",)
    finally:
        registry.clear()


def test_malformed_slice_arguments_emit_no_window_but_record_resolver_key():
    """A malformed ``after:`` cursor emits NO window but RECORDS the resolver key.

    Error-locality contract (spec-033 Decision 4 step f / Decision 8): the
    selection must NOT get a window prefetch (so the connection pipeline runs
    per-parent and raises its own cursor/pagination validation error), but the
    resolver identity IS recorded so the Slice-4 strictness check does not preempt
    that error with a spurious "Unplanned N+1" under ``"raise"``. This is the
    distinction from the other Decision-6 fallbacks (sidecar / distinct / hint),
    which stay fully unplanned so strictness CAN flag them.
    """
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3, "after": "not-a-valid-cursor"},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        assert plan.prefetch_related == ()
        # Recorded so strictness stays silent and the pipeline owns the error.
        assert len(plan.planned_resolver_keys) >= 1
    finally:
        registry.clear()


def test_fallback_not_planned_sidecar_input():
    """A nested connection carrying ``filter:`` / ``orderBy:`` is left unplanned."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3, "filter": object()},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        assert plan.prefetch_related == ()
        assert plan.planned_resolver_keys == ()
    finally:
        registry.clear()


def test_fallback_not_planned_divergent_aliases():
    """Divergent aliased pagination args fall back: NO window prefetch, NO resolver key."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 2},
                    alias="a",
                ),
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 5},
                    alias="b",
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        # Divergent aliases -> the wrong Prefetch / resolver-key entry is ABSENT.
        assert not any(
            getattr(pf, "to_attr", None) == "_dst_books_connection" for pf in plan.prefetch_related
        )
        assert plan.planned_resolver_keys == ()
    finally:
        registry.clear()


def test_fallback_not_planned_skip_hint():
    """An ``OptimizerHint.SKIP`` on the relation suppresses window planning."""
    from apps.library.models import Book, Genre
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

        class GenreType(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)
                optimizer_hints = {"books": OptimizerHint.SKIP}

        finalize_django_types()
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            Genre,
            info=_fake_info(),
            source_type=GenreType,
        )
        assert plan.prefetch_related == ()
        assert plan.planned_resolver_keys == ()
    finally:
        registry.clear()


def test_identical_alias_args_merge_and_plan():
    """Identical-argument aliases merge and ARE window-planned together."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                    alias="a",
                ),
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                    alias="b",
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        prefetch = _prefetch_entry(plan)
        assert prefetch.to_attr == "_dst_books_connection"
        # Both response keys recorded as planned (one resolver identity per key).
        assert len(plan.planned_resolver_keys) == 2
    finally:
        registry.clear()


def test_planned_resolver_keys_include_connection_field():
    """A planned connection records the field's resolver identity for strictness."""
    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        assert len(plan.planned_resolver_keys) == 1
        key = plan.planned_resolver_keys[0]
        # The key is built on the relation field name (books), not the generated attr.
        assert "books@" in key
    finally:
        registry.clear()


def test_both_shape_connection_to_attr_coexists_with_list_and_consumer_prefetch():
    """The list sibling, the connection window, and a consumer accessor prefetch coexist."""
    from apps.library.models import Genre

    from django_strawberry_framework.optimizer.plans import diff_plan_for_queryset

    registry.clear()
    try:
        types = _connection_relay_types()
        genre_model, genre_type = types["Genre"]
        plan = plan_optimizations(
            [
                _sel("books", selections=[_sel("title")]),
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        to_attrs = {getattr(pf, "to_attr", None) for pf in plan.prefetch_related}
        prefetch_throughs = {pf.prefetch_through for pf in plan.prefetch_related}
        # List sibling (no to_attr) and the window (to_attr) share lookup "books"
        # but distinct prefetch_to, so no Django duplicate-lookup error.
        assert None in to_attrs
        assert "_dst_books_connection" in to_attrs
        assert prefetch_throughs == {"books"}
        # A consumer accessor prefetch on "books" is reconciled against the plan:
        # the list sibling (a Prefetch carrying a queryset) losslessly absorbs the
        # consumer's bare "books" string, while the window (prefetch_to
        # "_dst_books_connection", a distinct lookup) passes through untouched. The
        # delta must therefore STILL carry both lookups un-merged - the
        # exact-match/absorption claim the Decision-4 ``to_attr``-isolation edge
        # case makes - not collapse one of them.
        consumer_qs = Genre.objects.prefetch_related("books")
        delta, _qs = diff_plan_for_queryset(plan.finalize(), consumer_qs)
        delta_to_attrs = {getattr(pf, "to_attr", None) for pf in delta.prefetch_related}
        assert None in delta_to_attrs
        assert "_dst_books_connection" in delta_to_attrs
        assert {pf.prefetch_through for pf in delta.prefetch_related} == {"books"}
    finally:
        registry.clear()


def test_visibility_target_window_flips_cacheable_false():
    """A windowed target overriding ``get_queryset`` flips ``plan.cacheable`` False."""
    from apps.library.models import Book, Genre
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

            @classmethod
            def get_queryset(cls, queryset, info):
                return queryset.filter(circulation_status="available")

        class GenreType(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)

        finalize_django_types()
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            Genre,
            info=_fake_info(),
            source_type=GenreType,
        )
        assert plan.cacheable is False
        prefetch = _prefetch_entry(plan)
        assert prefetch.to_attr == "_dst_books_connection"
    finally:
        registry.clear()


def test_distinct_child_queryset_left_unplanned_for_correct_total_count():
    """A ``.distinct()``-ing target ``get_queryset`` leaves the relation unplanned."""
    from apps.library.models import Book, Genre
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

            @classmethod
            def get_queryset(cls, queryset, info):
                # A visibility join that de-duplicates: window Count(1) OVER would
                # over-count pre-DISTINCT rows, so the window must not be planned.
                return queryset.distinct()

        class GenreType(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)

        finalize_django_types()
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            Genre,
            info=_fake_info(),
            source_type=GenreType,
        )
        # Distinct target -> per-parent fallback: no window prefetch, no resolver key.
        assert not any(
            getattr(pf, "to_attr", None) == "_dst_books_connection" for pf in plan.prefetch_related
        )
        assert plan.planned_resolver_keys == ()
    finally:
        registry.clear()


def _genre_books_connection_with_nested_relation_types(*, distinct):
    """Register ``GenreType`` / ``BookType`` (``BookType`` exposes the ``shelf`` FK).

    The node child ``shelf { id }`` is a nested RELATION, so the child plan
    generates a ``planned_resolver_keys`` / ``fk_id_elisions`` entry. A fallback
    connection must NOT leak that child metadata into the parent plan
    (spec-033 Decision 6 / DoD-4). When ``distinct`` is set, ``BookType`` adds a
    ``.distinct()``-ing ``get_queryset`` (the DISTINCT fallback); otherwise the
    caller supplies a malformed cursor for the malformed-slice fallback.
    """
    from apps.library.models import Book, Genre, Shelf
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            interfaces = (relay.Node,)

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            interfaces = (relay.Node,)

        if distinct:

            @classmethod
            def get_queryset(cls, queryset, info):
                return queryset.distinct()

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name", "books")
            interfaces = (relay.Node,)

    finalize_django_types()
    return Genre, GenreType


def test_distinct_fallback_does_not_leak_child_resolver_keys_into_parent():
    """A DISTINCT fallback with a nested-relation node child leaks NO parent metadata."""
    registry.clear()
    try:
        genre_model, genre_type = _genre_books_connection_with_nested_relation_types(distinct=True)
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("shelf", selections=[_sel("id")])],
                    arguments={"first": 3},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        # Falls back per-parent: no window prefetch and NO child metadata absorbed.
        assert not any(
            getattr(pf, "to_attr", None) == "_dst_books_connection" for pf in plan.prefetch_related
        )
        assert plan.planned_resolver_keys == ()
        assert plan.fk_id_elisions == ()
    finally:
        registry.clear()


def test_malformed_slice_fallback_does_not_leak_child_resolver_keys_into_parent():
    """A malformed-slice fallback with a nested-relation node child leaks NO CHILD metadata.

    The malformed-slice guard resolves before the child queryset is built, so no
    child plan exists to leak. The connection's OWN resolver key IS recorded (so
    strictness lets the pipeline raise the real cursor error - error locality),
    but the nested ``shelf`` child's resolver key and fk-id elisions must NOT
    appear on the parent plan.
    """
    registry.clear()
    try:
        genre_model, genre_type = _genre_books_connection_with_nested_relation_types(
            distinct=False,
        )
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("shelf", selections=[_sel("id")])],
                    arguments={"first": 3, "after": "not-a-valid-cursor"},
                ),
            ],
            genre_model,
            info=_fake_info(),
            source_type=genre_type,
        )
        assert not any(
            getattr(pf, "to_attr", None) == "_dst_books_connection" for pf in plan.prefetch_related
        )
        # The connection's own key is recorded (error-locality), but no CHILD
        # (``shelf``) key or fk-id elision leaked from a child build that never ran.
        assert plan.planned_resolver_keys == ("GenreType.books@booksConnection",)
        assert not any("shelf" in key for key in plan.planned_resolver_keys)
        assert plan.fk_id_elisions == ()
    finally:
        registry.clear()


def test_secondary_type_relation_shapes_nested_recognition():
    """Nested recognition reads the model's PRIMARY type's ``relation_connections``.

    The primary narrows ``books`` to ``"list"`` (no synthesis), so even though a
    secondary type synthesizes ``booksConnection``, nested recognition (which
    routes through the primary) does not window-plan it - it falls back
    per-parent (spec-033 Decision 3 primary-type contract).
    """
    from apps.library.models import Book, Genre
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

        class GenrePrimary(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)
                relation_shapes = {"books": "list"}
                primary = True

        class GenreSecondary(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)
                relation_shapes = {"books": "connection"}

        finalize_django_types()
        # Nested recognition routes through the primary (which narrowed to list),
        # so the connection is NOT window-planned at the nested level.
        plan = plan_optimizations(
            [
                _conn_sel(
                    "booksConnection",
                    node_selections=[_sel("title")],
                    arguments={"first": 3},
                ),
            ],
            Genre,
            info=_fake_info(),
        )
        assert not any(
            getattr(pf, "to_attr", None) == "_dst_books_connection" for pf in plan.prefetch_related
        )
    finally:
        registry.clear()


def test_window_subquery_wrap_preserves_only_mask_and_child_select_related():
    """Window annotations compose with a child ``.only()`` and a child ``select_related``."""
    from apps.library.models import Book, Genre, Shelf
    from strawberry import relay

    from django_strawberry_framework import DjangoType, finalize_django_types

    registry.clear()
    try:

        class ShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "code")
                interfaces = (relay.Node,)

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title", "shelf")
                interfaces = (relay.Node,)

        class GenreType(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name", "books")
                interfaces = (relay.Node,)

        finalize_django_types()
        # booksConnection { edges { node { title shelf { code } } } } -> child
        # plan carries select_related("shelf") + only(); window annotations ride.
        node_children = [_sel("title"), _sel("shelf", selections=[_sel("code")])]
        plan = plan_optimizations(
            [_conn_sel("booksConnection", node_selections=node_children, arguments={"first": 3})],
            Genre,
            info=_fake_info(),
            source_type=GenreType,
        )
        prefetch = _prefetch_entry(plan)
        child_qs = prefetch.queryset
        assert "shelf" in str(child_qs.query.select_related)
        # Window annotations are still present alongside the only() mask.
        from django_strawberry_framework.optimizer.plans import WINDOW_ROW_NUMBER

        assert WINDOW_ROW_NUMBER in child_qs.query.annotations
    finally:
        registry.clear()


# TODO(spec-035 Slice 2): add G2 operation-type projection-gating pins here.
# Pseudocode: build fake ``info`` objects whose operation is QUERY, MUTATION,
# SUBSCRIPTION, absent, and partial/operation-less; assert query plans still
# carry ``only_fields`` while non-query plans keep select/prefetch/fk elision but
# carry no root, connector, prefetch-child, or scalar-window column projection.
# Required named cases from the spec: mutation root drops ``only_fields`` but
# keeps select/prefetch, mutation to-one applied queryset has no deferred mask,
# mutation to-many ``Prefetch.queryset`` has no deferred mask, scalar-only
# connection window does not call ``.only(...)``, subscription is gated, and
# FK-id elision remains enabled under mutation.

# TODO(spec-035 Slice 3): add G3 walker narrowing pins here.
# Pseudocode: synthesize interface/union-like selection trees and registered
# DjangoType definitions; assert sibling concrete fragments are skipped whole,
# inherited-interface fragments still inline, same-named sibling relations do
# not over-plan, primary fragments skip under secondary roots but inline under
# primary roots, unknown composite/union wrappers recurse into nested matching
# fragments while dropping their own direct fields, anonymous inline fragments
# stay unconditional, and connection-wrapped sibling fragments narrow at the
# node walk.

# Helper-move (Decision 9) no-regression lives in test_extension.py (unmodified).
