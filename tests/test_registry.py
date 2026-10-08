"""TypeRegistry and finalization tests for lookups, primaries, lifecycle callbacks, retries, and reset.

Package-side TypeRegistry / finalize lifecycle. A live ``/graphql/`` request
cannot observe map identity, ``clear`` / ``unregister`` teardown order, pending
identity, phase-1 / phase-3 atomicity, or a ``ConfigurationError`` raised
before any schema exists. Rungs 1-3 would only wrap those internals in a
GraphQL type, which is not a consumer contract.

Wire-reachable consequences live elsewhere:

- composed type publication:
  ``examples/fakeshop/test_query/test_schema_composition_api.py``;
- Relay ``node(id:)`` / ``nodes(ids:)`` refetch:
  ``examples/fakeshop/test_query/test_library_api.py``
  (``test_node_refetch_genre``, ``test_nodes_batch_mixed_types_order_and_null``,
  ``test_node_malformed_id_live``). Successful type-name decode and
  ``GLOBALID_INVALID`` collapse to one envelope; the registry method's
  definition-object identity, Relay-only scan, ``Meta.name`` key, miss, and
  ambiguity stay here;
- ``Meta.name`` on a published type (SDL, not the registry lookup):
  ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.

DjangoType-wrapper collision and enum-caching through
``convert_choices_to_enum`` live in ``tests/types/test_base.py`` and
``tests/types/test_converters.py``. Finalize audit-success lives in
``tests/types/test_definition_order.py``.
"""

import functools
from collections.abc import Iterator
from enum import Enum
from typing import Any

import pytest
import strawberry
from apps.products.models import Category, Item, Property
from django.db import models
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import (
    TypeRegistry,
    _subsystem_clears,
    iter_subsystem_clears,
    register_subsystem_clear,
    registry,
)
from django_strawberry_framework.types import finalizer as finalizer_module
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.types.relations import PendingRelation, PendingRelationAnnotation
from tests._idioms import definition_raises
from tests._soft_dependency import blocked_modules


def _as_django_type(cls: type[object]) -> type[DjangoType]:
    """Hand a plain stand-in class to a registry method that takes a ``DjangoType``."""
    # basedpyright: the class is only a registry key (a real DjangoType would declare a Meta model
    # contradicting the model each test registers it against); the registry mutators type the
    # parameter as type[DjangoType]
    return cls  # pyright: ignore[reportReturnType]


def _as_definition(stand_in: object) -> DjangoTypeDefinition:
    """Hand a sentinel definition to a registry method that takes a ``DjangoTypeDefinition``."""
    # basedpyright: an ``object()`` sentinel the registry stores and returns by identity, never
    # reading a slot; the registry definition mutators type the parameter as DjangoTypeDefinition
    return stand_in  # pyright: ignore[reportReturnType]


@pytest.fixture
def fresh_registry() -> TypeRegistry:
    """Return a fresh registry instance per test (the global one is shared)."""
    return TypeRegistry()


@pytest.fixture(autouse=True)
def _isolate_global_registry() -> Iterator[None]:
    """Clear the global registry on entry/exit so tests touching it don't leak."""
    registry.clear()
    yield
    registry.clear()


# spec-031 - ``definition_for_graphql_name`` (the GlobalID type-name
# decode entry point: a unique ``graphql_type_name`` lookup over Relay-Node
# definitions only, raising ``ConfigurationError`` on miss / ambiguity).
# ---------------------------------------------------------------------------


def test_definition_for_graphql_name_returns_match():
    """A registered Relay-Node type's ``graphql_type_name`` resolves to its definition.

    Registry lifecycle: definition-object identity or ``ConfigurationError``, which the wire
    collapses to ``GLOBALID_INVALID``. No live request can show the registry object. Live sibling:
    ``examples/fakeshop/test_query/test_library_api.py::test_node_refetch_genre`` (acceptance) and
    ``::test_node_malformed_id_live`` (coded refusal).
    """

    class ItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    definition = ItemNode.__django_strawberry_definition__
    assert registry.definition_for_graphql_name("ItemNode") is definition


def test_definition_for_graphql_name_honors_meta_name():
    """The lookup keys on ``graphql_type_name`` (``Meta.name``), not ``type_cls.__name__``.

    Registry lifecycle: the decode key is ``graphql_type_name``, not ``__name__``. SDL
    ``Meta.name`` is live as
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``;
    this row pins the registry lookup the wire cannot name.
    """

    class ItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "Item"

    finalize_django_types()
    definition = ItemNode.__django_strawberry_definition__
    assert registry.definition_for_graphql_name("Item") is definition
    # The class name is NOT a valid key - only ``graphql_type_name`` is.
    with pytest.raises(ConfigurationError):
        registry.definition_for_graphql_name("ItemNode")


def test_definition_for_graphql_name_ignores_non_relay_definitions():
    """A non-Relay-Node DjangoType with a matching name is ignored (Relay-only scan).

    Registry lifecycle: Relay-only scan. A non-Node type is invisible to this lookup even when the
    GraphQL name matches. Live ``BranchType`` is non-Relay and never enters ``node(id:)`` decode;
    ``GLOBALID_INVALID`` would not distinguish this miss from an unknown name.
    """

    class ItemPlain(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemPlain

    finalize_django_types()
    # The only candidate named ``ItemPlain`` is non-Relay, so the lookup misses.
    with pytest.raises(ConfigurationError, match="ItemPlain"):
        registry.definition_for_graphql_name("ItemPlain")


def test_definition_for_graphql_name_unknown_raises():
    """An unregistered GraphQL type name raises ``ConfigurationError`` naming it.

    Registry lifecycle: definition-object identity or ``ConfigurationError``, which the wire
    collapses to ``GLOBALID_INVALID``. No live request can show the registry object. Live sibling:
    ``examples/fakeshop/test_query/test_library_api.py::test_node_refetch_genre`` (acceptance) and
    ``::test_node_malformed_id_live`` (coded refusal).
    """

    class ItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

    assert registry.get(Item) is ItemNode

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="Nonexistent"):
        registry.definition_for_graphql_name("Nonexistent")


