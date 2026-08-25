"""Relation resolver tests for cardinality, FK-ID elision, N+1 strictness, and multi-database routing.

Covers the cardinality-aware relation resolvers attached by
``DjangoType.__init_subclass__`` via ``_attach_relation_resolvers``:

- Forward FK / OneToOne - ``getattr(root, name)`` returns the related instance.
- Reverse FK / M2M (many-side) - ``list(getattr(root, name).all())`` so
  Strawberry sees an iterable instead of a Django ``RelatedManager``.
- Reverse OneToOne (``one_to_one`` and ``auto_created``) - try/except
  ``DoesNotExist`` so a missing reverse row collapses to ``None``.

Mix of integration tests (real Strawberry schema execution against
fakeshop seed data) and direct unit tests of ``_make_relation_resolver``
against synthetic ``SimpleNamespace`` fields, so the OneToOne branch can
be exercised without a real Django OneToOne in the example schema.
"""

import itertools
from types import SimpleNamespace

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from django.db import connection as db_connection
from django.db import models as djmodels
from django.test import override_settings

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.optimizer._context import (
    begin_scoped_relations as _begin_scoped_relations,
)
from django_strawberry_framework.optimizer._context import (
    end_scoped_relations as _end_scoped_relations,
)
from django_strawberry_framework.optimizer._context import (
    publish_scoped_relations as _publish_scoped_relations,
)
from django_strawberry_framework.optimizer.plans import resolver_key
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.resolvers import _make_relation_resolver


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


@pytest.mark.django_db
def test_many_relation_scopes_custom_target_without_optimizer():
    """Generated relation resolvers enforce target visibility without an optimizer."""
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None
    item = Item.objects.filter(category=category).first()
    assert item is not None
    Item.objects.filter(pk=item.pk).update(is_private=True)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "items")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return Category.objects.filter(pk=category.pk)

    result = strawberry.Schema(query=Query).execute_sync("{ categories { items { name } } }")
    assert result.errors is None, result.errors
    assert result.data == {"categories": [{"items": []}]}


@pytest.mark.django_db
def test_reverse_one_to_one_scopes_custom_target_by_planned_relation():
    """Reverse-OneToOne visibility follows the PER-RELATION optimizer attribution.

    No fakeshop reverse-OneToOne target declares ``get_queryset``, so this shape
    is unreachable from the shipped schema and lives here rather than in the live
    tier. Both sides of the attribution are asserted: a relation no optimizer
    planned is re-read through the target hook (a hidden card collapses to
    ``None``), and a relation the optimizer planned - whose ``Prefetch`` the
    walker already scoped - is returned as loaded without a second query.
    """
    from apps.library.models import MembershipCard, Patron

    hidden_patron = Patron.objects.create(name="Hidden Holder")
    MembershipCard.objects.create(patron=hidden_patron, barcode="HIDDEN-1")
    visible_patron = Patron.objects.create(name="Visible Holder")
    MembershipCard.objects.create(patron=visible_patron, barcode="OPEN-1")

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(barcode__startswith="HIDDEN")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "card")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def patrons(self) -> list[PatronType]:
            return Patron.objects.filter(name__endswith="Holder").order_by("name")

    query = "{ patrons { card { barcode } } }"
    unplanned = strawberry.Schema(query=Query).execute_sync(query)
    assert unplanned.errors is None, unplanned.errors
    assert unplanned.data == {"patrons": [{"card": None}, {"card": {"barcode": "OPEN-1"}}]}

    optimizer = DjangoOptimizerExtension()
    planned = strawberry.Schema(
        query=Query,
        extensions=[lambda: optimizer],
    ).execute_sync(query, context_value=SimpleNamespace())
    assert planned.errors is None, planned.errors
    assert planned.data == unplanned.data


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
    """Forward resolver returns a target stub from ``<field>_id`` when elided."""
    from types import SimpleNamespace

    from django.db import router

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    class Root:
        category_id = 42

        @property
        def category(self):
            raise AssertionError("the relation resolver must not lazy-load the relation")

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


@pytest.mark.django_db
def test_fk_id_elision_stub_is_scoped_when_the_relation_was_not_planned():
    """An FK-id stub for a CUSTOM-visibility target is re-read through the hook.

    The walker refuses to elide a target whose type overrides ``get_queryset``
    (``optimizer/walker.py::_plan_select_relation``), but the resolver's own
    ``visibility_type`` comes from ``registry.get(related_model)`` while that gate
    reads the plan-time target type - a multi-type registry can disagree. The
    guard therefore stays, and it must fail CLOSED: an unscoped stub is resolved
    through the target hook, which drops a stub whose row the hook excludes.
    """
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.none()

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    finalize_django_types()

    # Bound outside the class body: ``category`` is class-local there (the
    # property below), so the class body cannot read the enclosing name.
    elided_pk = category.pk

    class Root:
        category_id = elided_pk

        @property
        def category(self):
            raise AssertionError("the relation resolver must not lazy-load the relation")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = SimpleNamespace(
        context=SimpleNamespace(dst_optimizer_fk_id_elisions={key}),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    # No optimizer published this relation as planned, so the stub is rescoped -
    # and this target's hook hides every row.
    assert resolver(Root(), fake_info) is None

    # Published as planned: the stub is served as-is, no visibility re-read.
    token = _begin_scoped_relations()
    try:
        _publish_scoped_relations({key})
        scoped = resolver(Root(), fake_info)
    finally:
        _end_scoped_relations(token)
    assert isinstance(scoped, Category)
    assert scoped.pk == category.pk


@pytest.mark.django_db
def test_forward_relation_is_scoped_when_strictness_leaves_it_unplanned():
    """The forward tail re-reads a custom-visibility target the plan never claimed.

    Reached when planning metadata EXISTS for the request (strictness publishes
    ``DST_OPTIMIZER_PLANNED``) but this relation is not among the planned keys, so
    the ``getattr`` below is an unscoped lazy load.
    """
    services.seed_data(1)
    item = Item.objects.select_related("category").first()
    assert item is not None

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.none()

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    finalize_django_types()

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    fake_info = SimpleNamespace(
        context=SimpleNamespace(dst_optimizer_planned=frozenset()),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    assert resolver(item, fake_info) is None


def test_b2_forward_fk_id_elision_uses_registered_field_meta_attname():
    """Resolver FK-id elision reads attname from registered FieldMeta."""
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
            raise AssertionError("the relation resolver must not lazy-load the relation")

    result = resolver(Root(), fake_info)

    assert isinstance(result, Category)
    assert result.pk == 42


def test_b2_forward_fk_id_elision_returns_none_for_null_fk():
    """Nullable FK ids still resolve to ``None`` instead of a stub."""
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
    """Elision for one parent type does not affect another type."""
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
    """Elision requires the full branch-sensitive resolver key."""
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
    """Planned relations require the full branch-sensitive resolver key."""
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": {"category"}, "dst_optimizer_strictness": "raise"},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    with pytest.raises(OptimizerError, match="Unplanned N\\+1"):
        _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind=None)


def test_check_n1_returns_when_relation_is_already_loaded():
    """Unplanned-but-cached relations do not warn or raise."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=_path("allItems", 0, "category"),
    )

    _check_n1(fake_info, SimpleNamespace(category="cached"), "category", ItemType, kind=None)


def test_check_n1_warns_for_unplanned_lazy_load(caplog):
    """Warn strictness logs an unplanned lazy-load relation."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "warn"},
        path=_path("allItems", 0, "category"),
    )

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind=None)

    assert any("Potential N+1 on category" in r.message for r in caplog.records)


