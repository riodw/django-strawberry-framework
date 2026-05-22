"""Tests for ``django_strawberry_framework.types.resolvers``.

Covers the cardinality-aware relation resolvers attached by
``DjangoType.__init_subclass__`` via ``_attach_relation_resolvers``:

- Forward FK / OneToOne — ``getattr(root, name)`` returns the related instance.
- Reverse FK / M2M (many-side) — ``list(getattr(root, name).all())`` so
  Strawberry sees an iterable instead of a Django ``RelatedManager``.
- Reverse OneToOne (``one_to_one`` and ``auto_created``) — try/except
  ``DoesNotExist`` so a missing reverse row collapses to ``None``.

Mix of integration tests (real Strawberry schema execution against
fakeshop seed data) and direct unit tests of ``_make_relation_resolver``
against synthetic ``SimpleNamespace`` fields, so the OneToOne branch can
be exercised without a real Django OneToOne in the example schema.
"""

import pytest
import strawberry
from apps.products.models import Category, Item

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.optimizer.plans import resolver_key
from django_strawberry_framework.registry import registry

CATEGORY_SCALAR_FIELDS = (
    "id",
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
)


def _path(*keys):
    """Build a graphql-core-style linked response path."""
    path = None
    for key in keys:
        path = type("Path", (), {"key": key, "prev": path})()
    return path


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Custom relation resolvers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_o1_forward_fk_resolves_to_related_instance():
    """O1: forward FK resolver returns the Django instance, not the descriptor.

    Without O1, Strawberry's default resolver works for forward FK because
    ``getattr(item, "category")`` returns a Category instance directly.
    The test pins the behaviour stays correct after O1's resolver injection
    so a regression does not silently break forward-FK access.
    """
    from apps.products import services

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return list(Item.objects.all())

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ allItems { name category { name } } }")

    assert result.errors is None
    assert len(result.data["allItems"]) == 25
    # Every item has a non-null category (FK is non-nullable in fakeshop).
    assert all(item["category"]["name"] for item in result.data["allItems"])


@pytest.mark.django_db
def test_o1_reverse_fk_resolves_without_iterability_error():
    """O1: reverse FK resolver returns a list, fixing 'Expected Iterable'.

    Strawberry's default resolver returns a ``RelatedManager`` and raises
    ``Expected Iterable, but did not find one for field 'CategoryType.items'``.
    The custom resolver returns ``list(manager.all())`` so iteration works.
    """
    from apps.products import services

    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return list(Category.objects.all())

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ allCategories { name items { name } } }")

    assert result.errors is None
    assert len(result.data["allCategories"]) == 25
    # Every category exposes its items as a list (each fakeshop category
    # has at least one item under seed_data(1)).
    assert all(isinstance(c["items"], list) for c in result.data["allCategories"])
    assert all(len(c["items"]) >= 1 for c in result.data["allCategories"])


def test_o1_make_relation_resolver_many_side():
    """Direct unit: many-side resolver returns ``list(manager.all())``."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    fake_field = SimpleNamespace(name="items", many_to_many=False, one_to_many=True)
    resolver = _make_relation_resolver(fake_field)

    class FakeManager:
        def all(self):
            return [1, 2, 3]

    fake_root = SimpleNamespace(items=FakeManager())
    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(fake_root, fake_info) == [1, 2, 3]
    assert resolver.__name__ == "resolve_items"


def test_o1_make_relation_resolver_forward_returns_attribute():
    """Direct unit: forward-FK / OneToOne resolver returns the related instance."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    fake_field = SimpleNamespace(
        name="category",
        attname="category_id",
        many_to_many=False,
        one_to_many=False,
        one_to_one=False,
    )
    resolver = _make_relation_resolver(fake_field)

    sentinel = object()
    fake_root = SimpleNamespace(category=sentinel)
    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(fake_root, fake_info) is sentinel
    assert resolver.__name__ == "resolve_category"