def test_definition_for_graphql_name_ambiguous_raises():
    """Two Relay-Node definitions sharing one ``graphql_type_name`` raise, naming the collision.

    Registry lifecycle: two Relay-Node types sharing one ``graphql_type_name``. A live schema
    cannot publish that collision (Strawberry duplicate-name). No live sibling.
    """

    class CategoryDup(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "Dup"

    assert registry.get(Category) is CategoryDup

    class ItemDup(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "Dup"

    assert registry.get(Item) is ItemDup

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="ambiguous") as excinfo:
        registry.definition_for_graphql_name("Dup")
    message = str(excinfo.value)
    assert "CategoryDup" in message
    assert "ItemDup" in message


def test_register_and_get_round_trips(fresh_registry: TypeRegistry):
    """``register(model, type_cls)`` makes ``get(model)`` return ``type_cls``.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    fresh_registry.register(Category, CategoryType)
    assert fresh_registry.get(Category) is CategoryType


def test_get_returns_none_for_unregistered_model(fresh_registry: TypeRegistry):
    """``get`` returns ``None`` rather than raising when the model is unknown.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """
    assert fresh_registry.get(Category) is None


def test_register_same_class_against_two_models_raises(fresh_registry: TypeRegistry):
    """Registering the same ``type_cls`` against two models raises ``ConfigurationError``.

    Pins the reverse-direction guard: ``_models[type_cls]`` must not be silently overwritten when
    the same class is reused for a different model, because that would leave ``model_for_type``
    returning the wrong model for the original registration.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class SharedType:
        pass

    fresh_registry.register(Category, SharedType)
    with pytest.raises(ConfigurationError, match="already registered against Category"):
        fresh_registry.register(Item, SharedType)
    # Original mapping is preserved.
    assert fresh_registry.model_for_type(SharedType) is Category


def test_model_for_type_returns_none_for_none(fresh_registry: TypeRegistry):
    """Passing ``None`` short-circuits to ``None`` so the optimizer can pipeline.

    ``DjangoOptimizerExtension`` resolves GraphQL return types with ``unwrap_graphql_type`` and
    then calls ``model_for_type``; the registry must accept a missing origin without raising.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """
    assert fresh_registry.model_for_type(None) is None


def test_model_for_type_returns_none_for_unregistered_class(fresh_registry: TypeRegistry):
    """An unregistered class also returns ``None`` (no exception).

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    class NotRegistered:
        pass

    assert fresh_registry.model_for_type(NotRegistered) is None


def test_model_for_type_round_trips(fresh_registry: TypeRegistry):
    """``model_for_type`` reverses ``register``: ``type_cls`` -> ``model``.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    fresh_registry.register(Category, CategoryType)
    assert fresh_registry.model_for_type(CategoryType) is Category


def test_register_enum_caches_by_model_field(fresh_registry: TypeRegistry):
    """``register_enum`` keys on ``(model, field_name)`` and ``get_enum`` retrieves it.

    Registry lifecycle: enum cache keyed on ``(model, field_name)``. Converter acceptance is live
    via choice fields; this cache contract has no wire shape. No live sibling.
    """

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.register_enum(Category, "status", Status)
    assert fresh_registry.get_enum(Category, "status") is Status
    # Distinct ``(model, field_name)`` keys do not collide.
    assert fresh_registry.get_enum(Category, "other_field") is None
    assert fresh_registry.get_enum(Item, "status") is None


def test_register_enum_same_class_is_idempotent(fresh_registry: TypeRegistry):
    """Re-registering the *same* enum class for the same key is a no-op.

    Pins the convert_choices_to_enum cache pattern: the call site reads ``get_enum`` first, so a
    redundant ``register_enum`` with the same class must not raise.

    Registry lifecycle: enum cache keyed on ``(model, field_name)``. Converter acceptance is live
    via choice fields; this cache contract has no wire shape. No live sibling.
    """

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.register_enum(Category, "status", Status)
    fresh_registry.register_enum(Category, "status", Status)
    assert fresh_registry.get_enum(Category, "status") is Status


def test_register_enum_different_class_for_same_key_raises(fresh_registry: TypeRegistry):
    """Registering a *different* enum class for an existing key raises.

    Registry lifecycle: enum cache keyed on ``(model, field_name)``. Converter acceptance is live
    via choice fields; this cache contract has no wire shape. No live sibling.
    """

    class StatusA(Enum):
        ACTIVE = "active"

    class StatusB(Enum):
        ACTIVE = "active"

    fresh_registry.register_enum(Category, "status", StatusA)
    with pytest.raises(
        ConfigurationError,
        match="Category.status is already registered as StatusA",
    ):
        fresh_registry.register_enum(Category, "status", StatusB)
    # Original cache is preserved.
    assert fresh_registry.get_enum(Category, "status") is StatusA


def test_clear_drops_all_state(fresh_registry: TypeRegistry):
    """``clear()`` empties type, model, and enum maps in one call.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register_enum(Category, "status", Status)
    assert fresh_registry.get(Category) is CategoryType
    assert fresh_registry.get_enum(Category, "status") is Status

    fresh_registry.clear()

    assert fresh_registry.get(Category) is None
    assert fresh_registry.model_for_type(CategoryType) is None
    assert fresh_registry.get_enum(Category, "status") is None


def test_clear_runs_owner_registered_subsystem_callback(fresh_registry: TypeRegistry):
    """Subsystem teardown is resolved at registration, not by a drifting string lookup.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    callbacks = dict(_subsystem_clears)
    _subsystem_clears.clear()
    calls = []

    def clear_probe():
        calls.append("cleared")

    try:
        register_subsystem_clear(clear_probe, owner="test.probe")
        fresh_registry.clear()
        assert calls == ["cleared"]
    finally:
        _subsystem_clears.clear()
        _subsystem_clears.update(callbacks)


@pytest.mark.parametrize("action", ["clear", "unregister"])
def test_type_teardowns_run_in_reverse_order_once_before_registration_drops(
    fresh_registry: TypeRegistry,
    action: str,
):
    """Type teardown sees its registration, runs LIFO, and is discarded exactly once.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    calls = []
    fresh_registry.register(Category, CategoryType)

    def record(label: str):
        def teardown():
            assert fresh_registry.model_for_type(CategoryType) is Category
            calls.append(label)

        return teardown

    fresh_registry.register_type_teardown(CategoryType, record("first"))
    fresh_registry.register_type_teardown(CategoryType, record("second"))

    if action == "unregister":
        fresh_registry.unregister(CategoryType)
    else:
        fresh_registry.clear()
    assert calls == ["second", "first"]
    assert fresh_registry.model_for_type(CategoryType) is None

    fresh_registry.clear()
    assert calls == ["second", "first"]


@pytest.mark.parametrize("action", ["clear", "unregister"])
def test_failed_type_teardown_remains_registered_for_retry(
    fresh_registry: TypeRegistry,
    action: str,
):
    """A teardown failure preserves the callback and the type registration.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    attempts = 0
    fresh_registry.register(Category, CategoryType)

    def teardown():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("retry teardown")

    def invoke():
        if action == "clear":
            fresh_registry.clear()
        else:
            fresh_registry.unregister(CategoryType)

    fresh_registry.register_type_teardown(CategoryType, teardown)

    with pytest.raises(RuntimeError, match="retry teardown"):
        invoke()

    assert fresh_registry.model_for_type(CategoryType) is Category
    invoke()
    assert attempts == 2
    assert fresh_registry.model_for_type(CategoryType) is None


def test_register_type_teardown_rejects_invalid_registration(fresh_registry: TypeRegistry):
    """A teardown must belong to an already-registered type.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    with pytest.raises(ConfigurationError, match="unregistered type CategoryType"):
        fresh_registry.register_type_teardown(CategoryType, lambda: None)


def test_before_bind_iteration_excludes_full_clear_only_callbacks():
    """The finalizer cannot erase declaration registries before binding them.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    callbacks = dict(_subsystem_clears)
    _subsystem_clears.clear()

    def clear_emit_namespace():
        pass

    def clear_declarations():
        pass

    try:
        register_subsystem_clear(
            clear_emit_namespace,
            owner="test.emit_namespace",
            before_bind=True,
        )
        register_subsystem_clear(clear_declarations, owner="test.declarations")
        assert iter_subsystem_clears(before_bind=True) == (clear_emit_namespace,)
        assert iter_subsystem_clears() == (clear_emit_namespace, clear_declarations)
    finally:
        _subsystem_clears.clear()
        _subsystem_clears.update(callbacks)


def test_register_subsystem_clear_rejects_empty_owner():
    """``register_subsystem_clear`` rejects an empty owner string.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    with pytest.raises(ValueError, match="non-empty owner"):
        register_subsystem_clear(lambda: None, owner="")


def test_iter_types_yields_registered_pairs(fresh_registry: TypeRegistry):
    """``iter_types()`` yields ``(model, type_cls)`` for each registration.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register(Item, ItemType)
    result = dict(fresh_registry.iter_types())
    assert result == {Category: CategoryType, Item: ItemType}


def test_iter_types_empty_on_fresh_registry(fresh_registry: TypeRegistry):
    """``iter_types()`` yields nothing when no types are registered.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """
    assert list(fresh_registry.iter_types()) == []


def test_register_definition_rejects_different_definition_for_same_type(
    fresh_registry: TypeRegistry,
):
    """A type class cannot be rebound to a different collected definition.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    original_definition = _as_definition(object())
    fresh_registry.register_definition(CategoryType, original_definition)
    fresh_registry.register_definition(CategoryType, original_definition)

    with pytest.raises(
        ConfigurationError,
        match="CategoryType already has a registered DjangoTypeDefinition",
    ):
        fresh_registry.register_definition(CategoryType, _as_definition(object()))

    assert fresh_registry.get_definition(CategoryType) is original_definition


def test_global_registry_is_a_type_registry_instance():
    """The ``registry`` module-level singleton is a ``TypeRegistry``.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """
    assert isinstance(registry, TypeRegistry)
    # Sanity: still bound to the Django models module (smoke check that
    # the type signature didn't drift to a different shape).
    assert isinstance(Category, type) and issubclass(Category, models.Model)


def test_finalize_is_idempotent(monkeypatch: pytest.MonkeyPatch):
    """Calling finalize twice mutates type classes only once.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """
    calls = []
    original_type = strawberry.type

    # basedpyright: verbatim forward to strawberry.type; object fails its typed params
    def counting_type(type_cls: type, **kwargs: Any):  # pyright: ignore[reportExplicitAny]
        calls.append(type_cls)
        return original_type(type_cls, **kwargs)

    monkeypatch.setattr(strawberry, "type", counting_type)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    finalize_django_types()

    assert calls == [CategoryType]


def test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation():
    """Consumer-authored relation annotations are not rewritten if a stale pending record exists.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    try:

        class ManualPendingCategoryType(DjangoType):
            items: list["ManualPendingItemType"]

            class Meta:
                model = Category
                fields = ("id", "name", "items")

        definition = registry.get_definition(ManualPendingCategoryType)
        assert definition is not None
        assert definition.consumer_authored_fields == frozenset({"items"})

        registry.add_pending_relation(
            PendingRelation(
                source_type=ManualPendingCategoryType,
                source_model=Category,
                field_name="items",
                django_field=Category._meta.get_field("items"),
                related_model=Item,
            ),
        )

        class ManualPendingItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")

        globals()["ManualPendingItemType"] = ManualPendingItemType

        finalize_django_types()

        annotation = ManualPendingCategoryType.__annotations__["items"]
        assert getattr(annotation, "__args__", ()) == ("ManualPendingItemType",)
        assert list(registry.iter_pending_relations()) == []
    finally:
        globals().pop("ManualPendingItemType", None)


def test_finalize_skips_definitions_marked_finalized_when_registry_is_unfinalized(
    monkeypatch: pytest.MonkeyPatch,
):
    """Definition-level finalized flags prevent duplicate resolver and Strawberry mutation.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """
    attach_calls = []
    type_calls = []

    def counting_attach(*args: object, **kwargs: object):
        attach_calls.append((args, kwargs))

    def counting_type(type_cls: type, **kwargs: object):
        type_calls.append((type_cls, kwargs))

    monkeypatch.setattr(finalizer_module, "_attach_relation_resolvers", counting_attach)
    monkeypatch.setattr(strawberry, "type", counting_type)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    definition = registry.get_definition(CategoryType)
    assert definition is not None
    definition.finalized = True

    finalize_django_types()

    assert attach_calls == []
    assert type_calls == []
    assert registry.is_finalized() is True


def test_registering_concrete_type_after_finalization_raises():
    """A finalized registry rejects new concrete DjangoType classes.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    finalize_django_types()

    with pytest.raises(ConfigurationError, match=r"finalize_django_types\(\) already ran"):

        @definition_raises
        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")


def test_registry_clear_allows_fresh_type_classes_to_finalize_again():
    """clear() resets registry state for newly declared type classes.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    finalize_django_types()
    registry.clear()

    class FreshCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert registry.get(Category) is FreshCategoryType


def test_registry_clear_allows_fresh_relay_declared_type_to_finalize():
    """``registry.clear()`` lets a fresh Relay-declared ``DjangoType`` finalize cleanly.

    Pins the lifecycle contract that the same model can be re-bound to a fresh Relay-declared type
    after the previous one was dropped via ``clear()``. The fresh class must end up with
    ``relay.Node`` in its MRO plus the four ``resolve_*`` classmethods injected.

    Registry lifecycle: ``clear()`` then a fresh Relay ``DjangoType`` must finalize and inject
    ``resolve_*``. ``strawberry.Schema(...)`` here is construction, not a GraphQL execute. Live
    sibling for those methods on shipped types:
    ``examples/fakeshop/test_query/test_library_api.py::test_node_refetch_genre``.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryNode]:
            return []

    finalize_django_types()
    strawberry.Schema(query=Query)
    registry.clear()

    class FreshCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query2:
        @strawberry.field
        def all_categories(self) -> list[FreshCategoryNode]:
            return []

    finalize_django_types()
    strawberry.Schema(query=Query2)
    assert registry.is_finalized() is True
    assert registry.get(Category) is FreshCategoryNode
    assert relay.Node in FreshCategoryNode.__mro__
    for attr in (
        "resolve_id",
        "resolve_id_attr",
        "resolve_node",
        "resolve_nodes",
    ):
        assert attr in FreshCategoryNode.__dict__


def test_phase_1_failure_is_atomic_and_retryable_after_missing_target_registers():
    """Unresolved targets fail before class mutation and can retry after the target appears.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    definition = registry.get_definition(ItemType)
    assert registry.is_finalized() is False
    assert definition is not None
    assert definition.finalized is False
    assert not hasattr(ItemType, "__strawberry_definition__")
    assert list(registry.iter_pending_relations())

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert ItemType.__annotations__["category"] is CategoryType
    assert list(registry.iter_pending_relations()) == []


def test_phase_1_failure_does_not_rewrite_any_pending_annotations_when_one_target_is_missing():
    """A mixed pending set stays untouched until every relation target resolves.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = (
                "id",
                "name",
                "items",
                "properties",
            )

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert CategoryType.__annotations__["items"] is PendingRelationAnnotation
    assert CategoryType.__annotations__["properties"] is PendingRelationAnnotation

    with pytest.raises(ConfigurationError, match="Category.properties -> Property"):
        finalize_django_types()

    pending_names = [pending.field_name for pending in registry.iter_pending_relations()]
    category_definition = registry.get_definition(CategoryType)
    item_definition = registry.get_definition(ItemType)
    assert registry.is_finalized() is False
    assert category_definition is not None
    assert item_definition is not None
    assert category_definition.finalized is False
    assert item_definition.finalized is False
    assert not hasattr(CategoryType, "__strawberry_definition__")
    assert not hasattr(ItemType, "__strawberry_definition__")
    assert pending_names == ["items", "properties"]
    assert CategoryType.__annotations__["items"] is PendingRelationAnnotation
    assert CategoryType.__annotations__["properties"] is PendingRelationAnnotation

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert CategoryType.__annotations__["items"] == list[ItemType]
    assert CategoryType.__annotations__["properties"] == list[PropertyType]
    assert list(registry.iter_pending_relations()) == []


def test_phase_3_failure_leaves_registry_unfinalized_and_requires_fresh_classes(
    monkeypatch: pytest.MonkeyPatch,
):
    """A Strawberry-side failure is recovered by clear() plus fresh class recreation.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """
    original_type = strawberry.type
    reached_by_strawberry: list[type] = []

    def failing_type(type_cls: type, **kwargs: object):
        reached_by_strawberry.append(type_cls)
        raise TypeError("simulated Strawberry failure")

    monkeypatch.setattr(strawberry, "type", failing_type)

    class BrokenCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    with pytest.raises(TypeError):
        finalize_django_types()

    definition = registry.get_definition(BrokenCategoryType)
    assert registry.is_finalized() is False
    assert definition is not None
    assert definition.finalized is False
    assert reached_by_strawberry == [BrokenCategoryType]

    registry.clear()
    monkeypatch.setattr(strawberry, "type", original_type)

    class FreshCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert registry.get(Category) is FreshCategoryType
    assert registry.is_finalized() is True


def test_pending_set_is_cleaned_after_success_and_retained_after_phase_1_failure():
    """Pending records remain after unresolved failure but disappear after success.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    assert [pending.field_name for pending in registry.iter_pending_relations()] == ["category"]

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert ItemType.__annotations__["category"] is CategoryType
    assert list(registry.iter_pending_relations()) == []


def test_discard_pending_uses_identity_match_with_real_pending_relation(
    fresh_registry: TypeRegistry,
):
    """``discard_pending`` removes the exact records handed back by the caller.

    Builds two records from the same values and asserts that discarding one leaves the other in
    place.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """
    source_type = _as_django_type(type("SharedSource", (), {}))
    build_record = functools.partial(
        PendingRelation,
        source_type=source_type,
        source_model=Category,
        field_name="items",
        django_field=Category._meta.get_field("items"),
        related_model=Item,
    )
    record_a = build_record()
    record_b = build_record()
    # Sanity-check: distinct objects built from the same values, and unequal,
    # since records compare by identity.
    assert record_a is not record_b
    assert record_a != record_b
    fresh_registry.add_pending_relation(record_a)
    fresh_registry.add_pending_relation(record_b)
    fresh_registry.discard_pending([record_a])
    remaining = list(fresh_registry.iter_pending_relations())
    assert len(remaining) == 1
    assert remaining[0] is record_b


def test_discard_pending_tolerates_non_hashable_django_field(fresh_registry: TypeRegistry):
    """``discard_pending`` removes pending records by identity without hashing them.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    class _NonHashableField:
        @override
        def __eq__(self, other: object):
            return self is other

    pending = PendingRelation(
        source_type=_as_django_type(type("Src", (), {})),
        source_model=Category,
        field_name="items",
        # basedpyright: the unhashable field is the hostile input under test; PendingRelation types
        # django_field as ModelField
        django_field=_NonHashableField(),  # pyright: ignore[reportArgumentType]
        related_model=Item,
    )

    fresh_registry.add_pending_relation(pending)
    fresh_registry.discard_pending([pending])

    assert list(fresh_registry.iter_pending_relations()) == []


def test_mutators_reject_calls_after_mark_finalized(fresh_registry: TypeRegistry):
    """After ``mark_finalized``, every mutator raises ``ConfigurationError``.

    Defense-in-depth: ``DjangoType.__init_subclass__`` already rejects new subclasses
    post-finalization, but the registry boundary itself must also fail loud so out-of-band mutators
    (late imports, manual test harnesses) cannot silently corrupt the finalized snapshot.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.mark_finalized()
    pending = PendingRelation(
        source_type=CategoryType,
        source_model=Category,
        field_name="items",
        django_field=Category._meta.get_field("items"),
        related_model=Item,
    )

    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.register(Category, CategoryType)
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.register_definition(CategoryType, _as_definition(object()))
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.add_pending_relation(pending)
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.discard_pending([pending])
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.register_enum(Category, "status", Status)


def test_clear_does_not_remove_mutation_from_previously_finalized_classes():
    """clear() resets the registry, not already-mutated class objects.

    Registry lifecycle: finalize-time class mutation, pending records, and phase failure atomicity.
    A live request never sees a half-finalized registry. Live sibling for a successful compose:
    ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    definition = CategoryType.__django_strawberry_definition__
    registry.clear()

    assert registry.is_finalized() is False
    assert hasattr(CategoryType, "__strawberry_definition__")
    assert CategoryType.__django_strawberry_definition__ is definition


def test_register_with_definition_rolls_back_register_on_definition_failure(
    fresh_registry: TypeRegistry,
):
    """``register_with_definition`` is atomic across the pair.

    If ``register_definition`` raises after ``register`` succeeded, the model->type mapping must
    not persist. Otherwise a subsequent attempt to register the type would surface "already
    registered" instead of the real underlying failure.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    sentinel = _as_definition(object())
    fresh_registry.register_definition(CategoryType, sentinel)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Category, CategoryType, _as_definition(object()))

    assert fresh_registry.get(Category) is None
    assert fresh_registry.model_for_type(CategoryType) is None
    # The pre-existing definition pin survives the rollback.
    assert fresh_registry.get_definition(CategoryType) is sentinel

    # Re-registration after the rollback now sees a clean slate for the model.
    fresh_registry.register_with_definition(Category, CategoryType, sentinel)
    assert fresh_registry.get(Category) is CategoryType


