"""Relation resolver tests for FK-id elision, N+1 strictness, and multi-database routing.

Generated relation payloads, reverse-O2O custom visibility, and unoptimized
many-side query cost live in ``examples/fakeshop/test_query/test_products_visibility_api.py``
and ``examples/fakeshop/test_query/test_relations_async_api.py``. A nullable dangling
self-FK over HTTP lives in
``examples/fakeshop/test_query/test_scalars_api.py``
(``test_nullable_self_fk_dangling_parent_resolves_to_null_over_http``). This module
keeps direct ``_make_relation_resolver`` / ``_check_n1`` calls, hostile metadata,
router mocks, ``resolver.__name__``, and the nullable ``DoesNotExist`` swallow a
planned JOIN never takes.
"""

import datetime
import inspect
import uuid
from collections.abc import Iterable, Iterator, Sized
from types import SimpleNamespace
from typing import TYPE_CHECKING, Literal

import django
import pytest
from apps.products import services
from apps.products.models import Category, Item
from django.db import connection as db_connection
from django.db.models import Model, QuerySet
from django.utils import timezone
from strawberry import Info
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.optimizer._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
)
from django_strawberry_framework.optimizer._context import (
    begin_execution_frame as _begin_execution_frame,
)
from django_strawberry_framework.optimizer._context import (
    end_execution_frame as _end_execution_frame,
)
from django_strawberry_framework.optimizer._context import (
    publish_scoped_relations as _publish_scoped_relations,
)
from django_strawberry_framework.optimizer.plans import resolver_key
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.resolvers import _make_relation_resolver

if TYPE_CHECKING:
    from django_strawberry_framework.utils.typing import ModelField


def _as_strawberry_info(stand_in: object) -> Info[object, object]:
    """Hand a duck-typed info to a generated resolver that takes a Strawberry info."""
    # basedpyright: a stand-in info carrying only the slots the code under test reads; the
    # generated relation resolvers type info as a concrete Strawberry Info
    return stand_in  # pyright: ignore[reportReturnType]


def _as_django_type(cls: type[object]) -> type[DjangoType]:
    """Hand a plain parent class to a resolver builder that takes a ``DjangoType``."""
    # basedpyright: a plain stand-in class carrying only the hooks the code under test reads; the
    # relation resolver builders type the parameter as type[DjangoType]
    return cls  # pyright: ignore[reportReturnType]


def _as_field(stand_in: object) -> "ModelField":
    """Hand a duck-typed relation field to a resolver builder that takes a Django field."""
    # basedpyright: a stand-in field carrying only the slots the code under test reads; the
    # relation resolver builders type the parameter as a Django field
    return stand_in  # pyright: ignore[reportReturnType]


def _path(*keys: str | int):
    """Build a graphql-core-style linked response path."""
    path = None
    for key in keys:
        path = type("Path", (), {"key": key, "prev": path})()
    return path


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Custom relation resolvers
# ---------------------------------------------------------------------------


def test_make_relation_resolver_many_side_is_named_resolve_field():
    """Generated many-side resolver is named ``resolve_<field>``.

    Payload and SQL live in ``examples/fakeshop/test_query/test_products_visibility_api.py``.
    """
    fake_field = SimpleNamespace(name="items", many_to_many=False, one_to_many=True)
    resolver = _make_relation_resolver(_as_field(fake_field))
    assert resolver.__name__ == "resolve_items"

    class FakeManager:
        def all(self):
            return [1, 2, 3]

    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(SimpleNamespace(items=FakeManager()), _as_strawberry_info(fake_info)) == [
        1,
        2,
        3,
    ]