def test_check_n1_planned_absent_is_silent():
    """No planned sentinel on context -> optimizer is not engaged."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(context={}, path=_path("allItems", 0, "category"))
    # No exception, no log, no side effect - strictness is irrelevant when the
    # optimizer never set DST_OPTIMIZER_PLANNED.
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


def test_check_n1_planned_hit_is_silent():
    """Planned key present -> resolver is a no-op regardless of strictness."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": {key}, "dst_optimizer_strictness": "raise"},
        path=_path("allItems", 0, "category"),
    )
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


def test_check_n1_default_strictness_off_is_silent_on_lazy_load():
    """Strictness defaults to ``off`` and an unplanned lazy load is silent."""
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
    """Strictness=raise + unplanned + lazy -> OptimizerError."""
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=_path("allItems", 0, "category"),
    )
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: category"):
        _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


@pytest.mark.parametrize("kind", ("many", "reverse_many_to_one"))
def test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy(kind):
    """Many-side ignores ``__dict__`` short-circuit.

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
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=_path("allCategories", 0, "items"),
    )
    # ``items`` is set directly on the root - that would short-circuit the
    # single-valued cache check via ``__dict__`` membership but must NOT
    # short-circuit the many-side check.
    root = SimpleNamespace(items=["not-a-real-prefetch"])
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: items"):
        _check_n1(fake_info, root, "items", CategoryType, kind=kind)


def test_check_n1_many_kind_respects_prefetched_objects_cache():
    """Many-side recognises ``_prefetched_objects_cache`` as the only valid cache."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class CategoryType:
        pass

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=_path("allCategories", 0, "items"),
    )
    root = SimpleNamespace(_prefetched_objects_cache={"items": []})
    # No raise - the relation is prefetched, so the strictness branch is skipped.
    _check_n1(fake_info, root, "items", CategoryType, kind="many")


def test_check_n1_probes_prefetch_cache_under_accessor_name():
    """The cache probe keys on the ACCESSOR, the plan key on the field name.

    Django stores many-side prefetches under the instance accessor
    (``"plainbook_set"``), which diverges from ``field.name``
    (``"plainbook"``) for reverse relations without ``related_name``.
    With ``accessor_name`` supplied - as every
    production resolver does - a manually prefetched relation is
    recognized as cached; the field-name fallback (test-double direct
    callers) would mislabel the same root as lazy and raise.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.types.resolvers import _check_n1

    class PlainAuthorType:
        pass

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=_path("authors", 0, "plainbook"),
    )
    root = SimpleNamespace(_prefetched_objects_cache={"plainbook_set": []})
    # No raise: the accessor-keyed probe finds the prefetched rows.
    _check_n1(
        fake_info,
        root,
        "plainbook",
        PlainAuthorType,
        kind="reverse_many_to_one",
        accessor_name="plainbook_set",
    )
    # Without the accessor the probe falls back to the field name and
    # misses the cache - documenting why production callers must pass it.
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: plainbook"):
        _check_n1(fake_info, root, "plainbook", PlainAuthorType, kind="reverse_many_to_one")


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
    """Correctness-only: query count is 1 + N until the optimizer lands.

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
# Multi-database cooperation (spec-019)
# ---------------------------------------------------------------------------
#
# Per ``docs/SPECS/spec-023-multi_db-0_0_7.md``.
#
# Five resolver-level tests pin Decision 3 axis 1 (FK-id elision router
# call shape; four tests) and axis 4 (strictness connection-agnostic shape;
# one test). The four FK-id tests mock ``router.db_for_read`` per Decision 5;
# the strictness test does NOT mock the router (it never reaches that path
# per ``django_strawberry_framework/types/resolvers.py::_check_n1``).
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
# Both shapes are acceptable per Decision 5; the four FK-id tests below use
# one shape consistently.
#
# Fixture row pattern: the FK-id elision path needs a ``root`` with the
# FK ``attname`` populated (so ``getattr(root, field_meta.attname)`` is
# non-None). The minimum shape is a ``SimpleNamespace`` or a synthetic
# Django-model-shaped object - mirror the existing test-double pattern
# in this file's earlier tests (``test_o4_*`` and friends use
# ``SimpleNamespace`` constructions).


def test_fk_id_elision_stub_sets_state_db_via_router_db_for_read(monkeypatch):
    """Decision 3 axis 1 - stub's ``_state.db`` is set via ``router.db_for_read``."""
    from unittest.mock import Mock

    import django_strawberry_framework.types.resolvers as resolvers_module
    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.resolvers import _build_fk_id_stub

    mock_router = Mock()
    mock_router.db_for_read.return_value = "default"
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    parent_row = Item(category_id=42)
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    stub = _build_fk_id_stub(parent_row, field_meta)

    assert stub is not None
    assert isinstance(stub, Category)
    assert stub.pk == 42
    assert stub._state.db == "default"
    mock_router.db_for_read.assert_called_once()


