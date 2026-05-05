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
from fakeshop.products.models import Category, Item

from django_strawberry_framework import DjangoType
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
    from fakeshop.products import services

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
    from fakeshop.products import services

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
        _check_n1(fake_info, SimpleNamespace(), "category", ItemType)


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

    _check_n1(fake_info, SimpleNamespace(category="cached"), "category", ItemType)


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
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType)

    assert any("Potential N+1 on category" in r.message for r in caplog.records)


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
    from fakeshop.products import services

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

    schema = strawberry.Schema(query=Query)

    # 1 query for categories + N (=25) queries for each category's items.
    with django_assert_num_queries(26):
        result = schema.execute_sync("{ allCategories { name items { name } } }")
        assert result.errors is None