def test_make_relation_resolver_forward_is_named_resolve_field():
    """Generated forward-FK resolver is named ``resolve_<field>``.

    Payload and SQL live in ``examples/fakeshop/test_query/test_products_visibility_api.py``.
    """
    fake_field = SimpleNamespace(
        name="category",
        attname="category_id",
        many_to_many=False,
        one_to_many=False,
        one_to_one=False,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))
    assert resolver.__name__ == "resolve_category"

    sentinel = object()
    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(SimpleNamespace(category=sentinel), _as_strawberry_info(fake_info)) is sentinel


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
    resolver = _make_relation_resolver(field, parent_type=_as_django_type(ItemType))
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = SimpleNamespace(
        context=SimpleNamespace(dst_optimizer_fk_id_elisions={key}),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    root = Root()
    result = resolver(root, _as_strawberry_info(fake_info))
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
        @override
        def get_queryset(cls, queryset: QuerySet[Category], info: object, **kwargs: object):
            return queryset.none()

    assert registry.get(Category) is CategoryType

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
    assert resolver(Root(), _as_strawberry_info(fake_info)) is None

    # Published as planned: the stub is served as-is, no visibility re-read. The
    # execution that planned it published its elisions to its own frame, which is
    # where a managed read looks; the unmanaged read above has only the context.
    frame = _begin_execution_frame(
        {DST_OPTIMIZER_FK_ID_ELISIONS: {key}},
        nested=False,
    )
    try:
        _publish_scoped_relations({key})
        scoped = resolver(Root(), _as_strawberry_info(fake_info))
    finally:
        _end_execution_frame(frame)
    assert isinstance(scoped, Category)
    assert scoped.pk == category.pk


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
        _as_django_type(ItemType),
        DjangoTypeDefinition(
            origin=_as_django_type(ItemType),
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
    resolver = _make_relation_resolver(_as_field(field), parent_type=_as_django_type(ItemType))
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

    result = resolver(Root(), _as_strawberry_info(fake_info))

    assert isinstance(result, Category)
    assert result.pk == 42


def test_b2_forward_fk_id_elision_returns_none_for_null_fk():
    """Nullable FK ids still resolve to ``None`` instead of a stub."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=_as_django_type(ItemType))
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_root = SimpleNamespace(category_id=None)
    fake_info = SimpleNamespace(
        context={"dst_optimizer_fk_id_elisions": {key}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, _as_strawberry_info(fake_info)) is None


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
    resolver = _make_relation_resolver(field, parent_type=_as_django_type(ItemType))
    wrong_key = resolver_key(OtherType, "category", ("allItems", "category"))
    fake_root = SimpleNamespace(category_id=42, category=sentinel)
    fake_info = SimpleNamespace(
        context={"dst_optimizer_fk_id_elisions": {wrong_key}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, _as_strawberry_info(fake_info)) is sentinel


def test_b2_forward_fk_id_elision_ignores_bare_field_name_key():
    """Elision requires the full branch-sensitive resolver key."""
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class ItemType:
        pass

    sentinel = object()
    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=_as_django_type(ItemType))
    fake_root = SimpleNamespace(category_id=42, category=sentinel)
    fake_info = SimpleNamespace(
        context={"dst_optimizer_fk_id_elisions": {"category"}},
        field_name="category",
        path=_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, _as_strawberry_info(fake_info)) is sentinel


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
        _check_n1(fake_info, SimpleNamespace(), "category", _as_django_type(ItemType), kind=None)


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

    _check_n1(
        fake_info,
        SimpleNamespace(category="cached"),
        "category",
        _as_django_type(ItemType),
        kind=None,
    )


def test_check_n1_warns_for_unplanned_lazy_load(caplog: pytest.LogCaptureFixture):
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
    _check_n1(fake_info, SimpleNamespace(), "category", _as_django_type(ItemType), kind=None)

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
    _check_n1(
        fake_info,
        SimpleNamespace(),
        "category",
        _as_django_type(ItemType),
        kind="forward_single",
    )


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
    _check_n1(
        fake_info,
        SimpleNamespace(),
        "category",
        _as_django_type(ItemType),
        kind="forward_single",
    )


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
    _check_n1(
        fake_info,
        SimpleNamespace(),
        "category",
        _as_django_type(ItemType),
        kind="forward_single",
    )


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
        _check_n1(
            fake_info,
            SimpleNamespace(),
            "category",
            _as_django_type(ItemType),
            kind="forward_single",
        )


@pytest.mark.parametrize("kind", ("many", "reverse_many_to_one"))
def test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy(
    kind: Literal["many", "reverse_many_to_one"],
):
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
        _check_n1(fake_info, root, "items", _as_django_type(CategoryType), kind=kind)


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
    _check_n1(fake_info, root, "items", _as_django_type(CategoryType), kind="many")


def test_check_n1_probes_prefetch_cache_under_cache_name():
    """The cache probe keys on the CACHE NAME, the plan key on the field name.

    Django stores a reverse-FK prefetch under the instance accessor
    (``"plainbook_set"``), which diverges from ``field.name``
    (``"plainbook"``) for reverse relations without ``related_name``.
    With ``cache_name`` supplied - as every
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
    # No raise: the cache-name-keyed probe finds the prefetched rows.
    _check_n1(
        fake_info,
        root,
        "plainbook",
        _as_django_type(PlainAuthorType),
        kind="reverse_many_to_one",
        cache_name="plainbook_set",
    )
    # Without the cache name the probe falls back to the field name and
    # misses the cache - documenting why production callers must pass it.
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: plainbook"):
        _check_n1(
            fake_info,
            root,
            "plainbook",
            _as_django_type(PlainAuthorType),
            kind="reverse_many_to_one",
        )


def test_runtime_path_from_info_strips_list_indexes_and_keeps_aliases():
    """Runtime response paths preserve aliases and omit list indexes.

    ``runtime_path_from_info`` is an optimizer-plan helper with no GraphQL
    selection of its own; the live sibling for planned vs unplanned relations is
    ``examples/fakeshop/test_query/test_products_visibility_api.py``.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer.plans import runtime_path_from_info

    info = SimpleNamespace(path=_path("allItems", 0, "cat"))
    assert runtime_path_from_info(info) == ("allItems", "cat")


def test_o1_make_relation_resolver_reverse_one_to_one_returns_none_on_doesnotexist():
    """Direct unit: reverse OneToOne resolver swallows DoesNotExist into None.

    Direct ``_make_relation_resolver`` call with a fabricated ``DoesNotExist``.
    Live reverse-O2O payloads live in
    ``examples/fakeshop/test_query/test_products_visibility_api.py``; this row
    keeps the swallow-to-None branch a request cannot name without a missing
    reverse accessor.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class FakeDoesNotExist(Exception):  # noqa: N818  (mirrors Django's Model.DoesNotExist naming)
        pass

    class FakeProfile:
        DoesNotExist = FakeDoesNotExist

    fake_field = SimpleNamespace(
        name="profile",
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        related_model=FakeProfile,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))

    class RootMissingProfile:
        @property
        def profile(self):
            raise FakeDoesNotExist

    class RootWithProfile:
        profile = "the-profile"

    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(RootMissingProfile(), _as_strawberry_info(fake_info)) is None
    assert resolver(RootWithProfile(), _as_strawberry_info(fake_info)) == "the-profile"
    assert resolver.__name__ == "resolve_profile"


# ---------------------------------------------------------------------------
# Absence containment: a relation that does not resolve to a row collapses to
# ``None`` instead of letting the ORM's absence signal escape the resolver.
# Forward and reverse, sync and async, fast path and planned path.
# ---------------------------------------------------------------------------


def _forward_category_resolver():
    """Build the generated forward resolver for ``Item.category``."""
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    return _make_relation_resolver(
        Item._meta.get_field("category"),
        parent_type=_as_django_type(Item),
    )


def test_forward_resolver_contains_unsaved_instance_does_not_exist():
    """Forward resolver: an unsaved instance's unset non-null FK collapses to None.

    Django's ``ForwardManyToOneDescriptor`` answers ``item.category`` on an
    unsaved row with ``RelatedObjectDoesNotExist`` (an ``AttributeError``
    subclass) raised WITHOUT a query. The generated resolver contains it into
    ``None`` - the same absent-row contract the reverse OneToOne branch has -
    instead of letting the ORM exception escape the public resolver boundary.
    """
    resolver = _forward_category_resolver()
    root = Item(name="unsaved")
    assert root.category_id is None
    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(root, _as_strawberry_info(fake_info)) is None


@pytest.mark.asyncio
async def test_forward_resolver_async_contains_unsaved_instance_does_not_exist():
    """Async parity of the unsaved-instance containment (fast path).

    The async branch offloads the unloaded descriptor read through
    ``sync_to_async``; the absence signal raised inside that thread is
    contained into ``None`` exactly as the sync branch contains it.
    """
    resolver = _forward_category_resolver()
    root = Item(name="unsaved-async")
    fake_info = SimpleNamespace(context=None, path=None)
    pending = resolver(root, _as_strawberry_info(fake_info))
    assert inspect.isawaitable(pending)
    assert await pending is None


def test_forward_resolver_planned_path_contains_unsaved_instance_does_not_exist():
    """Planned-path parity: FK-id elisions armed, unsaved root still contained.

    Arming elisions (with a key that does not match this field) routes the
    resolve through the planned branch past ``_check_n1``; the descriptor
    read there carries the same containment as the fast path.
    """
    from django_strawberry_framework.optimizer._context import DST_OPTIMIZER_FK_ID_ELISIONS

    resolver = _forward_category_resolver()
    armed = {resolver_key(Item, "category", ("elsewhere", "category"))}
    fake_info = SimpleNamespace(
        context={DST_OPTIMIZER_FK_ID_ELISIONS: armed},
        path=_path("allItems", 0, "category"),
    )
    root = Item(name="unsaved-planned")
    assert resolver(root, _as_strawberry_info(fake_info)) is None


@pytest.mark.asyncio
async def test_forward_resolver_async_planned_path_contains_unsaved_instance():
    """Async planned-path parity of the unsaved-instance containment."""
    from django_strawberry_framework.optimizer._context import DST_OPTIMIZER_FK_ID_ELISIONS

    resolver = _forward_category_resolver()
    armed = {resolver_key(Item, "category", ("elsewhere", "category"))}
    fake_info = SimpleNamespace(
        context={DST_OPTIMIZER_FK_ID_ELISIONS: armed},
        path=_path("allItems", 0, "category"),
    )
    root = Item(name="unsaved-async-planned")
    pending = resolver(root, _as_strawberry_info(fake_info))
    assert inspect.isawaitable(pending)
    assert await pending is None


def test_o1_reverse_one_to_one_propagates_plain_attribute_error():
    """Reverse OneToOne: a plain ``AttributeError`` is a BUG, not an absent row.

    The catch is exactly ``related_model.DoesNotExist`` - which Django's
    per-relation ``RelatedObjectDoesNotExist`` subclasses, so the real absent
    reverse row is still contained. A plain ``AttributeError`` is not that: it
    comes from a consumer's own descriptor / property or a typo'd accessor,
    and swallowing it would turn a programming error into a silent ``null``.
    It propagates instead.
    """
    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    class FakeDoesNotExist(Exception):  # noqa: N818  (mirrors Django's Model.DoesNotExist naming)
        pass

    class FakeProfile:
        DoesNotExist = FakeDoesNotExist

    fake_field = SimpleNamespace(
        name="profile",
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        related_model=FakeProfile,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))

    class RootHostileProfile:
        @property
        def profile(self):
            raise AttributeError("hostile reverse descriptor")

    fake_info = SimpleNamespace(context=None, path=None)
    with pytest.raises(AttributeError, match="hostile reverse descriptor"):
        resolver(RootHostileProfile(), _as_strawberry_info(fake_info))