def test_fk_id_elision_router_call_passes_parent_row_as_instance(monkeypatch):
    """Decision 3 axis 1 - router.db_for_read receives ``instance=<parent_row>`` when parent has ``_state``."""
    from unittest.mock import Mock

    import django_strawberry_framework.types.resolvers as resolvers_module
    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.resolvers import _build_fk_id_stub

    mock_router = Mock()
    mock_router.db_for_read.return_value = "default"
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    parent_row = Item(category_id=42)
    assert hasattr(parent_row, "_state")  # invariant: Django model instances always have _state
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    _build_fk_id_stub(parent_row, field_meta)

    # ``instance=`` is load-bearing - a regression switching it to ``instance=None``
    # would silently break consumer routers that consult the parent row's ``_state.db``.
    mock_router.db_for_read.assert_called_once_with(Category, instance=parent_row)


def test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state(monkeypatch):
    """Decision 3 axis 1 - router.db_for_read receives ``instance=None`` when parent lacks ``_state``."""
    from types import SimpleNamespace
    from unittest.mock import Mock

    import django_strawberry_framework.types.resolvers as resolvers_module
    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.resolvers import _build_fk_id_stub

    mock_router = Mock()
    mock_router.db_for_read.return_value = "default"
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    # ``SimpleNamespace`` has no ``_state`` attribute, so the
    # ``hasattr(root, "_state") else None`` branch at
    # ``django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"instance = root if hasattr(root, "_state") else None"``
    # forwards ``instance=None`` to the router.
    parent_row = SimpleNamespace(pk=1, category_id=42)
    assert not hasattr(parent_row, "_state")

    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    stub = _build_fk_id_stub(parent_row, field_meta)

    assert stub is not None
    mock_router.db_for_read.assert_called_once_with(Category, instance=None)


def test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router(monkeypatch):
    """Decision 3 axis 1 - null FK takes the early-return branch BEFORE the router is consulted."""
    from types import SimpleNamespace
    from unittest.mock import Mock

    import django_strawberry_framework.types.resolvers as resolvers_module
    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.resolvers import _build_fk_id_stub

    mock_router = Mock()
    mock_router.db_for_read.return_value = "default"
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    parent_row = SimpleNamespace(category_id=None)
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    # ``django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"if related_id is None"``
    # - early ``return None`` before reaching the
    # router. Split from the parent-lacks-``_state`` case because
    # the two branches are distinct and a regression in either is a
    # different bug class.
    result = _build_fk_id_stub(parent_row, field_meta)

    assert result is None
    mock_router.db_for_read.assert_not_called()


def test_strictness_check_is_connection_agnostic_under_non_default_alias():
    """Decision 3 axis 4 - strictness mode raises ``OptimizerError`` regardless of ``_state.db``."""
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.optimizer._context import (
        DST_OPTIMIZER_PLANNED,
        DST_OPTIMIZER_STRICTNESS,
    )
    from django_strawberry_framework.types.resolvers import _check_n1

    class _ParentType:
        pass

    # ``_state.db = "shard_b"`` proves the non-default alias is accepted
    # without altering the check's shape; ``fields_cache`` is empty so the
    # second lazy-load gate at ``_will_lazy_load_single`` reports the
    # relation is unloaded.
    state = SimpleNamespace(db="shard_b", fields_cache={})
    root = SimpleNamespace(_state=state)
    assert "shelf" not in vars(root)
    assert "shelf" not in state.fields_cache

    # Non-empty planned set that does NOT include this resolver's key so
    # the lazy-load gate is reached (an empty planned set is also valid;
    # the unrelated key documents the "planned but not this one" shape).
    info = SimpleNamespace(
        context={
            DST_OPTIMIZER_PLANNED: {"some.unrelated.key@/"},
            DST_OPTIMIZER_STRICTNESS: "raise",
        },
        path=None,
    )

    with pytest.raises(OptimizerError, match="Unplanned N\\+1: shelf"):
        _check_n1(info, root, "shelf", _ParentType, kind="forward_single")


# ---------------------------------------------------------------------------
# spec-035 Decision 5 - FK-id elision loaded-check + loud fallback
# ---------------------------------------------------------------------------


