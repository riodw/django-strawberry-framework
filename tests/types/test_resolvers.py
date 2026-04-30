"""Tests for ``django_strawberry_framework.types.resolvers`` — spec-optimizer.md O1.

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
from django_strawberry_framework.registry import registry

CATEGORY_SCALAR_FIELDS = (
    "id",
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Slice O1 — custom relation resolvers (spec-optimizer.md)
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

    Pre-O1 failure mode (per spec-optimizer.md): Strawberry's default
    resolver returns a ``RelatedManager`` and raises ``Expected Iterable,
    but did not find one for field 'CategoryType.items'``. O1's custom
    resolver returns ``list(manager.all())`` so iteration works.
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
    assert resolver(fake_root) == [1, 2, 3]
    assert resolver.__name__ == "resolve_items"


def test_o1_make_relation_resolver_forward_returns_attribute():
    """Direct unit: forward-FK / OneToOne resolver returns the related instance."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    fake_field = SimpleNamespace(
        name="category",
        many_to_many=False,
        one_to_many=False,
        one_to_one=False,
    )
    resolver = _make_relation_resolver(fake_field)

    sentinel = object()
    fake_root = SimpleNamespace(category=sentinel)
    assert resolver(fake_root) is sentinel
    assert resolver.__name__ == "resolve_category"


def test_o1_make_relation_resolver_reverse_one_to_one_returns_none_on_doesnotexist():
    """Direct unit: reverse OneToOne resolver swallows DoesNotExist into None.

    Fakeshop has no OneToOne fields, so this exercises the branch via a
    SimpleNamespace and a fabricated ``DoesNotExist``. The behaviour is
    spec-mandated (see the cardinality table in spec-django_types.md).
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

    assert resolver(RootMissingProfile()) is None
    assert resolver(RootWithProfile()) == "the-profile"
    assert resolver.__name__ == "resolve_profile"


@pytest.mark.django_db
def test_o1_query_count_is_1_plus_n_without_optimizer(django_assert_num_queries):
    """O1 is correctness-only: query count is 1 + N until O3 lands the optimizer.

    Per spec-optimizer.md O1: 'After this slice, ``{ allCategories { items
    { name } } }`` returns correct results in 26 SQL queries (1 + 25). The
    optimizer is still off-architecture and not invoked.'
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