# ---------------------------------------------------------------------------
# Multi-type storage + primary tracking (spec-018-meta_primary-0_0_6.md).
# Tests below exercise the contract through ``register`` /
# ``register_with_definition`` directly with plain test classes (no
# ``DjangoType`` subclasses).
# ---------------------------------------------------------------------------


def test_register_two_types_same_model_without_primary_allows_both_in_types_for(
    fresh_registry: TypeRegistry,
):
    """Two types for one model without ``primary`` co-exist; both appear in ``types_for``.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemTypeA:
        pass

    @_as_django_type
    class ItemTypeB:
        pass

    fresh_registry.register(Item, ItemTypeA)
    fresh_registry.register(Item, ItemTypeB)
    assert fresh_registry.types_for(Item) == (ItemTypeA, ItemTypeB)
    assert fresh_registry.primary_for(Item) is None


def test_register_second_type_for_same_model_no_longer_raises_collision(
    fresh_registry: TypeRegistry,
):
    """A second type for an existing model registers without raising.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemTypeA:
        pass

    @_as_django_type
    class ItemTypeB:
        pass

    fresh_registry.register(Item, ItemTypeA)
    try:
        fresh_registry.register(Item, ItemTypeB)
    except ConfigurationError:
        pytest.fail("second registration without primary must not raise")