def test_b2_forward_fk_id_elision_returns_stub_without_accessing_relation():
    """B2: forward resolver returns a target stub from ``<field>_id`` when elided."""
    from types import SimpleNamespace

    from django.db import router

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    class Root:
        category_id = 42

        @property
        def category(self):
            raise AssertionError("B2 resolver should not lazy-load the relation")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = SimpleNamespace(
        context=SimpleNamespace(dst_optimizer_fk_id_elisions={key}),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    root = Root()
    result = resolver(root, fake_info)
    assert isinstance(result, Category)
    assert result.pk == 42
    assert result.id == 42
    assert result._state.adding is False
    assert result._state.db == router.db_for_read(Category)


def test_b2_forward_fk_id_elision_uses_registered_field_meta_attname():
    """B2: resolver FK-id elision reads attname from registered FieldMeta."""
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.definition import DjangoTypeDefinition
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    field = SimpleNamespace(name="category", attname="wrong_id")
    registry.register_definition(
        ItemType,
        DjangoTypeDefinition(
            origin=ItemType,
            model=Item,
            name=None,
            description=None,
            fields_spec=None,
            exclude_spec=None,
            selected_fields=(),
            field_map={
                "category": FieldMeta(
                    name="category",
                    is_relation=True,
                    attname="category_id",
                    related_model=Category,
                ),
            },
            optimizer_hints={},
            has_custom_get_queryset=False,
        ),
    )
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = SimpleNamespace(
        context={"dst_optimizer_fk_id_elisions": {key}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    class Root:
        category_id = 42

        @property
        def category(self):
            raise AssertionError("B2 resolver should not lazy-load the relation")

    result = resolver(Root(), fake_info)

    assert isinstance(result, Category)
    assert result.pk == 42


def test_b2_forward_fk_id_elision_returns_none_for_null_fk():
    """B2: nullable FK ids still resolve to ``None`` instead of a stub."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_root = SimpleNamespace(category_id=None)
    fake_info = SimpleNamespace(
        context={"dst_optimizer_fk_id_elisions": {key}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, fake_info) is None


def test_b2_fk_id_stub_returns_none_without_related_model():
    """Direct unit: incomplete metadata cannot build an FK-id stub."""
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.resolvers import _build_fk_id_stub

    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        attname="category_id",
        related_model=None,
    )

    assert _build_fk_id_stub(SimpleNamespace(category_id=42), field_meta) is None


def test_b2_forward_fk_id_elision_does_not_leak_across_parent_types():
    """B2/O4: elision for one parent type does not affect another type."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    class OtherType:
        pass

    sentinel = object()
    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    wrong_key = resolver_key(OtherType, "category", ("allItems", "category"))
    fake_root = SimpleNamespace(category_id=42, category=sentinel)
    fake_info = SimpleNamespace(
        context={"dst_optimizer_fk_id_elisions": {wrong_key}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, fake_info) is sentinel


def test_b2_forward_fk_id_elision_ignores_bare_field_name_key():
    """B2/O4: elision requires the full branch-sensitive resolver key."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    sentinel = object()
    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    fake_root = SimpleNamespace(category_id=42, category=sentinel)
    fake_info = SimpleNamespace(
        context={"dst_optimizer_fk_id_elisions": {"category"}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, fake_info) is sentinel


def test_check_n1_ignores_bare_field_name_key():
    """B3/O4: planned relations require the full branch-sensitive resolver key."""
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={
            "dst_optimizer_planned": {"category"},
            "dst_optimizer_strictness": "raise",
        },
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    with pytest.raises(OptimizerError, match="Unplanned N\\+1"):
        _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind=None)


def test_check_n1_returns_when_relation_is_already_loaded():
    """B3: unplanned-but-cached relations do not warn or raise."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={
            "dst_optimizer_planned": set(),
            "dst_optimizer_strictness": "raise",
        },
        path=_path("allItems", 0, "category"),
    )

    _check_n1(fake_info, SimpleNamespace(category="cached"), "category", ItemType, kind=None)


def test_check_n1_warns_for_unplanned_lazy_load(caplog):
    """B3: warn strictness logs an unplanned lazy-load relation."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={
            "dst_optimizer_planned": set(),
            "dst_optimizer_strictness": "warn",
        },
        path=_path("allItems", 0, "category"),
    )

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind=None)

    assert any("Potential N+1 on category" in r.message for r in caplog.records)


def test_check_n1_planned_absent_is_silent():
    """B3 branch: no planned sentinel on context → optimizer is not engaged."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(context={}, path=_path("allItems", 0, "category"))
    # No exception, no log, no side effect — strictness is irrelevant when the
    # optimizer never set DST_OPTIMIZER_PLANNED.
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


def test_check_n1_planned_hit_is_silent():
    """B3 branch: planned key present → resolver is a no-op regardless of strictness."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = SimpleNamespace(
        context={
            "dst_optimizer_planned": {key},
            "dst_optimizer_strictness": "raise",
        },
        path=_path("allItems", 0, "category"),
    )
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


def test_check_n1_default_strictness_off_is_silent_on_lazy_load():
    """B3 branch: strictness defaults to ``off`` and an unplanned lazy load is silent."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set()},
        path=_path("allItems", 0, "category"),
    )
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


def test_check_n1_raise_strictness_raises_on_lazy_load():
    """B3 branch: strictness=raise + unplanned + lazy → OptimizerError."""
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={
            "dst_optimizer_planned": set(),
            "dst_optimizer_strictness": "raise",
        },
        path=_path("allItems", 0, "category"),
    )
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: category"):
        _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