def test_reverse_one_to_one_real_model_missing_row_contained():
    """Real reverse OneToOne (library app): unsaved patron resolves to None.

    ``patron.card`` on an unsaved ``Patron`` raises
    ``MembershipCard.DoesNotExist`` from the descriptor without a query; the
    generated resolver contains it into ``None``.
    """
    from apps.library.models import Patron

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    resolver = _make_relation_resolver(
        Patron._meta.get_field("card"),
        parent_type=_as_django_type(Patron),
    )
    fake_info = SimpleNamespace(context=None, path=None)
    assert resolver(Patron(name="No Card"), _as_strawberry_info(fake_info)) is None


@pytest.mark.asyncio
async def test_reverse_one_to_one_async_contains_missing_row():
    """Async parity of the real-model reverse OneToOne containment."""
    from apps.library.models import Patron

    from django_strawberry_framework.types.resolvers import _make_relation_resolver

    resolver = _make_relation_resolver(
        Patron._meta.get_field("card"),
        parent_type=_as_django_type(Patron),
    )
    fake_info = SimpleNamespace(context=None, path=None)
    pending = resolver(Patron(name="No Card Async"), _as_strawberry_info(fake_info))
    assert inspect.isawaitable(pending)
    assert await pending is None


@pytest.mark.django_db
def test_forward_resolver_nullable_dangling_fk_resolves_to_none():
    """Direct resolver: a nullable dangling FK swallows the target's ``DoesNotExist``.

    The non-nullable dangling case raises ``RelatedObjectDoesNotExist`` (an
    ``AttributeError`` subclass); the nullable one lets the target's plain
    ``Model.DoesNotExist`` out of ``get_object()``. A planned JOIN on the
    shipped schema never takes this arm. Wire ``parent: null`` with the column
    still set lives in
    ``examples/fakeshop/test_query/test_scalars_api.py``
    (``test_nullable_self_fk_dangling_parent_resolves_to_null_over_http``).
    """
    from apps.scalars.models import ScalarSpecimen

    def create_specimen(label: str, *, parent: ScalarSpecimen | None = None):
        return ScalarSpecimen.objects.create(
            label=label,
            occurred_on=datetime.date(2026, 1, 1),
            occurred_at=timezone.now(),
            occurred_time=datetime.time(12, 0),
            payload={},
            external_id=uuid.uuid4(),
            parent=parent,
        )

    parent = create_specimen("dangling-fk-parent")
    child = create_specimen("dangling-fk-child", parent=parent)
    resolver = _make_relation_resolver(
        ScalarSpecimen._meta.get_field("parent"),
        parent_type=_as_django_type(ScalarSpecimen),
    )
    fake_info = SimpleNamespace(context=None, path=None)
    disabled = db_connection.disable_constraint_checking()
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM scalars_scalarspecimen WHERE id = %s", [parent.pk])
        # Re-read so the instance carries the dangling column with an EMPTY
        # relation cache: the row created above still holds the parent object
        # in ``_state.fields_cache`` and would answer from it without a query.
        dangling = ScalarSpecimen.objects.get(pk=child.pk)
        assert dangling.parent_id == parent.pk
        assert resolver(dangling, _as_strawberry_info(fake_info)) is None
    finally:
        # Clear the dangling column BEFORE re-enabling constraint checks so
        # the fixture teardown's ``PRAGMA foreign_key_check`` sees a
        # consistent database (the test's transaction rolls back anyway).
        ScalarSpecimen.objects.filter(pk=child.pk).update(parent=None)
        if disabled:
            db_connection.enable_constraint_checking()