def test_register_same_type_twice_is_idempotent(fresh_registry: TypeRegistry):
    """Calling ``register(Model, T)`` twice is a no-op for the second call.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    second = fresh_registry.register(Item, ItemType)
    assert second is False
    assert fresh_registry.types_for(Item) == (ItemType,)


def test_register_primary_flag_sets_primary_for(fresh_registry: TypeRegistry):
    """``primary=True`` populates ``_primaries`` and ``primary_for`` reads it back.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    assert fresh_registry.primary_for(Item) is ItemType
    assert fresh_registry.get(Item) is ItemType
    assert fresh_registry.types_for(Item) == (ItemType,)


def test_register_two_primaries_for_same_model_raises_configuration_error(
    fresh_registry: TypeRegistry,
):
    """Second ``primary=True`` on the same model raises naming attempt, model, and incumbent primary.

    Pins all three load-bearing identifiers in the error message so a future cosmetic refactor
    can't silently drop the attempt name (``AdminItemType``), the model name (``Item``), or the
    incumbent primary (``ItemType``) - the grep-from-a-stack-trace triage path needs each one.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    @_as_django_type
    class AdminItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    with pytest.raises(
        ConfigurationError,
        match=r"Cannot register AdminItemType as primary for Item;.*ItemType is already the primary type",
    ):
        fresh_registry.register(Item, AdminItemType, primary=True)
    # The duplicate-primary attempt did not append AdminItemType.
    assert fresh_registry.types_for(Item) == (ItemType,)
    assert fresh_registry.primary_for(Item) is ItemType


def test_register_same_type_re_register_with_flipped_primary_false_raises(
    fresh_registry: TypeRegistry,
):
    """Flip of stored ``primary=True`` to ``primary=False`` raises.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    with pytest.raises(ConfigurationError, match="primary flag cannot be flipped"):
        fresh_registry.register(Item, ItemType, primary=False)