@pytest.mark.parametrize("kind", ("many", "reverse_many_to_one"))
def test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy(kind):
    """B3: many-side ignores ``__dict__`` short-circuit.

    A consumer (or test double) setting ``root.<field>`` directly does
    not populate Django's prefetch cache, so the many-side resolver
    must still treat the access as lazy. Pinned via strictness=raise.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.types.resolvers import _check_n1

    class CategoryType:
        pass

    fake_info = SimpleNamespace(
        context={
            "dst_optimizer_planned": set(),
            "dst_optimizer_strictness": "raise",
        },
        path=_path("allCategories", 0, "items"),
    )
    # ``items`` is set directly on the root — that would short-circuit the
    # single-valued cache check via ``__dict__`` membership but must NOT
    # short-circuit the many-side check.
    root = SimpleNamespace(items=["not-a-real-prefetch"])
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: items"):
        _check_n1(fake_info, root, "items", CategoryType, kind=kind)


def test_check_n1_many_kind_respects_prefetched_objects_cache():
    """B3: many-side recognises ``_prefetched_objects_cache`` as the only valid cache."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class CategoryType:
        pass

    fake_info = SimpleNamespace(
        context={
            "dst_optimizer_planned": set(),
            "dst_optimizer_strictness": "raise",
        },
        path=_path("allCategories", 0, "items"),
    )
    root = SimpleNamespace(_prefetched_objects_cache={"items": []})
    # No raise — the relation is prefetched, so the strictness branch is skipped.
    _check_n1(fake_info, root, "items", CategoryType, kind="many")


def test_runtime_path_from_info_strips_list_indexes_and_keeps_aliases():
    """O4: runtime response paths preserve aliases and omit list indexes."""
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer.plans import runtime_path_from_info

    info = SimpleNamespace(path=_path("allItems", 0, "cat"))
    assert runtime_path_from_info(info) == ("allItems", "cat")