def test_fk_id_elision_enabled_under_mutation():
    """Decision 5: a fully-loaded FK column still elides; no join, no lazy load.

    The resolver never sees the operation type - the elision set is on
    ``info.context`` regardless of operation, so this asserts elision works when
    the FK column IS loaded (the optimizer-owned norm and the
    consumer-``.only()``-that-includes-the-FK case), which is exactly why the
    Decision 5 guard is operation-independent.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer._context import DST_OPTIMIZER_FK_ID_ELISIONS
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))

    class Root:
        category_id = 42

        @property
        def category(self):
            raise AssertionError("loaded FK column must elide, never lazy-load the relation")

    fake_info = SimpleNamespace(
        context={DST_OPTIMIZER_FK_ID_ELISIONS: {key}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )
    result = resolver(Root(), fake_info)
    assert isinstance(result, Category)
    assert result.pk == 42


@pytest.mark.parametrize("operation_arm", ["query", "mutation"])
def test_fk_id_elision_falls_back_when_consumer_only_defers_fk(operation_arm, caplog):
    """Decision 5: a deferred consumer-``.only()`` FK column falls back loudly.

    A consumer ``Item.objects.only("name")`` survives B8 consumer-wins diffing
    while the plan still carries the ``category`` elision AND records it planned.
    The resolver must NOT silently read the deferred ``category_id`` (the per-row
    lazy load Decision 5 forbids), and because the relation is planned it must
    NOT let ``_check_n1`` mistake the planned key for a satisfied relation - the
    fallback forces the lazy-load probe so strictness sees the access. The bug
    bites under both ``QUERY`` and a mutation (the resolver is operation-agnostic,
    so ``operation_arm`` only documents the two shapes - spec-035 edge case 316).
    """
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.optimizer._context import (
        DST_OPTIMIZER_FK_ID_ELISIONS,
        DST_OPTIMIZER_PLANNED,
        DST_OPTIMIZER_STRICTNESS,
    )
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))

    def make_root():
        class Root:
            accessed_relation = False

            def get_deferred_fields(self):
                return {"category_id"}

            @property
            def category_id(self):
                raise AssertionError("deferred FK column must NOT be read (silent per-row load)")

            @property
            def category(self):
                # The honest fallback: a real lazy load, which strictness must see.
                type(self).accessed_relation = True
                return SimpleNamespace(pk=42)

        return Root

    def context(strictness):
        # The relation is in BOTH elisions and planned (the elision branch records
        # it planned), exactly the production shape Decision 5 must not mistake.
        return {
            DST_OPTIMIZER_FK_ID_ELISIONS: {key},
            DST_OPTIMIZER_PLANNED: {key},
            DST_OPTIMIZER_STRICTNESS: strictness,
        }

    # "raise": the fallback is loud - OptimizerError, not a silent planned-relation
    # lazy load, and never a read of the deferred FK column.
    Root = make_root()
    info = SimpleNamespace(
        context=context("raise"),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: category"):
        resolver(Root(), info)

    # "warn": logs and returns the related object via the normal resolve.
    Root = make_root()
    info = SimpleNamespace(
        context=context("warn"),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = resolver(Root(), info)
    assert any("Potential N+1 on category" in r.message for r in caplog.records)
    assert Root.accessed_relation is True
    assert result.pk == 42


def test_fk_id_stub_returns_unsafe_sentinel_when_attname_deferred():
    """Direct unit: ``_build_fk_id_stub`` signals unsafe without reading the column.

    Pins the loaded-check at the function boundary (mirrors
    ``test_b2_fk_id_stub_returns_none_without_related_model``): a deferred FK
    ``attname`` yields ``_FK_ELISION_UNSAFE`` and the deferred column is never read
    (spec-035 Decision 5).
    """
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.resolvers import _FK_ELISION_UNSAFE, _build_fk_id_stub

    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        attname="category_id",
        related_model=Category,
    )

    class Root:
        def get_deferred_fields(self):
            return {"category_id"}

        @property
        def category_id(self):
            raise AssertionError("deferred FK column must NOT be read")

    assert _build_fk_id_stub(Root(), field_meta) is _FK_ELISION_UNSAFE
    # A fully-loaded double (column in ``__dict__``) still builds the stub.
    assert _build_fk_id_stub(SimpleNamespace(category_id=42), field_meta).pk == 42


@pytest.mark.django_db
def test_fk_id_elision_falls_back_on_real_deferred_only_instance(caplog):
    """Decision 5: a REAL ``Item.objects.only("name")`` instance.

    The double-based fallback test asserts the behavior; this pins the actual
    Django deferred-field bookkeeping the guard depends on - that a real
    ``Item.objects.only("name").get(...)`` reports ``category_id`` in
    ``get_deferred_fields()`` and absent from ``__dict__`` - so the loaded-check
    fires on the genuine ORM shape, not just a simulated one. With the relation
    in BOTH the elision set and the planned set (the production shape), the
    resolver must fall back loudly (``raise`` -> ``OptimizerError``; ``warn`` ->
    logged + normal resolve), never a silent per-row read of the deferred FK
    column.
    """
    from types import SimpleNamespace

    from apps.products import services

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.optimizer._context import (
        DST_OPTIMIZER_FK_ID_ELISIONS,
        DST_OPTIMIZER_PLANNED,
        DST_OPTIMIZER_STRICTNESS,
    )
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    services.seed_data(1)

    class ItemType:
        pass

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))

    # The Django contract the guard depends on, asserted on a real instance.
    pk = Item.objects.values_list("pk", flat=True).first()
    root = Item.objects.only("name").get(pk=pk)
    assert "category_id" in root.get_deferred_fields()
    assert "category_id" not in root.__dict__

    def context(strictness):
        return {
            DST_OPTIMIZER_FK_ID_ELISIONS: {key},
            DST_OPTIMIZER_PLANNED: {key},
            DST_OPTIMIZER_STRICTNESS: strictness,
        }

    # "raise": the deferred FK column is never read silently; the fallback is loud.
    info = SimpleNamespace(
        context=context("raise"),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: category"):
        resolver(root, info)

    # "warn": logs the access and resolves the real related object normally.
    root = Item.objects.only("name").get(pk=pk)
    info = SimpleNamespace(
        context=context("warn"),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = resolver(root, info)
    assert any("Potential N+1 on category" in r.message for r in caplog.records)
    assert isinstance(result, Category)


# ---------------------------------------------------------------------------
# File / image output resolvers (spec-037 Decision 4)
# ---------------------------------------------------------------------------


def _tiny_png_bytes():
    """Return the bytes of a 2x3 PNG built with Pillow (a real, parseable image).

    Pillow is a dev/test-only dependency added by spec-037 so the
    ``DjangoImageType`` ``width`` / ``height`` resolvers exercise a real
    image-dimension read rather than a stand-in. The package itself never
    imports Pillow.
    """
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (2, 3)).save(buffer, format="PNG")
    return buffer.getvalue()


_asset_model_counter = itertools.count(1)


def _make_asset_model():
    """Return a synthetic ``managed=False`` model with a FileField + ImageField.

    ``app_label="products"`` (an INSTALLED app) so the table can be created with
    ``schema_editor``; ``attachment`` is a required (no blank / no null) file
    column and ``preview`` is ``blank=True`` -- but both file/image outputs are
    nullable by default (spec-037 Decision 4), so the empty-file parent guard has
    a nullable object to land on either way. The model NAME is uniquified per call so Django's app
    registry does not warn ``Model 'products.asset' was already registered``
    when several tests each build a synthetic asset model.
    """
    suffix = next(_asset_model_counter)
    meta = type("Meta", (), {"app_label": "products", "managed": False})
    return type(
        f"Asset{suffix}",
        (djmodels.Model,),
        {
            "__module__": __name__,
            "attachment": djmodels.FileField(upload_to="files/"),
            "preview": djmodels.ImageField(upload_to="previews/", blank=True),
            "Meta": meta,
        },
    )


def _asset_type(model, *, filesystem_path_fields=()):
    """Build the asset DjangoType, optionally opting columns into the filesystem path.

    ``filesystem_path_fields`` threads ``Meta.filesystem_path_fields``
    (spec-048 Decision 2) so a row needing the ``path`` subfield asks for it
    the way a consumer would; omitted, the type gets the safe default output,
    which has no ``path`` at all.
    """
    attrs = {"model": model, "fields": ("id", "attachment", "preview")}
    if filesystem_path_fields:
        attrs["filesystem_path_fields"] = filesystem_path_fields
    meta = type("Meta", (), attrs)
    return type(f"{model.__name__}Type", (DjangoType,), {"Meta": meta})


def _asset_schema(asset_type, model):
    @strawberry.type
    class Query:
        @strawberry.field
        def assets(self) -> list[asset_type]:
            return list(model.objects.all())

    finalize_django_types()
    return strawberry.Schema(query=Query)


@pytest.mark.django_db(transaction=True)
def test_populated_file_and_image_resolve_all_subfields(tmp_path):
    """A populated FileField / ImageField resolves name/size/url (+ width/height).

    ``path`` is deliberately absent from the selection: it is off the safe
    default output (spec-048 Decision 1), and the SDL assertion below is what
    pins that rather than a query that would merely fail to compile.
    """
    from django.core.files.base import ContentFile

    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            asset = model()
            asset.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
            asset.preview.save("pic.png", ContentFile(_tiny_png_bytes()), save=False)
            asset.save()

            schema = _asset_schema(_asset_type(model), model)
            # The default output objects publish no filesystem path at all.
            sdl = str(schema)
            assert "type DjangoFileType {" in sdl
            assert "path" not in sdl
            result = schema.execute_sync(
                "{ assets { attachment { name size url } "
                "preview { name size url width height } } }",
            )
            assert result.errors is None
            row = result.data["assets"][0]
            assert row["attachment"]["name"].endswith("doc.txt")
            assert row["attachment"]["size"] == len(b"hello bytes")
            assert "doc.txt" in row["attachment"]["url"]
            # ImageField dimensions read through the real Pillow-parsed image.
            assert row["preview"]["width"] == 2
            assert row["preview"]["height"] == 3
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_empty_file_resolves_parent_object_to_null(tmp_path):
    """An empty / falsy FieldFile resolves the whole object to ``null`` (parent guard)."""
    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            # ``preview`` is blank=True and left unset: an empty ImageFieldFile.
            from django.core.files.base import ContentFile

            asset = model()
            asset.attachment.save("doc.txt", ContentFile(b"x"), save=False)
            asset.save()

            schema = _asset_schema(_asset_type(model), model)
            result = schema.execute_sync("{ assets { preview { url } } }")
            assert result.errors is None
            assert result.data["assets"][0]["preview"] is None
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_empty_required_file_resolves_to_null_without_error(tmp_path):
    """A required (``null=False, blank=False``) FileField holding an empty value
    resolves to ``null`` -- never a top-level "Cannot return null" error.

    ``attachment`` is a plain required ``FileField``; a row saved with no file
    stores ``""`` (the same empty-string state legacy rows, direct
    ``Model.objects.create()``, fixtures, and manual SQL produce). The parent
    resolver maps that empty ``FieldFile`` to ``None``, so the generated SDL must
    be nullable to represent it (spec-037 Decision 4). Emitting
    ``attachment: DjangoFileType!`` instead would turn the empty-file ``None``
    into a GraphQL non-null execution error.
    """
    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            # Required FileField left unset -> stored as "" (the legacy / direct-create edge).
            asset = model()
            asset.save()

            schema = _asset_schema(_asset_type(model), model)
            # SDL is nullable: the required column no longer emits ``DjangoFileType!``.
            assert "attachment: DjangoFileType\n" in str(schema)
            result = schema.execute_sync("{ assets { attachment { url } } }")
            assert result.errors is None
            assert result.data["assets"][0]["attachment"] is None
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_per_subfield_guard_isolates_storage_failure(tmp_path, monkeypatch):
    """A storage failure on ``path`` nulls only ``path``; ``url`` / ``name`` still resolve.

    The type opts ``attachment`` into ``Meta.filesystem_path_fields`` so the
    ``path`` subfield exists to fail (spec-048 Decision 2); the narrow guard
    itself is unchanged, and removing ``path`` from the default output is not a
    substitute for it (spec-048 Decision 3).

    Each subfield is selected ONE AT A TIME so the failure cannot be attributed
    to the parent resolver -- proving ``_safe_file_attr`` guards at the field
    level. The non-filesystem ``path`` case (S3-style) is the realistic backend
    whose ``.path`` raises ``NotImplementedError``; it is the one case mocked
    (a real non-filesystem backend is impractical in a unit test).
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import FileSystemStorage

    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            asset = model()
            asset.attachment.save("doc.txt", ContentFile(b"hello"), save=False)
            asset.save()

            def _no_path(self, name):
                raise NotImplementedError("This backend doesn't support absolute paths.")

            monkeypatch.setattr(FileSystemStorage, "path", _no_path)

            schema = _asset_schema(
                _asset_type(model, filesystem_path_fields=("attachment",)),
                model,
            )
            # ``path`` selected alone -> degrades to null via the subfield guard.
            path_result = schema.execute_sync("{ assets { attachment { path } } }")
            assert path_result.errors is None
            assert path_result.data["assets"][0]["attachment"]["path"] is None
            # ``url`` selected alone -> still resolves (its own guard never fires).
            url_result = schema.execute_sync("{ assets { attachment { url } } }")
            assert url_result.errors is None
            assert "doc.txt" in url_result.data["assets"][0]["attachment"]["url"]
            # ``name`` selected alone -> the un-guarded stored string still resolves.
            name_result = schema.execute_sync("{ assets { attachment { name } } }")
            assert name_result.errors is None
            assert name_result.data["assets"][0]["attachment"]["name"].endswith("doc.txt")
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_suspicious_file_operation_is_not_swallowed(tmp_path, monkeypatch):
    """A ``SuspiciousFileOperation`` on a subfield surfaces, never hides as ``null``.

    It is a ``SuspiciousOperation`` subclass, NOT a ``ValueError`` / ``OSError``,
    so the narrow ``_safe_file_attr`` guard must let it propagate (spec-037
    Decision 4 -- a path-traversal security signal). The type opts ``attachment``
    into ``Meta.filesystem_path_fields`` so the subfield exists at all.
    """
    from django.core.exceptions import SuspiciousFileOperation
    from django.core.files.base import ContentFile
    from django.core.files.storage import FileSystemStorage

    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            asset = model()
            asset.attachment.save("doc.txt", ContentFile(b"hello"), save=False)
            asset.save()

            def _suspicious(self, name):
                raise SuspiciousFileOperation("escaped media root")

            monkeypatch.setattr(FileSystemStorage, "path", _suspicious)

            schema = _asset_schema(
                _asset_type(model, filesystem_path_fields=("attachment",)),
                model,
            )
            result = schema.execute_sync("{ assets { attachment { path } } }")
            # The error surfaces (it is NOT degraded to a null subfield).
            assert result.errors is not None
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_vanished_file_degrades_size_to_null(tmp_path):
    """A vanished-on-disk file nulls ``size`` (the ``OSError`` arm).

    An earlier revision fired only the ``NotImplementedError`` arm of ``_safe_file_attr``
    (the non-filesystem ``.path`` case). This pins the ``OSError`` / ``ValueError``
    arms: a populated file deleted from disk makes ``FieldFile.size`` raise
    ``FileNotFoundError`` (an ``OSError`` subclass), so ``_safe_file_attr``
    degrades ``size`` to ``null`` -- the realistic "missing file in storage"
    edge (spec-037 Decision 4). Real on-disk deletion under ``tmp_path`` is used
    rather than a monkeypatch (Decision 9 prefers real temp storage).
    """
    import os

    from django.core.files.base import ContentFile

    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            asset = model()
            asset.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
            asset.save()
            # Remove the underlying file so storage can no longer read it.
            os.remove(asset.attachment.path)

            schema = _asset_schema(_asset_type(model), model)
            result = schema.execute_sync("{ assets { attachment { name size } } }")
            assert result.errors is None
            attachment = result.data["assets"][0]["attachment"]
            # ``size`` degrades to null (its read raised FileNotFoundError);
            # ``name`` (the un-guarded stored string) still resolves.
            assert attachment["size"] is None
            assert attachment["name"].endswith("doc.txt")
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_corrupt_image_degrades_width_and_height_to_null(tmp_path):
    """A corrupt image nulls ``width`` / ``height`` (the dimension-read FAILURE path).

    Sibling tests read ``width`` / ``height`` from a VALID Pillow image (the
    success path). This pins the FAILURE path: bytes that are not a parseable
    image make ``ImageFieldFile.width`` / ``.height`` raise when Pillow reads the
    dimensions, so ``_safe_file_attr`` degrades each to ``null`` -- the spec-037
    Decision 4 "corrupt / missing image dimensions degrade to null" edge. The
    bytes are stored with ``save=False`` so Pillow never validates at save time.
    """
    from django.core.files.base import ContentFile

    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            asset = model()
            asset.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
            # Non-image bytes on the ImageField -> dimension reads raise.
            asset.preview.save("broken.png", ContentFile(b"not an image"), save=False)
            asset.save()

            schema = _asset_schema(_asset_type(model), model)
            result = schema.execute_sync("{ assets { preview { name width height } } }")
            assert result.errors is None
            preview = result.data["assets"][0]["preview"]
            # ``width`` / ``height`` degrade to null (Pillow cannot parse the
            # bytes); ``name`` still resolves.
            assert preview["width"] is None
            assert preview["height"] is None
            assert preview["name"].endswith("broken.png")
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_relations_with_custom_visibility():
    """Relations re-check custom visibility hooks asynchronously.

    Stays in the package tier for the same structural reason the sync sibling
    ``test_reverse_one_to_one_scopes_custom_target_by_planned_relation`` gives:
    no fakeshop reverse-OneToOne target declares ``get_queryset``, so the
    reverse-o2o-plus-custom-visibility shape cannot be assembled from the
    shipped schema. ``MembershipCard.patron`` is the only library OneToOne and
    ``MembershipCardType`` has no visibility hook; kanban's OneToOnes have none
    either. Reaching this live would mean adding ``get_queryset`` to fakeshop's
    shipped ``MembershipCardType``, which changes what every existing
    ``patron { card { ... } }`` traversal returns -- a behavior change to the
    example schema, not an additive one.

    Its three no-visibility siblings DID move: they are now
    ``examples/fakeshop/test_query/test_relations_async_api.py``.
    """
    from apps.library.models import MembershipCard, Patron
    from asgiref.sync import sync_to_async

    p1 = await sync_to_async(Patron.objects.create)(name="Hidden Patron")
    await sync_to_async(MembershipCard.objects.create)(patron=p1, barcode="HIDDEN-99")
    p2 = await sync_to_async(Patron.objects.create)(name="Visible Patron")
    await sync_to_async(MembershipCard.objects.create)(patron=p2, barcode="OPEN-99")

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(barcode__startswith="HIDDEN")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        async def patrons(self) -> list[PatronType]:
            patrons = []
            async for p in Patron.objects.filter(pk__in=[p1.pk, p2.pk]).order_by("pk"):
                patrons.append(p)
            return patrons

    schema = strawberry.Schema(query=Query)
    result = await schema.execute("{ patrons { name card { barcode } } }")
    assert result.errors is None
    assert result.data == {
        "patrons": [
            {"name": "Hidden Patron", "card": None},
            {"name": "Visible Patron", "card": {"barcode": "OPEN-99"}},
        ],
    }