def test_register_same_type_re_register_with_flipped_primary_true_raises(
    fresh_registry: TypeRegistry,
):
    """Flip of stored ``primary=False`` to ``primary=True`` raises (symmetric guard).

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    with pytest.raises(ConfigurationError, match="primary flag cannot be flipped"):
        fresh_registry.register(Item, ItemType, primary=True)


def test_register_with_definition_rollback_clears_primary(fresh_registry: TypeRegistry):
    """``register_with_definition`` rolls back ``_primaries`` for state it added.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    # Pre-poison ``register_definition`` for ItemType so the second
    # ``register_with_definition`` call raises after ``register`` succeeded.
    sentinel = _as_definition(object())
    fresh_registry.register_definition(ItemType, sentinel)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(
            Item,
            ItemType,
            _as_definition(object()),
            primary=True,
        )

    assert fresh_registry.types_for(Item) == ()
    assert fresh_registry.model_for_type(ItemType) is None
    assert fresh_registry.primary_for(Item) is None
    # Pre-existing definition pin survives.
    assert fresh_registry.get_definition(ItemType) is sentinel


def test_register_with_definition_rollback_restores_pre_existing_primary(
    fresh_registry: TypeRegistry,
):
    """Rollback restores ``_primaries[model]`` to the pre-existing primary.

    Pins the ``else: self._primaries[model] = pre_primary`` branch of the rollback in
    ``register_with_definition``: when a model already has a primary set and a NEW non-primary
    type's ``register()`` succeeds, then ``register_definition`` raises, the rollback must restore
    the pre-existing primary rather than popping it.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    @_as_django_type
    class AdminItemType:
        pass

    # Set up a pre-existing primary on Item.
    fresh_registry.register_with_definition(Item, ItemType, _as_definition(object()), primary=True)
    assert fresh_registry.primary_for(Item) is ItemType

    # Pre-poison the definition for AdminItemType so register_definition raises
    # AFTER register() succeeds (appended=True for the new non-primary type).
    sentinel = _as_definition(object())
    fresh_registry.register_definition(AdminItemType, sentinel)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Item, AdminItemType, _as_definition(object()))

    # AdminItemType was rolled back from ``_types`` and ``_models``.
    assert fresh_registry.types_for(Item) == (ItemType,)
    assert fresh_registry.model_for_type(AdminItemType) is None
    # ``_primaries[Item]`` is still ``ItemType`` - the else-branch restore ran.
    assert fresh_registry.primary_for(Item) is ItemType


def test_register_with_definition_idempotent_re_register_does_not_corrupt_state(
    fresh_registry: TypeRegistry,
):
    """A re-register-with-different-definition failure leaves pre-existing state intact.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    def1 = _as_definition(object())
    def2 = _as_definition(object())
    assert def2 is not def1

    fresh_registry.register_with_definition(Item, ItemType, def1)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Item, ItemType, def2)

    assert fresh_registry.types_for(Item) == (ItemType,)
    assert fresh_registry.model_for_type(ItemType) is Item
    assert fresh_registry.get_definition(ItemType) is def1
    assert fresh_registry.primary_for(Item) is None