def test_o1_make_relation_resolver_reverse_one_to_one_returns_none_on_doesnotexist():
    """Direct unit: reverse OneToOne resolver swallows DoesNotExist into None.

    Fakeshop has no OneToOne fields, so this exercises the branch via a
    SimpleNamespace and a fabricated ``DoesNotExist``. The behaviour is
    part of the relation cardinality contract.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class FakeDoesNotExist(Exception):  # noqa: N818  (mirrors Django's Model.DoesNotExist naming)
        pass

    fake_field = SimpleNamespace(
        name="profile",
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        related_model=SimpleNamespace(DoesNotExist=FakeDoesNotExist),
    )
    resolver = _make_relation_resolver(fake_field)

    class RootMissingProfile:
        @property
        def profile(self):
            raise FakeDoesNotExist

    class RootWithProfile:
        profile = "the-profile"

    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(RootMissingProfile(), fake_info) is None
    assert resolver(RootWithProfile(), fake_info) == "the-profile"
    assert resolver.__name__ == "resolve_profile"


@pytest.mark.django_db
def test_o1_query_count_is_1_plus_n_without_optimizer(django_assert_num_queries):
    """O1 is correctness-only: query count is 1 + N until O3 lands the optimizer.

    Without the optimizer extension, ``{ allCategories { items { name } } }``
    returns correct results in 26 SQL queries (1 + 25): one category query
    plus one item query per category.
    """
    from apps.products import services

    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return list(Category.objects.all())

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    # 1 query for categories + N (=25) queries for each category's items.
    with django_assert_num_queries(26):
        result = schema.execute_sync("{ allCategories { name items { name } } }")
        assert result.errors is None


# ---------------------------------------------------------------------------
# Multi-database cooperation — spec-019 Slice 1 (rev4)
# ---------------------------------------------------------------------------
#
# TODO(spec-019 Slice 1, tests/types/test_resolvers.py extension — append-only):
# pre-staged scaffold per ``docs/spec-019-multi_db-0_0_7.md`` Slice 1. Worker 2
# replaces the ``raise NotImplementedError`` body in each test below with the
# pseudocode that follows it.
#
# Five new resolver-level tests pin Decision 3 axis 1 (FK-id elision router
# call shape; four tests) and axis 4 (strictness connection-agnostic shape;
# one test). The four FK-id tests mock ``router.db_for_read`` per Decision 5;
# the strictness test does NOT mock the router (it never reaches that path
# per ``types/resolvers.py:119-154``).
#
# Mock pattern (per spec Decision 5 + ``Mock contract`` block):
#
#     from unittest.mock import Mock
#     import django_strawberry_framework.types.resolvers as resolvers_module
#     mock_router = Mock()
#     mock_router.db_for_read.return_value = "default"
#     monkeypatch.setattr(resolvers_module, "router", mock_router)
#     # ...
#     mock_router.db_for_read.assert_called_once_with(
#         <related_model>, instance=<expected_instance>
#     )
#
# Equivalently::
#
#     monkeypatch.setattr(
#         resolvers_module.router,
#         "db_for_read",
#         Mock(return_value="default"),
#     )
#     # ...
#     resolvers_module.router.db_for_read.assert_called_once_with(
#         <related_model>, instance=<expected_instance>
#     )
#
# Both shapes are acceptable per Decision 5; tests pick whichever reads
# cleaner per test. Worker 2 picks one shape consistently across the four
# FK-id tests.
#
# Fixture row pattern: the FK-id elision path needs a ``root`` with the
# FK ``attname`` populated (so ``getattr(root, field_meta.attname)`` is
# non-None). The minimum shape is a ``SimpleNamespace`` or a synthetic
# Django-model-shaped object — mirror the existing test-double pattern
# in this file's earlier tests (``test_o4_*`` and friends use
# ``SimpleNamespace`` constructions).


def test_fk_id_elision_stub_sets_state_db_via_router_db_for_read(monkeypatch):
    """Decision 3 axis 1 — stub's ``_state.db`` is set via ``router.db_for_read``."""
    # TODO(spec-019 Slice 1 — test (a)): pin the router-call → stub._state.db wiring.
    #
    # Pseudocode (per spec Test plan + Decision 3 axis 1):
    #
    #     import django_strawberry_framework.types.resolvers as resolvers_module
    #     from django_strawberry_framework.optimizer.field_meta import FieldMeta
    #     from django_strawberry_framework.types.resolvers import _build_fk_id_stub
    #
    #     # 1. Mock router.db_for_read at the resolvers-module level (per
    #     #    Decision 5 — patches the imported alias, not django.db.router
    #     #    globally).
    #     mock_router = Mock()
    #     mock_router.db_for_read.return_value = "default"
    #     monkeypatch.setattr(resolvers_module, "router", mock_router)
    #
    #     # 2. Build a fixture parent row with a non-null FK attname and a
    #     #    _state attribute (so ``hasattr(root, "_state")`` is True).
    #     parent_row = Category.objects.create(name="P")  # _state.adding=False
    #     parent_row.child_id = 42  # the FK attname (e.g. ``shelf_id``)
    #
    #     # 3. Build a FieldMeta that points at the related model + attname.
    #     #    Mirror the synthesis pattern from existing tests in this file
    #     #    (see ``test_o4_*`` for the SimpleNamespace approach if a
    #     #    real Django field is overkill).
    #     field_meta = FieldMeta(
    #         name="child",
    #         is_relation=True,
    #         related_model=ChildModel,
    #         attname="child_id",
    #         # ... other FieldMeta fields with defaults
    #     )
    #
    #     # 4. Exercise the path and assert stub._state.db comes from the
    #     #    mocked router. Per types/resolvers.py:78-82::
    #     #
    #     #        stub = field_meta.related_model(pk=related_id)
    #     #        state = getattr(stub, "_state", None)
    #     #        if state is not None:
    #     #            state.adding = False
    #     #            instance = root if hasattr(root, "_state") else None
    #     #            state.db = router.db_for_read(
    #     #                field_meta.related_model, instance=instance
    #     #            )
    #     stub = _build_fk_id_stub(parent_row, field_meta)
    #     assert stub is not None
    #     assert stub._state.db == "default"
    #     mock_router.db_for_read.assert_called_once()  # called exactly once
    raise NotImplementedError("TODO(spec-019 Slice 1 — test a)")