def test_fk_attname_is_deferred_and_stub_exceptions():
    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.types.resolvers import (
        _FK_ELISION_UNSAFE,
        _build_fk_id_stub,
        _fk_attname_is_deferred,
        _visible_related_object,
    )

    class BrokenDeferred:
        def get_deferred_fields(self):
            raise RuntimeError("hostile get_deferred_fields")

    assert not _fk_attname_is_deferred(BrokenDeferred(), "category_id")

    class BrokenDeferredIn:
        def get_deferred_fields(self):
            class HostileContainer:
                def __contains__(self, item):
                    raise RuntimeError("hostile in")

            return HostileContainer()

    assert not _fk_attname_is_deferred(BrokenDeferredIn(), "category_id")

    # _visible_related_object(None, ...) -> None
    assert _visible_related_object(None, Category, None) is None

    # _build_fk_id_stub with unreadable attname / uninstantiable related_model
    class BrokenRoot:
        @property
        def category_id(self):
            raise AttributeError("broken attr")

    fm = FieldMeta.from_django_field(Item._meta.get_field("category"))
    assert _build_fk_id_stub(BrokenRoot(), fm) is None

    class BrokenModel:
        def __init__(self, pk=None):
            raise RuntimeError("uninstantiable model")

    fake_fm = SimpleNamespace(attname="target_id", related_model=BrokenModel)
    assert _build_fk_id_stub(SimpleNamespace(target_id=1), fake_fm) is _FK_ELISION_UNSAFE


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_resolvers_optimizer_scoped_and_visibility():
    import inspect

    import django_strawberry_framework.types.resolvers as resolvers_mod
    from django_strawberry_framework.optimizer._context import (
        begin_scoped_relations,
        begin_strictness,
        end_scoped_relations,
        end_strictness,
        publish_scoped_relations,
    )
    from django_strawberry_framework.optimizer.plans import resolver_key
    from django_strawberry_framework.types.base import DjangoType
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class CustomCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.filter(name__startswith="Visible")

    class CustomItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.filter(name__startswith="Visible")

    from django_strawberry_framework.types.finalizer import finalize_django_types

    finalize_django_types()
    token = begin_scoped_relations()

    try:

        class FakeRevRel:
            name = "profile"
            is_relation = True
            one_to_one = True
            auto_created = True
            related_model = Category

            def get_accessor_name(self):
                return "profile"

        # Reverse one-to-one resolver (scoped and unscoped)
        rev_field = FakeRevRel()
        rev_resolver = _make_relation_resolver(rev_field, parent_type=Item)

        key = resolver_key(Item, "profile", ("item", "profile"))
        publish_scoped_relations({key})

        cat = await Category.objects.acreate(name="Visible Cat")

        class FakeRevRoot:
            _state = SimpleNamespace(fields_cache={})

            @property
            def profile(self):
                return cat

        fake_info = SimpleNamespace(path=_path("item", "profile"), context={})
        fake_root = FakeRevRoot()

        res = rev_resolver(fake_root, fake_info)

        if inspect.isawaitable(res):
            res = await res
        assert res == cat

        unscoped_info = SimpleNamespace(path=_path("other", "profile"), context={})
        res_unscoped = rev_resolver(fake_root, unscoped_info)
        if inspect.isawaitable(res_unscoped):
            res_unscoped = await res_unscoped
        assert res_unscoped.pk == cat.pk

        # Forward resolver (scoped and unscoped, without strictness)
        fwd_field = Item._meta.get_field("category")
        fwd_resolver = _make_relation_resolver(fwd_field, parent_type=Item)
        fwd_key = resolver_key(Item, "category", ("item", "category"))
        publish_scoped_relations({fwd_key})
        fwd_info = SimpleNamespace(path=_path("item", "category"), context={})

        res_fwd = fwd_resolver(Item(name="Test Item 1", category_id=cat.pk), fwd_info)
        if inspect.isawaitable(res_fwd):
            res_fwd = await res_fwd
        assert res_fwd.pk == cat.pk

        fwd_unscoped_info = SimpleNamespace(path=_path("other", "category"), context={})
        res_fwd_unscoped = fwd_resolver(
            Item(name="Test Item 2", category_id=cat.pk),
            fwd_unscoped_info,
        )
        if inspect.isawaitable(res_fwd_unscoped):
            res_fwd_unscoped = await res_fwd_unscoped
        assert res_fwd_unscoped.pk == cat.pk

        # Forward resolver under active strictness (warn)
        strict_token = begin_strictness("warn")
        try:
            # Scoped
            res_strict_scoped = fwd_resolver(
                Item(name="Test Item 3", category_id=cat.pk),
                fwd_info,
            )
            if inspect.isawaitable(res_strict_scoped):
                res_strict_scoped = await res_strict_scoped
            assert res_strict_scoped.pk == cat.pk

            # Unscoped
            res_strict_unscoped = fwd_resolver(
                Item(name="Test Item 4", category_id=cat.pk),
                fwd_unscoped_info,
            )
            if inspect.isawaitable(res_strict_unscoped):
                res_strict_unscoped = await res_strict_unscoped
            assert res_strict_unscoped.pk == cat.pk

            # Sync / loaded path under strictness
            loaded_item = Item(name="Test Item Loaded", category_id=cat.pk)
            loaded_item._state.fields_cache["category"] = cat
            res_sync_scoped = fwd_resolver(loaded_item, fwd_info)
            assert res_sync_scoped.pk == cat.pk
        finally:
            end_strictness(strict_token)

        # Fallback when _visible_related_object returns non-awaitable (lines 510, 548, 601)
        orig_vis = resolvers_mod._visible_related_object
        try:
            resolvers_mod._visible_related_object = lambda rel, vt, inf: rel

            # Reverse one-to-one non-awaitable fallback (line 510)
            res_rev_sync = rev_resolver(FakeRevRoot(), unscoped_info)
            if inspect.isawaitable(res_rev_sync):
                res_rev_sync = await res_rev_sync
            assert res_rev_sync.pk == cat.pk

            # Forward non-awaitable fallback without strictness (line 548)
            res_fwd_sync = fwd_resolver(
                Item(name="Test Item 5", category_id=cat.pk),
                fwd_unscoped_info,
            )
            if inspect.isawaitable(res_fwd_sync):
                res_fwd_sync = await res_fwd_sync
            assert res_fwd_sync.pk == cat.pk

            # Forward non-awaitable fallback with strictness (line 601)
            strict_token = begin_strictness("warn")
            try:
                res_strict_sync = fwd_resolver(
                    Item(name="Test Item 6", category_id=cat.pk),
                    fwd_unscoped_info,
                )
                if inspect.isawaitable(res_strict_sync):
                    res_strict_sync = await res_strict_sync
                assert res_strict_sync.pk == cat.pk

                # Null related in strict async forward resolver (line 602)
                class FakeItemNull:
                    _state = SimpleNamespace(fields_cache={})
                    category = None

                res_strict_null = fwd_resolver(FakeItemNull(), fwd_unscoped_info)
                if inspect.isawaitable(res_strict_null):
                    res_strict_null = await res_strict_null
                assert res_strict_null is None

            finally:
                end_strictness(strict_token)
        finally:
            resolvers_mod._visible_related_object = orig_vis

        # Many-side resolver with prefetched cache and visibility in async context
        many_field = Category._meta.get_field("items")

        many_resolver = _make_relation_resolver(many_field, parent_type=Category)
        item_obj = await Item.objects.acreate(name="Visible Item", category=cat)
        cat_with_cache = SimpleNamespace(
            _prefetched_objects_cache={"items": [item_obj]},
            items=Item.objects.filter(category=cat),
        )
        many_res_unscoped = many_resolver(cat_with_cache, unscoped_info)
        if inspect.isawaitable(many_res_unscoped):
            many_res_unscoped = await many_res_unscoped
        assert len(many_res_unscoped) == 1

        many_scoped_key = resolver_key(Category, "items", ("category", "items"))
        publish_scoped_relations({many_scoped_key})
        many_scoped_info = SimpleNamespace(path=_path("category", "items"), context={})
        many_res_scoped = many_resolver(cat_with_cache, many_scoped_info)
        assert len(list(many_res_scoped)) == 1
    finally:
        end_scoped_relations(token)
        registry._finalized = False
        registry.unregister(Category)
        registry.unregister(Item)