def test_register_with_definition_idempotent_re_register_preserves_primary(
    fresh_registry: TypeRegistry,
):
    """Primary-preservation corollary: the pre-existing primary survives a re-register failure.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    def1 = _as_definition(object())
    def2 = _as_definition(object())
    fresh_registry.register_with_definition(Item, ItemType, def1, primary=True)
    assert fresh_registry.primary_for(Item) is ItemType

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Item, ItemType, def2, primary=True)

    assert fresh_registry.primary_for(Item) is ItemType
    assert fresh_registry.types_for(Item) == (ItemType,)


def test_register_returns_true_for_new_state(fresh_registry: TypeRegistry):
    """First registration returns ``True`` (state was added).

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class ItemType:
        pass

    assert fresh_registry.register(Item, ItemType) is True


def test_register_returns_false_for_idempotent_re_register(fresh_registry: TypeRegistry):
    """Idempotent re-register returns ``False`` (no state added).

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    assert fresh_registry.register(Item, ItemType) is False


def test_get_returns_single_type_when_one_registered_no_primary(fresh_registry: TypeRegistry):
    """``get(Model)`` returns the lone type even when ``primary`` is not declared.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    assert fresh_registry.get(Item) is ItemType


def test_get_returns_primary_when_multiple_and_primary_declared(fresh_registry: TypeRegistry):
    """``get(Model)`` returns the explicit primary when multiple types are registered.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    @_as_django_type
    class AdminItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    fresh_registry.register(Item, AdminItemType)
    assert fresh_registry.get(Item) is ItemType


def test_get_returns_none_when_multiple_and_no_primary(fresh_registry: TypeRegistry):
    """``get(Model)`` returns ``None`` when multi-type and no primary declared.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    @_as_django_type
    class AdminItemType:
        pass

    fresh_registry.register(Item, ItemType)
    fresh_registry.register(Item, AdminItemType)
    assert fresh_registry.get(Item) is None
    # Distinguishing path: types_for still surfaces the registered pair.
    assert fresh_registry.types_for(Item) == (ItemType, AdminItemType)


def test_primary_for_returns_none_when_only_implicit_single_type(fresh_registry: TypeRegistry):
    """``primary_for`` is strictly ``_primaries``; the single-type convenience lives on ``get``.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.get(Item) is ItemType


def test_types_for_preserves_registration_order(fresh_registry: TypeRegistry):
    """``types_for`` returns registrations in the order they happened.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class A:
        pass

    @_as_django_type
    class B:
        pass

    @_as_django_type
    class C:
        pass

    fresh_registry.register(Item, A)
    fresh_registry.register(Item, B)
    fresh_registry.register(Item, C)
    assert fresh_registry.types_for(Item) == (A, B, C)


def test_iter_types_yields_each_type_once_when_multiple_registered_for_same_model(
    fresh_registry: TypeRegistry,
):
    """``iter_types`` yields one pair per registered type; multi-type models appear repeatedly.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class A:
        pass

    @_as_django_type
    class B:
        pass

    fresh_registry.register(Item, A, primary=True)
    fresh_registry.register(Item, B)
    pairs = list(fresh_registry.iter_types())
    assert pairs == [(Item, A), (Item, B)]


def test_register_same_type_against_two_models_still_raises(fresh_registry: TypeRegistry):
    """Reverse-collision contract is preserved by the multi-type registry.

    Registry lifecycle: isolated ``TypeRegistry`` maps. A live request cannot show map identity. No
    live sibling.
    """

    @_as_django_type
    class SharedType:
        pass

    fresh_registry.register(Category, SharedType)
    with pytest.raises(ConfigurationError, match="already registered against Category"):
        fresh_registry.register(Item, SharedType)


def test_clear_resets_primaries(fresh_registry: TypeRegistry):
    """``clear()`` wipes ``_primaries`` alongside the other registry maps.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    fresh_registry.clear()
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.types_for(Item) == ()


def test_models_with_multiple_types_yields_only_models_with_two_or_more(
    fresh_registry: TypeRegistry,
):
    """``models_with_multiple_types`` reports only models with ``>= 2`` registered types.

    Registry lifecycle: primary / multi-type maps. A live request cannot show ``types_for`` order
    or rollback. Live sibling for shipped multi-type with a primary:
    ``test_library_api.py::test_public_patron_exclude_deny_list_shapes_type_and_resolves``.
    Ambiguity at finalize cannot ship.
    """

    @_as_django_type
    class CategoryType:
        pass

    @_as_django_type
    class ItemTypeA:
        pass

    @_as_django_type
    class ItemTypeB:
        pass

    @_as_django_type
    class PropertyTypeA:
        pass

    @_as_django_type
    class PropertyTypeB:
        pass

    @_as_django_type
    class PropertyTypeC:
        pass

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register(Item, ItemTypeA)
    fresh_registry.register(Item, ItemTypeB)
    fresh_registry.register(Property, PropertyTypeA)
    fresh_registry.register(Property, PropertyTypeB)
    fresh_registry.register(Property, PropertyTypeC)
    multi = sorted(fresh_registry.models_with_multiple_types(), key=lambda m: m.__name__)
    assert multi == [Item, Property]


# ---------------------------------------------------------------------------
# Finalize-time ambiguity audit (spec-018-meta_primary-0_0_6.md).
# Tests below cover ``_audit_primary_ambiguity()`` running inside
# ``finalize_django_types()``. The audit-success and audit-vs-unresolved
# tests live in ``tests/types/test_definition_order.py``; this file hosts
# the raise-at-finalize and once-per-build regression coverage.
# ---------------------------------------------------------------------------


def test_finalize_raises_when_model_has_multiple_types_no_primary():
    """``finalize_django_types`` raises when a model has 2+ types and no primary.

    Registry lifecycle: ``_audit_primary_ambiguity`` inside ``finalize_django_types``. A live
    schema with two types and no primary never builds. No live sibling for the raise; composition
    success is ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemTypeA

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.model_for_type(ItemTypeB) is Item

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Models with multiple registered DjangoType subclasses and no primary" in msg
    assert "Item" in msg
    assert "ItemTypeA" in msg
    assert "ItemTypeB" in msg


def test_finalize_ambiguity_error_message_contains_actionable_fix():
    """The ambiguity error message ends with the actionable ``Declare Meta.primary`` sentence.

    Registry lifecycle: ``_audit_primary_ambiguity`` inside ``finalize_django_types``. A live
    schema with two types and no primary never builds. No live sibling for the raise; composition
    success is ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemTypeA

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.model_for_type(ItemTypeB) is Item

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    assert (
        "Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."
    ) in str(
        exc_info.value,
    )