def test_forward_resolver_propagates_consumer_attribute_error():
    """A consumer descriptor raising ``AttributeError`` is NOT swallowed.

    The containment catches the target's ``DoesNotExist`` only. A plain
    ``AttributeError`` from a consumer-authored property / descriptor (or a
    typo'd accessor) is a programming error: collapsing it to ``None`` would
    answer the query with a silent ``null`` and hide the bug, so it
    propagates out of the resolver unchanged.
    """
    resolver = _forward_category_resolver()

    class HostileItem:
        """Stands in for a consumer overriding the relation with a broken property."""

        @property
        def category(self):
            raise AttributeError("consumer descriptor bug")

    fake_info = SimpleNamespace(context=None, path=None)
    with pytest.raises(AttributeError, match="consumer descriptor bug"):
        resolver(HostileItem(), _as_strawberry_info(fake_info))


# ---------------------------------------------------------------------------
# Multi-database cooperation (spec-023)
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
# Rebinding the module-local ``router`` name leaves the shared
# ``django.db.router`` singleton untouched (Decision 5); ``monkeypatch``
# restores the name at teardown.
#
# Fixture rows: the FK-id elision path needs a ``root`` with the FK
# ``attname`` populated (so ``getattr(root, field_meta.attname)`` is
# non-None). The tests below use an unsaved ``Item`` instance (has
# ``_state``) or a ``SimpleNamespace`` (no ``_state``).


def test_fk_id_elision_stub_sets_state_db_via_router_db_for_read(monkeypatch: pytest.MonkeyPatch):
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


def test_fk_id_elision_router_call_passes_parent_row_as_instance(monkeypatch: pytest.MonkeyPatch):
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


def test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state(
    monkeypatch: pytest.MonkeyPatch,
):
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
    # ``getattr(root, "_state", None) is not None`` branch at
    # ``django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"instance = root if getattr(root, "_state", None) is not None else None"``
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


def test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router(
    monkeypatch: pytest.MonkeyPatch,
):
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
        _check_n1(info, root, "shelf", _as_django_type(_ParentType), kind="forward_single")


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
    resolver = _make_relation_resolver(field, parent_type=_as_django_type(ItemType))
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
    result = resolver(Root(), _as_strawberry_info(fake_info))
    assert isinstance(result, Category)
    assert result.pk == 42