def test_sync_forward_and_many_resolver_visibility(db):
    from django_strawberry_framework.optimizer._context import (
        begin_scoped_relations,
        end_scoped_relations,
        publish_scoped_relations,
    )
    from django_strawberry_framework.optimizer.plans import resolver_key
    from django_strawberry_framework.types.base import DjangoType
    from django_strawberry_framework.types.finalizer import finalize_django_types
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class CustomCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.filter(name__startswith="Visible")

    class CustomItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.filter(name__startswith="Visible")

    finalize_django_types()
    token = begin_scoped_relations()

    try:
        cat = Category.objects.create(name="Visible Cat")
        item = Item.objects.create(name="Visible Item", category=cat)

        fwd_field = Item._meta.get_field("category")
        fwd_resolver = _make_relation_resolver(fwd_field, parent_type=Item)

        # Scoped (line 556)
        fwd_key = resolver_key(Item, "category", ("item", "category"))
        publish_scoped_relations({fwd_key})
        fwd_scoped_info = SimpleNamespace(path=_path("item", "category"), context={})
        res_scoped = fwd_resolver(item, fwd_scoped_info)
        assert res_scoped.pk == cat.pk

        # Unscoped (line 557)
        fwd_unscoped_info = SimpleNamespace(path=_path("other", "category"), context={})
        res_unscoped = fwd_resolver(item, fwd_unscoped_info)
        assert res_unscoped.pk == cat.pk

        # Many resolver sync unscoped with cache (line 462)
        many_field = Category._meta.get_field("items")
        many_resolver = _make_relation_resolver(many_field, parent_type=Category)
        cat_with_cache = SimpleNamespace(
            _prefetched_objects_cache={"items": [item]},
            items=Item.objects.filter(category=cat),
        )
        many_unscoped_info = SimpleNamespace(path=_path("other", "items"), context={})
        res_many_unscoped = many_resolver(cat_with_cache, many_unscoped_info)
        assert len(res_many_unscoped) == 1

        # Many resolver sync scoped with cache (line 467-469)
        many_key = resolver_key(Category, "items", ("category", "items"))
        publish_scoped_relations({many_key})
        many_scoped_info = SimpleNamespace(path=_path("category", "items"), context={})
        res_many_scoped = many_resolver(cat_with_cache, many_scoped_info)
        assert len(list(res_many_scoped)) == 1
    finally:
        end_scoped_relations(token)
        registry._finalized = False
        registry.unregister(Category)
        registry.unregister(Item)