def test_fk_id_elision_router_call_passes_parent_row_as_instance(monkeypatch):
    """Decision 3 axis 1 — router.db_for_read receives ``instance=<parent_row>`` when parent has ``_state``."""
    # TODO(spec-019 Slice 1 — test (b)): pin the parent-row ``instance=`` forwarding.
    #
    # Pseudocode (per spec Test plan):
    #
    #     mock_router = Mock()
    #     mock_router.db_for_read.return_value = "default"
    #     monkeypatch.setattr(resolvers_module, "router", mock_router)
    #
    #     parent_row = Category.objects.create(name="P")  # has _state
    #     parent_row.child_id = 42
    #
    #     field_meta = FieldMeta(
    #         name="child",
    #         is_relation=True,
    #         related_model=ChildModel,
    #         attname="child_id",
    #     )
    #
    #     _build_fk_id_stub(parent_row, field_meta)
    #
    #     # Pins instance=parent_row at types/resolvers.py:81 — a regression
    #     # where the call switches to instance=None would silently break
    #     # consumer routers that consult the parent row's _state.db.
    #     mock_router.db_for_read.assert_called_once_with(
    #         ChildModel, instance=parent_row,
    #     )
    raise NotImplementedError("TODO(spec-019 Slice 1 — test b)")


def test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state(monkeypatch):
    """Decision 3 axis 1 — router.db_for_read receives ``instance=None`` when parent lacks ``_state``."""
    # TODO(spec-019 Slice 1 — test (c)): pin the ``hasattr`` fallback to ``instance=None``.
    #
    # Pseudocode (per spec Test plan):
    #
    #     import types as types_module
    #
    #     mock_router = Mock()
    #     mock_router.db_for_read.return_value = "default"
    #     monkeypatch.setattr(resolvers_module, "router", mock_router)
    #
    #     # SimpleNamespace has NO _state attribute — pins the
    #     # ``hasattr(root, "_state") else None`` branch at
    #     # types/resolvers.py:81.
    #     parent_row = types_module.SimpleNamespace(pk=1, child_id=42)
    #     assert not hasattr(parent_row, "_state")  # invariant check
    #
    #     field_meta = FieldMeta(
    #         name="child",
    #         is_relation=True,
    #         related_model=ChildModel,
    #         attname="child_id",
    #     )
    #
    #     stub = _build_fk_id_stub(parent_row, field_meta)
    #     assert stub is not None  # the stub IS built; only the instance hint differs
    #     mock_router.db_for_read.assert_called_once_with(
    #         ChildModel, instance=None,
    #     )
    raise NotImplementedError("TODO(spec-019 Slice 1 — test c)")


def test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router(monkeypatch):
    """Decision 3 axis 1 — null FK takes the early-return branch BEFORE the router is consulted."""
    # TODO(spec-019 Slice 1 — test (d), rev2 H5): pin the null-FK early return.
    #
    # Pseudocode (per spec Test plan + rev2 H5 split):
    #
    #     mock_router = Mock()
    #     mock_router.db_for_read.return_value = "default"
    #     monkeypatch.setattr(resolvers_module, "router", mock_router)
    #
    #     # Parent row with FK attname set to None (nullable FK case).
    #     parent_row = Category.objects.create(name="P")
    #     parent_row.child_id = None
    #
    #     field_meta = FieldMeta(
    #         name="child",
    #         is_relation=True,
    #         related_model=ChildModel,
    #         attname="child_id",
    #     )
    #
    #     # types/resolvers.py:74-76::
    #     #     related_id = getattr(root, field_meta.attname)
    #     #     if related_id is None:
    #     #         return None
    #     # Early return BEFORE router.db_for_read is reached.
    #     result = _build_fk_id_stub(parent_row, field_meta)
    #     assert result is None
    #
    #     # The router MUST NOT be called — this is the rev2 H5 split
    #     # from rev1's conflated case. A regression where the early
    #     # return is removed would silently call db_for_read on a
    #     # null FK and that's a different bug class.
    #     mock_router.db_for_read.assert_not_called()
    raise NotImplementedError("TODO(spec-019 Slice 1 — test d)")