@pytest.mark.parametrize("operation_arm", ["query", "mutation"])
def test_fk_id_elision_falls_back_when_consumer_only_defers_fk(
    operation_arm: str,
    caplog: pytest.LogCaptureFixture,
):
    """Decision 5: a deferred consumer-``.only()`` FK column falls back loudly.

    A consumer ``Item.objects.only("name")`` survives B8 consumer-wins diffing
    while the plan still carries the ``category`` elision AND records it planned.
    The resolver must NOT silently read the deferred ``category_id`` (the per-row
    lazy load Decision 5 forbids), and because the relation is planned it must
    NOT let ``_check_n1`` mistake the planned key for a satisfied relation - the
    fallback forces the lazy-load probe so strictness sees the access. The bug
    bites under both ``QUERY`` and a mutation (the resolver is operation-agnostic,
    so ``operation_arm`` only documents the two shapes), per spec-035
    Decision 5 / Edge cases #"can defer the FK column (both".
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
    resolver = _make_relation_resolver(field, parent_type=_as_django_type(ItemType))
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

    def context(strictness: str):
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
        resolver(Root(), _as_strawberry_info(info))

    # "warn": logs and returns the related object via the normal resolve.
    Root = make_root()
    info = SimpleNamespace(
        context=context("warn"),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = resolver(Root(), _as_strawberry_info(info))
    assert any("Potential N+1 on category" in r.message for r in caplog.records)
    assert Root.accessed_relation is True
    assert isinstance(result, SimpleNamespace)
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
    stub = _build_fk_id_stub(SimpleNamespace(category_id=42), field_meta)
    assert isinstance(stub, Category)
    assert stub.pk == 42


@pytest.mark.django_db
def test_fk_id_elision_falls_back_on_real_deferred_only_instance(caplog: pytest.LogCaptureFixture):
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
    resolver = _make_relation_resolver(field, parent_type=_as_django_type(ItemType))
    key = resolver_key(ItemType, "category", ("allItems", "category"))

    # The Django contract the guard depends on, asserted on a real instance.
    pk = Item.objects.values_list("pk", flat=True).first()
    root = Item.objects.only("name").get(pk=pk)
    assert "category_id" in root.get_deferred_fields()
    assert "category_id" not in root.__dict__

    def context(strictness: str):
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
        resolver(root, _as_strawberry_info(info))

    # "warn": logs the access and resolves the real related object normally.
    root = Item.objects.only("name").get(pk=pk)
    info = SimpleNamespace(
        context=context("warn"),
        field_name="category",
        path=_path("allItems", 0, "category"),
    )
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = resolver(root, _as_strawberry_info(info))
    assert any("Potential N+1 on category" in r.message for r in caplog.records)
    assert isinstance(result, Category)


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
                def __contains__(self, item: object):
                    raise RuntimeError("hostile in")

            return HostileContainer()

    assert not _fk_attname_is_deferred(BrokenDeferredIn(), "category_id")

    # _visible_related_object(None, ...) -> None
    # basedpyright: the path under test returns before reading the target type or info;
    # _visible_related_object types them as type[DjangoType] and a required Info
    assert _visible_related_object(None, Category, None) is None  # pyright: ignore[reportArgumentType]

    # _build_fk_id_stub with unreadable attname / uninstantiable related_model
    class BrokenRoot:
        @property
        def category_id(self):
            raise AttributeError("broken attr")

    fm = FieldMeta.from_django_field(Item._meta.get_field("category"))
    assert _build_fk_id_stub(BrokenRoot(), fm) is None

    class BrokenModel:
        def __init__(self, pk: object = None):
            raise RuntimeError("uninstantiable model")

    fake_fm = SimpleNamespace(attname="target_id", related_model=BrokenModel)
    # basedpyright: a stand-in field meta carrying only the slots the code under test reads;
    # _build_fk_id_stub types the parameter as FieldMeta
    assert _build_fk_id_stub(SimpleNamespace(target_id=1), fake_fm) is _FK_ELISION_UNSAFE  # pyright: ignore[reportArgumentType]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_resolvers_optimizer_scoped_and_visibility():
    import inspect

    import django_strawberry_framework.types.resolvers as resolvers_mod
    from django_strawberry_framework.optimizer._context import (
        begin_execution_frame,
        end_execution_frame,
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
        @override
        def get_queryset(cls, queryset: QuerySet[Category], info: object):
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Category) is CustomCategoryType

    class CustomItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Item], info: object):
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Item) is CustomItemType

    from django_strawberry_framework.types.finalizer import finalize_django_types

    finalize_django_types()
    frame = begin_execution_frame({}, nested=False)

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
        rev_resolver = _make_relation_resolver(
            _as_field(rev_field),
            parent_type=_as_django_type(Item),
        )

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

        res = rev_resolver(fake_root, _as_strawberry_info(fake_info))

        if inspect.isawaitable(res):
            res = await res
        assert res == cat

        unscoped_info = SimpleNamespace(path=_path("other", "profile"), context={})
        res_unscoped = rev_resolver(fake_root, _as_strawberry_info(unscoped_info))
        if inspect.isawaitable(res_unscoped):
            res_unscoped = await res_unscoped
        assert isinstance(res_unscoped, Category)
        assert res_unscoped.pk == cat.pk

        # Forward resolver (scoped and unscoped, without strictness)
        fwd_field = Item._meta.get_field("category")
        fwd_resolver = _make_relation_resolver(fwd_field, parent_type=_as_django_type(Item))
        fwd_key = resolver_key(Item, "category", ("item", "category"))
        publish_scoped_relations({fwd_key})
        fwd_info = SimpleNamespace(path=_path("item", "category"), context={})

        res_fwd = fwd_resolver(
            Item(name="Test Item 1", category_id=cat.pk),
            _as_strawberry_info(fwd_info),
        )
        if inspect.isawaitable(res_fwd):
            res_fwd = await res_fwd
        assert isinstance(res_fwd, Category)
        assert res_fwd.pk == cat.pk

        fwd_unscoped_info = SimpleNamespace(path=_path("other", "category"), context={})
        res_fwd_unscoped = fwd_resolver(
            Item(name="Test Item 2", category_id=cat.pk),
            _as_strawberry_info(fwd_unscoped_info),
        )
        if inspect.isawaitable(res_fwd_unscoped):
            res_fwd_unscoped = await res_fwd_unscoped
        assert isinstance(res_fwd_unscoped, Category)
        assert res_fwd_unscoped.pk == cat.pk

        # Forward resolver under an execution armed at ``warn``, which is a
        # whole execution rather than a switch inside one: strictness is part of
        # the frame ``on_execute`` opens, so the planned relation is published
        # into that frame too.
        strict_frame = begin_execution_frame({}, nested=False, strictness="warn")
        try:
            publish_scoped_relations({fwd_key})
            # Scoped
            res_strict_scoped = fwd_resolver(
                Item(name="Test Item 3", category_id=cat.pk),
                _as_strawberry_info(fwd_info),
            )
            if inspect.isawaitable(res_strict_scoped):
                res_strict_scoped = await res_strict_scoped
            assert isinstance(res_strict_scoped, Category)
            assert res_strict_scoped.pk == cat.pk

            # Unscoped
            res_strict_unscoped = fwd_resolver(
                Item(name="Test Item 4", category_id=cat.pk),
                _as_strawberry_info(fwd_unscoped_info),
            )
            if inspect.isawaitable(res_strict_unscoped):
                res_strict_unscoped = await res_strict_unscoped
            assert isinstance(res_strict_unscoped, Category)
            assert res_strict_unscoped.pk == cat.pk

            # Sync / loaded path under strictness
            loaded_item = Item(name="Test Item Loaded", category_id=cat.pk)
            loaded_item._state.fields_cache["category"] = cat
            res_sync_scoped = fwd_resolver(loaded_item, _as_strawberry_info(fwd_info))
            assert isinstance(res_sync_scoped, Category)
            assert res_sync_scoped.pk == cat.pk
        finally:
            end_execution_frame(strict_frame)

        # Fallback when _visible_related_object returns a non-awaitable object.
        orig_vis = resolvers_mod._visible_related_object
        try:
            resolvers_mod._visible_related_object = lambda rel, vt, inf: rel

            res_rev_sync = rev_resolver(FakeRevRoot(), _as_strawberry_info(unscoped_info))
            if inspect.isawaitable(res_rev_sync):
                res_rev_sync = await res_rev_sync
            assert isinstance(res_rev_sync, Category)
            assert res_rev_sync.pk == cat.pk

            res_fwd_sync = fwd_resolver(
                Item(name="Test Item 5", category_id=cat.pk),
                _as_strawberry_info(fwd_unscoped_info),
            )
            if inspect.isawaitable(res_fwd_sync):
                res_fwd_sync = await res_fwd_sync
            assert isinstance(res_fwd_sync, Category)
            assert res_fwd_sync.pk == cat.pk

            strict_frame = begin_execution_frame({}, nested=False, strictness="warn")
            try:
                res_strict_sync = fwd_resolver(
                    Item(name="Test Item 6", category_id=cat.pk),
                    _as_strawberry_info(fwd_unscoped_info),
                )
                if inspect.isawaitable(res_strict_sync):
                    res_strict_sync = await res_strict_sync
                assert isinstance(res_strict_sync, Category)
                assert res_strict_sync.pk == cat.pk

                class FakeItemNull:
                    _state = SimpleNamespace(fields_cache={})
                    category = None

                res_strict_null = fwd_resolver(
                    FakeItemNull(),
                    _as_strawberry_info(fwd_unscoped_info),
                )
                if inspect.isawaitable(res_strict_null):
                    res_strict_null = await res_strict_null
                assert res_strict_null is None

            finally:
                end_execution_frame(strict_frame)
        finally:
            resolvers_mod._visible_related_object = orig_vis

        # Many-side resolver with prefetched cache and visibility in async context
        many_field = Category._meta.get_field("items")

        many_resolver = _make_relation_resolver(many_field, parent_type=_as_django_type(Category))
        item_obj = await Item.objects.acreate(name="Visible Item", category=cat)
        cat_with_cache = SimpleNamespace(
            _prefetched_objects_cache={"items": [item_obj]},
            items=Item.objects.filter(category=cat),
        )
        many_res_unscoped = many_resolver(cat_with_cache, _as_strawberry_info(unscoped_info))
        if inspect.isawaitable(many_res_unscoped):
            many_res_unscoped = await many_res_unscoped
        assert isinstance(many_res_unscoped, Sized)
        assert len(many_res_unscoped) == 1

        many_scoped_key = resolver_key(Category, "items", ("category", "items"))
        publish_scoped_relations({many_scoped_key})
        many_scoped_info = SimpleNamespace(path=_path("category", "items"), context={})
        many_res_scoped = many_resolver(cat_with_cache, _as_strawberry_info(many_scoped_info))
        assert isinstance(many_res_scoped, Iterable)
        assert len(list(many_res_scoped)) == 1
    finally:
        end_execution_frame(frame)
        registry._finalized = False
        # basedpyright: the model is not a registered type, so this call is a no-op;
        # registry.unregister types the parameter as type[DjangoType]
        registry.unregister(Category)  # pyright: ignore[reportArgumentType]
        registry.unregister(Item)  # pyright: ignore[reportArgumentType]


def test_sync_forward_and_many_resolver_visibility(db: None):
    from django_strawberry_framework.optimizer._context import (
        begin_execution_frame,
        end_execution_frame,
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
        @override
        def get_queryset(cls, queryset: QuerySet[Category], info: object):
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Category) is CustomCategoryType

    class CustomItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Item], info: object):
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Item) is CustomItemType

    finalize_django_types()
    frame = begin_execution_frame({}, nested=False)

    try:
        cat = Category.objects.create(name="Visible Cat")
        item = Item.objects.create(name="Visible Item", category=cat)

        fwd_field = Item._meta.get_field("category")
        fwd_resolver = _make_relation_resolver(fwd_field, parent_type=_as_django_type(Item))

        fwd_key = resolver_key(Item, "category", ("item", "category"))
        publish_scoped_relations({fwd_key})
        fwd_scoped_info = SimpleNamespace(path=_path("item", "category"), context={})
        res_scoped = fwd_resolver(item, _as_strawberry_info(fwd_scoped_info))
        assert isinstance(res_scoped, Category)
        assert res_scoped.pk == cat.pk

        fwd_unscoped_info = SimpleNamespace(path=_path("other", "category"), context={})
        res_unscoped = fwd_resolver(item, _as_strawberry_info(fwd_unscoped_info))
        assert isinstance(res_unscoped, Category)
        assert res_unscoped.pk == cat.pk

        many_field = Category._meta.get_field("items")
        many_resolver = _make_relation_resolver(many_field, parent_type=_as_django_type(Category))
        cat_with_cache = SimpleNamespace(
            _prefetched_objects_cache={"items": [item]},
            items=Item.objects.filter(category=cat),
        )
        many_unscoped_info = SimpleNamespace(path=_path("other", "items"), context={})
        res_many_unscoped = many_resolver(cat_with_cache, _as_strawberry_info(many_unscoped_info))
        assert isinstance(res_many_unscoped, Sized)
        assert len(res_many_unscoped) == 1

        many_key = resolver_key(Category, "items", ("category", "items"))
        publish_scoped_relations({many_key})
        many_scoped_info = SimpleNamespace(path=_path("category", "items"), context={})
        res_many_scoped = many_resolver(cat_with_cache, _as_strawberry_info(many_scoped_info))
        assert isinstance(res_many_scoped, Iterable)
        assert len(list(res_many_scoped)) == 1

        # ``strictness="warn"`` takes the non-cheap resolver arm; scoped True
        # returns the loaded related object without a visibility re-query.
        warn_frame = begin_execution_frame({}, nested=False, strictness="warn")
        try:

            class FakeRevRel:
                name = "profile"
                is_relation = True
                one_to_one = True
                auto_created = True
                related_model = Category

                def get_accessor_name(self):
                    return "profile"

            rev_resolver = _make_relation_resolver(
                _as_field(FakeRevRel()),
                parent_type=_as_django_type(Item),
            )
            rev_key = resolver_key(Item, "profile", ("item", "profile"))
            publish_scoped_relations({rev_key, fwd_key})

            class FakeRevRoot:
                _state = SimpleNamespace(fields_cache={})

                @property
                def profile(self):
                    return cat

            rev_info = SimpleNamespace(path=_path("item", "profile"), context={})
            assert rev_resolver(FakeRevRoot(), _as_strawberry_info(rev_info)) == cat
            related = fwd_resolver(item, _as_strawberry_info(fwd_scoped_info))
            assert isinstance(related, Category)
            assert related.pk == cat.pk
        finally:
            end_execution_frame(warn_frame)
    finally:
        end_execution_frame(frame)
        registry._finalized = False
        # basedpyright: the model is not a registered type, so this call is a no-op;
        # registry.unregister types the parameter as type[DjangoType]
        registry.unregister(Category)  # pyright: ignore[reportArgumentType]
        registry.unregister(Item)  # pyright: ignore[reportArgumentType]


def test_an_unsealable_prefetch_cache_is_refused_under_the_accessor_it_was_read_from():
    """A prefetch-cache entry the seal refuses is named as the cache it came from.

    The consumer wrote no collection resolver here; the queryset is the one
    Django cached under the relation's accessor, so that is what the error names.
    """
    from django.db import models

    from django_strawberry_framework.exceptions import ConfigurationError

    class _ProjectQuerySet(models.QuerySet[Item]):
        """A project's own queryset class."""

    cached = _ProjectQuerySet(model=Item)
    # basedpyright: the planted foreign row iterable is the hostile input under test; django-stubs
    # types the slot as one of Django's BaseIterable classes
    cached._iterable_class = list  # pyright: ignore[reportAttributeAccessIssue]
    resolver = _make_relation_resolver(
        Category._meta.get_field("items"),
        parent_type=_as_django_type(Category),
    )
    root = SimpleNamespace(_prefetched_objects_cache={"items": cached})
    info = SimpleNamespace(path=_path("category", "items"), context={})
    with pytest.raises(ConfigurationError) as excinfo:
        resolver(root, _as_strawberry_info(info))
    message = str(excinfo.value)
    assert message.startswith("The prefetch cache for 'items' held a _ProjectQuerySet ")
    assert "cannot be sealed into a framework-owned execution queryset" in message
    assert "collection resolver" not in message


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
        _as_django_type(Category),
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
        _as_django_type(Category),
        kind="connection_to_attr",
        to_attr="prefetched_page",
        strictness="warn",
    )
    # Lazy when to_attr is not a str
    _check_n1(
        info,
        root_with_attr,
        "items",
        _as_django_type(Category),
        kind="connection_to_attr",
        to_attr=None,
        strictness="warn",
    )

    # Lines 639 and 697: skip_field_names
    class DummyTarget:
        pass

    fake_rel = SimpleNamespace(name="skipped_rel", is_relation=True)
    _attach_relation_resolvers(
        _as_django_type(DummyTarget),
        (_as_field(fake_rel),),
        skip_field_names=frozenset({"skipped_rel"}),
    )
    assert not hasattr(DummyTarget, "skipped_rel")

    fake_file = SimpleNamespace(name="skipped_file", is_relation=False)
    _attach_file_resolvers(
        _as_django_type(DummyTarget),
        (_as_field(fake_file),),
        skip_field_names=frozenset({"skipped_file"}),
    )
    assert not hasattr(DummyTarget, "skipped_file")