def test_resolver_helpers_edge_cases():
    from django_strawberry_framework.types.resolvers import (
        _attach_file_resolvers,
        _attach_relation_resolvers,
        _check_n1,
    )

    # Line 313: kind == "connection_to_attr"
    info = SimpleNamespace(path=SimpleNamespace(key="items", prev=None), context={})
    root_with_attr = SimpleNamespace(prefetched_page=["item1"])
    # Not lazy when to_attr is present on root
    _check_n1(
        info,
        root_with_attr,
        "items",
        Category,
        kind="connection_to_attr",
        to_attr="prefetched_page",
        strictness="warn",
    )
    # Lazy when to_attr is None on root
    root_without_attr = SimpleNamespace(prefetched_page=None)
    _check_n1(
        info,
        root_without_attr,
        "items",
        Category,
        kind="connection_to_attr",
        to_attr="prefetched_page",
        strictness="warn",
    )
    # Lazy when to_attr is not a str
    _check_n1(
        info,
        root_with_attr,
        "items",
        Category,
        kind="connection_to_attr",
        to_attr=None,
        strictness="warn",
    )

    # Lines 639 and 697: skip_field_names
    class DummyTarget:
        pass

    fake_rel = SimpleNamespace(name="skipped_rel", is_relation=True)
    _attach_relation_resolvers(
        DummyTarget,
        (fake_rel,),
        skip_field_names=frozenset({"skipped_rel"}),
    )
    assert not hasattr(DummyTarget, "skipped_rel")

    fake_file = SimpleNamespace(name="skipped_file", is_relation=False)
    _attach_file_resolvers(
        DummyTarget,
        (fake_file,),
        skip_field_names=frozenset({"skipped_file"}),
    )
    assert not hasattr(DummyTarget, "skipped_file")