def test_strictness_check_is_connection_agnostic_under_non_default_alias():
    """Decision 3 axis 4 — strictness mode raises ``OptimizerError`` regardless of ``_state.db``."""
    # TODO(spec-019 Slice 1 — test (e), rev2 H6 + rev3 R2 + rev4 V2 + rev4 V3):
    # pin the connection-agnostic shape of _check_n1.
    #
    # CRITICAL setup notes (per rev4 V2 + V3):
    #
    # - kind MUST be "forward_single", NOT "many_to_one". The valid
    #   RelationKind values at utils/relations.py:7-12 are exactly:
    #       "many", "reverse_many_to_one", "reverse_one_to_one",
    #       "forward_single"
    #   "many_to_one" is NOT one of them.
    #
    # - For kind="forward_single", is_many_side_relation_kind(kind)
    #   returns False (MANY_SIDE_RELATION_KINDS = {"many",
    #   "reverse_many_to_one"} per utils/relations.py:14-19), so the
    #   lazy-load detector branches into ``_will_lazy_load_single``
    #   at types/resolvers.py:86-101. That helper reads
    #   ``root.__dict__`` and ``root._state.fields_cache``, NOT
    #   ``root._prefetched_objects_cache``.
    #
    # - Do NOT set ``root._prefetched_objects_cache`` in this test —
    #   it is irrelevant on the forward-single path (rev4 V3). The
    #   setup contract is:
    #     * ``root._state.db = "shard_b"`` — proves connection-agnostic shape.
    #     * ``field_name not in root.__dict__`` — first lazy-load gate.
    #     * ``field_name not in root._state.fields_cache`` — second gate.
    #
    # - Do NOT mock router.db_for_read in this test — _check_n1 never
    #   reaches the elision path (per Decision 5 + rev3 R3).
    #
    # Pseudocode (per spec Test plan + rev2 H6 / rev4 V2-V3):
    #
    #     import types as types_module
    #
    #     from django_strawberry_framework.exceptions import OptimizerError
    #     from django_strawberry_framework.optimizer._context import (
    #         DST_OPTIMIZER_PLANNED,
    #         DST_OPTIMIZER_STRICTNESS,
    #     )
    #     from django_strawberry_framework.optimizer.plans import resolver_key
    #     from django_strawberry_framework.types.resolvers import _check_n1
    #
    #     # 1. Build a row with _state.db = "shard_b" and no cache entries.
    #     #    Mirror this file's existing _path() helper + SimpleNamespace
    #     #    pattern from the earlier tests.
    #     state = types_module.SimpleNamespace(db="shard_b", fields_cache={})
    #     root = types_module.SimpleNamespace(_state=state)
    #     # invariant: field_name "shelf" is NOT in root.__dict__ or
    #     # state.fields_cache. SimpleNamespace.__dict__ holds only
    #     # what we set above, so this holds by construction.
    #     assert "shelf" not in vars(root)
    #     assert "shelf" not in state.fields_cache
    #
    #     # 2. Build a non-empty planned set that does NOT include the
    #     #    resolver_key the call will probe. _check_n1 short-circuits
    #     #    when planned is None (types/resolvers.py:139-140) so the set
    #     #    must be non-empty AND must not contain our key.
    #     class _ParentType:  # fixture parent type for resolver_key build
    #         pass
    #
    #     info = types_module.SimpleNamespace(
    #         context={
    #             DST_OPTIMIZER_PLANNED: {"some.unrelated.key@/"},
    #             DST_OPTIMIZER_STRICTNESS: "raise",
    #         },
    #         path=None,  # runtime_path_from_info handles None
    #     )
    #
    #     # 3. Exercise and assert the connection-agnostic shape — the
    #     #    error class and message do not vary with _state.db.
    #     with pytest.raises(OptimizerError, match="Unplanned N\\+1: shelf"):
    #         _check_n1(
    #             info, root, "shelf", _ParentType, kind="forward_single",
    #         )
    raise NotImplementedError("TODO(spec-019 Slice 1 — test e)")