# ---------------------------------------------------------------------------
# Many-side rows Django serves from an MTI ancestor's prefetch
# ---------------------------------------------------------------------------


def _declare_mti_tag_models():
    """Declare a forward many-to-many on an MTI parent, plus the parent's child.

    Test-local because fakeshop carries no forward many-to-many on a model with
    a multi-table child (its one inherited many-to-many, ``venuesponsor`` on the
    ``Venue`` chain, is a reverse relation, which Django never serves from an
    ancestor). ``managed = False`` keeps ``migrate`` away from the tables, which
    ``_mti_tag_tables`` creates and drops; the suite's ``_restore_app_registry``
    unregisters the classes after each test.
    """
    from django.db import models

    class MtiTag(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "library"
            managed = False
            db_table = "resolvers_mti_tag"

    class MtiPlace(models.Model):
        name = models.TextField()
        tags = models.ManyToManyField(MtiTag, db_table="resolvers_mti_place_tags")

        class Meta:
            app_label = "library"
            managed = False
            db_table = "resolvers_mti_place"

    class MtiShop(MtiPlace):
        # basedpyright: Django's ModelBase pops a concrete model's Meta (only an abstract model
        # keeps one), so MtiPlace has no Meta at run time for this one to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            app_label = "library"
            managed = False
            db_table = "resolvers_mti_shop"

    return MtiTag, MtiPlace, MtiShop


def _create_mti_tag_tables(*models_in_order: type[Model]):
    with db_connection.schema_editor() as editor:
        for model in models_in_order:
            editor.create_model(model)


def _drop_mti_tag_tables(*models_in_order: type[Model]):
    with db_connection.schema_editor() as editor:
        for model in reversed(models_in_order):
            editor.delete_model(model)


def _seed_mti_tags(tag_model: type[Model], shop_model: type[Model]):
    """Two shops: ``One`` tagged Alpha / Beta / Hidden, ``Two`` tagged Beta."""
    alpha = tag_model.objects.create(name="Alpha")
    beta = tag_model.objects.create(name="Beta")
    hidden = tag_model.objects.create(name="Hidden")
    # basedpyright: the MTI fixture model is built at run time and typed type[Model]; its tags
    # many-to-many accessor is unknown to the checker
    shop_model.objects.create(name="One").tags.add(alpha, beta, hidden)  # pyright: ignore[reportAttributeAccessIssue]
    shop_model.objects.create(name="Two").tags.add(beta)  # pyright: ignore[reportAttributeAccessIssue]


def _shops_reached_through_prefetched_places(place_model: type[Model]) -> list[Model]:
    """Prefetch ``tags`` on the PARENT rows, then walk down to each child.

    ``place.mtishop`` caches the parent on the child's ``mtiplace_ptr``. From
    Django 6.1 the child's ``tags`` manager answers from that ancestor's
    prefetch, so its ``all()`` is an EVALUATED queryset while the child's own
    ``_prefetched_objects_cache`` holds nothing.
    """
    places = place_model.objects.prefetch_related("tags").order_by("name")
    # basedpyright: the MTI fixture model is built at run time and typed type[Model]; its mtishop
    # child accessor is unknown to the checker
    return [place.mtishop for place in places]  # pyright: ignore[reportAttributeAccessIssue]


def _mti_tag_schema(
    tag_model: type[Model],
    place_model: type[Model],
    shop_model: type[Model],
    *,
    hide_prefix: str | None = None,
    run_async: bool,
):
    """Build a ``DjangoSchema`` whose ``shops`` root returns the walked-down children."""
    import strawberry
    from asgiref.sync import sync_to_async

    from django_strawberry_framework import strawberry_config
    from django_strawberry_framework.schema import DjangoSchema

    class MtiTagType(DjangoType):
        class Meta:
            model = tag_model
            fields = ("id", "name")

        if hide_prefix is not None:

            @classmethod
            @override
            def get_queryset(cls, queryset: QuerySet[Model], info: object):
                return queryset.exclude(name__startswith=hide_prefix)

    assert registry.get(tag_model) is MtiTagType

    class MtiShopType(DjangoType):
        class Meta:
            model = shop_model
            fields = ("id", "name", "tags")

    finalize_django_types()

    @strawberry.type(name="Query")
    class AsyncQuery:
        @strawberry.field
        async def shops(self) -> list[MtiShopType]:
            # basedpyright: Strawberry reads this annotation as the field's GraphQL type; the resolver
            # returns the model rows a DjangoType field resolves from, as the consumer corner does
            return await sync_to_async(_shops_reached_through_prefetched_places)(  # pyright: ignore[reportReturnType]
                place_model,
            )

    @strawberry.type(name="Query")
    class SyncQuery:
        @strawberry.field
        def shops(self) -> list[MtiShopType]:
            # basedpyright: Strawberry reads this annotation as the field's GraphQL type; the resolver
            # returns the model rows a DjangoType field resolves from, as the consumer corner does
            return _shops_reached_through_prefetched_places(place_model)  # pyright: ignore[reportReturnType]

    return DjangoSchema(query=AsyncQuery if run_async else SyncQuery, config=strawberry_config())


_MTI_TAGS_QUERY = "{ shops { name tags { name } } }"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("hide_prefix", "first_shop_tags"),
    (
        pytest.param(None, ["Alpha", "Beta", "Hidden"], id="no-visibility-hook"),
        pytest.param("Hidden", ["Alpha", "Beta"], id="unplanned-visibility-reread"),
    ),
)
async def test_async_many_side_served_from_an_mti_ancestor_prefetch(
    hide_prefix: str | None,
    first_shop_tags: list[str],
):
    """An ancestor-served evaluated queryset is routed like a prefetch cache entry.

    The key read in ``many_resolver`` misses (the child's own cache is empty), so
    the manager fall-through receives the ancestor's evaluated queryset. Without
    a hook its rows are bounded as fetched; handed to ``bounded_rows_async`` they
    would slice to a ``list`` and fail the ``async for``. With a hook the unplanned
    rows are re-read through the visibility boundary, as a consumer prefetch is.
    On Django below 6.1 the manager queries instead, which yields the same rows.
    """
    from asgiref.sync import sync_to_async

    tag_model, place_model, shop_model = _declare_mti_tag_models()
    models_in_order = (tag_model, place_model, shop_model)
    await sync_to_async(_create_mti_tag_tables)(*models_in_order)
    try:
        await sync_to_async(_seed_mti_tags)(tag_model, shop_model)
        schema = await sync_to_async(_mti_tag_schema)(
            tag_model,
            place_model,
            shop_model,
            hide_prefix=hide_prefix,
            run_async=True,
        )
        result = await schema.execute(_MTI_TAGS_QUERY)
    finally:
        await sync_to_async(_drop_mti_tag_tables)(*models_in_order)

    assert result.errors is None, result.errors
    assert result.data == {
        "shops": [
            {"name": "One", "tags": [{"name": name} for name in first_shop_tags]},
            {"name": "Two", "tags": [{"name": "Beta"}]},
        ],
    }