def test_audit_runs_once_per_build(monkeypatch: pytest.MonkeyPatch):
    """The ambiguity audit runs exactly once per finalize-cycle build.

    Pins that ``_audit_primary_ambiguity`` sits *below* the ``registry.is_finalized()``
    short-circuit in ``finalize_django_types``; a second ``finalize_django_types()`` call must
    short-circuit without re-auditing.

    Registry lifecycle: ``_audit_primary_ambiguity`` inside ``finalize_django_types``. A live
    schema with two types and no primary never builds. No live sibling for the raise; composition
    success is ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """
    calls = []
    original = registry.models_with_multiple_types

    def spy():
        calls.append(None)
        return original()

    monkeypatch.setattr(registry, "models_with_multiple_types", spy)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    finalize_django_types()
    finalize_django_types()  # second call must hit the is_finalized() guard

    assert len(calls) == 1


# ---------------------------------------------------------------------------
# The ``unregister`` public helper. Tests below
# exercise the new public surface that replaces the direct private-map
# pokes in the walker/extension fixtures and the older
# check_schema-audit fixtures (types list, model index, primary slot, and
# definition map).
# ---------------------------------------------------------------------------


def test_unregister_removes_from_types_models_primaries_definitions(fresh_registry: TypeRegistry):
    """``unregister`` drops the type from every registry map.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class ItemType:
        pass

    sentinel = _as_definition(object())
    fresh_registry.register(Item, ItemType, primary=True)
    fresh_registry.register_definition(ItemType, sentinel)

    fresh_registry.unregister(ItemType)

    assert fresh_registry.types_for(Item) == ()
    assert fresh_registry.model_for_type(ItemType) is None
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.get_definition(ItemType) is None


def test_unregister_evicts_connection_type_cache_entry(fresh_registry: TypeRegistry):
    """``unregister`` drops the type's generated-connection-class cache entry.

    ``clear()`` already purges the whole identity-keyed cache; ``unregister`` promises "all traces"
    of one type, so its eviction keeps the two public mutators consistent. Entries for OTHER types
    survive.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    from django_strawberry_framework.connection import (
        DjangoConnection,
        _CachedConnectionType,
        _connection_type_cache,
    )

    @_as_django_type
    class ItemType:
        pass

    @_as_django_type
    class CategoryType:
        pass

    fresh_registry.register(Item, ItemType)
    _connection_type_cache[ItemType] = _CachedConnectionType(
        _as_definition(object()),
        DjangoConnection[DjangoType],
    )
    _connection_type_cache[CategoryType] = sentinel_kept = _CachedConnectionType(
        _as_definition(object()),
        DjangoConnection[DjangoType],
    )
    try:
        fresh_registry.unregister(ItemType)
        assert ItemType not in _connection_type_cache
        assert _connection_type_cache[CategoryType] is sentinel_kept
    finally:
        _connection_type_cache.pop(ItemType, None)
        _connection_type_cache.pop(CategoryType, None)


def test_unregister_tolerates_unimportable_connection_submodule(fresh_registry: TypeRegistry):
    """``unregister``'s connection-cache ``except ImportError`` guard is best-effort.

    Unregister twin of ``test_clear_tolerates_unimportable_connection_submodule`` - same
    poisoned-``sys.modules`` shape; the registry's own maps are still cleaned when
    ``connection.py`` cannot be imported.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    connection_name = "django_strawberry_framework.connection"

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    with blocked_modules(connection_name):
        # Must not raise even though connection.py cannot be imported.
        fresh_registry.unregister(ItemType)
        assert fresh_registry.model_for_type(ItemType) is None


def test_unregister_removes_pending_relations_sourced_from_type(fresh_registry: TypeRegistry):
    """``unregister`` discards pending relations whose ``source_type`` matches.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class CategoryType:
        pass

    @_as_django_type
    class ItemType:
        pass

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register(Item, ItemType)
    pending_keep = PendingRelation(
        source_type=CategoryType,
        source_model=Category,
        field_name="items",
        django_field=Category._meta.get_field("items"),
        related_model=Item,
    )
    pending_drop = PendingRelation(
        source_type=ItemType,
        source_model=Item,
        field_name="category",
        django_field=Item._meta.get_field("category"),
        related_model=Category,
    )
    fresh_registry.add_pending_relation(pending_keep)
    fresh_registry.add_pending_relation(pending_drop)

    fresh_registry.unregister(ItemType)

    remaining = list(fresh_registry.iter_pending_relations())
    assert remaining == [pending_keep]


def test_unregister_keeps_siblings_intact_in_multi_type_case(fresh_registry: TypeRegistry):
    """``unregister`` of one type for a model leaves siblings registered.

    When the unregistered type was the primary, the model loses its primary slot - the caller is
    responsible for re-declaring a primary via a fresh registration cycle. Siblings stay in
    ``types_for`` in their original registration order.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class ItemTypeA:
        pass

    @_as_django_type
    class ItemTypeB:
        pass

    @_as_django_type
    class ItemTypeC:
        pass

    fresh_registry.register(Item, ItemTypeA, primary=True)
    fresh_registry.register(Item, ItemTypeB)
    fresh_registry.register(Item, ItemTypeC)

    fresh_registry.unregister(ItemTypeA)

    assert fresh_registry.types_for(Item) == (ItemTypeB, ItemTypeC)
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.model_for_type(ItemTypeB) is Item
    assert fresh_registry.model_for_type(ItemTypeC) is Item


def test_unregister_of_primary_leaves_state_that_audit_rejects():
    """``unregister(primary_for_multi)`` leaves a state the finalize audit refuses.

    Pins the contract narrated by ``unregister``'s docstring at
    ``django_strawberry_framework/registry.py::TypeRegistry.unregister #"When ``type_cls`` is the
    primary for its model"``: when ``type_cls`` is the primary for its model, the model loses its
    primary even if siblings remain - the caller must re-declare a primary via a fresh registration
    cycle. Concretely: register three types against the same model with the first as primary,
    unregister the primary, then call ``finalize_django_types()`` and confirm it raises the
    canonical ambiguity error. Prevents a later change from "helpfully" auto-promoting the next
    sibling to primary on unregister, which would silently change the relation-resolution target.

    Registry lifecycle: ``_audit_primary_ambiguity`` inside ``finalize_django_types``. A live
    schema with two types and no primary never builds. No live sibling for the raise; composition
    success is ``examples/fakeshop/test_query/test_schema_composition_api.py``.
    """

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemTypeC(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.primary_for(Item) is ItemTypeA
    assert registry.types_for(Item) == (ItemTypeA, ItemTypeB, ItemTypeC)

    registry.unregister(ItemTypeA)

    assert registry.primary_for(Item) is None
    assert registry.types_for(Item) == (ItemTypeB, ItemTypeC)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Models with multiple registered DjangoType subclasses and no primary" in msg
    assert "Item" in msg
    assert "ItemTypeB" in msg
    assert "ItemTypeC" in msg
    assert (
        "Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."
        in msg
    )


def test_unregister_is_noop_on_unknown_type(fresh_registry: TypeRegistry):
    """``unregister`` returns silently when ``type_cls`` was never registered.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    @_as_django_type
    class NotRegistered:
        pass

    fresh_registry.unregister(NotRegistered)  # no raise

    assert fresh_registry.types_for(Item) == ()


