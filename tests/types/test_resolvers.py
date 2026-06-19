"""Relation resolver tests for Django relation managers and optimizer hand-off.

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

# TODO(spec-037 Slice 1): add file/image output resolver tests here.
# Pseudo-code:
# - execute a schema over a synthetic model with populated FileField/ImageField
#   values and select name/path/size/url plus width/height for images.
# - assert an empty FieldFile resolves the parent object to null.
# - monkeypatch one storage-backed property at a time so path can return null
#   while url/name still resolve, proving the guard is on subfield resolvers.
# - assert SuspiciousFileOperation is not swallowed by the nullable guard.

import pytest
import strawberry
from apps.products.models import Category, Item

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.optimizer.plans import resolver_key
from django_strawberry_framework.registry import registry


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
        context={"dst_optimizer_planned": {"category"}, "dst_optimizer_strictness": "raise"},
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
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
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
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "warn"},
        path=_path("allItems", 0, "category"),
    )

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind=None)

    assert any("Potential N+1 on category" in r.message for r in caplog.records)


def test_check_n1_planned_absent_is_silent():
    """B3 branch: no planned sentinel on context -> optimizer is not engaged."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _check_n1

    class ItemType:
        pass

    fake_info = SimpleNamespace(context={}, path=_path("allItems", 0, "category"))
    # No exception, no log, no side effect - strictness is irrelevant when the
    # optimizer never set DST_OPTIMIZER_PLANNED.
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind="forward")


def test_check_n1_planned_hit_is_silent():
    """B3 branch: planned key present -> resolver is a no-op regardless of strictness."""
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
    """B3 branch: strictness=raise + unplanned + lazy -> OptimizerError."""
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
    """B3: many-side recognises ``_prefetched_objects_cache`` as the only valid cache."""
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
    """B3: the cache probe keys on the ACCESSOR, the plan key on the field name.

    Django stores many-side prefetches under the instance accessor
    (``"plainbook_set"``), which diverges from ``field.name``
    (``"plainbook"``) for reverse relations without ``related_name``
    (Round-4 S3 follow-up). With ``accessor_name`` supplied - as every
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
# Multi-database cooperation - spec-019 Slice 1 (rev4)
# ---------------------------------------------------------------------------
#
# TODO(spec-019 Slice 1, tests/types/test_resolvers.py extension - append-only):
# pre-staged scaffold per ``docs/spec-023-multi_db-0_0_7.md`` Slice 1. Worker 2
# replaces the ``raise NotImplementedError`` body in each test below with the
# pseudocode that follows it.
#
# Five new resolver-level tests pin Decision 3 axis 1 (FK-id elision router
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
# Both shapes are acceptable per Decision 5; tests pick whichever reads
# cleaner per test. Worker 2 picks one shape consistently across the four
# FK-id tests.
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
    # router. Rev2 H5: split from the parent-lacks-``_state`` case because
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
    """Decision 5 (review P2): a REAL ``Item.objects.only("name")`` instance.

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