@pytest.mark.skipif(
    django.VERSION < (6, 1),
    reason="Django below 6.1 never serves a child's many-to-many manager from an "
    "ancestor's prefetch, so the child's tags are queried rather than served",
)
@pytest.mark.django_db(transaction=True)
def test_sync_many_side_served_from_an_mti_ancestor_prefetch_costs_no_query():
    """The ancestor's prefetched rows are served without a per-child tag query.

    Four statements: the places, their ``tags`` prefetch, and one walk down to
    each of the two shops. A per-child ``tags`` read would add two more.
    """
    from django.test.utils import CaptureQueriesContext

    tag_model, place_model, shop_model = _declare_mti_tag_models()
    models_in_order = (tag_model, place_model, shop_model)
    _create_mti_tag_tables(*models_in_order)
    try:
        _seed_mti_tags(tag_model, shop_model)
        schema = _mti_tag_schema(tag_model, place_model, shop_model, run_async=False)
        with CaptureQueriesContext(db_connection) as captured:
            result = schema.execute_sync(_MTI_TAGS_QUERY)
    finally:
        _drop_mti_tag_tables(*models_in_order)

    assert result.errors is None, result.errors
    assert result.data == {
        "shops": [
            {"name": "One", "tags": [{"name": "Alpha"}, {"name": "Beta"}, {"name": "Hidden"}]},
            {"name": "Two", "tags": [{"name": "Beta"}]},
        ],
    }
    assert len(captured.captured_queries) == 4, captured.captured_queries