def test_unregister_raises_after_finalize():
    """``unregister`` honours ``_check_mutable``: post-finalize calls raise.

    The finalized registry is the runtime lookup source for optimizer planning, the schema audit,
    and relation-target resolution. Removing entries after ``finalize_django_types()`` would
    silently disable planning for types still present in the built Strawberry schema, so the public
    mutator refuses to corrupt the snapshot.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="finalized"):
        registry.unregister(CategoryType)


def test_clear_tolerates_unimportable_filter_submodules(fresh_registry: TypeRegistry):
    """``clear()`` itself imports nothing, so a broken ``sys.modules`` cannot break it.

    Every subsystem binds its own teardown callback at ITS import time via
    ``register_subsystem_clear``, and ``clear()`` replays the already-resolved callables. That
    replay is the only place a poisoned ``sys.modules`` can be reached at all, and it imports
    neither poisoned name directly; the two submodule lookups it does make are best-effort
    (``utils/inputs.py::_safe_import``). So neither the poisoned package nor the poisoned
    ``inputs`` module can make ``clear()`` raise: the registry's own state is dropped either way
    (spec-027 Decision 9).

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    inputs_name = "django_strawberry_framework.filters.inputs"
    filters_name = "django_strawberry_framework.filters"

    @_as_django_type
    class CategoryType:
        pass

    # ``None`` in ``sys.modules`` is the shape that makes an import of
    # either module raise ImportError. ``clear()`` itself runs no import,
    # and the replayed callbacks look up neither poisoned name directly.
    # The two submodule lookups they do make are best-effort, so nothing
    # on the teardown path can raise OUT of ``clear()``.
    with blocked_modules(inputs_name, filters_name):
        fresh_registry.register(Category, CategoryType)
        # Must not raise even though neither submodule can be imported.
        fresh_registry.clear()
        assert fresh_registry.get(Category) is None


def test_clear_tolerates_unimportable_order_submodules(fresh_registry: TypeRegistry):
    """``clear()`` itself imports nothing, so a broken ``sys.modules`` cannot break it.

    Order twin of ``test_clear_tolerates_unimportable_filter_submodules``. Every subsystem binds
    its own teardown callback at ITS import time via ``register_subsystem_clear`` -- the order side
    registers ``clear_order_input_namespace`` and ``_clear_helper_referenced_ordersets`` -- and
    ``clear()`` replays the already-resolved callables. That replay is the only place a poisoned
    ``sys.modules`` can be reached at all, and it imports neither poisoned name directly; the two
    submodule lookups it does make are best-effort (``utils/inputs.py::_safe_import``). So neither
    the poisoned package nor the poisoned ``inputs`` module can make ``clear()`` raise: the
    registry's own state is dropped either way (spec-028 Decision 9).

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    inputs_name = "django_strawberry_framework.orders.inputs"
    orders_name = "django_strawberry_framework.orders"

    @_as_django_type
    class CategoryType:
        pass

    # ``None`` in ``sys.modules`` is the shape that makes an import of
    # either module raise ImportError. ``clear()`` itself runs no import,
    # and the replayed callbacks look up neither poisoned name directly.
    # The two submodule lookups they do make are best-effort, so nothing
    # on the teardown path can raise OUT of ``clear()``.
    with blocked_modules(inputs_name, orders_name):
        fresh_registry.register(Category, CategoryType)
        # Must not raise even though neither order submodule can be imported.
        fresh_registry.clear()
        assert fresh_registry.get(Category) is None


def test_clear_tolerates_unimportable_connection_submodule(fresh_registry: TypeRegistry):
    """``clear()`` itself imports nothing, so a poisoned ``connection`` entry cannot break it.

    Connection twin of ``test_clear_tolerates_unimportable_order_submodules``. ``connection.py``
    binds its connection-type-cache teardown (``clear_connection_type_cache``) at ITS import time
    via ``register_subsystem_clear``, and ``clear()`` replays the already-resolved callable without
    importing ``connection.py``. So a ``sys.modules`` entry poisoned to ``None`` (the shape that
    makes an import of it raise ImportError) cannot make ``clear()`` raise: the registry's own
    state is dropped either way.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    connection_name = "django_strawberry_framework.connection"

    @_as_django_type
    class CategoryType:
        pass

    # ``None`` in ``sys.modules`` makes an import of ``connection.py`` raise
    # ImportError; ``clear()`` runs no import, so its teardown path never reaches it.
    with blocked_modules(connection_name):
        fresh_registry.register(Category, CategoryType)
        # Must not raise even though connection.py cannot be imported.
        fresh_registry.clear()
        assert fresh_registry.get(Category) is None


def test_clear_tolerates_unimportable_relay_module(fresh_registry: TypeRegistry):
    """``clear()`` itself imports nothing, so a poisoned ``relay`` entry cannot break it.

    Relay twin of ``test_clear_tolerates_unimportable_connection_submodule``. The top-level
    ``relay.py`` binds its root-node-field ledger teardown (``_clear_node_fields_declared``,
    spec-032 Decision 8) at ITS import time via ``register_subsystem_clear``, and ``clear()``
    replays the already-resolved callable without importing ``relay.py``. So a ``sys.modules``
    entry poisoned to ``None`` cannot make ``clear()`` raise: the registry's own state is dropped
    either way. The positive co-clear path is pinned by
    ``tests/test_relay_node_field.py::test_node_field_without_node_types_raises_at_finalize``.

    Registry lifecycle: ``clear`` / ``unregister`` / teardown callbacks. A live request cannot show
    LIFO order, retry, or ImportError guards. No live sibling.
    """
    relay_name = "django_strawberry_framework.relay"

    @_as_django_type
    class CategoryType:
        pass

    # ``None`` in ``sys.modules`` makes an import of ``relay.py`` raise
    # ImportError; ``clear()`` runs no import, so its teardown path never reaches it.
    with blocked_modules(relay_name):
        fresh_registry.register(Category, CategoryType)
        # Must not raise even though relay.py cannot be imported.
        fresh_registry.clear()
        assert fresh_registry.get(Category) is None
